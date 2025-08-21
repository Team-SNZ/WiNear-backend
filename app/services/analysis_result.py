from __future__ import annotations
from typing import List, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..repositories.user_features_repository import get_user_features_by_user_id
from ..schemas.user_features import UserFeaturesAnalysisResponse
from ..constants.result_keyword import POLYGON_LABELS, NUMERIC_MAPPINGS, TRAVEL_KEYWORD_MAPPINGS, PERSONAL_KEYWORD_MAPPINGS, TRAVEL_PURPOSE_MAPPINGS

import logging

logger = logging.getLogger("uvicorn.debug")

def map_doc_to_keyword(key: str, value: str | int | List[str], mappings: dict) -> int:
    """문자열 값을 정수로 매핑하는 함수"""
    # 이미 정수인 경우 그대로 반환
    if isinstance(value, int):
        return value
    
    # 해당 키의 매핑이 있으면 사용
    if key in mappings:
        if type(value) == list:
            mapped_value = []
            for v in value:
                if v not in mappings[key]:
                    raise ValueError(f"value list에서 매핑을 찾을 수 없습니다: key='{key}', value='{v}'")
                mapped_value.append(mappings[key][v])
            return mapped_value
        else:
            if value not in mappings[key]:
                raise ValueError(f"value에서 매핑을 찾을 수 없습니다: key='{key}', value='{value}'")
            mapped_value = mappings[key][value]
            return mapped_value
    
    # 매핑이 없으면 0 반환
    logger.info(f"No mapping found for key '{key}', returning 0")
    return 0


def flatten_mapped_values(values: List[Any]) -> List[str]:
    """매핑된 값들을 평탄화하여 문자열 리스트로 반환"""
    flattened = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(value)
        elif isinstance(value, str):
            flattened.append(value)
        elif value != 0:  # 0이 아닌 값들만 추가 (매핑이 없어서 0이 반환된 경우는 제외)
            flattened.append(str(value))
    return flattened


async def get_user_analysis_data(
    db: AsyncIOMotorDatabase, 
    user_id: str
) -> UserFeaturesAnalysisResponse:
    # 사용자 분석 데이터를 가져오는 서비스 함수
    doc = await get_user_features_by_user_id(db, user_id)
    if doc is None:
        raise ValueError("User features not found")
    
    # 오각형 매핑
    polygon_labels = POLYGON_LABELS
    polygon_values = [map_doc_to_keyword(label, doc.features.get(label, 0), NUMERIC_MAPPINGS) for label in polygon_labels]
    
    logger.info(f"polygon_values = {polygon_values}")

    # 여행 키워드 매핑
    travel_keywords_raw = [map_doc_to_keyword(schema, doc.features.get(schema, 0), TRAVEL_KEYWORD_MAPPINGS) for schema in TRAVEL_KEYWORD_MAPPINGS.keys()]
    travel_keywords = flatten_mapped_values(travel_keywords_raw)

    logger.info(f"travel_keywords = {travel_keywords}")

    # 개인 특성 키워드 매핑
    personal_keywords_raw = [map_doc_to_keyword(schema, doc.features.get(schema, 0), PERSONAL_KEYWORD_MAPPINGS) for schema in PERSONAL_KEYWORD_MAPPINGS.keys()]
    personal_keywords = flatten_mapped_values(personal_keywords_raw)
    
    logger.info(f"personal_keywords = {personal_keywords}")
    
    # 여행 목적 매핑
    travel_purposes_raw = [map_doc_to_keyword(schema, doc.features.get(schema, 0), TRAVEL_PURPOSE_MAPPINGS) for schema in TRAVEL_PURPOSE_MAPPINGS.keys()]
    travel_purposes = flatten_mapped_values(travel_purposes_raw)
    
    logger.info(f"travel_purposes = {travel_purposes}")

    return UserFeaturesAnalysisResponse(
        user_id=doc.user_id or user_id,
        user_name=None,
        travel_keywords=travel_keywords,
        personal_keywords=personal_keywords,
        travel_purposes=travel_purposes,
        polygon_labels=polygon_labels,
        polygon_values=polygon_values,
    )
