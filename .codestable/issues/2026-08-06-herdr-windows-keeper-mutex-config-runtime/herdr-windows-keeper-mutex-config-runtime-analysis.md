---
doc_type: issue-analysis
issue: 2026-08-06-herdr-windows-keeper-mutex-config-runtime
status: confirmed
root_cause_type: multi
root_cause_detail:
  G1: config (v2 顶层 runtime 字段 schema 脱节 — 设计验收过但实现未接线)
  G2: concurrency (Windows keeper 互斥失效 — fcntl 缺失时锁为空操作)
  G3: concurrency (Herdr 命名会话 socket 活性判定 — 文件存在不代表 server 存活)
  G4: robustness (kill -f 对已消失 Herdr workspace 不幂等)
  G5: tooling (采集/诊断编码与路径卫生)
related:
  - herdr-windows-keeper-mutex-config-runtime-report.md
  - herdr-windows-keeper-mutex-config-runtime-fix-note.md
cross_ref_audit: .codestable/audits/2026-08-05-herdr-ccb-recent-changes/index.md
tags:
  - windows
  - herdr
  - keeper
  - config-schema
  - ccbd
  - run_spike.ps1
---

# Herdr Windows keeper 互斥与 config runtime 字段 根因分析

## 0. 结论先行

这不是单一问题，而是三条独立故障链叠加。**agent pane 起不来的直接根因是 Windows keeper 互斥失效**（fcntl 缺失 → 锁空操作 → 多 keeper 并发 → 状态文件互相覆盖 → 启动围栏拒绝）；**config 报错是另一条独立的 schema 欠账**（已验收的 `runtime` 字段未实现且残留配置命中即失败）；**Herdr 命名会话 socket 活性判定缺失**让 mounted 状态对外不可验证。

## 1. G1 — config 顶层 `runtime` 字段 schema 脱节

### 1.1 证据链

1. 报错字符串唯一来源 `validation.py:113-118`：
   ```python
   unknown_top = sorted(set(document) - ALLOWED_TOP_LEVEL_KEYS)
   if unknown_top:
       raise ConfigValidationError(f'config contains unknown top-level fields: {", ".join(unknown_top)}')
   ```
2. 白名单 `common.py:17-30` 共 12 键，**无 `runtime`**；v3 顶层白名单 `workflow_v3.py:39` 亦无（v3 中它只在 `workflow.runtime` 下）。
3. 设计验收矛盾：`.codestable/features/2026-07-19-backend-resolver-opt-in-contract/` 的 AC-005 已勾选通过 ——"v2/v3 config `runtime.mux.backend` 解析一致；未知 runtime 字段 fail-closed（config loader selected tests，23 passed）"。但当前实现：
   - `terminal_runtime/backend_selection.py` / `backend_resolver.py` 的 `requested_backend` 只来自 `terminal_type` 与 env（`CCB_MUX_BACKEND` 等），**不读取 config 的 `runtime.mux.backend`**；
   - `git log` 显示 `RuntimeMuxConfig` / `runtime.mux` 只存在于历史提交（`5c3a81cf`、`72860d99`、`d54fd8dd`），当前分支无实现。
4. 残留配置实锤：
   - `D:\C#Project\.ccb\ccb.config`（外部项目父级锚点）→ `[runtime.mux] backend = "rmux"`（**本次已删除**）；
   - `E:\GitHub开源项目\TachiKuma\claude_code_bridge\.ccb\ccb.config` → 同样含 `[runtime.mux]`（当前仍存在）。

### 1.2 触发路径

`find_nearest_project_anchor()`（`project/discovery.py:31`）从 cwd 向上找最近的 `.ccb` 锚点；当启动 cwd 落在无独立 `.ccb` 的位置（如父目录、子目录，或项目锚点缺失）时解析到含 `runtime` 的锚点 config → `load_project_config`（`io_runtime/documents.py:317`）→ v2 校验失败 → `handle_phase2_exception`（`cli/phase2_errors.py`）输出 `command_status: failed`。

### 1.3 为何采集脚本复现不了

采集脚本工作目录是外部项目 `AvaPrintDesigner`（有独立、干净的 `.ccb`，`ccb.config` 为合法 v2），项目发现解析到该锚点，永远读不到父级/残留含 `runtime` 的 config。→ 采集盲区。

