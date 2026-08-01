---
doc_type: issue-fix-note
status: verified
issue_path: fast_path
---

# ccb-src windows layout 大小写启动失败修复记录

## 根因

`.ccb/ccb.config` 使用 windows topology 时，`parse_topology_windows` 会把 `WindowSpec.agent_names` 规范化为小写，但 `WindowSpec.layout_spec` 仍保留原始大小写，例如 `Main_Coder:codex`。

启动时 `build_project_layout_plan` 使用小写目标 agent 名剪枝 layout；由于 layout leaf 名仍是 `Main_Coder` 这类原始大小写，精确匹配失败，所有 pane 被剪掉，最终报错：

`layout_spec does not include any visible panes for the requested start`

## 改动

- 在 `lib/agents/config_loader_runtime/parsing_runtime/topology.py` 中，windows topology 解析完成后同步规范化 layout leaf 名。
- 保留 layout 结构、provider、workspace mode 和 percent 信息不变。
- 在 `test/test_v2_config_loader.py` 增加 mixed-case windows topology 回归测试，覆盖 agent leaf 和 tool alias，并验证 `build_project_layout_plan` 可生成可见 pane。

## 验证

- `python -m pytest test/test_v2_config_loader.py -k "mixed_case_windows_layout_names or mixed_case_windows_tool_alias or mixed_case_compact_agent_names"` 通过。
- `python -m pytest test/test_v2_layout_plan.py` 通过。
- `ccb-src.ps1 config validate --json` 对当前项目配置通过，输出 layout 已规范化为小写。
- `CCB_NO_ATTACH=1 ./ccb-src.ps1` 启动通过，启动 agent 为 `main_coder, code_reviewer, archi, ccb_self`。

## 遗留风险

未跑全量测试。本次改动限制在 windows topology 配置解析层，影响面主要是 mixed-case agent/tool alias 的 layout 渲染与后续剪枝匹配。
