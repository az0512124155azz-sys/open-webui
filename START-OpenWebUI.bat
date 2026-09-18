@echo off
chcp 65001 >nul
title Open WebUI - Start
cd /d "%~dp0"

if exist "%USERPROFILE%\open-webui\backend\open_webui\main.py" (
  set "ROOT=%USERPROFILE%\open-webui"
) else if exist "%~dp0backend\open_webui\main.py" (
  set "ROOT=%~dp0"
) else if exist "%~dp0open-webui\backend\open_webui\main.py" (
  set "ROOT=%~dp0open-webui"
) else (
  echo [ERROR] open-webui folder not found.
  pause
  exit /b 1
)

cd /d "%ROOT%"

echo.
echo  ========================================
echo   Open WebUI - One Click Start
echo  ========================================
echo  Project: %ROOT%
echo.

echo [1/4] Stopping old server on port 8080...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
  echo   Killing PID %%p
  taskkill /PID %%p /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

echo [2/4] Activating Python...
if not exist "%ROOT%\backend\.venv\Scripts\activate.bat" (
  echo [ERROR] venv missing. Run setup first.
  pause
  exit /b 1
)
call "%ROOT%\backend\.venv\Scripts\activate.bat"

set "WEBUI_SECRET_KEY=my-fixed-secret-key-do-not-change"
set "OLLAMA_KEEP_ALIVE=24h"
set "OLLAMA_BASE_URL=http://127.0.0.1:11434"
set "OPENAI_API_BASE_URLS=http://127.0.0.1:1234/v1"
set "OPENAI_API_KEYS=bionic"

echo [3/4] Env ready:
echo   Ollama:  %OLLAMA_BASE_URL%
echo   Bionic:  %OPENAI_API_BASE_URLS%
echo.

echo [4/4] Starting server + browser...
start "" cmd /c "timeout /t 4 /nobreak >nul & start http://localhost:8080"

cd /d "%ROOT%\backend"
echo.
echo  Keep this window OPEN while using the site.
echo  URL: http://localhost:8080
echo  Press Ctrl+C to stop.
echo.

uvicorn open_webui.main:app --host 0.0.0.0 --port 8080

echo.
echo Server stopped.
pause
