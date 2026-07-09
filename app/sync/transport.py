"""Sync transport over stdlib urllib."""

from __future__ import annotations

import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class SyncClient:
    def __init__(self, server_url: str, api_token: str, client_id: str):
        self.server_url = server_url.rstrip("/")
        self.api_token = api_token
        self.client_id = client_id

    def push(self, changes: list[dict], *, timeout: int = 10) -> bool:
        url = f"{self.server_url}/api/v1/push"
        payload = json.dumps({"changes": changes}, default=str).encode("utf-8")
        req = Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        })
        try:
            with urlopen(req, timeout=timeout) as resp:
                return resp.status // 100 == 2
        except (URLError, HTTPError, OSError, ValueError):
            return False

    def pull(self, since: str | None, schema_version: int, *, timeout: int = 10) -> list[dict] | None:
        url = f"{self.server_url}/api/v1/pull"
        qs = f"?schema_version={schema_version}"
        if since:
            qs += f"&since={since}"
        req = Request(url + qs, headers={
            "Authorization": f"Bearer {self.api_token}",
        })
        try:
            with urlopen(req, timeout=timeout) as resp:
                if resp.status // 100 != 2:
                    return None
                return json.loads(resp.read())
        except (URLError, HTTPError, OSError, ValueError):
            return None


class FakeTransport:
    """Injectable fake transport for offline verification/tests."""

    def __init__(self, pushes_ok: bool = True) -> None:
        self.pushes_ok = pushes_ok
        self.pushes: list[list[dict]] = []
        self.pulls: list[tuple[str | None, int]] = []

    def push(self, changes: list[dict], **_) -> bool:
        self.pushes.append(list(changes))
        return self.pushes_ok

    def pull(self, since: str | None, schema_version: int, **_) -> list[dict] | None:
        self.pulls.append((since, schema_version))
        return [] if self.pushes_ok else None
