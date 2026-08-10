<#
.SYNOPSIS
    CCB 启动闪窗诊断 — ETW 实时进程追踪

.DESCRIPTION
    使用 Windows 内核 ETW 提供者 (Microsoft-Windows-Kernel-Process) 捕获
    CCB 启动期间所有进程创建/退出事件，分析短命进程以识别闪窗源。

    用法（WezTerm 多 Tab）:
      Tab 1: .\diagnose_flash_windows.ps1 [-Mode installed|sourcedev]
      Tab 2: 执行 CCB 启动命令（如 ccb 或 .\ccb8.cmd）

    脚本在 Tab 1 中等待，自动检测 CCB 进程启动并分析。

.PARAMETER Mode
    监控模式:
      - sourcedev (默认): 监控 ccb8.cmd / ccb.py 启动
      - installed:       监控 ccb.cmd / ccb 启动

.PARAMETER TimeoutSeconds
    最长等待时间（秒）。默认 120 秒。

.PARAMETER QuietPeriodSeconds
    CCB 启动完成后的静默等待时间（秒）。在此期间无新进程创建即视为启动完成。默认 8 秒。

.PARAMETER FlashThresholdMs
    闪窗判定阈值（毫秒）。生命周期小于此值的进程视为闪窗候选。默认 500ms。

.PARAMETER OutputDir
    输出目录。默认自动生成 evidence/ 子目录。
#>

param(
    [ValidateSet('sourcedev', 'installed')]
    [string] $Mode = 'sourcedev',

    [int] $TimeoutSeconds = 120,

    [int] $QuietPeriodSeconds = 20,

    [int] $FlashThresholdMs = 500,

    [string] $OutputDir = ''
)

$ErrorActionPreference = 'Stop'
$script:utf8NoBom = New-Object System.Text.UTF8Encoding($false)
try { $OutputEncoding = $script:utf8NoBom } catch {}
try { [Console]::OutputEncoding = $script:utf8NoBom } catch {}

$script:runId = 'run-' + (Get-Date -Format 'yyyyMMdd-HHmmss')

if (-not $OutputDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $OutputDir = Join-Path (Join-Path $scriptDir 'evidence') $script:runId
}
if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$traceName = 'CCB_Flash_Diag'
$etlPath = Join-Path $OutputDir 'trace.etl'
$csvPath = Join-Path $OutputDir 'process_events.csv'
$reportPath = Join-Path $OutputDir 'flash_report.json'

# ── CCB process detection patterns ──────────────────────────────────────

$ccbTriggerPatterns = switch ($Mode) {
    'sourcedev' { @('ccb.py', 'ccb8.ps1', 'ccb8.cmd') }
    'installed' { @('ccb.py', 'ccb.cmd', 'ccb.bat') }
}

# ── Helper functions ────────────────────────────────────────────────────

function Write-Banner {
    param([string] $Text)
    $sep = '=' * 64
    Write-Host $sep
    Write-Host "  $Text"
    Write-Host $sep
    Write-Host ''
}

function Write-Step {
    param([string] $Text)
    Write-Host "  [$([DateTime]::Now.ToString('HH:mm:ss'))] $Text"
}

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ── Phase 1: Start ETW trace ────────────────────────────────────────────

Write-Banner "CCB Startup Flash Window Diagnostic"
Write-Host "  Mode:             $Mode"
Write-Host "  Run ID:           $script:runId"
Write-Host "  Output Dir:       $OutputDir"
Write-Host "  Timeout:          ${TimeoutSeconds}s"
Write-Host "  Quiet period:     ${QuietPeriodSeconds}s"
Write-Host "  Flash threshold:  ${FlashThresholdMs}ms"
Write-Host ''

if (-not (Test-Admin)) {
    Write-Host '[WARN] Not running as Administrator — kernel process trace may fail.' -ForegroundColor Yellow
    Write-Host '       Restart this script in an elevated terminal if trace fails to start.'
    Write-Host ''
}

# Clean up any stale trace session
$null = logman stop $traceName -ets *>$null 2>&1

