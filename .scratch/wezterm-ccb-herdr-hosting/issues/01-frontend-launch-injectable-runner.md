# 01：前台启动可注入命令 runner seam（prefactor）

**What to build：** 把前台启动路径（在 Native Windows 上经 WezTerm/Herdr 拉起可见 UI）里的命令
执行抽出为一个**可注入命令 runner** 的抽象，复刻代码中已有的 `run_fn` 依赖注入模式。这是
prefactor：**对用户行为零改变**，目的是让后续「探活/spawn/回退」逻辑无需真起 WezTerm 即可测试。
「先让改动变容易，再做容易的改动。」

**Blocked by：** 无（立即可开）

**Status:** done

**Implementation:** `3b4f75b4`

**Evidence:** `lib/cli/services/start_foreground.py`、`test/test_v2_start_foreground.py`

- [x] 前台启动路径的命令执行通过可注入 runner 完成，默认 runner 保持现有行为
- [x] 未注入自定义 runner 时，启动行为与改动前完全一致（characterization test 绿）
- [x] 新 seam 可被测试注入以捕获「探活/spawn」调用而不启动真实 WezTerm 进程
- [x] 不改变任何用户可见行为，不引入新窗口模型
