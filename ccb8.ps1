param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $CcbArgs
)

$ErrorActionPreference = 'Stop'
# ValueFromRemainingArguments may produce a scalar string when only one
# argument is passed.  Force array semantics so that @splatting transmits
# the argument as a single value rather than character-by-character.
$CcbArgs = @($CcbArgs)
# CRITICAL: on PowerShell 5.1, ValueFromRemainingArguments with [string[]]
# type constraint may receive a single string argument as a [char[]]
# (character array) rather than [string[]] (string array).  When ANY
# element is Char, re-join the whole array back into a single string
# argument.  (Single-char and multi-char arguments are both affected.)
if ($CcbArgs.Count -gt 0 -and $CcbArgs[0].GetType().Name -eq 'Char') {
    $CcbArgs = @([string]::new($CcbArgs))
}

$script:utf8Strict = New-Object System.Text.UTF8Encoding($false, $true)
$script:utf8NoBom = New-Object System.Text.UTF8Encoding($false)
try { $OutputEncoding = $script:utf8NoBom } catch {}
try { [Console]::OutputEncoding = $script:utf8NoBom } catch {}
try { [Console]::InputEncoding = $script:utf8NoBom } catch {}

function Write-Stderr {
    param([string] $Message)
    [Console]::Error.WriteLine($Message)
}

function Write-Utf8NoBom {
    param(
        [string] $Path,
        [string] $Content
    )
    [System.IO.File]::WriteAllText($Path, $Content, $script:utf8NoBom)
}

function Read-Utf8Text {
    param([string] $Path)
    try {
        $bytes = [System.IO.File]::ReadAllBytes($Path)
        $text = $script:utf8Strict.GetString($bytes)
    } catch [System.Text.DecoderFallbackException] {
        throw ('invalid UTF-8 JSON file: ' + $Path)
    }
    if ($text.Length -gt 0 -and $text[0] -eq [char] 0xFEFF) {
        return $text.Substring(1)
    }
    return $text
}

function Read-Utf8Json {
    param([string] $Path)
    return (Read-Utf8Text -Path $Path) | ConvertFrom-Json -ErrorAction Stop
}

function Test-Utf8Bom {
    param([string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }
    try {
        $stream = [System.IO.File]::OpenRead($Path)
        try {
            if ($stream.Length -lt 3) {
                return $false
            }
            $bytes = New-Object byte[] 3
            [void] $stream.Read($bytes, 0, 3)
            return $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
        } finally {
            $stream.Close()
        }
    } catch {
        return $false
    }
}

function Resolve-ExistingPath {
    param(
        [string] $Description,
        [string[]] $Candidates,
        [scriptblock] $Validate
    )
    foreach ($candidate in @($Candidates)) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }
        try {
            $resolved = (Get-Item -LiteralPath $candidate -ErrorAction Stop).FullName
        } catch {
            continue
        }
        if (& $Validate $resolved) {
            return $resolved
        }
    }
    throw ($Description + ' not found')
}

function Resolve-CcbSourceRoot {
    return Resolve-ExistingPath `
        -Description 'CCB source checkout' `
        -Candidates @('E:\GITHUB~1\TACHIK~1\claude_code_bridge', $env:CCB_SOURCE_ROOT, $PSScriptRoot) `
        -Validate { param([string] $Path) Test-Path -LiteralPath (Join-Path $Path 'ccb.py') }
}

function Install-HerdrAgentStateHook {
    $sourcePath = Join-Path $env:CCB_SOURCE_ROOT 'lib\terminal_runtime\herdr_backend_runtime\ccb\herdr-agent-state.ps1'
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        Write-Warning ('Herdr agent-state hook source not found: ' + $sourcePath)
        return $false
    }
    $userProfile = [string] $env:CCB_SOURCE_HOME
    if ([string]::IsNullOrWhiteSpace($userProfile)) {
        $userProfile = [Environment]::GetFolderPath('UserProfile')
    }
    if ([string]::IsNullOrWhiteSpace($userProfile)) {
        Write-Warning 'Cannot resolve the real user profile for Herdr hook installation.'
        return $false
    }
    $targetDir = Join-Path $userProfile '.ccb\hooks'
    $targetPath = Join-Path $targetDir 'herdr-agent-state.ps1'
    try {
        if (-not (Test-Path -LiteralPath $targetDir -PathType Container)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        $sourceText = [System.IO.File]::ReadAllText($sourcePath, $script:utf8Strict)
        $targetText = if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
            [System.IO.File]::ReadAllText($targetPath, $script:utf8Strict)
        } else {
            $null
        }
        if ($sourceText -ne $targetText) {
            [System.IO.File]::WriteAllText($targetPath, $sourceText, $script:utf8NoBom)
        }
        Write-Host ('ccb8: Herdr agent-state hook ready: ' + $targetPath)
        return $true
    } catch {
        Write-Warning ('failed to install Herdr agent-state hook: ' + $_.Exception.Message)
        return $false
    }
}

function Resolve-HerdrCapabilityReport {
    param([string] $SourceRoot)
    return Resolve-ExistingPath `
        -Description 'Herdr capability report' `
        -Candidates @(
            $env:CCB_HERDR_CAPABILITY_REPORT,
            (Join-Path $SourceRoot '.codestable\features\2026-07-31-herdr-backend-contract-spike\evidence\herdr-contract-spike-evidence.json')
        ) `
        -Validate { param([string] $Path) Test-Path -LiteralPath $Path -PathType Leaf }
}

