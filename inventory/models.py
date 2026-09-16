from django.db import models
from customers.models import Customer

class Endpoint(models.Model):
    STATUS_OK = "OK"
    STATUS_WARNING = "WARNING"
    STATUS_CRITICAL = "CRITICAL"
    STATUS_UNKNOWN = "UNKNOWN"
    STATUS_CHOICES = [
        (STATUS_OK, "OK"),
        (STATUS_WARNING, "Aviso"),
        (STATUS_CRITICAL, "Crítico"),
        (STATUS_UNKNOWN, "Desconhecido"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="endpoints")
    ksc_key = models.CharField(max_length=255)
    hostname = models.CharField(max_length=255, blank=True)
    display_name = models.CharField(max_length=255, blank=True)
    fqdn = models.CharField(max_length=255, blank=True)
    windows_domain = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    group_name = models.CharField(max_length=500, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNKNOWN)
    status_id = models.IntegerField(null=True, blank=True)
    status_mask = models.BigIntegerField(null=True, blank=True)

    agent_version = models.CharField(max_length=120, blank=True)
    antivirus_version = models.CharField(max_length=120, blank=True)
    antivirus_bases_at = models.DateTimeField(null=True, blank=True)
    rtp_state = models.IntegerField(null=True, blank=True)
    edr_status = models.IntegerField(null=True, blank=True)

    last_visible_at = models.DateTimeField(null=True, blank=True)
    last_agent_connection_at = models.DateTimeField(null=True, blank=True)
    last_full_scan_at = models.DateTimeField(null=True, blank=True)

    reboot_required = models.BooleanField(default=False)
    virus_count = models.IntegerField(default=0)
    uncured_count = models.IntegerField(default=0)

    os_name = models.CharField(max_length=255, blank=True)
    os_build = models.CharField(max_length=80, blank=True)

    raw_data = models.JSONField(default=dict, blank=True)
    last_sync_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["hostname", "display_name"]
        constraints = [
            models.UniqueConstraint(fields=["customer", "ksc_key"], name="uq_endpoint_customer_ksc_key")
        ]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["customer", "hostname"]),
            models.Index(fields=["customer", "last_agent_connection_at"]),
        ]

    def __str__(self):
        return self.hostname or self.display_name or self.ksc_key
