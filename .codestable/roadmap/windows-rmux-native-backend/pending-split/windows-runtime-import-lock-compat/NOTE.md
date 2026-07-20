# 待拆分 feature：windows-runtime-import-lock-compat

## 来源

从 `ccbd-control-plane-transport-seam` 的工作区中拆出的**越界改动**。Owner 决定（2026-07-20）：
这批 Windows 运行时兼容改动不属于 ccbd control-plane transport seam 的已审查 scope
（见该 feature `scope-gate.json` 的 `allowed_prefixes`），应作为独立 feature 走完整流程。

原 feature 因此不依赖本批改动即可收尾：CMD-005 按 checklist `failure_handling: document-baseline`
记为已文档化基线，AF_UNIX-on-Windows 原生传输交给下一个 roadmap feature
`ccbd-windows-tcp-loopback-transport`。

## 改动内容（已保存为 `compat-changes.patch` + `tests/`）

| 文件 | 改动 |
|---|---|
| `lib/mobile_gateway/terminal.py` | `fcntl`/`pty`/`termios` 从模块顶层改为延迟局部 import，使模块可在 Windows 被 import（解 CMD-005 collection blocker） |
| `lib/storage/locks.py` | `file_lock` 增加 Windows `msvcrt.locking` 分支，非 Windows 保持 `fcntl.flock`；fcntl 缺失时降级为无锁 yield |
| `lib/maintenance_heartbeat/lock.py` | `MaintenanceHeartbeatLock` 增加 Windows `msvcrt` 非阻塞加锁分支 |
| `lib/storage/atomic.py` | 无 `os.O_DIRECTORY`（Windows）时走 by-path 原子写回退路径，跳过目录 fsync |
| `test/test_mobile_gateway_terminal_import.py` | 新增：terminal 模块在无 fcntl 下可 import 的 guard |
| `test/test_maintenance_heartbeat_import.py` | 新增：heartbeat lock 模块 import guard |

## 已验证事实（拆出前的只读核验）

- 两个 import guard 测试：`2 passed`。
- 应用本批改动后重跑 CMD-005（`test_v2_start_service.py` + `test_v2_phase2_entrypoint.py -k "ccbd or socket or endpoint or ping"`）：
  fcntl collection blocker **已解除**（能 collect），但 **10 个 v2 phase2 集成测试在 Windows 硬失败**
  （`RuntimeError: unix domain sockets are not supported on this platform`），2 passed。
  → 结论：本批只解决 import/collection 层；AF_UNIX-on-Windows 的运行时能力需 `ccbd-windows-tcp-loopback-transport`。

## 拆分风险点（新 feature design 需覆盖）

- **锁语义**：`msvcrt.locking` 与 `fcntl.flock` 语义不同（前者按字节区间/文件指针，非咨询锁、可能阻塞或 `LK_NBLCK` 抛 `OSError`）。
  跨平台加锁的并发正确性、异常路径、锁范围（当前对 1 字节加锁）需单独 design + 测试。
- **原子写回退**：Windows 无目录 fsync 时的持久性保证弱化，需在 design 中明确 durability 契约与可接受性。
- 属于并发/持久化高风险语义，**不 quick-eligible**，新 feature 至少走 Standard lane（含 design gate）。

## 恢复方式

```
git apply .codestable/roadmap/windows-rmux-native-backend/pending-split/windows-runtime-import-lock-compat/compat-changes.patch
cp .../tests/*.py test/
```

然后以 `cs-feat` 新建独立 feature（建议 slug `windows-runtime-import-lock-compat`）走 design → review → impl → QA → accept。
