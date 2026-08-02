---
doc_type: feature-evidence
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
command_id: CMD-013
kind: native-windows-herdr-transcript
updated_at: 2026-08-02
---

# CMD-013 Native Windows Herdr Transcript

- workdir: `D:\tmp\ccb-herdr-cmd-013-20260802-225336`
- repo: `D:\Python\GitHub\claude_code_bridge`
- herdr_exe: `C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe`
- herdr_session: `ccb-cmd-013-20260802-225336`
- herdr_preflight_session: `ccb-cmd-013-20260802-225336-preflight`
- appdata: `D:\tmp\ccb-herdr-cmd-013-20260802-225336\.home\AppData\Roaming`
- capability_report: `D:\Python\GitHub\claude_code_bridge\.codestable\features\2026-07-31-herdr-backend-contract-spike\evidence\herdr-contract-spike-evidence.json`
- shim: POSIX-only Mobile imports, Windows directory fsync baseline, PYTHONPATH and CCB_HERDR_* control-plane allowlist are scoped to this transcript.

## Platform

```json
{"sys_platform": "win32", "machine": "AMD64", "python_bits": "64bit", "is_wsl": false}
```

## herdr availability

```text
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --version
exit_code: 0
--- stdout ---
herdr 0.7.5-preview.2026-07-29-44b3adb12552
```

## Capability Report Excerpt

```json
{
  "adapter_recommendation": "continue-with-gaps",
  "failure_class": "windows-beta-gap",
  "command_status": {
    "kill_pane": "supported",
    "pane_spawn": "supported",
    "read_output": "supported",
    "schema": "supported",
    "send_input": "supported",
    "server_restart_layout_restore": "supported",
    "server_restart_output_history": "unsupported",
    "server_restart_process_continuity": "unsupported",
    "server_status": "supported",
    "session_attach": "supported",
    "ui_detach_reattach": "needs_harness"
  },
  "semantic_status": {
    "kill_pane": "supported",
    "pane_spawn": "supported",
    "read_output": "supported",
    "schema": "supported",
    "send_input": "supported",
    "server_restart_layout_restore": "supported",
    "server_restart_output_history": "unsupported",
    "server_restart_process_continuity": "unsupported",
    "server_status": "supported",
    "session_attach": "supported",
    "ui_detach_reattach": "needs_harness"
  },
  "source_ref": "D:\\Python\\GitHub\\claude_code_bridge\\.codestable\\features\\2026-07-31-herdr-backend-contract-spike\\evidence\\herdr-contract-spike-evidence.json"
}
```

## herdr named session preflight


## herdr named session preflight: status server before

```text
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-cmd-013-20260802-225336-preflight status server --json
exit_code: 0
--- stdout ---
{"status":"not_running","running":false,"version":null,"protocol":null,"capabilities":null,"compatible":null,"socket":"D:\\tmp\\ccb-herdr-cmd-013-20260802-225336\\.home\\AppData\\Roaming\\herdr\\sessions\\ccb-cmd-013-20260802-225336-preflight\\herdr.sock","session":"ccb-cmd-013-20260802-225336-preflight","restart_needed":false}
```

## herdr named session preflight: direct server launch probe

```text
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-cmd-013-20260802-225336-preflight server
timeout_after_seconds: 5
--- stderr(partial) ---
herdr server running; you can use any herdr CLI command in another terminal.
api socket: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.home\AppData\Roaming\herdr\sessions\ccb-cmd-013-20260802-225336-preflight\herdr.sock
client socket: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.home\AppData\Roaming\herdr\sessions\ccb-cmd-013-20260802-225336-preflight\herdr-client.sock
logs: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.home\AppData\Roaming\herdr\sessions\ccb-cmd-013-20260802-225336-preflight\herdr-server.log
did you mean to open the Herdr TUI? run `herdr`; you do not need `herdr server`.
```

## herdr named session preflight: status server after direct launch

