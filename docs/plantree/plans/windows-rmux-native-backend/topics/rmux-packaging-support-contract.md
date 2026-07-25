# Windows Rmux Packaging Support Contract

## Support Tier

Native Windows Rmux is **beta opt-in** for the source / `install.ps1` route.

The support tier is not set by README wording. The single machine-readable owner is
`terminal_runtime.rmux_packaging_support.rmux_packaging_support_summary`, and `ccb doctor`,
diagnostic bundles, installer messaging, packaging tests, and docs guards consume that projection.

Allowed support tiers are:

- `blocked`: route approval or required capability evidence blocks use.
- `experimental`: evidence is incomplete and the route is diagnostic-only.
- `beta`: route approval, required capability evidence, and Windows validation evidence are good enough for explicit opt-in, but package or install gates still prevent a broader supported claim.
- `supported`: full validation, local install evidence, docs consistency, and packaging gates have all passed.

Current projection:

- `support_tier`: `beta`
- `install_entry`: `install_ps1`
- `windows_npm_enabled`: `false`
- `install_ps1_rmux_check`: `warn`
- `validation_ref`: `artifacts/rmux-windows-validation/rmux_windows_validation_report.json`

## Evidence Rules

`supported` requires all of the following:

- route approval is approved;
- required rmux capability gaps are closed;
- validation matrix has `selection_scope=full`;
- validation matrix has `full_matrix_status=pass`;
- true-host/manual Windows core rows are observed;
- docs consistency evidence is present;
- local install smoke evidence is present;
- npm is enabled only when Windows artifact, checksum, postinstall, package files, and docs strategy evidence has passed.

If any of those inputs are missing, the projection fails closed to `beta`, `experimental`, or `blocked`.

## npm No-Change Rationale

`package.json.os` stays `["linux", "darwin"]`. Native Windows Rmux is not exposed through
`npm install -g @seemseam/ccb` until a Windows artifact/checksum/postinstall gate passes.

Users on native Windows should use the source / `install.ps1` route for beta opt-in. Linux,
macOS, and WSL users should continue using the existing tmux route.

## Forbidden Release Actions

This contract does not authorize:

- `git push`;
- `git tag`;
- `npm publish`;
- release upload;
- making Windows Rmux the default backend.
