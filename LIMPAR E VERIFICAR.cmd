@echo off
setlocal
title Rodovia Studio - limpeza e verificacao
rem 2.56: feche o Rodovia Studio antes. Nada e apagado: o que sai vai para sistema\_quarentena (restauravel).
set "R=%~dp0"
if exist "%R%sistema\programa\app\server.py" (set "P=%R%sistema\programa") else if exist "%R%..\sistema\programa\app\server.py" (set "R=%~dp0..\" & set "P=%~dp0..\sistema\programa") else (echo Nao encontrei sistema\programa. & pause & exit /b 1)
if exist "%P%\runtime\python.exe" (set "PY=%P%\runtime\python.exe") else (set "PY=py.exe -3.12")
cd /d "%P%"
echo === 1/3 VERIFICACAO: pastas e arquivos ausentes ===
%PY% -m app.higiene --raiz "%R%" --verificar
echo.
echo === 2/3 PREVIA DA LIMPEZA (nada alterado) ===
%PY% -m app.higiene --raiz "%R%"
echo.
set /p OK=Mover esses itens para a quarentena agora? (S/N): 
if /i "%OK%"=="S" (
  %PY% -m app.higiene --raiz "%R%" --executar
  echo.
  echo === 3/3 VERIFICACAO APOS A LIMPEZA ===
  %PY% -m app.higiene --raiz "%R%" --verificar
) else (echo Nada foi movido.)
echo.
echo Para restaurar: python -m app.higiene --raiz "%R%" --restaurar CARIMBO   (pasta em sistema\_quarentena)
pause
