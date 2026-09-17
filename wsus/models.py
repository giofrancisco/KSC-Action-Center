from django.conf import settings
from django.db import models

from customers.models import Customer


class WsusServer(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="wsus_servers",
    )

    name = models.CharField(
        "Nome",
        max_length=120,
    )

    hostname = models.CharField(
        "Hostname",
        max_length=255,
    )

    port = models.PositiveIntegerField(
        "Porta",
        default=8530,
    )

    use_ssl = models.BooleanField(
        "Usa SSL",
        default=False,
    )

    active = models.BooleanField(
        "Ativo",
        default=True,
    )

    last_sync_at = models.DateTimeField(
        "Última coleta",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


    class Meta:

        ordering = [
            "customer__name",
            "name",
        ]

        verbose_name = "Servidor WSUS"

        verbose_name_plural = "Servidores WSUS"

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "customer",
                    "hostname",
                ],
                name="uq_wsus_server_customer_hostname",
            ),

        ]


    def __str__(self):

        return (
            f"{self.customer} - "
            f"{self.name}"
        )



class WsusComputer(models.Model):

    STATE_UPDATED = "UPDATED"

    STATE_PENDING = "PENDING"

    STATE_FAILED = "FAILED"

    STATE_REBOOT = "REBOOT"

    STATE_UNKNOWN = "UNKNOWN"


    STATE_CHOICES = [

        (
            STATE_UPDATED,
            "Atualizado",
        ),

        (
            STATE_PENDING,
            "Pendente",
        ),

        (
            STATE_FAILED,
            "Com falha",
        ),

        (
            STATE_REBOOT,
            "Reboot pendente",
        ),

        (
            STATE_UNKNOWN,
            "Desconhecido",
        ),

    ]


    server = models.ForeignKey(
        WsusServer,
        on_delete=models.CASCADE,
        related_name="computers",
    )


    wsus_id = models.CharField(
        "ID WSUS",
        max_length=120,
    )


    hostname = models.CharField(
        "Hostname",
        max_length=255,
    )


    ip_address = models.GenericIPAddressField(
        "IP",
        null=True,
        blank=True,
    )


    os_name = models.CharField(
        "Sistema operacional",
        max_length=255,
        blank=True,
    )


    group_name = models.CharField(
        "Grupo WSUS",
        max_length=255,
        blank=True,
    )


    update_state = models.CharField(
        "Situação",
        max_length=20,
        choices=STATE_CHOICES,
        default=STATE_UNKNOWN,
    )


    needed_count = models.PositiveIntegerField(
        "Atualizações pendentes",
        default=0,
    )


    failed_count = models.PositiveIntegerField(
        "Atualizações com falha",
        default=0,
    )


    installed_count = models.PositiveIntegerField(
        "Atualizações instaladas",
        default=0,
    )


    reboot_pending = models.BooleanField(
        "Reboot pendente",
        default=False,
    )


    last_report_at = models.DateTimeField(
        "Último status report",
        null=True,
        blank=True,
    )


    last_sync_at = models.DateTimeField(
        "Última coleta",
        null=True,
        blank=True,
    )


    raw_data = models.JSONField(
        default=dict,
        blank=True,
    )


    created_at = models.DateTimeField(
        auto_now_add=True,
    )


    updated_at = models.DateTimeField(
        auto_now=True,
    )


    class Meta:

        ordering = [
            "hostname",
        ]

        verbose_name = "Computador WSUS"

        verbose_name_plural = "Computadores WSUS"

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "server",
                    "wsus_id",
                ],
                name="uq_wsus_computer_server_id",
            ),

        ]


    def __str__(self):

        return self.hostname



class WsusMaintenanceTask(models.Model):

    PRIORITY_CHOICES = [

        (
            "P0",
            "P0 - Crítica",
        ),

        (
            "P1",
            "P1 - Alta",
        ),

        (
            "P2",
            "P2 - Operacional",
        ),

    ]


    STATUS_PENDING = "PENDING"

    STATUS_SCHEDULED = "SCHEDULED"

    STATUS_IN_PROGRESS = "IN_PROGRESS"

    STATUS_REBOOT = "REBOOT"

    STATUS_VALIDATION = "VALIDATION"

    STATUS_BLOCKED = "BLOCKED"

    STATUS_COMPLETED = "COMPLETED"

    STATUS_CANCELLED = "CANCELLED"


    STATUS_CHOICES = [

        (
            STATUS_PENDING,
            "Pendente",
        ),

        (
            STATUS_SCHEDULED,
            "Agendado",
        ),

        (
            STATUS_IN_PROGRESS,
            "Em execução",
        ),

        (
            STATUS_REBOOT,
            "Aguardando reboot",
        ),

        (
            STATUS_VALIDATION,
            "Validação",
        ),

        (
            STATUS_BLOCKED,
            "Bloqueado",
        ),

        (
            STATUS_COMPLETED,
            "Concluído",
        ),

        (
            STATUS_CANCELLED,
            "Cancelado",
        ),

    ]


    computer = models.ForeignKey(
        WsusComputer,
        on_delete=models.CASCADE,
        related_name="maintenance_tasks",
    )


    priority = models.CharField(
        "Criticidade",
        max_length=2,
        choices=PRIORITY_CHOICES,
        default="P2",
    )


    status = models.CharField(
        "Status",
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )


    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_wsus_tasks",
        verbose_name="Responsável",
    )


    planned_start_at = models.DateTimeField(
        "Início previsto",
        null=True,
        blank=True,
    )


    planned_end_at = models.DateTimeField(
        "Fim previsto",
        null=True,
        blank=True,
    )


    allow_reboot = models.BooleanField(
        "Reboot permitido",
        default=False,
    )


    notes = models.TextField(
        "Observações",
        blank=True,
    )


    completed_at = models.DateTimeField(
        "Concluído em",
        null=True,
        blank=True,
    )


    created_at = models.DateTimeField(
        auto_now_add=True,
    )


    updated_at = models.DateTimeField(
        auto_now=True,
    )


    class Meta:

        ordering = [
            "priority",
            "planned_end_at",
            "-created_at",
        ]

        verbose_name = "Atividade WSUS"

        verbose_name_plural = "Atividades WSUS"


    def __str__(self):

        return (
            f"{self.computer.hostname} - "
            f"{self.get_status_display()}"
        )



class WsusMaintenanceEvent(models.Model):

    task = models.ForeignKey(
        WsusMaintenanceTask,
        on_delete=models.CASCADE,
        related_name="timeline",
    )


    event_type = models.CharField(
        "Tipo",
        max_length=80,
    )


    description = models.TextField(
        "Descrição",
    )


    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wsus_events",
    )


    created_at = models.DateTimeField(
        auto_now_add=True,
    )


    class Meta:

        ordering = [
            "-created_at",
        ]

        verbose_name = "Evento WSUS"

        verbose_name_plural = "Eventos WSUS"


    def __str__(self):

        return (
            f"{self.task_id} - "
            f"{self.event_type}"
        )