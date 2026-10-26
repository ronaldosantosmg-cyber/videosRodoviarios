@echo off
setlocal
title Rodovia Studio
rem 1.32: funciona na pasta principal ou dentro de "sistema" (reserva quando ha o Rodovia Studio.exe).
set "P="
if exist "%~dp0sistema\programa\iniciar.ps1" set "P=%~dp0sistema\programa"
if not defined P if exist "%~dp0programa\iniciar.ps1" set "P=%~dp0programa"
if not defined P if exist "%~dp0suporte\sistema\iniciar.ps1" set "P=%~dp0suporte\sistema"
if not defined P (
 echo Instalacao incompleta: nao encontrei sistema\programa\iniciar.ps1
 pause
 exit /b 1
)
cd /d "%P%"
if exist "%P%\runtime\python.exe" (
 "%P%\runtime\python.exe" "%P%\preparar.py"
) else (
 py.exe -3.12 "%P%\preparar.py"
)
if errorlevel 1 (
 echo.
 echo O aplicativo nao iniciou. Consulte a mensagem acima e sistema\logs\instalacao.log
 pause
)
