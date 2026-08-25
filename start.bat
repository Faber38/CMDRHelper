@echo off
setlocal
cd /d "%~dp0"

title CMDRHelper

if not exist "venv\Scripts\python.exe" (
    echo ==========================================
    echo CMDRHelper ist noch nicht eingerichtet.
    echo Bitte zuerst install.bat ausfuehren.
    echo ==========================================
    echo.
    pause
    exit /b 1
)

if not exist "main.py" (
    echo ==========================================
    echo [FEHLER] main.py wurde nicht gefunden.
    echo ==========================================
    echo.
    pause
    exit /b 1
)

"venv\Scripts\python.exe" main.py

if errorlevel 1 (
    echo.
    echo ==========================================
    echo CMDRHelper wurde mit einem Fehler beendet.
    echo Die Meldung oben kann bei der Fehlersuche helfen.
    echo ==========================================
    echo.
    pause
)

exit /b %errorlevel%
