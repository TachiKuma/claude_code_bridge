---
doc_type: feature-evidence
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
command_id: CMD-013
kind: native-windows-herdr-transcript
updated_at: 2026-08-02
---

# CMD-013 Native Windows Herdr Transcript

- workdir: `C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509`
- repo: `D:\Python\GitHub\claude_code_bridge`
- herdr_exe: `C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe`
- herdr_session: `ccb-cmd-013-20260802-183509`
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
Refresh project memory/context under C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb? [y/N]
--- stderr ---
command_status: failed
error: [WinError 10054] 远程主机强迫关闭了一个现有的连接。
```

## ccbd ping namespace payload

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> ping ccbd
exit_code: 0
--- stdout ---
project_id: 06ece5f04a1cab4c3c7515176bd63c6f940e5b76633dd58618fdbd91bb041595
mount_state: mounted
desired_state: running
health: healthy
generation: 2
socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\ccbd.sock
control_plane_endpoint: {'kind': 'tcp_loopback', 'address': '127.0.0.1:59814', 'display': '127.0.0.1:59814', 'legacy_socket_path': None, 'auth_ref': 'C:\\Users\\Administrator\\AppData\\Local\\Temp\\ccb-herdr-cmd-013-20260802-183509\\.ccb\\ccbd\\control-plane-token-5e08abbec09f456a.json', 'fingerprint': '41cee48d55a4df62', 'socket_path': None, 'host': '127.0.0.1', 'port': 59814, 'token_ref': 'C:\\Users\\Administrator\\AppData\\Local\\Temp\\ccb-herdr-cmd-013-20260802-183509\\.ccb\\ccbd\\control-plane-token-5e08abbec09f456a.json', 'generation': '8b0399bb4555b196', 'acl_status': 'windows-icacls-user-read'}
tmux_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\tmux.sock
project_anchor_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb
runtime_state_root: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb
runtime_root_kind: project
runtime_relocation_reason: None
runtime_filesystem_hint: None
runtime_marker_status: not_required
runtime_root_marker_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\runtime-root.json
runtime_root_ref_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\runtime-root-ref.json
preferred_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\ccbd.sock
effective_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\ccbd.sock
socket_root_kind: project
socket_fallback_reason: None
socket_filesystem_hint: None
tmux_preferred_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\tmux.sock
tmux_effective_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\tmux.sock
tmux_socket_root_kind: project
tmux_socket_fallback_reason: None
tmux_socket_filesystem_hint: None
known_agents: ['agent1']
config_signature: 34e1f57f208c3e9c5e28816bd930f6fffcb4a29648cedf72004ce9fe7cef7e3e
serving_pid: 12296
serving_daemon_instance_id: 943ef8b4ef15463f8b3fb59842345692
serving_lease_generation: 2
serving_startup_generation: 2
accepted_startup_id: 2a8267c622be49a584569d42b9f6acba
namespace_epoch: 1
namespace_tmux_socket_path: 
namespace_tmux_session_name: ccb-ccb-herdr-cmd-013-20260802-183509-06ece5f0
namespace_backend_family: herdr-native
namespace_backend_impl: herdr
namespace_id: ccb-ccb-herdr-cmd-013-20260802-183509-06ece5f0
namespace_session_name: ccb-ccb-herdr-cmd-013-20260802-183509-06ece5f0
namespace_ipc_kind: herdr_socket
namespace_ipc_ref: herdr://cmd-013-local
namespace_restore_token_present: False
namespace_layout_version: 3
namespace_control_window_name: __ccb_ctl
namespace_control_window_id: None
namespace_workspace_window_name: main
namespace_workspace_window_id: w1
namespace_workspace_epoch: 1
namespace_ui_attachable: True
namespace_last_started_at: 2026-08-02T10:35:11.596284Z
namespace_last_destroyed_at: None
namespace_last_destroy_reason: None
namespace_last_event_kind: namespace_created
namespace_last_event_at: 2026-08-02T10:35:11.596284Z
namespace_last_event_epoch: 1
namespace_last_event_socket_path: None
namespace_last_event_session_name: ccb-ccb-herdr-cmd-013-20260802-183509-06ece5f0
namespace_last_event_backend_family: herdr-native
namespace_last_event_backend_impl: herdr
namespace_last_event_id: ccb-ccb-herdr-cmd-013-20260802-183509-06ece5f0
namespace_last_event_ipc_kind: herdr_socket
namespace_last_event_ipc_ref: herdr://cmd-013-local
namespace_last_event_restore_token_present: False
pid_alive: True
socket_connectable: True
heartbeat_fresh: True
takeover_allowed: False
reason: healthy
startup_id: 2a8267c622be49a584569d42b9f6acba
startup_stage: mounted
last_progress_at: 2026-08-02T10:35:44.201266Z
startup_deadline_at: None
last_failure_reason: None
shutdown_intent: None
last_request_queue_wait_s: 1.2899996363557875e-05
last_submit_duration_s: None
last_ping_duration_s: 0.0008985000022221357
last_handler_latency_s_by_op: {'ping': 0.000910000002477318}
last_maintenance_duration_s: None
last_heartbeat_duration_s: None
heartbeat_step_duration_s: {}
last_heartbeat_agents_inspected: None
last_heartbeat_runtime_store_writes: None
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
service_graph_created_at: 2026-08-02T10:35:43.902998Z
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
last_restore_at: 2026-08-02T10:35:44.196186Z
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
error: [WinError 10054] 远程主机强迫关闭了一个现有的连接。
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
exit_code: 1
--- stderr ---
command_status: failed
error: ccbd is unavailable: heartbeat_stale,socket_unreachable
```

