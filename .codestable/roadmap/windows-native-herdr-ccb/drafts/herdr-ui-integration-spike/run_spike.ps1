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
    [ValidateSet('herdr-baseline', 'wrapper-file-check', 'ccb-diagnose', 'process-samples', 'ccb-start', 'ccb-herdr-open', 'post-start-herdr', 'ccb-ping', 'ccb-layout', 'startup-state-files', 'pane-verification', 'backend-route', 'herdr-v0.8-probe', 'ccb-live-diag', 'provider-logs', 'ccb-lifecycle', 'herdr-config-probe', 'provider-session-files', 'ccb-ask-smoke', 'ccb-reload-smoke')]
    [string[]] $OnlyDimension = @(),
    [ValidateSet('herdr-baseline', 'wrapper-file-check', 'ccb-diagnose', 'process-samples', 'ccb-start', 'ccb-herdr-open', 'post-start-herdr', 'ccb-ping', 'ccb-layout', 'startup-state-files', 'pane-verification', 'backend-route', 'herdr-v0.8-probe', 'ccb-live-diag', 'provider-logs', 'ccb-lifecycle', 'herdr-config-probe', 'provider-session-files', 'ccb-ask-smoke', 'ccb-reload-smoke')]
    [string[]] $SkipDimension = @(),
    [ValidateRange(1, 500)]
    [int] $PaneCaptureLines = 20,
    [int] $StartTimeoutSeconds = 120,
    [int] $PostStartWaitSeconds = 5,
    [int] $SampleIntervalMs = 200
)

$ErrorActionPreference = 'Stop'
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:SpikeDimensions = @(
    'herdr-baseline',
    'wrapper-file-check',
    'ccb-diagnose',
    'process-samples',
    'ccb-start',
    'ccb-herdr-open',
    'post-start-herdr',
    'ccb-ping',
    'ccb-layout',
    'startup-state-files',
    'pane-verification',
    'backend-route',
    'herdr-v0.8-probe',
    'ccb-live-diag',
    'provider-logs',
    'ccb-lifecycle',
    'herdr-config-probe',
    'provider-session-files',
    'ccb-ask-smoke',
    'ccb-reload-smoke'
)

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

