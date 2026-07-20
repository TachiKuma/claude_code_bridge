---
doc_type: feature-review
feature: 2026-07-06-rmux-capability-gate
status: blocked
reviewed: 2026-07-20
round: 2
lane_a_state: unavailable
lane_a_ref: ""
lane_a_reason: "review-fix implementation gates 已通过，但当前 Codex 工具面没有可调用的可见 Task agent reviewer；`ask` 是 provider 管道且不满足 agent-conventions 的 visible Task agent gate，OCR / CodeGraph / 主线程自审都不能替代环节 A。"
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "ocr CLI 和 ocr llm test 可用，但环节 A 不可用时 OCR 不能单独放行 review；当前 workspace 还包含 goal/runtime 状态与多轮 generated evidence，故本轮按 skipped-lane-a-unavailable 记录。"
---

# rmux-capability-gate 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-design.md`
- Checklist: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-scope-gate.json`
- DoD results: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-dod-results.json`
- Implementation evidence: `scripts/probe_rmux_capability.py`, `test/test_rmux_capability_probe.py`, latest capability report under `.codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064214Z-14748/`.
- Diff basis: working tree diff and untracked files.
- Review mode: full-rereview after review-fix
- Baseline dirty files: CodeStable runtime/goal/review state and generated roadmap draft artifacts are present in the same workspace; review findings below are scoped to `rmux-capability-gate`.

### Independent Review

- Detection: current Codex tool surface exposes `ask` and `ocr`, but no callable visible Task agent reviewer; `ocr llm test` passed.
- 环节 A 独立隔离 Task agent: unavailable for round 2 rerun.
- 环节 B OCR CLI: skipped-lane-a-unavailable; OCR cannot satisfy the mandatory spec-isolated Task agent lane.
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded.
- Merge policy: 环节 A 是 gate 必需项；本轮没有可消费的独立 reviewer findings，不得定稿 `passed`。
- Gate effect: `blocked` prevents QA / acceptance until round 2 code review is rerun in a host with visible Task agent reviewer support.

### Review-Fix Rerun Attempt

- Review-fix implementation scope: `scripts/probe_rmux_capability.py`, `test/test_rmux_capability_probe.py`, refreshed feature gate artifacts, and latest capability report under `.codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T064214Z-14748/`.
- Fresh verification before review rerun:
  - `python -m pytest -q test/test_rmux_capability_probe.py`: 10 passed.
  - `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml" --yaml-only`: passed.
  - `python "scripts/probe_rmux_capability.py" --work-root ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate"`: `probe_status=completed`, `blocking_gaps=5`.
  - `python -m pytest -q test/test_codex_pane_status_probe.py`: 37 passed.
  - `scope-gate`, `dod-runner`, and `evidence-pack`: passed.
- Current blocking condition: independent code review lane A cannot be launched from the current visible tool surface.

### Independent Review Recovery Attempts

- Earlier `ask` / foreground recovery attempts did not produce consumable findings for this feature: `claude`, `gemini`, `opencode`, `codex`, `qwen`, `codebuddy`, `copilot`, and `droid` either had no reply, unrelated reply, no active session, or pane not alive.
- CodeGraph MCP status check returned not initialized in the prior driver run; CodeGraph is not an independent Task agent reviewer and cannot satisfy lane A.
- Prior round 1 `task-agent:019f7e2b-affd-7283-8442-bffbbb46197f`: returned `changes-requested`; those findings drove the review-fix implementation. It is not a round 2 reviewer result and cannot close the current gate.

## 2. Diff Summary

- 新增：`scripts/probe_rmux_capability.py`, `test/test_rmux_capability_probe.py`, Rmux capability report/artifacts under roadmap drafts, implementation gate JSON/evidence pack.
- 修改：`rmux-capability-gate-checklist.yaml`, `goal-state.yaml`, this review report.
- 删除：none
- 未跟踪 / staged：未跟踪文件主要属于当前 feature evidence 或 implementation artifacts.
- 风险热点：Windows external process probing, report schema correctness, artifact redaction, parser-facing capture fidelity, route-approval fact quality.

