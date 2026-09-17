@echo off
chcp 65001 >nul
SETLOCAL
title Open WebUI - Start
cd /d "%~dp0" || exit /b 1

IF NOT EXIST "backend\start_windows.bat" (
    echo [ERROR] backend\start_windows.bat not found.
    pause
    exit /b 1
)

IF EXIST "backend\.venv\Scripts\activate.bat" (
    call "backend\.venv\Scripts\activate.bat"
) ELSE (
    echo [WARN] No backend\.venv - run INSTALL_WINDOWS.bat first.
)

echo Starting Open WebUI at http://localhost:8080
echo Press Ctrl+C to stop.
call "backend\start_windows.bat"
ENDLOCAL
