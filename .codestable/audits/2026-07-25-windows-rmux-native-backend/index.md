---
doc_type: audit-index
audit: 2026-07-25-windows-rmux-native-backend
scope: Windows Rmux Native Backend
created: 2026-07-25
status: complete
dimensions: [bug, security, performance, maintainability]
excluded_dimensions: [arch-drift]
total_findings: 4
---

# Windows Rmux Native Backend 审计报告

## 范围

已确认范围：围绕 Windows Rmux Native Backend 的生产路径和交付契约做只读审计，不做全仓库盲扫，不修改业务代码。

扫描范围：

- Runtime/backend：`lib/terminal_runtime/rmux_backend.py`、`lib/terminal_runtime/rmux_backend_runtime/`、`lib/terminal_runtime/rmux_runner.py`、`lib/terminal_runtime/backend_resolver.py`、`lib/terminal_runtime/backend_selection.py`、`lib/terminal_runtime/mux_backend_contract.py`。
- CCBD 控制面与 Windows 进程路径：`lib/ccbd/control_plane_transport/`、`lib/ccbd/socket_client_runtime/`、`lib/ccbd/socket_server_runtime/`、`lib/ccbd/services/project_namespace_runtime/`、`lib/ccbd/services/runtime_runtime/`、`lib/ccbd/services/health*`、`lib/ccbd/services/ownership.py`、supervision / stop-flow 相关 rmux 路径。
- Provider/session/diagnostics：`lib/provider_runtime/`、`lib/provider_backends/*/launcher_runtime/`、`lib/cli/services/doctor.py`、`lib/cli/render_runtime/ops_views_doctor.py`、`lib/cli/services/diagnostics_runtime/`。
- Windows install/package/docs contract：`install.ps1`、`lib/terminal_runtime/rmux_packaging_support.py`、`lib/terminal_runtime/rmux_packaging_support_projection.json`、`README.md`、`docs/ccbd-diagnostics-contract.md`、`docs/plantree/plans/windows-rmux-native-backend/`。
- Evidence/tests：`scripts/*rmux*`、`scripts/*windows*`、`artifacts/rmux-windows-validation/`、`artifacts/rmux-packaging-docs-contracts/`、`test/test_*rmux*`、`test/test_*windows*`、`test/test_ccbd_*` 中与 Windows Rmux 路径直接相关的测试。

扫描维度：

- `bug`
- `security`
- `performance`
- `maintainability`

暂不扫描 `arch-drift`：当前未发现 `.codestable/requirements/adrs/` 可用 ADR。按 `cs-audit` 规则，架构偏离不能凭记忆判定。

## 总评

本次只读审计共发现 4 条问题：`P1` 2 条、`P2` 2 条。最值得优先处理的是 Windows additive patch 忽略 rmux respawn replacement pane id，以及 ccbd 客户端响应读取没有最大字节上限。packaging/doctor/install 的 rmux 支持投影整体有单一 owner 和测试覆盖，未发现需要单独上报的发布契约缺口。

## 发现清单

| # | 性质 | 严重度 | 置信度 | 标题 | 文件 |
|---|---|---|---|---|---|
| 1 | bug | P1 | high | Windows additive patch 忽略 rmux respawn 后的规范 pane id | [finding-01.md](finding-01.md) |
| 2 | security | P1 | medium | ccbd 客户端响应读取缺少最大字节上限 | [finding-02.md](finding-02.md) |
| 3 | performance | P2 | high | terminal API 的全局 backend cache 实际无法命中 | [finding-03.md](finding-03.md) |
| 4 | maintainability | P2 | medium | PowerShell export 转译用裸分号切分，边界条件会破坏 provider 命令 | [finding-04.md](finding-04.md) |

## 按维度分布

| 性质 | P0 | P1 | P2 | 合计 |
|---|---|---|---|---|
| bug | 0 | 1 | 0 | 1 |
| security | 0 | 1 | 0 | 1 |
| performance | 0 | 0 | 1 | 1 |
| maintainability | 0 | 0 | 1 | 1 |
| arch-drift | 0 | 0 | 0 | 0 |
| **合计** | **0** | **2** | **2** | **4** |

## 下一步建议

- **P1 本迭代修**：`finding-01.md`、`finding-02.md` 建议开 `cs-issue`，分别补 rmux additive patch replacement 测试和客户端响应上限测试。
- **P2 排期优化**：`finding-03.md`、`finding-04.md` 建议开 `cs-refactor`，分别收敛 backend cache 生命周期和 Windows PowerShell 命令转译边界。
- **暂不处理**：`arch-drift` 未扫描；如后续提供 ADR，可单独启动架构偏离审计。
