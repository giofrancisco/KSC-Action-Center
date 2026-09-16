$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host "=== KSC Action Center - Setup de Desenvolvimento ===" -ForegroundColor Cyan

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Criando virtualenv..." -ForegroundColor Yellow
    py -3 -m venv .venv
}

$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"

Write-Host "Atualizando pip..." -ForegroundColor Yellow
& $Python -m pip install --upgrade pip

Write-Host "Instalando dependencias..." -ForegroundColor Yellow
& $Python -m pip install -r requirements.txt

if (-not (Test-Path ".\.env")) {
    Copy-Item ".\.env.example" ".\.env"
    Write-Host ""
    Write-Host "Arquivo .env criado. EDITE O .env antes de testar a API." -ForegroundColor Yellow
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Subindo PostgreSQL pelo Docker..." -ForegroundColor Yellow
    docker compose up -d db
    Write-Host "Aguardando PostgreSQL..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}
else {
    Write-Host "Docker nao encontrado. O PostgreSQL precisa estar instalado e acessivel conforme o .env." -ForegroundColor Yellow
}

Write-Host "Aplicando migrations..." -ForegroundColor Yellow
& $Python manage.py makemigrations customers inventory actionplan integrations
& $Python manage.py migrate

Write-Host "Criando/atualizando cliente inicial..." -ForegroundColor Yellow
& $Python manage.py seed_customer

Write-Host ""
Write-Host "Setup concluido." -ForegroundColor Green
Write-Host ""
Write-Host "Proximos comandos:"
Write-Host "  .\.venv\Scripts\python.exe manage.py createsuperuser"
Write-Host "  .\.venv\Scripts\python.exe manage.py ksc_check"
Write-Host "  .\.venv\Scripts\python.exe manage.py sync_ksc"
Write-Host "  .\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000"
