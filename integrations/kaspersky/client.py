from __future__ import annotations

import base64
import os
import secrets
from dataclasses import dataclass
from typing import Any

import requests

from .utils import unwrap_ksc

HOST_FIELDS = [
    "KLHST_WKS_HOSTNAME",
    "KLHST_WKS_DN",
    "KLHST_WKS_WINHOSTNAME",
    "KLHST_WKS_FQDN",
    "KLHST_WKS_WINDOMAIN",
    "KLHST_WKS_IP_LONG",
    "KLHST_WKS_STATUS",
    "KLHST_WKS_STATUS_ID",
    "KLHST_WKS_STATUS_MASK",
    "KLHST_WKS_STATUS_HSDP",
    "KLHST_WKS_CREATED",
    "KLHST_WKS_LAST_VISIBLE",
    "KLHST_WKS_LAST_INFOUDATE",
    "KLHST_WKS_LAST_NAGENT_CONNECTED",
    "KLHST_WKS_LAST_UPDATE",
    "KLHST_WKS_LAST_FULLSCAN",
    "KLHST_WKS_LAST_SYSTEM_START",
    "KLHST_WKS_RTP_STATE",
    "KLHST_WKS_RTP_ERROR_CODE",
    "KLHST_WKS_NAG_VERSION",
    "KLHST_WKS_RTP_AV_VERSION",
    "KLHST_WKS_RTP_AV_BASES_TIME",
    "KLHST_WKS_OS_NAME",
    "KLHST_WKS_OS_BUILD_NUMBER",
    "KLHST_WKS_VIRUS_COUNT",
    "KLHST_WKS_UNCURED_COUNT",
    "KLHST_WKS_RBT_REQUIRED",
    "KLHST_WKS_EDR_STATUS",
    "KLHST_WKS_FROM_UNASSIGNED",
    "name",
]

def _bool_env(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "sim", "on"}

def _b64(text: str) -> str:
    return base64.b64encode((text or "").encode("utf-8")).decode("ascii")

@dataclass
class KSCConfig:
    host: str
    port: int = 13299
    username: str = ""
    password: str = ""
    internal_user: bool = True
    domain: str = ""
    verify_ssl: bool = True
    ca_cert: str = ""
    timeout: int = 30
    host_filter: str = '(&(KLHST_WKS_FROM_UNASSIGNED=0)(KLHST_WKS_DN="*"))'
    current_vserver_only: bool = True

    @classmethod
    def from_env(cls, host: str | None = None, port: int | None = None) -> "KSCConfig":
        return cls(
            host=host or os.getenv("KSC_HOST", ""),
            port=port or int(os.getenv("KSC_PORT", "13299")),
            username=os.getenv("KSC_USERNAME", ""),
            password=os.getenv("KSC_PASSWORD", ""),
            internal_user=_bool_env("KSC_INTERNAL_USER", True),
            domain=os.getenv("KSC_DOMAIN", ""),
            verify_ssl=_bool_env("KSC_VERIFY_SSL", True),
            ca_cert=os.getenv("KSC_CA_CERT", "").strip(),
            timeout=int(os.getenv("KSC_TIMEOUT", "30")),
            host_filter=os.getenv(
                "KSC_HOST_FILTER",
                '(&(KLHST_WKS_FROM_UNASSIGNED=0)(KLHST_WKS_DN="*"))',
            ),
            current_vserver_only=_bool_env("KSC_CURRENT_VSERVER_ONLY", True),
        )

class KSCAPIError(RuntimeError):
    pass

