"""공유 URL 라우터 - /api/v1/share/{share_code}."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from app import database as db
from app.models import CourseData, CourseGetResponse

router = APIRouter(prefix="/api/v1/share", tags=["share"])


@router.get("/{share_code}", response_model=CourseGetResponse)
async def get_shared_course(share_code: str) -> CourseGetResponse:
    """공유 코드(= course_id)로 코스를 조회한다. 비회원 접근 가능."""
    async with db.db_context() as conn, conn.execute(
        "SELECT id, query, course_json, created_at FROM courses WHERE id = ?",
        (share_code,),
    ) as cur:
        row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="공유 코스를 찾을 수 없습니다")

    return CourseGetResponse(
        course_id=row["id"],
        query=row["query"],
        course=CourseData(**json.loads(row["course_json"])),
        created_at=row["created_at"],
    )
