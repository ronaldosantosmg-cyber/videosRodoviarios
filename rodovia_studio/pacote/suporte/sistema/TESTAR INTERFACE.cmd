@echo off
setlocal
cd /d "%~dp0"
if exist "runtime\python.exe" (
  "runtime\python.exe" executar_testes_visuais.py
) else (
  python executar_testes_visuais.py
)
pause
