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

- pane_id=w1:p1 exit_code=0 tail= Herdr UI integration spike
    collecting CCB startup state files
    [oooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo                                  
- pane_id=w1:p2 exit_code=0 tail=实际值是 -2。
   在 System.Console.SetCursorPosition(Int32 left, Int32 top)
   在 Microsoft.PowerShell.PSConsoleReadLine.ReallyRender(RenderData renderData, String defaultColor)
   在 Microsoft.PowerShell.PSC
