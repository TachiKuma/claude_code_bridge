---
doc_type: feature-evidence
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
command_id: CMD-013
kind: native-windows-herdr-transcript
updated_at: 2026-08-02
---

# CMD-013 Native Windows Herdr Transcript

- workdir: `C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112`
- repo: `D:\Python\GitHub\claude_code_bridge`
- herdr_exe: `C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe`
- herdr_session: `ccb-cmd-013-20260802-093112`
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
Refresh project memory/context under C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112\.ccb? [y/N]
--- stderr ---
command_status: failed
error: timed out
```

## ccbd ping namespace payload

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> ping ccbd
exit_code: 1
--- stderr ---
command_status: failed
error: timed out
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
project_id: a09f5681b4cb720858d154ef8e462de8ec2ce55af39bf2e920fe74b0eeec2766
state: unmounted
socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112\.ccb\ccbd\ccbd.sock
forced: false
```

## post-kill ping

```text
$ C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -c <cmd013-wrapper> ping ccbd
exit_code: 0
--- stdout ---
project_id: a09f5681b4cb720858d154ef8e462de8ec2ce55af39bf2e920fe74b0eeec2766
mount_state: unmounted
health: stale
generation: 1
project_anchor_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112\.ccb
runtime_state_root: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112\.ccb
runtime_root_kind: project
runtime_relocation_reason: None
runtime_filesystem_hint: None
runtime_marker_status: not_required
socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112\.ccb\ccbd\ccbd.sock
preferred_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112\.ccb\ccbd\ccbd.sock
effective_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112\.ccb\ccbd\ccbd.sock
socket_root_kind: project
socket_fallback_reason: None
socket_filesystem_hint: None
tmux_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112\.ccb\ccbd\tmux.sock
tmux_preferred_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112\.ccb\ccbd\tmux.sock
tmux_effective_socket_path: C:\Users\Administrator\AppData\Local\Temp\ccb-herdr-cmd-013-20260802-093112\.ccb\ccbd\tmux.sock
tmux_socket_root_kind: project
tmux_socket_fallback_reason: None
tmux_socket_filesystem_hint: None
last_heartbeat_at: 2026-08-02T01:32:04.078303Z
pid_alive: False
socket_connectable: False
heartbeat_fresh: True
takeover_allowed: True
reason: pid_missing,socket_unreachable
startup_id: aafae792638b4964b66e3df73a5fc259
startup_stage: None
last_progress_at: 2026-08-02T01:32:06.573272Z
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
$ C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --session ccb-cmd-013-20260802-093112 server stop
exit_code: 1
--- stderr ---
server is not running or cannot be reached at C:\Users\Administrator\AppData\Roaming\herdr\sessions\ccb-cmd-013-20260802-093112\herdr.sock: 系统找不到指定的文件。 (os error 2)
```

## Verdict

blocked: namespace create, ccbd ping, foreground attach, reload apply
