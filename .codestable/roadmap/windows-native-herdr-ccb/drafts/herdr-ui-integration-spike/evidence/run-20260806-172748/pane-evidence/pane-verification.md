# Pane materialization verification
- snapshot_source: herdr-api-snapshot-ccb-namespace
- capture_session: ccb-avaprintdesigner-575a971f
- capture_lines: 20

- snapshot_available: true
- pane_count: 4
- workspace_count: 2

## Pane identity

- pane_id=w1:p1 title= display_agent=
- pane_id=w2:p1 title=sidebar display_agent=sidebar
  token: ccb_agent_label=sidebar
  token: ccb_is_cmd=0
  token: ccb_managed_by=ccbd
  token: ccb_namespace_epoch=1
  token: ccb_namespace_id=w2
  token: ccb_project_id=575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03
  token: ccb_role=sidebar
  token: ccb_root_pane=1
  token: ccb_sidebar_instance=main
  token: ccb_slot=sidebar:main
  token: ccb_window=main
- pane_id=w2:p3 title=agent_2 display_agent=agent_2
  token: ccb_is_cmd=0
  token: ccb_managed_by=ccbd
  token: ccb_order=1
  token: ccb_project_id=575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03
  token: ccb_session_id=ccb-agent_2-2ebe74b38cc1
  token: ccb_slot=agent_2
- pane_id=w2:p2 title=agent_1 display_agent=agent_1
  token: ccb_is_cmd=0
  token: ccb_managed_by=ccbd
  token: ccb_order=0
  token: ccb_project_id=575a971fdf5a0c497a48228040a14841fb4529aaa476beb21d34e53f1629bc03
  token: ccb_session_id=ccb-agent_1-4b3d57db10d6
  token: ccb_slot=agent_1

## Workspaces
- workspace_id=w1 label=ccb-debug-probe
- workspace_id=w2 label=ccb-avaprintdesigner-575a971f

## Pane content capture

- pane_id=w1:p1 exit_code=0 tail=PS D:\C#Project\GitHub\AvaPrintDesigner>

- pane_id=w2:p1 exit_code=0 tail=d-socket 'D:\.c8\rs\575a971fdf5a0c497a48228040a14841f
b4529aaa476beb21d34e53f1629bc03\ccbd\ccbd.sock' --pro
ject-root 'D:\C#Project\GitHub\AvaPrintDesigner' --pa
ne-window main"
sh : 鏃犳硶灏嗏€渟h鈥濋」璇嗗埆涓?c
- pane_id=w2:p3 exit_code=0 tail=鏂囦欢鎴栧彲杩愯绋嬪簭鐨勫悕绉般€傝妫€鏌ュ悕绉扮殑鎷煎啓锛屽
鏋滃寘鎷矾寰勶紝璇风‘淇濊矾寰勬纭紝鐒跺悗鍐嶈瘯涓€娆°€?鎵€鍦ㄤ綅缃?琛?1 瀛楃: 1
+ sh -lc "while :; do sleep 3600; done"
+ ~~
    + CategoryInfo          : ObjectNotFound
   : (sh:String) [], Com
- pane_id=w2:p2 exit_code=0 tail=杩愯绋嬪簭鐨勫悕绉般€傝妫€鏌ュ悕绉扮殑鎷煎啓锛屽鏋滃寘鎷矾寰勶紝璇风‘
淇濊矾寰勬纭紝鐒跺悗鍐嶈瘯涓€娆°€?鎵€鍦ㄤ綅缃?琛?1 瀛楃: 1
+ sh -lc "while :; do sleep 3600; done"
+ ~~
    + CategoryInfo          : ObjectNotFound: (sh:St
   ring) [], CommandNo
