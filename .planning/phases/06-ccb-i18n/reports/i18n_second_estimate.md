# CCB i18n Second Estimate

## Inputs

- 基线文档：`docs/feasibility-study/05-CCB-i18n-详细实施方案.md`
- 盘点脚本：`scripts/audit_ccb_i18n_surface.py`
- 盘点报告：`i18n_surface_inventory.md`

## Revised Estimate

| 范围 | 主要对象 | 估算 |
|------|----------|------|
| R0 | `lib/i18n_core.py`、`lib/i18n.py`、`tests/test_i18n_core.py` | 0.5-1 天 |
| P0-CLI | `ccb`、`bin/ask`、`bin/*ask`、`lib/*_comm.py`、CI 守卫 | 2-4 天 |
| P1-盘点 | Mail/Web/TUI 文案面盘点与策略 | 0.5-1 天 |
| P1-迁移 | `wizard.py`、模板、API、`sender.py` | 4-7 天 |
| 回归与伪本地化 | CLI + Web + Mail smoke | 1-2 天 |

## Conclusion

- 与原方案一致，Mail/Web/TUI 仍是剩余工作量的主来源。
- CLI 核心生产化可先独立完成并交付。
- 全量迁移建议继续按 `TUI -> Web 模板 -> Web API -> Mail 正文` 的顺序分批执行。

## Blocking Items

- `bin/ask` 仍有大量直接面向用户的字符串，需单独迁移。
- Web 模板尚无统一翻译注入机制。
- Mail 正文模板中同时存在中英文混排和动态字符串拼接。
