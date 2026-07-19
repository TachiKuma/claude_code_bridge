---
doc_type: roadmap-review
roadmap: windows-rmux-native-backend
status: passed
reviewed: 2026-07-19
round: 5
review_state: passed
---

# windows-rmux-native-backend roadmap 审查报告

## Round 5（2026-07-19 · v8.2.1 再基线 update 审查）

- **审查范围**：本轮 update 增量——基线 v8.0.16→v8.2.1；新增模块 CCBD Control Plane Transport / Accelerator Transport Guard；新增接口契约 §4.9（ccbd 控制面 RPC transport seam）；新增 items 17–21（transport-seam / tcp-loopback / accelerator-guard / process-liveness / full-chain-smoke）；`ccbd-rmux-namespace-lifecycle` 依赖调整；里程碑范围界定。
- **独立 review**：completed。独立 Task agent 亲自 grep/read 核验 v8.2.1 代码事实，非信文档自述。
- **首轮判定 changes-requested，两条 important 已修复后复核 passed**：
  - [important-1] §8 曾把 `lib/ccbd/socket_server_runtime/lifecycle.py:19 listen_server` 误标「无 guard」；实为 guard@15 抛 `RuntimeError`。已修正为「有 guard / 无 guard 裸 AttributeError」两分类，与实测对齐。
  - [important-2] 发现第四个控制面 blocker：`lib/ccbd/system.py:43 process_exists` 的 `os.kill(pid,0)` 在 Windows 为 `CTRL_C_EVENT` 语义（误判活为死 + 可能误投 Ctrl-C），被 keeper/health/ownership 约 10 文件消费。已新增 item `ccbd-windows-process-liveness` 并纳入 `ccbd-windows-full-chain-smoke` 依赖。
  - 非阻塞：nit-1（§4.9 补 client 侧端点发现归属）、suggestion-1（item 19 accelerator 默认 ask 必经）均已处理；nit-2 保留并在 note 区分实现/验收依赖。
- **代码事实核验 verdict**：帧协议 transport-neutral（成立）、bootstrap peer-path 鉴权 Unix 专用（成立）、backend_selection.py tmux-only（成立）、runtime_accelerator 独立 socket/协议（成立）、AF_UNIX 实测点行号（修正 lifecycle:19 后全部准确）。
- **DAG**：21 items，`validate-yaml.py` 通过，无环、无悬空依赖，唯一 minimal_loop 为 `rmux-capability-gate`。
- **Round 5 Verdict**：**passed**，无遗留 blocking/important。可交用户 review。

---

## Round 4（2026-07-06 · 历史记录）

# windows-rmux-native-backend roadmap 审查报告（round 4）

## 1. Scope And Inputs

- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`
- Items: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs:
  - `docs/ccbd-windows-psmux-plan.md`
  - `docs/plantree/plans/windows-wezterm-native/README.md`
  - `docs/ccbd-startup-supervision-contract.md`
  - `docs/ccbd-diagnostics-contract.md`
  - `docs/ccb-config-layout-contract.md`
- Code facts checked:
  - `lib/terminal_runtime/tmux.py`
  - `lib/terminal_runtime/tmux_panes_runtime/actions.py`
  - `lib/terminal_runtime/tmux_logs.py`
  - `lib/cli/services/start_foreground.py`
  - `lib/cli/services/runtime_launch.py`
  - `lib/cli/services/runtime_launch_runtime/session_files.py`
  - `lib/provider_backends/native_cli_support/launcher.py`
  - `lib/provider_backends/pane_log_support/session.py`
  - `lib/ccbd/services/project_namespace_runtime/backend.py`
  - `lib/ccbd/services/project_namespace_runtime/materialize_topology.py`
  - `lib/ccbd/services/project_namespace_runtime/agent_window_reflow.py`
  - `lib/ccbd/services/project_namespace_runtime/move_patch_agents.py`
  - `lib/ccbd/services/project_namespace_runtime/remove_patch_agents.py`
  - `lib/terminal_runtime/backend_selection.py`
  - `lib/provider_backends/pane_log_support/session.py`

### Independent Review

- Status: completed
- Detection: native-agent
- Provider / agent: subagent `019f3766-52bb-7f33-bf83-e7d484dd5488`
- Raw output: 最终复审返回 `blocking: none`、`important: none`、`nit: none`；确认用户补充审核提出的 I1 opt-in selection、I2 capture/provider completion 耦合、I3 Rmux daemon ownership，以及 N1/N2/N3 均已处理。仅保留 suggestion：`rmux-send-capture-logging` feature-design 应把 provider completion golden fixtures 落到具体测试/fixture 文件。
- Merge policy: 已逐条核验复审结论，并用本地 YAML / DAG / 代码事实检查合并；用户补充审核记录作为本轮 review 输入。
- Gate effect: none，独立 review 已完成且无未处理 blocking / important。

## 2. Roadmap Summary

- Goal completion signal: 原生 Windows 上可 opt-in 使用 Rmux 创建项目 namespace、启动 agents、attach UI、执行 `ccb ask`、关闭终端后 reattach、`ccb kill` 清理 namespace / provider process tree / runtime authority，并保持 Linux/macOS/WSL tmux 路径不回退。
- Module split: Capability Gate、Backend Resolver & Opt-in、MuxBackend Contract、Windows Runtime Boundary、Rmux Daemon Ownership、RmuxBackend、CCBD Integration、Provider Runtime Contract、Validation & Packaging。
- Interface contracts: `MuxBackend` 被定义为组合能力集合；`ProjectNamespaceBackend` 只承担 higher-level project namespace policy；backend resolver、runtime authority、Windows command builder、Rmux daemon ownership、provider session payload 均有字段级契约。
- Items: 16 个 planned item；最小闭环为 `rmux-capability-gate`，后续实现必须经过独立 `rmux-route-approval`。
- Dependency shape: DAG，无未知依赖、自依赖或循环。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] `rmux-send-capture-logging` 后续 feature-design 需要把 “provider completion parser golden fixtures” 具体落到测试/fixture 文件和比较维度。
  - Evidence: roadmap 已要求 capture 格式兼容证据且不重写 parser，但 roadmap 层没有绑定具体 fixture 路径。
  - Impact: 不阻塞 roadmap review；feature-design 若仍只写泛称，验收证据可能分散。
  - Expected fix scope: 在 `rmux-send-capture-logging` design / acceptance 中列出 fixture/test 文件，并覆盖尾部空白、ANSI、换行 wrapping、宽字符、截断语义。

### learning

- 当前代码仍大量依赖 tmux-only 假设：`backend_selection.py` 只有 `selected == "tmux"` 分支，`tmux_base()` 固定 `tmux` 并默认使用 `-f /dev/null`（可由 `CCB_TMUX_CONFIG` 覆盖），foreground attach 直接读取 `namespace_tmux_*` 并执行 `tmux attach-session`，provider session writer 写 `terminal=tmux` / `tmux_session`，project namespace runtime 多处通过 `_tmux_run` / `_tmux_run_ready` 族 helper 驱动 tmux。
- Roadmap 修订后把 capability probe 和 route approval 分离，避免“探针跑完但 owner 未批准”时误解锁后续实现。
- Capability gate 已补齐当前 layout/reflow/reload 需要的 `resize-pane`、`select-layout`、`swap-pane`、`move-pane`，并要求映射到实际代码路径。
- 用户补充审核提出的 opt-in selection、capture 格式保真、Rmux daemon ownership 已进入 roadmap 契约、items 和 Goal Coverage Matrix。

### praise

- 规划边界克制：没有把 Rmux 伪装成 tmux，也没有绕过 capability gate 直接进入实现。
- provider runtime/session payload 被单独拆出 item，能覆盖 `ccb ask` 与 provider recovery 的真实风险面。

## 4. User Review Focus

- 用户需要重点拍板：
  - 是否认可 Rmux 作为旧 psmux 方案的当前候选实现，而不是继续沿用旧 psmux 命名。
  - 是否认可 `rmux-route-approval` 作为 capability gate 后的显式路线决策点。
  - 是否认可 `runtime.mux.backend` / `CCB_MUX_BACKEND` 这类 opt-in 选择语义；feature-design 可改名，但必须保留优先级、fail-fast 和 diagnostics。
  - Windows 第一版对外定位是 experimental / beta / supported，最终由 `rmux-packaging-docs-contracts` 收口。
- 后续 feature-design 需要重点复核：
  - `MuxBackend` 拆成 capability-specific protocols 时不要退化成 pass-through。
  - backend resolver 必须覆盖 project config / user config / env / platform default / auto probe / fallback 诊断。
  - provider session payload 必须以 mux-neutral 字段为 canonical，旧 tmux 字段只能作为 compatibility alias。
  - Rmux daemon 只能作为 backend evidence，不能成为第二个 project authority。
  - Windows shell/log builder 不能让 `sh -lc`、`tee -a`、PowerShell quoting 散落回业务层。
  - `rmux-send-capture-logging` 必须用 provider completion golden fixtures 证明 capture 格式兼容。
- 不能靠 roadmap review 完全确认的点：
  - Rmux v0.8.0 或更新版本是否真实满足 CCB required command / semantic set。
  - Windows 真机上的 ConPTY、named pipe、provider CLI、Job Object 行为。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Granularity Gate | pass | E | roadmap 第 2 节说明横跨 terminal runtime、ccbd namespace、foreground attach、diagnostics、installer、Windows IPC/process lifecycle 和真实平台测试 | none |
| Goal Coverage Matrix | pass | E | roadmap Goal Coverage Matrix 覆盖 capability、route approval、backend resolver opt-in、tmux regression、runtime boundary、provider session、Rmux daemon ownership、Rmux backend、ccbd lifecycle、recovery、validation、packaging | none |
| DAG and minimal loop | pass | E | YAML 校验通过；16 个 item；无未知依赖、自依赖、循环；唯一 minimal loop 为 `rmux-capability-gate` | none |
| Interface contract usability | pass | E/C | roadmap 第 4 节给出 typed payload、错误语义、backend resolver、runtime authority、Rmux daemon ownership、provider session payload、Windows command builder；代码事实支持这些边界必要 | feature-design 继续细化协议 |
| Module interface depth | pass | E/C | roadmap 明确 `MuxBackend` 是组合能力集合，`ProjectNamespaceBackend` 只承担 higher-level policy，不暴露 primitive pass-through | feature-design 避免胖接口落地 |

Summary: E=5, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- Rmux 外部能力未在本轮验证。后续必须由 `rmux-capability-gate` 在原生 Windows 真机上产出 capability report，再由 `rmux-route-approval` 落盘 owner 决策；不能据此直接进入 Rmux implementation。
- capture 格式保真仍需真实 fixture 证据。roadmap 已要求验证，但具体 fixture/test 文件留给 `rmux-send-capture-logging` feature-design。
- 旧 authoritative docs 仍大量使用 tmux/psmux 命名。route approval 后需要通过 ADR、docs-neat 或 domain 流程标注 superseded / updated，避免后续 feature-design 引用旧结论。
- package 当前 Windows 发布策略仍未变更。该风险已放入 `rmux-packaging-docs-contracts`，不能提前声明 supported。

## 7. Verdict

- Status: passed
- Next: 交给用户 review；用户明确确认后才能把 roadmap 从 `status: draft` 改为 `active`。
