@echo off
chcp 65001 >nul
setlocal EnableExtensions
title Open WebUI - Full Start
cd /d "%~dp0"

set "LOG=%USERPROFILE%\open-webui-start-log.txt"
echo ===== %DATE% %TIME% ===== > "%LOG%"
echo.
echo  ========================================
echo   Open WebUI - FULL SYSTEM START
echo   Log: %LOG%
echo  ========================================
echo.

set "ROOT="
if exist "%USERPROFILE%\open-webui\backend\open_webui\main.py" set "ROOT=%USERPROFILE%\open-webui"
if not defined ROOT if exist "%~dp0backend\open_webui\main.py" set "ROOT=%~dp0"
if not defined ROOT if exist "%~dp0open-webui\backend\open_webui\main.py" set "ROOT=%~dp0open-webui"

if not defined ROOT (
  echo [ERROR] open-webui not found.
  goto HOLD
)

cd /d "%ROOT%"
echo Project: %ROOT%

echo [1/7] Stop port 8080...
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8080" ^| findstr "LISTENING"') do taskkill /PID %%p /F >>"%LOG%" 2>&1
timeout /t 2 /nobreak >nul

echo [2/7] Git sync...
where git >nul 2>&1
if %ERRORLEVEL%==0 (
  git fetch origin feature/custom-fork-v1 >>"%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- src/tailwind.css >>"%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- src/custom-fork-theme.css >>"%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- backend/open_webui/static/custom.css >>"%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- backend/open_webui/utils/seed_default_skills.py >>"%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- scripts/patch_middleware_skills.py >>"%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- plugins/github_tool.py >>"%LOG%" 2>&1
  git checkout origin/feature/custom-fork-v1 -- plugins/3d_builder_tool.py >>"%LOG%" 2>&1
)

echo [3/7] Theme custom.css...
if not exist "%ROOT%\backend\open_webui\static" mkdir "%ROOT%\backend\open_webui\static"
(echo html.dark body { background-color: #212121 !important; }&echo html.dark #sidebar, html.dark aside { background-color: #171717 !important; }&echo html.dark body::before { content: ""; position: fixed; top: 0; left: 0; right: 0; height: 3px; background: #10a37f; z-index: 99999; pointer-events: none; }) > "%ROOT%\backend\open_webui\static\custom.css"

echo [4/7] Patch skills...
if exist "%ROOT%\scripts\patch_middleware_skills.py" python "%ROOT%\scripts\patch_middleware_skills.py" >>"%LOG%" 2>&1

echo [5/7] Venv...
if not exist "%ROOT%\backend\.venv\Scripts\activate.bat" (
  echo [ERROR] venv missing
  goto HOLD
)
call "%ROOT%\backend\.venv\Scripts\activate.bat"

echo [6/7] Build check...
if not exist "%ROOT%\build\index.html" call npm run build >>"%LOG%" 2>&1

echo [7/7] Start...
where uvicorn >nul 2>&1
if errorlevel 1 (
  echo [ERROR] uvicorn missing
  goto HOLD
)
set "WEBUI_SECRET_KEY=my-fixed-secret-key-do-not-change"
set "OLLAMA_KEEP_ALIVE=24h"
set "OLLAMA_BASE_URL=http://127.0.0.1:11434"
set "OPENAI_API_BASE_URLS=http://127.0.0.1:1234/v1"
set "OPENAI_API_KEYS=bionic"
start "" cmd /c "timeout /t 6 /nobreak >nul & start http://localhost:8080"
cd /d "%ROOT%\backend"
echo.
echo   http://localhost:8080
echo   Keep window OPEN. Bionic on :1234
echo.
uvicorn open_webui.main:app --host 0.0.0.0 --port 8080

:HOLD
echo.
pause
endlocal
