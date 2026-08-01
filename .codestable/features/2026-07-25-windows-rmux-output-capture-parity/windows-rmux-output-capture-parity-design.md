---
doc_type: feature-design
feature: 2026-07-25-windows-rmux-output-capture-parity
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: windows-rmux-output-capture-parity
brainstorm: .codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-brainstorm.md
execution_lane: goal
status: approved
summary: 以证据优先方式验证 Windows/rmux output capture parity，区分 machine capture、provider completion 和 user-visible history
tags: [windows, rmux, wezterm, output, capture, completion, parity, evidence, epic-child]
---

# windows-rmux-output-capture-parity feature design

## 0. 术语约定

| 术语 | 定义 | 防冲突结论 |
|---|---|---|
| machine capture parity | 后端 `RmuxBackend.capture_pane()` 在 Windows/rmux 下对 plain、ANSI、宽字符、wrapping、尾部空白、line range、raw bytes 的机器可重复证据。 | 不等同于 WezTerm 前台滚轮或 GUI scrollback。 |
| provider completion parity | provider completion detector 消费 rmux capture/log 文本后仍能给出与 baseline 等价的 completion 判定。 | 不通过修改 provider parser 来适配不稳定 capture。 |
| user-visible history | 用户在 native Windows + WezTerm 前台能否回看输出的手工或 live transcript 证据。 | 只作为 UX supporting evidence，不能替代 machine capture 或 provider completion。 |
| documented delta | tmux baseline 与 Windows/rmux 之间被明确分类、解释并记录 artifact 的差异。 | 允许非字节级完全一致，但不允许未分类漂移。 |
| output_capture parity dimension | roadmap §4.1 `WindowsRmuxUxParityEvidence.parity_dimension` 的本 feature 固定值。 | 最终证据 JSON 必须写 `output_capture`。 |

Brainstorm admission：`.codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-brainstorm.md` 已 `confirmed`，owner 已批准采用 **parity evidence first** 进入 design。

## 1. 决策与约束

### 需求摘要

本 feature 不默认重写 Rmux IO，而是在已 accepted 的 `rmux-send-capture-logging` 基线之上，建立 Windows/rmux/WezTerm output capture parity 的机器可读证据矩阵。目标是证明或归因三条路径的边界：

- machine capture：真实 `RmuxCaptureResult` 或等价 fixture/report 能覆盖 raw bytes、ANSI、宽字符、wrapping、尾部空白和 range。
- provider completion：现有 completion detector 对 rmux capture/log 文本保持可消费，或差异被分类。
- user-visible history：WezTerm 前台回看只作为 supporting evidence，不替代后端 capture。

成功标准：

- 产出 `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/evidence/output-capture-parity-report.json`，其中每个 case 符合本 design 固定的 `RmuxCaptureParityCase`：保留 raw 与 normalized 两份 artifact ref，并记录 expected/normalized hash。
- 产出 `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/evidence/windows-rmux-ux-parity-evidence.json`，符合 roadmap §4.1 `WindowsRmuxUxParityEvidence`，且 `parity_dimension=output_capture`。
- 对 Linux/macOS tmux baseline 与 Windows/rmux output capture 的差异进行 `pass | known_delta | product_bug | provider_failure | terminal_scrollback_only | blocked` 分类。
- provider completion fixture 投影必须证明 Codex、Claude、AGY、DeepSeek/session snapshot 等代表性 family 对 capture/log 文本仍可消费，或明确归因。
- native Windows + WezTerm 前台不可用时，user-visible history 只能标 `blocked` 或 `partial`，不能把 headless transcript 记为 GUI pass。

明确不做：

- 不默认重写 `RmuxBackend.capture_pane()`、`rmux_backend_runtime/io.py` 或 Rmux CLI/SDK 调用层。
- 不重复实现 `capture_pane`；只在证据显示生产缺口时，把缺口转为后续实现步骤。
- 不把用户滚轮、WezTerm scrollback 或手工回看当作 machine capture / provider completion 证据。
- 不修改 provider completion parser 来适配不稳定 capture。
- 不把真实 provider auth、quota、credential failure 归为 rmux capture parity failure。
- 不把 Linux/macOS tmux backend 默认值纳入本 feature 的行为变更。

