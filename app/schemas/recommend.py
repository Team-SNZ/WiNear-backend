from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")


class RecommendResponse(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    rec_people: list[str] = Field(..., description="추천 동반자 목록")
    rec_travel: list[str] = Field(..., description="추천 여행지 목록")
    status: str = Field(..., description="처리 상태")


class UserProfileRequest(BaseModel):
    user_ids: list[str] = Field(..., description="사용자 ID 목록")


class UserProfileResponse(BaseModel):
    users: list[UserProfile] = Field(..., description="사용자 프로필 목록")


class UserProfile(BaseModel):
    ID: str = Field(..., description="사용자 ID")
    name: str = Field(..., description="이름")
    gender: str = Field(..., description="성별")
    age: int = Field(..., description="나이")
    Features: dict = Field(..., description="사용자 특징")


class TravelRequest(BaseModel):
    travel_ids: list[str] = Field(..., description="여행지 ID 목록")


class TravelResponse(BaseModel):
    travels: list[TravelInfo] = Field(..., description="여행 패키지 목록")


class TravelInfo(BaseModel):
    product_code: str = Field(..., description="상품 코드")
    title: str = Field(..., description="여행 패키지 제목")
    hashtags: list[str] = Field(..., description="해시태그 목록")
    url: str = Field(..., description="여행 패키지 URL")


