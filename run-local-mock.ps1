$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtualenv nao encontrada. Execute .\setup-local-mock.ps1 primeiro."
}
& $Python manage.py runserver 127.0.0.1:8000