### Baseline reuse / delta

复用 baseline：

- `rmux-send-capture-logging` acceptance 已确认 `RmuxBackend.capture_pane()`、`raw_bytes`、ANSI mode、`trim_policy=preserve`、logging bridge 和 provider completion fixtures。
- `test/test_rmux_send_capture_logging.py` 已覆盖 capture policy、raw bytes、line range、ANSI 和 logging builder。
- `test/test_rmux_completion_capture_fixtures.py` 已覆盖 completion detector 对 rmux capture/log 文本形态的兼容性。

本 feature 增量：

- 把现有 accepted baseline 投影成 UX parity evidence，而不是只保留 acceptance Markdown。
- 刷新 tmux baseline 与 Windows/rmux case 矩阵，按 input kind、artifact、hash、verdict 和 delta 分类记录。
- 为 user-visible history 增加 runbook/证据引用，但严格标注 supporting evidence。
- 把 report 汇总为 roadmap §4.1 所需 `windows-rmux-ux-parity-evidence.json`。

### 复杂度档位

- 行为兼容 = L3。capture/log 输出直接影响 provider completion 和用户验收，必须可证伪。
- 外部依赖 = mixed。核心 fixture/report 可 headless 运行，native Windows + WezTerm 前台证据是 live/manual supporting lane。
- 可测试性 = verified。JSON schema、fixtures、hash、enum、artifact refs 和 detector 投影均可测试。
- 数据完整性 = high。raw/normalized artifact、hash 和 delta 分类不能由自由文本替代。

### Top 3 风险与缓解

1. **风险：把已 accepted 的 IO baseline 误判为未完成，导致无证据重写。**  
   缓解：第一步先做 baseline inventory，report 中必须引用 `rmux-send-capture-logging` acceptance 和相关 tests。
2. **风险：用户可见 scrollback 与 machine capture 混淆。**  
   缓解：证据 schema 分三条 lane；`terminal_scrollback_only` 不能升级为 capture pass。
3. **风险：差异被“基本一致”掩盖。**  
   缓解：每个 case 必须有 raw artifact、normalized hash、expected hash、verdict 和 delta classification。

### 非显然依赖与关键假设

- 依赖 `windows-rmux-wezterm-native-interaction-parity` 的 design-review 已通过；但实现前仍需按 parent roadmap 确认依赖实际状态。
- 如果 `windows-rmux-wezterm-native-interaction-parity` 尚未 accepted，本 feature implementation 只能推进 headless machine/provider lanes；user-visible history 必须记录为 `blocked` 或 `partial`，不能作为 GUI pass。
- 假设现有 provider completion fixtures 可以作为 parser compatibility baseline；本 feature 只补真实 `RmuxCaptureResult` 投影或 parity report，不重写 detector。
- 假设 Linux/macOS tmux baseline 是强 baseline，但 Windows/rmux documented delta 可以被接受，只要有分类和 residual risk。
- native Windows + WezTerm GUI 不可用时，core machine/provider lanes 仍可给出 `partial` 或 `blocked` evidence，不能伪造 GUI evidence。

## 2. 名词与编排

### 2.1 名词层

#### 现状

- `lib/terminal_runtime/rmux_backend_runtime/io.py::capture_pane()` 返回 `RmuxCaptureResult`，包含 `text`、`raw_bytes`、`start_line`、`end_line`、`ansi_mode`、`trim_policy`、`diagnostics`。
- `lib/terminal_runtime/rmux_backend.py::RmuxBackend.capture_pane()` 已暴露 backend method，并由 `test/test_rmux_send_capture_logging.py` 覆盖 ANSI、raw bytes、range 和 diagnostics。
- `test/test_rmux_completion_capture_fixtures.py` 当前通过 `_rmux_capture_text()` 构造 capture-like 文本喂给 completion detectors，证明 parser compatibility，但还没有形成 roadmap §4.3 的 parity report。
- roadmap §4.1 要求每个 UX parity feature 产出 `windows-rmux-ux-parity-evidence.json`；§4.3 要求 output/capture case 记录 `RmuxCaptureParityCase`。

