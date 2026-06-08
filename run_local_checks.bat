@echo off
REM AI Agent OS - Full local validation suite (Windows)
setlocal
cd /d "%~dp0"
set FAIL=0

echo AI Agent OS - Local Checks
echo ========================================

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

call :run "manage.py check" python manage.py check || set FAIL=1
call :run "seed demo data" python scripts\seed_demo_data.py || set FAIL=1
call :run "check_environment" python scripts\check_environment.py || set FAIL=1
call :run "security_audit" python manage.py security_audit || set FAIL=1
call :run "smoke_test" python scripts\smoke_test.py || set FAIL=1
call :run "audit_routes" python scripts\audit_routes.py || set FAIL=1
call :run "api_smoke_test" python scripts\api_smoke_test.py || set FAIL=1
call :run "audit_agent_quality" python scripts\audit_agent_quality.py || set FAIL=1
call :run "pytest" python -m pytest tests\ -q || set FAIL=1

echo ========================================
if %FAIL%==0 (
    echo Result: PASS
    exit /b 0
) else (
    echo Result: FAIL
    exit /b 1
)

:run
echo.
echo [RUN] %~1
%~2
exit /b %ERRORLEVEL%
