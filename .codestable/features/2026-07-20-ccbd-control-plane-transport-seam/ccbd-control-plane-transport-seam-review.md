---
doc_type: feature-review
feature: 2026-07-20-ccbd-control-plane-transport-seam
status: passed
reviewer: subagent+ocr
reviewed: 2026-07-20
round: 5
lane_a_state: completed
lane_a_ref: "019f7f76-7b08-7670-8f9e-3ef26a03a7a2"
lane_a_reason: ""
lane_b_state: completed
lane_b_ref: "ocr-session:5588d845-1688-4ce2-92cd-b34879257870"
lane_b_reason: ""
---

# ccbd-control-plane-transport-seam 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-scope-gate.json`
- DoD results: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-dod-results.json`
- Implementation evidence: checklist steps all `done`; implementation gate evidence refreshed after review-fix.
- Diff basis: 当前 unstaged/untracked 工作区 diff；无 staged diff。
- Review mode: full-rereview after material review-fix
- Baseline dirty files: none

### Independent Review

- Detection: `multi_agent_v1` 可用，OCR CLI 可用。
- 环节 A 独立隔离 Task agent: completed，latest reviewer `019f7f76-7b08-7670-8f9e-3ef26a03a7a2`。
- 环节 B OCR CLI: completed，latest session `5588d845-1688-4ce2-92cd-b34879257870`。
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded。
- Merge policy: 五轮完整复审与 OCR findings 已逐条本地核验；最终轮无 OCR comments，Task reviewer verdict `passed`。
- Gate effect: `reviewer: subagent+ocr`，无 unresolved blocking / important。

## 2. Diff Summary

- 新增：`lib/ccbd/control_plane_transport/*`，`test/test_ccbd_control_plane_transport_*.py`，`test/test_ccbd_socket_server.py`
- 修改：ccbd socket client/server runtime、lease/lifecycle/mount/ownership/inspection/ping/doctor endpoint projection、bootstrap/lifecycle/socket tests、feature checklist、goal-state。
- 删除：none
- 未跟踪 / staged：新增文件均属于当前 feature scope；无 staged diff。
- 风险热点：control-plane transport seam、Unix bootstrap readiness、lease/diagnostics endpoint projection、fake transport contract、平台兼容边界。

## 3. Adversarial Pass

- 假设的生产 bug：socket wrapper、legacy endpoint record 或 fake transport 与真实 socket 语义不一致，导致后续 Windows adapter 或 Unix bootstrap 被误验证。
- 主动攻击过的反例：`select.select()` wrapper fd、legacy `{"socket_path": ...}` fallback、blank/whitespace endpoint path、fake bootstrap nonce contract、fake closed listener/connectability、lease/ping/lifecycle/doctor projection、Unix endpoint path 与 constructor legacy path 不一致。
- 结果：前四轮发现的 blocking/important 已通过 review-fix 关闭；第五轮未发现 blocking/important。

## 4. Findings

### blocking

- none

### important

- none

### nit

- none

### suggestion

- `lib/ccbd/control_plane_transport/fake.py` fake transport 当前按 one-shot listener 使用；若后续测试需要 `shutdown()->listen()` 重启同一 fake transport，可只在 fake 内重建 listener 或显式声明 one-shot。

### learning

- 包装 socket 后若继续参与 `select.select()`，listener protocol 需要包含 `fileno()`，否则 Unix bootstrap 会在 publish 前失败。
- fake transport 必须保留真实协议不变量；bootstrap nonce 格式、recv EOF/timeout、closed listener 行为都需要测试锁定。

### praise

- `RpcRequest` / `RpcResponse` JSON-line frame 与 handler dispatch 未漂移。
- `AF_UNIX` 生产使用收敛在 Unix adapter与既有 `ccbd.system` helper；未实现 Windows TCP adapter。
- ownership 默认 liveness 已改为 endpoint-first，同时保留显式注入旧 `socket_probe(socket_path)` 的测试兼容面。

## 5. Test And QA Focus

- QA 必须重点复核：endpoint descriptor canonical-first、legacy `socket_path` record fallback、Unix listener `fileno()` / bootstrap endpoint path、fake bootstrap nonce 与 closed/connectability 语义、lease/ping/doctor endpoint projection。
- Evidence pack residual risks / gate warnings：CMD-005 在 Windows 因 `mobile_gateway.terminal -> fcntl` collection baseline 失败；按 checklist `failure_handling=document-baseline` 记录，不视作本 feature 新失败。
- 建议新增或加强的测试：none blocking；后续如使用 fake restart lifecycle，可增加 fake one-shot / restart contract 测试。
- 不能靠 review 完全确认的点：当前 Windows 环境跳过真实 AF_UNIX bootstrap/lifecycle 用例，需 Unix CI/真机复跑。

## 6. Residual Risk

- Windows 本机 CMD-005 仍因既有 `mobile_gateway.terminal -> fcntl` collection error 失败，start/ping/doctor 抽样命令无法在本环境完整执行。
- 真实 Unix AF_UNIX bootstrap、stale cleanup、deferred external connection 仍需要在 Unix 环境复核；当前 Windows 证据中相关测试为 skip。

## 7. Verdict

- Status: passed
- Next: 进入 `cs-feat` QA 阶段。

## 8. Focused Closure

- none; review-fix 改动包含生产代码，已按协议进行完整复审至 round 5。
