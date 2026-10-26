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
set "WV=%P%\webview2"
if exist "%WV%\Microsoft.Web.WebView2.Core.dll" if exist "%WV%\Microsoft.Web.WebView2.WinForms.dll" if exist "%WV%\WebView2Loader.dll" goto webview
 echo WebView2 local nao encontrado. O iniciador usara o navegador em modo aplicativo.
"%CSC%" /nologo /codepage:65001 /target:winexe /r:System.Windows.Forms.dll /r:System.Drawing.dll /out:"%~dp0..\Rodovia Studio.exe" "%P%\iniciador\RodoviaStudio.cs"
exit /b %errorlevel%
:webview
"%CSC%" /nologo /codepage:65001 /target:winexe /define:WEBVIEW2 /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:"%WV%\Microsoft.Web.WebView2.Core.dll" /r:"%WV%\Microsoft.Web.WebView2.WinForms.dll" /out:"%~dp0..\Rodovia Studio.exe" "%P%\iniciador\RodoviaStudio.cs"
exit /b %errorlevel%
