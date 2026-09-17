from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from .forms import WsusTaskForm
from .models import (
    WsusComputer,
    WsusMaintenanceEvent,
    WsusMaintenanceTask,
)


User = get_user_model()


ACTIVITY_COLUMNS = [

    {
        "key": WsusMaintenanceTask.STATUS_PENDING,
        "label": "Pendente",
        "description": "Aguardando planejamento",
    },

    {
        "key": WsusMaintenanceTask.STATUS_SCHEDULED,
        "label": "Agendado",
        "description": "Janela definida",
    },

    {
        "key": WsusMaintenanceTask.STATUS_IN_PROGRESS,
        "label": "Em execução",
        "description": "Atualização em andamento",
    },

    {
        "key": WsusMaintenanceTask.STATUS_REBOOT,
        "label": "Aguardando reboot",
        "description": "Instalação concluída",
    },

    {
        "key": WsusMaintenanceTask.STATUS_VALIDATION,
        "label": "Validação",
        "description": "Aguardando confirmação",
    },

    {
        "key": WsusMaintenanceTask.STATUS_BLOCKED,
        "label": "Bloqueado",
        "description": "Existe impedimento",
    },

    {
        "key": WsusMaintenanceTask.STATUS_COMPLETED,
        "label": "Concluído",
        "description": "Atividade finalizada",
    },

]


EVENT_LABELS = {
    "CREATED": "Atividade criada",
    "ASSIGNMENT_CHANGED": "Responsável alterado",
    "PRIORITY_CHANGED": "Criticidade alterada",
    "STATUS_CHANGED": "Status alterado",
    "START_CHANGED": "Início previsto alterado",
    "END_CHANGED": "Fim previsto alterado",
    "REBOOT_CHANGED": "Permissão de reboot alterada",
    "NOTES_CHANGED": "Observações atualizadas",
}


EVENT_TONES = {
    "CREATED": "info",
    "ASSIGNMENT_CHANGED": "info",
    "PRIORITY_CHANGED": "warning",
    "STATUS_CHANGED": "primary",
    "START_CHANGED": "info",
    "END_CHANGED": "info",
    "REBOOT_CHANGED": "warning",
    "NOTES_CHANGED": "secondary",
}


def _active_task_statuses():
    return [
        value
        for value, _label
        in WsusMaintenanceTask.STATUS_CHOICES
        if value not in {
            WsusMaintenanceTask.STATUS_COMPLETED,
            WsusMaintenanceTask.STATUS_CANCELLED,
        }
    ]


def _task_form_context():
    return {
        "users": (
            User.objects
            .filter(is_active=True)
            .order_by("first_name", "username")
        ),
        "priority_choices":
            WsusMaintenanceTask.PRIORITY_CHOICES,
        "task_status_choices":
            WsusMaintenanceTask.STATUS_CHOICES,
    }


def _safe_redirect_target(
    request,
    fallback_name="wsus:activities",
):
    target = request.POST.get(
        "next",
        "",
    ).strip()

    if (
        target
        and url_has_allowed_host_and_scheme(
            url=target,
            allowed_hosts={
                request.get_host()
            },
            require_https=request.is_secure(),
        )
    ):
        return target

    return reverse(
        fallback_name
    )


def _user_display(user):
    if not user:
        return "Não atribuído"

    full_name = user.get_full_name().strip()

    if full_name:
        return (
            f"{full_name} "
            f"({user.username})"
        )

    return user.username


def _format_datetime(value):
    if not value:
        return "Não definido"

    return timezone.localtime(
        value
    ).strftime(
        "%d/%m/%Y %H:%M"
    )


def _datetime_input(value):
    if not value:
        return ""

    return timezone.localtime(
        value
    ).strftime(
        "%Y-%m-%dT%H:%M"
    )


