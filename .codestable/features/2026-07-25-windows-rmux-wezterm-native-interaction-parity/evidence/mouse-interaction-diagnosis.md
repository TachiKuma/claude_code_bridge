---
doc_type: feature-evidence
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
evidence: mouse-interaction-diagnosis
status: diagnosed
recorded_at: 2026-07-27
source: two parallel read-only diagnosis agents cross-checked against code + live-binding-snapshot + design.md
---

# Windows + WezTerm + rmux 交互六项缺陷 —— 只读诊断汇总

owner 于 2026-07-26 完成人工前台测试,六项交互全部 FAIL（见 `manual-wezterm-runbook.md`）。
本文件汇总根因诊断,供 cs-feat 修复阶段引用。

## ⚠️ 2026-07-27 实测更正（覆盖下文关于「rmux 不支持」的结论）

本文件初版基于一次静态代码诊断,推断根因是「rmux 不支持 `if-shell`/`select-pane`/`unbind-key`/
格式算术/鼠标 pane 定位」。**该前提已被真实 rmux 0.9.0 实测推翻**（scratch server 非交互探测）:

- rmux **支持** `if-shell`、`select-pane`、`unbind-key`、`bind-key`、`send-keys -M`、格式算术
  （`#{e|-:..}`）、条件（`#{==:..}`/`#{&&:..}`/`#{||:..}`）；`if-shell -F <format-cond>` 会被真实
  求值并据结果选分支。
- rmux **支持 `-t =`（当前鼠标 pane target）**,这正是 rmux 内置默认 `MouseDown1Pane =
  select-pane -t = ; send-keys -M` 的机制（单击本就应 focus）。`#{mouse_pane}` 不作 `-t` 自动解析
  （字面查找失败）,但 `-t =` 可用。
- **真根因改写**:fallback `_apply_sidebar_mouse_controls_without_mouse_pane_format` 主动绕开这些
  被支持的原语,普通 pane 左键/滚轮用了退化占位 `select-pane -M`（`-M`=清 marked-pane、无 `-t`、
  不 focus）;sidebar 分流的 `if-shell` 漏了 `-t =` target,导致条件对「当前活动 pane」而非「被点击
  的 sidebar pane」求值 → 恒假 → settings/kill 动作不触发。
- **失败 1（单击 focus）可实现**:`select-pane -M` → `select-pane -t =`。不再是「rmux 能力受限」。
- **失败 5/6（sidebar settings/x）修法**:给 fallback sidebar 分流 `if-shell` 补 `-t =`,或改为无
  条件 `send-keys -t = -M` 透传给 Rust `header_action_at`。均在 rmux 下可行。

owner 决策（2026-07-27）:**修 1 + 5 + 6**;3（右键粘贴）、4（滚轮）维持 design GUI-native 预期
残留;2（选区行 off-by-one）维持 design,作 rmux 外部残留。下文「rmux 不支持」类表述以本节为准。

## 统一根因图景

在 Windows + `backend_impl=rmux` 下:
- `service.py:70-72` `_mouse_pane_format_supported()` 返回 **False**（`is_windows() and backend_impl=='rmux'`）。
- 于是 `service.py:121-123` 走 **fallback** 分支 `_apply_sidebar_mouse_controls_without_mouse_pane_format`（`service.py:266-348`），完整分支（124-263，含 `#{mouse_pane}` 定位、copy-mode 滚动、`paste-buffer -p`）**从不执行**。
- 全局 `mouse on`（`lib/terminal_runtime/tmux_mux_backend.py:141`，另 `runtime_launch_runtime/tmux_panes.py:121`）使 WezTerm 把所有鼠标事件以 SGR 序列转发给 rmux,**绕过 `~/.wezterm.lua` 自己的 mouse_bindings**（右键粘贴、左键释放复制）。
- rmux **不支持** `if-shell`、`select-pane`、`run-shell`、`unbind-key`,也无 `#{mouse_x}`/`#{mouse_y}`/`#{mouse_pane}` 格式算术能力（据 `.codestable/features/2026-07-19-rmux-route-approval/rmux-capability-report.json`）。fallback 却依赖这些原语,故绑定虽被 `bind-key` 注册（`list-keys` 可见,给出"看似接线"假象),但点击时动作不可执行。

共性:fallback 对普通 pane 用退化占位 `select-pane -M`,加 `mouse on` 全局捕获阻断 WezTerm 原生语义 —— 普通 pane 既拿不到 tmux 语义,也拿不到 GUI 原生语义。

