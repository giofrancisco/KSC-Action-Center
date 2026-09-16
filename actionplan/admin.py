from django.contrib import admin
from .models import Problem, ProblemEvent, ProblemType

@admin.register(ProblemType)
class ProblemTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "default_priority", "default_sla_hours", "active")
    list_filter = ("default_priority", "active")
    search_fields = ("name", "code")

class ProblemEventInline(admin.TabularInline):
    model = ProblemEvent
    extra = 0
    readonly_fields = ("created_at",)

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("id", "priority", "problem_type", "endpoint", "customer", "technical_status", "workflow_status", "assigned_to", "last_seen_at")
    list_filter = ("customer", "priority", "technical_status", "workflow_status")
    search_fields = ("endpoint__hostname", "problem_type__name", "notes")
    inlines = [ProblemEventInline]
