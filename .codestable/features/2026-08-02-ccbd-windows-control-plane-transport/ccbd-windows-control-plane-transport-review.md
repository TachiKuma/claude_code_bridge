---
doc_type: feature-review
feature: 2026-08-02-ccbd-windows-control-plane-transport
status: blocked
reviewed: 2026-08-02
round: 1
lane_a_state: unavailable
lane_a_ref: ""
lane_a_reason: "当前 Codex 宿主未暴露可见独立 Task agent；按 CodeStable review gate，首次完整审查不能由主 agent 自审放行。"
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "OCR CLI 可用，但当前工作区混有其它 feature 的 dirty/untracked 改动，ocr review 只有 workspace/range 模式且无 include-only 文件列表；裸跑会越过本 feature scope。"
---

# ccbd-windows-control-plane-transport 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md`
- Checklist: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-checklist.yaml`
- Evidence pack: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-evidence-pack.md`
- Gate results: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-scope-gate-results.json`
- DoD results: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-dod-results.json`
- Implementation evidence: 当前 goal run 的 implementation gate 与 fresh command 输出。
- Diff basis: 工作区 diff，限定到 control-plane transport、socket client/server seam、诊断投影、focused tests、当前 feature 产物和 gate runner Windows 兼容修复。
- Review mode: initial。
- Baseline dirty files: 工作区存在其它 feature/roadmap 历史改动，本报告未审查且不得计入本 feature verdict。

### Independent Review

- Detection: 当前宿主没有原生 Task agent 工具；`ocr llm test` 通过，provider 为 OpenAI 兼容端点。
- 环节 A 独立隔离 Task agent: local-only + unavailable。
- 环节 B OCR CLI: skipped。
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded。
- Merge policy: 环节 A 未完成，不能写 `reviewer: subagent`，不能定稿 `passed`。
- Gate effect: blocks final verdict until an independent Task agent review is supplied or owner explicitly approves local-only fallback.

## 2. Diff Summary

- 新增：`lib/ccbd/control_plane_transport/*`，`test/test_ccbd_control_plane_transport_*`，`test/test_ccbd_windows_tcp_loopback_*`，当前 feature gate/evidence 产物。
- 修改：`lib/ccbd/socket_client_runtime/transport.py`，`lib/ccbd/socket_server_runtime/*`，ccbd endpoint diagnostics 投影，focused bootstrap/server/client tests，CodeStable gate runner Windows 兼容性。
- 删除：none。
- 未跟踪 / staged：当前 feature 新增目录与测试文件为 untracked；未 staged。
- 风险热点：Windows token ACL 权限证明、handler 前认证、bootstrap 自探测时序、scope boundary。

## 3. Adversarial Pass

- 假设的生产 bug：Windows token ACL proof 或 listener accept 时序存在漏判，导致 endpoint 发布但 client 连接不可用或坏 token 进入 handler。
- 主动攻击过的反例：bad token、missing/unreadable token、ACL proof 不可解析、slow preauth client、stale endpoint、Unix AF_UNIX regression、diagnostics token redaction。
- 结果：这些场景已有 focused tests 和 DoD evidence；但缺独立 reviewer 复核，不能升级为 review passed。

## 4. Findings

### blocking

- [ ] REV-001 `review gate` 缺少必需的独立 Task agent review。
  - Evidence: 当前宿主未暴露可见 Task agent 工具；`cs-code-review` / `independent-review` 要求首次完整审查的环节 A 为 gate 必需。
  - Impact: Goal feature 不能进入 QA；否则会跳过 CodeStable 独立审查硬门。
  - Expected fix scope: 提供可见独立 reviewer run/result，或由 owner 按 approval conventions 显式批准 local-only fallback 后重跑 review gate。

### important

none

### nit

none

### suggestion

none

### learning

- `codestable-dod-runner.py` 在 Windows 上需要固定 UTF-8/replace 输出处理，否则 pytest 中的非 ASCII 输出会让 gate 自身崩溃。
- `codestable-scope-gate.py` 在 Windows shell 下不能用单引号拼 pathspec；会导致 changed files 被漏检。

### praise

none

## 5. Test And QA Focus

- QA 必须重点复核：Windows TCP listener valid/bad token、ACL fail-fast、不发布 unprotectable endpoint、bootstrap self-ping 走同一 transport、diagnostics token redaction、Unix AF_UNIX regression。
- Evidence pack residual risks / gate warnings：CMD-006 是既有 Windows `fcntl` collection baseline；scope-gate 中 `.codestable` 文档/工具的 `TODO/FIXME/XXX` 命中是规则文本 false positive，不是新增临时标记。
- 建议新增或加强的测试：独立 reviewer 返回前不新增。
- 不能靠 review 完全确认的点：Native Windows CMD-013 已不再失败于 AF_UNIX unsupported，但当前 transcript 进入后续 namespace/reset 确认或 lifecycle 层失败，需要后续 feature 继续处理。

## 6. Residual Risk

- 独立审查未完成；本 feature 当前只能停在 review gate。

## 7. Verdict

- Status: blocked
- Next: 提供独立 Task agent reviewer 结果后重跑 `cs-code-review`；或 owner 明确批准 local-only fallback，再由主流程按协议消费该 approval。

## 8. Focused Closure

none
