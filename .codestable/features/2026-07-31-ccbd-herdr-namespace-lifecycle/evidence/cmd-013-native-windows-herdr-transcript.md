---
doc_type: feature-evidence
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
command_id: CMD-013
kind: native-windows-herdr-transcript
updated_at: 2026-08-02
---

# CMD-013 Native Windows Herdr Transcript

- workdir: `C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044`
- repo: `D:\Python\GitHub\claude_code_bridge`
- herdr_exe: `C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe`
- herdr_session: `ccb-cmd-013-20260802-144044`
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

## namespace create via ccb -n

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> --cmd013-confirm-stdin -n
exit_code: 1
--- stdout ---
Refresh project memory/context under C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb? [y/N]
--- stderr ---
command_status: failed
error: mux backend lacks required method for ensure_window
```

## ccbd ping namespace payload

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> ping ccbd
exit_code: 0
--- stdout ---
project_id: 8f09d3952cdf370344d90e05b9745c6905ec9e2dd2334c0f1ad9012b100573bd
mount_state: mounted
desired_state: running
health: healthy
generation: 1
socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\ccbd.sock
control_plane_endpoint: {'kind': 'tcp_loopback', 'address': '127.0.0.1:57027', 'display': '127.0.0.1:57027', 'legacy_socket_path': None, 'auth_ref': 'C:\\Users\\Administrator\\AppData\\Local\\Temp\\ccb-herdr-cmd-013-20260802-144044\\.ccb\\ccbd\\control-plane-token-a9cd44a3b391444d.json', 'fingerprint': 'b8cd74f31326fcd1', 'socket_path': None, 'host': '127.0.0.1', 'port': 57027, 'token_ref': 'C:\\Users\\Administrator\\AppData\\Local\\Temp\\ccb-herdr-cmd-013-20260802-144044\\.ccb\\ccbd\\control-plane-token-a9cd44a3b391444d.json', 'generation': '504788a545563270', 'acl_status': 'windows-icacls-user-read'}
tmux_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\tmux.sock
project_anchor_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb
runtime_state_root: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb
runtime_root_kind: project
runtime_relocation_reason: None
runtime_filesystem_hint: None
runtime_marker_status: not_required
runtime_root_marker_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\runtime-root.json
runtime_root_ref_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\runtime-root-ref.json
preferred_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\ccbd.sock
effective_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\ccbd.sock
socket_root_kind: project
socket_fallback_reason: None
socket_filesystem_hint: None
tmux_preferred_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\tmux.sock
tmux_effective_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\tmux.sock
tmux_socket_root_kind: project
tmux_socket_fallback_reason: None
tmux_socket_filesystem_hint: None
known_agents: ['agent1']
config_signature: 34e1f57f208c3e9c5e28816bd930f6fffcb4a29648cedf72004ce9fe7cef7e3e
serving_pid: 17216
serving_daemon_instance_id: 566b3a061d814fe3a79ec932a6245f8a
serving_lease_generation: 1
serving_startup_generation: 1
accepted_startup_id: 8759047fac7c4702b1c0c7483f7e9db2
pid_alive: True
socket_connectable: True
heartbeat_fresh: True
takeover_allowed: False
reason: healthy
startup_id: 8759047fac7c4702b1c0c7483f7e9db2
startup_stage: mounted
last_progress_at: 2026-08-02T06:40:46.276047Z
startup_deadline_at: None
last_failure_reason: None
shutdown_intent: None
last_request_queue_wait_s: 3.300000389572233e-05
last_submit_duration_s: None
last_ping_duration_s: 0.000647599998046644
last_handler_latency_s_by_op: {'ping': 0.0006563000060850754, 'start': 0.15460750000784174}
last_maintenance_duration_s: 0.001479700003983453
last_heartbeat_duration_s: 0.001479700003983453
heartbeat_step_duration_s: {'health_monitor': 3.2199997804127634e-05, 'runtime_supervision': 9.600000339560211e-05, 'dispatcher_runtime_views': 2.0099992980249226e-05, 'dispatcher_tick': 0.00010829999519046396, 'dispatcher_poll_completions': 2.339998900424689e-05, 'reload_drain_auto_retry': 2.920000406447798e-05, 'job_heartbeat': 8.850000449456275e-05}
last_heartbeat_agents_inspected: 1
last_heartbeat_runtime_store_writes: 0
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
service_graph_created_at: 2026-08-02T06:40:45.723228Z
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
last_restore_at: 2026-08-02T06:40:46.271337Z
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
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper>
exit_code: 1
--- stderr ---
command_status: failed
error: mux backend lacks required method for ensure_window
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
reload_namespace_patch_status: blocked
reload_namespace_patch_apply_deferred: true
reload_namespace_patch_blocked: op=namespace_scope reason=current project namespace scope is unavailable or mismatched
reload_reason: add_agent agent2: agent exists only in new config
```

