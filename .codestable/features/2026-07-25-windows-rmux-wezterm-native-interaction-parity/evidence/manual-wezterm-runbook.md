---
doc_type: feature-evidence
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
evidence: manual-wezterm-runbook
status: partial
recorded_at: 2026-07-27
human_operated: true
operator: owner
retest_required: true
note: "2026-07-27 新实现重测：真缺陷 1（单击 focus）已转 PASS；真缺陷 5/6（sidebar settings / x）仍 FAIL，本轮继续修；残留 3/4 按 design 记录；残留 2 出现 pane 间不对称（main_coder/archi off-by-one，code_reviewer/ccb_self 正常），需重判归因。详见「Manual Interaction Status (2026-07-27 retest)」。"
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
