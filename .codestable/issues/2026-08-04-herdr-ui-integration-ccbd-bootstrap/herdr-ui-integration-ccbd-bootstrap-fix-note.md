# Herdr UI integration ccbd bootstrap 修复记录

## 根因

最新采集显示 Herdr UI 侧能观察到 `claude`，且 CCB control-plane 已 mounted，但 `layout-status` 中两个配置 agent 的 `runtime_state=missing`、`pane_id=null`。doctor bundle 同时记录 `start_flow_failed`，`failure_reason=unknown option: --json`。

本机 Herdr 0.7.5 的 `workspace list` / `pane list` 不支持 `--json`；机器可读 workspace/pane 状态应通过 `api snapshot` 获取。上一轮给 Herdr list 命令强制追加 `--json` 会让 startup flow 失败，导致 layout materialization 没有机会完成。

## 改动

- `JsonStore.load()` 增加 3 次短重试，并在最终失败时带上状态文件路径和 `invalid JSON`，同时保留 `JSONDecodeError` / `UnicodeDecodeError` 异常类型语义。
- Herdr CLI adapter 恢复为调用不带 `--json` 的 `workspace list` / `pane list`；仅当 list 输出不是 JSON 时回退到 `api snapshot`，普通命令失败仍原样抛出。
- spike 脚本的 Herdr workspace/pane 采集改用 `api snapshot`，不再直接调用不兼容的 list JSON 命令。
- spike 脚本改用 `ccb8 layout status --json`，并把 `layout_materialized_count` / `layout_materialization_complete` 写入 `summary.json`。
- spike 脚本分类把 `ping all` 成功纳入通过类前置，避免 provider/runtime 未证明时误判 layout/UI 通过。
- spike 分类新增 `mounted-but-layout-materialization-missing`，避免只因 Herdr agents 面板出现 `claude` 就误判完成。
- 外部项目 `ccb8` 残留已清理，两个 wrapper 已备份到 spike `backups/` 目录。

## 验证

- `python -m pytest test/test_json_store.py test/test_herdr_backend_client.py -q`
  - `169 passed`
- `python -m pytest test/test_ccbd_bootstrap_probe.py test/test_ccbd_windows_tcp_loopback_transport.py -q`
  - `26 passed, 1 skipped`
- `run_spike.ps1 -SelfTest`
  - `herdr_ui_integration_spike_selftest: passed`

## 遗留风险

本轮尚未重新在真实 Herdr UI 中运行 spike。下一次验证应优先确认 `ccb8-start-project.stderr.txt` 不再出现 `unknown option: --json`；如果启动成功但 `layout_materialized_count` 仍为 0，再进入 `ensure_project_namespace` 的 session-alive refresh/recreate 分支排查。
