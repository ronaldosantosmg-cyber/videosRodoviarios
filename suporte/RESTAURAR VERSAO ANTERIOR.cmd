@echo off
setlocal
cd /d "%~dp0"
if exist "programa\runtime\python\python.exe" set "PY=programa\runtime\python\python.exe"
if not defined PY if exist "programa\runtime\python.exe" set "PY=programa\runtime\python.exe"
if not defined PY set "PY=python"
set "ROOT=%~dp0.."
echo Rodovia Studio - Restabelecer versao anterior
echo.
echo Projetos e videos nao serao alterados.
echo Sera criado um snapshot de seguranca da versao atual antes do rollback.
echo.
choice /C SN /N /M "Continuar? [S/N] "
if errorlevel 2 exit /b 0
"%PY%" "programa\atualizador.py" --raiz "%ROOT%" --restaurar-anterior
if errorlevel 1 (
  echo.
  echo Nao foi possivel restabelecer a versao anterior.
  pause
  exit /b 1
)
echo.
echo Versao anterior restabelecida.
pause