@login_required
def computer_list(request):

    active_tasks = (
        WsusMaintenanceTask.objects
        .filter(
            status__in=
            _active_task_statuses()
        )
        .select_related(
            "assigned_to"
        )
        .order_by(
            "-created_at"
        )
    )

    computers = (
        WsusComputer.objects
        .select_related(
            "server",
            "server__customer",
        )
        .prefetch_related(
            Prefetch(
                "maintenance_tasks",
                queryset=active_tasks,
                to_attr=
                "open_maintenance_tasks",
            )
        )
        .all()
        .order_by(
            "hostname"
        )
    )

    q = request.GET.get(
        "q",
        "",
    ).strip()

    state = request.GET.get(
        "state",
        "",
    ).strip()

    group = request.GET.get(
        "group",
        "",
    ).strip()

    if q:
        computers = computers.filter(
            Q(
                hostname__icontains=q
            )
            |
            Q(
                ip_address__icontains=q
            )
            |
            Q(
                os_name__icontains=q
            )
            |
            Q(
                group_name__icontains=q
            )
        )

    if state:
        computers = computers.filter(
            update_state=state
        )

    if group:
        computers = computers.filter(
            group_name=group
        )

    groups = (
        WsusComputer.objects
        .exclude(
            group_name=""
        )
        .values_list(
            "group_name",
            flat=True,
        )
        .distinct()
        .order_by(
            "group_name"
        )
    )

    paginator = Paginator(
        computers,
        50,
    )

    page = paginator.get_page(
        request.GET.get(
            "page"
        )
    )

    base_computers = (
        WsusComputer.objects
        .all()
    )

    counts = {
        "total":
            base_computers.count(),

        "updated":
            base_computers.filter(
                update_state=
                WsusComputer.STATE_UPDATED
            ).count(),

        "pending":
            base_computers.filter(
                update_state=
                WsusComputer.STATE_PENDING
            ).count(),

        "failed":
            base_computers.filter(
                update_state=
                WsusComputer.STATE_FAILED
            ).count(),

        "reboot":
            base_computers.filter(
                update_state=
                WsusComputer.STATE_REBOOT
            ).count(),
    }

    return render(
        request,
        "wsus/computer_list.html",
        {
            "page": page,
            "q": q,
            "state": state,
            "group": group,
            "groups": groups,
            "state_choices":
                WsusComputer.STATE_CHOICES,
            "counts": counts,
            **_task_form_context(),
        },
    )


@login_required
def activity_board(request):

    tasks = (
        WsusMaintenanceTask.objects
        .select_related(
            "computer",
            "computer__server",
            "assigned_to",
        )
        .exclude(
            status=
            WsusMaintenanceTask.STATUS_CANCELLED
        )
        .order_by(
            "priority",
            "planned_end_at",
            "-created_at",
        )
    )

    priority = request.GET.get(
        "priority",
        "",
    ).strip()

    q = request.GET.get(
        "q",
        "",
    ).strip()

    if priority:
        tasks = tasks.filter(
            priority=priority
        )

    if q:
        tasks = tasks.filter(
            Q(
                computer__hostname__icontains=q
            )
            |
            Q(
                computer__ip_address__icontains=q
            )
            |
            Q(
                assigned_to__username__icontains=q
            )
            |
            Q(
                assigned_to__first_name__icontains=q
            )
            |
            Q(
                assigned_to__last_name__icontains=q
            )
            |
            Q(
                notes__icontains=q
            )
        )

    cards_by_status = {
        column["key"]: []
        for column
        in ACTIVITY_COLUMNS
    }

    for task in tasks:

        if (
            task.status
            not in cards_by_status
        ):
            continue

        cards_by_status[
            task.status
        ].append(
            {
                "task":
                    task,

                "start_input":
                    _datetime_input(
                        task.planned_start_at
                    ),

                "end_input":
                    _datetime_input(
                        task.planned_end_at
                    ),
            }
        )

    columns = []

    for column in ACTIVITY_COLUMNS:

        cards = cards_by_status[
            column["key"]
        ]

        columns.append(
            {
                **column,
                "cards":
                    cards,
                "count":
                    len(cards),
            }
        )

    base_tasks = (
        WsusMaintenanceTask.objects
        .exclude(
            status=
            WsusMaintenanceTask.STATUS_CANCELLED
        )
    )

    counts = {
        "total":
            base_tasks.count(),

        "p0":
            base_tasks.filter(
                priority="P0"
            ).count(),

        "p1":
            base_tasks.filter(
                priority="P1"
            ).count(),

        "p2":
            base_tasks.filter(
                priority="P2"
            ).count(),
    }

    return render(
        request,
        "wsus/activity_board.html",
        {
            "columns": columns,
            "counts": counts,
            "priority": priority,
            "q": q,
            **_task_form_context(),
        },
    )


