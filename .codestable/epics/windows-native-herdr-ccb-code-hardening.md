---
status: accepted
created: 2026-08-07
accepted: 2026-08-07
---
# Native Windows CCB 代码硬化 — 修复已知缺陷与补齐支撑性缺口

## 起点

Epic `windows-native-herdr-ccb` 的 7 个子项在 Epic 文档层面通过了 final acceptance review（2 轮，
8 finding 全部 resolved），但独立 OCR review 揭示了 ITEM-4（A-lite import-herdr）和 ITEM-7
（managed startup）的交付物中存在真实代码缺陷，roadmap §12 `herdr-supportability-projection`
仍为 `in-progress`。

本 Epic 的目标是修复全部已知代码缺陷，补齐支撑性缺口，使代码层面满足 acceptance 条件，
为后续 Epic 的 evidence 采集与 support tier 毕业做好准备。

## 目标

1. `ccb config import-herdr` 功能完整且安全：不静默覆盖、输出合法 TOML、错误处理健壮、schema 合法
2. `ccb herdr open` 核心路径缺陷清零：daemon 冲突检测、跨平台 env、server shape 解析、ccb8.cmd 闪退
3. `ccb doctor --output` 接入 Herdr support tier 投影
4. roadmap §12 `herdr-supportability-projection` 从 `in-progress` → `accepted`
5. Herdr workspace 生命周期受控（namespace destroy 清理累积 workspace）

## 范围

- 修复 8 个 OCR 已核实代码缺陷（`herdr_config_import.py` ×4、`handlers_start.py` ×1、
  `herdr_common.py` ×1、`herdr_bootstrap.py` ×1、roadmap §12 in-progress ×1）
- `ccb doctor --output` consumer 端接入 projection 核心模块
- docs/README 与 projection 结论同步
- Herdr namespace destroy 时 workspace 清理
- 采集脚本同步更新
- 每个修复路径有 focused test

## 非目标

- 不获取 provider API 凭证（留给后续 Epic）
- 不追求 matrix pass evidence（留给后续 Epic）
- 不修改 C2 架构或权威矩阵
- 不向 Herdr upstream 提交 PR
- 不执行 npm publish/release/push
- 不改变 support tier（仍为 `unsupported`，留给后续 Epic 的 evidence）
- 不修复 Herdr viewport 渲染问题（Herdr upstream 侧）

## 验收标准

- `ccb config import-herdr` 输出通过 `validate_project_config` 验证；`--output` 已存在文件时拒绝覆盖
- `ccb herdr open` 全链路干净：WezTerm → Herdr → 双 pane → ask smoke，无闪窗、无超时、无误判
- `ccb doctor --output` 输出包含 `herdr.support_tier` 字段，值与 projection 核心模块一致
- roadmap items.yaml §12 状态 `accepted`
- kill + restart 周期后 Herdr 中无同名僵尸 workspace

## 关键决策

- **DEC-1 · 从 OCR findings 派生子项**：OCR review 揭示的 8 个缺陷直接映射为 ITEM-1（4 个
  import-herdr 缺陷）和 ITEM-2（3 个 herdr open 缺陷 + ccb8.cmd 闪退）。不另外创建独立
  issue，全部在本 Epic 内闭环。
- **DEC-2 · import-herdr 输出格式**：TOML 是 CCB config 链路的唯一格式。import-herdr
  当前写 JSON 是明确的 bug，修复为 TOML 输出，不做 JSON→TOML 双格式兼容。
- **DEC-3 · fail-closed 优先**：ITEM-2 的 daemon inspection 修复从 fail-open 改为至少
  log warning；如果无法安全区分"未安装"与"检测异常"，则 fail-closed（拒绝在 Herdr 模式下
  启动 CCB daemon），需用户显式确认。
- **DEC-4 · XDG_* 清除平台 gate**：`sys.platform == 'win32'` 才清除 XDG_*；非 Windows
  平台保留原生 XDG_* 环境变量，确保 Linux/macOS 上的 Herdr 复用 profile 不受影响。

## 子项契约

### ITEM-1 · A-lite import-herdr 完整修复
- **owning skill**：cs-issue
- **可交付结果**：
  - `herdr_config_import.py:71-73`：`target.exists()` 前置检查，已存在时 fail-fast
    （除非 `--force`）
  - `herdr_config_import.py:73`：`json.dumps` → TOML 序列化
  - `herdr_config_import.py:115-119`：`returncode != 0` 前置检查 + `isinstance(…, Mapping)`
    guard on `payload.get("result", payload)` before `.get("snapshot")`
  - `herdr_config_import.py:138`：`version=3` + `agents` 非法结构 → 合法 v2 `[windows]`
    或完整 v3 `workflow`，通过 `validate_project_config` 验证
  - 4 条修复路径各有 focused test
- **依赖**：无
- **验收要点**：`ccb config import-herdr` 输出通过 parser 验证；`--output` 已存在文件时
  拒绝覆盖并给出明确错误信息；TOML 输出可被 CCB config loader 直接读取
- **设计约束**：不改变 docstring "Does NOT overwrite an existing config file" 的保证；
  默认 target `ccb.config.herdr-import` 保持不变（不与 `ccb.config` 冲突）

### ITEM-2 · ccb herdr open 核心路径修复
- **owning skill**：cs-issue
- **可交付结果**：
  - `handlers_start.py:170-175`：区分 `ImportError`（herdr 模块不可用 → 安全返回 False）
    与通用 `Exception`（检测异常 → 至少 log warning，考虑 fail-closed）
  - `herdr_common.py:45-52`：`sys.platform == 'win32'` gate；非 Windows 保留 XDG_*
  - `herdr_bootstrap.py:63-71`：先 unwrap 嵌套 `result.server` 层再检查
    `running`/`compatible`，或确认 `query_herdr_server_status` 的返回形状契约
    并更新调用方
  - `ccb8.cmd` 闪退根因：定位 + 修复 + regression test
  - 端到端 smoke test：WezTerm → Herdr → `ccb herdr open` → 双 pane → ask
