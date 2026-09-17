@echo off
chcp 65001 >nul
SETLOCAL ENABLEDELAYEDEXPANSION
title Open WebUI - One-Click Setup

echo.
echo ============================================================
echo   Open WebUI Custom Fork - One-Click Setup
echo ============================================================
echo.
echo This will install anything missing (Git, Node 22, Python),
echo then set up the project and open http://localhost:8080
echo.
echo Press ENTER to continue, or close this window to cancel.
pause >nul

SET "REPO_URL=https://github.com/az0512124155azz-sys/open-webui.git"
SET "BRANCH=feature/custom-fork-v1"
SET "DIR=%USERPROFILE%\open-webui"

where winget >nul 2>&1
IF ERRORLEVEL 1 (SET "HAS_WINGET=0") ELSE (SET "HAS_WINGET=1")

echo.
echo [Check] Git ...
where git >nul 2>&1
IF ERRORLEVEL 1 (
    echo Git missing - installing automatically...
    IF "!HAS_WINGET!"=="1" (
        winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements --silent
    ) ELSE (
        start "" "https://git-scm.com/download/win"
        echo Install Git, then press ENTER.
        pause >nul
    )
    SET "PATH=%ProgramFiles%\Git\cmd;%ProgramFiles%\Git\bin;%PATH%"
    where git >nul 2>&1
    IF ERRORLEVEL 1 (
        echo [ERROR] Git still missing. Close, install Git, run again.
        pause
        exit /b 1
    )
)
FOR /F "tokens=*" %%v IN ('git --version 2^>nul') DO echo OK: %%v

echo.
echo [Check] Node.js ...
SET "NEED_NODE=0"
where node >nul 2>&1
IF ERRORLEVEL 1 SET "NEED_NODE=1"
IF "!NEED_NODE!"=="0" (
    FOR /F "tokens=*" %%v IN ('node -v 2^>nul') DO SET "NODE_VER=%%v"
    echo Found: !NODE_VER!
    FOR /F "tokens=1 delims=." %%a IN ("!NODE_VER:v=!") DO SET "NODE_MAJOR=%%a"
    IF !NODE_MAJOR! GEQ 23 SET "NEED_NODE=1"
    IF !NODE_MAJOR! LSS 18 SET "NEED_NODE=1"
)
IF "!NEED_NODE!"=="1" (
    echo Installing Node.js 22 automatically...
    IF "!HAS_WINGET!"=="1" (
        winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements --silent
        winget install --id OpenJS.NodeJS.22 -e --accept-source-agreements --accept-package-agreements --silent >nul 2>&1
        SET "PATH=%ProgramFiles%\nodejs;%PATH%"
    ) ELSE (
        start "" "https://nodejs.org/en/download"
        echo Install Node 22 LTS, then press ENTER.
        pause >nul
    )
    where node >nul 2>&1
    IF ERRORLEVEL 1 (
        echo [ERROR] Node still missing. Re-run after install.
        pause
        exit /b 1
    )
)
FOR /F "tokens=*" %%v IN ('node -v 2^>nul') DO echo OK: Node %%v

echo.
echo [Check] Python ...
where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python missing - installing automatically...
    IF "!HAS_WINGET!"=="1" (
        winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements --silent
        SET "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"
    ) ELSE (
        start "" "https://www.python.org/downloads/"
        echo Install Python 3.12 with PATH enabled, then press ENTER.
        pause >nul
    )
    where python >nul 2>&1
    IF ERRORLEVEL 1 (
        echo [ERROR] Python still missing. Re-run after install.
        pause
        exit /b 1
    )
)
FOR /F "tokens=*" %%v IN ('python --version 2^>^&1') DO echo OK: %%v

echo.
echo [Project] ...
IF EXIST "%~dp0backend\open_webui\main.py" (
    cd /d "%~dp0"
    SET "DIR=%CD%"
    echo Using: !DIR!
    GOTO :HAVE_REPO
)
IF EXIST "%DIR%\backend\open_webui\main.py" (
    echo Found: %DIR%
    cd /d "%DIR%"
    GOTO :UPDATE_REPO
)
echo Cloning to %DIR% ...
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
echo Updating...
git fetch origin
git checkout %BRANCH%
git pull origin %BRANCH%

:HAVE_REPO
cd /d "%DIR%"
IF EXIST "INSTALL_WINDOWS.bat" (
    SET "OPENWEBUI_AUTO=1"
    call "INSTALL_WINDOWS.bat"
    exit /b %ERRORLEVEL%
)

echo Minimal install path...
SET /P "ANS=Download heavy packages now? [YES/NO]: "
IF /I "!ANS!"=="YES" GOTO :PIP
IF /I "!ANS!"=="Y" GOTO :PIP
start "" "https://pytorch.org/get-started/locally/"
pause >nul
GOTO :START

:PIP
cd /d "%DIR%\backend"
IF NOT EXIST ".venv\Scripts\python.exe" python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
pip install -r requirements.txt
cd /d "%DIR%"
call npm install
call npm run build

:START
IF EXIST "START_WINDOWS.bat" call "START_WINDOWS.bat"
IF EXIST "backend\start_windows.bat" (
    cd /d "%DIR%\backend"
    IF EXIST ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
    call start_windows.bat
)
ENDLOCAL
