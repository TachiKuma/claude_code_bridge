param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot,

    [ValidateSet("rmux")]
    [string]$Backend = "rmux",

    [string]$AskTarget = "demo",

    [string]$AskMessage = "CCB Windows full-chain smoke: reply with SMOKE_OK only.",

    [ValidateSet("fake_provider", "local_provider", "real_provider")]
    [string]$AskCaseKind = "local_provider",

    [switch]$Json
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ArtifactRoot = Join-Path $RepoRoot "artifacts/ccbd-windows-full-chain-smoke"
$TranscriptPath = Join-Path $ArtifactRoot "transcript.json"
$ParserPath = Join-Path $RepoRoot "scripts/ccbd_windows_full_chain_smoke.py"
$CommandRecords = New-Object System.Collections.Generic.List[object]
$Artifacts = [ordered]@{}

function New-Directory([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Initialize-RmuxRouteApprovalFixture([string]$TargetProjectRoot) {
    if ($Backend -ne "rmux") {
        return
    }
    $relativeDir = ".codestable/features/2026-07-19-rmux-route-approval"
    $sourceDir = Join-Path $RepoRoot $relativeDir
    $targetDir = Join-Path $TargetProjectRoot $relativeDir
    foreach ($fileName in @("approval-report.md", "rmux-route-decision-summary.yaml")) {
        $sourcePath = Join-Path $sourceDir $fileName
        $targetPath = Join-Path $targetDir $fileName
        if (-not (Test-Path -LiteralPath $sourcePath)) {
            throw "missing rmux route approval source asset: $sourcePath"
        }
        New-Directory (Split-Path -Parent $targetPath)
        Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    }
    $summaryPath = Join-Path $sourceDir "rmux-route-decision-summary.yaml"
    $summaryText = Get-Content -Raw -LiteralPath $summaryPath
    $capabilityMatch = [regex]::Match($summaryText, "(?m)^capability_report:\s*(.+?)\s*$")
    if (-not $capabilityMatch.Success) {
        throw "missing rmux capability report ref in route approval summary: $summaryPath"
    }
    $capabilityRef = $capabilityMatch.Groups[1].Value.Trim().Trim("'`"")
    $sourceCapabilityPath = Join-Path $RepoRoot $capabilityRef
    $targetCapabilityPath = Join-Path $TargetProjectRoot $capabilityRef
    if (-not (Test-Path -LiteralPath $sourceCapabilityPath)) {
        throw "missing rmux capability report source asset: $sourceCapabilityPath"
    }
    New-Directory (Split-Path -Parent $targetCapabilityPath)
    Copy-Item -LiteralPath $sourceCapabilityPath -Destination $targetCapabilityPath -Force
}

function Initialize-SmokeProjectConfig([string]$TargetProjectRoot) {
    $configPath = Join-Path $TargetProjectRoot ".ccb/ccb.config"
    New-Directory (Split-Path -Parent $configPath)
    $provider = if ($AskCaseKind -eq "fake_provider") { "fake" } else { "codex" }
    $config = @"
version = 2
default_agents = ["demo"]
layout = "demo:$provider"

[runtime.mux]
backend = "$Backend"

[agents.demo]
provider = "$provider"
target = "."
workspace_mode = "inplace"
restore = "auto"
permission = "manual"
"@
    [System.IO.File]::WriteAllText($configPath, $config, [System.Text.UTF8Encoding]::new($false))
}

function Redact-Text([string]$Text) {
    $value = [string]$Text
    $userHomePath = [string]$env:USERPROFILE
    if ($userHomePath) {
        foreach ($homeVariant in @(
            $userHomePath,
            $userHomePath.Replace("\", "/"),
            $userHomePath.Replace("\", "\\"),
            $userHomePath.Replace("\", "/").Replace("/", "\/")
        )) {
            if ($homeVariant) {
                $value = [regex]::Replace($value, [regex]::Escape($homeVariant), "[USER_HOME]", "IgnoreCase")
            }
        }
    }
    $value = [regex]::Replace($value, "(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{6,}|(?<![A-Za-z0-9_])sess-[A-Za-z0-9_-]{6,}|Bearer\s+[A-Za-z0-9._-]+", "[REDACTED]")
    $value = [regex]::Replace(
        $value,
        "(?i)([`"']?\b(api[_-]?key|(?:[A-Za-z0-9]+[_-])*token|secret|password)[`"']?\s*[:=]\s*)([`"']?)([^`"'\s,}]+)([`"']?)",
        '${1}${3}[REDACTED]${5}'
    )
    return $value
}

function ConvertTo-RedactedObject($Value) {
    if ($null -eq $Value) {
        return $null
    }
    if ($Value -is [string]) {
        return Redact-Text $Value
    }
    if ($Value -is [System.Collections.IDictionary]) {
        $result = [ordered]@{}
        foreach ($entry in $Value.GetEnumerator()) {
            $result[$entry.Key] = ConvertTo-RedactedObject $entry.Value
        }
        return $result
    }
    if (($Value -is [System.Collections.IEnumerable]) -and -not ($Value -is [string])) {
        $items = @()
        foreach ($item in $Value) {
            $items += ConvertTo-RedactedObject $item
        }
        return ,$items
    }
    if ($Value -is [pscustomobject]) {
        $result = [ordered]@{}
        foreach ($property in $Value.PSObject.Properties) {
            $result[$property.Name] = ConvertTo-RedactedObject $property.Value
        }
        return $result
    }
    return $Value
}

function Write-ArtifactText([string]$RelativePath, [string]$Text) {
    $path = Join-Path $ArtifactRoot $RelativePath
    New-Directory (Split-Path -Parent $path)
    [System.IO.File]::WriteAllText($path, (Redact-Text $Text), [System.Text.UTF8Encoding]::new($false))
    return $RelativePath.Replace("\", "/")
}

function Quote-ProcessArgument([string]$Value) {
    if ($null -eq $Value) {
        return '""'
    }
    if ($Value -notmatch '[\s"]') {
        return $Value
    }
    return '"' + $Value.Replace('\', '\\').Replace('"', '\"') + '"'
}

function Invoke-SmokeCommand(
    [string]$Name,
    [string]$Stage,
    [string[]]$Argv,
    [string]$Cwd,
    [hashtable]$EnvAllowlist,
    [int]$TimeoutSeconds = 120
) {
    New-Directory $Cwd
    $stdoutRel = "commands/$Name.stdout.txt"
    $stderrRel = "commands/$Name.stderr.txt"
    $startedAt = [DateTimeOffset]::UtcNow
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $stdout = ""
    $stderr = ""
    $returnCode = 127
    $process = $null

    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $Argv[0]
        $psi.Arguments = (($Argv | Select-Object -Skip 1 | ForEach-Object { Quote-ProcessArgument ([string]$_) }) -join " ")
        $psi.WorkingDirectory = $Cwd
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
        $psi.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)
        foreach ($entry in $EnvAllowlist.GetEnumerator()) {
            if ($null -ne $entry.Value) {
                $psi.Environment[$entry.Key] = [string]$entry.Value
            }
        }
        $process = [System.Diagnostics.Process]::Start($psi)
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            try {
                $process.Kill()
            } catch {
            }
            $returnCode = 124
            $stderr = "timeout after ${TimeoutSeconds}s"
        } else {
            $process.WaitForExit()
            $returnCode = $process.ExitCode
            $stderr = $stderrTask.Result
        }
        $stdout = $stdoutTask.Result
    } catch {
        $stderr = $_.Exception.Message
        $returnCode = 127
    } finally {
        $timer.Stop()
    }

    Write-ArtifactText $stdoutRel $stdout | Out-Null
    Write-ArtifactText $stderrRel $stderr | Out-Null
    $record = [ordered]@{
        name = $Name
        stage = $Stage
        argv = $Argv
        cwd = $Cwd
        env_allowlist = $EnvAllowlist
        started_at = $startedAt.ToString("o")
        duration_ms = [Math]::Round($timer.Elapsed.TotalMilliseconds, 3)
        returncode = $returnCode
        stdout_path = $stdoutRel.Replace("\", "/")
        stderr_path = $stderrRel.Replace("\", "/")
    }
    $CommandRecords.Add([pscustomobject]$record) | Out-Null
    return $record
}

function Test-NativeWindows {
    $isWindowsRuntime = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform(
        [System.Runtime.InteropServices.OSPlatform]::Windows
    )
    return $isWindowsRuntime -and -not $env:WSL_DISTRO_NAME -and -not $env:MSYSTEM
}

function Get-DependencyStatus {
    $items = [ordered]@{
        "ccbd-windows-tcp-loopback-transport" = ".codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-acceptance.md"
        "ccbd-rmux-namespace-lifecycle" = ".codestable/features/2026-07-20-ccbd-rmux-namespace-lifecycle/ccbd-rmux-namespace-lifecycle-acceptance.md"
        "accelerator-transport-windows-guard" = ".codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-acceptance.md"
        "ccbd-windows-process-liveness" = ".codestable/features/2026-07-20-ccbd-windows-process-liveness/ccbd-windows-process-liveness-acceptance.md"
    }
    $status = [ordered]@{}
    foreach ($entry in $items.GetEnumerator()) {
        $path = Join-Path $RepoRoot $entry.Value
        if (-not (Test-Path -LiteralPath $path)) {
            $status[$entry.Key] = "pending"
            continue
        }
        $text = Get-Content -Raw -LiteralPath $path
        if ($text -match "status:\s*(passed|accepted)") {
            $status[$entry.Key] = "ready"
        } else {
            $status[$entry.Key] = "pending"
        }
    }
    return $status
}

function Test-CleanupOk {
    $kill = $CommandRecords | Where-Object { $_.name -eq "ccb-kill-force" } | Select-Object -First 1
    if ($null -eq $kill -or $kill.returncode -ne 0) {
        return $false
    }
    return $true
}

function New-CcbArgv([string[]]$CliArgs) {
    return @($PythonExe, $CcbScript) + $CliArgs
}

function Read-ArtifactText([string]$RelativePath) {
    $path = Join-Path $ArtifactRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        return ""
    }
    return Get-Content -Raw -LiteralPath $path
}

function Find-FirstMatch([string]$Text, [string[]]$Patterns) {
    foreach ($pattern in $Patterns) {
        $match = [regex]::Match($Text, $pattern, "IgnoreCase")
        if ($match.Success -and $match.Groups.Count -gt 1) {
            return $match.Groups[1].Value
        }
    }
    return $null
}

function Find-LineValue([string]$Text, [string]$Key) {
    $pattern = "(?m)^\s*" + [regex]::Escape($Key) + "\s*:\s*(.+?)\s*$"
    $match = [regex]::Match([string]$Text, $pattern)
    if ($match.Success) {
        return $match.Groups[1].Value.Trim()
    }
    return $null
}

function Find-BindingRuntimeRef([string]$Text) {
    return Find-FirstMatch $Text @("(?m)^binding:\s+.*?\bruntime=([A-Za-z0-9_.-]+:[^\s]+)")
}

function BackendFromRuntimeRef([string]$RuntimeRef) {
    if (-not $RuntimeRef) {
        return $null
    }
    $index = $RuntimeRef.IndexOf(":")
    if ($index -le 0) {
        return $null
    }
    return $RuntimeRef.Substring(0, $index)
}

function Get-OwnedProcessResidue {
    $residue = New-Object System.Collections.Generic.List[object]
    try {
        $escapedRoot = [regex]::Escape($ProjectRoot)
        $currentPid = $PID
        $processes = Get-CimInstance Win32_Process | Where-Object {
            $_.ProcessId -ne $currentPid -and $_.CommandLine -and ($_.CommandLine -match $escapedRoot)
        }
        foreach ($process in $processes) {
            $residue.Add([pscustomobject]@{
                pid = [int]$process.ProcessId
                name = [string]$process.Name
            }) | Out-Null
        }
    } catch {
        $residue.Add([pscustomobject]@{
            pid = 0
            name = "process-scan-failed"
        }) | Out-Null
    }
    return @($residue.ToArray())
}

function Get-CleanupResidueEvidence([string]$RmuxListText) {
    $ccbRoot = Join-Path $ProjectRoot ".ccb"
    $ccbdRoot = Join-Path $ccbRoot "ccbd"
    $tokenFiles = @()
    if (Test-Path -LiteralPath $ccbRoot) {
        $tokenFiles = @(Get-ChildItem -LiteralPath $ccbRoot -Recurse -File -Filter "*token*.json" -ErrorAction SilentlyContinue)
    }
    $endpointFiles = @()
    if (Test-Path -LiteralPath $ccbdRoot) {
        $endpointFiles = @(Get-ChildItem -LiteralPath $ccbdRoot -File -Filter "ccbd.sock" -ErrorAction SilentlyContinue)
    }
    $projectMarker = [regex]::Escape((Split-Path -Leaf $ProjectRoot))
    $rmuxHasProjectMarker = [regex]::IsMatch([string]$RmuxListText, $projectMarker, "IgnoreCase")
    return [ordered]@{
        endpoint_removed = ($endpointFiles.Count -eq 0 -and $tokenFiles.Count -eq 0)
        token_removed = ($tokenFiles.Count -eq 0)
        rmux_namespace_removed = -not $rmuxHasProjectMarker
        session_removed = -not $rmuxHasProjectMarker
        owned_process_residue = @(Get-OwnedProcessResidue)
    }
}

New-Directory $ArtifactRoot
New-Directory $ProjectRoot
Initialize-RmuxRouteApprovalFixture $ProjectRoot
Initialize-SmokeProjectConfig $ProjectRoot

$PythonExe = (Get-Command python -ErrorAction Stop).Source
$CcbScript = Join-Path $RepoRoot "ccb.py"
$RmuxExe = (Get-Command rmux -ErrorAction Stop).Source

$envAllowlist = @{
    CCB_MUX_BACKEND = $Backend
    CCB_RMUX_BIN = $RmuxExe
    CCB_SOURCE_RUNTIME_OK = "1"
    CCB_TEST_ENTRYPOINT = $env:CCB_TEST_ENTRYPOINT
    PYTHONUTF8 = "1"
}
$hostKind = if (Test-NativeWindows) { "native_windows" } else { "unsupported_host" }
$dependencyStatus = Get-DependencyStatus
$cleanup = [ordered]@{ status = "not_run"; ok = $false }
$askCase = [ordered]@{
    provider = $AskTarget
    test_entrypoint = if ($env:CCB_TEST_ENTRYPOINT -eq "1") { "CCB_TEST_ENTRYPOINT=1" } else { $null }
}

try {
    Invoke-SmokeCommand "preflight-python" "preflight" @($PythonExe, "--version") $RepoRoot $envAllowlist | Out-Null
    Invoke-SmokeCommand "preflight-ccb" "preflight" (New-CcbArgv -CliArgs @("--help")) $RepoRoot $envAllowlist | Out-Null
    Invoke-SmokeCommand "preflight-rmux-version" "preflight" @($RmuxExe, "-V") $RepoRoot $envAllowlist | Out-Null

    Invoke-SmokeCommand "ccb-start" "start" (New-CcbArgv -CliArgs @("--project", $ProjectRoot)) $ProjectRoot $envAllowlist | Out-Null
    Invoke-SmokeCommand "ccb-ping-ccbd" "ping" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "ping", "ccbd")) $ProjectRoot $envAllowlist | Out-Null
    Invoke-SmokeCommand "ccb-doctor" "doctor" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "doctor")) $ProjectRoot $envAllowlist | Out-Null
    Invoke-SmokeCommand "ccb-ask" "ask" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "ask", "--artifact-reply", $AskTarget, "--", $AskMessage)) $ProjectRoot $envAllowlist | Out-Null
    Invoke-SmokeCommand "ccb-ps-after-ask" "ask-evidence" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "ps")) $ProjectRoot $envAllowlist | Out-Null
} finally {
    $kill = Invoke-SmokeCommand "ccb-kill-force" "cleanup" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "kill", "-f")) $ProjectRoot $envAllowlist
    $rmuxList = Invoke-SmokeCommand "cleanup-rmux-list-sessions" "cleanup-scan" @($RmuxExe, "list-sessions") $ProjectRoot $envAllowlist
    $cleanup = [ordered]@{
        status = if ($kill.returncode -eq 0) { "cleaned" } else { "failed" }
        ok = ($kill.returncode -eq 0)
        evidence = $kill.stdout_path
    }
}

