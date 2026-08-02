# ccbd-windows-control-plane-transport

- Roadmap item: `ccbd-windows-control-plane-transport`
- Design: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md`
- Checklist: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-checklist.yaml`
- Design review: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design-review.md`
- Review: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-review.md`
- QA: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-qa.md`
- Acceptance: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-acceptance.md`
- Depends on: `herdr-backend-client`
- Nature: mixed
- Core runtime path: ccbd control-plane endpoint, Unix AF_UNIX adapter, Windows TCP loopback + same-user token adapter, bootstrap self-ping and diagnostics redaction.
- Mandatory commands: approved checklist `dod.commands`.
- Evidence required: transport seam tests, Windows TCP loopback/token tests, Unix regression, bootstrap regression, redaction/scope guard, Native Windows CMD-013 retry transcript.
- Failure recovery: keep Herdr namespace lifecycle, provider runtime, recovery, Mobile/Config UI and release/update changes out of this feature.
