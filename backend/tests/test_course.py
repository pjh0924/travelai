"""코스 API 테스트."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import IntentData


_MOCK_INTENT = IntentData(
    region="강원도",
    duration="2박3일",
    companions=["부모님"],
    constraints=["무릎통증"],
    preferences=["자연"],
)

_MOCK_COURSE_RAW: dict[str, object] = {
    "title": "강원도 2박3일 무장애 여행",
    "region": "강원도",
    "duration": "2박3일",
    "summary": "무릎 통증을 고려한 평지 위주 강원도 여행",
    "days": [
        {
            "day": 1,
            "date_label": "1일차",
            "places": [
                {
                    "order": 1,
                    "content_id": "126508",
                    "name": "설악산 케이블카",
                    "address": "강원도 속초시",
                    "lat": 38.12,
                    "lng": 128.46,
                    "image_url": "",
                    "open_hours": "09:00-17:00",
                    "recommendation": "케이블카 이용으로 무릎 부담 없이 전망 감상",
                    "barrier_free": {
                        "certified": True,
                        "wheelchair_rental": False,
                        "parking_accessible": True,
                        "note": "",
                    },
                    "travel_to_next": {"mode": "차량", "minutes": 15},
                }
            ],
        }
    ],
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_generate_course(client: TestClient) -> None:
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
                "contentid": "126508",
                "title": "설악산 케이블카",
                "addr1": "강원도 속초시",
                "mapy": "38.12",
                "mapx": "128.46",
                "contenttypeid": "12",
            }
        ]
        mock_search.return_value = []
        mock_gen.return_value = _MOCK_COURSE_RAW
        mock_img.return_value = "https://example.com/img.jpg"
        mock_intro.return_value = {}

        resp = client.post(
            "/api/v1/course/generate",
            json={"query": "2박3일 강원도 부모님 모시고 갈 건데 무릎 안 좋으세요"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "course_id" in data
    assert data["course"]["region"] == "강원도"
    assert len(data["course"]["days"]) == 1


def test_generate_course_empty_query(client: TestClient) -> None:
    resp = client.post("/api/v1/course/generate", json={"query": "   "})
    # Pydantic strip_query + min_length=1 → 422
    assert resp.status_code == 422


def test_get_course_not_found(client: TestClient) -> None:
    resp = client.get("/api/v1/course/NOTFOUND")
    assert resp.status_code == 404


def test_share_not_found(client: TestClient) -> None:
    resp = client.get("/api/v1/share/NOTFOUND")
    assert resp.status_code == 404
