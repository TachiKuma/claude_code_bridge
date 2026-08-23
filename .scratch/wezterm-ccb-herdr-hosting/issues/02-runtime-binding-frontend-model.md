# 02：HerdrRuntimeBinding.frontend 模型 + 持久化 + generation 校验

**What to build：** 为 Runtime Binding 引入可选 `frontend` 段，记录 attach 首屏可靠性所需的最小
前台事实（`kind`、`mux_available`，以及诊断用 `window_id`、后续升级用 `spawn_target`）。Binding
作为 CCB 重连/teardown/投影/事件去重的唯一运行时锚点，须绑定 project/namespace/pane/agent
slot/provider kind/session/runtime generation，并对过期 generation 做校验。

**Blocked by：** 无（立即可开）

**Status:** ready-for-agent

- [ ] Runtime Binding 能持久化并回读可选 `frontend` 段
- [ ] `frontend` 缺失或 `kind != "wezterm"` 时按「无前台事实」处理，不报错
- [ ] `window_id` 仅作诊断记录，不作重连锚点
- [ ] binding 按 project/session/workspace/pane/generation 复合键校验归属，过期 generation 被拒
- [ ] `frontend` 段不含任何原始凭据或 provider transcript 内容
