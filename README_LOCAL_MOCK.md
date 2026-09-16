# KSC Action Center - modo local ficticio

Esta variante permite validar a aplicacao sem Kaspersky e sem PostgreSQL.

## Usa
- Django
- SQLite local
- 80 endpoints ficticios
- Status OK / Aviso / Critico
- Problemas P0 / P1 / P2 ficticios
- Alguns problemas resolvidos
- Cliente BONJA-MOCK

## Instalacao

Extraia para:

    C:\KSC_Action_Center

No PowerShell:

    cd C:\KSC_Action_Center
    Set-ExecutionPolicy -Scope Process Bypass
    .\setup-local-mock.ps1

Crie o usuario:

    .\.venv\Scripts\python.exe manage.py createsuperuser

Execute:

    .\run-local-mock.ps1

Abra:

    http://127.0.0.1:8000

Admin:

    http://127.0.0.1:8000/admin/

Endpoints:

    http://127.0.0.1:8000/endpoints/

## Recriar o cenario

    .\.venv\Scripts\python.exe manage.py seed_mock_data --reset --endpoints 80

Ou com 250 endpoints:

    .\.venv\Scripts\python.exe manage.py seed_mock_data --reset --endpoints 250

A integracao real com a Kaspersky OpenAPI continua no projeto, mas nao e usada neste modo.