$Artifacts["ping"] = "commands/ccb-ping-ccbd.stdout.txt"
$Artifacts["doctor"] = "commands/ccb-doctor.stdout.txt"
$Artifacts["ask"] = "commands/ccb-ask.stdout.txt"
$Artifacts["runtime_session"] = "commands/ccb-ps-after-ask.stdout.txt"
$Artifacts["cleanup"] = "commands/ccb-kill-force.stdout.txt"
$Artifacts["cleanup_rmux_sessions"] = "commands/cleanup-rmux-list-sessions.stdout.txt"

$pingText = Read-ArtifactText $Artifacts["ping"]
$doctorText = Read-ArtifactText $Artifacts["doctor"]
$askText = Read-ArtifactText $Artifacts["ask"]
$runtimeSessionText = Read-ArtifactText $Artifacts["runtime_session"]
$rmuxSessionsText = Read-ArtifactText $Artifacts["cleanup_rmux_sessions"]
$taskId = Find-FirstMatch $askText @(
    "job[_ -]?id\s*[:=]\s*([A-Za-z0-9_.:-]+)",
    "task[_ -]?id\s*[:=]\s*([A-Za-z0-9_.:-]+)",
    "\b(job_[A-Za-z0-9_.:-]+)\b"
)
$askCase["task_id"] = $taskId
$askCase["reply_path"] = $Artifacts["ask"]
$askRecord = $CommandRecords | Where-Object { $_.name -eq "ccb-ask" } | Select-Object -First 1
$runtimeRef = Find-FirstMatch $runtimeSessionText @(
    "runtime[_ -]?ref\s*[:=]\s*([A-Za-z0-9_.:%\\/-]+)",
    "session[_ -]?(?:id|ref)\s*[:=]\s*([A-Za-z0-9_.:%\\/-]+)",
    "pane[_ -]?id\s*[:=]\s*([A-Za-z0-9_.:%\\/-]+)"
)
$bindingRuntimeRef = Find-BindingRuntimeRef $runtimeSessionText
if ($bindingRuntimeRef) {
    $runtimeRef = $bindingRuntimeRef
}
$runtimeBackendImpl = BackendFromRuntimeRef $runtimeRef
$backendSelectionEffective = Find-LineValue $doctorText "backend_selection_effective"
$backendSelectionSource = Find-LineValue $doctorText "backend_selection_source"
$doctorNamespaceBackend = Find-LineValue $doctorText "ccbd_namespace_backend_impl"
$pingNamespaceBackend = Find-LineValue $pingText "namespace_backend_impl"
$namespaceBackendImpl = if ($pingNamespaceBackend) { $pingNamespaceBackend } else { $doctorNamespaceBackend }

