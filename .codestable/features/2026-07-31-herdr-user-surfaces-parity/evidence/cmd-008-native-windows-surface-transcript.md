---
doc_type: feature-evidence
feature: 2026-07-31-herdr-user-surfaces-parity
command_id: CMD-008
kind: native-windows-x64-surface-transcript
updated_at: 2026-08-03
---

# CMD-008 Native Windows x64 Surface Transcript

## 采集边界

- Host：Windows native x64，`sys_platform=win32`，`machine=AMD64`，Python `64bit`。
- Python：`C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe`。
- Herdr：`C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --version` -> `herdr 0.7.5-preview.2026-07-29-44b3adb12552`。
- true-host Herdr namespace 证据：`.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/evidence/cmd-013-native-windows-herdr-transcript.md`，同一 roadmap 下已验收，verdict `passed`，覆盖 Herdr namespace create、ccbd ping、foreground attach、reload、restart deferred、kill/post-kill。
- 本 transcript 只证明本 feature surface 投影与 blocked/pass gate；不声明 Windows x64 CCB 最终 supported。

## fresh 验证命令

```text
$ python -m pytest -q "test/test_v2_start_foreground.py::test_start_foreground_herdr_attach_uses_builder_without_tmux_binary" "test/test_v2_start_foreground.py::test_start_foreground_herdr_attach_blocked_error_includes_projection" "test/test_mobile_gateway_service.py::test_terminal_history_returns_herdr_blocked_payload" "test/test_mobile_gateway_service.py::test_terminal_history_uses_herdr_backend_neutral_target" "test/test_mobile_gateway_service.py::test_agent_message_submit_returns_herdr_input_blocked_payload" "test/test_mobile_gateway_service.py::test_agent_message_submit_uses_herdr_backend_neutral_target" "test/test_mobile_gateway_service.py::test_terminal_attach_target_raises_herdr_attach_blocked_payload" "test/test_mobile_gateway_service.py::test_terminal_websocket_uses_herdr_backend_neutral_target" "test/test_config_ui.py::test_config_ui_session_projects_herdr_readonly_status" "test/test_v2_cli_render.py::test_render_ps_and_layout_include_herdr_surface_projection"
..........                                                               [100%]
10 passed in 2.79s
```

## surface transcript

### foreground attach pass

```json
{
  "backend_impl": "herdr",
  "namespace_id": "workspace-1",
  "session_name": "ccb-herdr",
  "ipc_kind": "herdr_socket",
  "namespace_restore_token_present": true,
  "tmux_fallback": "not_called",
  "attach_window": "main"
}
```

### foreground attach blocked

```text
ready: false
error: Herdr project namespace is not attachable after successful `ccb` start (capability_status=blocked, support_tier_projection=experimental, support_tier_source=validation_pending, beta_gaps=foreground-attach-validation-pending, blocking_gaps=attach_unsupported, next_action=collect-validation-transcript)
```

### Mobile terminal blocked

```json
{
  "history": {
    "http_status": 409,
    "status": "blocked",
    "terminal_blocked": {
      "code": "history_unsupported",
      "backend_impl": "herdr",
      "capability_status": "blocked",
      "beta_gaps": ["mobile-terminal-validation-pending"],
      "blocking_gaps": ["mobile-terminal-adapter-unavailable"],
      "degraded_next_action": "collect-validation-transcript"
    }
  },
  "message": {
    "http_status": 409,
    "status": "blocked",
    "terminal_blocked": {
      "code": "input_unsupported",
      "backend_impl": "herdr",
      "degraded_next_action": "collect-validation-transcript"
    },
    "sender_called": false
  },
  "attach": {
    "status_code": 409,
    "terminal_blocked": {
      "code": "attach_unsupported",
      "backend_impl": "herdr",
      "degraded_next_action": "collect-validation-transcript"
    }
  }
}
```

### Mobile terminal pass

