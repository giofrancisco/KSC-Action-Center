# Certificados

Se o Kaspersky Security Center utilizar certificado emitido por uma CA que não seja
confiável para o Python/Windows, coloque aqui o certificado CA em formato PEM.

Exemplo:

    certs/klserver.pem

Depois configure no `.env`:

    KSC_VERIFY_SSL=true
    KSC_CA_CERT=C:\KSC_Action_Center\certs\klserver.pem

Não versione certificados privados ou credenciais.
