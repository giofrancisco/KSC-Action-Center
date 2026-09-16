import os
from django.core.management.base import BaseCommand
from customers.models import Customer

class Command(BaseCommand):
    help = "Cria/atualiza o cliente inicial usando variaveis do .env."

    def handle(self, *args, **options):
        code = os.getenv("DEFAULT_CUSTOMER_CODE", "BONJA").strip()
        name = os.getenv("DEFAULT_CUSTOMER_NAME", code).strip()
        host = os.getenv("KSC_HOST", "").strip()
        port = int(os.getenv("KSC_PORT", "13299"))

        if not host:
            self.stderr.write(self.style.ERROR("KSC_HOST nao configurado no .env."))
            return

        customer, created = Customer.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "ksc_host": host,
                "ksc_port": port,
                "active": True,
            },
        )
        action = "criado" if created else "atualizado"
        self.stdout.write(self.style.SUCCESS(f"Cliente {customer.code} {action}: {customer.ksc_host}:{customer.ksc_port}"))
