from django.contrib.auth.decorators import (
    login_required
)

from django.core.paginator import (
    Paginator
)

from django.db.models import (
    Q
)

from django.shortcuts import (
    render
)

from .models import (
    WsusComputer,
    WsusMaintenanceTask,
)


ACTIVITY_COLUMNS = [

    {
        "key":
            WsusMaintenanceTask.STATUS_PENDING,

        "label":
            "Pendente",

        "description":
            "Aguardando planejamento",
    },

    {
        "key":
            WsusMaintenanceTask.STATUS_SCHEDULED,

        "label":
            "Agendado",

        "description":
            "Janela definida",
    },

    {
        "key":
            WsusMaintenanceTask.STATUS_IN_PROGRESS,

        "label":
            "Em execução",

        "description":
            "Atualização em andamento",
    },

    {
        "key":
            WsusMaintenanceTask.STATUS_REBOOT,

        "label":
            "Aguardando reboot",

        "description":
            "Instalação concluída",
    },

    {
        "key":
            WsusMaintenanceTask.STATUS_VALIDATION,

        "label":
            "Validação",

        "description":
            "Aguardando confirmação",
    },

    {
        "key":
            WsusMaintenanceTask.STATUS_BLOCKED,

        "label":
            "Bloqueado",

        "description":
            "Existe impedimento",
    },

    {
        "key":
            WsusMaintenanceTask.STATUS_COMPLETED,

        "label":
            "Concluído",

        "description":
            "Atividade finalizada",
    },

]


@login_required
def computer_list(
    request
):


    computers = (

        WsusComputer.objects

        .select_related(
            "server",
            "server__customer",
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

            update_state=
            state

        )


    if group:


        computers = computers.filter(

            group_name=
            group

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


    counts = {

        "total":

            WsusComputer.objects
            .count(),


        "updated":

            WsusComputer.objects
            .filter(
                update_state=
                WsusComputer.STATE_UPDATED
            )
            .count(),


        "pending":

            WsusComputer.objects
            .filter(
                update_state=
                WsusComputer.STATE_PENDING
            )
            .count(),


        "failed":

            WsusComputer.objects
            .filter(
                update_state=
                WsusComputer.STATE_FAILED
            )
            .count(),


        "reboot":

            WsusComputer.objects
            .filter(
                update_state=
                WsusComputer.STATE_REBOOT
            )
            .count(),

    }


    return render(

        request,

        "wsus/computer_list.html",

        {

            "page":
                page,

            "q":
                q,

            "state":
                state,

            "group":
                group,

            "groups":
                groups,

            "state_choices":
                WsusComputer.STATE_CHOICES,

            "counts":
                counts,

        },

    )



@login_required
def activity_board(
    request
):


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

            priority=
            priority

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
                notes__icontains=q
            )

        )


    cards_by_status = {

        column["key"]:
            []

        for column
        in ACTIVITY_COLUMNS

    }


    for task in tasks:


        if (
            task.status
            in cards_by_status
        ):


            cards_by_status[
                task.status
            ].append(
                task
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

            "columns":
                columns,

            "counts":
                counts,

            "priority":
                priority,

            "q":
                q,

        },

    )