## reload apply

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> reload
exit_code: 1
--- stderr ---
command_status: failed
error: project ccbd is starting; wait for keeper to finish startup
```

## restart unsupported/deferred evidence

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> restart agent1
exit_code: 1
--- stderr ---
command_status: failed
error: project ccbd is starting; wait for keeper to finish startup
```

## kill

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> kill
exit_code: 0
--- stdout ---
kill_status: ok
project_id: 06ece5f04a1cab4c3c7515176bd63c6f940e5b76633dd58618fdbd91bb041595
state: unmounted
socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\ccbd.sock
forced: false
```

## post-kill ping

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> ping ccbd
exit_code: 0
--- stdout ---
project_id: 06ece5f04a1cab4c3c7515176bd63c6f940e5b76633dd58618fdbd91bb041595
mount_state: unmounted
health: unmounted
generation: 3
project_anchor_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb
runtime_state_root: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb
runtime_root_kind: project
runtime_relocation_reason: None
runtime_filesystem_hint: None
runtime_marker_status: not_required
socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\ccbd.sock
preferred_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\ccbd.sock
effective_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\ccbd.sock
socket_root_kind: project
socket_fallback_reason: None
socket_filesystem_hint: None
tmux_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\tmux.sock
tmux_preferred_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\tmux.sock
tmux_effective_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-183509\.ccb\ccbd\tmux.sock
tmux_socket_root_kind: project
tmux_socket_fallback_reason: None
tmux_socket_filesystem_hint: None
last_heartbeat_at: 2026-08-02T10:36:08.835521Z
pid_alive: False
socket_connectable: False
heartbeat_fresh: True
takeover_allowed: True
reason: lease_unmounted
startup_id: 2271522cd0714d16984800a9fd69151f
startup_stage: None
last_progress_at: 2026-08-02T10:36:08.922559Z
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
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-cmd-013-20260802-183509 server stop
exit_code: 1
--- stderr ---
server is not running or cannot be reached at C:\Users\Administrator\AppData\Roaming\herdr\sessions\ccb-cmd-013-20260802-183509\herdr.sock: 系统找不到指定的文件。 (os error 2)
```

## Verdict

blocked: namespace create, foreground attach, reload dry run, reload apply
