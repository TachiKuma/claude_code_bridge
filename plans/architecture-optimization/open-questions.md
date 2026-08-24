# Open Questions

Date: 2026-05-18

## Questions

- Should `lib/provider_model_shortcuts.py` and `lib/release_artifacts.py` stay
  as root-level implementation modules, or should a later package-root cleanup
  introduce `lib/provider/` and `lib/release/` namespaces?
- Should `lib/cli/management_runtime/startup_update.py`, hotspot rank 8, be
  handled in Phase 2 with release/dev-tooling complexity work or deferred to a
  separate CLI management pass?
- Can OpenCode share only the generic memory projection signature/event helper
  while preserving its extended config merge fields and
  `opencode_config_merge_failed` event, or should it remain separate?

## Herdr 上游诉求（记名，不实现；来自 ADR 0002 观测聚合协作模型）

- 统一/文档化 Herdr 多源仲裁的 seq 语义与 source 优先级：让 `source=ccb` 能显式声明高优先级，
  而非靠 seq 量级碰运气（当前 CCB 用小整数 seq、agent 自带 hook 用 `time.time_ns()`，后者会永远
  压过前者）。
- Herdr 可选暴露稳定 pane-agent 关联，便于 CCB 对账——但不作为 agent_id 权威，仅只读关联
  （Herdr 架构上不铸造 agent 实例身份，见 docs/adr/0002）。
