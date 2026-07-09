"""Minimal Langfuse public-API client — just enough to assert on traces in tests.

Stdlib-only on purpose: this is a training/test helper, not something that
belongs in an application's dependency list.
"""

import base64
import json
import urllib.parse
import urllib.request
from typing import Any

from tracing import LangfuseSettings


def _get(path: str, settings: LangfuseSettings) -> dict[str, Any]:
    auth = base64.b64encode(f"{settings.public_key}:{settings.secret_key}".encode()).decode()
    request = urllib.request.Request(
        f"{settings.host}{path}", headers={"Authorization": f"Basic {auth}"}
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 (localhost only)
        return json.loads(response.read())


def traces_by_tag(tag: str, *, limit: int = 5, settings: LangfuseSettings | None = None) -> list[dict[str, Any]]:
    settings = settings or LangfuseSettings()
    query = urllib.parse.urlencode({"tags": tag, "limit": limit})
    return _get(f"/api/public/traces?{query}", settings)["data"]


def observations_for_trace(
    trace_id: str, *, settings: LangfuseSettings | None = None
) -> list[dict[str, Any]]:
    settings = settings or LangfuseSettings()
    query = urllib.parse.urlencode({"traceId": trace_id, "limit": 20})
    return _get(f"/api/public/observations?{query}", settings)["data"]
