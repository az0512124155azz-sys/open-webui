@echo off
chcp 65001 >nul
title Open WebUI - Start All
cd /d "%~dp0"

if exist "%USERPROFILE%\open-webui\backend\open_webui\main.py" (
  set "ROOT=%USERPROFILE%\open-webui"
) else if exist "%~dp0backend\open_webui\main.py" (
  set "ROOT=%~dp0"
) else if exist "%~dp0open-webui\backend\open_webui\main.py" (
  set "ROOT=%~dp0open-webui"
) else (
  echo [ERROR] open-webui not found
  pause
  exit /b 1
)

cd /d "%ROOT%"
echo.
echo  ========================================
echo   Open WebUI - ONE CLICK START ALL
echo  ========================================
echo.

echo [1/6] Stop old server...
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8080" ^| findstr "LISTENING"') do (
  taskkill /PID %%p /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

echo [2/6] Update files from GitHub...
git fetch origin feature/custom-fork-v1 >nul 2>&1
git checkout origin/feature/custom-fork-v1 -- backend/open_webui/utils/seed_default_skills.py >nul 2>&1
git checkout origin/feature/custom-fork-v1 -- src/custom-fork-theme.css >nul 2>&1
git checkout origin/feature/custom-fork-v1 -- plugins/github_tool.py >nul 2>&1
git checkout origin/feature/custom-fork-v1 -- plugins/3d_builder_tool.py >nul 2>&1

echo [3/6] Theme import...
python -c "from pathlib import Path;p=Path(r'src/app.css');t=p.read_text(encoding='utf-8') if p.exists() else '';imp=\"@import './custom-fork-theme.css';\";\nimport sys\nif p.exists() and imp not in t:\n  t=(t.split(chr(10),1)[0]+chr(10)+imp+chr(10)+t.split(chr(10),1)[1]) if t.startswith('@reference') else (imp+chr(10)+t);p.write_text(t,encoding='utf-8');print('  added')\nelse: print('  ok')"

echo [4/6] Skills hook...
python -c "from pathlib import Path;p=Path(r'backend/open_webui/routers/skills.py');\nimport sys\nif not p.exists(): print('  missing');sys.exit(0)\nt=p.read_text(encoding='utf-8');imp='from open_webui.utils.seed_default_skills import ensure_default_skills\n'\nif 'seed_default_skills' not in t: t=t.replace('from open_webui.utils.auth import get_admin_user, get_verified_user\n','from open_webui.utils.auth import get_admin_user, get_verified_user\n'+imp)\nold='async def get_skills(\n    request: Request,\n    query: Optional[str] = None,\n    user=Depends(get_verified_user),\n    db: AsyncSession = Depends(get_async_session),\n):\n    if user.role == \'admin\' and BYPASS_ADMIN_ACCESS_CONTROL:'\nnew='async def get_skills(\n    request: Request,\n    query: Optional[str] = None,\n    user=Depends(get_verified_user),\n    db: AsyncSession = Depends(get_async_session),\n):\n    await ensure_default_skills(user, db=db)\n    if user.role == \'admin\' and BYPASS_ADMIN_ACCESS_CONTROL:'\nif 'ensure_default_skills(user' not in t: t=t.replace(old,new,1)\np.write_text(t,encoding='utf-8');print('  ok')"

echo [5/6] Check build...
if not exist "%ROOT%\build\index.html" (
  call npm run build
) else (
  echo   build ok
)

echo [6/6] Start server...
call "%ROOT%\backend\.venv\Scripts\activate.bat"
set "WEBUI_SECRET_KEY=my-fixed-secret-key-do-not-change"
set "OLLAMA_KEEP_ALIVE=24h"
set "OLLAMA_BASE_URL=http://127.0.0.1:11434"
set "OPENAI_API_BASE_URLS=http://127.0.0.1:1234/v1"
set "OPENAI_API_KEYS=bionic"
start "" cmd /c "timeout /t 5 /nobreak >nul & start http://localhost:8080"
cd /d "%ROOT%\backend"
echo.
echo   http://localhost:8080
echo   Keep window OPEN. Bionic on :1234
echo.
uvicorn open_webui.main:app --host 0.0.0.0 --port 8080
pause
