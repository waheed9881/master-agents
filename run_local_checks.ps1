# AI Agent OS - Full local validation suite (PowerShell)
Set-Location $PSScriptRoot
$fail = 0

Write-Host "AI Agent OS - Local Checks"
Write-Host "========================================"

if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

function Run-Step($name, $cmd) {
    Write-Host ""
    Write-Host "[RUN] $name"
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) { $script:fail = 1 }
}

Run-Step "manage.py check" "python manage.py check"
Run-Step "seed demo data" "python scripts/seed_demo_data.py"
Run-Step "check_environment" "python scripts/check_environment.py"
Run-Step "security_audit" "python manage.py security_audit"
Run-Step "smoke_test" "python scripts/smoke_test.py"
Run-Step "audit_routes" "python scripts/audit_routes.py"
Run-Step "api_smoke_test" "python scripts/api_smoke_test.py"
Run-Step "audit_agent_quality" "python scripts/audit_agent_quality.py"
Run-Step "pytest" "python -m pytest tests/ -q"

Write-Host "========================================"
if ($fail -eq 0) {
    Write-Host "Result: PASS"
    exit 0
} else {
    Write-Host "Result: FAIL"
    exit 1
}
