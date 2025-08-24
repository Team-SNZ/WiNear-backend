from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.constants.result_keyword_ver2 import PERSONAL_KEYWORD_MAPPINGS, TRAVEL_PURPOSE_MAPPINGS, TRAVEL_KEYWORD_MAPPINGS
from ..services.analysis_result import get_user_analysis_data
from ..schemas.recommend import (
    RecommendRequest, 
    RecommendResponse,
    UserProfileRequest,
    UserProfileResponse,
    UserProfile,
    TravelRequest,
    TravelResponse,
    TravelInfo,
)
from ..services.ai_recommend_client import get_ai_recommend_client, AIRecommendClient
from ..dependencies.db import get_db, get_user_features_collection, get_travel_info_collection, get_travel_url_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("/health", summary="추천 API 상태 확인")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("", summary="사용자 추천 요청")
async def get_recommendations(
    req: RecommendRequest,
    ai_client: AIRecommendClient = Depends(get_ai_recommend_client),
) -> RecommendResponse:
    """
    AI 백엔드에서 사용자 맞춤 추천 정보를 조회
    """
    try:
        logger.info(f"사용자 추천 요청: {req.user_id}")
        
        # AI 백엔드에 추천 요청
        ai_response = await ai_client.get_user_recommendations(req.user_id)
        
        # 응답 데이터 검증 및 변환
        return RecommendResponse(
            user_id=ai_response.get("user_id", req.user_id),
            rec_people=ai_response.get("rec_people", []),
            rec_travel=ai_response.get("rec_travel", []),
            status=ai_response.get("status", "success"),
        )
        
    except Exception as e:
        logger.error(f"사용자 추천 요청 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"추천 요청 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/user-profile", summary="사용자 프로필 일괄 조회")
async def get_user_profiles(
    req: UserProfileRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    features_collection: AsyncIOMotorCollection = Depends(get_user_features_collection),
) -> UserProfileResponse:
    """
    여러 사용자의 프로필 정보를 MongoDB에서 조회하고 분석된 키워드 포함
    """
    try:
        logger.info(f"사용자 프로필 조회 요청: {len(req.user_ids)}명")
        
        users = []
        
        # 각 사용자 ID에 대해 MongoDB 조회
        async for doc in features_collection.find({"ID": {"$in": req.user_ids}}):
            user_id = doc["ID"]
            
            # 기본 프로필 정보
            user_profile_data = {
                "ID": user_id,
                "name": doc.get("name", "알 수 없음"),
                "gender": doc.get("gender", "알 수 없음"),
                "age": doc.get("age", 0)
            }
            
            # Features에서 특정 키워드만 추출
            features = doc.get("Features", {})
            
            # Features에서 원본 값 추출
            raw_keywords = {
                "시간약속": features.get("시간약속", ""),
                "의견수용": features.get("의견수용", ""),
                "여행희망지역": features.get("여행희망지역", []),
                "여행목적": features.get("여행목적", []),
            }
            
            # 매핑된 키워드로 변환
            keywords = {}
            
            # 개인 특성 키워드 매핑
            if raw_keywords["시간약속"]:
                keywords["시간약속"] = PERSONAL_KEYWORD_MAPPINGS.get("시간약속", {}).get(
                    raw_keywords["시간약속"], raw_keywords["시간약속"]
                )
            
            if raw_keywords["의견수용"]:
                keywords["의견수용"] = PERSONAL_KEYWORD_MAPPINGS.get("의견수용", {}).get(
                    raw_keywords["의견수용"], raw_keywords["의견수용"]
                )
            
            # 여행 키워드 매핑
            if raw_keywords["여행희망지역"]:
                keywords["여행희망지역"] = TRAVEL_KEYWORD_MAPPINGS.get("여행희망지역", {}).get(
                    raw_keywords["여행희망지역"], raw_keywords["여행희망지역"]
                )
            
            # 여행 목적 매핑 (리스트일 수 있음)
            if raw_keywords["여행목적"]:
                if isinstance(raw_keywords["여행목적"], str):
                    keywords["여행목적"] = TRAVEL_PURPOSE_MAPPINGS.get("여행목적", {}).get(
                        raw_keywords["여행목적"], raw_keywords["여행목적"]
                    )
                elif isinstance(raw_keywords["여행목적"], list):
                    mapped_purposes = []
                    for purpose in raw_keywords["여행목적"]:
                        mapped_purpose = TRAVEL_PURPOSE_MAPPINGS.get("여행목적", {}).get(purpose, purpose)
                        mapped_purposes.append(mapped_purpose)
                    keywords["여행목적"] = mapped_purposes
            
            # 선택된 Features 키워드를 프로필 데이터에 추가
            user_profile_data.update({
                "keywords": keywords,
            })

            user_profile = UserProfile(**user_profile_data)
            users.append(user_profile)
        
        logger.info(f"사용자 프로필 조회 완료: {len(users)}명")
        
        return UserProfileResponse(users=users)
        
    except Exception as e:
        logger.error(f"사용자 프로필 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"사용자 프로필 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/travel", summary="여행 패키지 정보 일괄 조회")
async def get_travel_packages(
    req: TravelRequest,
    travel_info_collection: AsyncIOMotorCollection = Depends(get_travel_info_collection),
    travel_url_collection: AsyncIOMotorCollection = Depends(get_travel_url_collection),
) -> TravelResponse:
    """
    여러 여행 패키지의 정보를 MongoDB에서 조회
    """
    try:
        logger.info(f"여행 패키지 조회 요청: {len(req.travel_ids)}개")
        
        travels = []
        
        # travel_info에서 기본 정보 조회
        travel_info_docs = {}
        async for doc in travel_info_collection.find({"product_code": {"$in": req.travel_ids}}):
            travel_info_docs[doc["product_code"]] = doc
        
        # travel_url에서 URL 정보 조회
        travel_url_docs = {}
        async for doc in travel_url_collection.find({"product_code": {"$in": req.travel_ids}}):
            travel_url_docs[doc["product_code"]] = doc
        
        # 데이터 결합
        for travel_id in req.travel_ids:
            info_doc = travel_info_docs.get(travel_id)
            url_doc = travel_url_docs.get(travel_id)
            
            if info_doc:
                travel_info = TravelInfo(
                    product_code=travel_id,
                    title=info_doc.get("title", ""),
                    hashtags=info_doc.get("hashtags", []),
                    url=url_doc.get("url", "") if url_doc else "",
                )
                travels.append(travel_info)
        
        logger.info(f"여행 패키지 조회 완료: {len(travels)}개")
        
        return TravelResponse(travels=travels)
        
    except Exception as e:
        logger.error(f"여행 패키지 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"여행 패키지 조회 중 오류가 발생했습니다: {str(e)}"
        )