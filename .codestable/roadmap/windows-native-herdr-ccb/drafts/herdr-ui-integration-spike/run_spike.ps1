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
    if ((Test-Path -LiteralPath $cmdPath) -and (Test-Utf8Bom -Path $cmdPath)) {
        $errors += ('wrapper cmd has UTF-8 BOM: ' + $cmdPath)
    }
    if ((Test-Path -LiteralPath $ps1Path) -and (Test-Utf8Bom -Path $ps1Path)) {
        $errors += ('wrapper ps1 has UTF-8 BOM: ' + $ps1Path)
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
        New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
        $cmdPath = Join-Path $tempDir 'ccb8.cmd'
        $ps1Path = Join-Path $tempDir 'ccb8.ps1'
        Write-Utf8NoBom -Path $cmdPath -Content "@echo off`r`n"
        Write-Utf8NoBom -Path $ps1Path -Content "param()`r`n"
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

if ($SelfTest) {
    Invoke-SelfTest
    exit 0
}

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

$hostContext = Get-HostContext -ProjectRoot $resolvedProject -RepoRoot $resolvedRepo -Ccb8Path $resolvedCcb8 -HerdrExe $resolvedHerdr -HerdrSession $effectiveHerdrSession
Write-Utf8NoBom -Path (Join-Path $resolvedOut 'host-context.json') -Content (($hostContext | ConvertTo-Json -Depth 30) + [Environment]::NewLine)
New-ManualObservationTemplate -Path (Join-Path $resolvedOut 'manual-observation.md') -RunId $runId -ObservedPanel $ObservedHerdrAgentsPanelText -ObservedFlash ([bool] $ObservedWindowsFlash)

$commands = @()
Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'collecting Herdr baseline' -PercentComplete 5
$commands += Invoke-CapturedCommand -Name 'herdr-version' -Command @($resolvedHerdr, '--version') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 15
$commands += Invoke-CapturedCommand -Name 'herdr-status-server-before' -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'status', 'server', '--json') -Session $effectiveHerdrSession) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
$commands += Invoke-CapturedCommand -Name 'herdr-api-snapshot-before' -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'api', 'snapshot') -Session $effectiveHerdrSession) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
$commands += Invoke-WrapperFileCheck -Name 'ccb8-wrapper-file-check' -Ccb8Path $resolvedCcb8 -RawDir $rawDir
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

