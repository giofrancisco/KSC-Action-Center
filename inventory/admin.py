from django.contrib import admin
from .models import Endpoint

@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    list_display = ("hostname", "customer", "ip_address", "status", "group_name", "last_agent_connection_at")
    list_filter = ("customer", "status")
    search_fields = ("hostname", "display_name", "fqdn", "ip_address", "group_name")
