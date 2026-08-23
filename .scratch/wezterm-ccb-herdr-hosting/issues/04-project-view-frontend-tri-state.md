# 04：project_view 前台三态投影

**What to build：** 让 `project_view`（进而 Agents 面板/mobile gateway）读取 Runtime Binding 的
`frontend` 段，如实呈现前台三态：「已 attach 到 WezTerm tab」「已回退到 detached Herdr 窗口」
「前台未就绪」。用户由此能区分「界面已在 WezTerm 中」与「已回退/尚未就绪」，不再面对静默的
空白。

**Blocked by：** 03（前台三态由其产生并写入 binding）

**Status:** ready-for-agent

- [ ] `project_view.runtime_status` 反映前台三态：WezTerm tab / detached 回退 / 未就绪
- [ ] 前台状态与运行时/业务状态分列，不混成单一权威
- [ ] 前台事实缺失（无 `frontend` 段）时呈现为「未知/未就绪」，不伪装成已 attach
- [ ] 下游（面板、mobile gateway）能一致消费该前台三态
- [ ] 不解析原始 provider transcript，不泄漏 prompt/reply/API key/OAuth token
