from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from actionplan.models import Problem
from customers.models import Customer
from inventory.models import Endpoint
from integrations.models import SyncRun

@login_required
def home(request):
    customer = Customer.objects.filter(code="BONJA-MOCK", active=True).first() or Customer.objects.filter(active=True).order_by("id").first()

    if not customer:
        return render(request, "dashboard/home.html", {"customer": None})

    endpoints = Endpoint.objects.filter(customer=customer)
    status_rows = endpoints.values("status").annotate(total=Count("id"))
    status_map = {row["status"]: row["total"] for row in status_rows}

    open_problems = Problem.objects.filter(customer=customer, technical_status="OPEN")
    last_sync = SyncRun.objects.filter(customer=customer).first()

    context = {
        "customer": customer,
        "total_endpoints": endpoints.count(),
        "ok_count": status_map.get(Endpoint.STATUS_OK, 0),
        "warning_count": status_map.get(Endpoint.STATUS_WARNING, 0),
        "critical_count": status_map.get(Endpoint.STATUS_CRITICAL, 0),
        "unknown_count": status_map.get(Endpoint.STATUS_UNKNOWN, 0),
        "p0_count": open_problems.filter(priority="P0").count(),
        "p1_count": open_problems.filter(priority="P1").count(),
        "p2_count": open_problems.filter(priority="P2").count(),
        "open_problem_count": open_problems.count(),
        "last_sync": last_sync,
    }
    return render(request, "dashboard/home.html", context)
