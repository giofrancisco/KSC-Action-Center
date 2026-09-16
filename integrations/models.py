from django.db import models
from customers.models import Customer

class SyncRun(models.Model):
    STATUS_CHOICES = [
        ("RUNNING", "Executando"),
        ("SUCCESS", "Sucesso"),
        ("FAILED", "Falha"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="sync_runs")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="RUNNING")

    hosts_received = models.PositiveIntegerField(default=0)
    endpoints_created = models.PositiveIntegerField(default=0)
    endpoints_updated = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.customer} - {self.started_at} - {self.status}"