## reload apply

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> reload
exit_code: 1
--- stdout ---
reload_status: blocked
dry_run: false
mutation_enabled: false
plan_class: add_agent
safe_to_apply: false
future_safe_to_apply: true
old_config_signature: 34e1f57f208c3e9c5e28816bd930f6fffcb4a29648cedf72004ce9fe7cef7e3e
new_config_signature: 89a33ade6817c0f74910cda7759b7adaca13c693f6c9ed56e3968fdf7e420f7a
reload_stage: plan
reload_old_graph_version: 1
reload_diagnostic: reason=namespace_patch_plan_not_planned
reload_diagnostic: message=additive reload apply requires an unblocked namespace patch plan
reload_diagnostic: graph_published=false
reload_diagnostic: lease_or_lifecycle_written=false
reload_diagnostic: config_watch_started=false
reload_diagnostic: unload_or_replace_executed=false
reload_operation: op=add_agent agent=agent2 window=main reason=agent exists only in new config
reload_drain_active_count: 0
reload_namespace_patch_status: blocked
reload_namespace_patch_apply_deferred: true
reload_namespace_patch_blocked: op=namespace_scope reason=current project namespace scope is unavailable or mismatched
reload_reason: add_agent agent2: agent exists only in new config
reload_error: namespace_patch_plan_not_planned: additive reload apply requires an unblocked namespace patch plan
```

## restart unsupported/deferred evidence

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> restart agent1
exit_code: 1
--- stdout ---
restart_status: failed
agent_name: agent1
restartable_agents: agent1
reason: restart_exception
restart_busy_gate: passed=true runtime_state=missing runtime_queue_depth=0 queue_depth=0 pending_reply_count=0 active_job_id=None active_inbound_event_id=None pending_callback_count=0
old_runtime: state=missing health=missing pane_id=None active_pane_id=None runtime_ref=None session_ref=None runtime_pid=None restart_count=0
new_runtime: state=missing health=missing pane_id=None active_pane_id=None runtime_ref=None session_ref=None runtime_pid=None restart_count=0
error: project namespace is not mounted
```

## kill

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> kill
exit_code: 0
--- stdout ---
kill_status: ok
project_id: 8f09d3952cdf370344d90e05b9745c6905ec9e2dd2334c0f1ad9012b100573bd
state: unmounted
socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\ccbd.sock
forced: false
```

## post-kill ping

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> ping ccbd
exit_code: 0
--- stdout ---
project_id: 8f09d3952cdf370344d90e05b9745c6905ec9e2dd2334c0f1ad9012b100573bd
mount_state: unmounted
health: unmounted
generation: 1
project_anchor_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb
runtime_state_root: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb
runtime_root_kind: project
runtime_relocation_reason: None
runtime_filesystem_hint: None
runtime_marker_status: not_required
socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\ccbd.sock
preferred_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\ccbd.sock
effective_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\ccbd.sock
socket_root_kind: project
socket_fallback_reason: None
socket_filesystem_hint: None
tmux_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\tmux.sock
tmux_preferred_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\tmux.sock
tmux_effective_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-144044\.ccb\ccbd\tmux.sock
tmux_socket_root_kind: project
tmux_socket_fallback_reason: None
tmux_socket_filesystem_hint: None
last_heartbeat_at: 2026-08-02T06:40:50.282230Z
pid_alive: False
socket_connectable: False
heartbeat_fresh: True
takeover_allowed: True
reason: lease_unmounted
startup_id: 8759047fac7c4702b1c0c7483f7e9db2
startup_stage: None
last_progress_at: 2026-08-02T06:40:50.334361Z
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
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-cmd-013-20260802-144044 server stop
exit_code: 1
--- stderr ---
server is not running or cannot be reached at C:\Users\Administrator\AppData\Roaming\herdr\sessions\ccb-cmd-013-20260802-144044\herdr.sock: 系统找不到指定的文件。 (os error 2)
```

## Verdict

blocked: namespace create, foreground attach, reload apply