```text
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-cmd-013-20260802-225336-preflight status server --json
exit_code: 0
--- stdout ---
{"status":"not_running","running":false,"version":null,"protocol":null,"capabilities":null,"compatible":null,"socket":"D:\\tmp\\ccb-herdr-cmd-013-20260802-225336\\.home\\AppData\\Roaming\\herdr\\sessions\\ccb-cmd-013-20260802-225336-preflight\\herdr.sock","session":"ccb-cmd-013-20260802-225336-preflight","restart_needed":false}
```

## herdr named session preflight: workspace list

```text
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-cmd-013-20260802-225336-preflight workspace list
exit_code: 1
--- stderr ---
Error: Os { code: 2, kind: NotFound, message: "系统找不到指定的文件。" }
```

## namespace create via ccb -n

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> --cmd013-confirm-stdin -n
exit_code: 0
--- stdout ---
Refresh project memory/context under D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb? [y/N] start_status: ok
project: D:\tmp\ccb-herdr-cmd-013-20260802-225336
project_id: 80548bf0b37fa9cb23169f14ea9bfa82fd92433bdd94de069b24c5a74cdcd51b
ccbd_started: true
socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\ccbd.sock
agents: agent1
startup_run_id: start_cdd632b0619542728312bc4ef87689d4
startup_cli_timings_ms: {"cli_post_rpc":146.814,"cli_pre_rpc":1.0997,"cli_total":1965.3919,"daemon_ensure":1325.4242,"layout_status":4.4719,"maintenance_heartbeat":0.7685,"sidebar_helper_refresh":141.5332,"start_rpc":491.9802}
layout_summary_status: ok
layout: windows=1 panes=1 runtime_panes=0 dynamic=0 loop=0 runtime=1 explicit=true entry_window=main ccbd_state=mounted observe_status=skipped observe_reason=namespace_tmux_scope_missing
layout_window: name=main index=- panes=1 runtime_panes=0 agents=agent1
layout_agent: name=agent1 kind=static source=configured ownership=static_configured dispatch=enabled window=main pane=- pane_identity=missing runtime_state=failed apply_status=- failed_apply=false
```

## namespace durable state after create

```json
{
  "namespace_backend_family": "herdr-native",
  "backend_impl": "herdr",
  "namespace_id": "w1",
  "namespace_session_name": "ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0",
  "namespace_ipc_kind": "herdr_socket",
  "namespace_ipc_ref": "herdr://cmd-013-local",
  "namespace_restore_token_present": true,
  "ui_attachable": true,
  "mount_state_hint": "mounted"
}
```

## herdr namespace session after create


## herdr namespace session after create: status server before

```text
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0 status server --json
exit_code: 0
--- stdout ---
{"status":"running","running":true,"version":"0.7.5-preview.2026-07-29-44b3adb12552","protocol":18,"capabilities":{"live_handoff":false,"detached_server_daemon":false},"compatible":true,"socket":"D:\\tmp\\ccb-herdr-cmd-013-20260802-225336\\.home\\AppData\\Roaming\\herdr\\sessions\\ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0\\herdr.sock","session":"ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0","restart_needed":false}
```

## herdr namespace session after create: workspace list

```text
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0 workspace list
exit_code: 0
--- stdout ---
{"id":"cli:workspace:list","result":{"type":"workspace_list","workspaces":[{"active_tab_id":"w1:t1","agent_status":"unknown","focused":true,"label":"ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0","number":1,"pane_count":2,"tab_count":1,"tokens":{"ccb_logical_window":"main","ccb_namespace_id":"w1","ccb_project_id":"ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0","ccb_window":"main"},"workspace_id":"w1"}]}}
```

## ccbd ping namespace payload

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> ping ccbd
exit_code: 0
--- stdout ---
project_id: 80548bf0b37fa9cb23169f14ea9bfa82fd92433bdd94de069b24c5a74cdcd51b
mount_state: mounted
desired_state: running
health: healthy
generation: 1
socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\ccbd.sock
control_plane_endpoint: {'kind': 'tcp_loopback', 'address': '127.0.0.1:52706', 'display': '127.0.0.1:52706', 'legacy_socket_path': None, 'auth_ref': 'D:\\tmp\\ccb-herdr-cmd-013-20260802-225336\\.ccb\\ccbd\\control-plane-token-d19f7e38580344a1.json', 'fingerprint': 'a1e557c4f6dcd736', 'socket_path': None, 'host': '127.0.0.1', 'port': 52706, 'token_ref': 'D:\\tmp\\ccb-herdr-cmd-013-20260802-225336\\.ccb\\ccbd\\control-plane-token-d19f7e38580344a1.json', 'generation': 'd1de929b12186bb9', 'acl_status': 'windows-icacls-user-read'}
tmux_socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\tmux.sock
project_anchor_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb
runtime_state_root: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb
runtime_root_kind: project
runtime_relocation_reason: None
runtime_filesystem_hint: None
runtime_marker_status: not_required
runtime_root_marker_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\runtime-root.json
runtime_root_ref_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\runtime-root-ref.json
preferred_socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\ccbd.sock
effective_socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\ccbd.sock
socket_root_kind: project
socket_fallback_reason: None
socket_filesystem_hint: None
tmux_preferred_socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\tmux.sock
tmux_effective_socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\tmux.sock
tmux_socket_root_kind: project
tmux_socket_fallback_reason: None
tmux_socket_filesystem_hint: None
known_agents: ['agent1']
config_signature: 34e1f57f208c3e9c5e28816bd930f6fffcb4a29648cedf72004ce9fe7cef7e3e
serving_pid: 25476
serving_daemon_instance_id: 10b3f30ae7b34498b211921d7c2132d4
serving_lease_generation: 1
serving_startup_generation: 1
accepted_startup_id: f4aa651d5933403aa8c228820ba70aed
namespace_epoch: 1
namespace_tmux_socket_path: 
namespace_tmux_session_name: ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0
namespace_backend_family: herdr-native
namespace_backend_impl: herdr
namespace_id: w1
namespace_session_name: ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0
namespace_ipc_kind: herdr_socket
namespace_ipc_ref: herdr://cmd-013-local
namespace_restore_token_present: True
namespace_layout_version: 3
namespace_control_window_name: __ccb_ctl
namespace_control_window_id: None
namespace_workspace_window_name: main
namespace_workspace_window_id: w1
namespace_workspace_epoch: 1
namespace_ui_attachable: True
namespace_last_started_at: 2026-08-02T14:53:43.737346Z
namespace_last_destroyed_at: None
namespace_last_destroy_reason: None
namespace_last_event_kind: namespace_created
namespace_last_event_at: 2026-08-02T14:53:43.737346Z
namespace_last_event_epoch: 1
namespace_last_event_socket_path: None
namespace_last_event_session_name: ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0
namespace_last_event_backend_family: herdr-native
namespace_last_event_backend_impl: herdr
namespace_last_event_id: w1
namespace_last_event_ipc_kind: herdr_socket
namespace_last_event_ipc_ref: herdr://cmd-013-local
namespace_last_event_restore_token_present: True
start_policy_auto_permission: True
start_policy_recovery_restore: False
start_policy_last_started_at: 2026-08-02T14:53:43.817589Z
start_policy_source: start_command
pid_alive: True
socket_connectable: True
heartbeat_fresh: True
takeover_allowed: False
reason: healthy
startup_id: f4aa651d5933403aa8c228820ba70aed
startup_stage: mounted
last_progress_at: 2026-08-02T14:53:43.301601Z
startup_deadline_at: None
last_failure_reason: None
shutdown_intent: None
last_request_queue_wait_s: 1.1000010999850929e-05
last_submit_duration_s: None
last_ping_duration_s: 0.000818600005004555
last_handler_latency_s_by_op: {'ping': 0.0008276000007754192, 'start': 0.49146429999382235}
last_maintenance_duration_s: 0.14701339999737684
last_heartbeat_duration_s: 0.14701339999737684
heartbeat_step_duration_s: {'health_monitor': 3.060000017285347e-05, 'runtime_supervision': 0.14577470000949688, 'dispatcher_runtime_views': 4.889999399892986e-05, 'dispatcher_tick': 0.00011439999798312783, 'dispatcher_poll_completions': 2.02999945031479e-05, 'reload_drain_auto_retry': 2.95999925583601e-05, 'job_heartbeat': 2.5300003471784294e-05}
last_heartbeat_agents_inspected: 1
last_heartbeat_runtime_store_writes: 5
pending_maintenance_ticks: 0
last_project_view_response_duration_s: None
last_project_view_build_duration_s: None
project_view_cache_hits: 0
project_view_cache_misses: 0
last_project_view_tmux_command_count: None
last_project_view_capture_pane_count: None
last_project_view_store_scan_count: None
rss_bytes: None
virtual_memory_bytes: None
fd_count: None
thread_count: 3
service_graph_version: 1
service_graph_created_at: 2026-08-02T14:53:42.743299Z
service_graph_retained_count: 1
service_graph_retained_count_scope: published_graph_count_not_inflight_retention
last_reload_duration_s: None
last_reload_plan_class: None
last_reload_error: None
active_execution_count: 0
recoverable_execution_count: 0
nonrecoverable_execution_count: 0
pending_items_count: 0
terminal_pending_count: 0
recoverable_execution_providers: []
nonrecoverable_execution_providers: []
last_restore_at: 2026-08-02T14:53:43.297380Z
last_restore_running_job_count: 0
last_restore_restored_execution_count: 0
last_restore_replay_pending_count: 0
last_restore_terminal_pending_count: 0
last_restore_abandoned_execution_count: 0
last_restore_already_active_count: 0
last_restore_results_text: none
```