#### 变化

新增 evidence-only contract，不改变 production IO surface：

```python
class OutputCaptureDelta(TypedDict):
    classification: Literal[
        "pass",
        "known_delta",
        "product_bug",
        "provider_failure",
        "terminal_scrollback_only",
        "blocked",
    ]
    failure_class: Literal[
        "none",
        "rmux_unavailable",
        "wezterm_gui_unavailable",
        "provider_failure",
        "system_failure",
        "test_design_failure",
        "unsupported_capability",
    ]
    explanation: str

class RmuxCaptureParityCase(TypedDict):
    case_id: str
    input_kind: Literal["plain_text", "ansi", "wide_char", "wrapped_line", "provider_completion"]
    expected_text_sha256: str
    capture_command: str
    normalized_output_sha256: str
    raw_artifact: str
    normalized_artifact: str
    verdict: Literal["pass", "partial", "failed"]

class ProviderProjectionEvidence(TypedDict):
    status: Literal["pass", "partial", "failed", "blocked"]
    detector_ref: str
    artifact_ref: str
    failure_class: Literal[
        "none",
        "provider_failure",
        "system_failure",
        "test_design_failure",
    ]
    explanation: str
```

Report shape：

```python
class OutputCaptureParityReport(TypedDict):
    schema_version: Literal[1]
    baseline_refs: list[str]
    cases: list[RmuxCaptureParityCase]
    deltas: dict[str, OutputCaptureDelta]
    provider_projection: dict[str, ProviderProjectionEvidence]
    user_visible_history: dict[str, object]
```

示例：

```json
{
  "case_id": "ansi-preserve-final-newline",
  "input_kind": "ansi",
  "expected_text_sha256": "sha256:...",
  "capture_command": "rmux capture-pane -p -e -S -50 -E -1",
  "normalized_output_sha256": "sha256:...",
  "raw_artifact": "evidence/cases/ansi-preserve-final-newline.raw",
  "normalized_artifact": "evidence/cases/ansi-preserve-final-newline.normalized.txt",
  "verdict": "pass"
}
```

##### Interface 设计检查

- Module：证据产物放在 feature `evidence/`，生产代码不因本 design 新增 adapter。
- Interface：supportability 和 roadmap acceptance 消费 JSON record，不消费自由 Markdown。
- Seam：seam 放在 QA/acceptance artifact 层；只在 evidence runner 需要时读取 `RmuxCaptureResult`。
- Depth / locality：output_capture 是 deep evidence dimension，但第一版保持 evidence-first，避免把测试归因和生产 IO 修改耦合。
- Dependency strategy：local-substitutable；fixture 可在无真实 rmux 时跑，live Windows/rmux/WezTerm lane 单独 blocked/partial。
- Adapter：无 production adapter；如后续发现 product bug，再在 implementation design 内明确生产改动边界。

### 2.2 编排层

本 feature 是简单线性证据管线，不需要复杂状态机图。

1. 读取 accepted baseline：`rmux-send-capture-logging` design/acceptance、相关 tests、当前 `RmuxCaptureResult` contract。
2. 定义 parity case schema 和 JSON validator，覆盖 required fields、enum、hash、raw artifact ref、normalized artifact ref、partial/blocked residual risk。
3. 生成或整理 machine capture cases：plain、ANSI、wide char、wrapped line、provider completion。
4. 把 cases 投影到 provider completion detectors，记录 provider family pass/partial/failed/blocked。
5. 记录 user-visible history runbook：native Windows + WezTerm GUI 可用时运行；不可用时明确 blocked/partial，不污染 machine/provider lanes。
6. 汇总为 `windows-rmux-ux-parity-evidence.json`，并填入 artifacts、failure_class、residual_risks。

错误与归因语义：

- `rmux_unavailable`：rmux binary/daemon/capability 不可用，machine capture lane blocked。
- `wezterm_gui_unavailable`：GUI 前台证据不可用，只影响 user-visible history lane。
- `provider_failure`：provider fixture 或真实 provider auth/quota/credential 失败，不归为 rmux capture bug。
- `test_design_failure`：fixture/schema/runner 本身无法证明目标。
- `system_failure`：环境、文件、权限或命令异常。
- `unsupported_capability`：rmux capability 缺失导致某 case 不可执行。

