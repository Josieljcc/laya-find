# Demo genérico: laya_find → JSON (contrato scraper)
#
# Pré-requisito: laya-serve em http://127.0.0.1:8000
# Uso:
#   cd C:\laya
#   .\examples\find_demo.ps1
#   .\examples\find_demo.ps1 -Url "https://kiwify.com.br/" -Intent "botão de login"
#   .\examples\find_demo.ps1 -Reveal

param(
    [string]$Url = "https://kiwify.com.br/",
    [string]$Intent = "botão de login",
    [string]$Mode = "dom",
    [string]$Policy = "strict",
    [int]$SettleMs = 3000,
    [switch]$Reveal,
    [switch]$NoCache
)

$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Python do venv nao encontrado: $python"
}

Write-Host "Checando laya-serve..."
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
    Write-Host "laya-serve ok · loaded=$($health.loaded -join ',')"
} catch {
    Write-Host @"
laya-serve offline. Em outro terminal:

  `$env:LAYA_HOST='127.0.0.1'; `$env:LAYA_PORT='8000'
  `$env:LAYA_PRELOAD='1'; `$env:LAYA_MODELS='multilingual'; `$env:LAYA_DEVICE='cpu'
  .\.venv\Scripts\laya-serve.exe
"@
    exit 1
}

$pyArgs = @(
    "examples\laya_find.py",
    "--policy", $Policy,
    "--url", $Url,
    "--mode", $Mode,
    "--intent", $Intent,
    "--json",
    "--settle-ms", "$SettleMs"
)
if ($Reveal) { $pyArgs += "--reveal" }
if ($NoCache) { $pyArgs += "--no-cache" }

Write-Host ""
Write-Host "find · policy=$Policy · intent=$Intent"
Write-Host "url=$Url"

$stderrFile = [System.IO.Path]::GetTempFileName()
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    $line = & $python @pyArgs 2>$stderrFile
    $exitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $prevEap
}

if (Test-Path $stderrFile) {
    Get-Content -LiteralPath $stderrFile -Encoding utf8 -ErrorAction SilentlyContinue |
        ForEach-Object { Write-Host $_ }
    Remove-Item -LiteralPath $stderrFile -Force -ErrorAction SilentlyContinue
}

if (-not $line) {
    Write-Error "Sem JSON no stdout (exit=$exitCode)."
    exit 1
}

$jsonLine = @($line | Where-Object { $_ -match '^\s*\{' } | Select-Object -Last 1)
if (-not $jsonLine) { $jsonLine = $line | Select-Object -Last 1 }

try {
    $result = $jsonLine | ConvertFrom-Json
} catch {
    Write-Error "JSON invalido: $jsonLine"
    exit 1
}

Write-Host ""
Write-Host "ok=$($result.ok) selector_ok=$($result.selector_ok) cached=$($result.cached)"
Write-Host "selector=$($result.selector)"
Write-Host "text=$($result.text) href=$($result.href)"
if ($exitCode -ne 0 -or -not $result.ok -or -not $result.selector_ok) {
    exit $(if ($exitCode) { $exitCode } else { 1 })
}
