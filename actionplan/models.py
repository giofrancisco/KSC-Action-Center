from django.conf import settings
from django.db import models
from customers.models import Customer
from inventory.models import Endpoint

class ProblemType(models.Model):
    PRIORITY_CHOICES = [("P0", "P0"), ("P1", "P1"), ("P2", "P2")]

    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=180)
    default_priority = models.CharField(max_length=2, choices=PRIORITY_CHOICES, default="P2")
    default_sla_hours = models.PositiveIntegerField(default=24)
    default_action = models.TextField(blank=True)
    resolution_criteria = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Problem(models.Model):
    PRIORITY_CHOICES = ProblemType.PRIORITY_CHOICES
    TECHNICAL_CHOICES = [
        ("OPEN", "Problema presente"),
        ("RESOLVED", "Resolução técnica confirmada"),
    ]
    WORKFLOW_CHOICES = [
        ("NEW", "Novo"),
        ("TRIAGE", "Triagem"),
        ("IN_PROGRESS", "Em andamento"),
        ("WAITING_CUSTOMER", "Aguardando cliente"),
        ("WAITING_THIRD_PARTY", "Aguardando terceiro"),
        ("SCHEDULED", "Agendado"),
        ("RESOLVED", "Resolvido"),
        ("REOPENED", "Reaberto"),
        ("DISMISSED", "Descartado"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="problems")
    endpoint = models.ForeignKey(Endpoint, on_delete=models.SET_NULL, null=True, blank=True, related_name="problems")
    problem_type = models.ForeignKey(ProblemType, on_delete=models.PROTECT, related_name="problems")

    priority = models.CharField(max_length=2, choices=PRIORITY_CHOICES)
    technical_status = models.CharField(max_length=20, choices=TECHNICAL_CHOICES, default="OPEN")
    workflow_status = models.CharField(max_length=30, choices=WORKFLOW_CHOICES, default="NEW")

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_security_problems",
    )

    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
    due_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    recurrence_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "-last_seen_at"]
        indexes = [
            models.Index(fields=["customer", "technical_status"]),
            models.Index(fields=["customer", "workflow_status"]),
            models.Index(fields=["customer", "priority"]),
        ]

    def __str__(self):
        return f"{self.priority} - {self.problem_type} - {self.endpoint or self.customer}"

class ProblemEvent(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="timeline")
    event_type = models.CharField(max_length=80)
    description = models.TextField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
