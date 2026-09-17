@echo off
chcp 65001 >nul
SETLOCAL ENABLEDELAYEDEXPANSION
title Open WebUI - One-Click Setup

if not defined OPENWEBUI_INNER (
  set OPENWEBUI_INNER=1
  cmd /k "%~f0"
  exit /b
)

cd /d "%~dp0" 2>nul
SET "LOG=%USERPROFILE%\open-webui-setup-log.txt"
echo ===== Open WebUI Setup %DATE% %TIME% =====> "%LOG%"
echo Log file: %LOG%
echo.

echo ============================================================
echo   Open WebUI Custom Fork - One-Click Setup
echo ============================================================
echo.
echo Window stays open. Log is saved to:
echo   %LOG%
echo.
echo Press ENTER to continue.
pause >nul

SET "REPO_URL=https://github.com/az0512124155azz-sys/open-webui.git"
SET "BRANCH=feature/custom-fork-v1"
SET "DIR=%USERPROFILE%\open-webui"

where winget >nul 2>&1
IF ERRORLEVEL 1 (SET "HAS_WINGET=0") ELSE (SET "HAS_WINGET=1")
echo HAS_WINGET=!HAS_WINGET! >> "%LOG%"

echo.
echo [1] Git
where git >nul 2>&1
IF ERRORLEVEL 1 (
    echo Git missing - trying auto install...
    echo Installing Git... >> "%LOG%"
    IF "!HAS_WINGET!"=="1" (
        winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
        echo winget Git exit=!ERRORLEVEL! >> "%LOG%"
    ) ELSE (
        start "" "https://git-scm.com/download/win"
        echo Install Git from browser, then press ENTER here.
        pause >nul
    )
    SET "PATH=%ProgramFiles%\Git\cmd;%ProgramFiles%\Git\bin;%PATH%"
)
where git >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Git still not found.
    echo ERROR Git >> "%LOG%"
    goto :FAIL
)
FOR /F "tokens=*" %%v IN ('git --version 2^>nul') DO (echo OK %%v & echo OK %%v >> "%LOG%")

echo.
echo [2] Node.js
SET "NEED_NODE=0"
where node >nul 2>&1
IF ERRORLEVEL 1 SET "NEED_NODE=1"
IF "!NEED_NODE!"=="0" (
    FOR /F "tokens=*" %%v IN ('node -v 2^>nul') DO SET "NODE_VER=%%v"
    echo Found !NODE_VER!
    FOR /F "tokens=1 delims=." %%a IN ("!NODE_VER:v=!") DO SET "NODE_MAJOR=%%a"
    IF !NODE_MAJOR! GEQ 23 SET "NEED_NODE=1"
    IF !NODE_MAJOR! LSS 18 SET "NEED_NODE=1"
)
IF "!NEED_NODE!"=="1" (
    echo Installing Node.js 22... warnings from winget are often OK.
    echo Installing Node... >> "%LOG%"
    IF "!HAS_WINGET!"=="1" (
        winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
        echo winget Node exit=!ERRORLEVEL! >> "%LOG%"
        SET "PATH=%ProgramFiles%\nodejs;%PATH%"
    ) ELSE (
        start "" "https://nodejs.org/en/download"
        echo Install Node 22 LTS, then press ENTER.
        pause >nul
    )
)
where node >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Node not found.
    echo ERROR Node >> "%LOG%"
    goto :FAIL
)
FOR /F "tokens=*" %%v IN ('node -v 2^>nul') DO (echo OK Node %%v & echo OK Node %%v >> "%LOG%")

echo.
echo [3] Python
where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo Installing Python 3.12... warnings from winget are often OK.
    echo Installing Python... >> "%LOG%"
    IF "!HAS_WINGET!"=="1" (
        winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
        echo winget Python exit=!ERRORLEVEL! >> "%LOG%"
        SET "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"
    ) ELSE (
        start "" "https://www.python.org/downloads/"
        echo Install Python with PATH, then press ENTER.
        pause >nul
    )
)
where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found.
    echo ERROR Python >> "%LOG%"
    goto :FAIL
)
FOR /F "tokens=*" %%v IN ('python --version 2^>^&1') DO (echo OK %%v & echo OK %%v >> "%LOG%")

echo.
echo [4] Project folder
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
echo Cloning...
git clone -b %BRANCH% "%REPO_URL%" "%DIR%" >> "%LOG%" 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] git clone failed. See log.
    goto :FAIL
)
cd /d "%DIR%"
GOTO :HAVE_REPO

:UPDATE_REPO
cd /d "%DIR%"
echo Updating...
git fetch origin >> "%LOG%" 2>&1
git checkout %BRANCH% >> "%LOG%" 2>&1
git pull origin %BRANCH% >> "%LOG%" 2>&1

:HAVE_REPO
cd /d "%DIR%"
echo Project: %CD%
echo Project: %CD% >> "%LOG%"

echo.
echo [5] npm install + build
call npm install >> "%LOG%" 2>&1
IF ERRORLEVEL 1 (
    echo npm install had errors - retrying without engine strict...
    call npm install --engine-strict=false >> "%LOG%" 2>&1
)
call npm run build >> "%LOG%" 2>&1
IF ERRORLEVEL 1 (
    echo [WARN] Frontend build failed. Continuing with backend. See log.
    echo WARN build failed >> "%LOG%"
)

echo.
echo [6] Python packages - this can take a long time (1-3 GB)
echo     Warnings during pip are often normal.
echo.
echo Type YES to download now, or NO to skip and do it later.
SET /P "ANS=pip install now? [YES/NO]: "
cd /d "%DIR%\backend"
IF NOT EXIST ".venv\Scripts\python.exe" (
    echo Creating venv...
    python -m venv .venv >> "%LOG%" 2>&1
)
call ".venv\Scripts\activate.bat"

IF /I "!ANS!"=="YES" GOTO :PIP
IF /I "!ANS!"=="Y" GOTO :PIP
echo Skipped pip. You can run later: pip install -r requirements.txt
GOTO :START_Q

:PIP
echo Installing requirements... (do not close this window)
python -m pip install -U pip >> "%LOG%" 2>&1
pip install -r requirements.txt >> "%LOG%" 2>&1
IF ERRORLEVEL 1 (
    echo [WARN] Some pip packages failed. Check %LOG%
    echo WARN pip >> "%LOG%"
) ELSE (
    echo pip OK
)

:START_Q
echo.
echo [7] Start server?
SET /P "ANS2=Start http://localhost:8080 now? [YES/NO]: "
IF /I NOT "!ANS2!"=="YES" IF /I NOT "!ANS2!"=="Y" (
    echo Done. Later run START_WINDOWS.bat from the project folder.
    echo Log: %LOG%
    goto :END
)

echo Starting server... Keep this window OPEN while using the site.
echo Browser: http://localhost:8080
echo.
IF EXIST "%DIR%\backend\start_windows.bat" (
    cd /d "%DIR%\backend"
    IF EXIST ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
    call start_windows.bat
) ELSE (
    SET "WEBUI_SECRET_KEY=local-dev-secret-change-me-12345"
    cd /d "%DIR%\backend"
    IF EXIST ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
    uvicorn open_webui.main:app --host 0.0.0.0 --port 8080
)
goto :END

:FAIL
echo.
echo ========== FAILED ==========
echo Read the messages above and the log:
echo   %LOG%
echo.
type "%LOG%"
echo.
pause
goto :END

:END
echo.
echo ========== Script finished ==========
echo Log saved to: %LOG%
echo Window stays open. You can close it manually.
pause
ENDLOCAL
