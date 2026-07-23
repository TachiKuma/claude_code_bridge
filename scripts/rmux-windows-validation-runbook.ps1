param(
    [string]$ProjectRoot = "",
    [ValidateSet("fake_provider", "local_provider", "real_provider")]
    [string]$AskCaseKind = "fake_provider",
    [string]$AskTarget = "demo",
    [string]$AskMessage = "CCB Windows Rmux validation: reply with RMUX_VALIDATION_OK only.",
    [switch]$IncludeRestartReplay,
    [switch]$IncludeMultiAgent,
    [switch]$IncludeMultiProject,
    [switch]$IncludeRecovery,
    [switch]$Json
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ArtifactRoot = Join-Path $RepoRoot "artifacts/rmux-windows-validation"
$TranscriptPath = Join-Path $ArtifactRoot "manual-transcript.json"
$PythonExe = (Get-Command python -ErrorAction Stop).Source
$CcbScript = Join-Path $RepoRoot "ccb.py"
$MatrixScript = Join-Path $RepoRoot "scripts/rmux_windows_validation_matrix.py"
$CommandRecords = New-Object System.Collections.Generic.List[object]
$Artifacts = [ordered]@{}

if (-not [string]$ProjectRoot) {
    $ProjectRoot = Join-Path $env:TEMP ("ccb-rmux-validation-" + ([guid]::NewGuid().ToString("N").Substring(0, 8)))
}

function New-Directory([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Redact-Text([string]$Text) {
    $value = [string]$Text
    $userHome = [string]$env:USERPROFILE
    if ($userHome) {
        foreach ($variant in @($userHome, $userHome.Replace("\", "/"), $userHome.Replace("\", "\\"))) {
            if ($variant) {
                $value = [regex]::Replace($value, [regex]::Escape($variant), "[USER_HOME]", "IgnoreCase")
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

function Write-ArtifactText([string]$RelativePath, [string]$Text) {
    $path = Join-Path $ArtifactRoot $RelativePath
    New-Directory (Split-Path -Parent $path)
    [System.IO.File]::WriteAllText($path, (Redact-Text $Text), [System.Text.UTF8Encoding]::new($false))
    return $RelativePath.Replace("\", "/")
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

function Quote-Argument([string]$Value) {
    if ($Value -notmatch '[\s"]') {
        return $Value
    }
    return '"' + $Value.Replace('\', '\\').Replace('"', '\"') + '"'
}

function Invoke-ValidationCommand(
    [string]$Name,
    [string]$Scenario,
    [string[]]$Argv,
    [string]$Cwd,
    [hashtable]$EnvAllowlist,
    [int]$TimeoutSeconds = 180
) {
    New-Directory $Cwd
    $stdoutRel = "commands/$Name.stdout.txt"
    $stderrRel = "commands/$Name.stderr.txt"
    $startedAt = [DateTimeOffset]::UtcNow
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $stdout = ""
    $stderr = ""
    $returnCode = 127
    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $Argv[0]
        $psi.Arguments = (($Argv | Select-Object -Skip 1 | ForEach-Object { Quote-Argument ([string]$_) }) -join " ")
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
            try { $process.Kill() } catch {}
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
        scenario = $Scenario
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

function New-CcbArgv([string[]]$CliArgs) {
    return @($PythonExe, $CcbScript) + $CliArgs
}

function Test-NativeWindows {
    $isWindowsRuntime = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform(
        [System.Runtime.InteropServices.OSPlatform]::Windows
    )
    return $isWindowsRuntime -and -not $env:WSL_DISTRO_NAME -and -not $env:MSYSTEM
}

function Initialize-RmuxRouteApprovalFixture([string]$Root) {
    $relativeDir = ".codestable/features/2026-07-19-rmux-route-approval"
    $sourceDir = Join-Path $RepoRoot $relativeDir
    $targetDir = Join-Path $Root $relativeDir
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
    $targetCapabilityPath = Join-Path $Root $capabilityRef
    if (-not (Test-Path -LiteralPath $sourceCapabilityPath)) {
        throw "missing rmux capability report source asset: $sourceCapabilityPath"
    }
    New-Directory (Split-Path -Parent $targetCapabilityPath)
    Copy-Item -LiteralPath $sourceCapabilityPath -Destination $targetCapabilityPath -Force
}

function Initialize-SmokeProject([string]$Root) {
    New-Directory $Root
    Initialize-RmuxRouteApprovalFixture $Root
    $configPath = Join-Path $Root ".ccb/ccb.config"
    New-Directory (Split-Path -Parent $configPath)
    $provider = if ($AskCaseKind -eq "fake_provider") { "fake" } else { "codex" }
    $layout = "${AskTarget}:$provider"
    $defaultAgents = "`"$AskTarget`""
    $extraAgentConfig = ""
    if ($IncludeMultiAgent) {
        $layout = "${AskTarget}:$provider, reviewer:fake"
        $defaultAgents = "`"$AskTarget`", `"reviewer`""
        $extraAgentConfig = @"

[agents.reviewer]
provider = "fake"
target = "."
workspace_mode = "inplace"
restore = "auto"
permission = "manual"
"@
    }
    $config = @"
version = 2
default_agents = [$defaultAgents]
layout = "$layout"

[runtime.mux]
backend = "rmux"

[agents.$AskTarget]
provider = "$provider"
target = "."
workspace_mode = "inplace"
restore = "auto"
permission = "manual"
$extraAgentConfig
"@
    [System.IO.File]::WriteAllText($configPath, $config, [System.Text.UTF8Encoding]::new($false))
}

function Read-ArtifactText([string]$RelativePath) {
    $path = Join-Path $ArtifactRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        return ""
    }
    return Get-Content -Raw -LiteralPath $path
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
            $residue.Add([pscustomobject]@{ pid = [int]$process.ProcessId; name = [string]$process.Name }) | Out-Null
        }
    } catch {
        $residue.Add([pscustomobject]@{ pid = 0; name = "process-scan-failed" }) | Out-Null
    }
    return @($residue.ToArray())
}

function Get-CleanupEvidence([string]$RmuxListText, [string]$Root = $ProjectRoot) {
    $ccbRoot = Join-Path $Root ".ccb"
    $tokenFiles = @()
    $endpointFiles = @()
    if (Test-Path -LiteralPath $ccbRoot) {
        $tokenFiles = @(Get-ChildItem -LiteralPath $ccbRoot -Recurse -File -Filter "*token*.json" -ErrorAction SilentlyContinue)
        $candidateFiles = @(Get-ChildItem -LiteralPath $ccbRoot -Recurse -File -ErrorAction SilentlyContinue)
        foreach ($file in $candidateFiles) {
            $name = [string]$file.Name
            if ($name -notmatch '(endpoint|socket)') {
                continue
            }
            $endpointFiles += $file
        }
    }
    $projectMarker = [regex]::Escape((Split-Path -Leaf $Root))
    $rmuxHasProjectMarker = [regex]::IsMatch([string]$RmuxListText, $projectMarker, "IgnoreCase")
    return [ordered]@{
        endpoint_removed = ($endpointFiles.Count -eq 0)
        token_removed = ($tokenFiles.Count -eq 0)
        rmux_namespace_removed = -not $rmuxHasProjectMarker
        session_removed = -not $rmuxHasProjectMarker
        endpoint_residue = @($endpointFiles | ForEach-Object { $_.FullName })
        token_residue = @($tokenFiles | ForEach-Object { $_.FullName })
        owned_process_residue = @(Get-OwnedProcessResidue)
    }
}

function New-ScenarioResult([string]$Scenario, [bool]$Observed, [string]$Classification, [string]$EvidencePath) {
    return [ordered]@{
        observed = $Observed
        classification = $Classification
        evidence = $EvidencePath
    }
}

function Select-Classification([bool]$Ok, [string]$FailureClassification) {
    if ($Ok) {
        return "pass"
    }
    return $FailureClassification
}

function Select-ValidNonSuccessClassification([bool]$Ok, [string]$EvidenceText) {
    if ($Ok) {
        return "pass"
    }
    if ([string]$EvidenceText -match "restart_status:\s*blocked|blocker:\s*reason=|unsupported_for_backend") {
        return "valid_non_success"
    }
    return "system_failure"
}

function Test-CommandsSucceeded([string[]]$Names) {
    foreach ($name in $Names) {
        $record = $CommandRecords | Where-Object { $_.name -eq $name } | Select-Object -First 1
        if ($null -eq $record -or $record.returncode -ne 0) {
            return $false
        }
    }
    return $true
}

function Test-CommandsObserved([string[]]$Names) {
    foreach ($name in $Names) {
        $record = $CommandRecords | Where-Object { $_.name -eq $name } | Select-Object -First 1
        if ($null -eq $record) {
            return $false
        }
    }
    return $true
}

New-Directory $ArtifactRoot
Initialize-SmokeProject $ProjectRoot

$rmuxCommand = Get-Command rmux -ErrorAction SilentlyContinue
$rmuxExe = if ($rmuxCommand) { $rmuxCommand.Source } else { "rmux" }
$envAllowlist = @{
    CCB_MUX_BACKEND = "rmux"
    CCB_RMUX_BIN = $rmuxExe
    CCB_SOURCE_RUNTIME_OK = "1"
    CCB_TEST_ENTRYPOINT = if ($AskCaseKind -eq "fake_provider") { "1" } else { $env:CCB_TEST_ENTRYPOINT }
    PYTHONUTF8 = "1"
}
$hostKind = if (Test-NativeWindows) { "native_windows" } else { "unsupported_host" }
$scenarioResults = [ordered]@{}
$cleanupEvidence = [ordered]@{
    endpoint_removed = $false
    token_removed = $false
    rmux_namespace_removed = $false
    session_removed = $false
    owned_process_residue = @()
}

try {
    Invoke-ValidationCommand "preflight-python" "preflight" @($PythonExe, "--version") $RepoRoot $envAllowlist | Out-Null
    Invoke-ValidationCommand "preflight-ccb" "preflight" (New-CcbArgv -CliArgs @("--help")) $RepoRoot $envAllowlist | Out-Null
    Invoke-ValidationCommand "preflight-rmux-version" "preflight" @($rmuxExe, "-V") $RepoRoot $envAllowlist | Out-Null
    Invoke-ValidationCommand "ccb-start" "start_ping" (New-CcbArgv -CliArgs @("--project", $ProjectRoot)) $ProjectRoot $envAllowlist | Out-Null
    Invoke-ValidationCommand "ccb-ping-ccbd" "start_ping" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "ping", "ccbd")) $ProjectRoot $envAllowlist | Out-Null
    Invoke-ValidationCommand "ccb-doctor" "diagnostics" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "doctor")) $ProjectRoot $envAllowlist | Out-Null
    Invoke-ValidationCommand "ccb-ask" "ask" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "ask", "--artifact-reply", $AskTarget, "--", $AskMessage)) $ProjectRoot $envAllowlist | Out-Null
    Invoke-ValidationCommand "ccb-ps-after-ask" "ask" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "ps")) $ProjectRoot $envAllowlist | Out-Null
    if ($IncludeRestartReplay) {
        Invoke-ValidationCommand "ccb-restart-agent" "restart_replay" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "restart", $AskTarget)) $ProjectRoot $envAllowlist | Out-Null
        Invoke-ValidationCommand "ccb-ps-after-restart" "restart_replay" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "ps")) $ProjectRoot $envAllowlist | Out-Null
    }
    if ($IncludeMultiAgent) {
        Invoke-ValidationCommand "ccb-ask-reviewer" "multi_agent" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "ask", "--artifact-reply", "reviewer", "--", "CCB Windows Rmux validation reviewer ping.")) $ProjectRoot $envAllowlist | Out-Null
        Invoke-ValidationCommand "ccb-ps-multi-agent" "multi_agent" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "ps")) $ProjectRoot $envAllowlist | Out-Null
    }
    if ($IncludeMultiProject) {
        $ProjectRootB = "$ProjectRoot-b"
        Initialize-SmokeProject $ProjectRootB
        Invoke-ValidationCommand "ccb-start-project-b" "multi_project" (New-CcbArgv -CliArgs @("--project", $ProjectRootB)) $ProjectRootB $envAllowlist | Out-Null
        Invoke-ValidationCommand "ccb-ping-project-b" "multi_project" (New-CcbArgv -CliArgs @("--project", $ProjectRootB, "ping", "ccbd")) $ProjectRootB $envAllowlist | Out-Null
        Invoke-ValidationCommand "ccb-ask-project-b" "multi_project" (New-CcbArgv -CliArgs @("--project", $ProjectRootB, "ask", "--artifact-reply", $AskTarget, "--", "CCB Windows Rmux validation second project ping.")) $ProjectRootB $envAllowlist | Out-Null
        Invoke-ValidationCommand "ccb-kill-project-b" "multi_project" (New-CcbArgv -CliArgs @("--project", $ProjectRootB, "kill", "-f")) $ProjectRootB $envAllowlist | Out-Null
    }
    if ($IncludeRecovery) {
        Invoke-ValidationCommand "ccb-recovery-restart-agent" "supervision_recovery" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "restart", $AskTarget)) $ProjectRoot $envAllowlist | Out-Null
        Invoke-ValidationCommand "ccb-recovery-ping" "supervision_recovery" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "ping", "ccbd")) $ProjectRoot $envAllowlist | Out-Null
    }
} finally {
    $kill = Invoke-ValidationCommand "ccb-kill-force" "kill" (New-CcbArgv -CliArgs @("--project", $ProjectRoot, "kill", "-f")) $ProjectRoot $envAllowlist
    $rmuxList = Invoke-ValidationCommand "cleanup-rmux-list-sessions" "kill" @($rmuxExe, "list-sessions") $ProjectRoot $envAllowlist
    $cleanupEvidence = Get-CleanupEvidence (Read-ArtifactText $rmuxList.stdout_path)
}