```json
{
  "history": {
    "http_status": 200,
    "status": "ok",
    "history_scope": "herdr_pane_history",
    "target": {
      "backend_impl": "herdr",
      "socket_path": "",
      "session_name": "ccb-herdr",
      "namespace_id": "workspace-1",
      "pane_ref": {"backend_impl": "herdr", "pane_id": "pane-1"},
      "history_supported": true
    }
  },
  "message": {
    "http_status": 202,
    "status": "ok",
    "target": {
      "backend_impl": "herdr",
      "socket_path": "",
      "session_name": "ccb-herdr",
      "namespace_id": "workspace-1",
      "pane_ref": {"backend_impl": "herdr", "pane_id": "pane-1"},
      "input_supported": true
    }
  },
  "attach_target": {
    "backend_impl": "herdr",
    "socket_path": "",
    "session_name": "ccb-herdr",
    "namespace_id": "workspace-1",
    "pane_ref": {"backend_impl": "herdr", "pane_id": "pane-1"},
    "attach_supported": true
  }
}
```

### Config UI blocked/pass

```json
{
  "blocked_session": {
    "schema_version": 2,
    "mode": "editor",
    "herdr_surface_projection": {
      "backend_impl": "herdr",
      "capability_status": "partial",
      "support_tier_projection": "experimental",
      "support_tier_projection_source": "validation_pending",
      "beta_gaps": ["validation_pending"]
    },
    "config_ui_readonly_status": {
      "status": "blocked",
      "backend_impl": "herdr",
      "reason": "capability_status=partial",
      "degraded_next_action": null
    }
  },
  "pass_gate_for_supported_projection": {
    "status": "pass",
    "backend_impl": "herdr",
    "reason": null,
    "degraded_next_action": null
  }
}
```

### ping / project view

```json
{
  "ping_ccbd_projection_excerpt": {
    "project_id": "proj-herdr",
    "mount_state": "mounted",
    "namespace_backend_impl": "herdr",
    "herdr_surface_projection": {
      "backend_impl": "herdr",
      "capability_status": "partial",
      "support_tier_projection": "experimental",
      "support_tier_projection_source": "validation_pending",
      "beta_gaps": ["mobile-terminal-validation-pending"],
      "blocking_gaps": ["config-ui-validation-pending"],
      "degraded_next_action": "collect-validation-transcript"
    }
  },
  "project_view_projection_excerpt": {
    "namespace": {
      "namespace_backend_family": "herdr-native",
      "namespace_backend_impl": "herdr",
      "namespace_id": "workspace-1",
      "namespace_session_name": "ccb-herdr",
      "namespace_ipc_kind": "herdr_socket",
      "herdr_surface_projection": "same projection"
    },
    "agents": [{"name": "mobile", "herdr_surface_projection": "same projection"}]
  }
}
```

### doctor / mounted

```text
ccbd_herdr_surface: capability_status=partial support_tier_projection=experimental source=validation_pending beta_gaps=mobile-terminal-validation-pending blocking_gaps=config-ui-validation-pending next_action=collect-validation-transcript
ccbd_herdr_namespace_ref: backend_impl=herdr,ipc_kind=herdr_socket,namespace_id=workspace-1,session_name=ccb-herdr
ccbd_herdr_pane_ref: backend_impl=herdr,pane_id=pane-1

project_id: proj-herdr
ccbd_state: mounted
herdr_surface: capability_status=partial support_tier_projection=experimental source=validation_pending beta_gaps=mobile-terminal-validation-pending blocking_gaps=config-ui-validation-pending next_action=collect-validation-transcript
herdr_namespace_ref: backend_impl=herdr,ipc_kind=herdr_socket,namespace_id=workspace-1,session_name=ccb-herdr
herdr_pane_ref: backend_impl=herdr,pane_id=pane-1
```

## redaction / supportability guard

- Harness 输入含 raw restore token sentinel；输出未包含 sentinel。
- Public excerpts 只记录 `namespace_restore_token_present=true` 或省略 raw token；不记录 provider secret 或 terminal buffer 全量。
- Mobile blocked 样例均是 `status=blocked`，不会被后续 supportability 当成 supported。
- Config UI partial 样例是 `config_ui_readonly_status.status=blocked`；只有 supported projection 才返回 pass gate。
- `support_tier_projection` 仅为 `experimental` / `beta` 投影，不是最终 support tier claim。

## Verdict

passed
