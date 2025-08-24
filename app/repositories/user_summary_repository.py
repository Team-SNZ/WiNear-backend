from __future__ import annotations
from typing import Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.user_summary import UserSummaryResponse

COLLECTION = "user_summary"

def _serialize(doc: dict[str, Any]) -> UserSummaryResponse:
    return UserSummaryResponse(
        id=str(doc["_id"]),
        user_id=str(doc.get("ID")) if doc.get("ID") is not None else doc.get("user_id"),
        summary=str(doc.get("Summary", "")),
        created_at=doc.get("createdAt"),
        updated_at=doc.get("updatedAt"),
    )


async def upsert_user_summary(db: AsyncIOMotorDatabase, user_id: str, summary_text: str) -> None:
    await db[COLLECTION].update_one(
        {"ID": user_id},
        {"$set": {"Summary": summary_text}},
        upsert=True,
    )


async def get_user_summary(db: AsyncIOMotorDatabase, user_id: str) -> UserSummaryResponse | None:
    doc = await db[COLLECTION].find_one({"ID": user_id})
    return _serialize(doc) if doc else None


async def delete_user_summary(db: AsyncIOMotorDatabase, user_id: str) -> None:
    await db[COLLECTION].delete_one({"ID": user_id})