## foreground attach

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> --cmd013-foreground-attach
exit_code: 0
--- stdout ---
project_id: cmd013
backend_impl: herdr
namespace_id: w1
session_name: ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0
ipc_kind: herdr_socket
ipc_ref: herdr://cmd-013-local
namespace_restore_token_present: True
```

## Config Changed For Reload

```toml
version = 2
entry_window = "main"

[windows]
main = "agent1:codex, agent2:codex"
```

## reload dry run

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> reload --dry-run
exit_code: 0
--- stdout ---
reload_status: ok
dry_run: true
mutation_enabled: false
plan_class: add_agent
safe_to_apply: false
future_safe_to_apply: true
old_config_signature: 34e1f57f208c3e9c5e28816bd930f6fffcb4a29648cedf72004ce9fe7cef7e3e
new_config_signature: 89a33ade6817c0f74910cda7759b7adaca13c693f6c9ed56e3968fdf7e420f7a
reload_operation: op=add_agent agent=agent2 window=main reason=agent exists only in new config
reload_drain_active_count: 0
reload_namespace_patch_status: planned
reload_namespace_patch_apply_deferred: true
reload_namespace_patch_step: action=create_agent_pane window=main agent=agent2 role=agent slot_key=agent2 managed_by=ccbd anchor_agent=agent1 reason=new agent appended to existing managed window
reload_reason: add_agent agent2: agent exists only in new config
```

