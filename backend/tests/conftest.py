"""테스트 공통 픽스처 - in-memory SQLite DB 초기화."""

from __future__ import annotations

import asyncio
from typing import Iterator
from unittest.mock import patch

import pytest

# in-memory DB 사용을 위해 DATABASE_URL 오버라이드
_TEST_DB_URL = "sqlite:///./data/test_travelai.db"


@pytest.fixture(autouse=True, scope="session")
def patch_db_url() -> Iterator[None]:
    """테스트 세션 동안 DB를 별도 파일로 격리한다."""
    import app.config as config_module

    original = config_module._settings

    test_settings = config_module.Settings(
        database_url=_TEST_DB_URL,
        llm_provider="google",
        llm_model="gemini-2.0-flash-exp",
        llm_api_key="test-key-xxxx",
        tourapi_key="test-tourapi-key",
    )
    config_module._settings = test_settings

    # DB 초기화 (동기적으로 실행)
    asyncio.run(_init_test_db())

    yield

    config_module._settings = original

    # 테스트 DB 파일 정리
    import os
    from pathlib import Path

    db_path = test_settings.db_path
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        wal_path = db_path + "-wal"
        shm_path = db_path + "-shm"
        for extra in [wal_path, shm_path]:
            if os.path.exists(extra):
                os.remove(extra)
    except OSError:
        pass


async def _init_test_db() -> None:
    """테스트용 DB 테이블 초기화 (personality_profile 컬럼 포함)."""
    import aiosqlite
    from pathlib import Path

    from app.config import get_settings

    settings = get_settings()
    db_path = settings.db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    schema = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS courses (
    id                  TEXT    NOT NULL,
    query               TEXT    NOT NULL,
    intent_json         TEXT    NOT NULL DEFAULT '{}',
    course_json         TEXT    NOT NULL DEFAULT '{}',
    personality_profile TEXT,
    created_at          TEXT    NOT NULL,
    expires_at          TEXT,
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

CREATE TABLE IF NOT EXISTS llm_cache (
    cache_key   TEXT    NOT NULL,
    response    TEXT    NOT NULL,
    cached_at   TEXT    NOT NULL,
    expires_at  TEXT    NOT NULL,
    CONSTRAINT pk_llm_cache PRIMARY KEY (cache_key)
);
"""
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.executescript(schema)
    await conn.commit()
    await conn.close()
