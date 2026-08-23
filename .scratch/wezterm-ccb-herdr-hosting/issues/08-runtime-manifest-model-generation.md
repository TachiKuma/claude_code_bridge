# 08：HerdrRuntimeManifest 模型 + 生成（Phase 0/2，expand）

**What to build：** 引入 `HerdrRuntimeManifest` 数据模型，CCB start path 生成 manifest 描述当前
已有的拓扑与策略（services/workspaces/panes/env_refs/restart 策略）。manifest **只传授权引用或
裁剪后的环境投影，禁止原始凭据**。这是 expand 步骤：新形态与旧证据路径并存，不破坏现状。

**Blocked by：** 无（立即可开）

**Status:** done

**Implementation:** `3b4f75b4`

**Evidence:** `lib/platforms/windows/herdr/runtime/contracts.py`、
`lib/platforms/windows/herdr/runtime/manifest.py`、`test/test_herdr_runtime_contracts.py`

- [x] 新增 `HerdrRuntimeManifest` 模型，描述 project/session/generation/services/workspaces/panes
- [x] CCB start path 生成并写出 manifest
- [x] manifest 只允许 `env_refs`，无原始 API key / OAuth token / 完整 prompt/reply
- [x] manifest 与现有启动路径并存，不改变现有行为（expand，不 contract）
- [x] manifest 无 secrets（有测试佐证）