$structuredEvidence = [ordered]@{
    control_plane = [ordered]@{
        mounted = (($pingText -match "ccbd") -and (($CommandRecords | Where-Object { $_.name -eq "ccb-ping-ccbd" } | Select-Object -First 1).returncode -eq 0))
        ping_target = "ccbd"
    }
    backend_selection = [ordered]@{
        backend_impl = $backendSelectionEffective
        effective_backend = $backendSelectionEffective
        source = if ($backendSelectionSource) { $backendSelectionSource } else { "env" }
        namespace_backend_impl = $namespaceBackendImpl
        doctor_namespace_backend_impl = $doctorNamespaceBackend
        ping_namespace_backend_impl = $pingNamespaceBackend
    }
    transport = [ordered]@{
        kind = if ((($pingText + "`n" + $doctorText) -match "tcp_loopback|tcp loopback")) { "tcp_loopback" } else { $null }
    }
    ask = [ordered]@{
        provider = $AskTarget
        task_id = $taskId
        reply_path = $Artifacts["ask"]
        terminal_state = if (($askRecord -and $askRecord.returncode -eq 0) -and $askText.Trim()) { "completed" } else { $null }
        runtime_session = [ordered]@{
            backend_impl = $runtimeBackendImpl
            runtime_ref = $runtimeRef
            evidence_path = $Artifacts["runtime_session"]
        }
    }
    cleanup = Get-CleanupResidueEvidence $rmuxSessionsText
}

