---
doc_type: work
work_type: feat
slug: npm-install-coexist
epic: windows-native-herdr-ccb
status: in_progress
created: 2026-08-10
---

# feat: 安装版推进（install.ps1 独立目录）与 CCB5/CCB 共存

## 目标

把开发测试从 `ccb8.cmd`（源码版）推进到安装版：保留当前已安装的旧版 CCB
（`codex-dual`，~v5.2.9）改名 `CCB5`，把当前版本（v8.5.2）安装到独立目录
`CCB`，两者共存互不影响。所有迭代测试通过后只更新 `CCB`（新），严禁改动
`CCB5`（旧）。

## 现场（已核实事实）

- 本 repo = `@seemseam/ccb` v8.5.2，源码版开发走 `ccb8.cmd`。
- "当前已安装的 CCB" = `C:\Users\Administrator\AppData\Local\codex-dual`：
  旧版 Claude Code Bridge（Python 单文件 + lib，v5.2.9），由旧版 install.ps1 装。
- 新版**没有 Windows release artifact**（无 ccb.exe / release archive）；
  `windows_x64_release_surface_projection.json` =
  `windows_npm_enabled:false`、`release_install_entry:diagnostic_only`、
  `artifact_status:missing`。实测 `npm install -g <tgz>` 与
  `CCB_NPM_SKIP_DOWNLOAD=1` 都在 postinstall release gate fail-closed。
- 因此 npm 安装版当前**无法产出可运行 ccb**；可走通的是 install.ps1 源码安装
  （`source_install_entry:install_ps1`、`source_install_allowed:true`）。
- install.ps1 默认 `$InstallPrefix = $env:LOCALAPPDATA\codex-dual`——与旧版
  同目录！必须显式 `-InstallPrefix` 指向独立目录，否则覆盖 CCB5。

## 边界

- 严禁改动 CCB5（codex-dual）逻辑；只允许重命名其 `ccb` 命令入口以让位。
- 新版只装独立目录（`C:\Users\Administrator\AppData\Local\ccb-new`）。
- 不改发布 gate 语义（`windows_npm_enabled` 保持 false，属正式 release 工作）。

## 证据

- codex-dual 结构：`bin/ccb.bat`→`ccb5.bat`（内容不变，指向 `..\ccb`）、
  `ccb-*`/`ask`/`pend` 等 79 个 bin 保留原名。
- `ccb5 --version` → v5.2.9（旧版，行为不变）。
- `ccb-new` install：`ccb --print-version` → v8.5.2（新版）。
- install.ps1 修复两处：①`$items` 加 `ccb.py`；②`ccb` wrapper relPath 改
  `..\ccb.py` 并对 `ccb.py` 做 shebang 修复（新版仓库 `ccb` 是 bash launcher，
  旧 wrapper 指向 bash 脚本导致 Python SyntaxError）。

## 迭代方案

- 迭代 A（旧版改名 CCB5）：完成 ✅ — `codex-dual/bin/ccb.bat|ccb.cmd` →
  `ccb5.bat|ccb5.cmd`，内容不变。
- 迭代 B（install.ps1 独立目录安装）：完成 ✅ — `install.ps1 install -Yes
  -InstallPrefix C:\Users\Administrator\AppData\Local\ccb-new`；修复 install.ps1
  两个缺口（ccb.py 复制 + wrapper 指向 Python 入口）。
- 迭代 C（npm 包正式打通）：未开始 — 依赖 roadmap `windows-x64-release-surface`
  生成 Windows release artifact（ccb.exe / helper / archive），
  `windows_npm_enabled` 才可置 true。属后续独立迭代。

## 状态与未决

- 状态：迭代 A、B 完成并验证（ccb v8.5.2 / ccb5 v5.2.9 共存）；安装后裸 `ccb`
  报 "Herdr capability evidence is unavailable" 的 issue 已修复。
- 修复（2026-08-10）：`handle_start` 在 `[runtime.mux] backend = "herdr"` 且无
  可用 capability report 时调用 `ensure_herdr_bootstrap_env` 自动探测并注入
  `CCB_HERDR_CAPABILITY_REPORT`，使 installed 版裸 `ccb` 与源码版 one-click
  行为一致。根因：installed `ccb`（普通 start）不跑 `ensure_herdr_bootstrap_env`，
  backend selection 读 `CCB_HERDR_CAPABILITY_REPORT` 缺失 → `herdr-capability-missing`
  fail-closed。测试：test_herdr_bootstrap 新增 5 个 evidence 探测用例。
- 未决：
  - 用户 PATH 注册表已含 `ccb-new\bin`（新终端生效）；`codex-dual\bin` 仍在
    其它 PATH 层，`ccb5` 可用。
  - MCP `ccb-delegation` 已存在，重装时提示需先 remove 才能覆盖（非阻塞）。
  - 新版运行依赖 Python 3.10+（当前 3.14.6 满足）。
  - 正式 npm 安装（迭代 C）待 release artifact 就绪。
