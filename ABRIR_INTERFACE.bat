@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   VIDEOS RODOVIARIOS - INICIALIZACAO
echo ========================================

echo.
where py >nul 2>nul
if %errorlevel%==0 (
    set PY=py -3.11
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python 3.11 ou superior nao foi encontrado.
        echo Instale o Python para Windows e marque "Add Python to PATH".
        pause
        exit /b 1
    )
    set PY=python
)

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente local sem permissao de administrador...
    %PY% -m venv .venv
    if errorlevel 1 goto :erro
)

set VPY=%CD%\.venv\Scripts\python.exe

echo Verificando dependencias...
"%VPY%" -m pip install -q --disable-pip-version-check -U pip
"%VPY%" -m pip install -q --disable-pip-version-check -e .
if errorlevel 1 goto :erro

echo Abrindo interface...
start "Videos Rodoviarios" "%VPY%" -m videos_rodoviarios.ui
exit /b 0

:erro
echo.
echo Ocorreu um erro durante a preparacao do aplicativo.
echo Copie a mensagem exibida acima para diagnostico.
pause
exit /b 1
