# 环境确认

执行时间：2026-08-26 17:39-18:05 +08:00

当前 CCB 入口：

```powershell
E:\GitHub开源项目\TachiKuma\NativeWin_CCB_Herdr\ccb.cmd
```

## 环境摘要

| 项 | 结果 |
|---|---|
| PowerShell | 7.6.5 |
| Windows | Microsoft Windows 10.0.19045 |
| `codex` | `C:\Users\Administrator\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` |
| `claude` | `C:\Users\Administrator\AppData\Roaming\npm\claude.ps1` |
| `herdr` | `C:\Users\Administrator\AppData\Local\Programs\Herdr\bin\herdr.exe` |
| repo venv Python | Python 3.14.7 |

## 关键观察

- 本机当前 `ccb.cmd` 可从外部目录启动。
- 当前仓库存在未提交改动：`lib/process_background.py`、`test/test_ccbd_process_env.py`，本轮未回滚也未修改。
- 旧证据中的真实项目 `E:\GitHub开源项目\TachiKuma\MewUI` 在本机不存在，阶段 B 无法沿用该路径。
- `E:\GitHub开源项目\TachiKuma\Herdr_Guides` 不是 Git 仓库，只能作为非仓库目录，不能当作阶段 B 真实项目。
- `E:\GitHub开源项目\TachiKuma\claude_code_bridge` 是另一份 CCB 源码仓库，而且已有大量未提交改动，不适合作为本轮清洁的真实项目验证对象。

