"""Pydantic 요청/응답 모델."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class PersonalityProfile(BaseModel):
    """v2: 사용자 성향 프로파일."""

    mbti: str = Field(
        default="",
        description="MBTI 16종 중 하나 (예: ENFP). 빈 문자열이면 성향 주입 건너뜀.",
    )
    blood_type: str = Field(
        default="",
        description="혈액형: A / B / AB / O / 모름 또는 빈 문자열.",
    )
    zodiac: str = Field(
        default="",
        description="별자리 (예: 사자자리). 선택 항목.",
    )
    note: str = Field(
        default="",
        max_length=100,
        description="자연어 보조 입력 1줄 (예: 혼자 조용한 곳 좋아함).",
    )

    @field_validator("mbti")
    @classmethod
    def validate_mbti(cls, v: str) -> str:
        valid = {
            "INTJ", "INTP", "ENTJ", "ENTP",
            "INFJ", "INFP", "ENFJ", "ENFP",
            "ISTJ", "ISFJ", "ESTJ", "ESFJ",
            "ISTP", "ISFP", "ESTP", "ESFP",
            "",
        }
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"유효하지 않은 MBTI 값: {v}")
        return upper

    @field_validator("blood_type")
    @classmethod
    def validate_blood_type(cls, v: str) -> str:
        valid = {"A", "B", "AB", "O", "모름", ""}
        if v not in valid:
            raise ValueError(f"유효하지 않은 혈액형 값: {v}")
        return v


class GenerateRequest(BaseModel):
    query: str = Field(..., max_length=200, description="자연어 여행 요청")
    personality_profile: PersonalityProfile | None = Field(
        default=None,
        description="v2: 성향 기반 추천용 프로파일. null 이면 v1 동작.",
    )

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("query는 공백이 아닌 문자를 포함해야 합니다")
        return stripped


class BarrierFreeInfo(BaseModel):
    certified: bool = False
    wheelchair_rental: bool = False
    parking_accessible: bool = False
    note: str = ""


class TravelToNext(BaseModel):
    mode: str = "차량"
    minutes: int = 0


class PlaceItem(BaseModel):
    order: int
    content_id: str
    name: str
    address: str
    lat: float
    lng: float
    image_url: str = ""
    open_hours: str = ""
    recommendation: str
    barrier_free: BarrierFreeInfo = Field(default_factory=BarrierFreeInfo)
    travel_to_next: TravelToNext | None = None


class DaySchedule(BaseModel):
    day: int
    date_label: str
    places: list[PlaceItem]


class CourseData(BaseModel):
    title: str
    region: str
    duration: str
    summary: str
    days: list[DaySchedule]
    personality_comment: str = Field(
        default="",
        description="v2: LLM 생성 성향 반영 코멘트 1줄. 성향 미입력 시 빈 문자열.",
    )


class GenerateResponse(BaseModel):
    course_id: str
    course: CourseData
    generated_at: str
    cache_hit: bool = False


class CourseGetResponse(BaseModel):
    course_id: str
    query: str
    course: CourseData
    created_at: str


class HealthResponse(BaseModel):
    status: str
    db: str
    timestamp: str


class IntentData(BaseModel):
    region: str = ""
    duration: str = ""
    companions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)
