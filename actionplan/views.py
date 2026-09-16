from ipaddress import ip_address

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ProblemQuickEditForm
from .models import Problem, ProblemEvent


User = get_user_model()


BOARD_COLUMNS = [
    {"key": "NEW", "label": "Novo", "description": "Problemas recém-identificados"},
    {"key": "TRIAGE", "label": "Triagem", "description": "Em análise inicial"},
    {"key": "IN_PROGRESS", "label": "Em andamento", "description": "Atendimento em execução"},
    {"key": "WAITING_CUSTOMER", "label": "Aguardando cliente", "description": "Dependência do cliente"},
    {"key": "WAITING_THIRD_PARTY", "label": "Aguardando terceiro", "description": "Dependência externa"},
    {"key": "SCHEDULED", "label": "Agendado", "description": "Ação programada"},
    {"key": "REOPENED", "label": "Reaberto", "description": "Problema reincidente"},
    {"key": "RESOLVED", "label": "Resolvido", "description": "Atendimento concluído"},
    {"key": "DISMISSED", "label": "Descartado", "description": "Problema descartado"},
]


def human_duration(delta):
    seconds = abs(int(delta.total_seconds()))
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}min"
    return f"{max(1, minutes)}min"


def normalize_datetime(value):
    if not value:
        return None
    return value.replace(second=0, microsecond=0)


def format_datetime(value):
    if not value:
        return "Não definida"
    return timezone.localtime(value).strftime("%d/%m/%Y %H:%M")


def build_problem_row(problem, now):
    overdue = False
    sla_text = "Sem prazo"
    due_input = ""

    if problem.due_at:
        delta = problem.due_at - now

        if delta.total_seconds() < 0:
            overdue = True
            sla_text = "Vencido há " + human_duration(delta)
        else:
            sla_text = human_duration(delta) + " restantes"

        due_input = timezone.localtime(
            problem.due_at
        ).strftime("%Y-%m-%dT%H:%M")

    return {
        "problem": problem,
        "sla_text": sla_text,
        "overdue": overdue,
        "age_text": human_duration(now - problem.first_seen_at),
        "due_input": due_input,
    }


def get_open_counts():
    qs = Problem.objects.filter(technical_status="OPEN")

    return {
        "total": qs.count(),
        "p0": qs.filter(priority="P0").count(),
        "p1": qs.filter(priority="P1").count(),
        "p2": qs.filter(priority="P2").count(),
    }


def get_quick_edit_context():
    return {
        "users": (
            User.objects
            .filter(is_active=True)
            .order_by("first_name", "username")
        ),
        "workflow_choices": Problem.WORKFLOW_CHOICES,
    }


def build_search_filter(q):
    result = (
        Q(endpoint__hostname__icontains=q)
        | Q(endpoint__display_name__icontains=q)
        | Q(endpoint__fqdn__icontains=q)
        | Q(problem_type__name__icontains=q)
        | Q(problem_type__code__icontains=q)
        | Q(assigned_to__username__icontains=q)
    )

    try:
        ip_address(q)
        result |= Q(endpoint__ip_address=q)
    except ValueError:
        pass

    return result


@login_required
def problem_board(request):
    problems = (
        Problem.objects
        .select_related(
            "customer",
            "endpoint",
            "problem_type",
            "assigned_to",
        )
        .filter(technical_status="OPEN")
        .order_by("priority", "due_at", "first_seen_at")
    )

    priority = request.GET.get("priority", "").strip()
    q = request.GET.get("q", "").strip()

    if priority:
        problems = problems.filter(priority=priority)

    if q:
        problems = problems.filter(build_search_filter(q))

    now = timezone.now()

    cards_by_status = {
        column["key"]: []
        for column in BOARD_COLUMNS
    }

    for problem in problems:
        card = build_problem_row(problem, now)
        if problem.workflow_status in cards_by_status:
            cards_by_status[problem.workflow_status].append(card)

    columns = []

    for column in BOARD_COLUMNS:
        cards = cards_by_status[column["key"]]
        columns.append({
            **column,
            "cards": cards,
            "count": len(cards),
        })

    context = {
        "columns": columns,
        "counts": get_open_counts(),
        "priority": priority,
        "q": q,
        **get_quick_edit_context(),
    }

    return render(
        request,
        "actionplan/problem_board.html",
        context,
    )


