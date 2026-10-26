@echo off
setlocal
rem Compilacao manual, sem downloads, elevacao ou alteracao de politicas.
set "P=%~dp0programa"
if not exist "%P%\iniciador\RodoviaStudio.cs" set "P=%~dp0suporte\sistema"
set "CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%CSC%" (
 echo Compilador .NET ausente. Solicite a TI a compilacao e assinatura do iniciador.
 exit /b 1
)
if not exist "%P%\iniciador\RodoviaStudio.cs" exit /b 1
"%CSC%" /nologo /target:winexe /r:System.Windows.Forms.dll /r:System.Drawing.dll /out:"%~dp0..\Rodovia Studio.exe" "%P%\iniciador\RodoviaStudio.cs"
exit /b %errorlevel%
