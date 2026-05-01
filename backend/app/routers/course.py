"""코스 관련 라우터."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from nanoid import generate

from app import database as db
from app.llm import extract_intent, generate_course
from app.models import (
    CourseData,
    CourseGetResponse,
    GenerateRequest,
    GenerateResponse,
)
from app.tourapi import area_based_list, detail_image, detail_intro, search_keyword

router = APIRouter(prefix="/api/v1/course", tags=["course"])


def _nanoid8() -> str:
    return str(generate(size=8))


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@router.post("/generate", response_model=GenerateResponse)
async def generate_course_endpoint(body: GenerateRequest) -> GenerateResponse:
    """자연어 쿼리 → 코스 생성.

    v2: body.personality_profile 이 있으면 MBTI 4축 매핑 룰을 LLM 에 주입한다.
    """
    query = body.query
    personality_profile = body.personality_profile

    # Step 1: 의도 추출 (v2: personality_profile 전달)
    intent = await extract_intent(query, personality_profile)

    # Step 2: TourAPI 병렬 호출
    area_code_map = {
        "강원도": "32", "제주": "39", "서울": "1", "경기": "31",
        "부산": "6", "경주": "35", "전주": "37", "광주": "5",
    }
    area_code = ""
    for name, code in area_code_map.items():
        if name in (intent.region or ""):
            area_code = code
            break

    keyword = " ".join(intent.preferences) if intent.preferences else intent.region or "관광"

    list_task = area_based_list(intent.region or "서울")
    search_task = search_keyword(keyword, area_code)
    list_results, search_results = await asyncio.gather(list_task, search_task)

    # 후보 병합 (contentId 기준 중복 제거)
    seen: set[str] = set()
    candidates = []
    for item in list_results + search_results:
        cid = str(item.get("contentid", ""))
        if cid and cid not in seen:
            seen.add(cid)
            candidates.append(
                {
                    "contentId": cid,
                    "name": item.get("title", ""),
                    "address": item.get("addr1", ""),
                    "lat": float(item.get("mapy", 0) or 0),
                    "lng": float(item.get("mapx", 0) or 0),
                    "content_type_id": str(item.get("contenttypeid", "12")),
                }
            )

    if not candidates:
        raise HTTPException(status_code=503, detail="TourAPI 후보 장소 없음")

    # Step 3: 동선 JSON 생성 (v2: personality_profile 전달)
    course_raw = await generate_course(intent, candidates, personality_profile)

    # Step 4: 이미지 URL 보강 (비동기, 실패 허용)
    for day in course_raw.get("days", []):
        for place in day.get("places", []):
            if not place.get("image_url"):
                try:
                    img_url = await detail_image(place["content_id"])
                    place["image_url"] = img_url
                except Exception:
                    pass

    # Step 5: 무장애 정보 보강
    for day in course_raw.get("days", []):
        for place in day.get("places", []):
            try:
                intro = await detail_intro(place["content_id"])
                if intro:
                    bf = place.setdefault("barrier_free", {})
                    handicap_note = intro.get("handicapinfo", "") or ""
                    if handicap_note:
                        bf["note"] = handicap_note
                        bf["certified"] = True
            except Exception:
                pass

    # Step 6: DB 저장 (v2: personality_profile 직렬화해서 저장)
    course_id = _nanoid8()
    now = _now_iso()
    course_data = CourseData(**course_raw)

    personality_json: str | None = None
    if personality_profile:
        personality_json = json.dumps(
            personality_profile.model_dump(), ensure_ascii=False
        )

    async with db.db_context() as conn:
        await conn.execute(
            "INSERT INTO courses (id, query, intent_json, course_json, personality_profile, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                course_id,
                query,
                json.dumps(intent.model_dump(), ensure_ascii=False),
                json.dumps(course_raw, ensure_ascii=False),
                personality_json,
                now,
            ),
        )
        await conn.commit()

    return GenerateResponse(
        course_id=course_id,
        course=course_data,
        generated_at=now,
        cache_hit=False,
    )


@router.get("/{course_id}", response_model=CourseGetResponse)
async def get_course(course_id: str) -> CourseGetResponse:
    """코스 ID로 조회."""
    async with db.db_context() as conn, conn.execute(
        "SELECT id, query, course_json, created_at FROM courses WHERE id = ?",
        (course_id,),
    ) as cur:
        row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다")

    return CourseGetResponse(
        course_id=row["id"],
        query=row["query"],
        course=CourseData(**json.loads(row["course_json"])),
        created_at=row["created_at"],
    )
