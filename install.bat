@echo off
setlocal EnableExtensions DisableDelayedExpansion
title CMDRHelper - Installation
if not exist "%~dp0install-windows.ps1" (
    echo [FEHLER] install-windows.ps1 fehlt. Bitte das vollstaendige ZIP entpacken.
    pause
    exit /b 3
)
rem ExecutionPolicy gilt nur fuer diesen Prozess; keine Systemeinstellung aendern.
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-windows.ps1"
set "INSTALL_EXIT=%errorlevel%"
if not "%INSTALL_EXIT%"=="0" echo [FEHLER] Einrichtung nicht abgeschlossen ^(Exitcode %INSTALL_EXIT%^).
pause
exit /b %INSTALL_EXIT%
