---
doc_type: issue-approval
issue: 2026-08-03-ccb8-prestart-kill-hang
status: pending
checkpoint: ConfirmFixCompletion
---

# 修复完成确认

## 待确认事项

修复已实现并通过独立 focused closure review。正常启动验证需要在外部项目执行 `.\\ccb8.cmd`，确认源码版 CCB 能启动，且已安装 CCB/v5 未被停止。

外部复现失败后的新增根因已定位并修正：旧 wrapper 清理块没有对 Windows 路径分隔符做归一化，且正则没有稳定命中 `ccbd\main.py` / `ccbd\keeper_main.py`，导致 `.ccb-source-dev` PID `14312/14572` 被识别后又被筛掉。最终只读 dry-run 已确认当前匹配条件会命中这两个 source-dev PID。

## Owner 决策

- status: pending
- checkpoint: ConfirmFixCompletion
- decision: 待外部验证后确认
