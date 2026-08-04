# Herdr UI integration spike report

- run_id: run-20260804-192845
- classification: blocked-not-herdr-ui
- output_dir: E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845
- process_samples: E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\process-samples.jsonl
- observed_windows_flash: True
- observed_herdr_agents_panel_text: claude

## Commands

- herdr-version: exit=0 timed_out=False ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\herdr-version.json
- herdr-status-server-before: exit=124 timed_out=True ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\herdr-status-server-before.json
- herdr-workspace-list-before: exit=124 timed_out=True ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\herdr-workspace-list-before.json
- herdr-pane-list-before: exit=124 timed_out=True ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\herdr-pane-list-before.json
- ccb8-wrapper-self-test: exit=2 timed_out=False ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\ccb8-wrapper-self-test.json
- ccb8-diagnose: exit=0 timed_out=False ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\ccb8-diagnose.json
- ccb8-start-new-context: exit=124 timed_out=True ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\ccb8-start-new-context.json
- herdr-status-server-after: exit=124 timed_out=True ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\herdr-status-server-after.json
- herdr-workspace-list-after: exit=124 timed_out=True ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\herdr-workspace-list-after.json
- herdr-pane-list-after: exit=124 timed_out=True ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\herdr-pane-list-after.json
- ccb8-ping-ccbd: exit=0 timed_out=False ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\ccb8-ping-ccbd.json
- ccb8-ping-all: exit=0 timed_out=False ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\ccb8-ping-all.json
- ccb8-ps: exit=0 timed_out=False ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\ccb8-ps.json
- ccb8-doctor-ps: exit=0 timed_out=False ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\ccb8-doctor-ps.json
- ccb8-layout-status: exit=0 timed_out=False ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\ccb8-layout-status.json
- ccb8-doctor-output: exit=0 timed_out=False ref=E:\GitHub开源项目\TachiKuma\claude_code_bridge\.codestable\roadmap\windows-native-herdr-ccb\drafts\herdr-ui-integration-spike\evidence\run-20260804-192845\raw-command-refs\ccb8-doctor-output.json

## Interpretation

- If `process-samples.jsonl` contains short-lived `cmd.exe` / `powershell.exe` children but CCB ping is not mounted, classify as startup wrapper failure.
- If CCB ping is mounted but Herdr pane/workspace list lacks expected provider panes, classify as layout/materialization projection gap.
- If Herdr agents panel shows `claude` while CCB runtime state is failed, treat Herdr agent detection as diagnostics-only evidence, not completion authority.