function Read-Utf8Json {
    param(
        [string] $Path
    )
    $text = [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
    return ($text | ConvertFrom-Json)
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

function Get-EnabledSpikeDimensions {
    param(
        [string[]] $Only,
        [string[]] $Skip
    )
    $onlySet = @($Only | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
    $skipSet = @($Skip | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
    $enabled = if ($onlySet.Count -gt 0) {
        @($script:SpikeDimensions | Where-Object { $onlySet -contains $_ })
    } else {
        @($script:SpikeDimensions)
    }
    return @($enabled | Where-Object { $skipSet -notcontains $_ })
}

function Test-SpikeDimensionEnabled {
    param(
        [string] $Dimension,
        [string[]] $EnabledDimensions
    )
    return @($EnabledDimensions) -contains $Dimension
}

function Get-FailedCommandSummaries {
    param([object[]] $Commands)
    $failures = @()
    $hasCanonicalPingAll = @($Commands | Where-Object { $_.name -eq 'ccb8-ping-all' }).Count -gt 0
    foreach ($command in @($Commands)) {
        if ($hasCanonicalPingAll -and [string] $command.name -like 'ccb8-ping-all-attempt-*') {
            continue
        }
        if ([bool] $command.timed_out -or [int] $command.exit_code -ne 0) {
            $failures += [ordered] @{
                name = [string] $command.name
                exit_code = [int] $command.exit_code
                timed_out = [bool] $command.timed_out
                ref = [string] $command.ref
            }
        }
    }
    return @($failures)
}

function Read-HerdrSnapshotCandidate {
    param([object] $CommandResult)
    if ($null -eq $CommandResult) {
        return [ordered] @{
            ok = $false
            reason = 'missing-command-result'
            snapshot = $null
        }
    }
    if ([bool] $CommandResult.timed_out -or [int] $CommandResult.exit_code -ne 0) {
        return [ordered] @{
            ok = $false
            reason = ('command-failed exit_code=' + [int] $CommandResult.exit_code + ' timed_out=' + [bool] $CommandResult.timed_out)
            snapshot = $null
        }
    }
    if (-not (Test-Path -LiteralPath $CommandResult.stdout_ref)) {
        return [ordered] @{
            ok = $false
            reason = 'missing-stdout'
            snapshot = $null
        }
    }
    $snapshotText = [System.IO.File]::ReadAllText($CommandResult.stdout_ref, [System.Text.Encoding]::UTF8)
    if ([string]::IsNullOrWhiteSpace($snapshotText)) {
        return [ordered] @{
            ok = $false
            reason = 'empty-stdout'
            snapshot = $null
        }
    }
    try {
        $snapshotPayload = $snapshotText | ConvertFrom-Json -ErrorAction Stop
    } catch {
        # 解析失败时保存 raw 输出，避免证据丢失（可能因中文路径/编码导致）
        $rawRef = $null
        try {
            $rawRef = $CommandResult.stdout_ref + '.raw.txt'
            Write-Utf8NoBom -Path $rawRef -Content $snapshotText
            # 写入失败时不返回悬空路径，避免消费方信任不存在的 raw 证据
            if (-not (Test-Path -LiteralPath $rawRef)) { $rawRef = $null }
        } catch {
            $rawRef = $null
        }
        return [ordered] @{
            ok = $false
            reason = ('json-parse-failed: ' + $_.Exception.Message)
            raw_ref = $rawRef
            snapshot = $null
        }
    }
    $snapshot = if ($null -ne $snapshotPayload.result -and $null -ne $snapshotPayload.result.snapshot) {
        $snapshotPayload.result.snapshot
    } else {
        $snapshotPayload.snapshot
    }
    if ($null -eq $snapshot) {
        return [ordered] @{
            ok = $false
            reason = 'missing-snapshot-object'
            snapshot = $null
        }
    }
    return [ordered] @{
        ok = $true
        reason = ''
        snapshot = $snapshot
    }
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

function Get-RepoRootFromScript {
    param([string] $ScriptRoot)
    if ([string]::IsNullOrWhiteSpace($ScriptRoot)) {
        return ""
    }
    $path = $ScriptRoot
    for ($i = 0; $i -lt 5; $i++) {
        if ([string]::IsNullOrWhiteSpace($path)) {
            return ""
        }
        $path = Split-Path -Parent $path
    }
    if ([string]::IsNullOrWhiteSpace($path)) {
        return ""
    }
    try {
        return (Resolve-Path -LiteralPath $path -ErrorAction Stop).ProviderPath
    } catch {
        return ""
    }
}

function Resolve-SpikeOutputDir {
    param(
        [string] $OutputDir,
        [string] $RepoRoot,
        [string] $RunId,
        [string] $ScriptRoot
    )
    if (-not [string]::IsNullOrWhiteSpace($OutputDir)) {
        return $OutputDir
    }
    $resolvedRepo = Resolve-OptionalPath -Path $RepoRoot -Fallback (Get-RepoRootFromScript -ScriptRoot $ScriptRoot)
    if ([string]::IsNullOrWhiteSpace($resolvedRepo)) {
        $resolvedRepo = (Get-Location).ProviderPath
    }
    if ([string]::IsNullOrWhiteSpace($resolvedRepo)) {
        throw 'unable to resolve a repository root for the default evidence directory; pass -OutputDir explicitly'
    }
    return (Join-Path $resolvedRepo ('.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/' + $RunId))
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

function Test-Utf8Bom {
    param([string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        if ($stream.Length -lt 3) {
            return $false
        }
        $buffer = New-Object byte[] 3
        [void] $stream.Read($buffer, 0, 3)
        return $buffer[0] -eq 0xEF -and $buffer[1] -eq 0xBB -and $buffer[2] -eq 0xBF
    } finally {
        $stream.Dispose()
    }
}

function Invoke-WrapperFileCheck {
    param(
        [string] $Name,
        [string] $Ccb8Path,
        [string] $RawDir
    )
    $stdoutPath = Join-Path $RawDir ($Name + '.stdout.txt')
    $stderrPath = Join-Path $RawDir ($Name + '.stderr.txt')
    $refPath = Join-Path $RawDir ($Name + '.json')
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    $cmdPath = $Ccb8Path
    $ps1Path = [System.IO.Path]::ChangeExtension($cmdPath, '.ps1')
    $errors = @()
    if (-not (Test-Path -LiteralPath $cmdPath)) {
        $errors += ('missing wrapper cmd: ' + $cmdPath)
    }
    if (-not (Test-Path -LiteralPath $ps1Path)) {
        $errors += ('missing wrapper ps1: ' + $ps1Path)
    }
    # cmd files are ASCII — BOM would break cmd.exe parsing
    if ((Test-Path -LiteralPath $cmdPath) -and (Test-Utf8Bom -Path $cmdPath)) {
        $errors += ('wrapper cmd has UTF-8 BOM (must be plain ASCII): ' + $cmdPath)
    }
    # ps1 files with Chinese paths NEED UTF-8 BOM for PowerShell 5.1
    if ((Test-Path -LiteralPath $ps1Path) -and -not (Test-Utf8Bom -Path $ps1Path)) {
        $errors += ('wrapper ps1 missing UTF-8 BOM (required for PS 5.1 with Chinese paths): ' + $ps1Path)
    }

    $stdoutLines = @(
        ('wrapper_cmd: ' + $cmdPath),
        ('wrapper_ps1: ' + $ps1Path),
        ('wrapper_cmd_exists: ' + (Test-Path -LiteralPath $cmdPath)),
        ('wrapper_ps1_exists: ' + (Test-Path -LiteralPath $ps1Path)),
        ('wrapper_cmd_utf8_bom: ' + (Test-Utf8Bom -Path $cmdPath)),
        ('wrapper_ps1_utf8_bom: ' + (Test-Utf8Bom -Path $ps1Path))
    )
    Write-Utf8NoBom -Path $stdoutPath -Content (($stdoutLines -join [Environment]::NewLine) + [Environment]::NewLine)
    Write-Utf8NoBom -Path $stderrPath -Content (($errors -join [Environment]::NewLine) + $(if ($errors.Count -gt 0) { [Environment]::NewLine } else { "" }))
    $sw.Stop()

    $exitCode = if ($errors.Count -gt 0) { 1 } else { 0 }
    New-CommandRef -Name $Name -Command @('wrapper-file-check', $Ccb8Path) -ExitCode $exitCode -TimedOut $false -ElapsedMs ([int] $sw.ElapsedMilliseconds) -StdoutPath $stdoutPath -StderrPath $stderrPath -RefPath $refPath

    $stdoutText = [System.IO.File]::ReadAllText($stdoutPath)
    $stderrText = [System.IO.File]::ReadAllText($stderrPath)
    return [ordered] @{
        name = $Name
        exit_code = $exitCode
        timed_out = $false
        elapsed_ms = [int] $sw.ElapsedMilliseconds
        ref = $refPath
        stdout_ref = $stdoutPath
        stderr_ref = $stderrPath
        stdout_tail = $stdoutText
        stderr_tail = $stderrText
    }
}

function _ResolveCmdToPowerShell {
    param(
        [string] $CmdPath,
        [string[]] $Args
    )
    # Parse a .cmd wrapper that delegates to powershell -File <ps1>.
    # Returns the resolved command array or $null if unparseable.
    if (-not (Test-Path -LiteralPath $CmdPath)) { return $null }
    try {
        $lines = @([System.IO.File]::ReadAllLines($CmdPath))
    } catch {
        return $null
    }
    $ps1Path = $null
    foreach ($line in $lines) {
        if ($line -match 'powershell\s+.*-File\s+"([^"]+\.ps1)"') {
            $ps1Path = $Matches[1]
            break
        }
    }
    if (-not $ps1Path) { return $null }
    # Resolve relative paths against the .cmd directory
    if (-not [System.IO.Path]::IsPathRooted($ps1Path)) {
        $ps1Path = Join-Path (Split-Path -Parent $CmdPath) $ps1Path
    }
    if (-not (Test-Path -LiteralPath $ps1Path)) { return $null }
    return @('powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $ps1Path) + @($Args)
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
        # Resolve .cmd wrapper to direct PowerShell invocation to avoid
        # cmd.exe creating a visible console window (observed flash source).
        $resolved = _ResolveCmdToPowerShell -CmdPath $actualCommand[0] -Args ($actualCommand | Select-Object -Skip 1)
        if ($resolved) {
            $actualCommand = $resolved
        } else {
            # Fallback: go through cmd.exe if we can't parse the wrapper
            $cmdText = Join-WindowsProcessArguments -Arguments $actualCommand
            $actualCommand = @($env:ComSpec, '/d', '/s', '/c', $cmdText)
        }
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
        # Resolve .cmd wrapper to direct PowerShell invocation to avoid
        # cmd.exe creating a visible console window (observed flash source).
        $resolved = _ResolveCmdToPowerShell -CmdPath $actualCommand[0] -Args ($actualCommand | Select-Object -Skip 1)
        if ($resolved) {
            $actualCommand = $resolved
        } else {
            # Fallback: go through cmd.exe if we can't parse the wrapper
            $cmdText = Join-WindowsProcessArguments -Arguments $actualCommand
            $actualCommand = @($env:ComSpec, '/d', '/s', '/c', $cmdText)
        }
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
    if ($process.HasExited) {
        try { $stdoutTask.Wait(5000) | Out-Null } catch {}
        try { $stderrTask.Wait(5000) | Out-Null } catch {}
        try { $stdoutText = Redact-Text -Text ([string] $stdoutTask.Result) } catch {}
        try { $stderrText = Redact-Text -Text ([string] $stderrTask.Result) } catch {}
    }
    Write-Utf8NoBom -Path $stdoutPath -Content $stdoutText
    Write-Utf8NoBom -Path $stderrPath -Content $stderrText
    $sw.Stop()

    $exitCode = if ($launchStatus -eq 'launch_failed') { [int] $process.ExitCode } else { 0 }
    $payload = [ordered] @{
        name = $Name
        command = @($Command | ForEach-Object { Redact-Text -Text $_ })
        status = $launchStatus
        process_id = $observedPid
        create_no_window = $true
        use_shell_execute = $false
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
        create_no_window = $true
        use_shell_execute = $false
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
        $herdrName = 'herdr.exe'
        $deadline = (Get-Date).AddSeconds($DurationSeconds)
        while ((Get-Date) -lt $deadline) {
            $now = (Get-Date).ToUniversalTime().ToString('o')
            $processes = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
                Where-Object {
                    $name = [string] $_.Name
                    $cmd = [string] $_.CommandLine
                    $lowerName = $name.ToLowerInvariant()
                    # 排除旧 ccb（codex-dual / WezTerm / 用户级 .cache\ccb）——
                    # 它们与 herdr UI 中的 source-dev CCB 无关（2026-08-06 采集暴露：
                    # 裸 codex.exe 来自旧 ccb 在 WezTerm 启动，CCB_RUN_DIR 指向 .cache\ccb）。
                    $legacyCcb = $cmd -match 'codex-dual|\.cache[\\/]ccb|CCB_PARENT_PID|CCB_RUN_DIR|CCB_CALLER'
                    $isWezTermWindow = $lowerName -in @('wezterm.exe', 'wezterm-gui.exe')
                    if ($legacyCcb -or $isWezTermWindow) {
                        return $false
                    }
                    $projectRelated = $cmd.IndexOf($ProjectRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
                        $cmd.IndexOf($RepoRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0
                    # source-dev CCB 相关：ccbd / keeper / ccb.py / ccb8 wrapper / CCB Herdr 会话 /
                    # provider bridge / provider-runtime 目录 / runtime root（D:\.c8\rs）
                    $sourceCcbMarker = $cmd -match 'ccbd[\\/]|keeper_main\.py|ccb\.py|ccb8\.(cmd|ps1)|ccb-herdr|provider_backends|provider-runtime|[\\/]\.c8[\\/]rs[\\/]'
                    $isHerdr = $lowerName -eq $herdrName
                    $projectRelated -or $sourceCcbMarker -or $isHerdr
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
        # 归因提示：spike 脚本在 repo 运行但操作外部项目时，current_directory 与 project_root 不一致；
        # ccb8.cmd 通过 $PSScriptRoot 定位项目，但 ccb.py 的项目发现基于 cwd，两者可能解析到不同 config。
        # 规范化路径（分隔符/尾斜杠/大小写）后再比较，避免同一物理目录被误判为不同。
        working_directory_differs_from_project = (-not [string]::Equals(
            [System.IO.Path]::GetFullPath((Get-Location).ProviderPath).TrimEnd('\'),
            [System.IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\'),
            [System.StringComparison]::OrdinalIgnoreCase
        ))
    }
}

function Invoke-CcbLiveDiagnostics {
    param(
        [string] $ProjectRoot,
        [string] $OutDir,
        [string] $HerdrExe
    )
    $diagDir = Join-Path $OutDir 'ccb-live-diag'
    New-Item -ItemType Directory -Force -Path $diagDir | Out-Null

    $projectId = $null
    $runtimeRoot = $null
    $refPath = Join-Path $ProjectRoot '.ccb\runtime-root-ref.json'
    if (Test-Path -LiteralPath $refPath) {
        try {
            $ref = Read-Utf8Json -Path $refPath
            $projectId = [string]$ref.project_id
            $runtimeRoot = [string]$ref.runtime_state_root
        } catch {}
    }

    # 1. 进程全景（python/codex/pwsh/powershell/cmd/node + parent + cmdline）——区分 source-dev vs 旧 ccb
    $procRecords = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -in @('python.exe','codex.exe','pwsh.exe','powershell.exe','cmd.exe','node.exe') } |
        ForEach-Object {
            [ordered]@{ pid=$_.ProcessId; parent_pid=$_.ParentProcessId; name=$_.Name; command_line=(Redact-Text -Text ([string]$_.CommandLine)) }
        })
    Write-Utf8NoBom -Path (Join-Path $diagDir 'processes.json') -Content (($procRecords | ConvertTo-Json -Depth 10) + "`r`n")

    # 2. ccbd 状态文件 + agent runtime
    $sessionName = $null
    if ($runtimeRoot) {
        $ccbdDir = Join-Path $runtimeRoot 'ccbd'
        if (Test-Path -LiteralPath $ccbdDir) {
            foreach ($f in @('lease.json','lifecycle.json','keeper.json','startup-report.json','shutdown-report.json','lifecycle.jsonl','state.json','ccbd.stderr.log','keeper.stderr.log','supervision.jsonl')) {
                $src = Join-Path $ccbdDir $f
                if (Test-Path -LiteralPath $src) { Copy-Item -LiteralPath $src -Destination (Join-Path $diagDir $f) -Force }
            }
            try { $ns = Read-Utf8Json -Path (Join-Path $ccbdDir 'state.json'); $sessionName = [string]$ns.namespace_session_name } catch {}
        }
        $agentsDir = Join-Path $runtimeRoot 'agents'
        if (Test-Path -LiteralPath $agentsDir) {
            Get-ChildItem -LiteralPath $agentsDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                $rt = Join-Path $_.FullName 'runtime.json'
                if (Test-Path -LiteralPath $rt) { Copy-Item -LiteralPath $rt -Destination (Join-Path $diagDir ("agent-{0}-runtime.json" -f $_.Name)) -Force }
            }
        }
    }

    # 3. herdr CCB 会话 pane 前台进程 + pane read（codex 是否进 pane / 启动错误）
    if ($sessionName -and $HerdrExe) {
        $wsOut = & $HerdrExe workspace list --session $sessionName 2>$null | Out-String
        Write-Utf8NoBom -Path (Join-Path $diagDir 'herdr-workspaces.json') -Content $wsOut
        $paneOut = & $HerdrExe pane list --session $sessionName 2>$null | Out-String
        Write-Utf8NoBom -Path (Join-Path $diagDir 'herdr-panes.json') -Content $paneOut
        try {
            $paneList = $paneOut | ConvertFrom-Json -ErrorAction Stop
            foreach ($p in @($paneList.result.panes)) {
                $paneId = [string]$p.pane_id
                if (-not $paneId) { continue }
                $safe = $paneId.Replace(':','_')
                $pi = & $HerdrExe pane process-info --pane $paneId --session $sessionName 2>$null | Out-String
                Write-Utf8NoBom -Path (Join-Path $diagDir ("pane-{0}-process-info.txt" -f $safe)) -Content $pi
                $pr = & $HerdrExe pane read --pane $paneId --session $sessionName 2>$null | Out-String
                Write-Utf8NoBom -Path (Join-Path $diagDir ("pane-{0}-read.txt" -f $safe)) -Content $pr
            }
        } catch {}
    }

    Write-Utf8NoBom -Path (Join-Path $diagDir 'meta.txt') -Content (("project_id: " + $projectId + "`r`n") + ("runtime_root: " + $runtimeRoot + "`r`n") + ("herdr_session: " + $sessionName + "`r`n"))
}

function Get-HerdrArgs {
    param([string] $Session)
    if ([string]::IsNullOrWhiteSpace($Session)) {
        return @()
    }
    return @('--session', $Session)
}

function Add-HerdrSessionArgs {
    param(
        [string[]] $Command,
        [string] $Session
    )
    if ([string]::IsNullOrWhiteSpace($Session)) {
        return @($Command)
    }
    return @($Command) + @('--session', $Session)
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
    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ('ccb-herdr-ui-spike-selftest-' + [Guid]::NewGuid().ToString('N'))
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
        $sessionArgs = Add-HerdrSessionArgs -Command @('herdr', 'status', 'server', '--json') -Session 'demo'
        if (($sessionArgs -join ' ') -ne 'herdr status server --json --session demo') {
            throw 'Herdr session arg ordering self-test failed'
        }
        $repoRoot = Get-RepoRootFromScript -ScriptRoot $PSScriptRoot
        if ([string]::IsNullOrWhiteSpace($repoRoot)) {
            throw 'repo root derivation self-test failed'
        }
        $defaultOutputDir = Resolve-SpikeOutputDir -OutputDir '' -RepoRoot '' -RunId 'run-selftest' -ScriptRoot $PSScriptRoot
        if ([string]::IsNullOrWhiteSpace($defaultOutputDir) -or $defaultOutputDir -notmatch '[\\/]\.codestable[\\/].*[\\/]evidence[\\/]run-selftest$') {
            throw 'default output dir self-test failed'
        }
        $paneOnly = Get-EnabledSpikeDimensions -Only @('pane-verification') -Skip @()
        if (($paneOnly -join ',') -ne 'pane-verification') {
            throw 'OnlyDimension self-test failed'
        }
        $skipPane = Get-EnabledSpikeDimensions -Only @() -Skip @('pane-verification')
        if (Test-SpikeDimensionEnabled -Dimension 'pane-verification' -EnabledDimensions $skipPane) {
            throw 'SkipDimension self-test failed'
        }
        $retryFailures = @(Get-FailedCommandSummaries -Commands @(
            [ordered] @{ name = 'ccb8-ping-all-attempt-1'; exit_code = 1; timed_out = $false; ref = 'attempt-1.json' },
            [ordered] @{ name = 'ccb8-ping-all'; exit_code = 0; timed_out = $false; ref = 'canonical.json' }
        ))
        if ($retryFailures.Count -ne 0) {
            throw 'ping retry failure summary self-test failed'
        }
        $commandFailures = @(Get-FailedCommandSummaries -Commands @(
            [ordered] @{ name = 'ccb-herdr-pane-capture-demo'; exit_code = 1; timed_out = $false; ref = 'pane.json' }
        ))
        if ($commandFailures.Count -ne 1 -or [string] $commandFailures[0].name -ne 'ccb-herdr-pane-capture-demo') {
            throw 'command failure summary self-test failed'
        }
        New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
        $cmdPath = Join-Path $tempDir 'ccb8.cmd'
        $ps1Path = Join-Path $tempDir 'ccb8.ps1'
        Write-Utf8NoBom -Path $cmdPath -Content "@echo off`r`n"
        # ps1 with Chinese paths requires UTF-8 BOM for PS 5.1 compatibility
        $utf8Bom = New-Object System.Text.UTF8Encoding($true)
        [System.IO.File]::WriteAllText($ps1Path, "param()`r`n", $utf8Bom)
        $check = Invoke-WrapperFileCheck -Name 'wrapper-file-check-selftest' -Ccb8Path $cmdPath -RawDir $tempDir
        if ([int] $check.exit_code -ne 0) {
            throw 'wrapper file check self-test failed'
        }
        Write-Host 'herdr_ui_integration_spike_selftest: passed'
    } finally {
        Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Stop-SpikeResidualProcesses {
    param(
        [string] $ProjectRoot,
        [string] $RepoRoot,
        [string] $Ccb8Path,
        [int] $TrackedStartPid,
        [bool] $InsideHerdrUi
    )
    if ([string]::IsNullOrWhiteSpace($ProjectRoot) -and [string]::IsNullOrWhiteSpace($RepoRoot)) {
        Write-Warning 'spike cleanup: no project or repo root available; skipping residual process cleanup'
        return
    }
    $normalizedPaths = @(
        if (-not [string]::IsNullOrWhiteSpace($ProjectRoot)) {
            try { [System.IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\') } catch { $ProjectRoot }
        }
        if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) {
            try { [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd('\') } catch { $RepoRoot }
        }
    ) | Select-Object -Unique
    if ($normalizedPaths.Count -eq 0) {
        Write-Warning 'spike cleanup: unable to normalize any project/repo path; skipping'
        return
    }
    Write-Host ('spike cleanup: starting residual process cleanup (project=' + $ProjectRoot + ', repo=' + $RepoRoot + ')')

    # ── Phase 1: try graceful CCB shutdown via ccb.py kill -f ──
    # ccb.py 优先从 ProjectRoot 找（repo 自引用时），fallback 到 RepoRoot（ext 项目时 ccb.py 在 repo 中）
    $ccbPyCandidates = @(
        if (-not [string]::IsNullOrWhiteSpace($ProjectRoot)) { Join-Path $ProjectRoot 'ccb.py' }
        if (-not [string]::IsNullOrWhiteSpace($RepoRoot) -and $RepoRoot -ne $ProjectRoot) { Join-Path $RepoRoot 'ccb.py' }
    ) | Where-Object { Test-Path -LiteralPath $_ }
    $ccbPyPath = @($ccbPyCandidates)[0]
    if ($ccbPyPath) {
        try {
            $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
            if (-not $pythonExe) { $pythonExe = 'python' }
            $killPsi = New-Object System.Diagnostics.ProcessStartInfo
            $killPsi.FileName = $pythonExe
            $killPsi.Arguments = (Quote-WindowsProcessArgument -Argument $ccbPyPath) + ' kill -f'
            $killPsi.WorkingDirectory = $ProjectRoot
            $killPsi.UseShellExecute = $false
            $killPsi.CreateNoWindow = $true
            $killPsi.RedirectStandardOutput = $true
            $killPsi.RedirectStandardError = $true
            $killProcess = [System.Diagnostics.Process]::Start($killPsi)
            if (-not $killProcess.WaitForExit(15000)) {
                try { $killProcess.Kill() } catch {}
                Write-Warning 'spike cleanup: ccb kill -f timed out after 15s'
            } elseif ($killProcess.ExitCode -ne 0) {
                Write-Warning ('spike cleanup: ccb kill -f exited with code ' + $killProcess.ExitCode)
            } else {
                Write-Host 'spike cleanup: ccb kill -f completed'
            }
        } catch {
            Write-Warning ('spike cleanup: ccb kill -f failed: ' + $_.Exception.Message)
        }
    } else {
        Write-Host ('spike cleanup: ccb.py not found in project root or repo root; skipping graceful shutdown')
    }

    # ── Phase 2: kill tracked start process tree ──
    if ($TrackedStartPid -gt 0) {
        try {
            $proc = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $TrackedStartPid) -ErrorAction SilentlyContinue
            if ($null -ne $proc) {
                Write-Host ('spike cleanup: terminating tracked start process tree pid=' + $TrackedStartPid)
                & taskkill /F /T /PID $TrackedStartPid 2>$null
                Start-Sleep -Milliseconds 500
            }
        } catch {
            Write-Warning ('spike cleanup: taskkill on tracked start pid ' + $TrackedStartPid + ' failed: ' + $_.Exception.Message)
        }
    }

    # ── Phase 3: broad sweep — find ALL processes referencing project/repo paths ──
    # NOTE: 变量名 `$procId` 有意避开 `$pid` — PowerShell 不区分大小写，
    # $pid 会覆盖自动变量 $PID，导致自身进程过滤失效。
    $sweepTargets = @{}
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $procId = $_.ProcessId
            if ($procId -eq $PID) { return $false }
            $cmd = [string] $_.CommandLine
            if ([string]::IsNullOrWhiteSpace($cmd)) { return $false }
            $matched = $false
            foreach ($root in $normalizedPaths) {
                if ([string]::IsNullOrWhiteSpace($root)) { continue }
                if ($cmd.IndexOf($root, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
                    $matched = $true
                    break
                }
            }
            return $matched
        } |
        ForEach-Object {
            $sweepTargets[[int] $_.ProcessId] = [string] $_.Name
        }

    # ── Phase 4: herdr sweep (only outside Herdr UI) ──
    if (-not $InsideHerdrUi) {
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.ProcessId -ne $PID -and
                [string] $_.Name -eq 'herdr.exe'
            } |
            ForEach-Object {
                if (-not $sweepTargets.ContainsKey([int] $_.ProcessId)) {
                    $sweepTargets[[int] $_.ProcessId] = 'herdr.exe'
                }
            }
    } else {
        Write-Host 'spike cleanup: inside Herdr UI; skipping herdr.exe termination'
    }

    # ── Phase 5: terminate every collected target with process tree ──
    foreach ($targetPid in $sweepTargets.Keys) {
        $targetName = $sweepTargets[$targetPid]
        Write-Host ('spike cleanup: terminating ' + $targetName + ' (pid=' + $targetPid + ') and its children')
        try {
            & taskkill /F /T /PID $targetPid 2>$null
        } catch {
            try {
                Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
            } catch {}
        }
    }

    # ── Phase 6: final verification sweep ──
    Start-Sleep -Milliseconds 1500
    $stubborn = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $procId = $_.ProcessId
            if ($procId -eq $PID) { return $false }
            $cmd = [string] $_.CommandLine
            if ([string]::IsNullOrWhiteSpace($cmd)) { return $false }
            $matched = $false
            foreach ($root in $normalizedPaths) {
                if ([string]::IsNullOrWhiteSpace($root)) { continue }
                if ($cmd.IndexOf($root, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
                    $matched = $true
                    break
                }
            }
            return $matched
        })
    if ($stubborn.Count -gt 0) {
        $names = ($stubborn | ForEach-Object { "$($_.Name)(pid=$($_.ProcessId))" }) -join ', '
        Write-Warning "spike cleanup: STUBBORN processes still alive after cleanup: $names"
        foreach ($proc in $stubborn) {
            try { & taskkill /F /T /PID $proc.ProcessId 2>$null } catch {}
        }
        Start-Sleep -Milliseconds 1000
    }

    $finalCheck = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $procId = $_.ProcessId
            if ($procId -eq $PID) { return $false }
            $cmd = [string] $_.CommandLine
            if ([string]::IsNullOrWhiteSpace($cmd)) { return $false }
            $matched = $false
            foreach ($root in $normalizedPaths) {
                if ([string]::IsNullOrWhiteSpace($root)) { continue }
                if ($cmd.IndexOf($root, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
                    $matched = $true
                    break
                }
            }
            return $matched
        })
    if ($finalCheck.Count -eq 0) {
        Write-Host 'spike cleanup: ALL residual CCB/herdr processes terminated'
    } else {
        $remaining = ($finalCheck | ForEach-Object { "$($_.Name)(pid=$($_.ProcessId))" }) -join ', '
        Write-Warning "spike cleanup: could not terminate: $remaining"
    }
}

if ($SelfTest) {
    Invoke-SelfTest
    exit 0
}

$script:ccbStartPid = 0
$script:insideHerdrUi = -not [string]::IsNullOrWhiteSpace($env:HERDR_ENV)

try {

$resolvedProject = Resolve-OptionalPath -Path $ProjectRoot -Fallback (Get-Location).ProviderPath
$resolvedRepo = Resolve-OptionalPath -Path $RepoRoot -Fallback (Get-RepoRootFromScript -ScriptRoot $PSScriptRoot)
if ([string]::IsNullOrWhiteSpace($resolvedRepo)) {
    $resolvedRepo = (Get-Location).ProviderPath
}
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
$OutputDir = Resolve-SpikeOutputDir -OutputDir $OutputDir -RepoRoot $RepoRoot -RunId $runId -ScriptRoot $PSScriptRoot
$resolvedOut = $OutputDir
New-Item -ItemType Directory -Force -Path $resolvedOut | Out-Null
$rawDir = Join-Path $resolvedOut 'raw-command-refs'
New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

$enabledDimensions = Get-EnabledSpikeDimensions -Only $OnlyDimension -Skip $SkipDimension
if ($enabledDimensions.Count -eq 0) {
    throw 'no spike collection dimensions enabled'
}
$collectPaneVerification = Test-SpikeDimensionEnabled -Dimension 'pane-verification' -EnabledDimensions $enabledDimensions
$collectBackendRoute = Test-SpikeDimensionEnabled -Dimension 'backend-route' -EnabledDimensions $enabledDimensions
$collectPostStartHerdr = (Test-SpikeDimensionEnabled -Dimension 'post-start-herdr' -EnabledDimensions $enabledDimensions) -or $collectPaneVerification
$collectCcbLayout = (Test-SpikeDimensionEnabled -Dimension 'ccb-layout' -EnabledDimensions $enabledDimensions) -or $collectPaneVerification
$collectCcbDiagnose = (Test-SpikeDimensionEnabled -Dimension 'ccb-diagnose' -EnabledDimensions $enabledDimensions) -or $collectBackendRoute
$collectProcessSamples = Test-SpikeDimensionEnabled -Dimension 'process-samples' -EnabledDimensions $enabledDimensions
$collectCcbStart = Test-SpikeDimensionEnabled -Dimension 'ccb-start' -EnabledDimensions $enabledDimensions
$collectHerdrOpen = Test-SpikeDimensionEnabled -Dimension 'ccb-herdr-open' -EnabledDimensions $enabledDimensions
# ccb-herdr-open 与 ccb-start 是两种启动路径：herdr-open 用 ccb herdr open 以 Herdr
# managed backend 启动，启用时跳过 ccb-start 避免 daemon backend 冲突。
$collectCcbStart = $collectCcbStart -and -not $collectHerdrOpen
$executedDimensions = @($enabledDimensions)
foreach ($dimension in @('post-start-herdr', 'ccb-layout', 'ccb-diagnose')) {
    $isImplicitlyExecuted = (
        ($dimension -eq 'post-start-herdr' -and $collectPostStartHerdr) -or
        ($dimension -eq 'ccb-layout' -and $collectCcbLayout) -or
        ($dimension -eq 'ccb-diagnose' -and $collectCcbDiagnose)
    )
    if ($isImplicitlyExecuted -and $executedDimensions -notcontains $dimension) {
        $executedDimensions += $dimension
    }
}
$dimensionSelection = [ordered] @{
    only_dimension = @($OnlyDimension)
    skip_dimension = @($SkipDimension)
    enabled_dimensions = @($enabledDimensions)
    executed_dimensions = @($executedDimensions)
    implicit_dependencies = [ordered] @{
        post_start_herdr_for_pane_verification = $collectPaneVerification -and (-not (Test-SpikeDimensionEnabled -Dimension 'post-start-herdr' -EnabledDimensions $enabledDimensions))
        ccb_layout_for_pane_verification = $collectPaneVerification -and (-not (Test-SpikeDimensionEnabled -Dimension 'ccb-layout' -EnabledDimensions $enabledDimensions))
        ccb_diagnose_for_backend_route = $collectBackendRoute -and (-not (Test-SpikeDimensionEnabled -Dimension 'ccb-diagnose' -EnabledDimensions $enabledDimensions))
    }
    pane_capture_lines = $PaneCaptureLines
}
Write-Utf8NoBom -Path (Join-Path $resolvedOut 'collection-dimensions.json') -Content (($dimensionSelection | ConvertTo-Json -Depth 20) + [Environment]::NewLine)

$hostContext = Get-HostContext -ProjectRoot $resolvedProject -RepoRoot $resolvedRepo -Ccb8Path $resolvedCcb8 -HerdrExe $resolvedHerdr -HerdrSession $effectiveHerdrSession
Write-Utf8NoBom -Path (Join-Path $resolvedOut 'host-context.json') -Content (($hostContext | ConvertTo-Json -Depth 30) + [Environment]::NewLine)
New-ManualObservationTemplate -Path (Join-Path $resolvedOut 'manual-observation.md') -RunId $runId -ObservedPanel $ObservedHerdrAgentsPanelText -ObservedFlash ([bool] $ObservedWindowsFlash)

$commands = @()
if (Test-SpikeDimensionEnabled -Dimension 'herdr-baseline' -EnabledDimensions $enabledDimensions) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'collecting Herdr baseline' -PercentComplete 5
    $commands += Invoke-CapturedCommand -Name 'herdr-version' -Command @($resolvedHerdr, '--version') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 15
    $commands += Invoke-CapturedCommand -Name 'herdr-status-server-before' -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'status', 'server', '--json') -Session $effectiveHerdrSession) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
    $commands += Invoke-CapturedCommand -Name 'herdr-api-snapshot-before' -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'api', 'snapshot') -Session $effectiveHerdrSession) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
}
if (Test-SpikeDimensionEnabled -Dimension 'wrapper-file-check' -EnabledDimensions $enabledDimensions) {
    $commands += Invoke-WrapperFileCheck -Name 'ccb8-wrapper-file-check' -Ccb8Path $resolvedCcb8 -RawDir $rawDir
}
if ($collectCcbDiagnose) {
    $commands += Invoke-CapturedCommand -Name 'ccb8-diagnose' -Command @($resolvedCcb8, '--diagnose') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 45
}

$samplerPath = Join-Path $resolvedOut 'process-samples.jsonl'
$sampleSeconds = [Math]::Max($StartTimeoutSeconds + $PostStartWaitSeconds + 5, 15)
$sampler = $null
if ($collectProcessSamples) {
    $sampler = Start-ProcessSampler -OutPath $samplerPath -ProjectRoot $resolvedProject -RepoRoot $resolvedRepo -DurationSeconds $sampleSeconds -IntervalMs $SampleIntervalMs
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status ('sampler running for ' + $sampleSeconds + 's') -PercentComplete 20
}

# 预清理：确保无残留 CCB daemon，避免 "old ccbd did not shut down in time"。
# 结果不加入 $commands（容忍失败，不污染 failed 计数）。
if ($collectCcbStart -or $collectHerdrOpen) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'cleaning stale CCB daemon before start' -PercentComplete 25
    $null = Invoke-CapturedCommand -Name 'ccb8-pre-start-cleanup' -Command @($resolvedCcb8, 'kill', '-f') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
}

if ($collectCcbStart) {
    $oldNoAttach = $env:CCB_NO_ATTACH
    $oldFault = $env:CCB_CCBD_FAULTHANDLER
    $oldUnbuffered = $env:PYTHONUNBUFFERED
    try {
        $env:CCB_NO_ATTACH = '1'
        $env:CCB_CCBD_FAULTHANDLER = '1'
        $env:PYTHONUNBUFFERED = '1'
        Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'starting CCB project' -PercentComplete 35 -CurrentOperation $resolvedCcb8
        $startResult = Invoke-DetachedCommand -Name 'ccb8-start-project' -Command @($resolvedCcb8) -WorkingDirectory $resolvedProject -RawDir $rawDir
        $commands += $startResult
        $script:ccbStartPid = [int] $startResult.process_id
        Start-Sleep -Seconds $PostStartWaitSeconds
    } finally {
        if ($null -eq $oldNoAttach) { Remove-Item Env:CCB_NO_ATTACH -ErrorAction SilentlyContinue } else { $env:CCB_NO_ATTACH = $oldNoAttach }
        if ($null -eq $oldFault) { Remove-Item Env:CCB_CCBD_FAULTHANDLER -ErrorAction SilentlyContinue } else { $env:CCB_CCBD_FAULTHANDLER = $oldFault }
        if ($null -eq $oldUnbuffered) { Remove-Item Env:PYTHONUNBUFFERED -ErrorAction SilentlyContinue } else { $env:PYTHONUNBUFFERED = $oldUnbuffered }
    }
}

# ccb-herdr-open：ITEM-7 —— 用 `ccb herdr open --no-attach` 以 Herdr managed backend 启动 CCB，
# 采集 bootstrap 启动结果（env 注入 / capability report / daemon 冲突检测行为）。
if ($collectHerdrOpen) {
    $oldNoAttach = $env:CCB_NO_ATTACH
    $oldFault = $env:CCB_CCBD_FAULTHANDLER
    $oldUnbuffered = $env:PYTHONUNBUFFERED
    try {
        $env:CCB_NO_ATTACH = '1'
        $env:CCB_CCBD_FAULTHANDLER = '1'
        $env:PYTHONUNBUFFERED = '1'
        Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'starting CCB via ccb herdr open' -PercentComplete 37 -CurrentOperation $resolvedCcb8
        $herdrOpenResult = Invoke-DetachedCommand -Name 'ccb8-herdr-open' -Command @($resolvedCcb8, 'herdr', 'open', '--no-attach') -WorkingDirectory $resolvedProject -RawDir $rawDir
        $commands += $herdrOpenResult
        $script:ccbStartPid = [int] $herdrOpenResult.process_id
        Start-Sleep -Seconds $PostStartWaitSeconds
        $herdrOpenEvidence = [ordered] @{
            command = 'ccb8 herdr open --no-attach'
            exit_code = [int] $herdrOpenResult.exit_code
            status = [string] $herdrOpenResult.status
            timed_out = [bool] $herdrOpenResult.timed_out
            stdout_tail = [string] $herdrOpenResult.stdout_tail
            stderr_tail = [string] $herdrOpenResult.stderr_tail
            notes = @(
                'ccb herdr open 在 detached 子进程内注入 CCB_HERDR_EXE/SESSION/CAPABILITY_REPORT env',
                '启动证据以 layout/ping 维度（backend=herdr + pane 创建）为准'
            )
        }
        Write-Utf8NoBom -Path (Join-Path $resolvedOut 'herdr-open-evidence.json') -Content (($herdrOpenEvidence | ConvertTo-Json -Depth 10) + [Environment]::NewLine)
        $script:herdrOpenEvidenceRef = Join-Path $resolvedOut 'herdr-open-evidence.json'
    } finally {
        if ($null -eq $oldNoAttach) { Remove-Item Env:CCB_NO_ATTACH -ErrorAction SilentlyContinue } else { $env:CCB_NO_ATTACH = $oldNoAttach }
        if ($null -eq $oldFault) { Remove-Item Env:CCB_CCBD_FAULTHANDLER -ErrorAction SilentlyContinue } else { $env:CCB_CCBD_FAULTHANDLER = $oldFault }
        if ($null -eq $oldUnbuffered) { Remove-Item Env:PYTHONUNBUFFERED -ErrorAction SilentlyContinue } else { $env:PYTHONUNBUFFERED = $oldUnbuffered }
    }
}

# ccb-live-diag：ccbd 启动后采集 pane 前台进程 / pane read / agent runtime / 进程全景 / ccbd 日志，
# 用于诊断"codex 是否进 pane"与 stop_all 触发源。
$collectLiveDiag = Test-SpikeDimensionEnabled -Dimension 'ccb-live-diag' -EnabledDimensions $enabledDimensions
if ($collectLiveDiag) {
    Start-Sleep -Seconds 3
    try {
        Invoke-CcbLiveDiagnostics -ProjectRoot $resolvedProject -OutDir $resolvedOut -HerdrExe $resolvedHerdr
    } catch {
        Write-Warning ('ccb-live-diag failed: ' + $_.Exception.Message)
    }
}

if ($collectPostStartHerdr) {
    $commands += Invoke-CapturedCommand -Name 'herdr-status-server-after' -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'status', 'server', '--json') -Session $effectiveHerdrSession) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
    $commands += Invoke-CapturedCommand -Name 'herdr-api-snapshot-after' -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'api', 'snapshot') -Session $effectiveHerdrSession) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
}
if (Test-SpikeDimensionEnabled -Dimension 'ccb-ping' -EnabledDimensions $enabledDimensions) {
    $commands += Invoke-CapturedCommand -Name 'ccb8-ping-ccbd' -Command @($resolvedCcb8, 'ping', 'ccbd') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
    # Retry ping-all up to 3 times to allow ccbd to finish starting
    $pingAllResult = $null
    for ($pingAllAttempt = 1; $pingAllAttempt -le 3; $pingAllAttempt++) {
        $pingAllResult = Invoke-CapturedCommand -Name ('ccb8-ping-all-attempt-' + $pingAllAttempt) -Command @($resolvedCcb8, 'ping', 'all') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
        $commands += $pingAllResult
        if ($pingAllAttempt -lt 3 -and [int] $pingAllResult.exit_code -ne 0) {
            Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status ('ccb8 ping-all retry ' + $pingAllAttempt + '/3, ccbd may still be starting') -PercentComplete 62
            Start-Sleep -Seconds 3
        } else {
            break
        }
    }
    # Keep the last (best) ping-all as canonical evidence for classification.
    if ($null -ne $pingAllResult) {
        $commands += [ordered] @{
            name = 'ccb8-ping-all'
            exit_code = [int] $pingAllResult.exit_code
            timed_out = [bool] $pingAllResult.timed_out
            elapsed_ms = [int] $pingAllResult.elapsed_ms
            ref = $pingAllResult.ref
            stdout_ref = $pingAllResult.stdout_ref
            stderr_ref = $pingAllResult.stderr_ref
            stdout_tail = $pingAllResult.stdout_tail
            stderr_tail = $pingAllResult.stderr_tail
        }
    }
}
if ($collectCcbLayout) {
    $commands += Invoke-CapturedCommand -Name 'ccb8-ps' -Command @($resolvedCcb8, 'ps') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
    $commands += Invoke-CapturedCommand -Name 'ccb8-doctor-ps' -Command @($resolvedCcb8, 'doctor', 'ps') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
    $commands += Invoke-CapturedCommand -Name 'ccb8-layout-status' -Command @($resolvedCcb8, 'layout', 'status', '--json') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
}
if ((Test-SpikeDimensionEnabled -Dimension 'ccb-layout' -EnabledDimensions $enabledDimensions) -or $collectBackendRoute -or (Test-SpikeDimensionEnabled -Dimension 'startup-state-files' -EnabledDimensions $enabledDimensions)) {
    # doctor --output 产出的是 gzip tar 归档：带 .tar.gz 后缀便于人工识别，并解压供后续读取。
    $doctorOutputArchive = Join-Path $resolvedOut 'doctor-output.tar.gz'
    $doctorOutputExtractDir = Join-Path $resolvedOut 'doctor-output-extracted'
    $commands += Invoke-CapturedCommand -Name 'ccb8-doctor-output' -Command @($resolvedCcb8, 'doctor', '--output', $doctorOutputArchive) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 60
    if (Test-Path -LiteralPath $doctorOutputArchive) {
        New-Item -ItemType Directory -Force -Path $doctorOutputExtractDir | Out-Null
        $extractFailed = $false
        try {
            & tar.exe -xzf $doctorOutputArchive -C $doctorOutputExtractDir
            if ($LASTEXITCODE -ne 0) { $extractFailed = $true }
        } catch {
            $extractFailed = $true
        }
        # 解压失败或目录为空时回退旧布局，避免空目录优先于真实证据
        if ($extractFailed -or -not (Get-ChildItem -LiteralPath $doctorOutputExtractDir -Recurse -File -ErrorAction SilentlyContinue)) {
            Write-Host 'WARNING: doctor-output extraction failed or empty; falling back to legacy layout'
            $doctorOutputExtractDir = $null
        }
    }
}

# --- Extract CCB actual Herdr session from ccb8-ps output ---
$ccbHerdrSession = ''
$psResult = $commands | Where-Object { $_.name -eq 'ccb8-ps' } | Select-Object -First 1
if ($psResult -and (Test-Path -LiteralPath $psResult.stdout_ref)) {
    $psText = [System.IO.File]::ReadAllText($psResult.stdout_ref, [System.Text.Encoding]::UTF8)
    if ($psText -match 'session_name=([^\s,]+)') {
        $ccbHerdrSession = $Matches[1]
    }
}
if ([string]::IsNullOrWhiteSpace($ccbHerdrSession)) {
    $layoutResult = $commands | Where-Object { $_.name -eq 'ccb8-layout-status' } | Select-Object -First 1
    if ($layoutResult -and (Test-Path -LiteralPath $layoutResult.stdout_ref)) {
        $layoutText = [System.IO.File]::ReadAllText($layoutResult.stdout_ref, [System.Text.Encoding]::UTF8)
        if ($layoutText -match '"session_name"\s*:\s*"([^"]+)"') {
            $ccbHerdrSession = $Matches[1]
        }
    }
}
if ($collectPaneVerification -and $ccbHerdrSession -and $ccbHerdrSession -ne $effectiveHerdrSession) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status ('collecting CCB namespace snapshot via session=' + $ccbHerdrSession) -PercentComplete 76
    $commands += Invoke-CapturedCommand `
        -Name 'herdr-api-snapshot-ccb-namespace' `
        -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'api', 'snapshot') -Session $ccbHerdrSession) `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir `
        -TimeoutSeconds 20
}

