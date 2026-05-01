"""TourAPI 4.0 클라이언트 - 백엔드 프록시 전용."""

from __future__ import annotations

import json
import urllib.parse
from typing import Any

import httpx

from app.config import get_settings
from app.database import get_tourapi_cache, set_tourapi_cache

_BASE_URL = "https://apis.data.go.kr/B551011/KorService1"
_TIMEOUT = 5.0

# 지역 코드 매핑 (TourAPI areaCode)
_AREA_CODES: dict[str, str] = {
    "서울": "1",
    "인천": "2",
    "대전": "3",
    "대구": "4",
    "광주": "5",
    "부산": "6",
    "울산": "7",
    "세종": "8",
    "경기": "31",
    "강원": "32",
    "충북": "33",
    "충남": "34",
    "경북": "35",
    "경남": "36",
    "전북": "37",
    "전남": "38",
    "제주": "39",
}


def _resolve_area_code(region: str) -> str:
    """지역명에서 가장 가까운 areaCode를 반환한다."""
    for name, code in _AREA_CODES.items():
        if name in region:
            return code
    return "1"  # 기본: 서울


def _build_common_params(extra: dict[str, Any] | None = None) -> dict[str, str]:
    settings = get_settings()
    params: dict[str, Any] = {
        "serviceKey": settings.tourapi_key,
        "MobileOS": "ETC",
        "MobileApp": "TravelAI",
        "_type": "json",
        "numOfRows": "20",
        "pageNo": "1",
    }
    if extra:
        params.update(extra)
    return {k: str(v) for k, v in params.items()}


async def _get_cached_or_fetch(endpoint: str, params: dict[str, str]) -> dict[str, Any]:
    key_data = f"{endpoint}?{urllib.parse.urlencode(sorted(params.items()))}"
    cached = await get_tourapi_cache(key_data)
    if cached:
        return json.loads(cached)  # type: ignore[no-any-return]

    url = f"{_BASE_URL}/{endpoint}"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

    await set_tourapi_cache(key_data, json.dumps(data, ensure_ascii=False))
    return data


async def area_based_list(region: str, content_type_id: str = "12") -> list[dict[str, Any]]:
    """areaBasedList1 (관광지 목록) 호출."""
    area_code = _resolve_area_code(region)
    params = _build_common_params(
        {
            "areaCode": area_code,
            "contentTypeId": content_type_id,
            "arrange": "P",
        }
    )
    data = await _get_cached_or_fetch("areaBasedList1", params)
    items: list[dict[str, Any]] = (
        data.get("response", {})
        .get("body", {})
        .get("items", {})
        .get("item", [])
    )
    return items if isinstance(items, list) else []


async def search_keyword(keyword: str, area_code: str = "") -> list[dict[str, Any]]:
    """searchKeyword1 (키워드 검색) 호출."""
    extra: dict[str, str] = {"keyword": keyword}
    if area_code:
        extra["areaCode"] = area_code
    params = _build_common_params(extra)
    data = await _get_cached_or_fetch("searchKeyword1", params)
    items: list[dict[str, Any]] = (
        data.get("response", {})
        .get("body", {})
        .get("items", {})
        .get("item", [])
    )
    return items if isinstance(items, list) else []


async def detail_intro(content_id: str, content_type_id: str = "12") -> dict[str, Any]:
    """detailIntro1 (무장애 정보 포함) 호출."""
    params = _build_common_params(
        {
            "contentId": content_id,
            "contentTypeId": content_type_id,
        }
    )
    data = await _get_cached_or_fetch("detailIntro1", params)
    items: list[dict[str, Any]] = (
        data.get("response", {})
        .get("body", {})
        .get("items", {})
        .get("item", [])
    )
    return items[0] if items else {}


async def detail_image(content_id: str) -> str:
    """detailImage1 (대표 이미지 URL) 호출 후 첫 번째 URL 반환."""
    params = _build_common_params(
        {
            "contentId": content_id,
            "imageYN": "Y",
            "subImageYN": "N",
        }
    )
    data = await _get_cached_or_fetch("detailImage1", params)
    items: list[dict[str, Any]] = (
        data.get("response", {})
        .get("body", {})
        .get("items", {})
        .get("item", [])
    )
    if items:
        return str(items[0].get("originimgurl", ""))
    return ""
