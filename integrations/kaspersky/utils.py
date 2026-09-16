from __future__ import annotations

from datetime import datetime, timezone
from ipaddress import IPv4Address
from typing import Any

def unwrap_ksc(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, list):
        return [unwrap_ksc(item) for item in value]

    if isinstance(value, dict):
        if "type" in value and "value" in value:
            type_name = str(value.get("type", "")).lower()
            inner = value.get("value")
            if type_name == "long":
                try:
                    return int(inner)
                except (TypeError, ValueError):
                    return inner
            if type_name == "array":
                return [unwrap_ksc(item) for item in (inner or [])]
            return unwrap_ksc(inner)

        return {str(k): unwrap_ksc(v) for k, v in value.items()}

    return value

def ipv4_from_ksc(value: Any) -> str | None:
    value = unwrap_ksc(value)
    if value in (None, ""):
        return None

    text = str(value).strip()
    if "." in text:
        try:
            return str(IPv4Address(text))
        except ValueError:
            return None

    try:
        number = int(value)
        if number < 0:
            number += 2**32
        if not 0 <= number <= 0xFFFFFFFF:
            return None
        return str(IPv4Address(number))
    except (TypeError, ValueError):
        return None

def parse_ksc_datetime(value: Any) -> datetime | None:
    value = unwrap_ksc(value)
    if not value:
        return None

    text = str(value).strip()
    try:
        # Python aceita ISO 8601 com Z ao trocar por +00:00.
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None
