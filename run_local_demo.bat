@echo off
REM AI Agent OS - One-click local demo launcher (Windows)
setlocal
cd /d "%~dp0"

echo AI Agent OS - Local Demo Launcher
echo ========================================

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [INFO] Virtual environment activated
) else (
    echo [WARN] .venv not found - using system Python
)

echo [STEP] Running migrations...
python manage.py migrate --noinput
if errorlevel 1 goto :fail

echo [STEP] Seeding demo data...
python scripts\seed_demo_data.py
if errorlevel 1 goto :fail

echo [STEP] Environment check...
python scripts\check_environment.py
if errorlevel 1 goto :fail

echo.
echo ========================================
echo Local demo ready. Starting server...
echo.
echo Login:  admin@example.com / Admin123!
echo URLs:
echo   Dashboard:    http://127.0.0.1:8000/dashboard/
echo   Demo Center:  http://127.0.0.1:8000/demo/
echo   Demo Report:  http://127.0.0.1:8000/demo/report/
echo   Agents:       http://127.0.0.1:8000/agents/
echo.
echo Press Ctrl+C to stop the server.
echo ========================================

python manage.py runserver 127.0.0.1:8000
goto :eof

:fail
echo [FAIL] Setup step failed. Fix errors above and retry.
exit /b 1
