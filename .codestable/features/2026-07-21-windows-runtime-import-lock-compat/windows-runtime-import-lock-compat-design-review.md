---
doc_type: feature-design-review
feature: 2026-07-21-windows-runtime-import-lock-compat
status: passed
review_state: passed
review_reason: ""
reviewer_id: "a832b8889ad32f50b"
reviewed: 2026-07-21
round: 2
---

# windows-runtime-import-lock-compat feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-21-windows-runtime-import-lock-compat/windows-runtime-import-lock-compat-design.md`
- Checklist: `.codestable/features/2026-07-21-windows-runtime-import-lock-compat/windows-runtime-import-lock-compat-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: 非 items 条目；来源 `pending-split/windows-runtime-import-lock-compat/`
- Related docs: goal-protocol §3.1、ccbd-control-plane-transport-seam 验收产物、NOTE.md 实现草案 patch
- Code facts checked: lib/storage/locks.py、lib/maintenance_heartbeat/lock.py、lib/storage/atomic.py、lib/mobile_gateway/terminal.py、lib/provider_core/runtime_lock.py、lib/provider_core/platform_info.py、test/test_storage_atomic.py、test/test_maintenance_heartbeat.py（独立 reviewer + 主 agent Explore 双核验）

### Independent Review

- Status: round-1 + round-2 completed
- Detection: independent-agent
- Provider / agent: Task agent `a832b8889ad32f50b`（同一独立 reviewer 完成 round-1 审查与 round-2 闭合复审）
- Raw output: round-1 findings 6 条（见 §3）；round-2 逐条判定 I-1/I-2/I-3/I-4/N-1/R-1 = closed、S-1 = accepted，无新引入 correctness 问题，verdict 建议 passed
- Merge policy: round-1 findings 全部经主 agent 对照 atomic.py/locks.py/lock.py/terminal.py 事实核验成立并修订闭合；round-2 独立复审确认闭合；4 处旧措辞 nit 与 R-1 enforcement 已由主 agent 顺手同步（Top-3 风险#2、§1 假设、§3.5 措辞；新增 DOD-ACCEPT-001 + check）
- Gate effect: round-2 passed，无 unresolved blocking/important

## 2. Design Summary

- Goal: 四运行时模块原生 Windows 可 import + 跨平台文件锁/原子写，Unix 零漂移；修复 CMD-005 fcntl collection 根因
- Key contracts: 对外签名/异常类型不变；platform_info.is_windows() 统一判定；对齐 ProviderLock msvcrt 手法不合并
- Steps: 5；Checks: 8（均标 design/AC/DOD 来源）
- Baseline / validation: compileall + storage/heartbeat/新测试 + CMD-005 collection

## 3. Findings（round-1 独立审查，主 agent 已本地核验）

### blocking

- none（无纯 blocking 级设计错误）

### important（均已核验成立并在修订稿闭合）

- [x] FDR-001 `atomic.py:84,70,24,17` **I-1（近 blocking）**：`atomic_write_text` 无条件先调 `ensure_durable_directory`，其创建缺失目录时经 `_fsync_directory→_open_directory` 在 Windows 抛 `NotImplementedError`；`ensure_durable_directory` 亦被 `frontdesk_direct_handoff.py:52,97` 直接调用。挂载点漏列该门控。
  - Evidence: 核验 atomic.py 调用链属实；patch 已给 `_fsync_directory` 加早返回但 design 未列。
  - 闭合：新增决策 D-DIRSYNC（§1.7），§2.1/§2.3 挂载点补 `_fsync_directory` Windows 门控，AC-006 增"父目录不存在需创建"，step 2 覆盖。
- [x] FDR-002 `test_storage_atomic.py:78,100,118,137,211,229,252` **I-2**：依赖 dir-fsync 的是一簇 6-8 个测试，非单条；Windows 跑该文件会红。
  - Evidence: 核验测试文件属实。
  - 闭合：AC-007/AC-008、step 2 改为"整簇加 Unix-only skip 守卫，Windows skip 而非 fail"。
- [x] FDR-003 `locks.py:11` **I-3**：`open('a+')` 指针在 EOF，未 seek(0) 则锁区间随文件大小漂移致互斥静默失效；ProviderLock 有 `os.lseek(fd,0,SEEK_SET)`。
  - Evidence: 核验 locks.py / runtime_lock.py:61,72 属实。
  - 闭合：§2.2 写死"seek(0) 锁固定 byte-0，不可用 append 位置"，AC-002 增"两 acquirer 文件大小不同"。
- [x] FDR-004 `lock.py:24-27` **I-4**：busy 判定应作用域收窄优先（try/except 紧包 msvcrt.locking 单点）、errno 为辅；Windows 竞争常抛 `EDEADLOCK`(36)，原 errno 集合 {EACCES,EDEADLK} 可能漏。
  - Evidence: 核验属实。
  - 闭合：§1.5 改为"作用域收窄优先，errno 白名单 {EACCES,EDEADLOCK,EDEADLK} 为辅，impl 实测校准"。

### nit

- [x] FDR-005 **N-1**：仅 terminal.py + heartbeat.lock（顶层 fcntl）真 import 失败；locks（惰性 fcntl）/atomic（无 fcntl）基线即可 import，AC-001 对这 2 个是绿灯误证。
  - 闭合：§1 成功标准与 AC-001 区分 import-safe vs functional。

### suggestion

- [x] FDR-006 **S-1**：`terminal.py::_resize` 无调用者、`_master_fd` 从不赋值 = 死代码；惰性 import 把 import 藏进死代码。
  - 处置：保守惰性 import（行为等价、scope 克制），死代码清理记为 §2.5 cs-refactor 观察。

### learning

- goal-protocol §3.1（`goal-protocol.md:63`）逐字点名本 blocker `mobile_gateway.terminal -> import fcntl` 为不受 AF_UNIX residual 豁免的目标平台核心阻塞，本 feature scope 与 goal 恢复条件严格对齐。

### praise

- D-SENTINEL 已实证（49 处均锁专用 .lock，RMW 读写其它 .json，无消费方读锁文件内容）。
- D-REUSE 不并入 ProviderLock 理由成立（heartbeat 锁文件承载 JSON 状态，与 ProviderLock 写 PID 冲突）。
- D-BLOCK 成立（49 处均锁内 RMW，依赖等到取锁）。

### residual-risk

- [x] R-1：D-DURABLE 弱化触及崩溃恢复 journal 完整性（frontdesk handoff `recover_*` 崩溃回读），属正确性相邻后果。
  - 闭合：§1.6/§4 加"崩溃恢复 journal"措辞，要求 acceptance 时 owner 按 §3.1 在 approval-report 落盘接受该弱化。

## 4. User Review Focus

- 用户需重点拍板：**D-REUSE**（不并入 ProviderLock，仅对齐手法）、**D-DURABLE**（Windows 事务/崩溃恢复链路 durability 弱化的可接受性，需按 §3.1 落盘接受）
- implement 需重点遵守：Unix 分支逐字不变、D-BLOCK 阻塞重试锁固定 byte-0、D-EXC 作用域收窄、D-DIRSYNC 门控、test_storage_atomic 整簇 Unix-only skip
- QA / acceptance 需重点复核：Windows 并发互斥证据（含不同文件大小）、durability 弱化边界的 owner 落盘

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | §3.3 覆盖 AC-001..010，均映射 step | none |
| DoD Contract | pass | E | §3.4 覆盖 Impl/Review/QA + Validation Commands | none |
| Steps and checks traceability | pass | E | checklist steps 独立可验、checks 标来源 | none |
| Roadmap contract compliance | pass | C | 非 items 条目；解 §3.1 点名 blocker，scope 对齐 | none |
| Module interface design | n/a | E | 无新增对外 interface，仅平台分支 helper | none |
| Validation and artifacts | pass | E | compileall + 测试 + CMD-005 collection | round-2 确认 |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- D-DURABLE：Windows 崩溃恢复 journal 弱化——须 owner acceptance 落盘（§4），QA/accept 复核。
- D-EXC errno 集合需 impl 实测校准（已前置为 step 4 退出信号）。

## 7. Verdict

- Status: passed（round-2 独立复审确认全部 findings 闭合，无 blocking/important 残留）
- Next: 交给用户整体 review（design gate，Standard lane 不自动 approve）；owner 确认后 `status: approved` 并进入 implementation

## 8. Focused Closure

- none（round-1 findings 经修订走完整 round-2 独立复审，非 focused closure）
