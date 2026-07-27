# foreground reverse validation

Recorded: 2026-07-27

## Environment

- Host: native Windows
- Terminal: WezTerm foreground session
- Backend: rmux
- Session: `ccb-claude_code_bridge-b72b0116`
- Sidebar pane: `%0`
- Selected route: `unsupported_capability`

## Scope

本 feature 没有启用新的 runtime mouse route，也没有写入 WezTerm 配置或 rmux broad fallback。因此本 step 不是新增一次完整前台反向手测；它的目标是记录 unsupported 路径下的 scope guard：不可实现路径没有把 settings-only 问题退化成更宽的点击行为变更。

## Transcript

复用父 feature 前台证据：

- `../2026-07-27-sidebar-settings-click-e2e/evidence/manual-foreground-retest.md`
- `../2026-07-27-sidebar-settings-click-e2e/evidence/sidebar-mouse-probe.json`，仅作为失败 mouse route 的 persisted probe state；不作为 direct `c` 健康证明

父 feature 已观察到：

1. 真实前台点击能命中 rmux root binding。
2. rmux coordinate probe 为 `,,41,0,0,sidebar`，没有 `mouse_x/mouse_y`。
3. `send-keys -t = -M` 没进入 Rust/crossterm mouse event probe。
4. 父 manual transcript 记录 direct `send-keys -t %0 c` 能打开 config UI，但只作为 settings action 健康诊断；当前父 `sidebar-mouse-probe.json` 保留的是失败 click-probe state，不能用来证明 direct `c`。
5. broad sidebar-left-click fallback 已被 owner 拒绝，因为它会覆盖普通 sidebar 与 `x` KillProject 点击语义。

本 feature 增量反向结论：

| 场景 | 结果 | 说明 |
|---|---|---|
| settings click | blocked | 无 settings-only route；不把 direct `c` 计为 mouse pass |
| sidebar `x` click | not re-tested here; unchanged by this feature | 未新增任何 sidebar-left-click -> settings fallback；`x` 留给 KillProject child feature |
| ordinary sidebar click | not re-tested here; unchanged by this feature | rmux fallback 仍只能尝试 `send-keys -M`，本 feature 未扩大为 settings |
| ordinary pane drag/right/wheel | not re-tested here; unchanged by this feature | 未修改普通 pane GUI-native 策略或 rmux pane binding |

## Evidence status

- Foreground settings click parity: `blocked`
- Failure class: `unsupported_capability`
- Runtime diff required: `false`
- Broad fallback present in this feature: `false`
- New x/ordinary/pane foreground retest performed by this feature: `false`

## TDD exception

本 step 是 unsupported 路径下的前台证据复用和 diff scope guard。没有 runtime 行为变更可做 RED/GREEN；替代证据为父前台 transcript、本 feature capability evidence、最终 diff review。