$Artifacts["ping"] = "commands/ccb-ping-ccbd.stdout.txt"
$Artifacts["doctor"] = "commands/ccb-doctor.stdout.txt"
$Artifacts["ask"] = "commands/ccb-ask.stdout.txt"
$Artifacts["runtime_session"] = "commands/ccb-ps-after-ask.stdout.txt"
$Artifacts["cleanup"] = "commands/ccb-kill-force.stdout.txt"
$Artifacts["residue"] = "manual-transcript.json"

$startPingObserved = Test-CommandsObserved @("ccb-start", "ccb-ping-ccbd")
$startPingOk = (($CommandRecords | Where-Object { $_.name -eq "ccb-start" } | Select-Object -First 1).returncode -eq 0) -and (($CommandRecords | Where-Object { $_.name -eq "ccb-ping-ccbd" } | Select-Object -First 1).returncode -eq 0)
$askOk = (($CommandRecords | Where-Object { $_.name -eq "ccb-ask" } | Select-Object -First 1).returncode -eq 0)
$doctorText = Read-ArtifactText $Artifacts["doctor"]
$diagnosticsOk = (Test-CommandsSucceeded @("ccb-doctor")) -and ($doctorText -match "ccbd_state:|ccbd_socket_path:|ccbd_effective_socket_path:") -and ($doctorText -match "backend_selection_backend_impl:\s*rmux|namespace_backend_impl:\s*rmux")
$cleanupOk = $cleanupEvidence.endpoint_removed -and $cleanupEvidence.token_removed -and $cleanupEvidence.rmux_namespace_removed -and $cleanupEvidence.session_removed
$scenarioResults["start_ping"] = New-ScenarioResult "start_ping" $startPingObserved (Select-Classification $startPingOk "system_failure") $Artifacts["ping"]
$scenarioResults["ask"] = New-ScenarioResult "ask" $true (Select-Classification $askOk "provider_failure") $Artifacts["ask"]
$scenarioResults["kill"] = New-ScenarioResult "kill" $true (Select-Classification $cleanupOk "system_failure") $Artifacts["cleanup"]
$scenarioResults["diagnostics"] = New-ScenarioResult "diagnostics" $true (Select-Classification $diagnosticsOk "system_failure") $Artifacts["doctor"]
if ($IncludeRestartReplay) {
    $restartOk = Test-CommandsSucceeded @("ccb-restart-agent", "ccb-ps-after-restart")
    $restartEvidence = (Read-ArtifactText "commands/ccb-restart-agent.stdout.txt") + "`n" + (Read-ArtifactText "commands/ccb-restart-agent.stderr.txt")
    $Artifacts["restart_replay"] = "commands/ccb-ps-after-restart.stdout.txt"
    $scenarioResults["restart_replay"] = New-ScenarioResult "restart_replay" $true (Select-ValidNonSuccessClassification $restartOk $restartEvidence) $Artifacts["restart_replay"]
}
if ($IncludeMultiAgent) {
    $multiAgentOk = Test-CommandsSucceeded @("ccb-ask-reviewer", "ccb-ps-multi-agent")
    $Artifacts["multi_agent"] = "commands/ccb-ps-multi-agent.stdout.txt"
    $scenarioResults["multi_agent"] = New-ScenarioResult "multi_agent" $true (Select-Classification $multiAgentOk "provider_failure") $Artifacts["multi_agent"]
}
if ($IncludeMultiProject) {
    $multiProjectOk = Test-CommandsSucceeded @("ccb-start-project-b", "ccb-ping-project-b", "ccb-ask-project-b", "ccb-kill-project-b")
    $Artifacts["multi_project"] = "commands/ccb-ping-project-b.stdout.txt"
    $scenarioResults["multi_project"] = New-ScenarioResult "multi_project" $true (Select-Classification $multiProjectOk "system_failure") $Artifacts["multi_project"]
}
if ($IncludeRecovery) {
    $recoveryOk = Test-CommandsSucceeded @("ccb-recovery-restart-agent", "ccb-recovery-ping")
    $recoveryEvidence = (Read-ArtifactText "commands/ccb-recovery-restart-agent.stdout.txt") + "`n" + (Read-ArtifactText "commands/ccb-recovery-restart-agent.stderr.txt")
    $Artifacts["supervision_recovery"] = "commands/ccb-recovery-ping.stdout.txt"
    $scenarioResults["supervision_recovery"] = New-ScenarioResult "supervision_recovery" $true (Select-ValidNonSuccessClassification $recoveryOk $recoveryEvidence) $Artifacts["supervision_recovery"]
}

