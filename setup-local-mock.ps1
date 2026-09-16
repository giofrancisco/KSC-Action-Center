$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host "=== KSC Action Center - Ambiente LOCAL MOCK ===" -ForegroundColor Cyan

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Criando virtualenv..." -ForegroundColor Yellow
    py -3 -m venv .venv
}

$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt
Copy-Item ".\.env.local.example" ".\.env" -Force
& $Python manage.py makemigrations customers inventory actionplan integrations
& $Python manage.py migrate
& $Python manage.py seed_mock_data --reset --endpoints 80

Write-Host ""
Write-Host "Ambiente ficticio pronto." -ForegroundColor Green
Write-Host "Crie o usuario com:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\python.exe manage.py createsuperuser"
Write-Host "Depois execute:" -ForegroundColor Cyan
Write-Host "  .\run-local-mock.ps1"
