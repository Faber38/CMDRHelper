@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "INSTALL_ROOT=%~dp0"
cd /d "%INSTALL_ROOT%"
if errorlevel 1 (
    echo [FEHLER] Der CMDRHelper-Installationsordner konnte nicht geoeffnet werden: "%INSTALL_ROOT%"
    pause
    exit /b 2
)
set "VENV_DIR=%INSTALL_ROOT%venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "REQUIREMENTS=%INSTALL_ROOT%requirements.txt"
set "PYTHON_SUPPORT=%INSTALL_ROOT%cmdrhelper\python_support.py"
set "REPAIR_MARKER=%INSTALL_ROOT%backup\update_repair_required.json"
title CMDRHelper - Installation
echo ==========================================
echo        CMDRHelper - Installation
echo ==========================================
echo Installationsordner: "%INSTALL_ROOT%"
echo.
if not exist "%PYTHON_SUPPORT%" (
    echo [FEHLER] Die Python-Kompatibilitaetspruefung fehlt: "%PYTHON_SUPPORT%"
    pause
    exit /b 3
)
set "PYTHON_CMD="
where py >nul 2>&1
if not errorlevel 1 (
    py -3.13 "%PYTHON_SUPPORT%" --check >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.13"
)
if not defined PYTHON_CMD (
    py -3.12 "%PYTHON_SUPPORT%" --check >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)
if not defined PYTHON_CMD (
    py -3.11 "%PYTHON_SUPPORT%" --check >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.11"
)
if not defined PYTHON_CMD (
    py -3.10 "%PYTHON_SUPPORT%" --check >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.10"
)
if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        python "%PYTHON_SUPPORT%" --check >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)
if not defined PYTHON_CMD (
    echo [FEHLER] Keine unterstuetzte Python-Version wurde gefunden.
    echo Unterstuetzt: Python 3.10 bis 3.13 ^(64-Bit empfohlen^).
    echo Bitte eine passende Python-Version installieren und install.bat erneut starten.
    pause
    exit /b 10
)
echo [1/5] Verwendeter Python-Interpreter:
%PYTHON_CMD% -c "import sys; print(sys.executable); print(sys.version)"
if errorlevel 1 (
    echo [FEHLER] Der ausgewaehlte Python-Interpreter konnte nicht gestartet werden.
    pause
    exit /b 11
)
echo.
echo [2/5] Lokale virtuelle Umgebung wird geprueft...
set "REBUILD_VENV=0"
if exist "%REPAIR_MARKER%" set "REBUILD_VENV=1"
if not exist "%VENV_PYTHON%" set "REBUILD_VENV=1"
if "%REBUILD_VENV%"=="0" (
    "%VENV_PYTHON%" "%PYTHON_SUPPORT%" --check >nul 2>&1
    if errorlevel 1 set "REBUILD_VENV=1"
)
if "%REBUILD_VENV%"=="0" (
    "%VENV_PYTHON%" -m pip --version >nul 2>&1
    if errorlevel 1 set "REBUILD_VENV=1"
)
if "%REBUILD_VENV%"=="1" (
    echo Das ausschliesslich lokale venv ist fehlend, defekt oder inkompatibel.
    echo Es wird neu erstellt. data und persoenliche Dateien bleiben unangetastet.
    if exist "%VENV_DIR%" (
        if /I not "%VENV_DIR%"=="%INSTALL_ROOT%venv" (
            echo [FEHLER] Unsicheres venv-Ziel. Reparatur wurde abgebrochen.
            pause
            exit /b 12
        )
        fsutil reparsepoint query "%VENV_DIR%" >nul 2>&1
        if not errorlevel 1 (
            echo [FEHLER] Das lokale venv ist ein Link/Reparse-Point.
            echo Aus Sicherheitsgruenden wird kein verknuepftes Verzeichnis geloescht.
            pause
            exit /b 12
        )
        rmdir /s /q "%VENV_DIR%"
        if exist "%VENV_DIR%" (
            echo [FEHLER] Das lokale venv konnte nicht entfernt werden.
            pause
            exit /b 13
        )
    )
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [FEHLER] Das lokale venv konnte nicht erstellt werden.
        pause
        exit /b 14
    )
) else (
    echo Das lokale venv ist gesund und wird weiterverwendet.
)
echo.
echo [3/5] Lokaler venv-Interpreter:
"%VENV_PYTHON%" -c "import sys; print(sys.executable); print(sys.version)"
if errorlevel 1 (
    echo [FEHLER] Der lokale venv-Interpreter ist nicht startbar.
    pause
    exit /b 15
)
echo.
echo [4/5] pip wird aktualisiert...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 (
    echo [FEHLER] pip konnte im lokalen venv nicht aktualisiert werden.
    pause
    exit /b 16
)
if not exist "%REQUIREMENTS%" (
    echo [FEHLER] requirements.txt wurde nicht gefunden: "%REQUIREMENTS%"
    pause
    exit /b 17
)
echo.
echo [5/5] Abhaengigkeiten werden im lokalen venv installiert...
"%VENV_PYTHON%" -m pip install -r "%REQUIREMENTS%"
if errorlevel 1 (
    echo [FEHLER] Nicht alle Abhaengigkeiten konnten installiert werden.
    pause
    exit /b 18
)
if exist "%REPAIR_MARKER%" del /f /q "%REPAIR_MARKER%" >nul 2>&1
echo.
echo ==========================================
echo CMDRHelper wurde erfolgreich eingerichtet.
echo Start: "%INSTALL_ROOT%start.bat"
echo ==========================================
pause
exit /b 0
