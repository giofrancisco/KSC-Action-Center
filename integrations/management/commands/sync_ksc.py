from django.core.management.base import BaseCommand, CommandError

from customers.models import Customer
from integrations.kaspersky.sync import sync_customer_hosts

class Command(BaseCommand):
    help = "Sincroniza endpoints do KSC para o PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument("--customer", default="", help="Codigo do cliente. Se omitido, usa o primeiro ativo.")

    def handle(self, *args, **options):
        if options["customer"]:
            customer = Customer.objects.filter(code=options["customer"], active=True).first()
        else:
            customer = Customer.objects.filter(active=True).order_by("id").first()

        if not customer:
            raise CommandError("Nenhum cliente ativo encontrado.")

        self.stdout.write(f"Sincronizando cliente {customer.code}...")
        try:
            run = sync_customer_hosts(customer)
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluido: recebidos={run.hosts_received}, criados={run.endpoints_created}, atualizados={run.endpoints_updated}"
            )
        )
