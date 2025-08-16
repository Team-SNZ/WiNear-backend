from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..repositories.user_features_repository import (
    create_user_features,
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


def map_string_to_int(key: str, value) -> int:
    """문자열 값을 1-5 정수로 매핑하는 함수"""
    print(f"DEBUG: map_string_to_int called with key='{key}', value='{value}', type={type(value)}")
    
    # 이미 정수인 경우 그대로 반환
    if isinstance(value, int):
        print(f"DEBUG: Value is already int: {value}")
        return value
    
    # 문자열이 아닌 경우 0 반환
    if not isinstance(value, str):
        print(f"DEBUG: Value is not string, returning 0")
        return 0
    
    # 각 키별 매핑 정의
    mappings = {
        "리더십": {
            "무조건 따름": 1,
            "따르는 편": 2,
            "보통": 3,
            "리드하는 편": 4,
            "무조건 리드": 5,
        },
        "말수": {
            "매우 적다": 1,
            "적다": 2,
            "보통": 3,
            "많다": 4,
            "매우 많다": 5,
        },
        "여행일정강도": {
            "매우 여유있게": 1,
            "꽤 여유있게": 2,
            "보통": 3,
            "꽤 빡빡하게": 4,
            "매우 빡빡하게": 5,
        },
        "청결민감도": {
            "매우 민감": 1,
            "꽤 민감": 2,
            "보통": 3,
            "둔감": 4,
            "매우 둔감": 5,
        },
    }
    
    # 해당 키의 매핑이 있으면 사용
    if key in mappings:
        mapped_value = mappings[key].get(value, 0)
        print(f"DEBUG: Mapped '{value}' to {mapped_value} for key '{key}'")
        return mapped_value
    
    # 매핑이 없으면 0 반환
    print(f"DEBUG: No mapping found for key '{key}', returning 0")
    return 0


@router.post("", response_model=dict, summary="User-features 컬렉션에 새 데이터 등록")
async def create_route(
    payload: UserFeaturesCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, str]:
    new_id = await create_user_features(db, payload)
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
    doc = await get_user_features_by_user_id(db, user_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Not found")
    # polygon_values를 매핑 함수를 사용하여 생성
    polygon_labels = ["체력", "리더십", "말수", "여행일정강도", "청결민감도"]
    polygon_values = []
    
    print(f"DEBUG: doc.features = {doc.features}")
    
    for label in polygon_labels:
        raw_value = doc.features.get(label, 0)
        print(f"DEBUG: Processing label='{label}', raw_value='{raw_value}'")
        mapped_value = map_string_to_int(label, raw_value)
        print(f"DEBUG: Mapped value for '{label}': {mapped_value}")
        polygon_values.append(mapped_value)
    
    print(f"DEBUG: Final polygon_values = {polygon_values}")
    
    return UserFeaturesAnalysisResponse(
        user_id=doc.user_id or user_id,
        user_name=None,
        travel_keywords=doc.features.get("여행희망지역", []),
        personal_keywords=doc.features.get("싫어하는기후", []),
        travel_purposes=doc.features.get("여행목적", []),
        polygon_labels=polygon_labels,
        polygon_values=polygon_values,
    )


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

