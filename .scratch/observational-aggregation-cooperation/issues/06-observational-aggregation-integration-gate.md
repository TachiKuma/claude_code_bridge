# 06：端到端观测聚合回归门禁

**What to build:** 在前置票完成后，保留一份最终集成门禁，验证 ADR 0002 的整体约束没有在跨模块集成中回潮：Herdr events 优先、polling 兜底、CCB 身份权威、运行时事实不关闭业务 job、WezTerm/Herdr 非竞争 mux、旧下放方向不重开。

**Blocked by:** 01：Herdr 原生 events 成为主状态通道；02：`source=ccb` 成为 CCB 管理 pane 的身份权威；03：`ensure_runtime` 叙述收敛为永久 CCB 职责；04：细粒度 `agent_status` 进入运行时读模型；05：防 Herdr hook 与 seq 架空 CCB 权威.

**Status:** ready-for-agent

- [ ] 集成验证覆盖 CCB 权威、Herdr 观测、WezTerm 呈现三层职责，并确认三者没有互相替代权威。
- [ ] 集成验证覆盖 events 主通道和 snapshot polling 兜底，并确认 source/fallback reason 在读模型中可见。
- [ ] 集成验证覆盖 CCB 管理 pane 的 `source=ccb` 身份/provider 权威，并确认屏幕检测不会覆盖它。
- [ ] 集成验证覆盖 `done`、`idle`、`unknown`、`blocked` 等运行时状态不会直接关闭、失败或恢复业务 job。
- [ ] 集成验证覆盖 `ensure_runtime(manifest)` 的长期 CCB 职责叙述，并确认旧“兼容层/过渡/待上游”方向没有回潮。
- [ ] 集成验证覆盖 CCB 管理 provider home 不安装 Herdr 原生 hook，或存在 hook 风险时可诊断且不架空 CCB 权威。
- [ ] 集成验证覆盖 WezTerm 是 Frontend Surface、Herdr 是真实 mux/pane owner，不引入 WezTermBackend 或竞争 mux 行为。
- [ ] 最终门禁通过后，本批 ticket 可作为 ADR 0002 落地闭环；若失败，失败项必须回指对应前置票修复。