$commands += Invoke-CapturedCommand -Name 'herdr-status-server-after' -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'status', 'server', '--json') -Session $effectiveHerdrSession) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
$commands += Invoke-CapturedCommand -Name 'herdr-api-snapshot-after' -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'api', 'snapshot') -Session $effectiveHerdrSession) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 20
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
# Keep the last (best) ping-all as ccb8-ping-all for classification
if ($pingAllAttempt -gt 1) {
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
$commands += Invoke-CapturedCommand -Name 'ccb8-ps' -Command @($resolvedCcb8, 'ps') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
$commands += Invoke-CapturedCommand -Name 'ccb8-doctor-ps' -Command @($resolvedCcb8, 'doctor', 'ps') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
$commands += Invoke-CapturedCommand -Name 'ccb8-layout-status' -Command @($resolvedCcb8, 'layout', 'status', '--json') -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 30
$commands += Invoke-CapturedCommand -Name 'ccb8-doctor-output' -Command @($resolvedCcb8, 'doctor', '--output', (Join-Path $resolvedOut 'doctor-output')) -WorkingDirectory $resolvedProject -RawDir $rawDir -TimeoutSeconds 60

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
if ($ccbHerdrSession -and $ccbHerdrSession -ne $effectiveHerdrSession) {
    Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status ('collecting CCB namespace snapshot via session=' + $ccbHerdrSession) -PercentComplete 76
    $commands += Invoke-CapturedCommand `
        -Name 'herdr-api-snapshot-ccb-namespace' `
        -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'api', 'snapshot') -Session $ccbHerdrSession) `
        -WorkingDirectory $resolvedProject `
        -RawDir $rawDir `
        -TimeoutSeconds 20
}

# --- expanded collection dimensions (analysis 2026-08-05) ---

# Dimension 1: CCB startup state files snapshot
Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'collecting CCB startup state files' -PercentComplete 72
$stateFilesDir = Join-Path $resolvedOut 'startup-state-files'
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
$ccbdDir = Join-Path $ccbDir 'ccbd'
$ccbdStateFiles = @('lease.json', 'keeper.json', 'lifecycle.json')
foreach ($fileName in $ccbdStateFiles) {
    $src = Join-Path $ccbdDir $fileName
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

# Also copy startup-report.json from doctor output if available
$startupReport = Join-Path $resolvedOut 'doctor-output/startup-report.json'
if (-not (Test-Path -LiteralPath $startupReport)) {
    $startupReport = Join-Path $resolvedOut 'doctor-output/ccbd/startup-report.json'
}
if (Test-Path -LiteralPath $startupReport) {
    try {
        Copy-Item -LiteralPath $startupReport -Destination (Join-Path $stateFilesDir 'startup-report.json') -Force
        Append-Utf8NoBom -Path (Join-Path $resolvedOut 'startup-state-files-manifest.txt') -Content "copied startup-report.json`r`n"
    } catch {
        Append-Utf8NoBom -Path (Join-Path $resolvedOut 'startup-state-files-manifest.txt') -Content ("failed to copy startup-report.json : $_`r`n")
    }
}

# Dimension 2: Pane-level materialization verification via Herdr api snapshot pane tokens
Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'validating pane materialization' -PercentComplete 78
$paneEvidenceDir = Join-Path $resolvedOut 'pane-evidence'
New-Item -ItemType Directory -Force -Path $paneEvidenceDir | Out-Null
# Prefer CCB namespace snapshot if available, fall back to wrapper session snapshot
$preferredSnapshotName = if ($ccbHerdrSession -and $ccbHerdrSession -ne $effectiveHerdrSession) { 'herdr-api-snapshot-ccb-namespace' } else { 'herdr-api-snapshot-after' }
$snapshotResult = $commands | Where-Object { $_.name -eq $preferredSnapshotName } | Select-Object -First 1
if ($null -eq $snapshotResult) {
    $snapshotResult = $commands | Where-Object { $_.name -eq 'herdr-api-snapshot-after' } | Select-Object -First 1
}
$paneVerificationReport = @()
$paneVerificationReport += '# Pane materialization verification'
$paneVerificationReport += ('- snapshot_source: ' + $preferredSnapshotName)
$paneVerificationReport += ''
if ($snapshotResult -and (Test-Path -LiteralPath $snapshotResult.stdout_ref)) {
    try {
        $snapshotText = [System.IO.File]::ReadAllText($snapshotResult.stdout_ref, [System.Text.Encoding]::UTF8)
        # api snapshot is nested: {"result":{"snapshot":{...}}}
        $snapshotPayload = $null
        $snapshot = $null
        try {
            $snapshotPayload = $snapshotText | ConvertFrom-Json -ErrorAction Stop
        } catch {
            $paneVerificationReport += ('- snapshot_parse_warning: direct ConvertFrom-Json failed, trying manual extraction')
            $snapshotPayload = $null
        }
        if ($null -eq $snapshotPayload) {
            $paneVerificationReport += ('- snapshot_available: true (raw text saved, unable to parse JSON)')
    } else {
        $paneVerificationReport += ('- snapshot_available: true')
        # Try result.snapshot first, then snapshot
        if ($null -ne $snapshotPayload.result -and $null -ne $snapshotPayload.result.snapshot) {
            $snapshot = $snapshotPayload.result.snapshot
        } else {
            $snapshot = $snapshotPayload.snapshot
        }
    }
        if ($null -ne $snapshot) {
            $panes = $snapshot.panes
            $workspaces = $snapshot.workspaces
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

            # Try capturing pane content for materialized panes (non-destructive read)
            $paneVerificationReport += ''
            $paneVerificationReport += '## Pane content capture'
            $paneVerificationReport += ''
            foreach ($pane in @($panes)) {
                $paneId = [string] $pane.pane_id
                if ([string]::IsNullOrWhiteSpace($paneId)) { continue }
                $captureResult = Invoke-CapturedCommand `
                    -Name ('ccb-herdr-pane-capture-' + ($paneId -replace '[^a-zA-Z0-9_-]', '-')) `
                    -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'pane', 'read', $paneId, '--lines', '3', '--format', 'text') -Session $effectiveHerdrSession) `
                    -WorkingDirectory $resolvedProject `
                    -RawDir $rawDir `
                    -TimeoutSeconds 10
                $captureText = if (Test-Path -LiteralPath $captureResult.stdout_ref) {
                    [System.IO.File]::ReadAllText($captureResult.stdout_ref)
                } else { '' }
                $paneVerificationReport += ('- pane_id=' + $paneId + ' exit_code=' + [int] $captureResult.exit_code + ' tail=' + ($captureText.Substring(0, [Math]::Min($captureText.Length, 80))))
            }
        } else {
            $paneVerificationReport += '- snapshot_available: false (no snapshot object in response)'
        }
    } catch {
        $paneVerificationReport += ('- snapshot_parse_error: ' + $_.Exception.Message)
    }
} else {
    $paneVerificationReport += '- snapshot_available: false (no herdr-api-snapshot-after output)'
}
Write-Utf8NoBom -Path (Join-Path $paneEvidenceDir 'pane-verification.md') -Content (($paneVerificationReport -join [Environment]::NewLine) + [Environment]::NewLine)

# Dimension 3: Backend resolver route evidence via ccb8 --diagnose extended output
Set-SpikeProgress -Activity 'Herdr UI integration spike' -Status 'collecting backend resolver route evidence' -PercentComplete 85
$backendRouteDir = Join-Path $resolvedOut 'backend-route-evidence'
New-Item -ItemType Directory -Force -Path $backendRouteDir | Out-Null
$doctorOutputDir = Join-Path $resolvedOut 'doctor-output'
if (Test-Path -LiteralPath $doctorOutputDir) {
    # Collect ccbd startup log fragments for backend selection
    Get-ChildItem -LiteralPath $doctorOutputDir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like '*.log' -or $_.Name -like '*.json' -or $_.Name -like '*.txt' } |
        ForEach-Object {
            try {
                $dest = Join-Path $backendRouteDir $_.Name
                Copy-Item -LiteralPath $_.FullName -Destination $dest -Force
            } catch {}
        }
}
# Extract backend-selection relevant lines from diagnose output
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
# Collect env vars relevant to backend selection
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
    startup_state_files_dir = $stateFilesDir
    startup_state_files_ref = Join-Path $resolvedOut 'startup-state-files-manifest.txt'
    pane_evidence_ref = Join-Path $paneEvidenceDir 'pane-verification.md'
    backend_route_evidence_ref = Join-Path $backendRouteDir 'backend-route-summary.md'
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