## 2. G2 — Windows keeper 互斥失效（核心）

### 2.1 证据链

`lib/ccbd/keeper_runtime/support.py:8-23`：

```python
def try_acquire_keeper_lock(path: Path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    handle = target.open('a+', encoding='utf-8')
    try:
        import fcntl
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except ModuleNotFoundError:
        return handle        # ← Windows 必走：打开文件但【不持有任何锁】
    except OSError as exc:
        handle.close()
        if exc.errno in {errno.EACCES, errno.EAGAIN}: return None
        raise
    return handle
```

- Windows 下 `import fcntl` 抛 `ModuleNotFoundError` → 直接 `return handle`，**锁是空操作**，任何两个 keeper 都"获取成功"。
- `ccbd.stderr.log` 实锤：`ModuleNotFoundError: No module named 'fcntl'` + `StartupFenceError: expected startup lifecycle rejected: startup_id mismatch`。
- 进程采样实锤双 keeper：`run-20260806-085751/process-samples.jsonl` 中 `keeper_main.py` 同时存在 pid 6440、pid 7192。
- 状态分裂实锤：`keeper.json`（新 keeper 写）`keeper_pid` 与 `lease.json`（旧 keeper 6944 写）不一致。
- 讽刺点：同仓库已有正确的 Windows 跨进程锁实现 `lib/ccbd/control_plane_transport/endpoint_store.py:124`（`msvcrt.locking`），keeper 未复用。

### 2.2 后果链

双 keeper 并发 → 各自写 `keeper.json` / `lifecycle.json` → 状态互相覆盖 → 启动围栏发现 `startup_id mismatch` 拒绝新生命周期 → 反复 prestart / 重启 → 外部表现"cmd 窗口闪现后关闭"、agent pane 永远不 materialize。

## 3. G3 — Herdr 命名会话 socket 活性判定缺失

- CCB 创建独立 Herdr 会话 `ccb-avaprintdesigner-575a971f`（结构性设计，非 bug），但该会话的 server 进程未存活。
- `herdr.sock` 文件存在（24B，2026-08-04 15:00）≠ server 运行中；`cli:pane:list` 仍报 `server_not_running`。
- 判定逻辑只看文件存在性，未探测 socket 活性（`herdr status server --session` / `list_windows`）。
- 状态源不一致：`lease/lifecycle` 报 mounted/healthy，`startup-report` 报 failed，Herdr UI 侧无 pane。单一权威状态缺失。

## 4. G4 — kill -f 对已消失 Herdr workspace 不幂等

- `ccbd.stderr.log` 反复出现 `workspace wB1/wB3 not found`：force kill 场景下，Herdr workspace 已消失时 `workspace close` 返回非零并冒泡为 `CalledProcessError`。
- 结果：kill 流程带脏错误退出，后续 prestart 状态清理不可靠，叠加 G2 放大竞争。

## 5. G5 — 采集/诊断编码与路径卫生

- `host-context.json` / snapshot JSON 含中文路径与反斜杠，默认 gbk 解码即抛 `UnicodeDecodeError`；采集侧未按 UTF-8 读取，且解析失败未降级。
- `doctor-output` 实际是 gzip 压缩包但无扩展名，不利于人工排查。
- 采集脚本 `current_directory` 是 repo 而 `ccb8_path` 是外部项目，两套上下文在同一 run 混读，易误导归因。

## 6. 根因分类汇总

| # | 根因 | 类型 | 严重度 |
|---|---|---|---|
| G2 | Windows keeper 互斥失效（fcntl 缺失） | concurrency | P0 |
| G1 | v2 顶层 `runtime` schema 脱节 + 残留配置 | config | P0 |
| G3 | Herdr 命名会话 socket 活性判定缺失 | concurrency | P1 |
| G4 | kill -f 非幂等 | robustness | P1 |
| G5 | 采集/诊断编码与路径卫生 | tooling | P2 |

> 注：G1 的触发 config（`D:\C#Project\.ccb\ccb.config`）已在用户操作中删除，本机不再复现该报错；但 schema 欠账与 repo 自身残留 config 仍未消除，属于必须在代码层关闭的问题。
