@echo off
setlocal
cd /d "%~dp0"

title CMDRHelper - Installation

echo ==========================================
echo        CMDRHelper - Installation
echo ==========================================
echo.

set "PYTHON_CMD="

where py >nul 2>&1
if not errorlevel 1 (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        python --version >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo [FEHLER] Python 3 wurde nicht gefunden.
    echo.
    echo Bitte Python 3 fuer Windows installieren.
    echo CMDRHelper unterstuetzt sowohl "py" als auch "python".
    echo Danach install.bat erneut starten.
    echo.
    pause
    exit /b 1
)

echo [1/4] Python gefunden.
%PYTHON_CMD% --version
if errorlevel 1 (
    echo.
    echo [FEHLER] Python 3 konnte nicht gestartet werden.
    pause
    exit /b 1
)

echo.
echo [2/4] Virtuelle Umgebung wird vorbereitet...

if not exist "venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv venv
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