### 2.3 挂载点清单

- `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/evidence/output-capture-parity-report.json`：本 feature 的细粒度 parity case report。
- `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/evidence/windows-rmux-ux-parity-evidence.json`：roadmap §4.1 汇总 evidence record。
- `.codestable/features/2026-07-25-windows-rmux-output-capture-parity/evidence/user-visible-history-runbook.md`：WezTerm 前台回看 supporting evidence。
- `test/test_rmux_send_capture_logging.py`：如需要，只新增 evidence/report 投影测试，不重写 capture implementation。
- `test/test_rmux_completion_capture_fixtures.py`：如需要，只新增真实 `RmuxCaptureResult` 或 report projection fixture，不改 parser。
- 新的轻量 schema/report 测试文件：仅当现有测试无法容纳 JSON evidence validation 时新增。

### 2.4 推进策略

1. **Baseline inventory**：把 `rmux-send-capture-logging` accepted evidence、当前 `RmuxCaptureResult` 字段和 completion fixtures 列入 report baseline refs。  
   退出信号：report baseline refs 指向存在的 design/acceptance/tests，且不声明 production IO 未完成。
2. **Capture parity schema/report**：定义并验证 `output-capture-parity-report.json` 的 case、delta、provider projection 和 user history 字段。  
   退出信号：JSON 可解析，required fields、enum、hash、artifact refs、partial/blocked residual risk 校验通过。
3. **Machine capture matrix**：覆盖 plain、ANSI、wide char、wrapped line、provider completion input kinds，记录 raw artifact、normalized artifact 与 normalized hash。  
   退出信号：每个 core case 都有 `verdict` 和 delta classification；无 raw 或 normalized artifact 的 pass 被拒绝。
4. **Provider completion projection**：把 capture/log fixture 输入投影到 Codex、Claude、AGY、DeepSeek/session snapshot 代表性 detectors。  
   退出信号：每个 provider family 有 pass/partial/failed/blocked 结果、detector ref、artifact ref 和 failure_class；provider failure 不污染 rmux lane。
5. **User-visible history runbook**：记录 native Windows + WezTerm 前台 scrollback/回看证据，或记录 GUI 不可用的 blocked/partial。  
   退出信号：runbook 明确 host、terminal、backend、操作、observable、verdict；supporting-only 口径写清。
6. **UX evidence integration**：汇总生成 `windows-rmux-ux-parity-evidence.json`，固定 `parity_dimension=output_capture`。  
   退出信号：roadmap §4.1 required fields 和 enum 校验通过；artifacts 引用细粒度 report/runbook/tests。
7. **Guard and delta closure**：补测试或 guard，禁止 parser 改动掩盖 capture 漂移，确保 documented delta 不是自由文本。  
   退出信号：相关 pytest、YAML/JSON 校验和 py_compile 通过；未跑 live GUI 时 evidence_status 不能为 pass。

### 2.5 结构健康度与微重构

##### 评估

- 文件级 — `lib/terminal_runtime/rmux_backend_runtime/io.py`：已有职责是生产 Rmux IO，不应为了 evidence-first 在此塞入 report/schema 逻辑。
- 文件级 — `test/test_rmux_send_capture_logging.py`：已有 IO behavior tests，适合小幅补 evidence projection，但不适合承载完整 roadmap evidence schema。
- 文件级 — `test/test_rmux_completion_capture_fixtures.py`：已有 provider compatibility fixtures，适合补真实 `RmuxCaptureResult` shape 投影，不改 detector。
- 目录级 — feature `evidence/`：最适合存放 report、UX evidence JSON 和 user-visible runbook；不污染生产目录。

##### 结论：不做行为微重构

本 feature 的第一版以证据产物和测试投影为主，不移动现有 IO 代码、不拆 production module。若 implementation 发现 JSON schema helper 需要复用，优先放在测试或 CodeStable evidence helper 范围内；只有后续 supportability feature 需要生产消费时，再单独设计公共 schema 模块。

