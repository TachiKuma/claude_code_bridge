# 07：移除 import-time Herdr 探测，introspection 命令不触碰 Herdr（Phase 1）

**What to build：** 让与运行时无关的 introspection 命令（`--help`、`version`、配置检查等）**完全
不触碰 Herdr**。移除导入期 Herdr 探测；需要运行时的命令改为在 operation-time 调用 Herdr 适配器
并返回结构化错误。明确选择 Herdr 而 Herdr 不可用时仍 fail-closed。

**Blocked by：** 无（立即可开）

**Status:** done

**Implementation:** `3b4f75b4`

**Evidence:** `ccb.py`、`test/test_source_runtime_guard.py`

- [x] `ccb --help`、`ccb version` 在 Native Windows 且 Herdr 缺失时仍成功
- [x] 配置检查等 introspection 命令不触发任何 Herdr 探测
- [x] 需要运行时的命令在 operation-time 检查 Herdr 可用性，返回结构化错误
- [x] 明确选择 Herdr 且不可用时 fail-closed（清晰错误，非含糊行为）
- [x] 旧路径仍 fail-closed（characterization test 佐证）