## reload apply

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> reload
exit_code: 0
--- stdout ---
reload_status: published
dry_run: false
mutation_enabled: true
plan_class: add_agent
safe_to_apply: true
future_safe_to_apply: true
old_config_signature: 34e1f57f208c3e9c5e28816bd930f6fffcb4a29648cedf72004ce9fe7cef7e3e
new_config_signature: 89a33ade6817c0f74910cda7759b7adaca13c693f6c9ed56e3968fdf7e420f7a
reload_stage: publish_transaction
reload_old_graph_version: 1
reload_target_graph_version: 2
reload_published_graph_version: 2
reload_diagnostic: graph_published=true
reload_diagnostic: lease_or_lifecycle_written=true
reload_diagnostic: config_watch_started=false
reload_diagnostic: unload_or_replace_executed=false
reload_diagnostic: project_view_cache_invalidated=true
reload_diagnostic: sidebar_refresh_signal_sent=false
reload_operation: op=add_agent agent=agent2 window=main reason=agent exists only in new config
reload_drain_active_count: 0
reload_namespace_patch_status: planned
reload_namespace_patch_apply_deferred: true
reload_namespace_patch_step: action=create_agent_pane window=main agent=agent2 role=agent slot_key=agent2 managed_by=ccbd anchor_agent=agent1 reason=new agent appended to existing managed window
reload_reason: add_agent agent2: agent exists only in new config
```

## restart unsupported/deferred evidence

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> restart agent1
exit_code: 1
--- stdout ---
restart_status: deferred
agent_name: agent1
restartable_agents: agent1, agent2
reason: deferred_to_provider_runtime_on_herdr
restart_busy_gate: passed=true runtime_state=failed runtime_queue_depth=0 queue_depth=0 pending_reply_count=0 active_job_id=None active_inbound_event_id=None pending_callback_count=0
old_runtime: state=failed health=start-failed pane_id=None active_pane_id=None runtime_ref=None session_ref=None runtime_pid=None restart_count=1
new_runtime: state=failed health=start-failed pane_id=None active_pane_id=None runtime_ref=None session_ref=None runtime_pid=None restart_count=1
restart_result: agent=agent1 status=deferred reason=deferred_to_provider_runtime_on_herdr backend_impl=herdr namespace_backend_family=herdr-native restart_mode=provider_runtime_required
```

