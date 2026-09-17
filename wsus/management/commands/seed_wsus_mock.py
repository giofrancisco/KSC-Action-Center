from datetime import timedelta
import random

from django.core.management.base import (
    BaseCommand
)

from django.utils import timezone

from customers.models import Customer

from wsus.models import (
    WsusComputer,
    WsusMaintenanceEvent,
    WsusMaintenanceTask,
    WsusServer,
)


class Command(BaseCommand):

    help = (
        "Cria dados fictícios do WSUS "
        "para desenvolvimento local."
    )


    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "--reset",
            action="store_true",
        )

        parser.add_argument(
            "--computers",
            type=int,
            default=60,
        )


    def handle(
        self,
        *args,
        **options,
    ):

        random.seed(
            20260917
        )

        now = timezone.now()


        customer, _ = (
            Customer.objects.get_or_create(
                code="BONJA-MOCK",
                defaults={
                    "name": (
                        "BONJA - "
                        "AMBIENTE FICTÍCIO"
                    ),
                    "active": True,
                    "ksc_host": "mock.local",
                    "ksc_port": 13299,
                    "timezone": (
                        "America/Sao_Paulo"
                    ),
                },
            )
        )


        if options["reset"]:

            WsusServer.objects.filter(
                customer=customer,
                hostname="wsus-mock.local",
            ).delete()


        server, _ = (
            WsusServer.objects
            .update_or_create(
                customer=customer,
                hostname="wsus-mock.local",
                defaults={
                    "name": "WSUS-MOCK01",
                    "port": 8530,
                    "use_ssl": False,
                    "active": True,
                    "last_sync_at": (
                        now
                        - timedelta(
                            minutes=5
                        )
                    ),
                },
            )
        )


        groups = [

            "SERVIDORES-PRODUCAO",

            "SERVIDORES-HOMOLOGACAO",

            "ESTACOES-ADMIN",

            "ESTACOES-OPERACAO",

        ]


        os_choices = [

            "Windows Server 2022",

            "Windows Server 2019",

            "Windows Server 2016",

            "Windows 11 Pro",

            "Windows 10 Pro",

        ]


        total = max(
            20,
            options["computers"],
        )


        computers = []


        for i in range(
            1,
            total + 1,
        ):


            if i % 13 == 0:

                state = "FAILED"

                needed = random.randint(
                    2,
                    8,
                )

                failed = random.randint(
                    1,
                    3,
                )

                reboot = False


            elif i % 11 == 0:

                state = "REBOOT"

                needed = 0

                failed = 0

                reboot = True


            elif i % 3 == 0:

                state = "PENDING"

                needed = random.randint(
                    1,
                    12,
                )

                failed = 0

                reboot = False


            else:

                state = "UPDATED"

                needed = 0

                failed = 0

                reboot = False


            if i <= max(
                20,
                total // 3,
            ):

                prefix = "SRV"

            else:

                prefix = "PC"


            hostname = (
                f"{prefix}-WSUS-{i:03d}"
            )


            computer, _ = (
                WsusComputer.objects
                .update_or_create(
                    server=server,

                    wsus_id=(
                        f"MOCK-WSUS-{i:05d}"
                    ),

                    defaults={

                        "hostname":
                            hostname,

                        "ip_address":
                            (
                                f"10.30."
                                f"{1 + (i // 240)}."
                                f"{10 + (i % 240)}"
                            ),

                        "os_name":
                            random.choice(
                                os_choices
                            ),

                        "group_name":
                            random.choice(
                                groups
                            ),

                        "update_state":
                            state,

                        "needed_count":
                            needed,

                        "failed_count":
                            failed,

                        "installed_count":
                            random.randint(
                                80,
                                250,
                            ),

                        "reboot_pending":
                            reboot,

                        "last_report_at":
                            (
                                now
                                - timedelta(
                                    minutes=
                                    random.randint(
                                        5,
                                        300,
                                    )
                                )
                            ),

                        "last_sync_at":
                            (
                                now
                                - timedelta(
                                    minutes=5
                                )
                            ),

                        "raw_data": {
                            "mock": True,
                            "sequence": i,
                        },

                    },
                )
            )


            computers.append(
                computer
            )


        statuses = [

            "PENDING",

            "SCHEDULED",

            "IN_PROGRESS",

            "REBOOT",

            "VALIDATION",

            "BLOCKED",

            "COMPLETED",

        ]


        task_computers = [

            computer

            for computer in computers

            if computer.update_state
            != "UPDATED"

        ][:24]


        for index, computer in enumerate(
            task_computers
        ):


            status = statuses[
                index
                % len(statuses)
            ]


            if computer.failed_count > 0:

                priority = "P0"

            elif (
                computer.needed_count
                >= 6
            ):

                priority = "P1"

            else:

                priority = "P2"


            start_at = (
                now
                + timedelta(
                    hours=(
                        index % 6
                    ) + 2
                )
            )


            end_at = (
                start_at
                + timedelta(
                    hours=2
                )
            )


            task = (
                WsusMaintenanceTask.objects
                .create(
                    computer=computer,

                    priority=priority,

                    status=status,

                    planned_start_at=
                        start_at,

                    planned_end_at=
                        end_at,

                    allow_reboot=(
                        computer.group_name
                        ==
                        "SERVIDORES-PRODUCAO"
                    ),

                    notes=(
                        "Atividade fictícia "
                        "para validação "
                        "do módulo WSUS."
                    ),

                    completed_at=(
                        now
                        - timedelta(
                            hours=1
                        )
                        if status
                        == "COMPLETED"
                        else None
                    ),
                )
            )


            WsusMaintenanceEvent.objects.create(
                task=task,

                event_type="CREATED",

                description=(
                    "Atividade WSUS "
                    "fictícia criada."
                ),
            )


        self.stdout.write(

            self.style.SUCCESS(

                (
                    f"WSUS mock criado: "
                    f"computadores={total}, "
                    f"atividades="
                    f"{len(task_computers)}."
                )

            )

        )