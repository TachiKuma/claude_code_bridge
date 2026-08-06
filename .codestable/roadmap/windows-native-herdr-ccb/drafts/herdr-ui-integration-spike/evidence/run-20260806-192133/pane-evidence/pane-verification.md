# Pane materialization verification
- snapshot_source: herdr-api-snapshot-ccb-namespace
- capture_session: ccb-avaprintdesigner-575a971f
- capture_lines: 20

- snapshot_available: true
- pane_count: 5
- workspace_count: 2

## Pane identity

- pane_id=w1:p1 title= display_agent=
- pane_id=w3:p1 title=sidebar display_agent=sidebar
  token: ccb_agent_label=sidebar
  token: ccb_is_cmd=0
  token: ccb_managed_by=ccbd
  token: ccb_namespace_epoch=1
  token: ccb_namespace_id=w3
  token: ccb_project_id=575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03
  token: ccb_role=sidebar
  token: ccb_root_pane=1
  token: ccb_sidebar_instance=main
  token: ccb_slot=sidebar:main
  token: ccb_window=main
- pane_id=w3:p4 title=agent2 display_agent=agent2
  token: ccb_is_cmd=0
  token: ccb_managed_by=ccbd
  token: ccb_order=1
  token: ccb_project_id=575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03
  token: ccb_session_id=ccb-agent2-012516afa999
  token: ccb_slot=agent2
- pane_id=w3:p3 title=agent1 display_agent=agent1
  token: ccb_is_cmd=0
  token: ccb_managed_by=ccbd
  token: ccb_order=0
  token: ccb_project_id=575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03
  token: ccb_session_id=ccb-agent1-39fbdcb6bf09
  token: ccb_slot=agent1
- pane_id=w3:p2 title=cmd display_agent=cmd
  token: ccb_agent_label=cmd
  token: ccb_is_cmd=1
  token: ccb_managed_by=ccbd
  token: ccb_namespace_epoch=1
  token: ccb_project_id=575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03
  token: ccb_role=cmd
  token: ccb_slot=cmd
  token: ccb_window=main

## Workspaces
- workspace_id=w1 label=claude_code_bridge
- workspace_id=w3 label=ccb-avaprintdesigner-575a971f

## Pane content capture

- pane_id=w1:p1 exit_code=0 tail=PS E:\GitHub开源项目\TachiKuma\claude_code_bridge>

- pane_id=w3:p1 exit_code=0 tail=ocket 'D:\.c8\rs\575a971fdf5a0c497a48228040a14841fb452
9aaa476beb21d34e53f1629bc03\ccbd\ccbd.sock' --project-
root 'D:\C#Project\GitHub\AvaPrintDesigner' --pane-win
dow main"
sh : 无法将“sh”项识别为 cmdlet、函
- pane_id=w3:p4 exit_code=0 tail=Welcome to Claude Code v2.1.220

 Unable to connect to Anthropic
 services

 Failed to connect to
 api.anthropic.com:
 ERR_BAD_REQUEST

 Please check your internet
 connection and network
 settings.


- pane_id=w3:p3 exit_code=0 tail=  Sign in with ChatGPT to use Codex as part of
your paid plan
  or connect an API key for usage-based
billing

> 1. Sign in with ChatGPT
     Usage included with Plus, Pro, Business,
and Enterprise pl
- pane_id=w3:p2 exit_code=0 tail=运行程序的名称。请检查名称的拼写，如果包括路径，请确
保路径正确，然后再试一次。
所在位置 行:1 字符: 1
+ sh -lc "while :; do sleep 3600; done"
+ ~~
    + CategoryInfo          : ObjectNotFound: (sh:St
   ring) [], CommandNotFoundException
    + Fu
