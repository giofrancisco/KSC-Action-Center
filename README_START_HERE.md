# KSC Action Center — Starter

Projeto inicial independente para administrar postura de segurança e plano de ação
a partir da Kaspersky Security Center OpenAPI.

## Stack

- Python
- Django 5.2 LTS
- PostgreSQL 18
- Bootstrap 5.3
- HTMX
- Chart.js
- Requests para KSC OpenAPI

## O que esta versão inicial já faz

1. Login com Django.
2. Cadastro de clientes.
3. Dashboard responsivo.
4. Inventário de endpoints.
5. Estrutura de banco para problemas e timeline.
6. Cliente Python para Kaspersky OpenAPI.
7. Teste de autenticação KSC.
8. Coleta inicial de hosts usando:
   - `Session.StartSession`
   - `HostGroup.FindHosts`
   - `ChunkAccessor.GetItemsCount`
   - `ChunkAccessor.GetItemsChunk`
   - `ChunkAccessor.Release`
   - `Session.EndSession`
9. Sincronização dos endpoints no PostgreSQL.
10. Registro das execuções de sincronização.

## Estrutura principal

    KSC_Action_Center_Starter/
    ├── config/
    ├── dashboard/
    ├── customers/
    ├── inventory/
    ├── actionplan/
    ├── integrations/
    │   └── kaspersky/
    ├── templates/
    ├── static/
    ├── certs/
    ├── docker-compose.yml
    ├── requirements.txt
    ├── .env.example
    ├── setup-dev.ps1
    └── run-dev.ps1

## 1. Pré-requisitos no Windows

Recomendado:

- Python 3.13+
- Docker Desktop
- PowerShell
- Acesso de rede do computador até `antivirus.bonja.local:13299`

Teste a conectividade:

    Test-NetConnection antivirus.bonja.local -Port 13299

## 2. Criar o projeto local

Extraia o ZIP para, por exemplo:

    C:\KSC_Action_Center

Abra PowerShell:

    cd C:\KSC_Action_Center
    Set-ExecutionPolicy -Scope Process Bypass
    .\setup-dev.ps1

## 3. Editar o .env

O `setup-dev.ps1` cria `.env` copiando `.env.example`.

Edite:

    notepad .env

Preencha principalmente:

    KSC_HOST=antivirus.bonja.local
    KSC_PORT=13299
    KSC_USERNAME=api_relatorio
    KSC_PASSWORD=SUA_SENHA
    KSC_INTERNAL_USER=true
    KSC_DOMAIN=bonja.local

Não compartilhe o `.env` e não coloque esse arquivo no Git.

## 4. Certificado

Se necessário, copie o PEM do KSC para:

    C:\KSC_Action_Center\certs\klserver.pem

E configure:

    KSC_VERIFY_SSL=true
    KSC_CA_CERT=C:\KSC_Action_Center\certs\klserver.pem

## 5. Criar usuário administrador

    .\.venv\Scripts\python.exe manage.py createsuperuser

## 6. Validar a KSC OpenAPI

Primeiro teste somente autenticação + consulta:

    .\.venv\Scripts\python.exe manage.py ksc_check

Resultado esperado:

    KSC: autenticacao OK
    Dispositivos retornados: NNN

## 7. Sincronizar endpoints para o PostgreSQL

    .\.venv\Scripts\python.exe manage.py sync_ksc

## 8. Executar a interface

    .\run-dev.ps1

Acesse:

    http://127.0.0.1:8000

Login:

    http://127.0.0.1:8000/accounts/login/

Admin:

    http://127.0.0.1:8000/admin/

## Próxima fase

Depois que `ksc_check` e `sync_ksc` estiverem validados no seu computador,
a próxima etapa será acrescentar:

1. ameaças (`RptViractSrvViewName`);
2. licenciamento;
3. postura de segurança;
4. motor automático de problemas P0/P1/P2;
5. resolução e reabertura automáticas;
6. plano de ação;
7. ETA para status PROTEGIDO.

## Observação sobre MFA

Este starter implementa autenticação `KSCBasic`, que atende o usuário interno
utilizado atualmente no projeto de relatórios. O fluxo interativo TOTP/MFA ainda
não foi incluído nesta primeira versão.
