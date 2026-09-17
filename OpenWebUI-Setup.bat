@echo off
chcp 65001 >nul
SETLOCAL ENABLEDELAYEDEXPANSION
title Open WebUI - One-Click Setup

echo.
echo ============================================================
echo   Open WebUI Custom Fork - One-Click Setup
echo ============================================================
echo.
echo This will:
echo   - Find or download the project
echo   - Check Node.js 22 and Python
echo   - Install packages (asks YES/NO before big downloads)
echo   - Start the website at http://localhost:8080
echo.
echo Press ENTER to continue, or close this window to cancel.
pause >nul

SET "REPO_URL=https://github.com/az0512124155azz-sys/open-webui.git"
SET "BRANCH=feature/custom-fork-v1"
SET "DIR=%USERPROFILE%\open-webui"

IF EXIST "%~dp0backend\open_webui\main.py" (
    cd /d "%~dp0"
    SET "DIR=%CD%"
    echo Using project folder: !DIR!
    GOTO :HAVE_REPO
)

IF EXIST "%DIR%\backend\open_webui\main.py" (
    echo Found existing project: %DIR%
    cd /d "%DIR%"
    GOTO :UPDATE_REPO
)

echo Project not found. Cloning to: %DIR%
where git >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Git is not installed.
    start "" "https://git-scm.com/download/win"
    echo Install Git, then run this file again.
    pause
    exit /b 1
)

git clone -b %BRANCH% "%REPO_URL%" "%DIR%"
IF ERRORLEVEL 1 (
    echo Clone failed.
    pause
    exit /b 1
)
cd /d "%DIR%"
GOTO :HAVE_REPO

:UPDATE_REPO
cd /d "%DIR%"
echo Updating project from GitHub...
git fetch origin
git checkout %BRANCH%
git pull origin %BRANCH%
GOTO :HAVE_REPO

:HAVE_REPO
cd /d "%DIR%"

IF EXIST "INSTALL_WINDOWS.bat" (
    echo Running INSTALL_WINDOWS.bat ...
    call "INSTALL_WINDOWS.bat"
    exit /b %ERRORLEVEL%
)

echo INSTALL_WINDOWS.bat missing - minimal setup...
where node >nul 2>&1 || (start "" "https://nodejs.org/en/download" & echo Install Node 22 & pause & exit /b 1)
where python >nul 2>&1 || (start "" "https://www.python.org/downloads/" & echo Install Python & pause & exit /b 1)

SET /P "ANS=Download heavy packages now? [YES/NO]: "
IF /I "!ANS!"=="YES" GOTO :MIN_PIP
IF /I "!ANS!"=="Y" GOTO :MIN_PIP
start "" "https://pytorch.org/get-started/locally/"
echo Press ENTER after manual install.
pause >nul
GOTO :MIN_START

:MIN_PIP
cd /d "%DIR%\backend"
IF NOT EXIST ".venv\Scripts\python.exe" python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
pip install -r requirements.txt
cd /d "%DIR%"
call npm install
call npm run build

:MIN_START
IF EXIST "START_WINDOWS.bat" (call "START_WINDOWS.bat") ELSE IF EXIST "backend\start_windows.bat" (call "backend\start_windows.bat")
ENDLOCAL
