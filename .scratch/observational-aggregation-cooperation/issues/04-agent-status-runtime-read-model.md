# 04：细粒度 `agent_status` 进入运行时读模型

**What to build:** CCB 消费 Herdr 更细的 `agent_status` 作为 Host Runtime 事实，丰富 project view、gateway 或等价读模型中的运行时状态展示；这些状态只影响运行时展示，不影响 ask/job completion、恢复、取消、continuation 或 provider completion 判定。

**Blocked by:** 01：Herdr 原生 events 成为主状态通道.

**Status:** ready-for-agent

- [ ] 读模型能表达 Herdr 的 `working`、`blocked`、`idle`、`done`、`unknown` 等运行时状态。
- [ ] `blocked` 能表达为等待用户输入或审批，供用户定位需要处理的 agent。
- [ ] `done` 只表示运行时完成，可保留 unseen done 或等价提示，不直接关闭 CCB job。
- [ ] `unknown` 保持不确定语义，不降级为空闲或健康。
- [ ] 运行时状态更新不会改变业务完成、业务失败、恢复、取消、continuation 或 provider completion 的判定。
- [ ] 读模型对外输出继续做敏感字段裁剪，不泄漏 prompt、reply、API key、OAuth token、transcript 或等价敏感内容。
- [ ] 局部门禁覆盖 runtime fact source 与 business completion authority 分离，以及 project view/gateway 对 Herdr 状态的外部展示语义。

