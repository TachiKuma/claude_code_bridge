---
doc_type: feature-evidence
feature: 2026-07-31-herdr-bounded-recovery-boundary
status: blocked
evidence_kind: native-windows-x64-herdr-recovery
captured: 2026-08-03
---

# Native Windows x64 Herdr recovery blocked evidence

## 结论

本机是 Native Windows 环境，Herdr binary 存在，但目标 Herdr session 的 server 未运行，`capabilities` 为 `null`。因此本轮不能证明 `herdr_auto_restore_mode=disabled`，也不能采集 pane/process/namespace recovery transcript。

按本 feature design 的 S7 / CMD-009 规则，本证据只能作为 `auto-restore-not-proven blocked evidence`，不能声明 Herdr recovery supported、Windows release-ready 或真实 recovery pass。

## 探测命令与结果

### OS

Command:

```powershell
$PSVersionTable.OS
```

Result:

```text
Microsoft Windows 10.0.19045
```

### Herdr binary

Command:

```powershell
Test-Path "C:/Users/Administrator/AppData/Local/Programs/Herdr/herdr.exe"
```

Result:

```text
True
```

### Herdr status

Command:

```powershell
& "C:/Users/Administrator/AppData/Local/Programs/Herdr/herdr.exe" --session "ccb-direct-shell-probe-20260802" status --json
```

Result:

```json
{
  "client": {
    "version": "0.7.5-preview.2026-07-29-44b3adb12552",
    "channel": "preview",
    "protocol": 18,
    "binary": "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Herdr\\herdr.exe",
    "session": "ccb-direct-shell-probe-20260802"
  },
  "server": {
    "status": "not_running",
    "running": false,
    "version": null,
    "protocol": null,
    "capabilities": null,
    "compatible": null,
    "socket": "C:\\Users\\Administrator\\AppData\\Roaming\\herdr\\sessions\\ccb-direct-shell-probe-20260802\\herdr.sock",
    "session": "ccb-direct-shell-probe-20260802",
    "restart_needed": false
  },
  "update": {
    "restart_needed": false
  }
}
```

## Acceptance 使用边界

- 允许作为 S7 blocked evidence：当前 host 无可用 Herdr server/capability，不能证明 auto-restore disabled。
- 不允许作为 recovery pass：未执行 pane/process/namespace recovery；未观察 90 秒 probation；未观察 circuit transition。
- 不允许作为 release evidence：没有 public Windows workflow pass。
