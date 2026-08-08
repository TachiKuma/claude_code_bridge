---
status: observed
scope: Native Windows 启动 / Config UI 拉起
date: 2026-08-08
---
规则：Config UI 的权威入口是 `ccb config ui`；当 native Windows 停用 sidebar 时，不应把 sidebar 作为必需入口，而应通过独立 CLI / Start Menu / 快捷方式等方式让用户直接启动同一个本地 Web 编辑器，浏览器自动打开失败时必须打印可手动复制的 loopback URL。
适用 / 不适用：适用于 native Windows 上的配置中心拉起、入口发现和手动恢复路径；不适用于已有 sidebar 可用且只需保留增强按钮的非 Windows 场景。
证据：
- [lib/cli/services/config_ui.py](../lib/cli/services/config_ui.py)
- [lib/cli/phase2_runtime/handlers_start.py](../lib/cli/phase2_runtime/handlers_start.py)
- [docs/plantree/plans/config-designer-ui/decisions/001-config-ui-is-local-config-editor.md](../docs/plantree/plans/config-designer-ui/decisions/001-config-ui-is-local-config-editor.md)
- [docs/plantree/plans/config-designer-ui/topics/sidebar-config-entry.md](../docs/plantree/plans/config-designer-ui/topics/sidebar-config-entry.md)
候选归宿：project-doc
