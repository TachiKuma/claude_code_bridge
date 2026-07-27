---
doc_type: feature-evidence
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
evidence: manual-wezterm-runbook
status: failed
recorded_at: 2026-07-27
human_operated: true
operator: owner
retest_required: true
note: "2026-07-27 owner 前台复测：6 项中仅普通 pane 单击聚焦 PASS；普通 pane 拖拽选区、右键粘贴、WezTerm 滚轮、sidebar settings、sidebar x KillProject 均 FAIL。需要独立根因审查，并将交互验收拆成更细 feature。"
---

# Manual WezTerm Runbook

## Environment

- Host shell reports `TERM_PROGRAM=WezTerm`.
- Host shell reports `WEZTERM_PANE=3`.
- `wezterm.exe` is available at `D:\Tools\AI Tools\WezTerm\wezterm.exe`.
- `rmux.exe` is available from the WinGet package path.
- Live rmux binding validation passed in `evidence/live-binding-snapshot.txt`.

## Manual Interaction Status

Owner performed the human-operated foreground mouse transcript on native Windows + WezTerm + rmux
on 2026-07-26. All six required interactions FAILED against AC-007 expectations:

- ordinary pane single-click focus: **FAIL** — single click does not focus the target pane. Double
  click does focus the pane, and the matching agent-name item in the sidebar auto-highlights.
- ordinary pane drag selection: **FAIL** — text can be selected, but the selection start lands on the
  line *below* the mouse (horizontal start column is correct; only the row is off by one). Drag also
  triggers pane single-click focus, which is expected.
- ordinary pane right-click paste: **FAIL** — right click does not paste into the CLI, contradicting
  the WezTerm config `C:\Users\Administrator\.wezterm.lua` (left-drag copy / right-click paste).
- ordinary pane wheel behavior: **FAIL** — no scrolling behavior observed at all.
- sidebar settings click: **FAIL** — no response.
- sidebar `x` KillProject click: **FAIL** — no response.

## Manual Interaction Status (2026-07-27 retest — new implementation)

Owner performed a second human-operated foreground mouse transcript on native Windows + WezTerm +
rmux on 2026-07-27 against the new implementation. Result: 1 PASS, 5 FAIL (two of them already
classified as design residuals). Per-interaction:

1. ordinary pane single-click focus: **PASS** — single click now focuses the target pane (fix via
   `select-pane -t =` confirmed effective; previously FAIL).
2. ordinary pane drag selection: **FAIL (pane-asymmetric)** — text can be selected. In the
   `main_coder` and `archi` panes the selection start lands on the line *below* the mouse (horizontal
   start column correct; only the row is off by one). In the `code_reviewer` and `ccb_self` panes the
   drag selection is normal. Drag also triggers pane single-click focus, which is expected. NOTE: this
   pane-to-pane asymmetry (only 2 of 4 panes affected) contradicts a pure "rmux daemon internal
   coordinate mapping" attribution — the offset appears layout/pane-position dependent and must be
   re-diagnosed before it is written off as rmux-external residual.
3. ordinary pane right-click paste: **FAIL** — right click does not paste into the CLI, contradicting
   `C:\Users\Administrator\.wezterm.lua` (left-drag copy / right-click paste). Classified as GUI-native
   residual (rmux mouse capture cannot override WezTerm native binding); AC-001 negative assertion passes.
4. ordinary pane wheel behavior: **FAIL** — no scrolling behavior observed. Classified as GUI-native
   residual; AC-002 negative assertion passes.
5. sidebar settings (`⚙`) click: **FAIL** — no response. Real defect; the header passthrough fix
   (`send-keys -t = -M` → Rust `header_action_at`) did NOT take effect. Continue fixing this round.
6. sidebar `x` KillProject click: **FAIL** — no response. Same root cause as (5); continue fixing.

Remaining true defects after this retest: **(5) sidebar settings click and (6) sidebar x KillProject
click** — both still dead. Interaction (2) needs a fresh diagnosis given the pane-asymmetric offset.

## Implementation Fix Prepared (2026-07-27)

