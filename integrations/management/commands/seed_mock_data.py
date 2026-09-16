from datetime import timedelta
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from actionplan.models import Problem, ProblemEvent, ProblemType
from customers.models import Customer
from inventory.models import Endpoint
from integrations.models import SyncRun

PROBLEM_TYPES = [
    ("THREAT_PENDING", "Ameaca sem tratamento confirmado", "P0", 4, "Investigar a deteccao, conter o endpoint e validar remediacao."),
    ("UNTREATED_OBJECT", "Objeto nao tratado", "P0", 8, "Executar remediacao e verificacao completa no endpoint."),
    ("RTP_DISABLED", "Protecao em tempo real desativada", "P0", 4, "Validar KES, politica e servicos de protecao em tempo real."),
    ("AGENT_OFFLINE", "Network Agent sem comunicacao", "P1", 8, "Validar conectividade, servico do Network Agent e vinculo com o KSC."),
    ("DATABASE_OUTDATED", "Bases antivirus desatualizadas", "P1", 8, "Forcar atualizacao e revisar tarefa/politica de update."),
    ("FULL_SCAN_OLD", "Full Scan desatualizado", "P2", 72, "Executar ou reagendar verificacao completa."),
    ("REBOOT_REQUIRED", "Reinicializacao pendente", "P2", 72, "Programar janela de manutencao e reiniciar o endpoint."),
    ("LICENSE_CRITICAL", "Licenciamento em nivel critico", "P1", 120, "Revisar consumo, associacoes e capacidade contratada."),
]