$hasDependencyPending = $false
foreach ($value in $dependencyStatus.Values) {
    if ($value -ne "ready") { $hasDependencyPending = $true }
}
$nonAskFailures = @($CommandRecords | Where-Object {
    $_.name -in @("ccb-start", "ccb-ping-ccbd", "ccb-doctor", "ccb-kill-force") -and $_.returncode -ne 0
})

$verdict = "pass"
$failureClass = "none"
$finalStatus = "pass"
if ($hostKind -ne "native_windows") {
    $verdict = "blocked"
    $failureClass = "environment_blocked"
    $finalStatus = "blocked"
} elseif ($hasDependencyPending) {
    $verdict = "blocked"
    $failureClass = "dependency_pending"
    $finalStatus = "blocked"
} elseif ($nonAskFailures.Count -gt 0 -or -not (Test-CleanupOk)) {
    $verdict = "system_failure"
    $failureClass = "system_failure"
    $finalStatus = "failed"
} elseif ($askRecord -and $askRecord.returncode -ne 0) {
    $verdict = "provider_failure"
    $failureClass = "provider_failure"
    $finalStatus = "failed"
}

$transcript = [ordered]@{
    schema_version = 1
    host_kind = $hostKind
    runner_host = [ordered]@{
        shell = "PowerShell"
        edition = [string]$PSVersionTable.PSEdition
        version = $PSVersionTable.PSVersion.ToString()
        executable = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    }
    control_plane = "ccbd"
    backend_impl = $Backend
    probe_bypass = $false
    backend_selection_source = if ($backendSelectionSource) { $backendSelectionSource } else { "env" }
    ccbd_transport = "tcp_loopback"
    dependency_status = $dependencyStatus
    ask_case_kind = $AskCaseKind
    ask_case = $askCase
    verdict = $verdict
    failure_class = $failureClass
    commands = $CommandRecords
    artifacts = $Artifacts
    evidence = $structuredEvidence
    redaction_summary = [ordered]@{
        redacted = $true
        raw_retention_policy = "redacted_artifacts_only"
        home_placeholder = "[USER_HOME]"
    }
    cleanup = $cleanup
    final_status = $finalStatus
}

$redactedTranscript = ConvertTo-RedactedObject $transcript
$transcriptJson = $redactedTranscript | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($TranscriptPath, $transcriptJson + "`n", [System.Text.UTF8Encoding]::new($false))

$parserArgv = @($PythonExe, $ParserPath, "--transcript", $TranscriptPath, "--json")
$parser = Invoke-SmokeCommand "parser-verdict" "parse" $parserArgv $RepoRoot $envAllowlist

if ($Json) {
    Get-Content -Raw -LiteralPath (Join-Path $ArtifactRoot $parser.stdout_path)
} else {
    Write-Host "transcript: $TranscriptPath"
    Write-Host "parser_stdout: $($parser.stdout_path)"
}

exit $parser.returncode
