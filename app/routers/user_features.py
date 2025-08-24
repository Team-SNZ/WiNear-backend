from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.analysis_result import get_user_analysis_data

from ..repositories.user_features_repository import (
    upsert_user_features,
    delete_user_features_by_oid,
    delete_user_features_by_user_id,
    get_user_features_by_oid,
    get_user_features_by_user_id,
    list_user_features,
    update_user_features_by_oid,
    update_user_features_by_user_id,
)
from ..schemas.user_features import (
    UserFeaturesCreate,
    UserFeaturesListResponse,
    UserFeaturesResponse,
    UserFeaturesUpdate,
    UserFeaturesAnalysisResponse,
)
from ..dependencies.db import get_db


router = APIRouter(prefix="/user-features", tags=["user-features"])


@router.post("", response_model=dict, summary="User-features 컬렉션에 새 데이터 등록")
async def create_route(
    payload: UserFeaturesCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, str]:
    new_id = await upsert_user_features(db, payload)
    return {"id": new_id}


@router.get("/{document_id}", response_model=UserFeaturesResponse, summary="User-features 컬렉션에서 objectId로 데이터 조회")
async def get_by_oid_route(
    document_id: str = Path(..., description="ObjectId"),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserFeaturesResponse:
    try:
        doc = await get_user_features_by_oid(db, document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document id")
    if doc is None:
        raise HTTPException(status_code=404, detail="Not found")
    return doc


@router.get("/by-user/{user_id}", response_model=UserFeaturesResponse, summary="User-features 컬렉션에서 user_id로 데이터 조회")
async def get_by_user_id_route(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserFeaturesResponse:
    doc = await get_user_features_by_user_id(db, user_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Not found")
    return doc


@router.get("/analysis/{user_id}", response_model=UserFeaturesAnalysisResponse, summary="분석 페이지용: MongoDB 조회")
async def get_analysis_by_user_id_route(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserFeaturesAnalysisResponse:
    return await get_user_analysis_data(db, user_id)


@router.get("", response_model=UserFeaturesListResponse, summary="User-features 컬렉션에서 모든 데이터 조회")
async def list_route(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserFeaturesListResponse:
    return await list_user_features(db, limit=limit, offset=offset)


@router.patch("/{document_id}", response_model=UserFeaturesResponse, summary="User-features 컬렉션에서 objectId로 데이터 수정")
async def update_by_oid_route(
    document_id: str,
    data: UserFeaturesUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserFeaturesResponse:
    try:
        updated = await update_user_features_by_oid(db, document_id, data)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document id")
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.patch("/by-user/{user_id}", response_model=UserFeaturesResponse, summary="User-features 컬렉션에서 user_id로 데이터 수정")
async def update_by_user_id_route(
    user_id: str,
    data: UserFeaturesUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserFeaturesResponse:
    updated = await update_user_features_by_user_id(db, user_id, data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="User-features 컬렉션에서 objectId로 데이터 삭제")
async def delete_by_oid_route(
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    try:
        deleted = await delete_user_features_by_oid(db, document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document id")
    if not deleted:
        raise HTTPException(status_code=404, detail="Not found")
    return None


@router.delete("/by-user/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="User-features 컬렉션에서 user_id로 데이터 삭제")
async def delete_by_user_id_route(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    deleted = await delete_user_features_by_user_id(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Not found")
    return None

