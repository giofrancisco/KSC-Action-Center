from django.contrib import admin
from .models import SyncRun

@admin.register(SyncRun)
class SyncRunAdmin(admin.ModelAdmin):
    list_display = ("customer", "started_at", "finished_at", "status", "hosts_received", "endpoints_created", "endpoints_updated")
    list_filter = ("customer", "status")
    readonly_fields = ("started_at",)
