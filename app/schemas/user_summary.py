from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UserSummaryBase(BaseModel):
    user_id: str | None = Field(default=None, description="사용자 식별자 (Mongo 필드 'ID'와 매핑)")
    summary: str = Field(default="", description="사용자 특성 (Mongo 필드 'Summary')")


class UserSummaryCreate(BaseModel):
    # 실제 Mongo 'ID' 필드와 매핑되는 사용자 식별자
    user_id: str = Field(alias="ID")
    summary: str = Field(alias="Summary")


class UserSummaryUpdate(BaseModel):
    user_id: str | None = None
    summary: str | None = None


class UserSummaryResponse(UserSummaryBase):
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None