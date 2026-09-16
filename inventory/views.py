from ipaddress import ip_address

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from .models import Endpoint

@login_required
def endpoint_list(request):
    qs = Endpoint.objects.select_related("customer").all()
    customer = request.GET.get("customer", "").strip()
    status = request.GET.get("status", "").strip()
    q = request.GET.get("q", "").strip()

    if customer:
        qs = qs.filter(customer__code=customer)
    if status:
        qs = qs.filter(status=status)
    if q:
        text_filter = (
            Q(hostname__icontains=q)
            | Q(display_name__icontains=q)
            | Q(fqdn__icontains=q)
            | Q(group_name__icontains=q)
        )
        try:
            ip_address(q)
            text_filter |= Q(ip_address=q)
        except ValueError:
            pass
        qs = qs.filter(text_filter)

    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    return render(request, "inventory/endpoint_list.html", {"page": page, "q": q, "status": status})
