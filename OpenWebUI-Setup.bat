@echo off
chcp 65001 >nul 2>&1
SETLOCAL ENABLEDELAYEDEXPANSION
title Open WebUI Setup

if not defined OPENWEBUI_INNER (
  set OPENWEBUI_INNER=1
  cmd /k "%~f0"
  exit /b
)

cd /d "%~dp0" 2>nul
SET "LOG=%USERPROFILE%\open-webui-setup-log.txt"
SET "REPO_URL=https://github.com/az0512124155azz-sys/open-webui.git"
SET "BRANCH=feature/custom-fork-v1"
SET "DIR=%USERPROFILE%\open-webui"

echo ===== %DATE% %TIME% =====> "%LOG%"

cls
echo.
echo  ========================================
echo   Open WebUI - Quiet Setup
echo  ========================================
echo.
echo  Log: %LOG%
echo  Window stays open until you close it.
echo.
echo  Press ENTER to start...
pause >nul

SET "WINGET_OPTS=--accept-source-agreements --accept-package-agreements --disable-interactivity --silent"

where winget >nul 2>&1
IF ERRORLEVEL 1 (SET "HAS_WINGET=0") ELSE (SET "HAS_WINGET=1")

echo.
echo  [1/7] Git...
where git >nul 2>&1
IF ERRORLEVEL 1 (
    IF "!HAS_WINGET!"=="1" (
        winget install --id Git.Git -e %WINGET_OPTS% >nul 2>&1
    ) ELSE (
        start "" "https://git-scm.com/download/win"
        echo  Install Git, then press ENTER.
        pause >nul
    )
    SET "PATH=%ProgramFiles%\Git\cmd;%ProgramFiles%\Git\bin;%PATH%"
)
where git >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [FAILED] Git not found. Install from https://git-scm.com/download/win
    echo ERROR Git>> "%LOG%"
    goto :DONE
)
echo  [OK] Git

echo  [2/7] Node.js 22...
SET "NEED_NODE=0"
where node >nul 2>&1
IF ERRORLEVEL 1 SET "NEED_NODE=1"
IF "!NEED_NODE!"=="0" (
    FOR /F "tokens=*" %%v IN ('node -v 2^>nul') DO SET "NODE_VER=%%v"
    FOR /F "tokens=1 delims=." %%a IN ("!NODE_VER:v=!") DO SET "NODE_MAJOR=%%a"
    IF !NODE_MAJOR! GEQ 23 SET "NEED_NODE=1"
    IF !NODE_MAJOR! LSS 18 SET "NEED_NODE=1"
)
IF "!NEED_NODE!"=="1" (
    IF "!HAS_WINGET!"=="1" (
        winget install --id OpenJS.NodeJS.LTS -e %WINGET_OPTS% >nul 2>&1
        winget install --id OpenJS.NodeJS.22 -e %WINGET_OPTS% >nul 2>&1
        SET "PATH=%ProgramFiles%\nodejs;%PATH%"
    ) ELSE (
        start "" "https://nodejs.org/en/download"
        echo  Install Node 22 LTS, then press ENTER.
        pause >nul
    )
)
where node >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [FAILED] Node not found. Install Node 22 from https://nodejs.org
    echo ERROR Node>> "%LOG%"
    goto :DONE
)
echo  [OK] Node

echo  [3/7] Python...
where python >nul 2>&1
IF ERRORLEVEL 1 (
    IF "!HAS_WINGET!"=="1" (
        winget install --id Python.Python.3.12 -e %WINGET_OPTS% >nul 2>&1
        SET "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"
    ) ELSE (
        start "" "https://www.python.org/downloads/"
        echo  Install Python 3.12 with PATH, then press ENTER.
        pause >nul
    )
)
where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [FAILED] Python not found.
    echo ERROR Python>> "%LOG%"
    goto :DONE
)
echo  [OK] Python

echo  [4/7] Project files...
IF EXIST "%~dp0backend\open_webui\main.py" (
    cd /d "%~dp0"
    SET "DIR=%CD%"
    GOTO :REPO_OK
)
IF EXIST "%DIR%\backend\open_webui\main.py" (
    cd /d "%DIR%"
    git fetch origin >nul 2>&1
    git checkout %BRANCH% >nul 2>&1
    git pull origin %BRANCH% >nul 2>&1
    GOTO :REPO_OK
)
git clone -b %BRANCH% "%REPO_URL%" "%DIR%" >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [FAILED] Could not download project. Check internet.
    echo ERROR clone>> "%LOG%"
    goto :DONE
)
cd /d "%DIR%"

:REPO_OK
cd /d "%DIR%"
echo  [OK] Project

echo  [5/7] Frontend packages (quiet)...
call npm install --no-fund --no-audit --loglevel=error >nul 2>&1
IF ERRORLEVEL 1 call npm install --engine-strict=false --no-fund --no-audit --loglevel=error >nul 2>&1
call npm run build >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [WARN] UI build skipped - site API may still work
    echo WARN build>> "%LOG%"
) ELSE (
    echo  [OK] Frontend
)

echo  [6/7] Backend packages (quiet, may take 10-30 min)...
cd /d "%DIR%\backend"
IF NOT EXIST ".venv\Scripts\python.exe" python -m venv .venv >nul 2>&1
call ".venv\Scripts\activate.bat" >nul 2>&1
python -m pip install -U pip -q >nul 2>&1
pip install -r requirements.txt -q --disable-pip-version-check >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [WARN] Some Python packages failed - see log
    echo WARN pip>> "%LOG%"
) ELSE (
    echo  [OK] Backend
)

echo  [7/7] Starting server...
echo.
echo  ========================================
echo   Open:  http://localhost:8080
echo   Keep this window OPEN while using the site.
echo  ========================================
echo.

SET "WEBUI_SECRET_KEY=local-dev-secret-change-me-12345"
IF EXIST "start_windows.bat" (
    call start_windows.bat
) ELSE (
    uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 2>nul
)

:DONE
echo.
echo  Finished. Log: %LOG%
echo  Press ENTER to close.
pause >nul
ENDLOCAL
