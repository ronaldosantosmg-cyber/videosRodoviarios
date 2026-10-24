@echo off
setlocal
title Compilar o iniciador do Rodovia Studio
rem Gera "Rodovia Studio.exe" com o compilador C# que ja vem no Windows (.NET Framework 4). Nao requer administrador.
rem 1.27 (iniciador 1.1): com as DLLs do WebView2 o programa abre numa janela propria do Windows; sem elas, no Edge em modo aplicativo.
rem 1.32 (iniciador 1.2): este arquivo fica em "sistema"; o .exe e criado na pasta principal e o ABRIR RODOVIA STUDIO.cmd
rem passa a ficar so em "sistema" (reserva). RODOVIA_SEM_PAUSA=1: sem perguntas (usado pelo proprio aplicativo).
set "SYS="
if exist "%~dp0programa\run.py" (set "SYS=%~dp0programa" & for %%I in ("%~dp0..") do set "ROOT=%%~fI")
if not defined SYS if exist "%~dp0sistema\programa\run.py" (set "SYS=%~dp0sistema\programa" & for %%I in ("%~dp0.") do set "ROOT=%%~fI")
if not defined SYS if exist "%~dp0suporte\sistema\run.py" (set "SYS=%~dp0suporte\sistema" & for %%I in ("%~dp0.") do set "ROOT=%%~fI")
if not defined SYS (
 echo Nao encontrei a pasta do programa ^(sistema\programa^).
 if not defined RODOVIA_SEM_PAUSA pause
 exit /b 1
)
cd /d "%SYS%"
set "SRC=%SYS%\iniciador\RodoviaStudio.cs"
set "ICO=%SYS%\rodovia.ico"
set "OUT=%ROOT%\Rodovia Studio.exe"
set "WV=%SYS%\webview2"
set "PKG=%SYS%\pacotes_webview2"
set "WVVER=1.0.2903.40"
set "CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%CSC%" set "CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe"
if not exist "%CSC%" (
 echo Nao encontrei o compilador do .NET Framework 4 ^(csc.exe^) neste Windows.
 echo Continue usando "ABRIR RODOVIA STUDIO.cmd".
 if not defined RODOVIA_SEM_PAUSA pause
 exit /b 1
)
if not exist "%SRC%" (
 echo Falta o arquivo sistema\programa\iniciador\RodoviaStudio.cs. Aplique a atualizacao 1.23 ou mais nova.
 if not defined RODOVIA_SEM_PAUSA pause
 exit /b 1
)
tasklist /FI "IMAGENAME eq Rodovia Studio.exe" 2>nul | find /I "Rodovia Studio.exe" >nul
if not errorlevel 1 (
 echo O Rodovia Studio esta aberto. Encerre-o pelo icone perto do relogio ^(botao direito ^> Encerrar^) e execute de novo.
 if not defined RODOVIA_SEM_PAUSA pause
 exit /b 1
)
rem ---- WebView2: usa as DLLs ja extraidas; senao um .nupkg em pacotes_webview2; senao tenta baixar do nuget.org ----
if exist "%WV%\Microsoft.Web.WebView2.WinForms.dll" if exist "%WV%\Microsoft.Web.WebView2.Core.dll" if exist "%WV%\WebView2Loader.dll" goto temwv
if not exist "%PKG%" mkdir "%PKG%"
set "NUP="
for %%f in ("%PKG%\microsoft.web.webview2*.nupkg") do set "NUP=%%~ff"
if not defined NUP (
 echo Baixando o componente WebView2 ^(Microsoft.Web.WebView2 %WVVER%, nuget.org^)...
 powershell -NoProfile -ExecutionPolicy Bypass -Command "try{[Net.ServicePointManager]::SecurityProtocol='Tls12';Invoke-WebRequest -UseBasicParsing -Uri 'https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/%WVVER%/microsoft.web.webview2.%WVVER%.nupkg' -OutFile '%PKG%\microsoft.web.webview2.%WVVER%.nupkg';exit 0}catch{Write-Host $_.Exception.Message;exit 1}"
 if exist "%PKG%\microsoft.web.webview2.%WVVER%.nupkg" set "NUP=%PKG%\microsoft.web.webview2.%WVVER%.nupkg"
)
if not defined NUP goto semwv
echo Extraindo o WebView2...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop';$t=Join-Path $env:TEMP ('wv2_'+[guid]::NewGuid());Add-Type -AssemblyName System.IO.Compression.FileSystem;[IO.Compression.ZipFile]::ExtractToDirectory('%NUP%',$t);New-Item -ItemType Directory -Force -Path '%WV%'|Out-Null;foreach($n in 'Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll'){$f=Get-ChildItem -Recurse -Path (Join-Path $t 'lib') -Filter $n|Sort-Object {if($_.FullName -match 'net462'){0}elseif($_.FullName -match 'net45'){1}else{2}}|Select-Object -First 1;if(-not $f){throw ('falta '+$n)};Copy-Item $f.FullName '%WV%' -Force};$l=Get-ChildItem -Recurse -Path $t -Filter 'WebView2Loader.dll'|Where-Object {$_.FullName -match 'win-x64'}|Select-Object -First 1;if(-not $l){throw 'falta WebView2Loader.dll (win-x64)'};Copy-Item $l.FullName '%WV%' -Force;Remove-Item -Recurse -Force $t"
if errorlevel 1 goto semwv
:temwv
echo Compilando com janela propria ^(WebView2^)...
if exist "%ICO%" (
 "%CSC%" /nologo /codepage:65001 /target:winexe /optimize+ /define:WEBVIEW2 /out:"%OUT%" /win32icon:"%ICO%" /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:"%WV%\Microsoft.Web.WebView2.Core.dll" /r:"%WV%\Microsoft.Web.WebView2.WinForms.dll" "%SRC%"
) else (
 "%CSC%" /nologo /codepage:65001 /target:winexe /optimize+ /define:WEBVIEW2 /out:"%OUT%" /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:"%WV%\Microsoft.Web.WebView2.Core.dll" /r:"%WV%\Microsoft.Web.WebView2.WinForms.dll" "%SRC%"
)
if not errorlevel 1 goto compilado
echo.
echo A compilacao com WebView2 falhou; compilando a versao que abre no Edge em modo aplicativo.
:semwv
echo WebView2 indisponivel ^(sem internet ou bloqueado^): o programa abrira no Edge em modo aplicativo.
echo Para a janela propria, coloque o arquivo microsoft.web.webview2.*.nupkg em sistema\programa\pacotes_webview2 e execute de novo.
echo Compilando...
if exist "%ICO%" (
 "%CSC%" /nologo /codepage:65001 /target:winexe /optimize+ /out:"%OUT%" /win32icon:"%ICO%" /r:System.Windows.Forms.dll /r:System.Drawing.dll "%SRC%"
) else (
 "%CSC%" /nologo /codepage:65001 /target:winexe /optimize+ /out:"%OUT%" /r:System.Windows.Forms.dll /r:System.Drawing.dll "%SRC%"
)
:compilado
if errorlevel 1 (
 echo.
 echo A compilacao falhou. Copie as mensagens acima e envie ao suporte. Continue usando "ABRIR RODOVIA STUDIO.cmd".
 if not defined RODOVIA_SEM_PAUSA pause
 exit /b 1
)
echo.
echo Pronto: "Rodovia Studio.exe" criado na pasta principal.
rem 1.32: com o .exe, a pasta principal fica so com ele; o ABRIR RODOVIA STUDIO.cmd fica de reserva em "sistema".
if exist "%ROOT%\ABRIR RODOVIA STUDIO.cmd" if exist "%ROOT%\sistema\ABRIR RODOVIA STUDIO.cmd" del "%ROOT%\ABRIR RODOVIA STUDIO.cmd"
if exist "%ROOT%\ABRIR RODOVIA STUDIO.cmd" if exist "%ROOT%\sistema" move /y "%ROOT%\ABRIR RODOVIA STUDIO.cmd" "%ROOT%\sistema\" >nul
if exist "%ROOT%\sistema\logs\recompilar_iniciador.txt" del "%ROOT%\sistema\logs\recompilar_iniciador.txt"
if defined RODOVIA_SEM_PAUSA exit /b 0
echo Abrindo...
start "" "%OUT%"
timeout /t 3 >nul