class KSCClient:
    def __init__(self, config: KSCConfig):
        if not config.host:
            raise ValueError("KSC_HOST nao informado.")
        self.config = config
        self.base_url = f"https://{config.host}:{config.port}/api/v1.0"
        self.http = requests.Session()
        self.session_id: str | None = None

    @property
    def verify(self):
        if not self.config.verify_ssl:
            return False
        if self.config.ca_cert:
            return self.config.ca_cert
        return True

    def _request(
        self,
        method: str,
        body: dict[str, Any] | None = None,
        authorization: str = "",
        session_id: str = "",
    ) -> dict[str, Any]:
        headers = {
            "X-KSC-RequestId": f"{secrets.token_hex(8).upper()}_{secrets.token_hex(8).upper()}",
        }
        if authorization:
            headers["Authorization"] = authorization
        sid = session_id or self.session_id or ""
        if sid:
            headers["X-KSC-Session"] = sid

        url = f"{self.base_url}/{method}"

        try:
            response = self.http.post(
                url,
                json=body or {},
                headers=headers,
                timeout=self.config.timeout,
                verify=self.verify,
            )
        except requests.RequestException as exc:
            raise KSCAPIError(f"Falha de comunicacao com {url}: {exc}") from exc

        if response.status_code == 401 and "KSCMFA" in response.headers.get("WWW-Authenticate", ""):
            raise KSCAPIError(
                "O KSC solicitou MFA/TOTP. O starter ainda nao implementa o fluxo interativo de MFA."
            )

        if response.status_code in {401, 403}:
            raise KSCAPIError(
                f"KSC retornou HTTP {response.status_code}. Valide usuario, senha, dominio/internal e permissoes da OpenAPI."
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            body_preview = response.text[:1000]
            raise KSCAPIError(
                f"KSC retornou HTTP {response.status_code} em {method}: {body_preview}"
            ) from exc

        try:
            return unwrap_ksc(response.json())
        except ValueError as exc:
            raise KSCAPIError(f"Resposta JSON invalida em {method}.") from exc

    def start_session(self) -> str:
        username = self.config.username.strip()
        password = self.config.password

        if not username or not password:
            raise KSCAPIError("KSC_USERNAME/KSC_PASSWORD nao configurados.")

        if self.config.internal_user:
            user = username
            auth = f'KSCBasic user="{_b64(user)}", pass="{_b64(password)}", internal="1"'
        else:
            domain = self.config.domain.strip()
            user = username

            if "\\" in username:
                domain, user = username.split("\\", 1)
            elif "@" in username:
                user, domain = username.split("@", 1)

            if not domain:
                raise KSCAPIError("KSC_DOMAIN e obrigatorio para conta nao interna.")

            auth = (
                f'KSCBasic user="{_b64(user)}", pass="{_b64(password)}", '
                f'domain="{_b64(domain)}", internal="0"'
            )

        result = self._request("Session.StartSession", authorization=auth)
        session_id = str(result.get("PxgRetVal") or "").strip()
        if not session_id:
            raise KSCAPIError("Session.StartSession nao retornou PxgRetVal/session id.")

        self.session_id = session_id
        return session_id

    def end_session(self):
        if not self.session_id:
            return
        try:
            self._request("Session.EndSession", session_id=self.session_id)
        finally:
            self.session_id = None

    def __enter__(self):
        self.start_session()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.end_session()

    def get_managed_hosts(self, page_size: int = 500) -> list[dict[str, Any]]:
        if not self.session_id:
            raise KSCAPIError("Sessao KSC nao iniciada.")

        find_body = {
            "wstrFilter": self.config.host_filter,
            "vecFieldsToReturn": HOST_FIELDS,
            "vecFieldsToOrder": [],
            "pParams": {
                "KLGRP_FIND_FROM_CUR_VS_ONLY": self.config.current_vserver_only,
            },
            "lMaxLifeTime": 3600,
        }

        find = self._request("HostGroup.FindHosts", body=find_body)
        accessor = str(find.get("strAccessor") or "").strip()
        if not accessor:
            raise KSCAPIError("HostGroup.FindHosts nao retornou strAccessor.")

        try:
            count_resp = self._request(
                "ChunkAccessor.GetItemsCount",
                body={"strAccessor": accessor},
            )
            count = int(count_resp.get("PxgRetVal") or 0)
            result: list[dict[str, Any]] = []

            start = 0
            while start < count:
                chunk_resp = self._request(
                    "ChunkAccessor.GetItemsChunk",
                    body={
                        "strAccessor": accessor,
                        "nStart": start,
                        "nCount": page_size,
                    },
                )
                chunk = chunk_resp.get("pChunk") or {}
                items = chunk.get("KLCSP_ITERATOR_ARRAY") or []
                if not isinstance(items, list):
                    items = [items]
                result.extend(item for item in items if isinstance(item, dict))
                start += page_size

            return result
        finally:
            try:
                self._request(
                    "ChunkAccessor.Release",
                    body={"strAccessor": accessor},
                )
            except Exception:
                pass