# --- expanded collection dimensions (analysis 2026-08-05) ---

$stateFilesDir = Join-Path $resolvedOut 'startup-state-files'
$paneEvidenceDir = Join-Path $resolvedOut 'pane-evidence'
$backendRouteDir = Join-Path $resolvedOut 'backend-route-evidence'

# Dimension 1: CCB startup state files snapshot
if (Test-SpikeDimensionEnabled -Dimension 'startup-state-files' -EnabledDimensions $enabledDimensions) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'collecting CCB startup state files' -PercentComplete 72
    New-Item -ItemType Directory -Force -Path $stateFilesDir | Out-Null
    $ccbDir = Join-Path $resolvedProject '.ccb'
    $stateKeyFiles = @('runtime-root-ref.json', 'project.identity.json')
    foreach ($fileName in $stateKeyFiles) {
        $src = Join-Path $ccbDir $fileName
        if (Test-Path -LiteralPath $src) {
            try {
                $dest = Join-Path $stateFilesDir $fileName
                Copy-Item -LiteralPath $src -Destination $dest -Force
                Append-Utf8NoBom -Path (Join-Path $resolvedOut 'startup-state-files-manifest.txt') -Content ("copied $fileName`r`n")
            } catch {
                Append-Utf8NoBom -Path (Join-Path $resolvedOut 'startup-state-files-manifest.txt') -Content ("failed to copy $fileName : $_`r`n")
            }
        }
    }
    # Resolve the actual ccbd state directory.  When CCB_RUNTIME_STATE_HOME
    # relocates runtime state, ccbd state files live under the runtime state
    # root rather than under .ccb/ccbd/.  Parse runtime-root-ref.json (already
    # collected above) to build the correct path; fall back to .ccb/ccbd/ when
    # the ref is unavailable or the runtime-root directory does not exist.
    $runtimeStateRoot = $null
    $runtimeProjectId = $null
    $runtimeRootRefPath = Join-Path $stateFilesDir 'runtime-root-ref.json'
    if (Test-Path -LiteralPath $runtimeRootRefPath) {
        try {
            $refPayload = Get-Content -Raw -LiteralPath $runtimeRootRefPath | ConvertFrom-Json
            $runtimeStateRoot = if ($refPayload.PSObject.Properties['runtime_state_root']) { $refPayload.runtime_state_root } else { $null }
            $runtimeProjectId = if ($refPayload.PSObject.Properties['project_id']) { $refPayload.project_id } else { $null }
        } catch { }
    }
    $ccbdStateDirs = @()
    if ($runtimeStateRoot) {
        # runtime_state_root in runtime-root-ref.json already includes the
        # project_id segment (e.g. D:\.c8\rs\<project_id>).  The ccbd state
        # directory is directly under it — no additional project_id needed.
        $ccbdStateDirs += Join-Path $runtimeStateRoot 'ccbd'
    }
    $ccbdStateDirs += Join-Path $ccbDir 'ccbd'
    $ccbdStateFiles = @('lease.json', 'keeper.json', 'lifecycle.json')
    # Track copied files per-name so that files split across directories
    # are still collected from fallback paths (e.g. lease.json in runtime
    # root while keeper.json only exists under .ccb/ccbd/).
    $copiedCcbdFiles = @{}
    foreach ($ccbdSearchDir in $ccbdStateDirs) {
        if (-not (Test-Path -LiteralPath $ccbdSearchDir)) { continue }
        foreach ($fileName in $ccbdStateFiles) {
            if ($copiedCcbdFiles.ContainsKey($fileName)) { continue }
            $src = Join-Path $ccbdSearchDir $fileName
            if (Test-Path -LiteralPath $src) {
                try {
                    $dest = Join-Path $stateFilesDir $fileName
                    Copy-Item -LiteralPath $src -Destination $dest -Force
                    Append-Utf8NoBom -Path (Join-Path $resolvedOut 'startup-state-files-manifest.txt') -Content ("copied $fileName`r`n")
                    $copiedCcbdFiles[$fileName] = $true
                } catch {
                    Append-Utf8NoBom -Path (Join-Path $resolvedOut 'startup-state-files-manifest.txt') -Content ("failed to copy $fileName : $_`r`n")
                }
            }
        }
    }
    foreach ($fileName in $ccbdStateFiles) {
        $dest = Join-Path $stateFilesDir $fileName
        if (-not (Test-Path -LiteralPath $dest)) {
            Append-Utf8NoBom -Path (Join-Path $resolvedOut 'startup-state-files-manifest.txt') -Content ("skipped $fileName : not found in any ccbd state directory (searched: $($ccbdStateDirs -join ', '))`r`n")
        }
    }

    # Also copy startup-report.json from doctor output if available
    # doctor-output 是 .tar.gz 归档，优先从解压目录搜索；回退到旧目录布局。
    $startupReport = $null
    if (-not [string]::IsNullOrWhiteSpace($doctorOutputExtractDir) -and (Test-Path -LiteralPath $doctorOutputExtractDir)) {
        $foundStartupReport = Get-ChildItem -LiteralPath $doctorOutputExtractDir -Recurse -File -Filter 'startup-report.json' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $foundStartupReport) {
            $startupReport = $foundStartupReport.FullName
        }
    }
    if ($null -eq $startupReport) {
        $legacyStartupReport = Join-Path $resolvedOut 'doctor-output/startup-report.json'
        if (-not (Test-Path -LiteralPath $legacyStartupReport)) {
            $legacyStartupReport = Join-Path $resolvedOut 'doctor-output/ccbd/startup-report.json'
        }
        if (Test-Path -LiteralPath $legacyStartupReport) {
            $startupReport = $legacyStartupReport
        }
    }
    if ($null -ne $startupReport -and (Test-Path -LiteralPath $startupReport)) {
        try {
            Copy-Item -LiteralPath $startupReport -Destination (Join-Path $stateFilesDir 'startup-report.json') -Force
            Append-Utf8NoBom -Path (Join-Path $resolvedOut 'startup-state-files-manifest.txt') -Content "copied startup-report.json`r`n"
        } catch {
            Append-Utf8NoBom -Path (Join-Path $resolvedOut 'startup-state-files-manifest.txt') -Content ("failed to copy startup-report.json : $_`r`n")
        }
    }
}

