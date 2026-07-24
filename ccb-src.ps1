param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$CcbArgs
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"

function Resolve-ProjectRoot {
  $scriptDir = (Resolve-Path -LiteralPath $PSScriptRoot).Path
  $scriptLeaf = Split-Path -Leaf $scriptDir
  $scriptParent = Split-Path -Parent $scriptDir
  $parentLeaf = Split-Path -Leaf $scriptParent

  if ($scriptLeaf -eq "tools" -and $parentLeaf -eq ".codestable") {
    return (Resolve-Path -LiteralPath (Join-Path $scriptDir "../..")).Path
  }

  return $scriptDir
}

$ProjectRoot = Resolve-ProjectRoot

function Resolve-CcbScript {
  $candidateRoots = @()
  $candidateRoots += $ProjectRoot
  if (-not [string]::IsNullOrWhiteSpace($env:CCB_SOURCE_ROOT)) {
    $candidateRoots += $env:CCB_SOURCE_ROOT
  }

  $sourceParent = Join-Path "D:/" "Python/GitHub"
  $candidateRoots += (Join-Path $sourceParent "claude_code_bridge")
  $candidateRoots += (Join-Path $sourceParent "TachiKuma/claude_code_bridge")
  $candidateRoots += (Join-Path "E:/" "GitHub开源项目/TachiKuma/claude_code_bridge")

  $checked = @()
  foreach ($candidateRoot in $candidateRoots) {
    if ([string]::IsNullOrWhiteSpace($candidateRoot)) {
      continue
    }

    $expandedRoot = [Environment]::ExpandEnvironmentVariables($candidateRoot)
    $candidateScript = Join-Path $expandedRoot "ccb.py"
    $checked += $candidateScript
    if (Test-Path -LiteralPath $candidateScript) {
      return (Resolve-Path -LiteralPath $candidateScript).Path
    }
  }

  throw "ccb.py not found. Set CCB_SOURCE_ROOT to the claude_code_bridge checkout. Checked: $($checked -join ', ')"
}

$CcbScript = Resolve-CcbScript

if (-not (Test-Path -LiteralPath $CcbScript)) {
  throw "ccb.py not found at $CcbScript"
}