## 3. 验收契约

### 3.1 关键场景清单

| ID | 输入 / 触发 | 期望可观察结果 | 证据类型 |
|---|---|---|---|
| AC-001 | 读取 `rmux-send-capture-logging` accepted baseline | report baseline refs 指向 accepted design/acceptance/tests，不重写 IO | diff / JSON |
| AC-002 | plain、ANSI、wide char、wrapped line case | 每个 case 有 raw artifact、normalized artifact、expected hash、normalized hash、capture command、verdict | JSON / pytest |
| AC-003 | provider completion case | detector projection 有 provider family 结果、detector ref、artifact ref、failure_class，parser 未被修改适配 | golden pytest / guard |
| AC-004 | tmux baseline 与 Windows/rmux 差异 | 每个 delta 分类为 `pass|known_delta|product_bug|provider_failure|terminal_scrollback_only|blocked` | JSON / review |
| AC-005 | WezTerm GUI 不可用 | user-visible history 标 `blocked` 或 `partial`，不能让 whole evidence 伪造 pass | runbook / JSON |
| AC-006 | `windows-rmux-ux-parity-evidence.json` | required fields、enum、artifact refs、partial/blocked residual risk 校验通过 | JSON validation |
| AC-007 | scope guard | 无 provider parser workaround、无重复 `capture_pane` 实现、无滚轮/scrollback 替代 capture pass | guard / diff review |
| AC-008 | parent dependency 未 accepted | implementation 只能推进 headless machine/provider lanes，GUI/user-visible history 记录 blocked/partial | roadmap check / JSON |

### 3.2 明确不做的反向核对项

- 不应重写或重复实现 `RmuxBackend.capture_pane()`。
- 不应把 `terminal_scrollback_only` 归为 machine capture pass。
- 不应修改 provider completion parser 才让 fixture 通过。
- 不应把真实 provider auth/quota/credential failure 记为 rmux capture failure。
- 不应在缺少 native Windows + WezTerm GUI evidence 时把 user-visible history 标为 pass。

### 3.3 Acceptance Coverage Matrix

| Scenario | Covered By Step | Evidence Type | Command / Action | Core? |
|---|---|---|---|---|
| AC-001 baseline reuse | S1 | JSON / diff review | validate report baseline refs | yes |
| AC-002 machine capture matrix | S2-S3 | JSON / pytest | report schema + focused fixtures | yes |
| AC-003 provider completion projection | S4 | golden pytest | `test/test_rmux_completion_capture_fixtures.py` | yes |
| AC-004 documented delta | S3/S7 | JSON / review | delta enum validation | yes |
| AC-005 user-visible history supporting lane | S5 | runbook / JSON | manual WezTerm runbook or blocked record | yes |
| AC-006 UX evidence integration | S6 | JSON validation | roadmap §4.1 evidence validator | yes |
| AC-007 scope guard | S7 | guard / diff review | parser/capture/scrollback guard | yes |
| AC-008 dependency state gate | S1/S5 | roadmap check / JSON | parent item status + GUI lane verdict | yes |

### 3.4 DoD Contract

| ID | 要求 | 证据 | 阻塞级别 |
|---|---|---|---|
| DOD-DESIGN-001 | design/checklist/review 完整，且引用 confirmed brainstorm 和 roadmap §4.1/§4.3 | design review | blocking |
| DOD-IMPL-001 | `output-capture-parity-report.json` 存在并通过 schema/enum/hash/artifact 校验 | pytest / JSON validate | blocking |
| DOD-IMPL-002 | `windows-rmux-ux-parity-evidence.json` 存在，`parity_dimension=output_capture` | pytest / JSON validate | blocking |
| DOD-IMPL-003 | machine capture matrix 覆盖 plain、ANSI、wide char、wrapped line、provider_completion，且 raw/normalized artifacts 都可解析 | report / pytest | blocking |
| DOD-IMPL-004 | provider completion projection 覆盖代表性 detector family，记录 detector/artifact/failure_class，且不修改 parser 兜底 | golden pytest / diff guard | blocking |
| DOD-IMPL-005 | user-visible history 只作为 supporting evidence，GUI 不可用时不伪造 pass | runbook / JSON | blocking |
| DOD-IMPL-006 | documented delta 分类可枚举、可追踪到 raw artifact | JSON / review | blocking |
| DOD-IMPL-007 | 如果 parent interaction feature 未 accepted，GUI lane 必须 blocked/partial，不能作为 pass | roadmap check / JSON | blocking |
| DOD-REVIEW-001 | code review passed 且无 unresolved blocking | review report | blocking |
| DOD-QA-001 | QA 覆盖 JSON evidence、fixtures、provider projection、GUI blocked/partial 归因 | QA report | blocking |
| DOD-ACCEPT-001 | acceptance 回写 roadmap item，并记录 residual risks / supportability handoff | acceptance report | blocking |

