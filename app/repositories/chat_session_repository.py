from __future__ import annotations

import json
from typing import Any, Dict, Optional

from redis.asyncio import Redis


def _session_key(session_id: str) -> str:
    return f"chat_session:{session_id}"


async def create_session(redis: Redis, session_id: str, data: Dict[str, Any], ttl_seconds: int = 60 * 60) -> None:
    await redis.set(_session_key(session_id), json.dumps(data), ex=ttl_seconds)


async def get_session(redis: Redis, session_id: str) -> Optional[Dict[str, Any]]:
    raw = await redis.get(_session_key(session_id))
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def update_session(redis: Redis, session_id: str, data: Dict[str, Any], ttl_seconds: int = 60 * 60) -> None:
    await redis.set(_session_key(session_id), json.dumps(data), ex=ttl_seconds)


async def delete_session(redis: Redis, session_id: str) -> None:
    await redis.delete(_session_key(session_id))


