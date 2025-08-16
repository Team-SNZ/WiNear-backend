from fastapi import HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from redis.asyncio import Redis


def get_db(request: Request) -> AsyncIOMotorDatabase:
    db = getattr(request.app.state, "mongo_db", None)
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db


def get_redis(request: Request) -> Optional[Redis]:
    redis_client: Optional[Redis] = getattr(request.app.state, "redis", None)
    if redis_client is None:
        raise HTTPException(status_code=503, detail="Redis is unavailable")
    return redis_client


