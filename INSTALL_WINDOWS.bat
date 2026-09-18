@echo off
chcp 65001 >nul
SETLOCAL ENABLEDELAYEDEXPANSION
title Open WebUI - Installer
cd /d "%~dp0" || exit /b 1

echo.
echo ============================================================
echo   Open WebUI - Windows Installer
echo ============================================================
echo.

where winget >nul 2>&1
IF ERRORLEVEL 1 (SET "HAS_WINGET=0") ELSE (SET "HAS_WINGET=1")

echo [1/5] Node.js
SET "NEED_NODE=0"
where node >nul 2>&1
IF ERRORLEVEL 1 SET "NEED_NODE=1"
IF "!NEED_NODE!"=="0" (
    FOR /F "tokens=*" %%v IN ('node -v 2^>nul') DO SET "NODE_VER=%%v"
    FOR /F "tokens=1 delims=." %%a IN ("!NODE_VER:v=!") DO SET "NODE_MAJOR=%%a"
    IF !NODE_MAJOR! GEQ 23 SET "NEED_NODE=1"
    IF !NODE_MAJOR! LSS 18 SET "NEED_NODE=1"
    IF "!NEED_NODE!"=="0" echo OK: !NODE_VER!
)
IF "!NEED_NODE!"=="1" (
    echo Installing Node 22...
    IF "!HAS_WINGET!"=="1" (
        winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements --silent
        winget install --id OpenJS.NodeJS.22 -e --accept-source-agreements --accept-package-agreements --silent >nul 2>&1
        SET "PATH=%ProgramFiles%\nodejs;%PATH%"
    ) ELSE (
        start "" "https://nodejs.org/en/download"
        echo Install Node 22, press ENTER.
        pause >nul
    )
)
FOR /F "tokens=*" %%v IN ('node -v 2^>nul') DO echo Node: %%v

echo [2/5] Python
where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo Installing Python 3.12...
    IF "!HAS_WINGET!"=="1" (
        winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements --silent
        SET "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"
    ) ELSE (
        start "" "https://www.python.org/downloads/"
        pause >nul
    )
)
FOR /F "tokens=*" %%v IN ('python --version 2^>^&1') DO echo %%v

echo [3/5] Frontend
IF /I "%OPENWEBUI_AUTO%"=="1" (SET "ANS_NPM=YES") ELSE (SET /P "ANS_NPM=npm install+build? [YES/NO]: ")
IF /I "!ANS_NPM!"=="YES" GOTO :NPM
IF /I "!ANS_NPM!"=="Y" GOTO :NPM
GOTO :BE
:NPM
call npm install
IF ERRORLEVEL 1 call npm install --engine-strict=false
call npm run build

:BE
echo [4/5] Backend pip (may be 1-3 GB)
IF /I "%OPENWEBUI_AUTO%"=="1" (SET "ANS_PIP=YES") ELSE (
    echo YES=auto  NO=manual then ENTER
    SET /P "ANS_PIP=pip install now? [YES/NO]: "
)
cd /d "%~dp0backend" || exit /b 1
IF NOT EXIST ".venv\Scripts\python.exe" python -m venv .venv
call ".venv\Scripts\activate.bat"
IF /I "!ANS_PIP!"=="YES" GOTO :PIP
IF /I "!ANS_PIP!"=="Y" GOTO :PIP
start "" "https://pytorch.org/get-started/locally/"
pause >nul
GOTO :ST
:PIP
python -m pip install -U pip
pip install -r requirements.txt

:ST
echo [5/5] Start?
IF /I "%OPENWEBUI_AUTO%"=="1" (SET "ANS_START=YES") ELSE (SET /P "ANS_START=Start 8080? [YES/NO]: ")
IF /I NOT "!ANS_START!"=="YES" IF /I NOT "!ANS_START!"=="Y" (
    echo Later: START_WINDOWS.bat
    pause
    exit /b 0
)
echo http://localhost:8080
call "%~dp0backend\start_windows.bat"
ENDLOCAL
