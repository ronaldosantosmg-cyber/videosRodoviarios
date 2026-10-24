@echo off
setlocal
title Atualizar Rodovia Studio
rem 1.32: fica em "sistema". Tambem da para atualizar pelo aplicativo (Arquivo > Atualizar).
set "R="
if exist "%~dp0programa\atualizar.ps1" for %%I in ("%~dp0..") do set "R=%%~fI"
if not defined R if exist "%~dp0sistema\programa\atualizar.ps1" for %%I in ("%~dp0.") do set "R=%%~fI"
if not defined R if exist "%~dp0suporte\sistema\atualizar.ps1" for %%I in ("%~dp0.") do set "R=%%~fI"
if not defined R (
 echo Nao encontrei a pasta do Rodovia Studio.
 pause
 exit /b 1
)
set "A=%R%\sistema\programa\atualizar.ps1"
if not exist "%A%" set "A=%R%\suporte\sistema\atualizar.ps1"
echo Procurando atualizacoes somente na pasta "atualizacoes"...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%A%" -Raiz "%R%"
if not defined RODOVIA_SEM_PAUSA pause
