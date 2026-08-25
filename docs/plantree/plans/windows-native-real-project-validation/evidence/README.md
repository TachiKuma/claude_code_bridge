# Windows 原生外部项目验收证据目录

日期：2026-08-25

本目录用于保存后续实机验收记录。每次运行建议创建一个按时间命名的子目录：

```text
evidence/YYYYMMDD-HHMMSS/
```

建议文件：

- `environment.md`：PowerShell、Windows、provider CLI、CCB 入口和隔离 prefix。
- `smoke-project.md`：一次性 smoke 项目的命令、输出摘要和清理结果。
- `real-project.md`：真实项目的写入边界、启动观测和清理结果。
- `ask-results.md`：Codex/Claude ask 的 job id、trace/pend 摘要和业务结果。
- `resilience.md`：第二阶段中断、重启、恢复、clear、compact、followup 证据。
- `failures.md`：未通过项、复现命令、分类和修复归属。

不得在证据中保存 provider token、API key、完整认证文件或可复用登录材料。
