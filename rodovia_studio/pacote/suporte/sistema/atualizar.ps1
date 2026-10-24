param([string]$Raiz,[string]$Pacote='',[int]$Aguardar=0,[switch]$RestaurarAnterior,[string]$Backup='')
# Executa o atualizador com uma copia temporaria do Python portatil, para que a pasta do
# programa possa ser reorganizada e atualizada sem arquivos em uso.
$ErrorActionPreference = 'Stop'
try {
    $Raiz = (Resolve-Path $Raiz).Path
    $runtime = $null
    foreach ($c in @((Join-Path $Raiz 'sistema\programa\runtime'), (Join-Path $Raiz 'suporte\sistema\runtime'), (Join-Path $Raiz 'runtime'))) {
        if (Test-Path (Join-Path $c 'python.exe')) { $runtime = $c; break }
    }
    if (-not $runtime) { throw 'Python portatil nao encontrado. Abra o Rodovia Studio uma vez antes de atualizar.' }
    $tmp = Join-Path $env:TEMP ('rodovia_atualizador_' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force $tmp | Out-Null
    Get-ChildItem $runtime -File | ForEach-Object { Copy-Item $_.FullName $tmp }
    $installed = Join-Path $Raiz 'sistema\programa\atualizador.py'
    if (-not (Test-Path $installed)) { $installed = Join-Path $Raiz 'suporte\sistema\atualizador.py' }
    $script = if ($Pacote) { Join-Path $Pacote 'suporte\sistema\atualizador.py' } else { $installed }
    $copyScript = Join-Path $tmp 'atualizador.py'
    Copy-Item $script $copyScript
    $py = Join-Path $tmp 'python.exe'
    if ($RestaurarAnterior) {
        $arguments = @('-X','utf8',$copyScript,'--raiz',$Raiz,'--restaurar-anterior','--aguardar',"$Aguardar")
        if ($Backup) { $arguments += @('--backup',$Backup) }
        & $py @arguments
    }
    elseif ($Pacote) { & $py -X utf8 $copyScript --raiz $Raiz --pacote $Pacote } else { & $py -X utf8 $copyScript --raiz $Raiz --procurar --aguardar $Aguardar }
    $code = $LASTEXITCODE
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    exit $code
} catch {
    Write-Host $_.Exception.Message
    exit 1
}
