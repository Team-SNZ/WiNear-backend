from datetime import datetime
from typing import Any, List, Dict

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


class UserFeaturesAnalysisResponse(BaseModel):
    user_id: str
    user_name: str | None = None
    travel_keywords: List[str] = []
    personal_keywords: List[str] = []
    travel_purposes: List[str] = []
    polygon_labels: List[str] = []
    polygon_values: List[int] = []
    empty_fields: List[str] = []

    @staticmethod
    def _coerce_to_int(value: Any) -> int:
        try:
            return int(value)
        except Exception:
            return 0

    @staticmethod
    def _is_non_empty_str(value: Any) -> bool:
        return isinstance(value, str) and value.strip() != ""

    def model_post_init(self, __context: Dict[str, Any]) -> None:  # type: ignore[override]
        # 라벨 문자열 정규화
        self.polygon_labels = [lbl.strip() for lbl in self.polygon_labels if self._is_non_empty_str(lbl)]
        # 값 정수 변환 및 음수 방지
        self.polygon_values = [max(0, self._coerce_to_int(v)) for v in self.polygon_values]
        # 길이 검증
        if len(self.polygon_labels) != len(self.polygon_values):
            raise ValueError("polygon_labels와 polygon_values의 길이가 일치해야 합니다.")
        # 키워드 정규화(공백 제거 및 공백 문자열 제거)
        self.travel_keywords = [kw.strip() for kw in self.travel_keywords if self._is_non_empty_str(kw)]
        self.personal_keywords = [kw.strip() for kw in self.personal_keywords if self._is_non_empty_str(kw)]
        self.travel_purposes = [kw.strip() for kw in self.travel_purposes if self._is_non_empty_str(kw)]

        # 빈 값 검증 결과 생성
        empty: list[str] = []
        if not self.travel_keywords:
            empty.append("travel_keywords")
        if not self.personal_keywords:
            empty.append("personal_keywords")
        if not self.travel_purposes:
            empty.append("travel_purposes")
        if not self.polygon_labels or not self.polygon_values or all(v == 0 for v in self.polygon_values):
            empty.append("polygon")
        self.empty_fields = empty