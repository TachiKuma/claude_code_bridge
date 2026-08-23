# 03：前台探活 + 缺 mux 可观测回退

**What to build：** 用户启动项目时，若已运行 WezTerm GUI mux 则在其中开出 agent tab；若未运行
mux（或 spawn 失败），系统**可观测地回退**到 Herdr 独立窗口并记录回退原因，绝不静默失败。启动
前先探活 WezTerm mux，spawn 需判定返回码，探活/spawn 结果写入 Runtime Binding 的
`frontend.mux_available`。这是第一颗 tracer bullet，直接修掉「前台静默降级」缺陷。

**Blocked by：** 01（可注入 runner seam）、02（binding.frontend 模型）

**Status:** done

**Implementation:** `3b4f75b4`

**Evidence:** `lib/cli/services/start_foreground.py`、`test/test_v2_start_foreground.py`

**Notes:** 已通过可注入 runner 覆盖有 mux、无 mux、spawn 失败、无二进制路径；尚未执行真实 Windows
live validation。

- [x] 有可用 WezTerm GUI mux 时，agent tab 在其中开出
- [x] 无 mux 时**触发可观测回退**到 Herdr 独立窗口（不再静默），回退原因被记录
- [x] spawn 失败（返回码非 0）被正确判定，不被丢弃
- [x] 无 WezTerm 二进制时也走可观测回退
- [x] `frontend.mux_available` 在「有 mux / 无 mux / 无二进制」三态下取值正确
- [x] 本轮不引入新窗口寻址（维持现有窗口模型）