# Dimension 2: Pane-level materialization verification via Herdr api snapshot pane tokens
if ($collectPaneVerification) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'validating pane materialization' -PercentComplete 78
    New-Item -ItemType Directory -Force -Path $paneEvidenceDir | Out-Null
    # Prefer CCB namespace snapshot if available, fall back to wrapper session snapshot.
    $preferredSnapshotName = if ($ccbHerdrSession -and $ccbHerdrSession -ne $effectiveHerdrSession) { 'herdr-api-snapshot-ccb-namespace' } else { 'herdr-api-snapshot-after' }
    $captureSession = if ($preferredSnapshotName -eq 'herdr-api-snapshot-ccb-namespace') { $ccbHerdrSession } else { $effectiveHerdrSession }
    $snapshotResult = $commands | Where-Object { $_.name -eq $preferredSnapshotName } | Select-Object -First 1
    $snapshotCandidate = Read-HerdrSnapshotCandidate -CommandResult $snapshotResult
    if (-not [bool] $snapshotCandidate.ok -and $preferredSnapshotName -ne 'herdr-api-snapshot-after') {
        $failedSnapshotName = $preferredSnapshotName
        $failedSnapshotReason = [string] $snapshotCandidate.reason
        $preferredSnapshotName = 'herdr-api-snapshot-after'
        $captureSession = $effectiveHerdrSession
        $snapshotResult = $commands | Where-Object { $_.name -eq $preferredSnapshotName } | Select-Object -First 1
        $snapshotCandidate = Read-HerdrSnapshotCandidate -CommandResult $snapshotResult
    }
    $paneVerificationReport = @()
    $paneVerificationReport += '# Pane materialization verification'
    $paneVerificationReport += ('- snapshot_source: ' + $preferredSnapshotName)
    $paneVerificationReport += ('- capture_session: ' + $captureSession)
    $paneVerificationReport += ('- capture_lines: ' + $PaneCaptureLines)
    if (-not [string]::IsNullOrWhiteSpace($failedSnapshotName)) {
        $paneVerificationReport += ('- snapshot_fallback_from: ' + $failedSnapshotName)
        $paneVerificationReport += ('- snapshot_fallback_reason: ' + $failedSnapshotReason)
    }
    $paneVerificationReport += ''
    if ([bool] $snapshotCandidate.ok) {
        try {
            $snapshot = $snapshotCandidate.snapshot
            $panes = $snapshot.panes
            $workspaces = $snapshot.workspaces
            $paneVerificationReport += '- snapshot_available: true'
            $paneVerificationReport += ('- pane_count: ' + @($panes).Count)
            $paneVerificationReport += ('- workspace_count: ' + @($workspaces).Count)
            $paneVerificationReport += ''
            $paneVerificationReport += '## Pane identity'
            $paneVerificationReport += ''
            foreach ($pane in @($panes)) {
                $paneId = [string] $pane.pane_id
                $title = [string] $pane.title
                $displayAgent = [string] $pane.display_agent
                $paneVerificationReport += ('- pane_id=' + $paneId + ' title=' + $title + ' display_agent=' + $displayAgent)
                $tokens = $pane.tokens
                if ($null -ne $tokens) {
                    foreach ($prop in $tokens.PSObject.Properties) {
                        $paneVerificationReport += ('  token: ' + $prop.Name + '=' + $prop.Value)
                    }
                }
            }
            $paneVerificationReport += ''
            $paneVerificationReport += '## Workspaces'
            foreach ($workspace in @($workspaces)) {
                $wsId = [string] $workspace.workspace_id
                $label = [string] $workspace.label
                $paneVerificationReport += ('- workspace_id=' + $wsId + ' label=' + $label)
            }

            # Try capturing pane content for materialized panes (non-destructive read).
            $paneVerificationReport += ''
            $paneVerificationReport += '## Pane content capture'
            $paneVerificationReport += ''
            foreach ($pane in @($panes)) {
                $paneId = [string] $pane.pane_id
                if ([string]::IsNullOrWhiteSpace($paneId)) { continue }
                $captureResult = Invoke-CapturedCommand `
                    -Name ('ccb-herdr-pane-capture-' + ($paneId -replace '[^a-zA-Z0-9_-]', '-')) `
                    -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'pane', 'read', $paneId, '--lines', ([string] $PaneCaptureLines), '--format', 'text') -Session $captureSession) `
                    -WorkingDirectory $resolvedProject `
                    -RawDir $rawDir `
                    -TimeoutSeconds 10
                $commands += $captureResult
                $captureText = if (Test-Path -LiteralPath $captureResult.stdout_ref) {
                    [System.IO.File]::ReadAllText($captureResult.stdout_ref)
                } else { '' }
                $paneVerificationReport += ('- pane_id=' + $paneId + ' exit_code=' + [int] $captureResult.exit_code + ' tail=' + ($captureText.Substring(0, [Math]::Min($captureText.Length, 200))))
            }
        } catch {
            $paneVerificationReport += ('- snapshot_parse_error: ' + $_.Exception.Message)
        }
    } else {
        $paneVerificationReport += '- snapshot_available: false'
        $paneVerificationReport += ('- snapshot_unavailable_reason: ' + [string] $snapshotCandidate.reason)
    }
    Write-Utf8NoBom -Path (Join-Path $paneEvidenceDir 'pane-verification.md') -Content (($paneVerificationReport -join [Environment]::NewLine) + [Environment]::NewLine)
}

# Dimension 3: Backend resolver route evidence via ccb8 --diagnose extended output
if ($collectBackendRoute) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'collecting backend resolver route evidence' -PercentComplete 85
    New-Item -ItemType Directory -Force -Path $backendRouteDir | Out-Null
    $doctorOutputDir = $null
    if (-not [string]::IsNullOrWhiteSpace($doctorOutputExtractDir) -and (Test-Path -LiteralPath $doctorOutputExtractDir)) {
        $doctorOutputDir = $doctorOutputExtractDir
    } elseif (Test-Path -LiteralPath (Join-Path $resolvedOut 'doctor-output')) {
        $doctorOutputDir = Join-Path $resolvedOut 'doctor-output'
    }
    if ($null -ne $doctorOutputDir -and (Test-Path -LiteralPath $doctorOutputDir)) {
        # Collect ccbd startup log fragments for backend selection.
        Get-ChildItem -LiteralPath $doctorOutputDir -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like '*.log' -or $_.Name -like '*.json' -or $_.Name -like '*.txt' } |
            ForEach-Object {
                try {
                    $dest = Join-Path $backendRouteDir $_.Name
                    Copy-Item -LiteralPath $_.FullName -Destination $dest -Force
                } catch {}
            }
    }
    # Extract backend-selection relevant lines from diagnose output.
    $diagnoseResult = $commands | Where-Object { $_.name -eq 'ccb8-diagnose' } | Select-Object -First 1
    $backendRouteSummary = @()
    $backendRouteSummary += '# Backend resolver route evidence'
    $backendRouteSummary += ''
    if ($diagnoseResult -and (Test-Path -LiteralPath $diagnoseResult.stdout_ref)) {
        $diagnoseText = [System.IO.File]::ReadAllText($diagnoseResult.stdout_ref)
        $backendRouteSummary += '## Diagnose output (backend-relevant lines)'
        $backendRouteSummary += ''
        foreach ($line in ($diagnoseText -split "`n")) {
            if ($line -match 'herdr|backend|Herdr|HERDR|CCB_HERDR') {
                $backendRouteSummary += ('- ' + $line.Trim())
            }
        }
    }
    # Collect env vars relevant to backend selection.
    $backendRouteSummary += ''
    $backendRouteSummary += '## Herdr environment variables'
    foreach ($entry in Get-ChildItem Env:) {
        if ($entry.Name -like 'HERDR*' -or $entry.Name -like 'CCB_HERDR*') {
            $backendRouteSummary += ('- ' + $entry.Name + '=' + (Redact-Text -Text $entry.Value))
        }
    }
    $backendRouteSummary += ''
    $backendRouteSummary += '## Platform gate (from host context)'
    $backendRouteSummary += ('- os_platform: ' + $hostContext.os_version)
    $backendRouteSummary += ('- powershell_version: ' + $hostContext.powershell_version)
    $backendRouteSummary += ('- machine_name: ' + $hostContext.machine_name)

    Write-Utf8NoBom -Path (Join-Path $backendRouteDir 'backend-route-summary.md') -Content (($backendRouteSummary -join [Environment]::NewLine) + [Environment]::NewLine)
}

