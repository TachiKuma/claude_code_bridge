# 05：防 Herdr hook 与 seq 架空 CCB 权威

**What to build:** CCB 管理的 provider home 不安装 Herdr 原生 agent hook；当环境中存在 hook 或竞争来源风险时，系统能暴露诊断信息并保持 `source=ccb` 权威，避免 hook 的 `time_ns` seq 架空 CCB 的单调 seq。

**Blocked by:** 02：`source=ccb` 成为 CCB 管理 pane 的身份权威.

**Status:** ready-for-agent

- [ ] CCB 管理的 provider home 创建或更新流程不会安装 Herdr 原生 agent hook。
- [ ] 如果检测到 CCB 管理范围内存在 Herdr hook 竞争风险，系统提供明确诊断，而不是静默采纳 hook 权威。
- [ ] hook 产生的更细运行时事实不得替代 `source=ccb` 的身份/provider 权威。
- [ ] hook 的 `time_ns` 级 seq 不得使 CCB 管理 pane 的 CCB 来源状态永久失效。
- [ ] CCB 的 agent 状态上报保持单调 seq 约束，旧状态不能覆盖新状态。
- [ ] 已存在的非 CCB hook 产物可以作为运行时事实被观察，但不能改变业务完成判定。
- [ ] 局部门禁覆盖 provider home 不装 hook、竞争风险可诊断、seq 架空被阻断和 CCB source 权威保持。