Validation Commands:

| ID | 命令 | 目的 | 核心性 | 失败处理 |
|---|---|---|---|---|
| CMD-001 | `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-25-windows-rmux-output-capture-parity/windows-rmux-output-capture-parity-checklist.yaml" --yaml-only` | checklist YAML 合法性 | core | fix-or-block |
| CMD-002 | `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"` | roadmap items 回写合法性 | core | fix-or-block |
| CMD-003 | `python -m pytest -q test/test_windows_rmux_output_capture_parity_evidence.py` | 校验 output capture report 与 UX evidence JSON 的 schema、enum、artifact refs、raw/normalized artifacts、residual risk 和 parent dependency gate | core | fix-or-block |
| CMD-004 | `python -m pytest -q test/test_rmux_send_capture_logging.py` | accepted Rmux capture/send/logging baseline 防回退 | core | fix-or-block |
| CMD-005 | `python -m pytest -q test/test_rmux_completion_capture_fixtures.py` | provider completion fixture baseline 防回退 | core | fix-or-block |
| CMD-006 | `python -m py_compile "lib/terminal_runtime/rmux_backend.py" "lib/terminal_runtime/rmux_backend_runtime/io.py"` | touched/depended Python module 语法检查 | core | fix-or-block |
| CMD-007 | `python -m pytest -q test/test_rmux_send_capture_logging_import_guard.py` | 禁止重复 parser/capture fallback 和 shell leakage | core | fix-or-block |

Required Artifacts：design、checklist、design-review、`evidence/output-capture-parity-report.json`、`evidence/windows-rmux-ux-parity-evidence.json`、`evidence/user-visible-history-runbook.md` 或 QA 同名记录、JSON/schema tests、provider projection tests、scope guard。

### 3.5 自我批判结论

- 可证伪性：每个 core scenario 都绑定 JSON 字段、pytest、runbook 或 diff guard。
- 步骤原子性：baseline、schema、machine matrix、provider projection、user history、UX evidence、guard 七步分离。
- 最弱依赖：native GUI evidence 最容易不可用；设计明确 blocked/partial，不让它污染 machine/provider pass。
- 证据完整性：raw artifact、normalized artifact、hash、capture command、verdict、delta classification 缺一不可。
- 基线可执行性：核心命令复用已 accepted tests；live GUI 不作为 headless pass 前提。
- 交付物可核验性：acceptance 可从 feature evidence 目录、tests、roadmap item 和 review 报告反查。
- 清洁度规则：不新增临时 TODO/FIXME、调试输出、注释掉代码、死 import；不把自由 Markdown 当机器证据。

## 4. 与项目级架构文档的关系

- 严格遵守 roadmap §4.1 `WindowsRmuxUxParityEvidence`：本 feature 的 `parity_dimension` 固定为 `output_capture`。
- 严格遵守 roadmap §4.3 `Output/capture parity contract`：provider completion case 必须证明 parser 看到的文本与 baseline 等价或记录差异。
- 复用 `rmux-send-capture-logging` accepted evidence；不推翻其 production IO 结论。
- 为后续 `windows-rmux-supportability-parity-contract` 提供机器可读 input；缺失或 partial/blocked 必须保留 residual risk，不能由 docs/support tier 自行猜测。
