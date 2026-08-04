param(
    [string] $ProjectRoot = "",
    [string] $Ccb8Path = "",
    [string] $RepoRoot = "E:/GitHub开源项目/TachiKuma/claude_code_bridge",
    [string] $OutputDir = "",
    [string] $HerdrExe = "",
    [string] $HerdrSession = "",
    [int] $ExpectedAgents = 2,
    [string] $ObservedHerdrAgentsPanelText = "",
    [switch] $ObservedWindowsFlash,
    [switch] $AllowNonHerdrUi,
    [switch] $SelfTest,
    [int] $StartTimeoutSeconds = 120,
    [int] $PostStartWaitSeconds = 5,
    [int] $SampleIntervalMs = 200
)

$ErrorActionPreference = 'Stop'
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-Utf8NoBom {
    param(
        [string] $Path,
        [string] $Content
    )
    $parent = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

function Set-SpikeProgress {
    param(
        [string] $Activity,
        [string] $Status,
        [int] $PercentComplete = -1,
        [int] $Id = 1,
        [string] $CurrentOperation = ""
    )
    $params = @{
        Id = $Id
        Activity = $Activity
        Status = $Status
    }
    if ($PercentComplete -ge 0) {
        $params.PercentComplete = [Math]::Min(100, [Math]::Max(0, $PercentComplete))
    }
    if (-not [string]::IsNullOrWhiteSpace($CurrentOperation)) {
        $params.CurrentOperation = $CurrentOperation
    }
    Write-Progress @params
}

function Append-Utf8NoBom {
    param(
        [string] $Path,
        [string] $Content
    )
    $parent = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    [System.IO.File]::AppendAllText($Path, $Content, $script:Utf8NoBom)
}

function Redact-Text {
    param([string] $Text)
    if ($null -eq $Text) {
        return ""
    }
    $value = [string] $Text
    $value = [regex]::Replace($value, '(?i)(api[_-]?key|token|secret|password)(\s*[:=]\s*|\s+)[^;\s"''<>]+', '$1$2<redacted>')
    $value = [regex]::Replace($value, '(?i)(bearer)\s+[a-z0-9._~+/-]+', '$1 <redacted>')
    return $value
}

function ConvertTo-JsonLine {
    param([object] $Value)
    return (($Value | ConvertTo-Json -Depth 30 -Compress) + [Environment]::NewLine)
}

function Quote-WindowsProcessArgument {
    param([string] $Argument)
    $value = [string] $Argument
    if ($value.Length -gt 0 -and $value.IndexOfAny([char[]] @(' ', "`t", '"')) -lt 0) {
        return $value
    }
    $result = '"'
    $backslashes = 0
    foreach ($char in $value.ToCharArray()) {
        if ($char -eq '\') {
            $backslashes += 1
            continue
        }
        if ($char -eq '"') {
            $result += '\' * (($backslashes * 2) + 1)
            $result += '"'
            $backslashes = 0
            continue
        }
        if ($backslashes -gt 0) {
            $result += '\' * $backslashes
            $backslashes = 0
        }
        $result += $char
    }
    if ($backslashes -gt 0) {
        $result += '\' * ($backslashes * 2)
    }
    return $result + '"'
}

function Join-WindowsProcessArguments {
    param([string[]] $Arguments)
    return (@($Arguments) | ForEach-Object { Quote-WindowsProcessArgument -Argument $_ }) -join ' '
}

function Resolve-OptionalPath {
    param(
        [string] $Path,
        [string] $Fallback
    )
    $candidate = if ([string]::IsNullOrWhiteSpace($Path)) { $Fallback } else { $Path }
    if ([string]::IsNullOrWhiteSpace($candidate)) {
        return ""
    }
    return (Resolve-Path -LiteralPath $candidate -ErrorAction Stop).ProviderPath
}

function Resolve-HerdrExe {
    param([string] $Explicit)
    if (-not [string]::IsNullOrWhiteSpace($Explicit)) {
        return (Resolve-Path -LiteralPath $Explicit -ErrorAction Stop).ProviderPath
    }
    if (-not [string]::IsNullOrWhiteSpace($env:CCB_HERDR_EXE) -and (Test-Path -LiteralPath $env:CCB_HERDR_EXE)) {
        return (Resolve-Path -LiteralPath $env:CCB_HERDR_EXE -ErrorAction Stop).ProviderPath
    }
    $default = 'C:/Users/Administrator/AppData/Local/Programs/Herdr/herdr.exe'
    if (Test-Path -LiteralPath $default) {
        return (Resolve-Path -LiteralPath $default -ErrorAction Stop).ProviderPath
    }
    return 'herdr'
}

function New-CommandRef {
    param(
        [string] $Name,
        [string[]] $Command,
        [int] $ExitCode,
        [bool] $TimedOut,
        [int] $ElapsedMs,
        [string] $StdoutPath,
        [string] $StderrPath,
        [string] $RefPath
    )
    $payload = [ordered] @{
        name = $Name
        command = @($Command | ForEach-Object { Redact-Text -Text $_ })
        exit_code = $ExitCode
        timed_out = $TimedOut
        elapsed_ms = $ElapsedMs
        stdout_ref = $StdoutPath
        stderr_ref = $StderrPath
    }
    Write-Utf8NoBom -Path $RefPath -Content (($payload | ConvertTo-Json -Depth 20) + [Environment]::NewLine)
}

function Invoke-CapturedCommand {
    param(
        [string] $Name,
        [string[]] $Command,
        [string] $WorkingDirectory,
        [string] $RawDir,
        [int] $TimeoutSeconds = 30
    )
    $stdoutPath = Join-Path $RawDir ($Name + '.stdout.txt')
    $stderrPath = Join-Path $RawDir ($Name + '.stderr.txt')
    $refPath = Join-Path $RawDir ($Name + '.json')

    $actualCommand = @($Command)
    if ($actualCommand[0].ToLowerInvariant().EndsWith('.cmd') -or $actualCommand[0].ToLowerInvariant().EndsWith('.bat')) {
        $cmdText = Join-WindowsProcessArguments -Arguments $actualCommand
        $actualCommand = @($env:ComSpec, '/d', '/s', '/c', $cmdText)
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $actualCommand[0]
    $psi.Arguments = Join-WindowsProcessArguments -Arguments @($actualCommand | Select-Object -Skip 1)
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    [void] $process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $timedOut = $false
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status ('running ' + $Name) -CurrentOperation ($Command -join ' ')
    while (-not $process.HasExited) {
        if ($process.WaitForExit(1000)) {
            break
        }
        if ($TimeoutSeconds -gt 0 -and $sw.Elapsed.TotalSeconds -ge $TimeoutSeconds) {
            $timedOut = $true
            break
        }
        $elapsedSeconds = [Math]::Round($sw.Elapsed.TotalSeconds, 1)
        $percent = if ($TimeoutSeconds -gt 0) {
            [int] ([Math]::Min(99, (($sw.Elapsed.TotalSeconds / $TimeoutSeconds) * 100)))
        } else {
            -1
        }
        Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status ('running ' + $Name + ', waited ' + $elapsedSeconds + 's') -PercentComplete $percent -CurrentOperation ($Command -join ' ')
    }
    if ($timedOut -or -not $process.HasExited) {
        $timedOut = $true
        try { $process.Kill() } catch {}
        try { $process.WaitForExit(5000) | Out-Null } catch {}
    }
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status ('completed ' + $Name) -PercentComplete 100 -CurrentOperation ($Command -join ' ')
    try { $stdoutTask.Wait(5000) | Out-Null } catch {}
    try { $stderrTask.Wait(5000) | Out-Null } catch {}
    $sw.Stop()
    Write-Progress -Id 1 -Activity 'Herdr UI integration spike' -Completed

    $stdoutText = Redact-Text -Text ([string] $stdoutTask.Result)
    $stderrText = Redact-Text -Text ([string] $stderrTask.Result)
    Write-Utf8NoBom -Path $stdoutPath -Content $stdoutText
    Write-Utf8NoBom -Path $stderrPath -Content $stderrText
    $exitCode = if ($timedOut) { 124 } else { [int] $process.ExitCode }
    New-CommandRef -Name $Name -Command $Command -ExitCode $exitCode -TimedOut $timedOut -ElapsedMs ([int] $sw.ElapsedMilliseconds) -StdoutPath $stdoutPath -StderrPath $stderrPath -RefPath $refPath

    return [ordered] @{
        name = $Name
        exit_code = $exitCode
        timed_out = $timedOut
        elapsed_ms = [int] $sw.ElapsedMilliseconds
        ref = $refPath
        stdout_ref = $stdoutPath
        stderr_ref = $stderrPath
        stdout_tail = if ($stdoutText.Length -gt 1200) { $stdoutText.Substring($stdoutText.Length - 1200) } else { $stdoutText }
        stderr_tail = if ($stderrText.Length -gt 1200) { $stderrText.Substring($stderrText.Length - 1200) } else { $stderrText }
    }
}

function Invoke-DetachedCommand {
    param(
        [string] $Name,
        [string[]] $Command,
        [string] $WorkingDirectory,
        [string] $RawDir,
        [int] $LaunchProbeSeconds = 10
    )
    $stdoutPath = Join-Path $RawDir ($Name + '.stdout.txt')
    $stderrPath = Join-Path $RawDir ($Name + '.stderr.txt')
    $refPath = Join-Path $RawDir ($Name + '.json')

    $actualCommand = @($Command)
    if ($actualCommand[0].ToLowerInvariant().EndsWith('.cmd') -or $actualCommand[0].ToLowerInvariant().EndsWith('.bat')) {
        $cmdText = Join-WindowsProcessArguments -Arguments $actualCommand
        $actualCommand = @($env:ComSpec, '/d', '/s', '/c', $cmdText)
    }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $process = Start-Process `
        -FilePath $actualCommand[0] `
        -ArgumentList (Join-WindowsProcessArguments -Arguments @($actualCommand | Select-Object -Skip 1)) `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -WindowStyle Hidden `
        -PassThru

    $launchDeadline = (Get-Date).AddSeconds($LaunchProbeSeconds)
    $observedPid = $process.Id
    $launchStatus = 'running'
    while ((Get-Date) -lt $launchDeadline) {
        try { $process.Refresh() } catch {}
        if ($process.HasExited) {
            $launchStatus = if ($process.ExitCode -eq 0) { 'exited' } else { 'launch_failed' }
            break
        }

        $targetScript = [System.IO.Path]::ChangeExtension($Command[0], '.ps1')
        $match = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $cmdLine = [string] $_.CommandLine
                $cmdLine.IndexOf($targetScript, [StringComparison]::OrdinalIgnoreCase) -ge 0
            } |
            Select-Object -First 1
        if ($null -ne $match) {
            $observedPid = $match.ProcessId
            break
        }
        Start-Sleep -Milliseconds 250
    }

    if ($launchStatus -eq 'running') {
        $statusText = 'launched ' + $Name + ' (pid ' + $observedPid + ', running)'
    } else {
        $statusText = 'launched ' + $Name + ' (pid ' + $observedPid + ', ' + $launchStatus + ')'
    }
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status $statusText -CurrentOperation ($Command -join ' ')

    $stdoutText = ""
    $stderrText = ""
    if (Test-Path -LiteralPath $stdoutPath) {
        try { $stdoutText = Redact-Text -Text ([System.IO.File]::ReadAllText($stdoutPath)) } catch {}
    }
    if (Test-Path -LiteralPath $stderrPath) {
        try { $stderrText = Redact-Text -Text ([System.IO.File]::ReadAllText($stderrPath)) } catch {}
    }
    $sw.Stop()

    $exitCode = if ($launchStatus -eq 'launch_failed') { [int] $process.ExitCode } else { 0 }
    $payload = [ordered] @{
        name = $Name
        command = @($Command | ForEach-Object { Redact-Text -Text $_ })
        status = $launchStatus
        process_id = $observedPid
        exit_code = $exitCode
        elapsed_ms = [int] $sw.ElapsedMilliseconds
        stdout_ref = $stdoutPath
        stderr_ref = $stderrPath
    }
    Write-Utf8NoBom -Path $refPath -Content (($payload | ConvertTo-Json -Depth 20) + [Environment]::NewLine)

    return [ordered] @{
        name = $Name
        exit_code = $exitCode
        timed_out = $false
        elapsed_ms = [int] $sw.ElapsedMilliseconds
        ref = $refPath
        stdout_ref = $stdoutPath
        stderr_ref = $stderrPath
        stdout_tail = if ($stdoutText.Length -gt 1200) { $stdoutText.Substring($stdoutText.Length - 1200) } else { $stdoutText }
        stderr_tail = if ($stderrText.Length -gt 1200) { $stderrText.Substring($stderrText.Length - 1200) } else { $stderrText }
        status = $launchStatus
        process_id = $observedPid
    }
}

function Start-ProcessSampler {
    param(
        [string] $OutPath,
        [string] $ProjectRoot,
        [string] $RepoRoot,
        [int] $DurationSeconds,
        [int] $IntervalMs
    )
    $script = {
        param($OutPath, $ProjectRoot, $RepoRoot, $DurationSeconds, $IntervalMs)
        $utf8 = New-Object System.Text.UTF8Encoding($false)
        function Local-Redact {
            param([string] $Text)
            if ($null -eq $Text) { return "" }
            $value = [string] $Text
            $value = [regex]::Replace($value, '(?i)(api[_-]?key|token|secret|password)(\s*[:=]\s*|\s+)[^;\s"''<>]+', '$1$2<redacted>')
            $value = [regex]::Replace($value, '(?i)(bearer)\s+[a-z0-9._~+/-]+', '$1 <redacted>')
            return $value
        }
        $names = @('cmd.exe', 'powershell.exe', 'pwsh.exe', 'python.exe', 'pythonw.exe', 'node.exe', 'claude.exe', 'codex.exe', 'herdr.exe')
        $deadline = (Get-Date).AddSeconds($DurationSeconds)
        while ((Get-Date) -lt $deadline) {
            $now = (Get-Date).ToUniversalTime().ToString('o')
            $processes = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
                Where-Object {
                    $name = [string] $_.Name
                    $cmd = [string] $_.CommandLine
                    $names -contains $name.ToLowerInvariant() -or
                        $cmd.IndexOf($ProjectRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
                        $cmd.IndexOf($RepoRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
                        $cmd.IndexOf('ccb', [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
                        $cmd.IndexOf('herdr', [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
                        $cmd.IndexOf('claude', [StringComparison]::OrdinalIgnoreCase) -ge 0
                } |
                Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, CommandLine
            foreach ($process in @($processes)) {
                $payload = [ordered] @{
                    sampled_at = $now
                    pid = $process.ProcessId
                    parent_pid = $process.ParentProcessId
                    name = $process.Name
                    executable_path = Local-Redact -Text ([string] $process.ExecutablePath)
                    command_line = Local-Redact -Text ([string] $process.CommandLine)
                }
                [System.IO.File]::AppendAllText($OutPath, (($payload | ConvertTo-Json -Depth 10 -Compress) + [Environment]::NewLine), $utf8)
            }
            Start-Sleep -Milliseconds $IntervalMs
        }
    }
    return Start-Job -ScriptBlock $script -ArgumentList $OutPath, $ProjectRoot, $RepoRoot, $DurationSeconds, $IntervalMs
}

function Get-HostContext {
    param(
        [string] $ProjectRoot,
        [string] $RepoRoot,
        [string] $Ccb8Path,
        [string] $HerdrExe,
        [string] $HerdrSession
    )
    $herdrVars = [ordered] @{}
    foreach ($entry in Get-ChildItem Env: | Where-Object { $_.Name -like 'HERDR*' -or $_.Name -like 'CCB_HERDR*' }) {
        $herdrVars[$entry.Name] = Redact-Text -Text $entry.Value
    }
    return [ordered] @{
        captured_at = (Get-Date).ToUniversalTime().ToString('o')
        project_root = $ProjectRoot
        repo_root = $RepoRoot
        ccb8_path = $Ccb8Path
        herdr_exe = $HerdrExe
        herdr_session = $HerdrSession
        expected_agents = $ExpectedAgents
        in_herdr_ui = -not [string]::IsNullOrWhiteSpace($env:HERDR_ENV)
        herdr_env = $herdrVars
        powershell_version = $PSVersionTable.PSVersion.ToString()
        os_version = [Environment]::OSVersion.VersionString
        machine_name = [Environment]::MachineName
        user_domain = [Environment]::UserDomainName
        user_name = [Environment]::UserName
        current_directory = (Get-Location).ProviderPath
    }
}

function Get-HerdrArgs {
    param([string] $Session)
    if ([string]::IsNullOrWhiteSpace($Session)) {
        return @()
    }
    return @('--session', $Session)
}

function New-ManualObservationTemplate {
    param(
        [string] $Path,
        [string] $RunId,
        [string] $ObservedPanel,
        [bool] $ObservedFlash
    )
    $lines = @()
    $lines += '# Herdr UI integration spike manual observation'
    $lines += ''
    $lines += ('- run_id: ' + $RunId)
    $lines += ('- observed_windows_flash: ' + $ObservedFlash)
    $lines += ('- observed_herdr_agents_panel_text: ' + $ObservedPanel)
    $lines += ''
    $lines += '## Fill after running inside Herdr UI'
    $lines += ''
    $lines += '- Did Herdr left agents panel show claude/codex/etc?:'
    $lines += '- Did CCB expected provider panes become visible?:'
    $lines += '- Did cmd.exe windows flash outside the Herdr pane?:'
    $lines += '- Did manual claude in the same Herdr pane still work after this run?:'
    $lines += '- Screenshot or transcript ref, if any:'
    $lines += ''
    Write-Utf8NoBom -Path $Path -Content (($lines -join [Environment]::NewLine) + [Environment]::NewLine)
}

function Invoke-SelfTest {
    $temp = Join-Path ([System.IO.Path]::GetTempPath()) ('ccb-herdr-ui-spike-selftest-' + [Guid]::NewGuid().ToString('N') + '.json')
    try {
        $redacted = Redact-Text -Text 'token=abc password xyz bearer qwerty'
        if ($redacted -match 'abc|xyz|qwerty') {
            throw 'redaction self-test failed'
        }
        Write-Utf8NoBom -Path $temp -Content (([ordered] @{ ok = $true } | ConvertTo-Json) + [Environment]::NewLine)
        $bytes = [System.IO.File]::ReadAllBytes($temp)
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            throw 'UTF-8 BOM self-test failed'
        }
        Write-Host 'herdr_ui_integration_spike_selftest: passed'
    } finally {
        Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
    }
}

if ($SelfTest) {
    Invoke-SelfTest
    exit 0
}

$resolvedProject = Resolve-OptionalPath -Path $ProjectRoot -Fallback (Get-Location).ProviderPath
$resolvedRepo = Resolve-OptionalPath -Path $RepoRoot -Fallback ""
$resolvedCcb8 = Resolve-OptionalPath -Path $Ccb8Path -Fallback (Join-Path $resolvedProject 'ccb8.cmd')
$resolvedHerdr = Resolve-HerdrExe -Explicit $HerdrExe
$effectiveHerdrSession = if (-not [string]::IsNullOrWhiteSpace($HerdrSession)) {
    $HerdrSession
} elseif (-not [string]::IsNullOrWhiteSpace($env:CCB_HERDR_SESSION)) {
    $env:CCB_HERDR_SESSION
} elseif (-not [string]::IsNullOrWhiteSpace($env:HERDR_SESSION)) {
    $env:HERDR_SESSION
} else {
    ''
}

$runId = 'run-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $resolvedRepo ('.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/' + $runId)
}
$resolvedOut = $OutputDir
New-Item -ItemType Directory -Force -Path $resolvedOut | Out-Null
$rawDir = Join-Path $resolvedOut 'raw-command-refs'
New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

$hostContext = Get-HostContext -ProjectRoot $resolvedProject -RepoRoot $resolvedRepo -Ccb8Path $resolvedCcb8 -HerdrExe $resolvedHerdr -HerdrSession $effectiveHerdrSession
Write-Utf8NoBom -Path (Join-Path $resolvedOut 'host-context.json') -Content (($hostContext | ConvertTo-Json -Depth 30) + [Environment]::NewLine)
New-ManualObservationTemplate -Path (Join-Path $resolvedOut 'manual-observation.md') -RunId $runId -ObservedPanel $ObservedHerdrAgentsPanelText -ObservedFlash ([bool] $ObservedWindowsFlash)

$commands = @()
$herdrPrefix = Get-HerdrArgs -Session $effectiveHerdrSession
Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'collecting Herdr baseline' -PercentComplete 5
$commands += Invoke-CapturedCommand -Name 'herdr-version' -Command @($resolvedHerdr, '--version') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 15
$commands += Invoke-CapturedCommand -Name 'herdr-status-server-before' -Command @($resolvedHerdr) + $herdrPrefix + @('status', 'server', '--json') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
$commands += Invoke-CapturedCommand -Name 'herdr-api-snapshot-before' -Command @($resolvedHerdr) + $herdrPrefix + @('api', 'snapshot') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
$commands += Invoke-CapturedCommand -Name 'ccb8-wrapper-self-test' -Command @($resolvedCcb8, '--wrapper-self-test') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
$commands += Invoke-CapturedCommand -Name 'ccb8-diagnose' -Command @($resolvedCcb8, '--diagnose') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 45

$samplerPath = Join-Path $resolvedOut 'process-samples.jsonl'
$sampleSeconds = [Math]::Max($StartTimeoutSeconds + $PostStartWaitSeconds + 5, 15)
$sampler = Start-ProcessSampler -OutPath $samplerPath -ProjectRoot $resolvedProject -RepoRoot $resolvedRepo -DurationSeconds $sampleSeconds -IntervalMs $SampleIntervalMs
Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status ('sampler running for ' + $sampleSeconds + 's') -PercentComplete 20

$oldNoAttach = $env:CCB_NO_ATTACH
$oldFault = $env:CCB_CCBD_FAULTHANDLER
$oldUnbuffered = $env:PYTHONUNBUFFERED
try {
    $env:CCB_NO_ATTACH = '1'
    $env:CCB_CCBD_FAULTHANDLER = '1'
    $env:PYTHONUNBUFFERED = '1'
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'starting CCB project' -PercentComplete 35 -CurrentOperation $resolvedCcb8
    $commands += Invoke-DetachedCommand -Name 'ccb8-start-project' -Command @($resolvedCcb8) -WorkingDirectory $resolvedProject -RawDir $rawDir
    Start-Sleep -Seconds $PostStartWaitSeconds
} finally {
    if ($null -eq $oldNoAttach) { Remove-Item Env:CCB_NO_ATTACH -ErrorAction SilentlyContinue } else { $env:CCB_NO_ATTACH = $oldNoAttach }
    if ($null -eq $oldFault) { Remove-Item Env:CCB_CCBD_FAULTHANDLER -ErrorAction SilentlyContinue } else { $env:CCB_CCBD_FAULTHANDLER = $oldFault }
    if ($null -eq $oldUnbuffered) { Remove-Item Env:PYTHONUNBUFFERED -ErrorAction SilentlyContinue } else { $env:PYTHONUNBUFFERED = $oldUnbuffered }
}

$commands += Invoke-CapturedCommand -Name 'herdr-status-server-after' -Command @($resolvedHerdr) + $herdrPrefix + @('status', 'server', '--json') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
$commands += Invoke-CapturedCommand -Name 'herdr-api-snapshot-after' -Command @($resolvedHerdr) + $herdrPrefix + @('api', 'snapshot') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
$commands += Invoke-CapturedCommand -Name 'ccb8-ping-ccbd' -Command @($resolvedCcb8, 'ping', 'ccbd') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
$commands += Invoke-CapturedCommand -Name 'ccb8-ping-all' -Command @($resolvedCcb8, 'ping', 'all') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
$commands += Invoke-CapturedCommand -Name 'ccb8-ps' -Command @($resolvedCcb8, 'ps') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
$commands += Invoke-CapturedCommand -Name 'ccb8-doctor-ps' -Command @($resolvedCcb8, 'doctor', 'ps') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
$commands += Invoke-CapturedCommand -Name 'ccb8-layout-status' -Command @($resolvedCcb8, 'layout', 'status', '--json') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
$commands += Invoke-CapturedCommand -Name 'ccb8-doctor-output' -Command @($resolvedCcb8, 'doctor', '--output', (Join-Path $resolvedOut 'doctor-output')) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 60

try {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'waiting for sampler completion' -PercentComplete 90
    $sampleDeadline = (Get-Date).AddSeconds($sampleSeconds + 5)
    while ($sampler.State -eq 'Running' -and (Get-Date) -lt $sampleDeadline) {
        $remaining = [Math]::Max(0, [int] ($sampleDeadline.Subtract((Get-Date)).TotalSeconds))
        $completed = [Math]::Max(0, [Math]::Min(99, [int] ((1 - ($remaining / [double] ($sampleSeconds + 5))) * 100)))
        Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status ('waiting for sampler completion, ' + $remaining + 's remaining') -PercentComplete $completed
        if (Wait-Job -Job $sampler -Timeout 1) {
            break
        }
    }
    if ($sampler.State -eq 'Running') {
        throw 'process sampler did not finish before timeout'
    }
} finally {
    Remove-Job -Job $sampler -Force -ErrorAction SilentlyContinue
}
Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'writing evidence artifacts' -PercentComplete 98

$startCommand = @(
    $commands |
        Where-Object { $_.name -eq 'ccb8-start-project' -or $_.name -eq 'ccb8-start-new-context' } |
        Select-Object -First 1
)
$pingCommand = @($commands | Where-Object { $_.name -eq 'ccb8-ping-ccbd' } | Select-Object -First 1)
$pingText = ""
if ($pingCommand.Count -gt 0 -and (Test-Path -LiteralPath $pingCommand[0].stdout_ref)) {
    $pingText = [System.IO.File]::ReadAllText($pingCommand[0].stdout_ref)
}
$pingAllCommand = @($commands | Where-Object { $_.name -eq 'ccb8-ping-all' } | Select-Object -First 1)
$pingAllText = ""
if ($pingAllCommand.Count -gt 0 -and (Test-Path -LiteralPath $pingAllCommand[0].stdout_ref)) {
    $pingAllText = [System.IO.File]::ReadAllText($pingAllCommand[0].stdout_ref)
}
$pingAllSuccess = (
    $pingAllCommand.Count -gt 0 -and
    [int] $pingAllCommand[0].exit_code -eq 0 -and
    -not [bool] $pingAllCommand[0].timed_out -and
    $pingAllText -match 'mount_state[''"]?\s*:\s*[''"]?mounted'
)
$layoutCommand = @($commands | Where-Object { $_.name -eq 'ccb8-layout-status' } | Select-Object -First 1)
$layoutText = ""
$layoutPayload = $null
$layoutMaterializedCount = 0
$layoutConfiguredCount = 0
if ($layoutCommand.Count -gt 0 -and (Test-Path -LiteralPath $layoutCommand[0].stdout_ref)) {
    $layoutText = [System.IO.File]::ReadAllText($layoutCommand[0].stdout_ref)
    try {
        if (-not [string]::IsNullOrWhiteSpace($layoutText)) {
            $layoutPayload = $layoutText | ConvertFrom-Json -ErrorAction Stop
            foreach ($window in @($layoutPayload.windows)) {
                foreach ($agent in @($window.agents)) {
                    $layoutConfiguredCount += 1
                    $paneId = [string] $agent.pane_id
                    $runtimeState = [string] $agent.runtime_state
                    if (-not [string]::IsNullOrWhiteSpace($paneId) -and $runtimeState -ne 'missing') {
                        $layoutMaterializedCount += 1
                    }
                }
            }
        }
    } catch {
        $layoutPayload = $null
    }
}
$layoutMaterializationComplete = $layoutConfiguredCount -ge $ExpectedAgents -and $layoutMaterializedCount -ge $ExpectedAgents
$hasHerdrUiEvidence = [bool] $hostContext.in_herdr_ui -or -not [string]::IsNullOrWhiteSpace($ObservedHerdrAgentsPanelText)
$startStatus = if ($startCommand.Count -gt 0) { [string] $startCommand[0].status } else { "" }
$startExitCode = if ($startCommand.Count -gt 0 -and $null -ne $startCommand[0].exit_code) { [int] $startCommand[0].exit_code } else { 0 }
$classification = 'needs-review'
if (-not $hasHerdrUiEvidence -and -not $AllowNonHerdrUi) {
    $classification = 'blocked-not-herdr-ui'
} elseif ($startCommand.Count -eq 0 -or $startStatus -eq 'launch_failed' -or ([string]::IsNullOrWhiteSpace($startStatus) -and $startExitCode -ne 0)) {
    $classification = 'ccb8-start-failed'
} elseif ($pingText -notmatch 'mount_state:\s*mounted') {
    $classification = 'ccb-mounted-not-proven'
} elseif (-not $pingAllSuccess) {
    $classification = 'ccb-provider-ping-not-proven'
} elseif (-not $layoutMaterializationComplete) {
    $classification = 'mounted-but-layout-materialization-missing'
} elseif ([string]::IsNullOrWhiteSpace($ObservedHerdrAgentsPanelText)) {
    $classification = 'mounted-but-panel-observation-missing'
} else {
    $classification = 'mounted-with-herdr-panel-observation'
}

$summary = [ordered] @{
    schema_version = 1
    spike = 'herdr-ui-integration-spike'
    run_id = $runId
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    classification = $classification
    output_dir = $resolvedOut
    process_samples_ref = $samplerPath
    host_context_ref = Join-Path $resolvedOut 'host-context.json'
    manual_observation_ref = Join-Path $resolvedOut 'manual-observation.md'
    observed_windows_flash = [bool] $ObservedWindowsFlash
    observed_herdr_agents_panel_text = $ObservedHerdrAgentsPanelText
    has_herdr_ui_evidence = $hasHerdrUiEvidence
    expected_agents = $ExpectedAgents
    ping_all_success = $pingAllSuccess
    layout_configured_count = $layoutConfiguredCount
    layout_materialized_count = $layoutMaterializedCount
    layout_materialization_complete = $layoutMaterializationComplete
    commands = $commands
    notes = @(
        'Herdr agents panel text is manual observation unless Herdr exposes it through CLI metadata.',
        'Herdr agent detection is diagnostics evidence only; CCB provider completion/runtime authority remains CCB-owned.',
        'This spike does not claim Native Windows supported.'
    )
}
Write-Utf8NoBom -Path (Join-Path $resolvedOut 'summary.json') -Content (($summary | ConvertTo-Json -Depth 40) + [Environment]::NewLine)

$report = @()
$report += '# Herdr UI integration spike report'
$report += ''
$report += ('- run_id: ' + $runId)
$report += ('- classification: ' + $classification)
$report += ('- output_dir: ' + $resolvedOut)
$report += ('- process_samples: ' + $samplerPath)
$report += ('- observed_windows_flash: ' + [bool] $ObservedWindowsFlash)
$report += ('- observed_herdr_agents_panel_text: ' + $ObservedHerdrAgentsPanelText)
$report += ''
$report += '## Commands'
$report += ''
foreach ($command in $commands) {
    $report += ('- ' + $command.name + ': exit=' + $command.exit_code + ' timed_out=' + $command.timed_out + ' ref=' + $command.ref)
}
$report += ''
$report += '## Interpretation'
$report += ''
$report += '- If `process-samples.jsonl` contains short-lived `cmd.exe` / `powershell.exe` children but CCB ping is not mounted, classify as startup wrapper failure.'
$report += '- If CCB ping is mounted but `ccb8 layout status --json` lacks expected provider pane ids, classify as layout/materialization projection gap.'
$report += '- Herdr CLI `workspace list` / `pane list` are intentionally not used here because Herdr 0.7.5 exposes machine-readable workspace/pane state through `api snapshot` instead.'
$report += '- If Herdr agents panel shows `claude` while CCB runtime state is failed, treat Herdr agent detection as diagnostics-only evidence, not completion authority.'
$report += ''
Write-Utf8NoBom -Path (Join-Path $resolvedOut 'report.md') -Content (($report -join [Environment]::NewLine) + [Environment]::NewLine)

$summaryRef = Join-Path $resolvedOut 'summary.json'
Write-Progress -Id 1 -Activity 'Herdr UI integration spike' -Completed
Write-Host (('wrote {0} classification={1}' -f $summaryRef, $classification))
