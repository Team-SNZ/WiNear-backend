from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from ..schemas.user_features import (
    UserFeaturesCreate,
    UserFeaturesListResponse,
    UserFeaturesResponse,
    UserFeaturesUpdate,
)


COLLECTION = "user_features"


def _to_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise ValueError("Invalid ObjectId")
    return ObjectId(id_str)


def _serialize(doc: dict[str, Any]) -> UserFeaturesResponse:
    return UserFeaturesResponse(
        id=str(doc["_id"]),
        user_id=doc.get("user_id"),
        legacy_id=doc.get("ID"),
        features=doc.get("Features", {}),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


async def create_user_features(db: AsyncIOMotorDatabase, payload: UserFeaturesCreate) -> str:
    now = datetime.now(timezone.utc)
    doc: dict[str, Any] = {
        "user_id": payload.user_id,
        "ID": payload.legacy_id,
        "Features": payload.features,
        "created_at": now,
        "updated_at": now,
    }
    result = await db[COLLECTION].insert_one(doc)
    return str(result.inserted_id)


async def get_user_features_by_oid(db: AsyncIOMotorDatabase, document_id: str) -> UserFeaturesResponse | None:
    oid = _to_object_id(document_id)
    doc = await db[COLLECTION].find_one({"_id": oid})
    return _serialize(doc) if doc else None


async def get_user_features_by_user_id(db: AsyncIOMotorDatabase, user_id: str) -> UserFeaturesResponse | None:
    doc = await db[COLLECTION].find_one({"user_id": user_id})
    return _serialize(doc) if doc else None


async def get_user_features_by_legacy_id(db: AsyncIOMotorDatabase, legacy_id: int) -> UserFeaturesResponse | None:
    doc = await db[COLLECTION].find_one({"ID": legacy_id})
    return _serialize(doc) if doc else None


async def list_user_features(
    db: AsyncIOMotorDatabase,
    *,
    limit: int,
    offset: int,
) -> UserFeaturesListResponse:
    cursor = (
        db[COLLECTION]
        .find({}, projection=None)
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    items = [_serialize(doc) async for doc in cursor]
    total = await db[COLLECTION].count_documents({})
    return UserFeaturesListResponse(items=items, total=total)


async def update_user_features_by_oid(
    db: AsyncIOMotorDatabase,
    document_id: str,
    data: UserFeaturesUpdate,
) -> UserFeaturesResponse | None:
    oid = _to_object_id(document_id)
    update_doc: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if data.user_id is not None:
        update_doc["user_id"] = data.user_id
    if data.legacy_id is not None:
        update_doc["ID"] = data.legacy_id
    if data.features is not None:
        update_doc["Features"] = data.features

    doc = await db[COLLECTION].find_one_and_update(
        {"_id": oid},
        {"$set": update_doc},
        return_document=ReturnDocument.AFTER,
    )
    return _serialize(doc) if doc else None


async def update_user_features_by_user_id(
    db: AsyncIOMotorDatabase,
    user_id: str,
    data: UserFeaturesUpdate,
) -> UserFeaturesResponse | None:
    update_doc: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if data.user_id is not None:
        update_doc["user_id"] = data.user_id
    if data.legacy_id is not None:
        update_doc["ID"] = data.legacy_id
    if data.features is not None:
        update_doc["Features"] = data.features

    doc = await db[COLLECTION].find_one_and_update(
        {"user_id": user_id},
        {"$set": update_doc},
        return_document=ReturnDocument.AFTER,
    )
    return _serialize(doc) if doc else None


async def delete_user_features_by_oid(db: AsyncIOMotorDatabase, document_id: str) -> bool:
    oid = _to_object_id(document_id)
    result = await db[COLLECTION].delete_one({"_id": oid})
    return result.deleted_count == 1


async def delete_user_features_by_user_id(db: AsyncIOMotorDatabase, user_id: str) -> bool:
    result = await db[COLLECTION].delete_one({"user_id": user_id})
    return result.deleted_count == 1

