param([switch]$PrepararApenas)
# -PrepararApenas: so prepara Python, bibliotecas e FFmpeg (usado pelo Rodovia Studio.exe) e nao abre o aplicativo.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$runtime = Join-Path $PSScriptRoot 'runtime'
$py = Join-Path $runtime 'python.exe'
$logs = Join-Path (Split-Path $PSScriptRoot -Parent) 'logs'
if (@('sistema','programa') -notcontains (Split-Path $PSScriptRoot -Leaf)) { $logs = $PSScriptRoot }
New-Item -ItemType Directory -Force $logs | Out-Null
$log = Join-Path $logs 'instalacao.log'
try {
    if (-not (Test-Path $py)) {
        Write-Host 'Preparando Python portatil na pasta do aplicativo. Nao requer administrador.'
        New-Item -ItemType Directory -Force $runtime | Out-Null
        $zip = Join-Path $runtime 'python.zip'
        Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' -OutFile $zip -UseBasicParsing
        Expand-Archive $zip -DestinationPath $runtime -Force
        Remove-Item $zip
        $pth = Join-Path $runtime 'python312._pth'
        @('python312.zip','.','Lib\site-packages','..','import site') | Set-Content $pth -Encoding ASCII
    }
    if (-not (Test-Path (Join-Path $runtime 'Lib\site-packages\pip\__init__.py'))) {
        $getpip = Join-Path $runtime 'get-pip.py'
        Invoke-WebRequest 'https://bootstrap.pypa.io/get-pip.py' -OutFile $getpip -UseBasicParsing
        & $py $getpip --no-warn-script-location 2>&1 | Tee-Object -FilePath $log -Append
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar pip. Confira a internet e instalacao.log.' }
        Remove-Item $getpip -ErrorAction SilentlyContinue
    }
    $req = Join-Path $PSScriptRoot 'requirements.txt'
    $fingerprint = (Get-FileHash $req -Algorithm SHA256).Hash
    $stamp = Join-Path $runtime 'dependencias.ok'
    if (-not (Test-Path $stamp) -or (Get-Content $stamp -Raw).Trim() -ne $fingerprint) {
        Write-Host 'Baixando dependencias e FFmpeg. Aguarde a primeira preparacao.'
        $wheels = Join-Path $PSScriptRoot 'pacotes'
        if (Test-Path $wheels) {
            # Instalacao sem internet a partir de pacotes .whl copiados para a pasta 'pacotes'.
            & $py -m pip install --no-index --find-links $wheels --disable-pip-version-check --no-warn-script-location -r $req 2>&1 | Tee-Object -FilePath $log -Append
        } else {
            & $py -m pip install --no-cache-dir --disable-pip-version-check --no-warn-script-location -r $req 2>&1 | Tee-Object -FilePath $log -Append
        }
        if ($LASTEXITCODE -ne 0) { throw 'Falha nas dependencias. Confira instalacao.log. Execute INICIAR.cmd novamente apos corrigir a conexao.' }
        $fingerprint | Set-Content $stamp -Encoding ASCII
    }
    # 1.32: pasta principal so com o arquivo principal (Rodovia Studio.exe ou ABRIR RODOVIA STUDIO.cmd).
    $root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
    $exe = Join-Path $root 'Rodovia Studio.exe'
    $sistema = Join-Path $root 'sistema'
    # Depois da atualizacao para a 1.32 o .exe antigo foi guardado; recompila sozinho (sem administrador).
    $rec = Join-Path $logs 'recompilar_iniciador.txt'
    $comp = Join-Path $sistema 'COMPILAR INICIADOR.cmd'
    if (-not $PrepararApenas -and (Test-Path $rec) -and -not (Test-Path $exe) -and (Test-Path $comp)) {
        Write-Host 'Recriando o "Rodovia Studio.exe" para a nova organizacao das pastas...'
        $env:RODOVIA_SEM_PAUSA = '1'
        $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        try { & cmd.exe /c "`"$comp`"" *>> $log } catch { } finally { $ErrorActionPreference = $eap }
        Remove-Item Env:RODOVIA_SEM_PAUSA -ErrorAction SilentlyContinue
        if (Test-Path $exe) { Write-Host 'Pronto: use o "Rodovia Studio.exe" da pasta principal.' }
        else { Move-Item $rec (Join-Path $logs 'recompilar_iniciador_falhou.txt') -Force -ErrorAction SilentlyContinue; Write-Host 'Nao foi possivel recriar o .exe agora; continue pelo ABRIR RODOVIA STUDIO.cmd.' }
    }
    $main = if (Test-Path $exe) { $exe } elseif (Test-Path (Join-Path $root 'ABRIR RODOVIA STUDIO.cmd')) { Join-Path $root 'ABRIR RODOVIA STUDIO.cmd' } else { Join-Path $sistema 'ABRIR RODOVIA STUDIO.cmd' }
    # Atalho "Rodovia Studio" na Area de Trabalho: criado uma vez; corrigido se apontar para um arquivo que nao existe mais.
    if (-not $PrepararApenas -and (Test-Path $main)) {
        try {
            $desk = [Environment]::GetFolderPath('Desktop')
            $ws = New-Object -ComObject WScript.Shell
            $lnkPath = Join-Path $desk 'Rodovia Studio.lnk'
            $flag = Join-Path $logs 'atalho.ok'
            $fix = $false
            if (Test-Path $lnkPath) { $cur = $ws.CreateShortcut($lnkPath).TargetPath; if ($cur -and -not (Test-Path $cur)) { $fix = $true } }
            if ($fix -or (-not (Test-Path $flag) -and -not (Test-Path $lnkPath))) {
                $lnk = $ws.CreateShortcut($lnkPath)
                $lnk.TargetPath = $main
                $lnk.WorkingDirectory = $root
                $lnk.IconLocation = (Join-Path $PSScriptRoot 'rodovia.ico')
                $lnk.Description = 'Rodovia Studio - apresentacoes rodoviarias em video'
                $lnk.Save()
                'ok' | Set-Content $flag -Encoding ASCII
                Write-Host 'Atalho "Rodovia Studio" da Area de Trabalho criado/atualizado.'
            }
        } catch { }
    }
    & $py (Join-Path $PSScriptRoot 'diagnostico.py')
    if ($LASTEXITCODE -ne 0) { throw 'O diagnostico encontrou dependencias ausentes.' }
    if ($PrepararApenas) { Write-Host 'Preparacao concluida.'; exit 0 }
    & $py (Join-Path $PSScriptRoot 'run.py')
    if ($LASTEXITCODE -ne 0) { throw 'O aplicativo encerrou com erro.' }
} catch {
    $_ | Out-String | Tee-Object -FilePath $log -Append | Write-Host
    Write-Host 'Se a empresa bloquear downloads ou PowerShell, sera necessario liberar esses acessos.'
    exit 1
}
