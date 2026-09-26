# Demo: achar campo de senha na Hotmart (laya-find)
# Pré-requisito: laya-serve em http://127.0.0.1:8000
#
# Senha na home costuma estar atrás do CTA de login → usa --reveal (opt-in).
#
# Uso:
#   cd C:\laya
#   .\examples\hotmart_senha.ps1

$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

$env:PYTHONIOENCODING = "utf-8"
# Evita NativeCommandError quando o CLI escreve logs em stderr
$env:PYTHONUTF8 = "1"

$layaFind = Join-Path $PSScriptRoot "..\.venv\Scripts\laya-find.exe"
if (-not (Test-Path $layaFind)) { $layaFind = "laya-find" }

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

Write-Host ""
Write-Host "Hotmart · intent=campo de senha · policy=strict · --reveal"

$findArgs = @(
    "--policy", "strict",
    "--url", "https://hotmart.com/pt-br",
    "--mode", "dom",
    "--intent", "campo de senha",
    "--json",
    "--reveal",
    "--settle-ms", "3000",
    "--no-cache"
)

# PowerShell trata escrita em stderr de exe nativo como erro se ErrorActionPreference=Stop.
# Temporariamente Continue + captura stderr em arquivo.
$stderrFile = [System.IO.Path]::GetTempFileName()
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    $line = & $layaFind @findArgs 2>$stderrFile
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

# Se vierem várias linhas, pega a que parece JSON
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
Write-Host "text=$($result.text)"
if ($exitCode -ne 0 -or -not $result.ok -or -not $result.selector_ok) {
    exit $(if ($exitCode) { $exitCode } else { 1 })
}