# Dimension 4: Herdr v0.8.0 capability probe
# Collect version, API surface, plugin state, and session-reporting format
# to assess integration readiness vs the C2 federation architecture.
if (Test-SpikeDimensionEnabled -Dimension 'herdr-v0.8-probe' -EnabledDimensions $enabledDimensions) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'probing Herdr v0.8 capabilities' -PercentComplete 87
    $v08Dir = Join-Path $resolvedOut 'herdr-v0.8-probe'
    New-Item -ItemType Directory -Force -Path $v08Dir | Out-Null

    # 1: Exact version string
    $commands += Invoke-CapturedCommand -Name 'herdr-v0.8-version' -Command @($resolvedHerdr, '--version') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 15

    # 2: Full API help / usage to discover new endpoints
    $commands += Invoke-CapturedCommand -Name 'herdr-v0.8-api-help' -Command @($resolvedHerdr, 'api', '--help') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 15

    # 3: Server status with full JSON — compare format against v0.7.5
    $commands += Invoke-CapturedCommand -Name 'herdr-v0.8-status-server' -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'status', 'server', '--json') -Session $effectiveHerdrSession) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20

    # 4: Plugin list (if available in v0.8)
    $commands += Invoke-CapturedCommand -Name 'herdr-v0.8-plugin-list' -Command @($resolvedHerdr, 'plugin', 'list', '--json') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 15

    # 5: Help top-level — discover any new subcommands
    $commands += Invoke-CapturedCommand -Name 'herdr-v0.8-help' -Command @($resolvedHerdr, '--help') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 15

    # 6: Session list to probe lifecycle reporting format (no `session info` in v0.8)
    $commands += Invoke-CapturedCommand -Name 'herdr-v0.8-session-list' -Command @($resolvedHerdr, 'session', 'list', '--json') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 15

    # 7: Status (non-server) for agent detection changes
    $commands += Invoke-CapturedCommand -Name 'herdr-v0.8-status' -Command @($resolvedHerdr, 'status', '--json') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 15

    # Build v0.8 probe summary markdown
    $v08Summary = @()
    $v08Summary += '# Herdr v0.8.0 Capability Probe'
    $v08Summary += ''
    $v08Summary += '## Probe commands executed'
    $v08Summary += ''
    foreach ($cmd in @($commands | Where-Object { $_.name -like 'herdr-v0.8-*' })) {
        $v08Summary += ('- `' + $cmd.name + '`: exit=' + $cmd.exit_code + ', elapsed=' + $cmd.elapsed_ms + 'ms')
    }
    $v08Summary += ''
    $v08Summary += '## Integration Readiness Assessment'
    $v08Summary += ''
    $v08Summary += '| Capability | v0.7.5 Status | v0.8.0 Probe Result | C2 Impact |'
    $v08Summary += '|---|---|---|---|'
    $v08Summary += '| Session reporting format | `herdr status server --json` | see `herdr-v0.8-status-server.stdout.txt` | CCB→Herdr evidence path |'
    $v08Summary += '| Plugin system | CLI-wrapped only | see `herdr-v0.8-plugin-list` | B-lite feasibility |'
    $v08Summary += '| API surface | `api snapshot`, `api workspace` | see `herdr-v0.8-api-help.stdout.txt` | C2 pane lifecycle |'
    $v08Summary += '| Lifecycle reporting | Kimi/Qoder/Cursor simplified | see `herdr-v0.8-status.stdout.txt` | C2 integration pattern |'
    $v08Summary += '| Session list/attach | `session list`/`attach`/`stop`/`delete` | see `herdr-v0.8-session-list.stdout.txt` | C2 session lifecycle |'
    $v08Summary += '| License | unknown | check `herdr-v0.8-version.stdout.txt` | Apache-2.0 confirmed? |'
    $v08Summary += ''
    $v08Summary += '## Raw evidence'
    $v08Summary += ''
    $v08Summary += 'Full command outputs under `raw-command-refs/herdr-v0.8-*`.'

    Write-Utf8NoBom -Path (Join-Path $v08Dir 'herdr-v0.8-probe-summary.md') -Content (($v08Summary -join [Environment]::NewLine) + [Environment]::NewLine)
}

