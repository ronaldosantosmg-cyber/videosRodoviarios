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
set "P=%R%\sistema\programa"
if not exist "%P%\atualizar_portatil.py" set "P=%R%\suporte\sistema"
if exist "%P%\runtime\python.exe" (
 "%P%\runtime\python.exe" "%P%\atualizar_portatil.py" --raiz "%R%"
) else if exist "%P%\runtime\Scripts\python.exe" (
 "%P%\runtime\Scripts\python.exe" "%P%\atualizar_portatil.py" --raiz "%R%"
) else (
 py.exe -3.12 "%P%\atualizar_portatil.py" --raiz "%R%"
)
set "RC=%ERRORLEVEL%"
if not defined RODOVIA_SEM_PAUSA pause

exit /b %RC%
