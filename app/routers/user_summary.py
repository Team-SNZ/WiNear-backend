from fastapi import APIRouter, Depends, HTTPException

from app.schemas.user_summary import UserSummaryResponse

from ..dependencies.db import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..repositories.user_summary_repository import (
    delete_user_summary,
    get_user_summary,
    upsert_user_summary,
)

router = APIRouter(prefix="/user-summary", tags=["user-summary"])

@router.get("/{user_id}", response_model=UserSummaryResponse, summary="User-summary 컬렉션에서 user_id로 데이터 조회")
async def get_by_user_id_route(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> UserSummaryResponse:
    docs = await get_user_summary(db, user_id)
    if docs is None:
        raise HTTPException(status_code=404, detail="Not found")
    return docs


@router.post("", summary="User-summary 컬렉션에 새 데이터 등록")
async def create_route(user_id: str, summary: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> None:
    await upsert_user_summary(db, user_id, summary)


@router.delete("/{user_id}", summary="User-summary 컬렉션에서 user_id로 데이터 삭제")
async def delete_by_user_id_route(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> None:
    await delete_user_summary(db, user_id)