function Invoke-WrapperSelfTest {
    $samplePath = 'E:\GitHub' + [char] 0x5F00 + [char] 0x6E90 + [char] 0x9879 + [char] 0x76EE + '\TachiKuma'
    $tempPath = Join-Path ([System.IO.Path]::GetTempPath()) ('ccb8-wrapper-self-test-' + [Guid]::NewGuid().ToString('N') + '.json')
    $utf16Path = Join-Path ([System.IO.Path]::GetTempPath()) ('ccb8-wrapper-self-test-utf16-' + [Guid]::NewGuid().ToString('N') + '.json')
    try {
        $payload = @{ path = $samplePath } | ConvertTo-Json -Compress
        Write-Utf8NoBom -Path $tempPath -Content $payload
        if (Test-Utf8Bom -Path $tempPath) {
            throw 'self-test JSON was written with UTF-8 BOM'
        }
        $json = Read-Utf8Json -Path $tempPath
        if ([string] $json.path -ne $samplePath) {
            throw 'self-test UTF-8 JSON roundtrip failed'
        }
        [System.IO.File]::WriteAllText($utf16Path, $payload, [System.Text.Encoding]::Unicode)
        $invalidUtf8Rejected = $false
        try {
            [void] (Read-Utf8Json -Path $utf16Path)
        } catch {
            $invalidUtf8Rejected = $true
        }
        if (-not $invalidUtf8Rejected) {
            throw 'self-test UTF-16 JSON was not rejected'
        }
        if ($CcbArgs.Count -gt 1 -and $CcbArgs[1] -ieq '--full-env') {
            $sourceRoot = Resolve-CcbSourceRoot
            [void] (Resolve-HerdrCapabilityReport -SourceRoot $sourceRoot)
        }
        Write-Host 'wrapper_self_test: passed'
    } finally {
        Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $utf16Path -Force -ErrorAction SilentlyContinue
    }
    exit 0
}

function Show-ConfigUiLauncherHint {
    Write-Host 'ccb8: config ui: run .\ccb8.cmd config ui'
    Write-Host 'ccb8: config ui: after release run ccb config ui'
    Write-Host 'ccb8: config ui: the command prints http://127.0.0.1:PORT/?token=... for copy'
}

function Set-DefaultEnv {
    param(
        [string] $Name,
        [string] $Value
    )
    if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($Name, 'Process'))) {
        [Environment]::SetEnvironmentVariable($Name, $Value, 'Process')
    }
}

function Repair-SourceDevRuntimeRootRef {
    $refPath = Join-Path (Join-Path $env:CCB_PROJECT_ROOT '.ccb') 'runtime-root-ref.json'
    if (-not (Test-Path -LiteralPath $refPath)) {
        return
    }
    try {
        $json = Read-Utf8Json -Path $refPath
    } catch {
        throw ('failed to read runtime root ref: ' + $refPath)
    }
    $projectId = [string] $json.project_id
    if ([string]::IsNullOrWhiteSpace($projectId)) {
        throw ('runtime root ref is missing project_id: ' + $refPath)
    }
    $currentRoot = [string] $json.runtime_state_root
    $legacyRoot = Join-Path $env:CCB_LEGACY_RUNTIME_STATE_HOME $projectId
    $expectedRoot = Join-Path $env:CCB_RUNTIME_STATE_HOME $projectId
    if ($currentRoot -eq $expectedRoot) {
        return
    }
    if ($currentRoot -ne $legacyRoot -and $currentRoot -like '*\.ccb\ccbd*') {
        throw ('runtime root ref points at installed CCB state; refusing to update: ' + $refPath)
    }
    if ($currentRoot -ne $legacyRoot -and $currentRoot -notlike '*\.ccb-source-dev\state\runtime-state*') {
        throw ('runtime root ref points at an unexpected location; refusing to update: ' + $currentRoot)
    }
    $json.runtime_state_root = $expectedRoot
    $json.created_at = (Get-Date).ToUniversalTime().ToString('o')
    Write-Utf8NoBom -Path $refPath -Content (($json | ConvertTo-Json -Depth 20) + [Environment]::NewLine)
}

function Get-JsonPid {
    param(
        [object] $Json,
        [string] $Key
    )
    if ($null -eq $Json) {
        return $null
    }
    $property = $Json.PSObject.Properties | Where-Object { $_.Name -eq $Key } | Select-Object -First 1
    if ($null -eq $property -or $null -eq $property.Value) {
        return $null
    }
    try {
        $pidValue = [int] $property.Value
    } catch {
        return $null
    }
    if ($pidValue -le 0) {
        return $null
    }
    return $pidValue
}

