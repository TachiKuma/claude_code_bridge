# 03：`ensure_runtime` 叙述收敛为永久 CCB 职责

**What to build:** 把 `ensure_runtime(manifest)` 从“临时兼容层/过渡层/等待 Herdr 原生 runtime.ensure”收敛为 CCB 的长期运行时收敛职责；旧 v2 方向中已被 ADR 0002 取代的 Herdr agent_id 权威、删除 CCB 身份上报路径、restart/backoff 下放，不得再作为待实现目标出现。

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] 文档、spec、契约说明中不再把 `ensure_runtime(manifest)` 描述为临时兼容层、过渡层或等待 Herdr 原生 `runtime.ensure` 的桥。
- [ ] `ensure_runtime(manifest)` 被描述为 CCB 的长期运行时收敛职责，并与 Collaboration Control Plane 术语保持一致。
- [ ] 旧 v2 工单或说明中已证伪的下放方向明确指向 ADR 0002 的取代结论，不再表现为 open blocker。
- [ ] Herdr 上游诉求保持为 source 优先级/seq 语义和只读 pane-agent 关联，不要求 Herdr 成为 agent identity authority。
- [ ] manifest 与 binding 的现有安全约束保持不变，不引入原始凭据或 restore token 泄漏。
- [ ] 局部门禁覆盖“兼容层/过渡/待上游”措辞清理，以及 12C/13A/13B 不被错误重开。