class Command(BaseCommand):
    help = "Cria dados ficticios para validar o sistema localmente sem acessar o Kaspersky."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--endpoints", type=int, default=80)

    def handle(self, *args, **options):
        random.seed(42)
        now = timezone.now()

        customer, _ = Customer.objects.update_or_create(
            code="BONJA-MOCK",
            defaults={
                "name": "BONJA - AMBIENTE FICTICIO",
                "active": True,
                "ksc_host": "mock.local",
                "ksc_port": 13299,
                "timezone": "America/Sao_Paulo",
            },
        )

        if options["reset"]:
            ProblemEvent.objects.filter(problem__customer=customer).delete()
            Problem.objects.filter(customer=customer).delete()
            Endpoint.objects.filter(customer=customer).delete()
            SyncRun.objects.filter(customer=customer).delete()

        type_map = {}
        for code, name, priority, sla, action in PROBLEM_TYPES:
            obj, _ = ProblemType.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "default_priority": priority,
                    "default_sla_hours": sla,
                    "default_action": action,
                    "resolution_criteria": "A sincronizacao deve confirmar que a condicao deixou de existir.",
                    "active": True,
                },
            )
            type_map[code] = obj

        groups = ["Administrativo", "Educacional", "Servidores", "Financeiro", "Diretoria"]
        os_choices = [
            ("Windows 11 Pro", "26100"),
            ("Windows 10 Pro", "19045"),
            ("Windows Server 2022", "20348"),
        ]

        total = max(20, options["endpoints"])
        critical_target = max(4, round(total * 0.10))
        warning_target = max(8, round(total * 0.20))
        endpoints = []

        for i in range(1, total + 1):
            if i <= critical_target:
                status = Endpoint.STATUS_CRITICAL
            elif i <= critical_target + warning_target:
                status = Endpoint.STATUS_WARNING
            else:
                status = Endpoint.STATUS_OK

            prefix = "SRV" if i % 17 == 0 else ("NT" if i % 3 == 0 else "C")
            hostname = f"{prefix}{1000+i}"
            ip = f"10.20.{1 + (i // 240)}.{10 + (i % 240)}"
            os_name, os_build = random.choice(os_choices)

            ep, _ = Endpoint.objects.update_or_create(
                customer=customer,
                ksc_key=f"MOCK-{i:05d}",
                defaults={
                    "hostname": hostname,
                    "display_name": hostname,
                    "fqdn": f"{hostname.lower()}.bonja.local",
                    "windows_domain": "BONJA",
                    "ip_address": ip,
                    "group_name": random.choice(groups),
                    "status": status,
                    "status_id": 1 if status == Endpoint.STATUS_CRITICAL else (2 if status == Endpoint.STATUS_WARNING else 0),
                    "status_mask": 0,
                    "agent_version": "15.1.0.20748",
                    "antivirus_version": "12.12.0.522",
                    "antivirus_bases_at": now - timedelta(hours=random.randint(1, 90)),
                    "rtp_state": 4 if status != Endpoint.STATUS_CRITICAL or i % 2 else 9,
                    "edr_status": 1,
                    "last_visible_at": now - timedelta(minutes=random.randint(1, 120)),
                    "last_agent_connection_at": now - timedelta(hours=random.randint(0, 72 if status != Endpoint.STATUS_OK else 6)),
                    "last_full_scan_at": now - timedelta(days=random.randint(1, 55)),
                    "reboot_required": (i % 11 == 0),
                    "virus_count": 1 if i % 19 == 0 else 0,
                    "uncured_count": 1 if i in {1, 2} else 0,
                    "os_name": os_name,
                    "os_build": os_build,
                    "raw_data": {"mock": True, "sequence": i},
                },
            )
            endpoints.append(ep)

        open_specs = [
            ("THREAT_PENDING", endpoints[0], "P0", 2),
            ("UNTREATED_OBJECT", endpoints[1], "P0", 3),
            ("RTP_DISABLED", endpoints[2], "P0", 4),
            ("AGENT_OFFLINE", endpoints[critical_target], "P1", 10),
            ("AGENT_OFFLINE", endpoints[critical_target + 1], "P1", 14),
            ("DATABASE_OUTDATED", endpoints[critical_target + 2], "P1", 20),
            ("DATABASE_OUTDATED", endpoints[critical_target + 3], "P1", 30),
            ("FULL_SCAN_OLD", endpoints[critical_target + warning_target], "P2", 96),
            ("REBOOT_REQUIRED", endpoints[min(total - 1, critical_target + warning_target + 1)], "P2", 48),
        ]

        for code, ep, priority, age_hours in open_specs:
            ptype = type_map[code]
            first_seen = now - timedelta(hours=age_hours)
            problem, created = Problem.objects.update_or_create(
                customer=customer,
                endpoint=ep,
                problem_type=ptype,
                technical_status="OPEN",
                defaults={
                    "priority": priority,
                    "workflow_status": random.choice(["NEW", "TRIAGE", "IN_PROGRESS", "WAITING_CUSTOMER"]),
                    "first_seen_at": first_seen,
                    "last_seen_at": now,
                    "due_at": first_seen + timedelta(hours=ptype.default_sla_hours),
                    "notes": "Registro ficticio para validacao visual e funcional.",
                },
            )
            if created:
                ProblemEvent.objects.create(
                    problem=problem,
                    event_type="DETECTED",
                    description="Problema detectado automaticamente na coleta ficticia.",
                )

        resolved_specs = [
            ("DATABASE_OUTDATED", endpoints[-1], "P1", 30, 4),
            ("AGENT_OFFLINE", endpoints[-2], "P1", 50, 8),
            ("REBOOT_REQUIRED", endpoints[-3], "P2", 70, 24),
        ]
        for code, ep, priority, started_hours, resolved_hours in resolved_specs:
            ptype = type_map[code]
            Problem.objects.update_or_create(
                customer=customer,
                endpoint=ep,
                problem_type=ptype,
                technical_status="RESOLVED",
                defaults={
                    "priority": priority,
                    "workflow_status": "RESOLVED",
                    "first_seen_at": now - timedelta(hours=started_hours),
                    "last_seen_at": now - timedelta(hours=resolved_hours),
                    "resolved_at": now - timedelta(hours=resolved_hours),
                    "due_at": now - timedelta(hours=started_hours) + timedelta(hours=ptype.default_sla_hours),
                    "notes": "Problema ficticio ja resolvido.",
                },
            )

        SyncRun.objects.create(
            customer=customer,
            finished_at=now - timedelta(minutes=1),
            status="SUCCESS",
            hosts_received=total,
            endpoints_created=total,
            endpoints_updated=0,
        )

        open_count = Problem.objects.filter(customer=customer, technical_status="OPEN").count()
        self.stdout.write(self.style.SUCCESS(
            f"Mock criado: cliente={customer.code}, endpoints={total}, criticos={critical_target}, avisos={warning_target}, problemas_abertos={open_count}."
        ))
