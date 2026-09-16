from django.core.management.base import BaseCommand, CommandError

from customers.models import Customer
from integrations.kaspersky.client import KSCClient, KSCConfig

class Command(BaseCommand):
    help = "Testa autenticacao KSC e consulta inicial de hosts."

    def add_arguments(self, parser):
        parser.add_argument("--customer", default="", help="Codigo do cliente. Se omitido, usa o primeiro ativo.")

    def handle(self, *args, **options):
        if options["customer"]:
            customer = Customer.objects.filter(code=options["customer"], active=True).first()
        else:
            customer = Customer.objects.filter(active=True).order_by("id").first()

        if not customer:
            raise CommandError("Nenhum cliente ativo encontrado. Execute: python manage.py seed_customer")

        self.stdout.write(f"KSC: {customer.ksc_host}:{customer.ksc_port}")
        config = KSCConfig.from_env(host=customer.ksc_host, port=customer.ksc_port)

        try:
            with KSCClient(config) as client:
                self.stdout.write(self.style.SUCCESS("KSC: autenticacao OK"))
                hosts = client.get_managed_hosts()
                self.stdout.write(self.style.SUCCESS(f"Dispositivos retornados: {len(hosts)}"))
                for host in hosts[:5]:
                    name = host.get("KLHST_WKS_DN") or host.get("KLHST_WKS_HOSTNAME") or host.get("name")
                    self.stdout.write(f"  - {name}")
        except Exception as exc:
            raise CommandError(str(exc)) from exc
