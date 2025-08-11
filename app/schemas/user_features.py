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
    user_id: str | None = Field(default=None, description="사용자 식별자 (선택)")
    legacy_id: int | None = Field(default=None, description="기존 정수형 ID (Mongo 필드 'ID')")
    features: dict[str, Any] = Field(default_factory=dict, description="사용자 특성 (Mongo 필드 'Features')")


class UserFeaturesCreate(UserFeaturesBase):
    legacy_id: int = Field(alias="ID")
    features: FeaturesSchema = Field(alias="Features")


class UserFeaturesUpdate(BaseModel):
    user_id: str | None = None
    legacy_id: int | None = None
    features: dict[str, Any] | None = None


class UserFeaturesResponse(UserFeaturesBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserFeaturesListResponse(BaseModel):
    items: list[UserFeaturesResponse]
    total: int