@login_required
def problem_list(request):
    problems = (
        Problem.objects
        .select_related(
            "customer",
            "endpoint",
            "problem_type",
            "assigned_to",
        )
        .filter(technical_status="OPEN")
    )

    priority = request.GET.get("priority", "").strip()
    workflow_status = request.GET.get("status", "").strip()
    q = request.GET.get("q", "").strip()

    if priority:
        problems = problems.filter(priority=priority)

    if workflow_status:
        problems = problems.filter(
            workflow_status=workflow_status
        )

    if q:
        problems = problems.filter(build_search_filter(q))

    problems = problems.order_by(
        "priority",
        "due_at",
        "first_seen_at",
    )

    now = timezone.now()

    rows = [
        build_problem_row(problem, now)
        for problem in problems
    ]

    page = Paginator(rows, 25).get_page(
        request.GET.get("page")
    )

    context = {
        "page": page,
        "priority": priority,
        "workflow_status": workflow_status,
        "q": q,
        "counts": get_open_counts(),
        **get_quick_edit_context(),
    }

    return render(
        request,
        "actionplan/problem_list.html",
        context,
    )


@login_required
@require_POST
def problem_update(request, pk):
    problem = get_object_or_404(
        Problem.objects.select_related(
            "assigned_to",
            "problem_type",
            "endpoint",
        ),
        pk=pk,
    )

    old_assigned_id = problem.assigned_to_id
    old_assigned_name = (
        problem.assigned_to.username
        if problem.assigned_to
        else "Não atribuído"
    )
    old_priority = problem.priority
    old_status = problem.workflow_status
    old_due_at = normalize_datetime(problem.due_at)

    form = ProblemQuickEditForm(
        request.POST,
        instance=problem,
    )

    if not form.is_valid():
        messages.error(
            request,
            "Não foi possível salvar a atividade. Revise os campos informados.",
        )
        return redirect(_safe_redirect_target(request))

    updated = form.save()
    events = []

    if old_assigned_id != updated.assigned_to_id:
        new_name = (
            updated.assigned_to.username
            if updated.assigned_to
            else "Não atribuído"
        )

        events.append((
            "ASSIGNMENT_CHANGED",
            f"Responsável alterado de '{old_assigned_name}' para '{new_name}'.",
        ))

    if old_priority != updated.priority:
        events.append((
            "PRIORITY_CHANGED",
            f"Criticidade alterada de '{old_priority}' para '{updated.priority}'.",
        ))

    if old_status != updated.workflow_status:
        labels = dict(Problem.WORKFLOW_CHOICES)

        events.append((
            "STATUS_CHANGED",
            (
                f"Status alterado de "
                f"'{labels.get(old_status, old_status)}' para "
                f"'{labels.get(updated.workflow_status, updated.workflow_status)}'."
            ),
        ))

    new_due_at = normalize_datetime(updated.due_at)

    if old_due_at != new_due_at:
        events.append((
            "DUE_DATE_CHANGED",
            (
                f"Data fim da atividade alterada de "
                f"'{format_datetime(old_due_at)}' para "
                f"'{format_datetime(new_due_at)}'."
            ),
        ))

    for event_type, description in events:
        ProblemEvent.objects.create(
            problem=updated,
            event_type=event_type,
            description=description,
            actor=request.user,
        )

    if events:
        messages.success(
            request,
            "Atividade atualizada com sucesso.",
        )
    else:
        messages.info(
            request,
            "Nenhuma alteração foi identificada.",
        )

    return redirect(_safe_redirect_target(request))


def _safe_redirect_target(request):
    target = request.POST.get("next", "").strip()

    if (
        target
        and url_has_allowed_host_and_scheme(
            url=target,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    ):
        return target

    return reverse("actionplan:board")
