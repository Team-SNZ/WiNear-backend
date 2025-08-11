from datetime import datetime
from typing import Any, List

from pydantic import BaseModel, Field

# features 딕셔너리의 내부 구조를 더 명확하게 정의하는 방법
class FeaturesSchema(BaseModel):
    예민함정도: str
    의견수용: str
    말수: str
    시간약속: str
    리더십: str
    체력: int
    청결민감도: str
    여행일정강도: str
    국내or해외: str
    산or바다: str
    계획or즉흥: str
    랜드마크: str
    코골이: str
    웨이팅: str
    여행희망지역: List[str]
    싫어하는기후: List[str]
    여행목적: List[str]
    숙소유형: List[str]
    기상시간: str
    여행예산: str


class UserFeaturesBase(BaseModel):
    user_id: str | None = Field(default=None, description="사용자 식별자 (Mongo 필드 'ID'와 매핑)")
    features: dict[str, Any] = Field(default_factory=dict, description="사용자 특성 (Mongo 필드 'Features')")


class UserFeaturesCreate(BaseModel):
    # 실제 Mongo 'ID' 필드와 매핑되는 사용자 식별자
    user_id: str = Field(alias="ID")
    # Mongo 'Features' 필드와 매핑
    features: FeaturesSchema | dict[str, Any] = Field(alias="Features")


class UserFeaturesUpdate(BaseModel):
    user_id: str | None = None
    features: dict[str, Any] | None = None


class UserFeaturesResponse(UserFeaturesBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserFeaturesListResponse(BaseModel):
    items: list[UserFeaturesResponse]
    total: int