@login_required
@require_POST
@transaction.atomic
def task_create(
    request,
    computer_id,
):

    computer = get_object_or_404(
        WsusComputer.objects
        .select_related(
            "server"
        ),
        pk=computer_id,
    )

    existing = (
        WsusMaintenanceTask.objects
        .filter(
            computer=computer,
            status__in=
            _active_task_statuses(),
        )
        .order_by(
            "-created_at"
        )
        .first()
    )

    if existing:

        messages.warning(
            request,
            (
                f"{computer.hostname} já possui "
                f"a atividade #{existing.id} aberta."
            ),
        )

        return redirect(
            _safe_redirect_target(
                request,
                fallback_name=
                "wsus:computers",
            )
        )

    form = WsusTaskForm(
        request.POST
    )

    if not form.is_valid():

        messages.error(
            request,
            (
                "Não foi possível criar "
                "a atividade WSUS. "
                "Revise os campos."
            ),
        )

        return redirect(
            _safe_redirect_target(
                request,
                fallback_name=
                "wsus:computers",
            )
        )

    task = form.save(
        commit=False
    )

    task.computer = computer

    if (
        task.status
        ==
        WsusMaintenanceTask.STATUS_COMPLETED
    ):
        task.completed_at = (
            timezone.now()
        )

    task.save()

    WsusMaintenanceEvent.objects.create(
        task=task,
        event_type="CREATED",
        description=(
            "Atividade WSUS criada. "
            f"Responsável: "
            f"{_user_display(task.assigned_to)}. "
            f"Criticidade: "
            f"{task.priority}. "
            f"Status: "
            f"{task.get_status_display()}. "
            f"Início previsto: "
            f"{_format_datetime(task.planned_start_at)}. "
            f"Fim previsto: "
            f"{_format_datetime(task.planned_end_at)}. "
            f"Reboot permitido: "
            f"{'Sim' if task.allow_reboot else 'Não'}."
        ),
        actor=request.user,
    )

    messages.success(
        request,
        (
            f"Atividade #{task.id} criada "
            f"para {computer.hostname}."
        ),
    )

    return redirect(
        _safe_redirect_target(
            request,
            fallback_name=
            "wsus:activities",
        )
    )