function Test-SourceDevCcbdCommandLine {
    param(
        [string] $CommandLine,
        [string] $ProjectRoot
    )
    $cmdNorm = ([string] $CommandLine).Replace('/', '\')
    $scriptMatch =
        $cmdNorm.IndexOf('\ccbd\main.py', [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
        $cmdNorm.IndexOf('\ccbd\keeper_main.py', [StringComparison]::OrdinalIgnoreCase) -ge 0
    if (-not $scriptMatch) {
        return $false
    }
    return $cmdNorm.IndexOf($ProjectRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0
}

function Read-ProtectedInstalledPids {
    $protected = @{}
    $protectedDir = Join-Path $env:CCB_PROJECT_ROOT '.ccb\ccbd'
    foreach ($name in @('lease.json', 'keeper.json', 'lifecycle.json')) {
        $path = Join-Path $protectedDir $name
        if (-not (Test-Path -LiteralPath $path)) {
            continue
        }
        try {
            $json = Read-Utf8Json -Path $path
        } catch {
            throw ('failed to read installed CCB protection state file: ' + $path)
        }
        foreach ($key in @('keeper_pid', 'owner_pid', 'ccbd_pid')) {
            $pidValue = Get-JsonPid -Json $json -Key $key
            if ($null -ne $pidValue) {
                $protected[$pidValue] = $true
            }
        }
    }
    return $protected
}

function Get-SourceDevProjectId {
    foreach ($path in @(
        (Join-Path (Join-Path $env:CCB_PROJECT_ROOT '.ccb') 'runtime-root-ref.json'),
        (Join-Path (Join-Path $env:CCB_PROJECT_ROOT '.ccb') 'project.identity.json')
    )) {
        if (-not (Test-Path -LiteralPath $path)) {
            continue
        }
        try {
            $json = Read-Utf8Json -Path $path
            $projectId = [string] $json.project_id
            if (-not [string]::IsNullOrWhiteSpace($projectId)) {
                return $projectId
            }
        } catch {
            continue
        }
    }
    return $null
}

function Get-SourceDevStateFiles {
    $stateFileNames = @('lease.json', 'keeper.json', 'lifecycle.json')
    $projectId = Get-SourceDevProjectId
    if ([string]::IsNullOrWhiteSpace($projectId)) {
        return @()
    }
    $runtimeRoots = @($env:CCB_RUNTIME_STATE_HOME, $env:CCB_LEGACY_RUNTIME_STATE_HOME) |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    $files = @()
    $seen = @{}
    foreach ($runtimeRoot in $runtimeRoots) {
        $ccbdDir = Join-Path (Join-Path $runtimeRoot $projectId) 'ccbd'
        try {
            $key = [System.IO.Path]::GetFullPath($ccbdDir).TrimEnd('\').ToLowerInvariant()
        } catch {
            $key = $ccbdDir.ToLowerInvariant()
        }
        if ($seen.ContainsKey($key)) {
            continue
        }
        $seen[$key] = $true
        if (-not (Test-Path -LiteralPath $ccbdDir)) {
            continue
        }
        $files += @(
            Get-ChildItem -LiteralPath $ccbdDir -File -ErrorAction SilentlyContinue |
                Where-Object { $stateFileNames -contains $_.Name -and $_.FullName -like '*\ccbd\*' }
        )
    }
    return @($files)
}

function Get-SourceDevPidTargets {
    param([object[]] $StateFiles)
    $items = @()
    foreach ($file in $StateFiles) {
        try {
            $json = Read-Utf8Json -Path $file.FullName
        } catch {
            continue
        }
        foreach ($entry in @(@('keeper_pid', 0), @('owner_pid', 1), @('ccbd_pid', 1))) {
            $pidValue = Get-JsonPid -Json $json -Key $entry[0]
            if ($null -ne $pidValue) {
                $items += [pscustomobject] @{
                    PidValue = $pidValue
                    Priority = [int] $entry[1]
                    Source = $file.FullName
                }
            }
        }
    }

    $seen = @{}
    return @(
        $items |
            Sort-Object Priority, PidValue |
            Where-Object {
                if ($seen.ContainsKey($_.PidValue)) {
                    return $false
                }
                $seen[$_.PidValue] = $true
                return $true
            }
    )
}

function Stop-SourceDevRuntimePids {
    $stateFiles = Get-SourceDevStateFiles
    if ($stateFiles.Count -eq 0) {
        return
    }

    $project = $env:CCB_PROJECT_ROOT.TrimEnd('\').Replace('/', '\')
    $protected = Read-ProtectedInstalledPids
    $targets = Get-SourceDevPidTargets -StateFiles $stateFiles

    foreach ($target in $targets) {
        $pidValue = $target.PidValue
        if ($protected.ContainsKey($pidValue)) {
            Write-Host ('Skipping installed CCB pid=' + $pidValue)
            continue
        }

        $process = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $pidValue) -ErrorAction SilentlyContinue
        if ($null -eq $process) {
            continue
        }
        if (-not (Test-SourceDevCcbdCommandLine -CommandLine $process.CommandLine -ProjectRoot $project)) {
            continue
        }

        Write-Host ('Stopping source-dev CCB pid=' + $pidValue)
        Stop-Process -Id $pidValue -Force -ErrorAction Stop
    }

    Start-Sleep -Milliseconds 250

    foreach ($target in $targets) {
        $pidValue = $target.PidValue
        if ($protected.ContainsKey($pidValue)) {
            continue
        }
        $process = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $pidValue) -ErrorAction SilentlyContinue
        if ($null -eq $process) {
            continue
        }
        if (Test-SourceDevCcbdCommandLine -CommandLine $process.CommandLine -ProjectRoot $project) {
            throw ('source-dev CCB pid still alive after targeted cleanup: ' + $pidValue)
        }
    }

    Reset-SourceDevStateFiles -StateFiles $stateFiles
}

function Reset-SourceDevStateFiles {
    param([object[]] $StateFiles)
    $now = (Get-Date).ToUniversalTime().ToString('o')
    foreach ($file in $StateFiles) {
        # Delete + recreate to force ACL refresh on D:\.c8\rs\ files
        # (WriteAllText preserves existing ACL even if it lacks DELETE for os.replace)
        $path = $file.FullName
        $resetContent = $null
        try {
            $json = Read-Utf8Json -Path $path
            switch ($file.Name) {
                'lease.json' {
                    $json.mount_state = 'unmounted'
                    $json.last_heartbeat_at = $now
                }
                'lifecycle.json' {
                    $json.desired_state = 'running'
                    $json.phase = 'unmounted'
                    $json.phase_started_at = $now
                    $json.startup_stage = $null
                    $json.last_progress_at = $now
                    $json.startup_deadline_at = $null
                    $json.owner_pid = $null
                    $json.owner_daemon_instance_id = $null
                    $json.socket_inode = $null
                    $json.control_plane_endpoint = $null
                    $json.last_failure_reason = $null
                    $json.shutdown_intent = $null
                }
                'keeper.json' {
                    $json.state = 'stopped'
                    $json.restart_count = 0
                    $json.last_check_at = $now
                    $json.last_restart_at = $now
                    $json.last_failure_reason = $null
                }
                default {
                    continue
                }
            }
            $resetContent = ($json | ConvertTo-Json -Depth 20) + [Environment]::NewLine
        } catch {
            Write-Warning ('failed to read source-dev state file for reset: ' + $path)
            continue
        }
        if ($null -eq $resetContent) {
            continue
        }
        try {
            Remove-Item -LiteralPath $path -Force -ErrorAction Stop
        } catch {
            Write-Warning ('failed to delete source-dev state file before ACL refresh: ' + $path)
        }
        try {
            Write-Utf8NoBom -Path $path -Content $resetContent
        } catch {
            Write-Warning ('failed to recreate source-dev state file after ACL refresh: ' + $path)
        }
    }
}

function Reset-ProjectCcbdStateFiles {
    $ccbdDir = Join-Path $env:CCB_PROJECT_ROOT '.ccb\ccbd'
    if (-not (Test-Path -LiteralPath $ccbdDir)) {
        return
    }
    $now = (Get-Date).ToUniversalTime().ToString('o')
    foreach ($fileName in @('keeper.json')) {
        $path = Join-Path $ccbdDir $fileName
        if (-not (Test-Path -LiteralPath $path)) {
            continue
        }
        try {
            $json = Read-Utf8Json -Path $path
            $json.state = 'stopped'
            $json.restart_count = 0
            $json.last_check_at = $now
            $json.last_restart_at = $now
            $json.last_failure_reason = $null
            Write-Utf8NoBom -Path $path -Content (($json | ConvertTo-Json -Depth 20) + [Environment]::NewLine)
        } catch {
            Write-Warning ('failed to reset project ccbd state file, attempting delete+recreate: ' + $path)
            try {
                Remove-Item -LiteralPath $path -Force -ErrorAction Stop
                $defaultState = [ordered] @{
                    schema_version = 2
                    record_type = 'ccbd_keeper'
                    state = 'stopped'
                    restart_count = 0
                    last_check_at = $now
                    last_restart_at = $now
                    last_failure_reason = $null
                }
                Write-Utf8NoBom -Path $path -Content (($defaultState | ConvertTo-Json -Depth 10) + [Environment]::NewLine)
            } catch {
                Write-Warning ('failed to recreate project ccbd state file: ' + $path)
            }
        }
    }
}

function Run-BoundedKillForce {
    $timeoutMs = 15000
    if (-not [string]::IsNullOrEmpty($env:CCB_PRESTART_KILL_TIMEOUT_MS)) {
        try {
            $timeoutMs = [int] $env:CCB_PRESTART_KILL_TIMEOUT_MS
        } catch {
            $timeoutMs = 15000
        }
    }

    try {
        $scriptPath = Join-Path $env:CCB_SOURCE_ROOT 'ccb.py'
        $argumentText = Join-WindowsProcessArguments -Arguments @($scriptPath, 'kill', '-f')
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $env:CCB_PYTHON
        $psi.Arguments = $argumentText
        $psi.WorkingDirectory = $env:CCB_PROJECT_ROOT
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $psi
        [void] $process.Start()
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($timeoutMs)) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            Write-Warning ('source-dev ccb kill -f timed out after ' + $timeoutMs + 'ms; continuing after targeted PID cleanup')
            return
        }
        try { $stdoutTask.Wait(5000) | Out-Null } catch {}
        try { $stderrTask.Wait(5000) | Out-Null } catch {}
        if ($process.ExitCode -ne 0) {
            Write-Stderr 'Warning: source-dev ccb kill -f did not complete cleanly; continuing after targeted PID cleanup.'
        }
    } catch {
        Write-Stderr ('Warning: source-dev ccb kill -f could not be started cleanly; continuing after targeted PID cleanup. ' + $_.Exception.Message)
    }
}

function Invoke-PrestartCleanup {
    $protected = Read-ProtectedInstalledPids
    Stop-SourceDevRuntimePids
    Run-BoundedKillForce
    Reset-ProjectCcbdStateFiles
    # Run-BoundedKillForce（ccb kill -f）可能把 lifecycle desired_state 置为 stopped
    # （shutdown_intent=stop_all）；在 start 前恢复 running 意图，避免 start 命令因
    # desired_state=stopped 拒绝拉起 ccbd 而报 lease_unmounted（2026-08-06 采集暴露）。
    Reset-SourceDevStateFiles -StateFiles (Get-SourceDevStateFiles)
    # Final sweep: after kill -f and state reset, verify no ccbd
    # processes are still alive for this project.  On Windows the
    # kill may race with a lingering process that will later collide
    # on lease.json / lifecycle.json atomic writes.
    # Reuse the same installed-PID protection that Stop-SourceDevRuntimePids
    # applies so that stale source-dev state pointing at installed CCB never
    # causes an accidental installed-daemon kill.
    $remaining = Get-SourceDevStateFiles
    $targets = Get-SourceDevPidTargets -StateFiles $remaining
    $project = $env:CCB_PROJECT_ROOT.TrimEnd('\').Replace('/', '\')
    foreach ($target in $targets) {
        if ($protected.ContainsKey($target.PidValue)) { continue }
        $proc = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $target.PidValue) -ErrorAction SilentlyContinue
        if ($null -eq $proc) { continue }
        if (-not (Test-SourceDevCcbdCommandLine -CommandLine $proc.CommandLine -ProjectRoot $project)) { continue }
        Write-Warning ('ccbd pid=' + $target.PidValue + ' still alive after prestart cleanup; forcing stop')
        Stop-Process -Id $target.PidValue -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
        $proc2 = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $target.PidValue) -ErrorAction SilentlyContinue
        if ($null -ne $proc2) {
            throw ('ccbd pid=' + $target.PidValue + ' could not be stopped after prestart cleanup')
        }
    }
}

function Test-ShouldPrestartKill {
    param([string[]] $CliArgs)
    if ($null -eq $CliArgs) {
        return $true
    }
    if ($CliArgs.Count -eq 0) {
        return $true
    }
    # Treat 'start' as an alias for bare start (no agent names / extra args)
    $first = if ($CliArgs[0] -ieq 'start') {
        if ($CliArgs.Count -eq 1) {
            return $true
        }
        $CliArgs[1]
    } else {
        $CliArgs[0]
    }
    return $first -ieq '-s' -or $first -ieq '--safe' -or $first -ieq '-n' -or $first -ieq '--new-context'
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

function Initialize-WrapperEnvironment {
    try {
        $sourceRoot = Resolve-CcbSourceRoot
    } catch {
        Write-Stderr $_.Exception.Message
        exit 1
    }
    $projectRoot = (Resolve-Path -LiteralPath $PSScriptRoot).ProviderPath
    $devRoot = Join-Path $projectRoot '.ccb-source-dev'
    $devBin = Join-Path $devRoot 'bin'
    $devHome = Join-Path $devRoot 'home'
    $devTmp = Join-Path $devRoot 'tmp'
    $devState = Join-Path $devRoot 'state'
    # 获取真实用户主目录（不受 HOME/USERPROFILE 覆盖影响），
    # 用于 CCB_SOURCE_HOME / CODEX_HOME 等"配置来源"变量，
    # 确保 provider 能从 C:\Users\<account> 继承 settings、auth、MCP 等配置。
    $realUserProfile = [Environment]::GetFolderPath('UserProfile')
    try {
        $runtimeStateHome = if ([string]::IsNullOrWhiteSpace($env:CCB_RUNTIME_STATE_HOME)) { 'D:\.c8\rs' } else { [System.IO.Path]::GetFullPath($env:CCB_RUNTIME_STATE_HOME) }
    } catch {
        Write-Stderr ('invalid CCB_RUNTIME_STATE_HOME: ' + $env:CCB_RUNTIME_STATE_HOME)
        exit 1
    }
    $legacyRuntimeStateHome = Join-Path $devState 'runtime-state'
    $python = if ([string]::IsNullOrWhiteSpace($env:CCB_PYTHON)) { $env:CCB_PYTHON_BIN } else { $env:CCB_PYTHON }
    if ([string]::IsNullOrWhiteSpace($python)) {
        $python = 'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe'
    }
    $herdrExe = if ([string]::IsNullOrWhiteSpace($env:CCB_HERDR_EXE)) { 'C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe' } else { $env:CCB_HERDR_EXE }
    try {
        $herdrCapabilityReport = Resolve-HerdrCapabilityReport -SourceRoot $sourceRoot
    } catch {
        Write-Warning $_.Exception.Message
        $herdrCapabilityReport = $null
    }

    if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot 'ccb.py'))) {
        Write-Stderr ('CCB source checkout not found: "' + $sourceRoot + '"')
        exit 1
    }
    if (-not (Test-Path -LiteralPath $python)) {
        $python = 'python'
    }

    foreach ($path in @($devBin, $devHome, $devTmp, $devState, $runtimeStateHome)) {
        if (-not (Test-Path -LiteralPath $path)) {
            New-Item -ItemType Directory -Path $path | Out-Null
        }
    }

    $env:CCB_SOURCE_ROOT = $sourceRoot
    $env:CCB_PROJECT_ROOT = $projectRoot
    $env:CCB_DEV_ROOT = $devRoot
    $env:CCB_DEV_BIN = $devBin
    $env:CCB_DEV_HOME = $devHome
    $env:CCB_DEV_TMP = $devTmp
    $env:CCB_DEV_STATE = $devState
    $env:CCB_PYTHON = $python
    $env:CCB_HERDR_EXE = $herdrExe
    $env:CCB_HERDR_SESSION = if ([string]::IsNullOrWhiteSpace($env:CCB_HERDR_SESSION)) { 'ccb-herdr-avaprintdesigner-source-dev' } else { $env:CCB_HERDR_SESSION }
    if ([string]::IsNullOrWhiteSpace($herdrCapabilityReport)) {
        Remove-Item Env:CCB_HERDR_CAPABILITY_REPORT -ErrorAction SilentlyContinue
    } else {
        $env:CCB_HERDR_CAPABILITY_REPORT = $herdrCapabilityReport
    }
    # 显式指定 Git Bash sh.exe 路径，确保 Herdr pane（PowerShell）中能通过
    # resolve_sh_executable() 正确定位 sh.exe 来执行 .sh 启动脚本。
    $gitShExe = $null
    foreach ($candidate in @(
        (Join-Path $env:ProgramFiles 'Git\bin\sh.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Git\bin\sh.exe'),
        'C:\Program Files\Git\bin\sh.exe'
    )) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $gitShExe = $candidate
            break
        }
    }
    if ($gitShExe) {
        $env:CCB_SH_EXECUTABLE = $gitShExe
    }
    $env:CCB_SOURCE_ALLOWED_ROOTS = $projectRoot
    $env:CCB_TEST_ROOTS = $projectRoot
    $env:CCB_SKIP_STARTUP_UPDATE_CHECK = '1'
    $env:CCB_RUNTIME_STATE_HOME = $runtimeStateHome
    $env:CCB_LEGACY_RUNTIME_STATE_HOME = $legacyRuntimeStateHome
    $env:CCB_SOURCE_HOME = $realUserProfile
    $env:HOME = $devHome
    $env:USERPROFILE = $devHome
    $env:XDG_CONFIG_HOME = Join-Path $devState 'xdg-config'
    $env:XDG_CACHE_HOME = Join-Path $devState 'xdg-cache'
    $env:XDG_STATE_HOME = Join-Path $devState 'xdg-state'
    $env:TEMP = $devTmp
    $env:TMP = $devTmp
    $env:CODEX_HOME = Join-Path $realUserProfile '.codex'

    Set-DefaultEnv -Name 'CCB_CCBD_FAULTHANDLER' -Value '1'
    Set-DefaultEnv -Name 'PYTHONUNBUFFERED' -Value '1'
    Set-DefaultEnv -Name 'CCB_PRESTART_KILL_TIMEOUT_MS' -Value '15000'

    $env:PATH = $devBin + ';' + $env:PATH
    $env:PYTHONPATH = (Join-Path $sourceRoot 'lib') + ';' + $env:PYTHONPATH

    $shim = Join-Path $devBin 'ccb.cmd'
    $shimText = (
        '@echo off',
        'chcp 65001 > nul',
        ('set "PYTHONPATH=' + (Join-Path $sourceRoot 'lib') + ';%PYTHONPATH%"'),
        ('"' + $python + '" "' + (Join-Path $sourceRoot 'ccb.py') + '" %*')
    ) -join [Environment]::NewLine
    [System.IO.File]::WriteAllText($shim, $shimText, $script:utf8NoBom)

    Set-Location -LiteralPath $projectRoot
}

