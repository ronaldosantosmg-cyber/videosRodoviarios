@echo off
setlocal
title Rodovia Studio - Instalar atualizacao
cd /d "%~dp0"
echo.
echo Rodovia Studio - Atualizacao 1.40.9
echo Feche o aplicativo antes de continuar.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0apoio\instalar.ps1"
if errorlevel 1 (
  echo.
  echo A atualizacao nao foi concluida.
  pause
  exit /b 1
)
exit /b 0
