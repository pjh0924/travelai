"""aiosqlite 연결 관리."""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

from app.config import get_settings

# code/backend/app/database.py → code/db/schema.sql
_SCHEMA_PATH = Path(__file__).parent.parent.parent / "db" / "schema.sql"

_INLINE_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS courses (
    id          TEXT    NOT NULL,
    query       TEXT    NOT NULL,
    intent_json TEXT    NOT NULL DEFAULT '{}',
    course_json TEXT    NOT NULL DEFAULT '{}',
    created_at  TEXT    NOT NULL,
    expires_at  TEXT,
    CONSTRAINT pk_courses PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_courses_created_at ON courses (created_at);

CREATE TABLE IF NOT EXISTS tourapi_cache (
    cache_key   TEXT    NOT NULL,
    response    TEXT    NOT NULL,
    cached_at   TEXT    NOT NULL,
    expires_at  TEXT    NOT NULL,
    CONSTRAINT pk_tourapi_cache PRIMARY KEY (cache_key)
);

CREATE INDEX IF NOT EXISTS idx_tourapi_cache_expires_at ON tourapi_cache (expires_at);

CREATE TABLE IF NOT EXISTS llm_cache (
    cache_key   TEXT    NOT NULL,
    response    TEXT    NOT NULL,
    cached_at   TEXT    NOT NULL,
    expires_at  TEXT    NOT NULL,
    CONSTRAINT pk_llm_cache PRIMARY KEY (cache_key)
);

CREATE INDEX IF NOT EXISTS idx_llm_cache_expires_at ON llm_cache (expires_at);
"""


async def get_connection() -> aiosqlite.Connection:
    settings = get_settings()
    db_path = settings.db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode = WAL")
    await conn.execute("PRAGMA foreign_keys = ON")
    return conn


@asynccontextmanager
async def db_context() -> AsyncIterator[aiosqlite.Connection]:
    conn = await get_connection()
    try:
        yield conn
    finally:
        await conn.close()


async def init_db() -> None:
    """앱 시작 시 테이블을 생성한다."""
    if _SCHEMA_PATH.exists():
        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    else:
        schema_sql = _INLINE_SCHEMA
    async with db_context() as conn:
        await conn.executescript(schema_sql)
        await conn.commit()


# ─── 캐시 헬퍼 ────────────────────────────────────────────────

def _make_key(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _expires_iso(hours: int = 24) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


async def get_llm_cache(prompt: str) -> str | None:
    key = _make_key(prompt)
    now = _now_iso()
    async with db_context() as conn, conn.execute(
        "SELECT response FROM llm_cache WHERE cache_key = ? AND expires_at > ?",
        (key, now),
    ) as cur:
        row = await cur.fetchone()
    return str(row["response"]) if row else None


async def set_llm_cache(prompt: str, response: str) -> None:
    key = _make_key(prompt)
    now = _now_iso()
    expires = _expires_iso()
    async with db_context() as conn:
        await conn.execute(
            """
            INSERT INTO llm_cache (cache_key, response, cached_at, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                response = excluded.response,
                cached_at = excluded.cached_at,
                expires_at = excluded.expires_at
            """,
            (key, response, now, expires),
        )
        await conn.commit()


async def get_tourapi_cache(key_data: str) -> str | None:
    key = _make_key(key_data)
    now = _now_iso()
    async with db_context() as conn, conn.execute(
        "SELECT response FROM tourapi_cache WHERE cache_key = ? AND expires_at > ?",
        (key, now),
    ) as cur:
        row = await cur.fetchone()
    return str(row["response"]) if row else None


async def set_tourapi_cache(key_data: str, response: str) -> None:
    key = _make_key(key_data)
    now = _now_iso()
    expires = _expires_iso()
    async with db_context() as conn:
        await conn.execute(
            """
            INSERT INTO tourapi_cache (cache_key, response, cached_at, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                response = excluded.response,
                cached_at = excluded.cached_at,
                expires_at = excluded.expires_at
            """,
            (key, response, now, expires),
        )
        await conn.commit()
