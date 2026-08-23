# 05：_run_command_once no-window 兜底 + 防回归

**What to build：** 消除潜在的控制台闪窗脆弱点：运行时命令适配器的单条命令执行**默认构造**也
必须携带 `CREATE_NO_WINDOW`，不再仅依赖注入的 runner。用户日常启动路径不因某处使用默认
构造而闪出黑窗。附带降低 `ccb.cmd` 对 `%TEMP%` 验证脚本的依赖噪声。

**Blocked by：** 无（立即可开）

**Status:** done

**Implementation:** `3b4f75b4`

**Evidence:** `lib/platforms/windows/herdr/runtime/cli.py`、`lib/platforms/windows/herdr/common.py`、
`ccb.cmd`、`test/test_herdr_backend_client.py`、`test/test_ccb_cmd_launcher.py`

- [x] 以默认构造直接使用运行时命令适配器时也携带 no-window 标志，不闪控制台
- [x] 增加防回归测试：断言任一 Herdr 命令路径均携带 no-window creationflags
- [x] `ccb.cmd` 的 `%TEMP%` Python 验证脚本依赖噪声降低（尽量减少临时文件写删或改内联探测）
- [x] 后台进程仍保持既有 detached/no-window 启动策略，不回归
