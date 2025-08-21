from fastapi import HTTPException, Request, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
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


def get_user_features_collection(db: AsyncIOMotorDatabase = Depends(get_db)) -> AsyncIOMotorCollection:
    """user_features 컬렉션 반환"""
    return db["user_features"]


def get_travel_info_collection(db: AsyncIOMotorDatabase = Depends(get_db)) -> AsyncIOMotorCollection:
    """travel_info 컬렉션 반환"""
    return db["travel_info"]


def get_travel_url_collection(db: AsyncIOMotorDatabase = Depends(get_db)) -> AsyncIOMotorCollection:
    """travel_url 컬렉션 반환"""
    return db["travel_url"]