- **依赖**：无
- **验收要点**：4 条修复路径各有 focused test；WezTerm → Herdr → CCB → ask 全链路
  干净（无闪窗、无超时、无误判）；daemon 冲突检测在异常场景下不静默通过；
  非 Windows 平台 Herdr profile 不受 XDG_* 清除影响
- **设计约束**：daemon inspection 修复不改变既有 Herdr backend 检测的正常路径语义；
  跨平台 env 修复不引入 `sys.platform` 散落（集中在 `herdr_command_env()` 内）

### ITEM-3 · Doctor support tier 集成
- **owning skill**：cs-feat
- **可交付结果**：
  - `ccb doctor --output` 输出包含 `herdr.support_tier` 字段
  - consumer 端消费 `herdr_supportability_projection.py` 的 `compute_tier()` 结果
  - 字段值与 projection 核心模块计算一致
- **依赖**：无（projection 核心模块 624 行已完成，只需 consumer 端接线）
- **验收要点**：`ccb doctor --output` JSON 输出中 `herdr.support_tier` 字段存在；
  值与 `herdr_supportability_projection.py` 独立计算结果一致；tier 变化时
  doctor 输出同步反映

### ITEM-4 · Supportability projection roadmap 收尾
- **owning skill**：cs-feat
- **可交付结果**：
  - roadmap items.yaml §12 状态 `in-progress` → `accepted`
  - docs/README 中 Windows Herdr 章节与 projection 结论同步
  - 不夸大 support tier（当前为 `unsupported`，如实反映）
- **依赖**：ITEM-3（doctor 集成完成后 projection 才算有 consumer）
- **验收要点**：items.yaml §12 `status: accepted`；README 不宣称 supported；
  doctor/docs/README 三方不互相矛盾

### ITEM-5 · Herdr workspace 生命周期管理
- **owning skill**：cs-feat
- **可交付结果**：
  - ccbd namespace destroy 时通过 Herdr socket API 关闭关联 workspace
  - 采集脚本 cleanup phase 验证 workspace 不累积
  - 可选：`ccb herdr cleanup` 命令（手动清理孤儿 workspace）
- **依赖**：ITEM-2（managed startup 修复后才能安全测试 destroy 路径）
- **验收要点**：kill + restart 周期后 `herdr api snapshot` 证实 workspace 数量
  不随 kill/restart 单调增长；无同名僵尸 workspace（当前 run-20260807-004015
  发现 6 个 `ccb-avaprintdesigner` workspace 累积）

## 依赖 DAG

```
ITEM-1 (import-herdr)  ──┐
ITEM-2 (herdr open)    ──┼──→ ITEM-5 (workspace lifecycle)
ITEM-3 (doctor)        ──┼──→ ITEM-4 (projection 收尾)
                        │
                  (ITEM-1/2/3 可并行起步)
```

## 最终交付索引

| 子项 | 产物 | 类型 |
|---|---|---|
| ITEM-1 | 修复后的 `herdr_config_import.py` + 4 focused tests | code |
| ITEM-2 | 修复后的 `handlers_start.py` / `herdr_common.py` / `herdr_bootstrap.py` + `ccb8.cmd` 修复 + 5 focused tests + e2e smoke | code |
| ITEM-3 | `ccb doctor --output` herdr support_tier 字段 | code |
| ITEM-4 | items.yaml §12 accepted + docs/README 同步 | docs + yaml |
| ITEM-5 | namespace destroy workspace 清理 | code |

## 整体验收

- 全部 8 个 OCR 已核实代码缺陷有对应的修复 commit 和 focused test
- `ccb config import-herdr` 和 `ccb herdr open` 的核心路径缺陷清零
- `ccb doctor --output` 向用户展示 Herdr support tier
- roadmap §12 收尾
- 当前 Epic `windows-native-herdr-ccb` 的阻塞条件全部解除后，该 Epic 可重新进入
  final acceptance

## 遗留风险

- **Herdr API 稳定性**：Herdr socket API 仍在快速迭代。缓解：`HerdrSocketClient` 内置
  `EXPECTED_HERDR_API_SCHEMA` version gate，本 Epic 的修复不引入新的 API 依赖
- **ccb8.cmd 闪退根因未知**：ITEM-2 包含排查与修复，但根因可能不在 CCB 代码内
  （如 Herdr ConPTY、Windows wrapper 链路）。缓解：bootstrap socket 路径（`ccb herdr open`）
  已验证可用，闪退修复是增强而非阻塞
- **跨平台 env 修复的回归风险**：`herdr_command_env()` 的 XDG_* 平台 gate 修改可能影响
  非 Windows 平台上 Herdr 的行为。缓解：focused test 覆盖 Windows + Linux 两条路径

## 终态交付记录

- **Final acceptance review**：2 轮，通过（reviewer `ad96839e`）
- **Commit 链**：`8fc5094c` → `1118dc24` → `5aea5f08` → `19ff80f2` → `decadbd4` → `0a52d424`
- **OCR 缺陷闭环**：8/8（session `55e822c8` ×3 + session `3826db82` ×5）
- **测试覆盖**：46+ bootstrap/config_import + 134 backend_client + 10 doctor + 19 projection = 209+ pass
- **上游 Epic 解除阻塞**：`windows-native-herdr-ccb` 的 OCR findings 全部修复，可重新进入 final acceptance
