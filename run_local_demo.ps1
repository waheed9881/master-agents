# AI Agent OS - One-click local demo launcher (PowerShell)
Set-Location $PSScriptRoot

Write-Host "AI Agent OS - Local Demo Launcher"
Write-Host "========================================"

if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
    Write-Host "[INFO] Virtual environment activated"
} else {
    Write-Host "[WARN] .venv not found - using system Python"
}

Write-Host "[STEP] Running migrations..."
python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "[STEP] Seeding demo data..."
python scripts/seed_demo_data.py
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "[STEP] Environment check..."
python scripts/check_environment.py
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "========================================"
Write-Host "Local demo ready. Starting server..."
Write-Host ""
Write-Host "Login:  admin@example.com / Admin123!"
Write-Host "URLs:"
Write-Host "  Dashboard:    http://127.0.0.1:8000/dashboard/"
Write-Host "  Demo Center:  http://127.0.0.1:8000/demo/"
Write-Host "  Demo Report:  http://127.0.0.1:8000/demo/report/"
Write-Host "  Agents:       http://127.0.0.1:8000/agents/"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server."
Write-Host "========================================"

python manage.py runserver 127.0.0.1:8000