@login_required
@require_POST
@transaction.atomic
def task_update(
    request,
    pk,
):

    task = get_object_or_404(
        WsusMaintenanceTask.objects
        .select_for_update()
        .select_related(
            "computer",
            "assigned_to",
        ),
        pk=pk,
    )

    old = {
        "assigned_to_id":
            task.assigned_to_id,

        "assigned_to":
            _user_display(
                task.assigned_to
            ),

        "priority":
            task.priority,

        "status":
            task.status,

        "planned_start_at":
            task.planned_start_at,

        "planned_end_at":
            task.planned_end_at,

        "allow_reboot":
            task.allow_reboot,

        "notes":
            task.notes,
    }

    form = WsusTaskForm(
        request.POST,
        instance=task,
    )

    if not form.is_valid():

        messages.error(
            request,
            (
                "Não foi possível atualizar "
                "a atividade WSUS. "
                "Revise os campos."
            ),
        )

        return redirect(
            _safe_redirect_target(
                request
            )
        )

    task = form.save(
        commit=False
    )

    if (
        task.status
        ==
        WsusMaintenanceTask.STATUS_COMPLETED
    ):

        if not task.completed_at:
            task.completed_at = (
                timezone.now()
            )

    else:
        task.completed_at = None

    task.save()

    events = []

    if (
        old["assigned_to_id"]
        !=
        task.assigned_to_id
    ):

        events.append(
            (
                "ASSIGNMENT_CHANGED",
                (
                    "Responsável alterado de "
                    f"'{old['assigned_to']}' "
                    "para "
                    f"'{_user_display(task.assigned_to)}'."
                ),
            )
        )

    if (
        old["priority"]
        !=
        task.priority
    ):

        events.append(
            (
                "PRIORITY_CHANGED",
                (
                    "Criticidade alterada de "
                    f"'{old['priority']}' "
                    "para "
                    f"'{task.priority}'."
                ),
            )
        )

    if (
        old["status"]
        !=
        task.status
    ):

        labels = dict(
            WsusMaintenanceTask.STATUS_CHOICES
        )

        events.append(
            (
                "STATUS_CHANGED",
                (
                    "Status alterado de "
                    f"'{labels.get(old['status'], old['status'])}' "
                    "para "
                    f"'{labels.get(task.status, task.status)}'."
                ),
            )
        )

    if (
        old["planned_start_at"]
        !=
        task.planned_start_at
    ):

        events.append(
            (
                "START_CHANGED",
                (
                    "Início previsto alterado de "
                    f"'{_format_datetime(old['planned_start_at'])}' "
                    "para "
                    f"'{_format_datetime(task.planned_start_at)}'."
                ),
            )
        )

    if (
        old["planned_end_at"]
        !=
        task.planned_end_at
    ):

        events.append(
            (
                "END_CHANGED",
                (
                    "Fim previsto alterado de "
                    f"'{_format_datetime(old['planned_end_at'])}' "
                    "para "
                    f"'{_format_datetime(task.planned_end_at)}'."
                ),
            )
        )

    if (
        old["allow_reboot"]
        !=
        task.allow_reboot
    ):

        events.append(
            (
                "REBOOT_CHANGED",
                (
                    "Reboot permitido alterado para "
                    f"{'Sim' if task.allow_reboot else 'Não'}."
                ),
            )
        )

    if (
        old["notes"]
        !=
        task.notes
    ):

        events.append(
            (
                "NOTES_CHANGED",
                (
                    "Observações da atividade "
                    "foram atualizadas."
                ),
            )
        )

    for (
        event_type,
        description,
    ) in events:

        WsusMaintenanceEvent.objects.create(
            task=task,
            event_type=event_type,
            description=description,
            actor=request.user,
        )

    if events:

        messages.success(
            request,
            (
                f"Atividade #{task.id} "
                "atualizada com sucesso."
            ),
        )

    else:

        messages.info(
            request,
            (
                f"Nenhuma alteração foi "
                f"identificada na atividade "
                f"#{task.id}."
            ),
        )

    return redirect(
        _safe_redirect_target(
            request
        )
    )


@login_required
@require_GET
def task_history(
    request,
    pk,
):

    task = get_object_or_404(
        WsusMaintenanceTask.objects
        .select_related(
            "computer",
            "computer__server",
            "assigned_to",
        ),
        pk=pk,
    )

    events = (
        task.timeline
        .select_related(
            "actor"
        )
        .all()
        .order_by(
            "-created_at"
        )
    )

    event_items = []

    for event in events:

        event_items.append(
            {
                "id":
                    event.id,

                "type":
                    event.event_type,

                "label":
                    EVENT_LABELS.get(
                        event.event_type,
                        event.event_type,
                    ),

                "tone":
                    EVENT_TONES.get(
                        event.event_type,
                        "secondary",
                    ),

                "description":
                    event.description,

                "actor":
                    _user_display(
                        event.actor
                    )
                    if event.actor
                    else "Sistema",

                "created_at":
                    _format_datetime(
                        event.created_at
                    ),
            }
        )

    return JsonResponse(
        {
            "ok": True,

            "task": {
                "id":
                    task.id,

                "hostname":
                    task.computer.hostname,

                "ip":
                    (
                        task.computer.ip_address
                        or ""
                    ),

                "group":
                    (
                        task.computer.group_name
                        or ""
                    ),

                "priority":
                    task.priority,

                "status":
                    task.get_status_display(),

                "assigned_to":
                    _user_display(
                        task.assigned_to
                    ),

                "planned_start_at":
                    _format_datetime(
                        task.planned_start_at
                    ),

                "planned_end_at":
                    _format_datetime(
                        task.planned_end_at
                    ),

                "allow_reboot":
                    task.allow_reboot,

                "completed_at":
                    _format_datetime(
                        task.completed_at
                    )
                    if task.completed_at
                    else "",

                "notes":
                    task.notes,
            },

            "events":
                event_items,
        }
    )
