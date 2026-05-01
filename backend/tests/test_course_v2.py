"""코스 API v2 테스트 - personality_profile 기능."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import IntentData, PersonalityProfile
from app.llm import _build_personality_rule


_MOCK_INTENT = IntentData(
    region="서울",
    duration="1박2일",
    companions=["혼자"],
    constraints=[],
    preferences=["카페", "감성"],
)

_MOCK_COURSE_RAW_V2: dict[str, object] = {
    "title": "ENFP 감성 서울 여행",
    "region": "서울",
    "duration": "1박2일",
    "summary": "즉흥적인 ENFP 를 위한 감성 서울",
    "personality_comment": "ENFP라 즉흥적으로 들를 만한 카페를 골랐어요",
    "days": [
        {
            "day": 1,
            "date_label": "1일차",
            "places": [
                {
                    "order": 1,
                    "content_id": "264337",
                    "name": "북촌한옥마을",
                    "address": "서울 종로구",
                    "lat": 37.58,
                    "lng": 126.98,
                    "image_url": "",
                    "open_hours": "",
                    "recommendation": "감성 사진 명소",
                    "barrier_free": {
                        "certified": False,
                        "wheelchair_rental": False,
                        "parking_accessible": False,
                        "note": "",
                    },
                    "travel_to_next": {"mode": "도보", "minutes": 10},
                }
            ],
        }
    ],
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_generate_course_with_personality(client: TestClient) -> None:
    """personality_profile 포함 요청 시 코스가 생성되고 personality_comment 가 반환된다."""
    with (
        patch("app.routers.course.extract_intent", new_callable=AsyncMock) as mock_intent,
        patch("app.routers.course.area_based_list", new_callable=AsyncMock) as mock_area,
        patch("app.routers.course.search_keyword", new_callable=AsyncMock) as mock_search,
        patch("app.routers.course.generate_course", new_callable=AsyncMock) as mock_gen,
        patch("app.routers.course.detail_image", new_callable=AsyncMock) as mock_img,
        patch("app.routers.course.detail_intro", new_callable=AsyncMock) as mock_intro,
    ):
        mock_intent.return_value = _MOCK_INTENT
        mock_area.return_value = [
            {
                "contentid": "264337",
                "title": "북촌한옥마을",
                "addr1": "서울 종로구",
                "mapy": "37.58",
                "mapx": "126.98",
                "contenttypeid": "12",
            }
        ]
        mock_search.return_value = []
        mock_gen.return_value = _MOCK_COURSE_RAW_V2
        mock_img.return_value = ""
        mock_intro.return_value = {}

        resp = client.post(
            "/api/v1/course/generate",
            json={
                "query": "서울 1박2일 감성 여행",
                "personality_profile": {
                    "mbti": "ENFP",
                    "blood_type": "B",
                    "zodiac": "사자자리",
                    "note": "혼자 조용한 곳 좋아함",
                },
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "course_id" in data
    assert data["course"]["personality_comment"] == "ENFP라 즉흥적으로 들를 만한 카페를 골랐어요"


def test_generate_course_without_personality_backward_compat(client: TestClient) -> None:
    """personality_profile 없는 v1 방식 요청도 정상 동작해야 한다."""
    with (
        patch("app.routers.course.extract_intent", new_callable=AsyncMock) as mock_intent,
        patch("app.routers.course.area_based_list", new_callable=AsyncMock) as mock_area,
        patch("app.routers.course.search_keyword", new_callable=AsyncMock) as mock_search,
        patch("app.routers.course.generate_course", new_callable=AsyncMock) as mock_gen,
        patch("app.routers.course.detail_image", new_callable=AsyncMock) as mock_img,
        patch("app.routers.course.detail_intro", new_callable=AsyncMock) as mock_intro,
    ):
        _no_personality_course: dict[str, object] = {
            **_MOCK_COURSE_RAW_V2,
            "personality_comment": "",
        }
        mock_intent.return_value = _MOCK_INTENT
        mock_area.return_value = [
            {
                "contentid": "264337",
                "title": "북촌한옥마을",
                "addr1": "서울 종로구",
                "mapy": "37.58",
                "mapx": "126.98",
                "contenttypeid": "12",
            }
        ]
        mock_search.return_value = []
        mock_gen.return_value = _no_personality_course
        mock_img.return_value = ""
        mock_intro.return_value = {}

        resp = client.post(
            "/api/v1/course/generate",
            json={"query": "서울 1박2일"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["course"]["personality_comment"] == ""


def test_invalid_mbti_rejected(client: TestClient) -> None:
    """유효하지 않은 MBTI 값은 422 로 거부된다."""
    resp = client.post(
        "/api/v1/course/generate",
        json={
            "query": "서울 여행",
            "personality_profile": {"mbti": "XXXX"},
        },
    )
    assert resp.status_code == 422


def test_invalid_blood_type_rejected(client: TestClient) -> None:
    """유효하지 않은 혈액형 값은 422 로 거부된다."""
    resp = client.post(
        "/api/v1/course/generate",
        json={
            "query": "서울 여행",
            "personality_profile": {"mbti": "ENFP", "blood_type": "Z"},
        },
    )
    assert resp.status_code == 422


def test_build_personality_rule_contains_mbti() -> None:
    """_build_personality_rule 이 MBTI 4축 정보를 포함한 룰 문자열을 반환한다."""
    profile = PersonalityProfile(mbti="ENFP", blood_type="B", zodiac="사자자리", note="")
    rule = _build_personality_rule(profile)
    assert "ENFP" in rule
    assert "personality_comment" in rule
    assert "즉흥" in rule  # P 축 → 즉흥성 키워드


def test_build_personality_rule_empty_mbti() -> None:
    """MBTI 미입력 시 빈 문자열을 반환한다."""
    profile = PersonalityProfile(mbti="", blood_type="A", zodiac="")
    rule = _build_personality_rule(profile)
    assert rule == ""
