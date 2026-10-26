param([switch]$PrepararApenas)
# Respeita a politica corporativa; nao altera ExecutionPolicy ou antivirus.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$py = Join-Path $PSScriptRoot 'runtime\python.exe'
$argsPython = @((Join-Path $PSScriptRoot 'preparar.py'))
if ($PrepararApenas) { $argsPython += '--preparar-apenas' }
if (Test-Path $py) { & $py @argsPython }
elseif (Get-Command py.exe -ErrorAction SilentlyContinue) { & py.exe -3.12 @argsPython }
else { Write-Host 'Python 3.12 ausente. Solicite a TI um Python oficial aprovado. Nenhuma protecao foi desativada.'; exit 1 }
exit $LASTEXITCODE
