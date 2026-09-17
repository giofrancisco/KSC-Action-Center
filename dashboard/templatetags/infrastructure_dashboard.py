from django import template

from wsus.models import (
    WsusComputer,
    WsusMaintenanceTask,
    WsusServer,
)


register = template.Library()


@register.simple_tag(takes_context=True)
def wsus_summary(context):

    customer = context.get(
        "customer"
    )

    servers = (
        WsusServer.objects
        .filter(
            active=True
        )
    )

    if customer:

        servers = servers.filter(
            customer=customer
        )

    server = (
        servers
        .order_by("id")
        .first()
    )


    if not server:

        return {
            "available": False,

            "server_name": "",
            "hostname": "",

            "total": 0,

            "updated": 0,
            "pending": 0,
            "failed": 0,
            "reboot": 0,
            "unknown": 0,

            "updated_percent": 0,

            "open_tasks": 0,

            "pending_tasks": 0,
            "scheduled_tasks": 0,
            "in_progress_tasks": 0,
            "reboot_tasks": 0,
            "validation_tasks": 0,
            "blocked_tasks": 0,

            "last_sync_at": None,
        }


    computers = (
        WsusComputer.objects
        .filter(
            server=server
        )
    )


    total = computers.count()


    updated = computers.filter(
        update_state=
        WsusComputer.STATE_UPDATED
    ).count()


    pending = computers.filter(
        update_state=
        WsusComputer.STATE_PENDING
    ).count()


    failed = computers.filter(
        update_state=
        WsusComputer.STATE_FAILED
    ).count()


    reboot = computers.filter(
        update_state=
        WsusComputer.STATE_REBOOT
    ).count()


    unknown = computers.filter(
        update_state=
        WsusComputer.STATE_UNKNOWN
    ).count()


    if total:

        updated_percent = round(
            (
                updated
                / total
            )
            * 100,
            1,
        )

    else:

        updated_percent = 0


    tasks = (
        WsusMaintenanceTask.objects
        .filter(
            computer__server=server
        )
    )


    open_tasks = (
        tasks
        .exclude(
            status__in=[
                WsusMaintenanceTask.STATUS_COMPLETED,
                WsusMaintenanceTask.STATUS_CANCELLED,
            ]
        )
        .count()
    )


    return {

        "available":
            True,

        "server_name":
            server.name,

        "hostname":
            server.hostname,

        "port":
            server.port,

        "last_sync_at":
            server.last_sync_at,


        "total":
            total,

        "updated":
            updated,

        "pending":
            pending,

        "failed":
            failed,

        "reboot":
            reboot,

        "unknown":
            unknown,

        "updated_percent":
            updated_percent,


        "open_tasks":
            open_tasks,


        "pending_tasks":
            tasks.filter(
                status=
                WsusMaintenanceTask.STATUS_PENDING
            ).count(),


        "scheduled_tasks":
            tasks.filter(
                status=
                WsusMaintenanceTask.STATUS_SCHEDULED
            ).count(),


        "in_progress_tasks":
            tasks.filter(
                status=
                WsusMaintenanceTask.STATUS_IN_PROGRESS
            ).count(),


        "reboot_tasks":
            tasks.filter(
                status=
                WsusMaintenanceTask.STATUS_REBOOT
            ).count(),


        "validation_tasks":
            tasks.filter(
                status=
                WsusMaintenanceTask.STATUS_VALIDATION
            ).count(),


        "blocked_tasks":
            tasks.filter(
                status=
                WsusMaintenanceTask.STATUS_BLOCKED
            ).count(),

    }