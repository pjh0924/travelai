-- T20260501-001 트레블AI DB 스키마
-- DB: SQLite (7월 Postgres 이관 대비 ANSI SQL 준수)
-- 작성: db-engineer | 2026-05-01

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================
-- 코스 테이블
-- id: nanoid 8자리 (courseId 겸 shareCode)
-- ============================================================
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

-- ============================================================
-- TourAPI 응답 캐시 테이블
-- cache_key: SHA256(endpoint + sorted_params)
-- expires_at: cached_at + 24h
-- ============================================================
CREATE TABLE IF NOT EXISTS tourapi_cache (
    cache_key   TEXT    NOT NULL,
    response    TEXT    NOT NULL,
    cached_at   TEXT    NOT NULL,
    expires_at  TEXT    NOT NULL,
    CONSTRAINT pk_tourapi_cache PRIMARY KEY (cache_key)
);

CREATE INDEX IF NOT EXISTS idx_tourapi_cache_expires_at ON tourapi_cache (expires_at);

-- ============================================================
-- LLM 응답 캐시 테이블
-- cache_key: SHA256(model + normalized_prompt)
-- expires_at: cached_at + 24h
-- ============================================================
CREATE TABLE IF NOT EXISTS llm_cache (
    cache_key   TEXT    NOT NULL,
    response    TEXT    NOT NULL,
    cached_at   TEXT    NOT NULL,
    expires_at  TEXT    NOT NULL,
    CONSTRAINT pk_llm_cache PRIMARY KEY (cache_key)
);

CREATE INDEX IF NOT EXISTS idx_llm_cache_expires_at ON llm_cache (expires_at);
