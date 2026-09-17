from django.contrib import admin

from .models import (
    WsusComputer,
    WsusMaintenanceEvent,
    WsusMaintenanceTask,
    WsusServer,
)


@admin.register(WsusServer)
class WsusServerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "customer",
        "hostname",
        "port",
        "use_ssl",
        "active",
        "last_sync_at",
    )

    list_filter = (
        "customer",
        "active",
        "use_ssl",
    )

    search_fields = (
        "name",
        "hostname",
    )


@admin.register(WsusComputer)
class WsusComputerAdmin(admin.ModelAdmin):
    list_display = (
        "hostname",
        "server",
        "ip_address",
        "update_state",
        "needed_count",
        "failed_count",
        "reboot_pending",
        "last_report_at",
    )

    list_filter = (
        "server",
        "update_state",
        "reboot_pending",
        "group_name",
    )

    search_fields = (
        "hostname",
        "ip_address",
        "group_name",
        "os_name",
    )


class WsusMaintenanceEventInline(admin.TabularInline):
    model = WsusMaintenanceEvent
    extra = 0

    readonly_fields = (
        "created_at",
    )


@admin.register(WsusMaintenanceTask)
class WsusMaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "computer",
        "priority",
        "status",
        "assigned_to",
        "planned_start_at",
        "planned_end_at",
        "allow_reboot",
    )

    list_filter = (
        "priority",
        "status",
        "allow_reboot",
    )

    search_fields = (
        "computer__hostname",
        "assigned_to__username",
        "notes",
    )

    inlines = [
        WsusMaintenanceEventInline,
    ]