function Show-Diagnose {
    $sep = [string]::new('=', 56)
    $div = [string]::new('-', 56)

    Write-Host $sep
    Write-Host '  CCB Source-Dev Wrapper -- Diagnostic'
    Write-Host $sep
    Write-Host ''

    # -- Entry Points --
    Write-Host '-- Entry Points --'
    Write-Host ('  wrapper       ' + (Join-Path $PSScriptRoot 'ccb8.cmd'))
    Write-Host ('  powershell    ' + $PSCommandPath)
    Write-Host ('  source ccb    ' + (Join-Path $env:CCB_SOURCE_ROOT 'ccb.py'))
    Write-Host ('  shim          ' + (Join-Path $env:CCB_DEV_BIN 'ccb.cmd'))
    Write-Host ''

    # -- Paths --
    Write-Host '-- Paths --'
    Write-Host ('  project root  ' + $env:CCB_PROJECT_ROOT)
    Write-Host ('  dev root      ' + $env:CCB_DEV_ROOT)
    Write-Host ('  python        ' + $env:CCB_PYTHON)
    Write-Host ''

    # -- Runtime State --
    Write-Host '-- Runtime State --'
    Write-Host ('  RUNTIME       ' + $env:CCB_RUNTIME_STATE_HOME)
    $legacy = $env:CCB_LEGACY_RUNTIME_STATE_HOME
    if ($legacy) {
        Write-Host ('  legacy        ' + $legacy)
    }
    Write-Host ''

    # -- Isolation (source-dev vs installed) --
    Write-Host '-- Isolation --'
    $devHome = $env:CCB_DEV_HOME
    $isIsolated = ($env:HOME -eq $devHome)
    $mark = if ($isIsolated) { '[OK]' } else { '[!!]' }
    Write-Host ('  HOME          ' + $env:HOME + '   isolated ' + $mark)
    Write-Host ('  USERPROFILE   ' + $env:USERPROFILE)
    Write-Host ('  TEMP          ' + $env:TEMP)
    Write-Host ('  XDG_CONFIG    ' + $env:XDG_CONFIG_HOME)
    Write-Host ''

    # -- Herdr --
    Write-Host '-- Herdr --'
    $herdrOk = $env:CCB_HERDR_EXE -and (Test-Path -LiteralPath $env:CCB_HERDR_EXE)
    $herdrMark = if ($herdrOk) { '[OK]' } else { '[!!] not found' }
    Write-Host ('  exe           ' + $env:CCB_HERDR_EXE + '   ' + $herdrMark)
    Write-Host ('  session       ' + $env:CCB_HERDR_SESSION)
    $cap = $env:CCB_HERDR_CAPABILITY_REPORT
    if ($cap) {
        Write-Host ('  capability    ' + $cap)
    }
    Write-Host ''

    # -- Runtime Flags --
    Write-Host '-- Runtime Flags --'
    $flags = [ordered] @{
        CCB_NO_ATTACH              = $env:CCB_NO_ATTACH
        CCB_CCBD_FAULTHANDLER      = $env:CCB_CCBD_FAULTHANDLER
        PYTHONUNBUFFERED           = $env:PYTHONUNBUFFERED
        CCB_SKIP_STARTUP_UPDATE    = $env:CCB_SKIP_STARTUP_UPDATE_CHECK
        CCB_PRESTART_KILL_TIMEOUT  = $env:CCB_PRESTART_KILL_TIMEOUT_MS
    }
    foreach ($flag in $flags.GetEnumerator()) {
        $val = if ($flag.Value) { $flag.Value } else { '(unset)' }
        Write-Host ('  ' + $flag.Key.PadRight(28) + $val)
    }
    Write-Host ''

    # -- System --
    Write-Host '-- System --'
    Write-Host ('  powershell    ' + $PSVersionTable.PSVersion.ToString())
    Write-Host ('  encoding      ' + [System.Text.Encoding]::Default.WebName)
    $bomPs1 = Test-Utf8Bom -Path $PSCommandPath
    $bomMark = if ($bomPs1) { '[OK]' } else { '[!!] ps1 missing UTF-8 BOM (required for PS 5.1)' }
    Write-Host ('  ccb8 BOM      ' + $bomMark)
    Write-Host ''

    # -- CCB Version --
    Write-Host '-- CCB Version --'
    & $env:CCB_PYTHON (Join-Path $env:CCB_SOURCE_ROOT 'ccb.py') --print-version
    Write-Host ''

    Write-Host $div
    if ($null -ne $LASTEXITCODE) {
        exit $LASTEXITCODE
    }
    exit 0
}

