@echo off
setlocal
cd /d "%~dp0"

title CMDRHelper - Installation

echo ==========================================
echo        CMDRHelper - Installation
echo ==========================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python wurde nicht gefunden.
    echo.
    echo Bitte Python 3 fuer Windows installieren und dabei
    echo "Add Python to PATH" aktivieren.
    echo Danach install.bat erneut starten.
    echo.
    pause
    exit /b 1
)

echo [1/4] Python gefunden.
py -3 --version
if errorlevel 1 (
    echo.
    echo [FEHLER] Python 3 konnte nicht gestartet werden.
    pause
    exit /b 1
)

echo.
echo [2/4] Virtuelle Umgebung wird vorbereitet...

if not exist "venv\Scripts\python.exe" (
    py -3 -m venv venv
    if errorlevel 1 (
        echo.
        echo [FEHLER] Die virtuelle Umgebung konnte nicht erstellt werden.
        pause
        exit /b 1
    )
) else (
    echo Virtuelle Umgebung ist bereits vorhanden.
)

echo.
echo [3/4] pip wird aktualisiert...
"venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo.
    echo [FEHLER] pip konnte nicht aktualisiert werden.
    pause
    exit /b 1
)

echo.
echo [4/4] Abhaengigkeiten werden installiert...

if not exist "requirements.txt" (
    echo.
    echo [FEHLER] requirements.txt wurde nicht gefunden.
    pause
    exit /b 1
)

"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [FEHLER] Nicht alle Abhaengigkeiten konnten installiert werden.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo CMDRHelper wurde erfolgreich eingerichtet.
echo.
echo Zum Starten einfach start.bat ausfuehren.
echo ==========================================
echo.
pause
exit /b 0