## 3. Adversarial Pass

- 假设的生产 bug：probe 把“命令能跑”误当成“CCB 依赖语义成立”，从而让后续 route approval 消费不可信 capability facts。
- 主动攻击过的反例：命令依赖全 supported 但 session/pane/capture/cleanup 真实语义失败；非 Windows 或 rmux 缺失仍 `ok=true`；artifact stdout/stderr 含 JSON secret；cleanup command 失败却不影响 semantic status。
- 结果：升级为 REV-001 至 REV-006；实现必须回 review-fix。

## 4. Findings

### blocking

- [ ] REV-001 `scripts/probe_rmux_capability.py:376` semantic probe 不是语义验证，只是命令依赖推断。
  - Evidence: `_derive_semantics` 对除 capture fidelity 外的语义只检查依赖命令 status；最新 `artifacts/semantics/session_survival.json` 只记录 `dependencies` / `missing` / `status`。
  - Impact: design 明确要求“命令存在不等于语义满足”。`session_survival`、`namespace_isolation`、`pane_id_stability`、`buffer_paste` 等可能在真实 Rmux 行为不满足 CCB 语义时被标为 `supported`。
  - Expected fix scope: 每个 required semantic 至少执行一个真实场景断言；命令状态只能作为 prerequisite，不能直接推出 semantic `supported`。

- [ ] REV-002 `scripts/probe_rmux_capability.py:311` capture fidelity evidence 没有采集真实 Rmux capture，也无法证明 tmux / Rmux 输出平价。
  - Evidence: `_capture_fidelity_evidence` 只使用合成 raw 字符串；最新 `capture_format_fidelity_for_provider_completion.json` 中 wrapping / wide_char / last_n_tail 标为 `absorbed=false`，但没有真实 Rmux artifact 对比。
  - Impact: AC-005 要求 fixture 与 Windows 真机 artifacts 不可互替。当前实现既不能证明真实 Rmux 输出安全，也让 route approval 缺少可判定事实。
  - Expected fix scope: 将真实 `capture-pane` 输出按 raw bytes / decoded / consumer-strip / direct-stdout 落 artifact；对 wrapping、宽字符、OSC、last-N 做真实对比，再由观测结果计算 status。

- [ ] REV-003 `scripts/probe_rmux_capability.py:423` preflight 失败仍会产出 `probe_status=completed` 与 CLI `ok=true`。
  - Evidence: `_probe_preflight` 记录 platform/version returncode，但 `run_probe` 无条件继续；report 固定 `"probe_status": "completed"`；`main` 固定打印 `"ok": true` 并返回 0。
  - Impact: 非 Windows、`rmux` 缺失、`rmux -V` 失败时，DoD 仍可能假阳性通过，违反 design 中 preflight fail 要写 skipped/failed report 的契约。
  - Expected fix scope: 若 platform 非 Windows、version returncode 非 0、rmux executable 不可定位，report 写 `probe_status=skipped|failed`、可行动 reason，CLI 对 preflight hard fail 返回非 0 或至少 `ok=false`。

- [ ] REV-004 `scripts/probe_rmux_capability.py:33` redaction 对 JSON / quoted secret 形态漏报。
  - Evidence: `SECRET_RE` 只覆盖裸 `key=value` / `key: value` 后续 `\S+`，测试只覆盖 `token=sk-secret-value`。
  - Impact: artifacts 会写入 stdout/stderr；`{"password": "hunter2"}`、`"api_key": "..."` 等常见 JSON 形态可能进入 repo evidence。
  - Expected fix scope: 增加 JSON/quoted-key redaction 规则和测试；覆盖 `password/token/secret/api_key` 的 `:`, `=`, JSON string value、Bearer、sk/sess 之外的普通值。

### important

- [ ] REV-005 `scripts/probe_rmux_capability.py:493` cleanup 失败没有反馈到 report 语义。
  - Evidence: 最新 `artifacts/cleanup/kill-session.json` returncode 为 1，但 report 中 `kill_session_cleanup` 可由依赖命令推导为 `supported`。
  - Impact: QA / route approval 可能误以为 cleanup 已验证，实际 cleanup 结果只被附加到 artifact_index，未参与 semantic / gap / notes。
  - Expected fix scope: cleanup result 应进入 preflight / cleanup summary；若本次 session/window/pane 未能证明清理完成，`kill_session_cleanup` 至少 partial/unsupported 或带 explicit evidence note。