$transcript = [ordered]@{
    schema_version = 1
    host_kind = $hostKind
    control_plane = "ccbd"
    backend_impl = "rmux"
    probe_bypass = $false
    backend_selection_source = "env"
    ccbd_transport = "tcp_loopback"
    commands = $CommandRecords
    artifacts = $Artifacts
    evidence = [ordered]@{
        cleanup = $cleanupEvidence
    }
    redaction_summary = [ordered]@{
        redacted = $true
        raw_retention_policy = "redacted_artifacts_only"
        home_placeholder = "[USER_HOME]"
    }
    cleanup = [ordered]@{
        status = if ($cleanupOk) { "cleaned" } else { "failed" }
        ok = $cleanupOk
        evidence = $cleanupEvidence
    }
    scenario_results = $scenarioResults
}

$redactedTranscript = ConvertTo-RedactedObject $transcript
$transcriptJson = $redactedTranscript | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($TranscriptPath, $transcriptJson + "`n", [System.Text.UTF8Encoding]::new($false))

$parser = Invoke-ValidationCommand "matrix-parser" "parse" @($PythonExe, $MatrixScript, "--lane", "windows_true_host", "--scope", "full", "--transcript", $TranscriptPath, "--json") $RepoRoot $envAllowlist

if ($Json) {
    Get-Content -Raw -LiteralPath (Join-Path $ArtifactRoot $parser.stdout_path)
} else {
    Write-Host "transcript: $TranscriptPath"
    Write-Host "matrix_parser_stdout: $($parser.stdout_path)"
}

exit $parser.returncode
