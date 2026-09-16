$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtualenv nao encontrada. Execute .\setup-dev.ps1 primeiro."
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker compose up -d db | Out-Null
}

& $Python manage.py runserver 0.0.0.0:8000
