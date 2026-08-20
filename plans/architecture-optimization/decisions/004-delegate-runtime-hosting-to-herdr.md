# Delegate Runtime Hosting To Herdr

Date: 2026-08-20

## Context

Herdr `v0.8.2` adds stronger agent lifecycle behavior, including readiness
waiting, idle/working/blocked state detection, native Windows agent support,
remote clients, and server-stop handling that bypasses pane/API traffic.

CCB currently integrates Herdr as a terminal backend, but still owns much of
the host-runtime startup path:

- `ccb.py` performs an early native-Windows Herdr gate.
- `handle_start()` probes Herdr, starts the server, and injects capability
  evidence.
- `platforms/windows/herdr/bootstrap.py` discovers sessions, starts servers,
  waits for readiness, probes capabilities, and writes a temporary capability
  report.
- `HerdrCliRequestAdapter` translates many CCB operations into separate Herdr
  CLI calls.
- CCB maintains the Herdr operation whitelist and performs extra pane-agent
  registration and state reporting.

Representative evidence:

- `ccb.py:42-60, 159-171`
- `lib/cli/phase2_runtime/handlers_start.py:89-114, 175-252`
- `lib/platforms/windows/herdr/bootstrap.py:38-159`
- `lib/platforms/windows/herdr/runtime/cli.py:23-116`
- `lib/cli/services/runtime_launch_runtime/tmux_runtime.py:289-319`
- Herdr release `v0.8.2`, published 2026-08-19:
  https://github.com/herdrdev/herdr/releases/tag/v0.8.2

## Decision

Evolve the boundary to:

> Herdr owns the host runtime; CCB owns the collaboration control plane.

Herdr should own:

- server, session, workspace, tab/window, and pane lifecycle;
- process launch, readiness, exit, restart, attach, focus, and layout;
- generic agent state detection and runtime events;
- generic pane cleanup, restart backoff, and resource ownership;
- terminal UI, remote attachment, and host-window presentation.

CCB should retain ownership of:

- `ccbd`, keeper, startup fences, and project control-plane state;
- Provider commands, isolated Provider homes, credentials, and native sessions;
- asks, jobs, queues, replies, cancellation, collaboration graphs, and memory;
- Provider-specific completion, resume/fork, continuation, and recovery policy;
- authorization, command approval, and business-level failure decisions.

The target startup contract is a declarative CCB runtime manifest submitted to a
single Herdr runtime operation:

```text
CCB manifest
    -> Herdr ensure_runtime()
    -> workspace/session/pane handles and readiness events
    -> CCB attaches ccbd and Provider business state
```

The first contract should return stable server/session/workspace/pane handles,
runtime generation, readiness, and capability data in one structured response.
CCB should not need a temporary `CCB_HERDR_CAPABILITY_REPORT` file for normal
startup.

## Consequences

Positive:

- CCB startup loses platform-specific server discovery and repeated Herdr CLI
  orchestration.
- Herdr can apply one consistent lifecycle policy across all managed panes.
- CCB can consume runtime events instead of polling or interpreting terminal
  text for generic process state.
- Capability and readiness evidence become one runtime contract rather than
  several environment variables, probes, and temporary files.

Constraints:

- Provider session semantics must remain in CCB; moving them into Herdr would
  create two coupled business authorities.
- Existing startup and Provider isolation contracts remain authoritative.
- The migration must preserve fail-closed identity checks for project,
  namespace, pane, session, and runtime generation.
- Herdr should not receive raw credentials through the manifest; CCB retains
  credential authority and passes only authorized references or scoped
  environment projections.

## Migration Order

1. Introduce a persistent Herdr runtime client and one handshake that returns
   server info, capabilities, and generation.
2. Add a declarative runtime manifest and an `ensure_runtime`-style Herdr
   contract; keep the current bootstrap as a compatibility adapter.
3. Move generic workspace/pane readiness, liveness, and restart handling to
   Herdr; keep Provider recovery in CCB.
4. Replace CCB startup capability files and import-time Herdr checks with
   operation-time contract validation.
5. Add Herdr runtime events and make `ccbd` consume them for pane/agent
   lifecycle projection.
6. Only after the contract is proven, simplify or remove the legacy
   `HerdrCliRequestAdapter` and bootstrap paths.

## Non-Goals

This decision does not move CCB's message bureau, Provider session authority,
ask cancellation semantics, credentials, or Provider-specific recovery into
Herdr.
