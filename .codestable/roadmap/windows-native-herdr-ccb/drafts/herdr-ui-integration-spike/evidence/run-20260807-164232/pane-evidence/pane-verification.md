# Pane materialization verification
- snapshot_source: herdr-api-snapshot-ccb-namespace
- capture_session: ccb-avaprintdesigner-575a971f
- capture_lines: 20

- snapshot_available: true
- pane_count: 7
- workspace_count: 3

## Pane identity

- pane_id=w1:p1 title= display_agent=
- pane_id=w2:p1 title= display_agent=
- pane_id=w2:p3 title= display_agent=
- pane_id=w2:p2 title= display_agent=
- pane_id=w7:p1 title=sidebar display_agent=sidebar
  token: ccb_agent_label=sidebar
  token: ccb_is_cmd=0
  token: ccb_managed_by=ccbd
  token: ccb_namespace_epoch=6
  token: ccb_namespace_id=w7
  token: ccb_project_id=575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03
  token: ccb_role=sidebar
  token: ccb_root_pane=1
  token: ccb_sidebar_instance=main
  token: ccb_slot=sidebar:main
  token: ccb_window=main
- pane_id=w7:p3 title=agent_2 display_agent=agent_2
  token: ccb_is_cmd=0
  token: ccb_managed_by=ccbd
  token: ccb_order=1
  token: ccb_project_id=575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03
  token: ccb_session_id=ccb-agent_2-8af327daddb9
  token: ccb_slot=agent_2
- pane_id=w7:p2 title=agent_1 display_agent=agent_1
  token: ccb_is_cmd=0
  token: ccb_managed_by=ccbd
  token: ccb_order=0
  token: ccb_project_id=575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03
  token: ccb_session_id=ccb-agent_1-82a4eff85442
  token: ccb_slot=agent_1

## Workspaces
- workspace_id=w1 label=ccb-debug-probe
- workspace_id=w2 label=ccb-avaprintdesigner-575a971f
- workspace_id=w7 label=ccb-avaprintdesigner-575a971f

## Pane content capture

- pane_id=w1:p1 exit_code=0 tail=PS D:\C#Project\GitHub\AvaPrintDesigner>

- pane_id=w2:p1 exit_code=0 tail=PS D:\C#Project\GitHub\AvaPrintDesigner>

- pane_id=w2:p3 exit_code=0 tail=PS D:\C#Project\GitHub\AvaPrintDesigner>

- pane_id=w2:p2 exit_code=0 tail=\C#Pr
oject
\GitH
ub\Av
aPrin
tDesi
gner>

- pane_id=w7:p1 exit_code=0 tail=b寮€婧愰」鐩甛TachiKuma\claude_code_bridge\bin\ccb
-agent-sidebar' --ccbd-socket 'D:\.c8\rs\575a9
71fdf5a0c497a48228040a14841fb4529aaa476beb21d3
4e53f1629bc03\ccbd\ccbd.sock' --project-root '
D:\C#Project\G
- pane_id=w7:p3 exit_code=0 tail=    at defaultResolveImpl (node:internal/modul
es/cjs/loader:1059:19)
    at resolveForCJSWithHooks (node:internal/m
odules/cjs/loader:1064:22)
    at Module._load (node:internal/modules/cjs
/loader:1
- pane_id=w7:p2 exit_code=0 tail=cjs/loader:1421:15)
    at defaultResolveImpl (node:internal/modules/cjs/l
oader:1059:19)
    at resolveForCJSWithHooks (node:internal/modules/c
js/loader:1064:22)
    at Module._load (node:internal/m
