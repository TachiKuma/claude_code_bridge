---
doc_type: issue-report
issue: herdr-residual-gaps
status: confirmed
severity: P3
summary: CCB Herdr集成路径上存在三个低级残留问题，不影响核心功能但需跟踪
tags:
  - native-windows
  - herdr-integration
  - residual
---

# Herdr 集成残留问题报告

## 1. 问题现象

`run-20260805-121840` 已确认 CCB 在 Native Windows + Herdr 0.7.5 中完整运行（mounted + 2/2 agent panes materialized），但存在三个低级残留问题：

1. **cmd 窗口闪现**：`observed_windows_flash: true`，尽管 CCB wrapper 已设置 `CreateNoWindow=true`
2. **keeper `D:\.c8\rs\` 路径 `PermissionError`**：`os.replace(tmp, target)` 在 Windows 上要求目标目录 DELETE 权限，`D:\.c8\rs\` 下的文件由上一代 keeper 在不同用户上下文中创建导致权限不一致
3. **spike 脚本 `api snapshot` 连接的 session 与 CCB namespace session 不一致**：采集脚本 query 的是 `ccb-herdr-avaprintdesigner-source-dev`，CCB 实际在 `ccb-avaprintdesigner-575a971f` session 中创建 workspace

## 2. 复现步骤

1. 在 Herdr UI 内启动 CCB
2. 观察是否有短暂 cmd 窗口闪现
3. 检查 `.ccb/ccbd/keeper.stderr.log` 是否有 `PermissionError: os.replace`
4. 运行 `run_spike.ps1`，对比 `pane-evidence/pane-verification.md` 中 pane 数量与 `ccb8-ps` 中的 pane 数量

## 3. 期望 vs 实际

**期望**：零闪窗、keeper 写入不报错、snapshot 正确显示 CCB namespace 的 pane
**实际**：闪窗仍存在、PermissionError 存在但不阻塞、snapshot 中 panes=0

## 4. 环境信息

- 涉及模块：`ccb8.ps1` wrapper、keeper 文件持久化、spike 脚本 Herdr session 选择
- 运行环境：Windows 10 Pro x64, Herdr 0.7.5, Python 3.14

## 5. 严重程度

**P3 轻微** — 三个问题均不影响 CCB 核心功能。问题一是体验问题，问题二是健壮性问题（write 失败但有重试兜底），问题三是采集局限。
