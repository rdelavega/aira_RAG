# start.ps1 — AIRA (Windows PowerShell; same flow as start.sh)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# #region agent log
$script:_airaDbgLog = Join-Path $PSScriptRoot 'debug-11adcd.log'
function Write-AiraAgentLog {
    param(
        [string]$HypothesisId,
        [string]$Location,
        [string]$Message,
        [hashtable]$Data
    )
    $ts = [int64]([DateTime]::UtcNow - [datetime]'1970-01-01').TotalMilliseconds
    $payload = [ordered]@{
        sessionId    = '11adcd'
        hypothesisId = $HypothesisId
        location     = $Location
        message      = $Message
        data         = $Data
        timestamp    = $ts
    } | ConvertTo-Json -Compress -Depth 6
    Add-Content -LiteralPath $script:_airaDbgLog -Value $payload -Encoding utf8
}
# #endregion

# #region agent log
Write-AiraAgentLog -HypothesisId 'H1' -Location 'start.ps1:entry' -Message 'powershell start' -Data @{
    pwd      = (Get-Location).Path
    env_file = (Test-Path -LiteralPath '.env')
}
# #endregion

Write-Host 'Inicializing AIRA...'

if (-not (Test-Path -LiteralPath '.env')) {
    Write-Host "Error, there's no .env file — copy .env.example and fill with your config"
    exit 1
}

Get-Content -LiteralPath '.env' | ForEach-Object {
    $line = $_.TrimEnd("`r")
    if ($line -match '^\s*#' -or $line -match '^\s*$') { return }
    $ix = $line.IndexOf('=')
    if ($ix -gt 0) {
        $k = $line.Substring(0, $ix).Trim()
        $v = $line.Substring($ix + 1).Trim()
        [Environment]::SetEnvironmentVariable($k, $v, 'Process')
    }
}

$vaultPath = [Environment]::GetEnvironmentVariable('VAULT_PATH', 'Process')
$vaultNonempty = [bool]$vaultPath
$vaultIsDir = ($vaultNonempty -and (Test-Path -LiteralPath $vaultPath -PathType Container))

# #region agent log
Write-AiraAgentLog -HypothesisId 'H3' -Location 'start.ps1:after-dotenv' -Message 'vault env' -Data @{
    vault_nonempty = $vaultNonempty
    vault_isdir    = $vaultIsDir
}
# #endregion

if (-not $vaultIsDir) {
    Write-Host "Vault not found on: $vaultPath"
    Write-Host 'Check VAULT_PATH on your .env'
    exit 1
}

foreach ($sub in @('10_Books', '20_Design', '30_Business', '40_Personal', '90_Archive')) {
    $d = Join-Path $vaultPath $sub
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

Write-Host "Vault verified: $vaultPath"

$dockerBin = [bool](Get-Command docker -ErrorAction SilentlyContinue)
$composeOk = $false
if ($dockerBin) {
    $prevEa = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'SilentlyContinue'
        docker compose version *> $null
        $composeOk = ($LASTEXITCODE -eq 0)
    }
    finally {
        $ErrorActionPreference = $prevEa
    }
}

# #region agent log
Write-AiraAgentLog -HypothesisId 'H4' -Location 'start.ps1:pre-compose' -Message 'docker cli' -Data @{
    docker_bin         = $dockerBin
    compose_subcmd_ok  = $composeOk
}
# #endregion

docker compose up -d

Write-Host ''
Write-Host 'AIRA iniciated..'
Write-Host '   API RAG:   http://localhost:8000'
Write-Host '   OpenClaw:  http://localhost:18789'
Write-Host '   Ollama:    http://localhost:11434'
Write-Host ''
Write-Host 'Logs: docker compose logs -f'
Write-Host 'Stop: docker compose down'
