"""DB 마이그레이션 스크립트 - T20260501-001 트레블AI.

실행: python migrate.py
환경변수 DATABASE_URL 이 없으면 ./data/travelai.db 를 기본 사용.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


SCHEMA_PATH = Path(__file__).parent / "schema.sql"
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "travelai.db"


def get_db_path() -> Path:
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("sqlite:///"):
        return Path(url.removeprefix("sqlite:///"))
    return DEFAULT_DB_PATH


def run_migration() -> None:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print(f"[migrate] 완료: {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
