"""DB 마이그레이션 v2 - T20260501-001 트레블AI.

변경 내용:
  - courses 테이블에 personality_profile TEXT DEFAULT NULL 컬럼 추가

실행: python migrate_v2.py
환경변수 DATABASE_URL 이 없으면 ./data/travelai.db 를 기본 사용.
기존 레코드에 영향 없음 (NULL 허용 컬럼 추가).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "travelai.db"

MIGRATION_SQL = """
ALTER TABLE courses ADD COLUMN personality_profile TEXT DEFAULT NULL;
"""

VERIFY_SQL = """
SELECT COUNT(*) FROM pragma_table_info('courses') WHERE name = 'personality_profile';
"""


def get_db_path() -> Path:
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("sqlite:///"):
        return Path(url.removeprefix("sqlite:///"))
    return DEFAULT_DB_PATH


def column_exists(conn: sqlite3.Connection) -> bool:
    cursor = conn.execute(VERIFY_SQL)
    row = cursor.fetchone()
    return bool(row and row[0] > 0)


def run_migration_v2() -> None:
    db_path = get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(
            f"DB 파일이 없습니다: {db_path}\n"
            "migrate.py 를 먼저 실행해 v1 스키마를 초기화하세요."
        )

    conn = sqlite3.connect(db_path)
    try:
        if column_exists(conn):
            print("[migrate_v2] personality_profile 컬럼이 이미 존재합니다. 건너뜁니다.")
            return

        conn.executescript(MIGRATION_SQL)
        conn.commit()

        if column_exists(conn):
            print(f"[migrate_v2] 완료: {db_path}")
            print("[migrate_v2] personality_profile TEXT DEFAULT NULL 컬럼 추가됨")
        else:
            raise RuntimeError("마이그레이션 후 컬럼 검증 실패")
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration_v2()
