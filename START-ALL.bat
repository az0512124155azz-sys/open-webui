@echo off
chcp 65001 >nul
setlocal EnableExtensions
title Open WebUI - Start All
cd /d "%~dp0"

set "LOG=%USERPROFILE%\open-webui-start-log.txt"
echo ===== START %DATE% %TIME% ===== > "%LOG%"

echo.
echo  ========================================
echo   Open WebUI - ONE CLICK START
echo   Log: %LOG%
echo  ========================================
echo.

set "ROOT="
if exist "%USERPROFILE%\open-webui\backend\open_webui\main.py" set "ROOT=%USERPROFILE%\open-webui"
if not defined ROOT if exist "%~dp0backend\open_webui\main.py" set "ROOT=%~dp0"
if not defined ROOT if exist "%~dp0open-webui\backend\open_webui\main.py" set "ROOT=%~dp0open-webui"

if not defined ROOT (
  echo [ERROR] open-webui folder not found.
  echo Put this BAT in C:\Users\%USERNAME%\ or inside open-webui
  goto :hold
)

cd /d "%ROOT%"
echo ROOT=%ROOT%
echo ROOT=%ROOT% >> "%LOG%"

echo [1/5] Kill port 8080...
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8080" ^| findstr "LISTENING"') do (
  echo   PID %%p
  taskkill /PID %%p /F >> "%LOG%" 2>&1
)
timeout /t 2 /nobreak >nul

echo [2/5] Git update optional...
where git >nul 2>&1
if %ERRORLEVEL%==0 (
  git fetch origin feature/custom-fork-v1 >> "%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- backend/open_webui/utils/seed_default_skills.py >> "%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- src/custom-fork-theme.css >> "%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- plugins/github_tool.py >> "%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- plugins/3d_builder_tool.py >> "%LOG%" 2>&1
  echo   git done
) else (
  echo   git skip
)

echo [3/5] Theme import...
if exist "%ROOT%\src\app.css" (
  findstr /C:"custom-fork-theme.css" "%ROOT%\src\app.css" >nul 2>&1
  if errorlevel 1 (
    echo @import './custom-fork-theme.css';> "%TEMP%\owui-theme-line.txt"
    copy /y "%TEMP%\owui-theme-line.txt"+"%ROOT%\src\app.css" "%TEMP%\owui-app.css" >nul
    copy /y "%TEMP%\owui-app.css" "%ROOT%\src\app.css" >nul
    echo   import added
  ) else (
    echo   import ok
  )
)

echo [4/5] Check venv...
if not exist "%ROOT%\backend\.venv\Scripts\activate.bat" (
  echo [ERROR] venv missing
  goto :hold
)
if not exist "%ROOT%\build\index.html" (
  echo   npm run build...
  call npm run build >> "%LOG%" 2>&1
)

echo [5/5] Start server...
call "%ROOT%\backend\.venv\Scripts\activate.bat"
set "WEBUI_SECRET_KEY=my-fixed-secret-key-do-not-change"
set "OLLAMA_KEEP_ALIVE=24h"
set "OLLAMA_BASE_URL=http://127.0.0.1:11434"
set "OPENAI_API_BASE_URLS=http://127.0.0.1:1234/v1"
set "OPENAI_API_KEYS=bionic"

where uvicorn >nul 2>&1
if errorlevel 1 (
  echo [ERROR] uvicorn not found in venv
  goto :hold
)

start "" cmd /c "timeout /t 6 /nobreak >nul & start http://localhost:8080"
cd /d "%ROOT%\backend"
echo.
echo   http://localhost:8080
echo   Keep window OPEN
echo.
uvicorn open_webui.main:app --host 0.0.0.0 --port 8080
echo uvicorn exit %ERRORLEVEL% >> "%LOG%"

:hold
echo.
echo Press any key to close...
pause >nul
endlocal
