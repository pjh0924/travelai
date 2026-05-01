"""헬스체크 라우터."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from app import database as db
from app.models import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    db_status = "connected"
    try:
        async with db.db_context() as conn:
            await conn.execute("SELECT 1")
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok",
        db=db_status,
        timestamp=datetime.now(UTC).isoformat(),
    )