# --- Dimension: provider-logs (NEW 2026-08-07) ---
# Capture agent stdout/stderr logs to verify provider CLI output reaches the pane.
if (Test-SpikeDimensionEnabled -Dimension 'provider-logs' -EnabledDimensions $enabledDimensions) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'collecting provider logs' -PercentComplete 89
    $logsDir = Join-Path $resolvedOut 'provider-logs'
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

    # Determine agent names from ping-all output
    $agentNames = @()
    if ($pingAllText -match 'agent_name') {
        $agentNames = @([regex]::Matches($pingAllText, "agent_name[''']?\s*:\s*[''']?(\S+?)[''']?[\s,}]") | ForEach-Object { $_.Groups[1].Value })
    }

    foreach ($agentName in $agentNames) {
        if ([string]::IsNullOrWhiteSpace($agentName)) { continue }
        # ccb logs <agent>
        $logResult = Invoke-CapturedCommand `
            -Name ('ccb8-logs-' + ($agentName -replace '[^a-zA-Z0-9_-]', '-')) `
            -Command @($resolvedCcb8, 'logs', $agentName, '--tail', '50') `
            -WorkingDirectory $resolvedProject `
            -RawDir $rawDir `
            -TimeoutSeconds 20
        $commands += $logResult
    }
    # Also capture ccbd daemon log (keeper/ccbd stderr)
    if ($runtimeStateRoot) {
        $ccbdLogDir = Join-Path $runtimeStateRoot 'ccbd'
        if (Test-Path -LiteralPath $ccbdLogDir) {
            foreach ($logFile in @('ccbd.stderr.log', 'keeper.stderr.log')) {
                $src = Join-Path $ccbdLogDir $logFile
                if (Test-Path -LiteralPath $src) {
                    try { Copy-Item -LiteralPath $src -Destination (Join-Path $logsDir $logFile) -Force } catch {}
                }
            }
        }
    }
}

# --- Dimension: ccb-lifecycle (NEW 2026-08-07) ---
# Execute kill/restart cycle to verify Herdr pane lifecycle operations.
if (Test-SpikeDimensionEnabled -Dimension 'ccb-lifecycle' -EnabledDimensions $enabledDimensions) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'testing CCB kill/restart lifecycle' -PercentComplete 91
    $lifecycleDir = Join-Path $resolvedOut 'lifecycle-evidence'
    New-Item -ItemType Directory -Force -Path $lifecycleDir | Out-Null

    # Step 1: ccb kill (stop agents, keep ccbd)
    $killResult = Invoke-CapturedCommand `
        -Name 'ccb8-kill' `
        -Command @($resolvedCcb8, 'kill') `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir `
        -TimeoutSeconds 30
    $commands += $killResult

    Start-Sleep -Seconds 2

    # Step 2: Post-kill ping to verify agents stopped
    $commands += Invoke-CapturedCommand `
        -Name 'ccb8-ping-after-kill' `
        -Command @($resolvedCcb8, 'ping', 'all') `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir `
        -TimeoutSeconds 20

    # Step 3: Post-kill herdr snapshot to verify panes cleaned
    $commands += Invoke-CapturedCommand `
        -Name 'herdr-snapshot-after-kill' `
        -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'api', 'snapshot') -Session $effectiveHerdrSession) `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir `
        -TimeoutSeconds 20

    # Step 4: ccb restart
    Start-Sleep -Seconds 2
    $restartResult = Invoke-DetachedCommand `
        -Name 'ccb8-restart' `
        -Command @($resolvedCcb8) `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir
    $commands += $restartResult
    Start-Sleep -Seconds $PostStartWaitSeconds

    # Step 5: Post-restart ping — poll until daemon finishes startup (restart
    # spawns a new keeper/ccbd; a single ping right after is usually too early).
    # Attempts are not recorded in $commands so failed probes do not inflate
    # command_failure_count; only the canonical result is kept.
    $restartPingResult = $null
    for ($restartAttempt = 1; $restartAttempt -le 3; $restartAttempt++) {
        $restartPingResult = Invoke-CapturedCommand `
            -Name ('ccb8-ping-after-restart-attempt-' + $restartAttempt) `
            -Command @($resolvedCcb8, 'ping', 'all') `
            -WorkingDirectory $resolvedProject `
            -RawDir $rawDir `
            -TimeoutSeconds 30
        if ($restartAttempt -lt 3 -and [int] $restartPingResult.exit_code -ne 0) {
            Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status ('ping-after-restart retry ' + $restartAttempt + '/3') -PercentComplete 92
            Start-Sleep -Seconds 5
        } else {
            break
        }
    }
    if ($null -ne $restartPingResult) {
        # Keep the last (best) ping as canonical evidence for classification.
        $commands += [ordered] @{
            name = 'ccb8-ping-after-restart'
            exit_code = [int] $restartPingResult.exit_code
            timed_out = [bool] $restartPingResult.timed_out
            elapsed_ms = [int] $restartPingResult.elapsed_ms
            ref = $restartPingResult.ref
            stdout_ref = $restartPingResult.stdout_ref
            stderr_ref = $restartPingResult.stderr_ref
            stdout_tail = $restartPingResult.stdout_tail
            stderr_tail = $restartPingResult.stderr_tail
        }
    }

    # Step 6: Post-restart herdr snapshot
    $commands += Invoke-CapturedCommand `
        -Name 'herdr-snapshot-after-restart' `
        -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'api', 'snapshot') -Session $effectiveHerdrSession) `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir `
        -TimeoutSeconds 20

    # Write lifecycle summary
    $lifecycleSummary = @()
    $lifecycleSummary += '# CCB Kill/Restart Lifecycle Evidence'
    $lifecycleSummary += ''
    $lifecycleSummary += ('- kill_exit_code: ' + [int] $killResult.exit_code)
    $lifecycleSummary += ('- restart_status: ' + [string] $restartResult.status)
    $lifecycleSummary += ('- restart_pid: ' + [int] $restartResult.process_id)
    Write-Utf8NoBom -Path (Join-Path $lifecycleDir 'lifecycle-summary.md') -Content (($lifecycleSummary -join [Environment]::NewLine) + [Environment]::NewLine)
}

# --- Dimension: herdr-config-probe (NEW 2026-08-07) ---
# Capture Herdr config.toml to determine auto_restore mode and other settings.
if (Test-SpikeDimensionEnabled -Dimension 'herdr-config-probe' -EnabledDimensions $enabledDimensions) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'probing Herdr configuration' -PercentComplete 92
    $configDir = Join-Path $resolvedOut 'herdr-config'
    New-Item -ItemType Directory -Force -Path $configDir | Out-Null

    $herdrConfigCandidates = @(
        Join-Path $env:APPDATA 'herdr\config.toml'
        Join-Path $env:LOCALAPPDATA 'herdr\config.toml'
        Join-Path $env:USERPROFILE '.herdr\config.toml'
    )
    $foundConfig = $null
    foreach ($candidate in $herdrConfigCandidates) {
        if (Test-Path -LiteralPath $candidate) {
            $foundConfig = $candidate
            break
        }
    }
    if ($foundConfig) {
        try { Copy-Item -LiteralPath $foundConfig -Destination (Join-Path $configDir 'config.toml') -Force } catch {}
    }
    # Also capture active session config
    if ($ccbHerdrSession) {
        $sessionConfigDir = Join-Path $env:APPDATA ('herdr\sessions\' + $ccbHerdrSession)
        if (Test-Path -LiteralPath $sessionConfigDir) {
            foreach ($f in @('session.json', 'config.toml')) {
                $src = Join-Path $sessionConfigDir $f
                if (Test-Path -LiteralPath $src) {
                    try { Copy-Item -LiteralPath $src -Destination (Join-Path $configDir $f) -Force } catch {}
                }
            }
        }
    }

    # Parse resume_agents_on_restore setting from [session] section.
    # Herdr's actual config key is "resume_agents_on_restore" (not "auto_restore").
    $autoRestoreMode = 'unknown'
    if ($foundConfig) {
        $configText = [System.IO.File]::ReadAllText($foundConfig)
        if ($configText -match 'resume_agents_on_restore\s*=\s*(true|false)') {
            $autoRestoreMode = if ($Matches[1] -eq 'false') { 'disabled' } else { 'enabled' }
        }
    }
    $configProbe = [ordered] @{
        config_found = ($null -ne $foundConfig)
        config_path = [string] $foundConfig
        auto_restore_mode = $autoRestoreMode
    }
    Write-Utf8NoBom -Path (Join-Path $configDir 'config-probe.json') -Content (($configProbe | ConvertTo-Json -Depth 10) + [Environment]::NewLine)
}

# --- Dimension: provider-session-files (NEW 2026-08-07) ---
# Capture provider session state files to verify runtime bindings.
if (Test-SpikeDimensionEnabled -Dimension 'provider-session-files' -EnabledDimensions $enabledDimensions) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'collecting provider session files' -PercentComplete 93
    $sessionDir = Join-Path $resolvedOut 'provider-sessions'
    New-Item -ItemType Directory -Force -Path $sessionDir | Out-Null

    $ccbDir = Join-Path $resolvedProject '.ccb'
    if (Test-Path -LiteralPath $ccbDir) {
        Get-ChildItem -LiteralPath $ccbDir -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like '.*-agent*-session' -or $_.Name -like '.*-session*' } |
            ForEach-Object {
                try { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $sessionDir $_.Name) -Force } catch {}
            }
    }
    # Also capture agent runtime state from ccbd
    if ($runtimeStateRoot) {
        $agentsDir = Join-Path $runtimeStateRoot 'agents'
        if (Test-Path -LiteralPath $agentsDir) {
            Get-ChildItem -LiteralPath $agentsDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                $agentSessionDir = Join-Path $sessionDir ('agent-' + $_.Name)
                New-Item -ItemType Directory -Force -Path $agentSessionDir | Out-Null
                Get-ChildItem -LiteralPath $_.FullName -File -ErrorAction SilentlyContinue | ForEach-Object {
                    try { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $agentSessionDir $_.Name) -Force } catch {}
                }
            }
        }
    }
}

# --- Dimension: ccb-ask-smoke (NEW 2026-08-07) ---
# Smoke test ask workflow — sends a trivial prompt and captures response.
# Will likely fail without API credentials but captures the full error path.
if (Test-SpikeDimensionEnabled -Dimension 'ccb-ask-smoke' -EnabledDimensions $enabledDimensions) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'running ask smoke test' -PercentComplete 94
    $askDir = Join-Path $resolvedOut 'ask-smoke'
    New-Item -ItemType Directory -Force -Path $askDir | Out-Null

    # Determine an agent name from ping output. Read ping-all output here
    # independently: $pingAllText is defined later (for classification), so
    # depending on it here always yields the hard-coded fallback.
    $targetAgent = $null
    $pingAllSmokeCmd = @($commands | Where-Object { $_.name -eq 'ccb8-ping-all' -or $_.name -like 'ccb8-ping-all-attempt-*' } | Select-Object -Last 1)
    if ($pingAllSmokeCmd.Count -gt 0 -and (Test-Path -LiteralPath $pingAllSmokeCmd[0].stdout_ref)) {
        $pingAllSmokeText = [System.IO.File]::ReadAllText($pingAllSmokeCmd[0].stdout_ref)
        if ($pingAllSmokeText -match "agent_name[''']?\s*:\s*[''']?(\S+?)[''']?[\s,}]") {
            $targetAgent = $Matches[1]
        }
    }
    if ([string]::IsNullOrWhiteSpace($targetAgent)) {
        $targetAgent = 'agent1'
    }

    $askResult = Invoke-CapturedCommand `
        -Name 'ccb8-ask-smoke' `
        -Command @($resolvedCcb8, 'ask', $targetAgent, 'echo ok') `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir `
        -TimeoutSeconds 30
    $commands += $askResult

    # Post-ask ping to verify agent state unchanged
    Start-Sleep -Seconds 3
    $pingAfterAskResult = Invoke-CapturedCommand `
        -Name 'ccb8-ping-after-ask' `
        -Command @($resolvedCcb8, 'ping', $targetAgent) `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir `
        -TimeoutSeconds 20
    $commands += $pingAfterAskResult

    # Write ask-smoke evidence
    $askEvidence = [ordered] @{
        target_agent = $targetAgent
        ask_exit_code = [int] $askResult.exit_code
        ask_stdout_tail = [string] $askResult.stdout_tail
        ask_stderr_tail = [string] $askResult.stderr_tail
        ping_after_ask_exit_code = [int] $pingAfterAskResult.exit_code
    }
    Write-Utf8NoBom -Path (Join-Path $askDir 'ask-smoke-evidence.json') -Content (($askEvidence | ConvertTo-Json -Depth 10) + [Environment]::NewLine)
}

# --- Dimension: ccb-reload-smoke (NEW 2026-08-07) ---
# Smoke test reload to verify config hot-reload works in Herdr context.
if (Test-SpikeDimensionEnabled -Dimension 'ccb-reload-smoke' -EnabledDimensions $enabledDimensions) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'running reload smoke test' -PercentComplete 95
    $reloadDir = Join-Path $resolvedOut 'reload-smoke'
    New-Item -ItemType Directory -Force -Path $reloadDir | Out-Null

    $reloadResult = Invoke-CapturedCommand `
        -Name 'ccb8-reload' `
        -Command @($resolvedCcb8, 'reload') `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir `
        -TimeoutSeconds 30
    $commands += $reloadResult

    Start-Sleep -Seconds 3
    $pingAfterReloadResult = Invoke-CapturedCommand `
        -Name 'ccb8-ping-after-reload' `
        -Command @($resolvedCcb8, 'ping', 'all') `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir `
        -TimeoutSeconds 20
    $commands += $pingAfterReloadResult

    # Write reload-smoke evidence
    $reloadEvidence = [ordered] @{
        reload_exit_code = [int] $reloadResult.exit_code
        reload_stdout_tail = [string] $reloadResult.stdout_tail
        reload_stderr_tail = [string] $reloadResult.stderr_tail
        ping_after_reload_exit_code = [int] $pingAfterReloadResult.exit_code
    }
    Write-Utf8NoBom -Path (Join-Path $reloadDir 'reload-smoke-evidence.json') -Content (($reloadEvidence | ConvertTo-Json -Depth 10) + [Environment]::NewLine)
}

if ($null -ne $sampler) {
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
}
Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'writing evidence artifacts' -PercentComplete 98

$startCommand = @(
    $commands |
        Where-Object { $_.name -eq 'ccb8-start-project' -or $_.name -eq 'ccb8-start-new-context' -or $_.name -eq 'ccb8-herdr-open' } |
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
$isPartialDimensionRun = $enabledDimensions.Count -lt $script:SpikeDimensions.Count
$classificationScope = if ($isPartialDimensionRun) { 'partial' } else { 'full' }
$failedCommands = @(Get-FailedCommandSummaries -Commands $commands)
$classification = 'needs-review'
if (-not $hasHerdrUiEvidence -and -not $AllowNonHerdrUi) {
    $classification = 'blocked-not-herdr-ui'
} elseif ($startCommand.Count -eq 0 -or $startStatus -eq 'launch_failed' -or ([string]::IsNullOrWhiteSpace($startStatus) -and $startExitCode -ne 0)) {
    $classification = 'ccb8-start-failed'
} elseif (-not $pingAllSuccess) {
    # ping-all (agent-level, with retry) is the authoritative mount signal.
    # Fall back to ping-ccbd (daemon-level) only when ping-all failed,
    # to distinguish daemon-not-mounted from specific-provider-failure.
    if ($pingText -notmatch 'mount_state:\s*mounted') {
        $classification = 'ccb-mounted-not-proven'
    } else {
        $classification = 'ccb-provider-ping-not-proven'
    }
} elseif (-not $layoutMaterializationComplete) {
    $classification = 'mounted-but-layout-materialization-missing'
} elseif ([string]::IsNullOrWhiteSpace($ObservedHerdrAgentsPanelText)) {
    $classification = 'mounted-but-panel-observation-missing'
} else {
    $classification = 'mounted-with-herdr-panel-observation'
}
if ($isPartialDimensionRun) {
    $classification = if ($failedCommands.Count -gt 0) { 'partial-dimension-failed' } else { 'partial-dimension-complete' }
}
$processSamplesRef = if ($collectProcessSamples) { $samplerPath } else { $null }
$startupStateFilesRef = if (Test-SpikeDimensionEnabled -Dimension 'startup-state-files' -EnabledDimensions $enabledDimensions) { Join-Path $resolvedOut 'startup-state-files-manifest.txt' } else { $null }
$paneEvidenceRef = if ($collectPaneVerification) { Join-Path $paneEvidenceDir 'pane-verification.md' } else { $null }
$backendRouteEvidenceRef = if ($collectBackendRoute) { Join-Path $backendRouteDir 'backend-route-summary.md' } else { $null }
$herdrV08ProbeRef = if (Test-SpikeDimensionEnabled -Dimension 'herdr-v0.8-probe' -EnabledDimensions $enabledDimensions) { Join-Path (Join-Path $resolvedOut 'herdr-v0.8-probe') 'herdr-v0.8-probe-summary.md' } else { $null }
$skippedDimensions = @($script:SpikeDimensions | Where-Object { $executedDimensions -notcontains $_ })

$summary = [ordered] @{
    schema_version = 1
    spike = 'herdr-ui-integration-spike'
    run_id = $runId
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    classification = $classification
    classification_scope = $classificationScope
    output_dir = $resolvedOut
    collection_dimensions_ref = Join-Path $resolvedOut 'collection-dimensions.json'
    enabled_dimensions = @($enabledDimensions)
    executed_dimensions = @($executedDimensions)
    skipped_dimensions = @($skippedDimensions)
    partial_dimension_run = $isPartialDimensionRun
    pane_capture_lines = $PaneCaptureLines
    command_failure_count = $failedCommands.Count
    failed_commands = @($failedCommands)
    process_samples_ref = $processSamplesRef
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
    startup_state_files_dir = $stateFilesDir
    startup_state_files_ref = $startupStateFilesRef
    pane_evidence_ref = $paneEvidenceRef
    backend_route_evidence_ref = $backendRouteEvidenceRef
    herdr_v0_8_probe_ref = $herdrV08ProbeRef
    provider_logs_ref = if (Test-SpikeDimensionEnabled -Dimension 'provider-logs' -EnabledDimensions $enabledDimensions) { Join-Path $resolvedOut 'provider-logs' } else { $null }
    lifecycle_evidence_ref = if (Test-SpikeDimensionEnabled -Dimension 'ccb-lifecycle' -EnabledDimensions $enabledDimensions) { Join-Path $resolvedOut 'lifecycle-evidence' } else { $null }
    herdr_config_probe_ref = if (Test-SpikeDimensionEnabled -Dimension 'herdr-config-probe' -EnabledDimensions $enabledDimensions) { Join-Path $resolvedOut 'herdr-config' } else { $null }
    provider_sessions_ref = if (Test-SpikeDimensionEnabled -Dimension 'provider-session-files' -EnabledDimensions $enabledDimensions) { Join-Path $resolvedOut 'provider-sessions' } else { $null }
    ask_smoke_ref = if (Test-SpikeDimensionEnabled -Dimension 'ccb-ask-smoke' -EnabledDimensions $enabledDimensions) { Join-Path $resolvedOut 'ask-smoke' } else { $null }
    reload_smoke_ref = if (Test-SpikeDimensionEnabled -Dimension 'ccb-reload-smoke' -EnabledDimensions $enabledDimensions) { Join-Path $resolvedOut 'reload-smoke' } else { $null }
    herdr_open_ref = if ($collectHerdrOpen) { $script:herdrOpenEvidenceRef } else { $null }
    notes = @(
        'Herdr agents panel text is manual observation unless Herdr exposes it through CLI metadata.',
        'Herdr agent detection is diagnostics evidence only; CCB provider completion/runtime authority remains CCB-owned.',
        'This spike does not claim Native Windows supported.',
        '2026-08-07: Added provider-logs, ccb-lifecycle, herdr-config-probe, provider-session-files, ccb-ask-smoke, ccb-reload-smoke dimensions.',
        'Provider pane content IS rendered in Herdr (confirmed by pane read); user-visible CLI absence is viewport/rendering issue, not launch failure.'
    )
}
Write-Utf8NoBom -Path (Join-Path $resolvedOut 'summary.json') -Content (($summary | ConvertTo-Json -Depth 40) + [Environment]::NewLine)

$report = @()
$report += '# Herdr UI integration spike report'
$report += ''
$report += ('- run_id: ' + $runId)
$report += ('- classification: ' + $classification)
$report += ('- classification_scope: ' + $classificationScope)
$report += ('- output_dir: ' + $resolvedOut)
$report += ('- enabled_dimensions: ' + (@($enabledDimensions) -join ', '))
$report += ('- executed_dimensions: ' + (@($executedDimensions) -join ', '))
$report += ('- skipped_dimensions: ' + (@($skippedDimensions) -join ', '))
$report += ('- pane_capture_lines: ' + $PaneCaptureLines)
$report += ('- command_failure_count: ' + $failedCommands.Count)
$report += ('- process_samples: ' + $(if ($null -ne $processSamplesRef) { $processSamplesRef } else { 'not collected' }))
$report += ('- observed_windows_flash: ' + [bool] $ObservedWindowsFlash)
$report += ('- observed_herdr_agents_panel_text: ' + $ObservedHerdrAgentsPanelText)
$report += ''
$report += '## Commands'
$report += ''
foreach ($command in $commands) {
    $report += ('- ' + $command.name + ': exit=' + $command.exit_code + ' timed_out=' + $command.timed_out + ' ref=' + $command.ref)
}
if ($failedCommands.Count -gt 0) {
    $report += ''
    $report += '## Failed Commands'
    $report += ''
    foreach ($command in $failedCommands) {
        $report += ('- ' + $command.name + ': exit=' + $command.exit_code + ' timed_out=' + $command.timed_out + ' ref=' + $command.ref)
    }
}
$report += ''
$report += '## Interpretation'
$report += ''
$report += '- If `process-samples.jsonl` contains short-lived `cmd.exe` / `powershell.exe` children but CCB ping is not mounted, classify as startup wrapper failure.'
$report += '- If CCB ping is mounted but `ccb8 layout status --json` lacks expected provider pane ids, classify as layout/materialization projection gap.'
$report += '- Herdr CLI `workspace list` / `pane list` are intentionally not used here because Herdr 0.7.5 exposes machine-readable workspace/pane state through `api snapshot` instead.'
if ($herdrV08ProbeRef) {
    $report += '- Herdr v0.8.0 capability probe evidence: ' + $herdrV08ProbeRef
}
$report += '- If Herdr agents panel shows `claude` while CCB runtime state is failed, treat Herdr agent detection as diagnostics-only evidence, not completion authority.'
$report += '- **NEW (2026-08-07):** Provider pane content IS rendered (confirmed by pane read captures). CLI not visible to user = Herdr viewport/rendering issue, not CCB launch failure.'
$report += '- **NEW (2026-08-07):** Check `herdr-config/config-probe.json` for `auto_restore_mode` — required for support tier gating.'
$report += '- **NEW (2026-08-07):** Kill/restart lifecycle evidence under `lifecycle-evidence/` verifies pane cleanup and agent recovery.'
$report += '- **NEW (2026-08-07):** Provider logs under `provider-logs/` capture agent stdout for diagnostics.'
$report += ''
Write-Utf8NoBom -Path (Join-Path $resolvedOut 'report.md') -Content (($report -join [Environment]::NewLine) + [Environment]::NewLine)

$summaryRef = Join-Path $resolvedOut 'summary.json'
Write-Progress -Id 1 -Activity 'Herdr UI integration spike' -Completed
Write-Host (('wrote {0} classification={1}' -f $summaryRef, $classification))

} finally {
    $cleanupProject = if (Test-Path variable:resolvedProject) { $resolvedProject } else { '' }
    $cleanupRepo = if (Test-Path variable:resolvedRepo) { $resolvedRepo } else { '' }
    $cleanupCcb8 = if (Test-Path variable:resolvedCcb8) { $resolvedCcb8 } else { '' }
    $cleanupHerdrUi = if (Test-Path variable:script:insideHerdrUi) { $script:insideHerdrUi } else { $false }
    $cleanupStartPid = if (Test-Path variable:script:ccbStartPid) { $script:ccbStartPid } else { 0 }
    try {
        Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'cleaning up residual CCB/herdr processes' -PercentComplete 100
        Stop-SpikeResidualProcesses -ProjectRoot $cleanupProject -RepoRoot $cleanupRepo -Ccb8Path $cleanupCcb8 -TrackedStartPid $cleanupStartPid -InsideHerdrUi $cleanupHerdrUi
    } catch {
        Write-Warning ('spike cleanup error: ' + $_.Exception.Message)
    } finally {
        Write-Progress -Id 1 -Activity 'Herdr UI integration spike' -Completed
    }
}