function Get-WrapperLogRoots {
    $roots = @(
        (Join-Path (Join-Path $env:CCB_DEV_HOME '.ccb') 'logs'),
        (Join-Path $env:CCB_PROJECT_ROOT '.ccb\ccbd'),
        (Join-Path $env:CCB_PROJECT_ROOT '.ccb\agents')
    )
    $projectId = Get-SourceDevProjectId
    if (-not [string]::IsNullOrWhiteSpace($projectId)) {
        foreach ($runtimeRoot in @($env:CCB_RUNTIME_STATE_HOME, $env:CCB_LEGACY_RUNTIME_STATE_HOME)) {
            if ([string]::IsNullOrWhiteSpace($runtimeRoot)) {
                continue
            }
            $roots += (Join-Path (Join-Path $runtimeRoot $projectId) 'ccbd')
        }
    }

    $seen = @{}
    return @(
        foreach ($root in $roots) {
            if ([string]::IsNullOrWhiteSpace($root) -or -not (Test-Path -LiteralPath $root -PathType Container)) {
                continue
            }
            try {
                $key = [System.IO.Path]::GetFullPath($root).TrimEnd('\').ToLowerInvariant()
            } catch {
                $key = $root.TrimEnd('\').ToLowerInvariant()
            }
            if ($seen.ContainsKey($key)) {
                continue
            }
            $seen[$key] = $true
            $root
        }
    )
}

function Show-WrapperLogs {
    param(
        [string] $Filter,
        [int] $TailLines = 80,
        [int] $MaxFiles = 8
    )

    $roots = Get-WrapperLogRoots
    Write-Host ('log_roots: ' + (($roots | ForEach-Object { '"' + $_ + '"' }) -join '; '))
    if ($roots.Count -eq 0) {
        Write-Host 'log_status: no_log_roots'
        exit 0
    }

    $files = @(
        foreach ($root in $roots) {
            Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -like '*.log' -or $_.Name -like '*.out' -or $_.Name -like '*.err' }
        }
    )
    if (-not [string]::IsNullOrWhiteSpace($Filter)) {
        $files = @($files | Where-Object { $_.FullName.IndexOf($Filter, [StringComparison]::OrdinalIgnoreCase) -ge 0 })
    }
    $files = @($files | Sort-Object LastWriteTime -Descending | Select-Object -First $MaxFiles)
    if ($files.Count -eq 0) {
        Write-Host 'log_status: no_logs'
        exit 0
    }

    Write-Host ('log_status: ok')
    foreach ($file in $files) {
        Write-Host ('--- ' + $file.FullName + ' (' + $file.Length + ' bytes, ' + $file.LastWriteTime.ToString('s') + ') ---')
        if ($file.Length -eq 0) {
            Write-Host '<empty>'
            continue
        }
        try {
            Get-Content -LiteralPath $file.FullName -Tail $TailLines -ErrorAction Stop
        } catch {
            Write-Warning ('failed to read log: ' + $file.FullName)
        }
    }
    exit 0
}

if ($CcbArgs.Count -gt 0 -and $CcbArgs[0] -ieq '--wrapper-self-test') {
    Invoke-WrapperSelfTest
    exit 0
}

Initialize-WrapperEnvironment
try {
    Repair-SourceDevRuntimeRootRef
} catch {
    Write-Stderr $_.Exception.Message
    exit 1
}

# -- one-click mode: bare `ccb8.cmd` opens WezTerm + Herdr + CCB together -----
# PowerShell 5.1 may receive an empty string via ValueFromRemainingArguments
# when the .cmd wrapper passes %* with zero arguments.  Filter out empty/blank
# entries so that a bare invocation is reliably detected.
$CcbArgs = @($CcbArgs | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
$isOneClick = ($CcbArgs.Count -eq 0)
if ($isOneClick) {
    Write-Host 'ccb8: one-click mode — starting Herdr + CCB managed environment...'
    [void] (Install-HerdrAgentStateHook)
    # Use `herdr open --no-attach --wait-ready`: the documented working flow
    # from the WezTerm+Herdr+CCB joint startup milestone (2026-08-07).
    # This calls ensure_herdr_bootstrap_env (locate Herdr, ensure server —
    # auto-starting the ccbd-derived session server when needed — probe
    # capabilities, inject CCB_HERDR_* env), then starts agents in detached
    # daemon mode with Herdr backend.  `--wait-ready` makes Python block until
    # ccbd is mounted, replacing the lifecycle.json poll below.
    $CcbArgs = @('herdr', 'open', '--no-attach', '--wait-ready')
}

if ($CcbArgs.Count -gt 0 -and $CcbArgs[0] -ieq '--diagnose') {
    Show-Diagnose
}

if ($CcbArgs.Count -gt 0 -and $CcbArgs[0] -ieq '--log') {
    $filter = if ($CcbArgs.Count -gt 1) { $CcbArgs[1] } else { '' }
    Show-WrapperLogs -Filter $filter
}

if ($isOneClick -or (Test-ShouldPrestartKill -CliArgs $CcbArgs)) {
    try {
        Invoke-PrestartCleanup
    } catch {
        Write-Stderr $_.Exception.Message
        exit 1
    }
    # One-click mode: after killing old processes, wait for the keeper to
    # fully exit before herdr-open starts a fresh ccbd.  Otherwise the old
    # keeper restarts ccbd in non-Herdr mode before herdr-open can take over.
    if ($isOneClick) {
        $projectId = Get-SourceDevProjectId
        if ($projectId) {
            $keeperPath = Join-Path (Join-Path (Join-Path $env:CCB_RUNTIME_STATE_HOME $projectId) 'ccbd') 'keeper.json'
            $deadline = (Get-Date).AddSeconds(30)
            Write-Host 'ccb8: waiting for keeper to stop...'
            while ((Get-Date) -lt $deadline) {
                $stopped = $true
                if (Test-Path -LiteralPath $keeperPath) {
                    try {
                        $keeper = Get-Content -Raw -LiteralPath $keeperPath | ConvertFrom-Json
                        $rawState = $keeper.state
                        $state = if ($rawState) { [string] $rawState } else { '' }
                        if ($state -ne 'stopped') { $stopped = $false }
                    } catch { $stopped = $false }
                }
                if ($stopped) { break }
                Start-Sleep -Seconds 1
            }
            Write-Host 'ccb8: keeper stopped — starting fresh ccbd with Herdr backend'
        }
    }
}

# Translate 'start' alias to bare invocation (no args)
$finalArgs = if ($CcbArgs.Count -gt 0 -and $CcbArgs[0] -ieq 'start') {
    @($CcbArgs | Select-Object -Skip 1)
} else {
    $CcbArgs
}
# Force array semantics: when ValueFromRemainingArguments receives a single
# argument with [string[]] type constraint on PowerShell 5.1, the parameter
# may bind as a scalar string.  @() wrapping at param init (line 10) guards
# against char-by-char splatting, but the if/else assignment can collapse
# single-element arrays back to scalars.  Re-wrap right before the call.
$finalArgs = @($finalArgs)

# Herdr server startup and session probing are owned by Python
# (`ccb herdr open` -> ensure_herdr_bootstrap_env -> HerdrCliRequestAdapter).
# `handle_herdr_open --wait-ready` auto-starts the ccbd-derived session server
# and waits for ccbd mounted, so no PowerShell pre-start/probe is needed.

& $env:CCB_PYTHON (Join-Path $env:CCB_SOURCE_ROOT 'ccb.py') @finalArgs
$ccbExit = $LASTEXITCODE

if ($isOneClick -and $null -ne $ccbExit -and $ccbExit -ne 0) {
    Write-Stderr ('ccb8: ccb startup failed with exit code ' + $ccbExit + '; skipping Herdr UI launch.')
    exit $ccbExit
}

# One-click mode: after CCB starts, wait for ccbd to be ready, then
# launch Herdr UI attached to the CCB-managed session.
if ($isOneClick) {
    $herdrExe = $env:CCB_HERDR_EXE
    if ([string]::IsNullOrWhiteSpace($herdrExe) -or -not (Test-Path -LiteralPath $herdrExe)) {
        Write-Stderr 'ccb8: Herdr not found; cannot launch UI.'
    } else {
        # CCB derives the Herdr session name from project_slug
        # (e.g., ccb-avaprintdesigner-575a971f), independently of
        # CCB_HERDR_SESSION.  Match CCB's formula exactly so the
        # UI attaches to the same session CCB is using.
        $projectId = Get-SourceDevProjectId
        $projectName = (Split-Path -Leaf $env:CCB_PROJECT_ROOT).ToLowerInvariant() -replace '[^a-z0-9._-]+', '-'
        $projectName = $projectName.Trim('-')
        if ([string]::IsNullOrWhiteSpace($projectName)) { $projectName = 'project' }
        $shortId = if ($projectId) { $projectId.Substring(0, [Math]::Min(8, $projectId.Length)) } else { '00000000' }
        $ccbSession = "ccb-${projectName}-${shortId}"

        # ccbd readiness is owned by Python (`ccb herdr open --wait-ready`
        # blocks until lifecycle phase == mounted), so no lifecycle.json poll
        # is needed here.  Open the Herdr UI attached to the CCB-managed
        # session.  Herdr's agent dispatch requires the herdr process to run
        # in an interactive terminal; `wezterm cli spawn -- <prog>` runs the
        # program as that tab's foreground process (a real ConPTY), which
        # satisfies the same interactive-terminal requirement as the former
        # send-text keyboard injection.
        $weztermDir = $env:WEZTERM_EXECUTABLE_DIR
        if (-not $weztermDir) { $weztermDir = Split-Path $env:WEZTERM_EXECUTABLE -Parent -ErrorAction SilentlyContinue }
        $weztermCli = if ($weztermDir) { Join-Path $weztermDir 'wezterm.exe' } else { '' }
        if ($weztermCli -and (Test-Path -LiteralPath $weztermCli)) {
            Write-Host "ccb8: opening Herdr session in WezTerm..."
            # Structured attach: `herdr session attach <name>` as the tab's
            # program, replacing the old `spawn` + `send-text --no-paste`
            # keyboard injection.  Fall back to send-text if wezterm cannot
            # spawn the program directly.
            $paneId = (& $weztermCli cli spawn --cwd $env:CCB_PROJECT_ROOT -- $herdrExe session attach $ccbSession 2>&1).Trim()
            if (-not $paneId -or $paneId -match 'error') {
                Write-Host "ccb8: direct spawn failed; falling back to send-text..."
                $paneId = (& $weztermCli cli spawn --cwd $env:CCB_PROJECT_ROOT 2>&1).Trim()
                Start-Sleep -Seconds 2
                $herdrCmd = "& `"$herdrExe`" session attach $ccbSession`r`n"
                & $weztermCli cli send-text --pane-id $paneId --no-paste $herdrCmd
            }
            Write-Host "ccb8: agents starting — waiting 15s..."
            Show-ConfigUiLauncherHint
            Start-Sleep -Seconds 15
        } else {
            Write-Host "ccb8: WezTerm CLI not found, launching standalone..."
            Show-ConfigUiLauncherHint
            Start-Process -FilePath $herdrExe -ArgumentList '--session', $ccbSession
        }
    }
}

if ($null -ne $ccbExit) {
    exit $ccbExit
}
exit 0