- [ ] REV-006 `scripts/probe_rmux_capability.py:197` 部分 command probe 参数会制造假阴性。
  - Evidence: `attach-session` 使用交互路径，`move-pane` source 与 target 相同，`refresh-client -S` 可能依赖 client 上下文；latest report 中这些命令出现 timeout / unsupported。
  - Impact: probe 可能把“scenario invalid”误判为 Rmux capability 缺失，污染后续 route approval facts。
  - Expected fix scope: 为交互/上下文敏感命令设计非交互验证路径；`move-pane` / `swap-pane` 创建两个 pane 后验证 identity 变化；unsupported 要区分 command missing 与 scenario invalid。

### nit

- [ ] REV-007 `test/test_rmux_capability_probe.py:80` capture evidence 测试只断言字段和失败维度标签，没有断言 parser 输出与 `absorbed` 语义一致。

### suggestion

- 增加轻量 schema validator，专门验证 `status` / `workaround` / `blocking_gaps` / `artifact_index` invariant，降低 evidence 有文件但不影响语义判断的漏网风险。

### learning

- `probe completed` 与 `route approved` 分离是正确方向；CMD-003 返回 0 且 `blocking_gaps=7` 本身不必然是失败。
- 在此宿主中运行 CodeStable Python 工具时，`PYTHONDONTWRITEBYTECODE=1` 可避免工具自重启吞掉输出。
- `codestable-dod-runner.py` 在 Windows 上捕获包含 Unicode 的子命令输出时，需要 `PYTHONUTF8=1`，否则可能触发 GBK 解码错误。

### praise

- command catalog 覆盖面完整，`artifact_index` 使用相对路径、size/hash、kind/probe/name，方向正确。
- 新增独立 probe 脚本符合不扩写旧 `probe_codex_pane_status.py` 的 SRP 约束。

## 5. Test And QA Focus

- QA 必须重点复核 latest report 的 5 个 gaps 是否来自真实 Rmux 缺失，还是仍有 probe 参数 / 场景设计造成的假阴性。
- 已新增并通过 preflight hard-fail 测试：非 Windows、`rmux -V` 返回非 0 时不能 `probe_status=completed` + `ok=true`；真实 rmux 缺失路径由 CLI hard-fail 保护。
- 已新增并通过 semantic 场景断言测试：依赖命令全 supported 但语义断言失败时，semantic 会变成 `partial` 并进入 gap。
- 已新增并通过 capture fidelity 真实 artifact 校验：capability evidence 记录 real Rmux capture raw bytes digest / decoded / consumer-strip / direct-stdout observation，不再只保留合成 fixture。
- 已新增并通过 redaction 测试：JSON secret、quoted key、普通 password 值、Bearer 均覆盖。
- Evidence pack residual risks / gate warnings：provider helpers skipped by evidence-pack; no provider warning.
- 不能靠 review 完全确认的点：round 2 独立 reviewer 未启动；QA 前必须先在可见 Task agent reviewer 宿主中完成 round 2 code review。

## 6. Residual Risk

- Round 1 独立 reviewer 没有执行 pytest / Windows probe；round 2 独立 reviewer 未启动，因此本报告不能把 review-fix 标为 passed。
- CodeGraph 未初始化，结构化调用图不可用；本轮按文件与相邻代码定点读取完成核验。
- 当前 workspace 混有大量未提交 goal/evidence 状态；review 结论只归因到 `rmux-capability-gate` 的实现与证据。

## 7. Verdict

- Status: blocked
- Next: 在具备可见 Task agent reviewer 的宿主中恢复 round 2 `cs-code-review`；review passed 后才能进入 Goal QA。Goal mode 不得用 OCR、CodeGraph、`ask` provider pipe 或主线程 self-review 替代环节 A。

## 8. Focused Closure

none
