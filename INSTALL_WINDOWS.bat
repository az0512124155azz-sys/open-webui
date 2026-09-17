@echo off
chcp 65001 >nul
SETLOCAL ENABLEDELAYEDEXPANSION
title Open WebUI - Custom Fork Installer (Windows)

cd /d "%~dp0" || exit /b 1

echo.
echo ============================================================
echo   Open WebUI Custom Fork - Windows Installer
echo ============================================================
echo.
echo This script will:
echo   1. Check Node.js and Python
echo   2. Install frontend packages (npm)
echo   3. Install backend packages (pip) - can be LARGE
echo   4. Build the UI
echo.
echo Press ENTER to start, or close this window to cancel.
pause >nul

echo.
echo [1/5] Checking Node.js ...
where node >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Node.js is not installed.
    echo Download Node.js 22 LTS: https://nodejs.org/en/download
    start "" "https://nodejs.org/en/download"
    pause
    exit /b 1
)

FOR /F "tokens=*" %%v IN ('node -v 2^>nul') DO SET "NODE_VER=%%v"
echo Found Node: !NODE_VER!
SET "NODE_MAJOR="
FOR /F "tokens=1 delims=." %%a IN ("!NODE_VER:v=!") DO SET "NODE_MAJOR=%%a"

IF NOT "!NODE_MAJOR!"=="" (
    IF !NODE_MAJOR! GEQ 23 (
        echo [ERROR] Node !NODE_VER! is too new. Need 18.13-22.x only.
        echo Opening https://nodejs.org/en/download
        start "" "https://nodejs.org/en/download"
        echo After installing Node 22, press ENTER to re-check.
        pause >nul
        FOR /F "tokens=*" %%v IN ('node -v 2^>nul') DO SET "NODE_VER=%%v"
        FOR /F "tokens=1 delims=." %%a IN ("!NODE_VER:v=!") DO SET "NODE_MAJOR=%%a"
        IF !NODE_MAJOR! GEQ 23 (
            echo Still on Node !NODE_VER!. Stopping.
            pause
            exit /b 1
        )
    )
    IF !NODE_MAJOR! LSS 18 (
        echo [ERROR] Node too old. Need 18.13+.
        start "" "https://nodejs.org/en/download"
        pause
        exit /b 1
    )
)
echo Node version OK.

echo.
echo [2/5] Checking Python ...
where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found. Install 3.11/3.12 from https://www.python.org/downloads/
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)
FOR /F "tokens=*" %%v IN ('python --version 2^>^&1') DO echo Found: %%v

echo.
echo [3/5] Frontend - npm install
echo Type YES to continue automatic download, or NO to skip.
SET /P "ANS_NPM=Continue npm install? [YES/NO]: "
IF /I NOT "!ANS_NPM!"=="YES" IF /I NOT "!ANS_NPM!"=="Y" (
    echo Skipped npm install.
    goto :BACKEND_SECTION
)

call npm install
IF ERRORLEVEL 1 (
    SET /P "ANS_RETRY=Try npm install --engine-strict=false? [YES/NO]: "
    IF /I "!ANS_RETRY!"=="YES" call npm install --engine-strict=false
    IF /I "!ANS_RETRY!"=="Y" call npm install --engine-strict=false
)

echo Building frontend...
call npm run build
IF ERRORLEVEL 1 echo [WARN] Frontend build failed. Backend may still run.

:BACKEND_SECTION
echo.
echo [4/5] Backend - Python packages
echo WARNING: may download 1-3 GB (PyTorch etc).
echo   YES = automatic download in this terminal
echo   NO  = stop, open manual guide, then press ENTER when done
SET /P "ANS_PIP=Download heavy Python packages now? [YES/NO]: "

cd /d "%~dp0backend" || (echo backend folder not found & pause & exit /b 1)

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo Creating .venv ...
    python -m venv .venv
)
call ".venv\Scripts\activate.bat"

IF /I "!ANS_PIP!"=="YES" GOTO :PIP_AUTO
IF /I "!ANS_PIP!"=="Y" GOTO :PIP_AUTO

echo.
echo Manual install:
echo   cd /d "%CD%"
echo   .venv\Scripts\activate
echo   python -m pip install -U pip
echo   pip install -r requirements.txt
echo.
echo Torch guide: https://pytorch.org/get-started/locally/
start "" "https://pytorch.org/get-started/locally/"
echo.
echo When manual install is DONE, press ENTER to continue.
pause >nul
GOTO :START_SERVER

:PIP_AUTO
echo Installing pip packages (long)...
python -m pip install -U pip
pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo pip failed. Try manual: https://pytorch.org/get-started/locally/
    pause
    exit /b 1
)

:START_SERVER
echo.
echo [5/5] Start server?
SET /P "ANS_START=Start Open WebUI on port 8080? [YES/NO]: "
IF /I NOT "!ANS_START!"=="YES" IF /I NOT "!ANS_START!"=="Y" (
    echo Later run: START_WINDOWS.bat
    pause
    exit /b 0
)
echo Open http://localhost:8080
call "%~dp0backend\start_windows.bat"
ENDLOCAL
