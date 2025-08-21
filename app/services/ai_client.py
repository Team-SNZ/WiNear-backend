from __future__ import annotations

import httpx
from typing import Any, Dict

from ..core.config import get_settings


async def request_recommendations(payload: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    base_url = settings.ai_backend_url.rstrip("/")
    path = settings.ai_backend_recommendations_path
    url = f"{base_url}{path}"

    timeout = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()