本轮代码修复已去掉 Windows/rmux fallback 中依赖 `#{mouse_x}` / `#{mouse_y}` 的 header 按钮分支，也不再用
`send-keys -t = c` / `send-keys -t = Q` 模拟 settings / KillProject。当前 live binding 证据显示：

- sidebar pane 左键统一执行 `select-pane -t = ; send-keys -t = -M`，由 Rust `header_action_at` 判断 `⚙` 与 `x`。
- ordinary pane 左键只执行 `select-pane -t =`。
- sidebar wheel 与 left-click 一样透传给 Rust；ordinary wheel 只走 `select-pane -t =` 分支，不进入 copy-mode 或 scroll command。
- right-click、drag 不在 rmux fallback root binding 中重绑。

需要 owner 在 native Windows + WezTerm + rmux 前台复测以下结果后，才能把本文件 `status` 从 `partial` 更新为
`passed` 或新的失败状态：

1. sidebar `⚙` 点击打开 settings/config UI 或显示可诊断失败。
2. sidebar `x` 点击触发 KillProject。
3. 拖选行偏移按 pane 位置重新记录，确认是否仍为 pane-asymmetric。

## Manual Interaction Status (2026-07-27 retest after Round 3 QA-fix)

Owner performed a third human-operated foreground transcript on native Windows + WezTerm + rmux
after the Round 3 QA-fix. Result: 1 PASS, 5 FAIL.

1. ordinary pane single-click focus: **PASS** — single click focuses and switches panes normally.
2. ordinary pane drag selection: **FAIL** — dragging cannot select any string.
3. ordinary pane right-click paste: **FAIL** — no response; even after copying text in another app,
   right-click does not paste into the pane.
4. ordinary pane wheel behavior in WezTerm: **FAIL** — no scrolling behavior observed.
5. sidebar settings click: **FAIL** — no response.
6. sidebar `x` KillProject click: **FAIL** — no response.

QA disposition: this is no longer an evidence gap. The current implementation still fails five
foreground interaction paths. The next step is independent root-cause review plus a finer feature
split for the six interaction checks.

## Substitute Evidence Available

- Unit/fake backend evidence proves Windows/rmux fallback does not bind ordinary pane wheel to `copy-mode -e` or `send-keys -X scroll-up/down`.
- Unit/fake backend evidence proves Windows/rmux fallback does not bind ordinary pane right-click to `paste-buffer -p`.
- Unit/fake backend evidence proves ordinary pane left-click does not use a bare `send-keys -M` binding.
- Live rmux binding evidence proves rmux accepts the generated root bindings without ordinary pane copy-mode / paste-buffer capture.

## QA Disposition（2026-07-27 实测更正）

上面六项 FAIL 是 owner 对**旧实现**的前台观测。初判「六项全 FAIL = 六个缺陷」在读 design 验收
契约 + rmux 0.9.0 实测后更正（实测详见 `mouse-interaction-diagnosis.md` 顶部「实测更正」节）。
对照 design 的分类：

- **真缺陷（本轮修，owner 2026-07-27 决策）**：单击 focus（1）、sidebar `⚙` settings（5）、
  sidebar `x` KillProject（6）。根因**不是**「rmux 不支持」，而是 fallback 误用无 `-t` 的
  `select-pane -M`、sidebar `if-shell` 漏 `-t` target。修法：普通 pane 左键改 `select-pane -t =`；
  sidebar header 改无条件 `send-keys -t = -M` 透传给 Rust `header_action_at`。见 design 2.1/2.2、
  AC-003 / AC-004 / AC-008。
- **已知残留（design GUI-native 取舍，不计 AC 失败，只记录）**：右键粘贴（3）、滚轮原生滚动（4）——
  因 rmux mouse capture 无法接管 WezTerm 原生绑定；AC-001 / AC-002 的 negative assertion 已 pass。
- **rmux 外部残留**：拖选起点行 off-by-one（2）在 rmux daemon 内部坐标映射，本 feature 不修，
  必要时另行推动 rmux 侧。

QA 结论：AC-007 待新方案实现完成后**重测**——单击聚焦、sidebar `⚙`/`x` 应转 pass；右键粘贴、
滚轮、选区行偏移记为残留。QA 不得据本文件当前状态直接判 pass 或 fail，须以新实现的重测为准。