## kill

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> kill
exit_code: 0
--- stdout ---
kill_status: ok
project_id: 80548bf0b37fa9cb23169f14ea9bfa82fd92433bdd94de069b24c5a74cdcd51b
state: unmounted
socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\ccbd.sock
forced: false
```

## post-kill ping

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> ping ccbd
exit_code: 0
--- stdout ---
project_id: 80548bf0b37fa9cb23169f14ea9bfa82fd92433bdd94de069b24c5a74cdcd51b
mount_state: unmounted
health: unmounted
generation: 1
project_anchor_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb
runtime_state_root: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb
runtime_root_kind: project
runtime_relocation_reason: None
runtime_filesystem_hint: None
runtime_marker_status: not_required
socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\ccbd.sock
preferred_socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\ccbd.sock
effective_socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\ccbd.sock
socket_root_kind: project
socket_fallback_reason: None
socket_filesystem_hint: None
tmux_socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\tmux.sock
tmux_preferred_socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\tmux.sock
tmux_effective_socket_path: D:\tmp\ccb-herdr-cmd-013-20260802-225336\.ccb\ccbd\tmux.sock
tmux_socket_root_kind: project
tmux_socket_fallback_reason: None
tmux_socket_filesystem_hint: None
last_heartbeat_at: 2026-08-02T14:53:46.722384Z
pid_alive: True
socket_connectable: False
heartbeat_fresh: True
takeover_allowed: True
reason: lease_unmounted
startup_id: f4aa651d5933403aa8c228820ba70aed
startup_stage: None
last_progress_at: 2026-08-02T14:53:55.345717Z
startup_deadline_at: None
last_failure_reason: None
shutdown_intent: stop_all
last_request_queue_wait_s: None
last_submit_duration_s: None
last_ping_duration_s: None
last_maintenance_duration_s: None
last_heartbeat_duration_s: None
pending_maintenance_ticks: None
service_graph_version: None
service_graph_created_at: None
service_graph_retained_count: None
service_graph_retained_count_scope: None
```

## herdr server stop cleanup

```text
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-cmd-013-20260802-225336 server stop
exit_code: 0
```

## herdr preflight server stop cleanup

```text
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-cmd-013-20260802-225336-preflight server stop
exit_code: 1
--- stderr ---
server is not running or cannot be reached at D:\tmp\ccb-herdr-cmd-013-20260802-225336\.home\AppData\Roaming\herdr\sessions\ccb-cmd-013-20260802-225336-preflight\herdr.sock: 系统找不到指定的文件。 (os error 2)
```

## herdr namespace server stop cleanup

```text
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-ccb-herdr-cmd-013-20260802-225336-80548bf0 server stop
exit_code: 0
```

## Verdict

passed
