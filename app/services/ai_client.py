from __future__ import annotations

import httpx
from typing import Any, Dict

from ..core.config import get_settings


async def request_recommendations(payload: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    base_url = settings.ai_backend_url.rstrip("/")
    path = settings.ai_backend_recommendations_path
    url = f"{base_url}{path}"
    timeout = settings.ai_backend_timeout_seconds

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


