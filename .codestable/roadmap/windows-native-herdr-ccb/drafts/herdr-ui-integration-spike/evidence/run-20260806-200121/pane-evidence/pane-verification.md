# Pane materialization verification
- snapshot_source: herdr-api-snapshot-after
- capture_session: 
- capture_lines: 20

- snapshot_available: true
- pane_count: 2
- workspace_count: 1

## Pane identity

- pane_id=w1:p1 title= display_agent=
- pane_id=w1:p2 title= display_agent=

## Workspaces
- workspace_id=w1 label=claude_code_bridge

## Pane content capture

- pane_id=w1:p1 exit_code=0 tail=ps1" -ProjectRoot "E:\GitHub开源项目\TachiKuma\claude_code_bridge" -ObservedWindowsFlash -ObservedHerdrAgentsPanelText  "codex"
 Herdr UI integration spike
    running ccb8-doctor-output
    E:\GitHub开源项目
- pane_id=w1:p2 exit_code=0 tail=    launched ccb8-start-project (pid 17940, running)
    D:\C#Project\GitHub\AvaPrintDesigner\ccb8.cmd
异异常常:
    em.ArgumentOutOfRangeException: 该值必须大于或等于零，且必须小于控制台缓冲区在该维度的大小。
参数名: top
实际值是 -2。
   在 S
