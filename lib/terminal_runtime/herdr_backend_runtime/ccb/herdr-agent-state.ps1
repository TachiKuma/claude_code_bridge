# Herdr agent-state hook for CCB (Claude Code Bridge)
# Place this file at: C:\Users\Administrator\.ccb\hooks\herdr-agent-state.ps1
#
# Herdr calls this hook to discover CCB-managed agents in the current
# project.  The hook queries ccbd via its control-plane socket and emits
# JSON with one agent entry per CCB-managed pane.
#
# Expected output (JSON to stdout):
# {
#   "agents": [
#     {"name": "agent1", "provider": "codex", "pane_id": "wH:p3", "state": "idle"},
#     {"name": "agent2", "provider": "claude", "pane_id": "wH:p4", "state": "idle"}
#   ]
# }

param(
    [string] $ProjectRoot = $PSScriptRoot
)

$ErrorActionPreference = 'SilentlyContinue'

# Locate the ccbd control-plane token and socket.
# The state root follows CCB_RUNTIME_STATE_HOME / project_id / ccbd.
$ccbDir = Join-Path $ProjectRoot '.ccb'
$refPath = Join-Path $ccbDir 'runtime-root-ref.json'
if (-not (Test-Path $refPath)) {
    Write-Output '{"agents":[]}'
    exit 0
}

try {
    $ref = Get-Content -Raw $refPath | ConvertFrom-Json
    $projectId = $ref.project_id
    $stateRoot = if ($ref.PSObject.Properties['runtime_state_root']) { $ref.runtime_state_root } else { "D:\.c8\rs\$projectId" }
} catch {
    Write-Output '{"agents":[]}'
    exit 0
}

$ccbdDir = Join-Path $stateRoot 'ccbd'
$tokenFiles = Get-ChildItem -Path $ccbdDir -Filter 'control-plane-token-*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if (-not $tokenFiles) {
    Write-Output '{"agents":[]}'
    exit 0
}

# Read the most recent token to discover the ccbd TCP endpoint.
$tokenPath = $tokenFiles[0].FullName
try {
    $token = Get-Content -Raw $tokenPath | ConvertFrom-Json
    $address = $token.address
    $port = $token.port
    $authToken = $token.token
} catch {
    Write-Output '{"agents":[]}'
    exit 0
}

# Query ccbd for agent state via TCP control plane.
$agents = @()
try {
    $tcp = New-Object System.Net.Sockets.TcpClient($address, $port)
    $stream = $tcp.GetStream()
    $writer = New-Object System.IO.StreamWriter($stream)
    $reader = New-Object System.IO.StreamReader($stream)

    # Send a ping request to ccbd (minimal JSON-RPC).
    $request = '{"op":"ping","project_id":"' + $projectId + '","auth":"' + $authToken + '"}' + "`n"
    $writer.Write($request)
    $writer.Flush()

    # Read response with a short timeout.
    $tcp.ReceiveTimeout = 3000
    $response = $reader.ReadLine()
    if ($response) {
        $payload = $response | ConvertFrom-Json
        if ($payload.agents) {
            foreach ($agent in $payload.agents) {
                $agents += @{
                    name = $agent.agent_name
                    provider = $agent.provider
                    state = $agent.runtime_state
                }
            }
        }
    }
    $reader.Close()
    $writer.Close()
    $stream.Close()
    $tcp.Close()
} catch {
    # ccbd not reachable; return empty.
}

$output = @{ agents = $agents } | ConvertTo-Json -Compress
Write-Output $output
