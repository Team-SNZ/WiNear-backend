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


def _id_variants(user_id: str) -> list[Any]:
    variants: list[Any] = [user_id]
    if isinstance(user_id, str) and user_id.isdigit():
        try:
            variants.append(int(user_id))
        except Exception:
            pass
    return variants

def _payload_to_update_dict(payload: UserFeaturesCreate) -> dict[str, Any]:
    # Pydantic v2 기준
    try:
        d = payload.model_dump(exclude_none=True, exclude_unset=True)
    except AttributeError:
        d = payload.dict(exclude_none=True, exclude_unset=True)

    d.pop("user_id", None)
    d.pop("id",     None)
    d.pop("_id",    None)

    return d


def _coerce_user_id_for_storage(user_id: str | None) -> Any:
    if user_id is None:
        return None
    if isinstance(user_id, str) and user_id.isdigit():
        try:
            return int(user_id)
        except Exception:
            return user_id
    return user_id


def _serialize(doc: dict[str, Any]) -> UserFeaturesResponse:
    return UserFeaturesResponse(
        id=str(doc["_id"]),
        user_id=str(doc.get("ID")) if doc.get("ID") is not None else doc.get("user_id"),
        features=doc.get("features", {}),
        created_at=doc.get("createdAt"),
        updated_at=doc.get("updatedAt"),
    )


async def create_user_features(db: AsyncIOMotorDatabase, payload: UserFeaturesCreate) -> str:
    now = datetime.now(timezone.utc)
    doc: dict[str, Any] = {
        "ID": _coerce_user_id_for_storage(payload.user_id),
        "Features": payload.features.model_dump(),
        "createdAt": now,
        "updated_at": now,
    }
    result = await db[COLLECTION].insert_one(doc)
    return str(result.inserted_id)


async def get_user_features_by_oid(db: AsyncIOMotorDatabase, document_id: str) -> UserFeaturesResponse | None:
    oid = _to_object_id(document_id)
    doc = await db[COLLECTION].find_one({"_id": oid})
    return _serialize(doc) if doc else None


async def get_user_features_by_user_id(db: AsyncIOMotorDatabase, user_id: str) -> UserFeaturesResponse | None:
    doc = await db[COLLECTION].find_one(
        {"ID": {"$in": _id_variants(user_id)}}
    )
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
        .sort("createdAt", -1)
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
        update_doc["ID"] = _coerce_user_id_for_storage(data.user_id)
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
        update_doc["ID"] = _coerce_user_id_for_storage(data.user_id)
    if data.features is not None:
        update_doc["Features"] = data.features

    doc = await db[COLLECTION].find_one_and_update(
        {"ID": {"$in": _id_variants(user_id)}},
        {"$set": update_doc},
        return_document=ReturnDocument.AFTER,
    )
    return _serialize(doc) if doc else None

async def upsert_user_features(db: AsyncIOMotorDatabase, payload: UserFeaturesCreate) -> str:
    """
    user_id를 기준으로 upsert.
    - 있으면 업데이트
    - 없으면 새로 생성
    """
    col = db[COLLECTION]
    user_id = str(payload.user_id)

    doc = await col.find_one_and_update(
        {"ID": {"$in": _id_variants(user_id)}},
        {
            "$setOnInsert": {
                "ID": user_id,
                "createdAt": datetime.now(timezone.utc),
            },
            "$set": {
                **_payload_to_update_dict(payload),
                "updatedAt": datetime.now(timezone.utc),
            },
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    return str(doc["_id"])


async def delete_user_features_by_oid(db: AsyncIOMotorDatabase, document_id: str) -> bool:
    oid = _to_object_id(document_id)
    result = await db[COLLECTION].delete_one({"_id": oid})
    return result.deleted_count == 1


async def delete_user_features_by_user_id(db: AsyncIOMotorDatabase, user_id: str) -> bool:
    result = await db[COLLECTION].delete_one({"ID": {"$in": _id_variants(user_id)}})
    return result.deleted_count == 1