## 逐项根因

| # | 现象 | 根因 | 位置 | 置信度 |
|---|---|---|---|---|
| 1 | 单击不聚焦、双击才聚焦 | 左键绑到 `select-pane -M`（`-M` 是清 marked-pane,不带 `-t` 无法定位鼠标 pane）→ 单击 no-op;无 `DoubleClick1Pane` 绑定,双击落到 rmux 内置 focus | `service.py:267,285-299` | 高 |
| 2 | 拖拽选区起点行 off-by-one（列正确） | 本仓库不绑 `MouseDrag1Pane`（仅 `MouseDrag1Border` resize),普通 pane 选区完全由 **rmux daemon 内部坐标→pane 行映射**处理,行多算 1 | **rmux 外部二进制**,本仓库未定位 | 高（定位到外部）；具体行未定位 |
| 3 | 右键不粘贴 | (a) `mouse on` 使右键作 SGR 转发给 rmux,绕过 `.wezterm.lua:29-31` 右键粘贴; (b) `service.py:115-116` unbind `MouseDown3Pane`/`M-MouseDown3Pane`,fallback 从不重绑 → rmux 吞掉右键 | `service.py:115-116` + `tmux_mux_backend.py:141` | 高 |
| 4 | 滚轮无反应 | fallback 普通 pane `WheelUpPane`/`WheelDownPane` 也绑死 `select-pane -M`,既不进 copy-mode、不 `send-keys -M` 透传、也无原生 scrollback（被 `mouse on` 拦） | `service.py:267,327-348` | 高 |
| 5 | 侧栏 settings 点击无反应 | settings 点击靠 `if-shell -F <cond> 'send-keys c'` 分发,rmux 不支持 `if-shell`+格式算术 → 动作落空;Rust 侧命中逻辑本身正确但收不到事件 | `service.py:279-320,374-389`;条件 `_sidebar_settings_click_condition` | 高 |
| 6 | 侧栏 x KillProject 点击无反应 | 与 5 同根因:`if-shell -F <kill cond> 'send-keys Q'`,rmux 无法执行 | `service.py:290-297,392-397`;`_sidebar_kill_click_condition` | 高 |

## 关键修复线索

1. **Rust sidebar 命中逻辑已正确,无需改**:`tools/ccb-agent-sidebar/src/tui.rs`（真实源码,由 `bin/build-ccb-agent-sidebar` 构建）的 `handle_mouse_down`（503-529）→ `header_action_at`（1275-1291）已能正确处理 settings（⚙ 在 `pane_width-4`）与 KillProject（× 在 `pane_width-2`）,坐标与 `service.py` 条件一致,有单测（`tui.rs:2243-2248`）。**方向:fallback 不要用 `if-shell` 条件判 settings/kill,应无条件 `send-keys -M` 把鼠标透传给 sidebar,交 Rust `header_action_at` 处理。**
2. **fallback 的 `if-shell -F` 均缺 `-t` 目标**（对比完整分支 `service.py:130-135` 全带 `-t #{mouse_pane}`）→ `#{@ccb_role}`/`#{pane_width}` 等对"当前活动 pane"而非"被点击 pane"求值,即使 rmux 支持 `if-shell` 也会误判。（`service.py:288/291-292/309/312-313`，置信度中）
3. **右键/滚轮要恢复 GUI 原生语义,仅 unbind 不够**:需让 rmux 对普通 pane 不捕获（关闭上报/放行,或 Shift 旁路),才能让事件回流 WezTerm。
4. **测试盲区**:`test/test_v2_tmux_ui.py:380-386,417-493` 只断言 `list-keys` 含绑定串,从不验证点击时 `if-shell` 条件在真实运行时被求值执行 —— 缺陷因此漏网。修复须补运行时派发/行为测试。

## 修复归属

- **本仓库可修(1/3/4/5/6)**:核心待改 `lib/cli/services/tmux_ui_runtime/service.py`（`_apply_sidebar_mouse_controls_without_mouse_pane_format` 266-348、`_sidebar_settings_click_condition`/`_sidebar_kill_click_condition` 374-397）+ 复核 `tmux_mux_backend.py:141` 全局 `mouse on` 的作用面。
- **需外部处理(2)**:rmux daemon 鼠标坐标→pane 行映射 off-by-one,不在本仓库;修复前作为已知残留,或推动 rmux 侧修正。
