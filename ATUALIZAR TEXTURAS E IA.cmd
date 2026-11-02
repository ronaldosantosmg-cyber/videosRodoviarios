@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Feche o Rodovia Studio antes de continuar.
pause
if exist "sistema\programa\runtime\python.exe" (set PY="sistema\programa\runtime\python.exe") else (set PY=python)
cd /d "%~dp0sistema\programa"
%PY% -m app.componentes --raiz "%~dp0." --instalar
echo.
set /p R=Instalar a IA local gratuita agora (baixa ~2 GB)? [S/N] 
if /i "%R%"=="S" %PY% -m app.ia_instalar --raiz "%~dp0." --baixar
pause