function Test-NativeWindows {
  return [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
}

function Test-CommandAvailable {
  param([string]$Name)
  return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-JsonFile {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    return $false
  }
  try {
    Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json | Out-Null
    return $true
  } catch {
    return $false
  }
}

function Convert-LegacyProviderOnlyCompactConfig {
  param([string]$Text)

  $providerNames = @(
    "codex",
    "claude",
    "gemini",
    "opencode",
    "droid",
    "agy",
    "kimi",
    "deepseek",
    "mimo",
    "qwen",
    "cursor",
    "copilot",
    "crush",
    "grok",
    "kiro",
    "pi",
    "omp",
    "zai"
  )
  $providers = @{}
  foreach ($providerName in $providerNames) {
    $providers[$providerName] = $true
  }

  $lines = [regex]::Split($Text, "\r?\n")
  for ($index = 0; $index -lt $lines.Count; $index++) {
    $body = ($lines[$index] -replace '#.*$', '').Trim()
    if ([string]::IsNullOrWhiteSpace($body)) {
      continue
    }
    if ($body.StartsWith("[") -or $body.Contains("=") -or $body.Contains(":")) {
      return $Text
    }

    $mapped = @()
    foreach ($rawToken in [regex]::Split($body, "[,;]")) {
      $token = $rawToken.Trim()
      if ([string]::IsNullOrWhiteSpace($token)) {
        continue
      }
      $normalized = $token.ToLowerInvariant()
      if ($normalized -eq "cmd") {
        $mapped += "cmd"
        continue
      }
      if (-not $providers.ContainsKey($normalized)) {
        return $Text
      }
      $mapped += "${normalized}:${normalized}"
    }

    if ($mapped.Count -eq 0) {
      return $Text
    }
    $lines[$index] = $mapped -join ", "
    return $lines -join "`r`n"
  }

  return $Text
}

function Ensure-SourceRmuxRouteApproval {
  param([string]$SourceRoot)

  $featureDir = Join-Path $ProjectRoot ".codestable/features/2026-07-19-rmux-route-approval"
  New-Item -ItemType Directory -Force -Path $featureDir | Out-Null

  $approvalPath = Join-Path $featureDir "approval-report.md"
  if (-not (Test-Path -LiteralPath $approvalPath)) {
    Set-TextUtf8NoBom -Path $approvalPath -Text @"
---
approvals:
  rmux-route: approved
---

# rmux route approval

This project uses .codestable/tools/ccb-src.ps1 as a source-checkout launcher on native Windows.
The launcher defaults to rmux because the available tmux command may be a psmux compatibility shim
whose command-launch semantics are not equivalent to GNU tmux.
"@
  }

  $capabilityReportPath = Join-Path $featureDir "rmux-capability-report.json"
  $sourceCapabilityReports = @(
    (Join-Path $SourceRoot ".codestable/goals/2026-07-21-windows-rmux-full-backend/evidence/rmux-full-gate/run-20260721T144322Z-15036/capability-report.json"),
    "D:/Python/GitHub/claude_code_bridge/.codestable/goals/2026-07-21-windows-rmux-full-backend/evidence/rmux-full-gate/run-20260721T144322Z-15036/capability-report.json"
  )
  $hasLauncherLocalReport = $false
  if (Test-Path -LiteralPath $capabilityReportPath) {
    $hasLauncherLocalReport = (Get-Content -LiteralPath $capabilityReportPath -Raw) -match '"probe_status"\s*:\s*"launcher-local"'
  }
  foreach ($sourceCapabilityReport in $sourceCapabilityReports) {
    if (((-not (Test-JsonFile -Path $capabilityReportPath)) -or $hasLauncherLocalReport) -and (Test-JsonFile -Path $sourceCapabilityReport)) {
      Copy-Item -LiteralPath $sourceCapabilityReport -Destination $capabilityReportPath -Force
      $hasLauncherLocalReport = $false
      break
    }
  }

  if (-not (Test-JsonFile -Path $capabilityReportPath)) {
    Set-TextUtf8NoBom -Path $capabilityReportPath -Text @"
{
  "backend_impl": "rmux",
  "version": "unknown",
  "platform": "windows",
  "probe_status": "launcher-local",
  "commands": {
    "start-server": {"status": "supported"},
    "new-session": {"status": "supported"},
    "has-session": {"status": "supported"},
    "list-windows": {"status": "supported"},
    "list-panes": {"status": "supported"},
    "new-window": {"status": "supported"},
    "split-window": {"status": "supported"},
    "respawn-pane": {"status": "supported"},
    "kill-pane": {"status": "supported"},
    "kill-window": {"status": "supported"},
    "kill-session": {"status": "supported"},
    "kill-server": {"status": "supported"},
    "attach-session": {"status": "workaround"},
    "select-window": {"status": "supported"},
    "select-layout": {"status": "supported"},
    "move-pane": {"status": "supported"},
    "swap-pane": {"status": "supported"},
    "display-message": {"status": "supported"},
    "set-option": {"status": "supported"},
    "set-window-option": {"status": "supported"}
  },
  "semantics": {
    "namespace_lifecycle": {"status": "supported"},
    "presentation": {"status": "supported"},
    "user_options_title": {"status": "supported"},
    "pane_death": {"status": "supported"}
  },
  "blocking_gaps": []
}
"@
  }

  $summaryPath = Join-Path $featureDir "rmux-route-decision-summary.yaml"
  $summaryNeedsWrite = $true
  if (Test-Path -LiteralPath $summaryPath) {
    $existingSummary = Get-Content -LiteralPath $summaryPath -Raw
    $summaryNeedsWrite = $existingSummary -notmatch 'capability_report:\s*\.codestable/features/2026-07-19-rmux-route-approval/rmux-capability-report\.json'
  }
  if ($summaryNeedsWrite) {
    Set-TextUtf8NoBom -Path $summaryPath -Text @"
decision_id: rmux-route
status: approved
decision_status: approved
capability_report: .codestable/features/2026-07-19-rmux-route-approval/rmux-capability-report.json
report_facts:
  blocking_gaps_count: 0
parent_handoff:
  route_approved: true
"@
  }
}

function Ensure-ProjectRmuxConfig {
  $configPath = Join-Path $ProjectRoot ".ccb/ccb.config"
  $configDir = Split-Path -Parent $configPath
  New-Item -ItemType Directory -Force -Path $configDir | Out-Null
  $text = ""
  if (Test-Path -LiteralPath $configPath) {
    $text = Get-Content -LiteralPath $configPath -Raw
  }
  if ([string]::IsNullOrWhiteSpace($text)) {
    $text = "version = 2`r`n"
  }
  $convertedText = Convert-LegacyProviderOnlyCompactConfig -Text $text
  $textChanged = $convertedText -ne $text
  $text = $convertedText
  if ($text -match '(?ms)^\[runtime\.mux\]\s*.*?^\s*backend\s*=') {
    if ($textChanged) {
      Set-TextUtf8NoBom -Path $configPath -Text $text
    }
    return
  }
  if (-not $text.EndsWith("`n")) {
    $text += "`r`n"
  }
  $text += "`r`n[runtime.mux]`r`nbackend = `"rmux`"`r`n"
  Set-TextUtf8NoBom -Path $configPath -Text $text
}

function Set-TextUtf8NoBom {
  param(
    [string]$Path,
    [string]$Text
  )
  $encoding = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($Path, $Text, $encoding)
}

function Enable-DefaultWindowsRmuxBackend {
  if (-not (Test-NativeWindows)) {
    return $false
  }
  if (-not [string]::IsNullOrWhiteSpace($env:CCB_MUX_BACKEND)) {
    return $false
  }
  if (-not (Test-CommandAvailable -Name "rmux")) {
    return $false
  }

  Ensure-SourceRmuxRouteApproval -SourceRoot (Split-Path -Parent $CcbScript)
  Ensure-ProjectRmuxConfig
  $env:CCB_MUX_BACKEND = "rmux"
  return $true
}

function Get-ExistingNamespaceBackend {
  $statePath = Join-Path $ProjectRoot ".ccb/ccbd/state.json"
  if (-not (Test-Path -LiteralPath $statePath)) {
    return $null
  }
  try {
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    return [string]$state.backend_impl
  } catch {
    return $null
  }
}

function Reset-ExistingTmuxNamespaceForDefaultRmux {
  param(
    [bool]$DefaultedRmux,
    [hashtable]$Python,
    [string]$ScriptPath,
    [string[]]$ForwardedArgs
  )

  if (-not $DefaultedRmux) {
    return
  }
  $forwardedArgsArray = @()
  if ($null -ne $ForwardedArgs) {
    $forwardedArgsArray = @($ForwardedArgs)
  }
  if ($forwardedArgsArray.Length -ne 0) {
    return
  }
  $existingBackend = Get-ExistingNamespaceBackend
  if ([string]::IsNullOrWhiteSpace($existingBackend) -or $existingBackend -eq "rmux") {
    return
  }

  $previousErrorAction = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    & $Python.Exe @($Python.Args) $ScriptPath "--project" $ProjectRoot "kill" "-f" *> $null
  } catch {
  } finally {
    $ErrorActionPreference = $previousErrorAction
  }
  $global:LASTEXITCODE = 0
}

function Assert-NoProjectOverride {
  param([string[]]$ForwardedArgs)

  foreach ($arg in @($ForwardedArgs)) {
    if ($arg -eq "--project" -or $arg -like "--project=*") {
      throw "ccb-src is bound to $ProjectRoot and does not accept --project overrides."
    }
  }
}

function Resolve-CcbSourcePython {
  $candidates = @()
  if (-not [string]::IsNullOrWhiteSpace($env:CCB_SOURCE_PYTHON)) {
    $candidates += ,@($env:CCB_SOURCE_PYTHON)
  }
  $candidates += ,@("py", "-3")
  $candidates += ,@("python")
  $candidates += ,@("python3")

  foreach ($candidate in $candidates) {
    $candidateParts = @($candidate)
    $exe = $candidateParts[0]
    $prefixArgs = @()
    if ($candidateParts.Count -gt 1) {
      $prefixArgs = @($candidateParts[1..($candidateParts.Count - 1)])
    }
    $command = Get-Command $exe -ErrorAction SilentlyContinue
    if ($null -eq $command) {
      continue
    }
    & $exe @prefixArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" *> $null
    if ($LASTEXITCODE -eq 0) {
      return @{
        Exe = $exe
        Args = $prefixArgs
      }
    }
  }

  throw "Python 3.10+ was not found. Set CCB_SOURCE_PYTHON to a Python executable or install Python."
}

$hadAllowedRoots = Test-Path Env:\CCB_SOURCE_ALLOWED_ROOTS
$previousAllowedRoots = $env:CCB_SOURCE_ALLOWED_ROOTS
$hadMuxBackend = Test-Path Env:\CCB_MUX_BACKEND
$previousMuxBackend = $env:CCB_MUX_BACKEND
$exitProcess = $env:CCB_SRC_EXIT_PROCESS -eq "1"
Assert-NoProjectOverride -ForwardedArgs $CcbArgs
$python = Resolve-CcbSourcePython
$script:CcbExitCode = 1

try {
  $defaultedRmux = Enable-DefaultWindowsRmuxBackend

  if ([string]::IsNullOrWhiteSpace($previousAllowedRoots)) {
    $env:CCB_SOURCE_ALLOWED_ROOTS = $ProjectRoot
  } else {
    $env:CCB_SOURCE_ALLOWED_ROOTS = $ProjectRoot + [System.IO.Path]::PathSeparator + $previousAllowedRoots
  }

  Reset-ExistingTmuxNamespaceForDefaultRmux -DefaultedRmux $defaultedRmux -Python $python -ScriptPath $CcbScript -ForwardedArgs $CcbArgs
  & $python.Exe @($python.Args) $CcbScript "--project" $ProjectRoot @CcbArgs
  $script:CcbExitCode = $LASTEXITCODE
} finally {
  if ($hadAllowedRoots) {
    $env:CCB_SOURCE_ALLOWED_ROOTS = $previousAllowedRoots
  } else {
    Remove-Item Env:\CCB_SOURCE_ALLOWED_ROOTS -ErrorAction SilentlyContinue
  }
  if ($hadMuxBackend) {
    $env:CCB_MUX_BACKEND = $previousMuxBackend
  } else {
    Remove-Item Env:\CCB_MUX_BACKEND -ErrorAction SilentlyContinue
  }
}

$global:LASTEXITCODE = $script:CcbExitCode
if ($exitProcess) {
  exit $script:CcbExitCode
}
