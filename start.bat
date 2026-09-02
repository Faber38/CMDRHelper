@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "INSTALL_ROOT=%~dp0"
cd /d "%INSTALL_ROOT%"
if errorlevel 1 (
    echo [FEHLER] Der CMDRHelper-Installationsordner konnte nicht geoeffnet werden: "%INSTALL_ROOT%"
    pause
    exit /b 2
)
set "VENV_PYTHON=%INSTALL_ROOT%venv\Scripts\python.exe"
set "MAIN_PY=%INSTALL_ROOT%main.py"
set "PYTHON_SUPPORT=%INSTALL_ROOT%cmdrhelper\python_support.py"
set "REPAIR_MARKER=%INSTALL_ROOT%backup\update_repair_required.json"
title CMDRHelper
echo CMDRHelper-Installation: "%INSTALL_ROOT%"
if exist "%REPAIR_MARKER%" (
    echo.
    echo ==========================================
    echo Update fehlgeschlagen. Die vorherige Version wurde wiederhergestellt.
    echo Das lokale venv muss repariert werden.
    echo Bitte jetzt "%INSTALL_ROOT%install.bat" ausfuehren.
    echo Update-Log: "%INSTALL_ROOT%backup\update.log"
    echo ==========================================
    pause
    exit /b 20
)
if not exist "%VENV_PYTHON%" goto :venv_error
if not exist "%PYTHON_SUPPORT%" goto :venv_error
"%VENV_PYTHON%" "%PYTHON_SUPPORT%" --check >nul 2>&1
if errorlevel 1 goto :venv_error
"%VENV_PYTHON%" -m pip --version >nul 2>&1
if errorlevel 1 goto :venv_error
if not exist "%MAIN_PY%" (
    echo [FEHLER] main.py wurde nicht in dieser Installation gefunden: "%MAIN_PY%"
    pause
    exit /b 3
)
"%VENV_PYTHON%" "%MAIN_PY%"
set "APP_EXIT=%errorlevel%"
if "%APP_EXIT%"=="0" exit /b 0
echo.
echo ==========================================
echo CMDRHelper wurde mit Exitcode %APP_EXIT% beendet.
echo Installation: "%INSTALL_ROOT%"
echo Die Meldung oben kann bei der Fehlersuche helfen.
echo ==========================================
pause
exit /b %APP_EXIT%
:venv_error
echo.
echo ==========================================
echo [FEHLER] Das lokale CMDRHelper-venv fehlt oder ist nicht startbereit.
echo Bitte "%INSTALL_ROOT%install.bat" zur sicheren Reparatur ausfuehren.
echo Es wird kein Python aus einer anderen Installation verwendet.
echo ==========================================
pause
exit /b 4