Write-Step 'Starting ETW kernel process trace...'
try {
    logman create trace $traceName `
        -p "Microsoft-Windows-Kernel-Process" 0x10 `
        -o $etlPath `
        -ets `
        -bs 64 `
        -max 256
} catch {
    $errMsg = $_.Exception.Message
    Write-Host "[ERROR] Failed to start ETW trace: $errMsg" -ForegroundColor Red
    Write-Host ''
    Write-Host 'Troubleshooting:'
    Write-Host '  1. Run PowerShell as Administrator'
    Write-Host '  2. Ensure "Performance Log Users" group membership'
    Write-Host '  3. Check: logman query providers | findstr Kernel-Process'
    exit 1
}
Write-Step 'ETW trace active. Kernel process events are being captured.'

# ── Phase 2: Wait for CCB startup ────────────────────────────────────────

Write-Host ''
Write-Banner 'ACTION REQUIRED'
Write-Host '  ETW trace is now capturing ALL process creation/exit events.'
Write-Host ''
Write-Host '  In ANOTHER WezTerm tab (or terminal window), run:'
Write-Host ''
if ($Mode -eq 'sourcedev') {
    Write-Host '    .\ccb8.cmd' -ForegroundColor Cyan
} else {
    Write-Host '    ccb' -ForegroundColor Cyan
}
Write-Host ''
Write-Host '  This script will auto-detect CCB startup and stop tracing.'
Write-Host '  Or press ENTER here when CCB has fully started.'
Write-Host ''

$traceStartTime = Get-Date
$deadline = $traceStartTime.AddSeconds($TimeoutSeconds)

# -- Two-phase detection:
#    Phase 1: Wait for the CCB wrapper process (powershell.exe / python.exe)
#             to appear → "CCB startup begun".
#    Phase 2: Wait for the CCB core process (python.exe with ccb.py)
#             to appear → "CCB core running", then begin quiet-period countdown.
#    When spawn activity has been quiet for $QuietPeriodSeconds AND the core
#    has been seen, stop the trace.  This avoids triggering on the initial
#    wrapper and missing the actual startup.
#
# Detection is WMI-polling (250ms interval).  WMI CommandLine may be empty
# for very young processes; we retry on the next poll cycle naturally.

$ccbWrapperPatterns = @('ccb8.ps1', 'ccb8.cmd', 'ccb.cmd', 'ccb.bat')
$ccbCorePatterns    = @('ccb.py')

$ccbWrapperSeen = $false
$ccbCoreSeen    = $false
$ccbQuietSince  = $null

$knownPids = @{}
# WMI snapshot for PID→ImageName cross-reference (ETW events lack ImageName on Win10+)
$wmiImageNames = @{}
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | ForEach-Object {
    $knownPids[$_.ProcessId] = $true
    $wmiImageNames[$_.ProcessId] = [string] $_.Name
}

Write-Step 'Monitoring for CCB processes (2-phase: wrapper → core → quiet)...'

do {
    Start-Sleep -Milliseconds 250

    $currentPids = @{}
    $newWrapperProcs = @()
    $newCoreProcs = @()
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | ForEach-Object {
        $currentPids[$_.ProcessId] = $true
        $wmiImageNames[$_.ProcessId] = [string] $_.Name
        if (-not $knownPids.ContainsKey($_.ProcessId)) {
            $cmdLine = [string] $_.CommandLine
            if (-not $cmdLine) { return }  # WMI hasn't populated CommandLine yet
            if (-not $ccbWrapperSeen) {
                foreach ($pattern in $ccbWrapperPatterns) {
                    if ($cmdLine.IndexOf($pattern, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
                        $newWrapperProcs += $_
                        break
                    }
                }
            }
            if (-not $ccbCoreSeen) {
                foreach ($pattern in $ccbCorePatterns) {
                    if ($cmdLine.IndexOf($pattern, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
                        $newCoreProcs += $_
                        break
                    }
                }
            }
        }
    }

    # Phase 1 → Phase 2 transition
    if (-not $ccbWrapperSeen -and $newWrapperProcs.Count -gt 0) {
        $ccbWrapperSeen = $true
        $names = ($newWrapperProcs | ForEach-Object { "$($_.Name)($($_.ProcessId))" }) -join ', '
        Write-Step "Phase 1: CCB wrapper detected: $names"
    }
    if ($ccbWrapperSeen -and -not $ccbCoreSeen -and $newCoreProcs.Count -gt 0) {
        $ccbCoreSeen = $true
        $ccbQuietSince = Get-Date
        $names = ($newCoreProcs | ForEach-Object { "$($_.Name)($($_.ProcessId))" }) -join ', '
        Write-Step "Phase 2: CCB core detected: $names"
        Write-Step "Waiting for startup quiet period (${QuietPeriodSeconds}s)..."
    }

    # Quiet-period countdown (only after core seen)
    if ($ccbCoreSeen) {
        $anyNewCcb = ($newWrapperProcs.Count + $newCoreProcs.Count) -gt 0
        if ($anyNewCcb) {
            $ccbQuietSince = Get-Date
        } else {
            $quietElapsed = ((Get-Date) - $ccbQuietSince).TotalSeconds
            if ($quietElapsed -ge $QuietPeriodSeconds) {
                Write-Step 'Quiet period reached. Stopping trace...'
                break
            }
        }
    }

    $knownPids = $currentPids

    # Progress indicator
    $elapsed = ((Get-Date) - $traceStartTime).TotalSeconds
    if ([Math]::Floor($elapsed) % 15 -eq 0 -and $elapsed -gt 0) {
        $lastReported = Get-Variable -Name 'lastProgressReport' -ValueOnly -ErrorAction SilentlyContinue
        if (-not $lastReported -or ($elapsed - $lastReported) -ge 14.5) {
            $phaseLabel = if ($ccbCoreSeen) { 'quiet-countdown' }
                          elseif ($ccbWrapperSeen) { 'waiting-for-core' }
                          else { 'waiting-for-wrapper' }
            Write-Host "  ... $phaseLabel (${elapsed}s elapsed) ..."
            Set-Variable -Name 'lastProgressReport' -Value $elapsed -Scope Script
        }
    }

} while ((Get-Date) -lt $deadline)

if (-not $ccbWrapperSeen) {
    Write-Host '[WARN] CCB wrapper was not detected within timeout.' -ForegroundColor Yellow
    Write-Host '       Stopping trace and analyzing whatever was captured.'
}
elseif (-not $ccbCoreSeen) {
    Write-Host '[WARN] CCB core (python.exe ccb.py) was not detected — startup may have failed early.' -ForegroundColor Yellow
    Write-Host '       Stopping trace and analyzing whatever was captured.'
}

# ── Phase 3: Stop ETW trace ──────────────────────────────────────────────

Write-Step 'Stopping ETW trace...'
$stopResult = logman stop $traceName -ets 2>&1
if ($LASTEXITCODE -ne 0) {
    $stopMsg = ($stopResult -join ' ').Trim()
    if ($stopMsg -and $stopMsg -notmatch 'not found') {
        Write-Host "[WARN] logman stop: $stopMsg" -ForegroundColor Yellow
    }
}

# Wait for ETL file to be fully written
Start-Sleep -Seconds 2

if (-not (Test-Path -LiteralPath $etlPath)) {
    Write-Host '[ERROR] ETW trace file not found. No data captured.' -ForegroundColor Red
    exit 1
}

$etlSize = (Get-Item -LiteralPath $etlPath).Length
Write-Step "Trace captured: $etlSize bytes"

# ── Phase 4: Parse ETL → process events ──────────────────────────────────

Write-Step 'Parsing ETW trace with Get-WinEvent...'
# tracerpt loses structured data for kernel process events (User Data
# becomes a numeric pointer).  Instead, use Get-WinEvent to read the
# ETL file directly — it returns proper event objects with XML payload
# that contains ImageName, CommandLine, ParentProcessID, etc.

$processes = @{}
$processList = [System.Collections.ArrayList]::new()

try {
    $kernelEvents = Get-WinEvent -Path $etlPath -Oldest -ErrorAction Stop -FilterXPath "*[System[Provider[@Name='Microsoft-Windows-Kernel-Process']]]"
} catch {
    # Fallback: try without filter
    try {
        $kernelEvents = Get-WinEvent -Path $etlPath -Oldest -ErrorAction Stop
    } catch {
        Write-Host "[ERROR] Get-WinEvent failed to read ETL: $_" -ForegroundColor Red
        $kernelEvents = @()
    }
}

Write-Step "Raw kernel events read: $($kernelEvents.Count)"

# Event IDs for Microsoft-Windows-Kernel-Process:
#   1 — ProcessStart (Win7)    5 — ProcessStop  (Win7)
#   2 — ThreadStart            6 — ThreadStop
# In many traces, the detailed ProcessStart/Stop events use IDs 1/2.
# But the actual IDs vary by Windows version.  Inspect the data to adapt.

foreach ($evt in $kernelEvents) {
    $evtId = $evt.Id
    $time  = $evt.TimeCreated.ToString('o')

    # Kernel-Process event XML is in EventData/Data elements
    $xml = $evt.ToXml()
    $procPid = 0; $ppid = 0; $image = ''; $cmdLine = ''

    # Extract EventData/Data nodes from event XML.  Use local-name()
    # XPath to avoid namespace mismatches (.NET XPath 1.0 namespace
    # resolution via hashtable is unreliable across PS versions).
    try {
        $eventXml = [xml] $xml
        $dataNodes = $eventXml.SelectNodes('//*[local-name()="EventData"]/*[local-name()="Data"]')

        $dataMap = @{}
        foreach ($node in $dataNodes) {
            $name  = $node.Name
            $value = $node.InnerText
            if ($name) { $dataMap[$name] = $value }
        }

        # Common field names (vary by event ID)
        $procPid = try { [int] ($dataMap['ProcessID'] -as [string]) }
                   catch { try { [int] ($dataMap['ProcessId'] -as [string]) } catch { 0 } }
        $ppid    = try { [int] ($dataMap['ParentProcessID'] -as [string]) }
                   catch { try { [int] ($dataMap['ParentProcessId'] -as [string]) } catch { 0 } }
        $image   = $dataMap['ImageName'] -as [string]
        if (-not $image) { $image = $dataMap['ImagePath'] -as [string] }
        $cmdLine = $dataMap['CommandLine'] -as [string]

        # PID fallback: some events use alternate field names
        if ($procPid -le 0) {
            $procPid = try { [int] ($dataMap['CreatorID'] -as [string]) } catch { 0 }
        }
        if ($procPid -le 0) {
            $procPid = try { [int] ($dataMap['ThreadID'] -as [string]) } catch { 0 }
        }
        # PPID fallback via regex if XPath didn't capture it
        if ($ppid -le 0 -and $evtId -eq 1) {
            if ($xml -match 'ParentProcessID[^0-9]*(\d+)') {
                $ppid = [int] $Matches[1]
            }
        }
    } catch {
        # XML parsing failed — extract PID/PPID from raw XML as last resort
        if ($xml -match 'ProcessID[^0-9]*(\d+)') {
            $procPid = [int] $Matches[1]
        }
        if ($ppid -le 0 -and $xml -match 'ParentProcessID[^0-9]*(\d+)') {
            $ppid = [int] $Matches[1]
        }
    }

    if ($procPid -le 0) { continue }

    # Event classification: 1=Start, 2=Stop, 5=Start, others=Thread/Image/...
    $isStart = ($evtId -eq 1 -or $evtId -eq 5)
    $isStop  = ($evtId -eq 2 -or $evtId -eq 6)

    if (-not $isStart -and -not $isStop) {
        # Thread start/stop or image load/unload — skip for flash analysis
        continue
    }

    # Cross-reference with WMI snapshots (ETW on Win10+ does not include ImageName)
    if (-not $image -or $image -eq '') {
        $image = $wmiImageNames[$procPid]
    }
    if ((-not $image -or $image -eq '') -and $ppid -gt 0) {
        # Inherit parent's image label for context (e.g. "child-of-powershell.exe")
        $parentName = $wmiImageNames[$ppid]
        if ($parentName) { $image = "child-of-$parentName" }
    }

    if ($isStart) {
        if (-not $processes.ContainsKey($procPid)) {
            $proc = [ordered] @{
                pid          = $procPid
                ppid         = $ppid
                image        = if ($image) { $image } else { '(unknown)' }
                command_line = if ($cmdLine) { $cmdLine } else { '' }
                start_time   = $time
                exit_time    = $null
                lifetime_ms  = $null
                is_flash     = $false
                flash_reason = ''
            }
            $processes[$procPid] = $proc
            [void] $processList.Add($proc)
        }
    }
    elseif ($isStop) {
        if ($processes.ContainsKey($procPid)) {
            $processes[$procPid].exit_time = $time
            # Backfill image name from WMI if still unknown
            if ($processes[$procPid].image -eq '(unknown)' -and $wmiImageNames[$procPid]) {
                $processes[$procPid].image = $wmiImageNames[$procPid]
            }
        } else {
            # Exit event without matching start — still record for completeness
            if (-not $image -or $image -eq '') { $image = $wmiImageNames[$procPid] }
            $proc = [ordered] @{
                pid          = $procPid
                ppid         = $ppid
                image        = if ($image) { $image } else { '(unknown)' }
                command_line = if ($cmdLine) { $cmdLine } else { '' }
                start_time   = $null
                exit_time    = $time
                lifetime_ms  = $null
                is_flash     = $false
                flash_reason = ''
            }
            $processes[$procPid] = $proc
            [void] $processList.Add($proc)
        }
    }
}

Write-Step "Process events parsed: $($processList.Count) unique processes"

# ── Phase 5: Analyze → flash report ──────────────────────────────────────

Write-Step 'Analyzing process events...'

# Also export to CSV for manual inspection
$processList | ForEach-Object {
    [PSCustomObject] @{
        PID          = $_.pid
        PPID         = $_.ppid
        Image        = $_.image
        CommandLine  = $_.command_line
        StartTime    = $_.start_time
        ExitTime     = $_.exit_time
        LifetimeMs   = $_.lifetime_ms
        IsFlash      = $_.is_flash
    }
} | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8

if ($processList.Count -eq 0) {
    Write-Host '[WARN] No process events found in trace.' -ForegroundColor Yellow

    $report = [ordered] @{
        run_id              = $script:runId
        mode                = $Mode
        trace_start         = $traceStartTime.ToString('o')
        trace_end           = (Get-Date).ToString('o')
        total_events        = $kernelEvents.Count
        flash_windows       = @()
        process_tree        = @()
        summary             = @{
            flash_count      = 0
            total_processes  = 0
            flash_sources    = @()
        }
    }
    $report | ConvertTo-Json -Depth 8 | Out-File -LiteralPath $reportPath -Encoding UTF8
    Write-Host "Empty report written to: $reportPath"
    exit 0
}

# Compute lifetimes and classify flash windows.
#
# Classification tiers:
#   VISIBLE   — console subsystem process that creates a real window:
#               conhost.exe (IS the console window),
#               cmd.exe / powershell.exe / bash.exe / wsl.exe / etc.
#   INVISIBLE — GUI/TUI subsystem or MSYS utility (no console window):
#               herdr.exe / wezterm.exe / claude.exe / sleep.exe / git.exe / …
#   conhost is the definitive visible-flash indicator: every conhost spawn
#   means a console window appeared (and then disappeared).

$flashWindows = [System.Collections.ArrayList]::new()

# Console-subsystem images → visible flash (when short-lived)
$visibleFlashImages = @(
    'conhost.exe',           # IS the console window
    'cmd.exe',               # batch files / shell
    'powershell.exe',        # PowerShell host
    'pwsh.exe',              # PowerShell Core
    'bash.exe',              # Git-Bash / MSYS shell
    'sh.exe',                # POSIX shell
    'wsl.exe',               # WSL launcher
    'python.exe',            # CPython (console subsystem)
    'python3.exe',           # Python 3.x
    'reg.exe',               # Registry tool
    'whoami.exe'             # System utility
)

# GUI / TUI / MSYS images → invisible (no console window created)
$invisibleImages = @(
    'herdr.exe',             # TUI multiplexer
    'wezterm.exe',           # GUI terminal
    'claude.exe',            # GUI app
    'sleep.exe',             # MSYS util (runs in inherited PTY)
    'git.exe',               # MSYS util
    'sed.exe',               # MSYS util
    'rm.exe',                # MSYS util
    'uname.exe',             # MSYS util
    'dirname.exe',           # MSYS util
    'tmux.exe'               # psmux utility
)

foreach ($proc in $processList) {
    if ($proc.start_time -and $proc.exit_time) {
        try {
            $start = [DateTime]::Parse($proc.start_time)
            $end = [DateTime]::Parse($proc.exit_time)
            $proc.lifetime_ms = [Math]::Round(($end - $start).TotalMilliseconds, 1)
        } catch {
            $proc.lifetime_ms = $null
        }
    }

    $imageName = (Split-Path -Leaf $proc.image).ToLowerInvariant()

    if ($proc.lifetime_ms -ne $null -and $proc.lifetime_ms -le $FlashThresholdMs) {
        $proc.is_flash = $true

        # Determine visibility tier
        if ($visibleFlashImages -contains $imageName) {
            $proc.visible_flash = $true
            $proc.flash_reason = "VISIBLE — console-subsystem ($imageName, lifetime=$($proc.lifetime_ms)ms)"
        }
        elseif ($invisibleImages -contains $imageName) {
            $proc.visible_flash = $false
            $proc.flash_reason = "invisible — GUI/TUI/MSYS ($imageName, lifetime=$($proc.lifetime_ms)ms)"
        }
        else {
            # Unknown image: assume console if path is under \Windows\System32\
            $isSystemConsole = $proc.image -match '\\Windows\\System32\\'
            $proc.visible_flash = $isSystemConsole
            $tier = if ($isSystemConsole) { 'VISIBLE — console-subsystem' } else { 'invisible — unknown' }
            $proc.flash_reason = "$tier ($imageName, lifetime=$($proc.lifetime_ms)ms)"
        }

        [void] $flashWindows.Add($proc)
    } else {
        $proc.is_flash = $false
        $proc.visible_flash = $false
        $proc.flash_reason = ''
    }
}

# Split into visible vs invisible for reporting
$visibleFlashes  = @($flashWindows | Where-Object { $_.visible_flash })
$invisibleShorts = @($flashWindows | Where-Object { -not $_.visible_flash })

# Build process tree for flash processes
$flashTree = @()
foreach ($fw in $flashWindows) {
    $ancestry = @()
    $currentPid = $fw.ppid
    $depth = 0
    while ($depth -lt 10 -and $currentPid -gt 0 -and $processes.ContainsKey($currentPid)) {
        $ancestor = $processes[$currentPid]
        $ancestry += "$($ancestor.image)($($ancestor.pid))"
        $currentPid = $ancestor.ppid
        $depth++
    }
    [Array]::Reverse($ancestry)

    $flashTree += [ordered] @{
        pid           = $fw.pid
        image         = $fw.image
        lifetime_ms   = $fw.lifetime_ms
        visible_flash = $fw.visible_flash
        flash_reason  = $fw.flash_reason
        parent_chain  = $ancestry -join ' → '
    }
}

# ── Phase 6: Generate report ─────────────────────────────────────────────

Write-Step 'Generating flash window report...'

# Summarize sources separately for visible vs invisible
function Build-SourceSummary {
    param([object[]] $Items, [string] $Tier)
    $summary = @{}
    foreach ($fw in $Items) {
        $imageKey = (Split-Path -Leaf $fw.image).ToLowerInvariant()
        if (-not $summary.ContainsKey($imageKey)) {
            $summary[$imageKey] = @{
                image  = $imageKey
                tier   = $Tier
                count  = 0
                min_lifetime_ms = [int]::MaxValue
                max_lifetime_ms = 0
                total_lifetime_ms = 0
            }
        }
        $s = $summary[$imageKey]
        $s.count++
        $lifetime = $fw.lifetime_ms
        if ($lifetime -lt $s.min_lifetime_ms) { $s.min_lifetime_ms = $lifetime }
        if ($lifetime -gt $s.max_lifetime_ms) { $s.max_lifetime_ms = $lifetime }
        $s.total_lifetime_ms += $lifetime
    }
    $results = @()
    foreach ($item in $summary.Values) {
        $item.avg_lifetime_ms = [Math]::Round($item.total_lifetime_ms / $item.count, 1)
        $item.Remove('total_lifetime_ms')
        $results += $item
    }
    return @($results | Sort-Object count -Descending)
}

$visibleSources   = Build-SourceSummary -Items $visibleFlashes  -Tier 'visible'
$invisibleSources = Build-SourceSummary -Items $invisibleShorts -Tier 'invisible'

# conhost trigger analysis: which parent processes spawn the conhost flashes?
$conhostTriggers = @{}
foreach ($fw in $visibleFlashes) {
    $imageName = (Split-Path -Leaf $fw.image).ToLowerInvariant()
    if ($imageName -ne 'conhost.exe') { continue }
    # The immediate parent is the trigger
    if ($fw.ppid -gt 0 -and $processes.ContainsKey($fw.ppid)) {
        $parentImg = (Split-Path -Leaf $processes[$fw.ppid].image).ToLowerInvariant()
        if (-not $conhostTriggers.ContainsKey($parentImg)) {
            $conhostTriggers[$parentImg] = 0
        }
        $conhostTriggers[$parentImg]++
    }
}

$report = [ordered] @{
    run_id              = $script:runId
    mode                = $Mode
    trace_start         = $traceStartTime.ToString('o')
    trace_end           = (Get-Date).ToString('o')
    total_events        = $kernelEvents.Count
    total_processes     = $processList.Count
    flash_threshold_ms  = $FlashThresholdMs
    flash_windows       = @($flashTree)
    all_processes       = @($processList | Select-Object pid, ppid, image, start_time, exit_time, lifetime_ms, is_flash, visible_flash)
    summary             = [ordered] @{
        visible_flash_count    = $visibleFlashes.Count
        invisible_short_count  = $invisibleShorts.Count
        total_short_lived      = $flashWindows.Count
        total_processes        = $processList.Count
        visible_sources        = @($visibleSources)
        invisible_sources      = @($invisibleSources)
        conhost_triggers       = $conhostTriggers
    }
}

$report | ConvertTo-Json -Depth 10 | Out-File -LiteralPath $reportPath -Encoding UTF8

# ── Phase 7: Print summary ───────────────────────────────────────────────

Write-Host ''
Write-Banner 'FLASH WINDOW DIAGNOSTIC RESULTS'

$durSec = '{0:F1}s' -f ((Get-Date) - $traceStartTime).TotalSeconds
Write-Host "  Trace duration:       $durSec"
Write-Host "  Total processes:      $($processList.Count)"
Write-Host ''

# ── VISIBLE flash windows (actually create a console) ──────────────────
$visColor = if ($visibleFlashes.Count -gt 0) { 'Red' } else { 'Green' }
Write-Host "  VISIBLE flash windows: $($visibleFlashes.Count)" -ForegroundColor $visColor
Write-Host '    (console subsystem processes that created a real window)'
Write-Host ''

if ($visibleSources.Count -gt 0) {
    Write-Host '  --- Visible Sources ---' -ForegroundColor Red
    $fmtHeader = '  {0,-24} {1,6} {2,10} {3,10} {4,10}' -f 'IMAGE', 'COUNT', 'MIN(ms)', 'AVG(ms)', 'MAX(ms)'
    Write-Host $fmtHeader
    Write-Host ('  {0,-24} {1,6} {2,10} {3,10} {4,10}' -f ('-' * 24), ('-' * 6), ('-' * 10), ('-' * 10), ('-' * 10))
    foreach ($src in $visibleSources) {
        $row = '  {0,-24} {1,6} {2,10} {3,10} {4,10}' -f $src.image, $src.count, $src.min_lifetime_ms, $src.avg_lifetime_ms, $src.max_lifetime_ms
        Write-Host $row
    }
    Write-Host ''

    # conhost trigger breakdown
    if ($conhostTriggers.Count -gt 0) {
        Write-Host '  --- conhost.exe Trigger Sources ---' -ForegroundColor Red
        Write-Host '    (processes whose spawn caused a console window to appear)'
        foreach ($trigger in ($conhostTriggers.GetEnumerator() | Sort-Object Value -Descending)) {
            Write-Host "    $($trigger.Key)  →  $($trigger.Value) conhost instance(s)"
        }
        Write-Host ''
    }
} else {
    Write-Host '  [OK] No visible flash windows.' -ForegroundColor Green
    Write-Host ''
}

# ── INVISIBLE short-lived processes (no console window) ─────────────────
$invColor = if ($invisibleShorts.Count -gt 0) { 'DarkGray' } else { 'Green' }
Write-Host "  Invisible short-lived: $($invisibleShorts.Count)" -ForegroundColor $invColor
Write-Host '    (GUI/TUI/MSYS processes — no console window created)'
Write-Host ''

if ($invisibleSources.Count -gt 0) {
    Write-Host '  --- Invisible Sources ---' -ForegroundColor DarkGray
    $fmtHeader = '  {0,-24} {1,6} {2,10} {3,10} {4,10}' -f 'IMAGE', 'COUNT', 'MIN(ms)', 'AVG(ms)', 'MAX(ms)'
    Write-Host $fmtHeader
    Write-Host ('  {0,-24} {1,6} {2,10} {3,10} {4,10}' -f ('-' * 24), ('-' * 6), ('-' * 10), ('-' * 10), ('-' * 10))
    foreach ($src in $invisibleSources) {
        $row = '  {0,-24} {1,6} {2,10} {3,10} {4,10}' -f $src.image, $src.count, $src.min_lifetime_ms, $src.avg_lifetime_ms, $src.max_lifetime_ms
        Write-Host $row
    }
    Write-Host ''
}

# ── Sample visible flash detail (first 5) ──────────────────────────────
if ($visibleFlashes.Count -gt 0) {
    Write-Host '  --- Sample Visible Flashes (first 10) ---' -ForegroundColor Red
    $visibleFlashes | Select-Object -First 10 | ForEach-Object {
        $fw = $_
        # Reconstruct parent chain for this specific flash
        $ancestry = @()
        $cur = $fw.ppid
        $d = 0
        while ($d -lt 6 -and $cur -gt 0 -and $processes.ContainsKey($cur)) {
            $ancestry += "$($processes[$cur].image)($($cur))"
            $cur = $processes[$cur].ppid
            $d++
        }
        [Array]::Reverse($ancestry)
        Write-Host "    $($fw.image)($($fw.pid))  lifetime=$($fw.lifetime_ms)ms"
        Write-Host "      → $($ancestry -join ' → ')"
    }
    Write-Host ''
}

Write-Host '--- Files ---'
Write-Host "  Report:  $reportPath"
Write-Host "  Raw ETL: $etlPath"
Write-Host "  CSV:     $csvPath"
Write-Host ''

# Clean up trace session
$null = logman stop $traceName -ets *>$null 2>&1

# ── Final verdict ───────────────────────────────────────────────────────
if ($visibleFlashes.Count -eq 0) {
    Write-Host '  Verdict: PASS — no visible flash windows' -ForegroundColor Green
} else {
    Write-Host "  Verdict: WARN — $($visibleFlashes.Count) visible flash(es)" -ForegroundColor Red
    Write-Host "           + $($invisibleShorts.Count) invisible short-lived process(es)" -ForegroundColor DarkGray
}
Write-Host ''
Write-Host 'Done.' -ForegroundColor Green
exit 0
