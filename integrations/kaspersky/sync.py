from __future__ import annotations

from django.utils import timezone

from customers.models import Customer
from inventory.models import Endpoint
from integrations.models import SyncRun

from .client import KSCClient, KSCConfig
from .utils import ipv4_from_ksc, parse_ksc_datetime

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def status_from_id(status_id):
    value = safe_int(status_id, -1)
    if value == 0:
        return Endpoint.STATUS_OK
    if value == 1:
        return Endpoint.STATUS_CRITICAL
    if value == 2:
        return Endpoint.STATUS_WARNING
    return Endpoint.STATUS_UNKNOWN

def sync_customer_hosts(customer: Customer) -> SyncRun:
    run = SyncRun.objects.create(customer=customer)

    try:
        config = KSCConfig.from_env(host=customer.ksc_host, port=customer.ksc_port)

        with KSCClient(config) as client:
            hosts = client.get_managed_hosts()

        created_count = 0
        updated_count = 0

        for host in hosts:
            hostname = str(host.get("KLHST_WKS_HOSTNAME") or host.get("KLHST_WKS_WINHOSTNAME") or "").strip()
            display_name = str(host.get("KLHST_WKS_DN") or host.get("name") or hostname).strip()

            # Enquanto nao adicionamos o identificador interno mais adequado do KSC,
            # usamos nome/hostname como chave estável inicial.
            ksc_key = str(host.get("KLHST_WKS_DN") or host.get("KLHST_WKS_HOSTNAME") or host.get("name") or "").strip()
            if not ksc_key:
                continue

            defaults = {
                "hostname": hostname,
                "display_name": display_name,
                "fqdn": str(host.get("KLHST_WKS_FQDN") or ""),
                "windows_domain": str(host.get("KLHST_WKS_WINDOMAIN") or ""),
                "ip_address": ipv4_from_ksc(host.get("KLHST_WKS_IP_LONG")),
                "group_name": "",  # O caminho/grupo KSC sera incluido na proxima fase com o campo apropriado.",
                "status": status_from_id(host.get("KLHST_WKS_STATUS_ID")),
                "status_id": safe_int(host.get("KLHST_WKS_STATUS_ID"), -1),
                "status_mask": safe_int(host.get("KLHST_WKS_STATUS"), 0),
                "agent_version": str(host.get("KLHST_WKS_NAG_VERSION") or ""),
                "antivirus_version": str(host.get("KLHST_WKS_RTP_AV_VERSION") or ""),
                "antivirus_bases_at": parse_ksc_datetime(host.get("KLHST_WKS_RTP_AV_BASES_TIME")),
                "rtp_state": safe_int(host.get("KLHST_WKS_RTP_STATE"), -1),
                "edr_status": safe_int(host.get("KLHST_WKS_EDR_STATUS"), -1),
                "last_visible_at": parse_ksc_datetime(host.get("KLHST_WKS_LAST_VISIBLE")),
                "last_agent_connection_at": parse_ksc_datetime(host.get("KLHST_WKS_LAST_NAGENT_CONNECTED")),
                "last_full_scan_at": parse_ksc_datetime(host.get("KLHST_WKS_LAST_FULLSCAN")),
                "reboot_required": bool(safe_int(host.get("KLHST_WKS_RBT_REQUIRED"), 0)),
                "virus_count": safe_int(host.get("KLHST_WKS_VIRUS_COUNT"), 0),
                "uncured_count": safe_int(host.get("KLHST_WKS_UNCURED_COUNT"), 0),
                "os_name": str(host.get("KLHST_WKS_OS_NAME") or ""),
                "os_build": str(host.get("KLHST_WKS_OS_BUILD_NUMBER") or ""),
                "raw_data": host,
            }

            _, created = Endpoint.objects.update_or_create(
                customer=customer,
                ksc_key=ksc_key,
                defaults=defaults,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        run.status = "SUCCESS"
        run.finished_at = timezone.now()
        run.hosts_received = len(hosts)
        run.endpoints_created = created_count
        run.endpoints_updated = updated_count
        run.save(
            update_fields=[
                "status",
                "finished_at",
                "hosts_received",
                "endpoints_created",
                "endpoints_updated",
            ]
        )
        return run

    except Exception as exc:
        run.status = "FAILED"
        run.finished_at = timezone.now()
        run.error_message = str(exc)
        run.save(update_fields=["status", "finished_at", "error_message"])
        raise
