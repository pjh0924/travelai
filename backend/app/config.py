"""애플리케이션 설정 - 환경변수 기반."""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """전체 환경변수를 타입 안전하게 관리한다."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    tourapi_key: str = ""
    llm_api_key: str = ""
    llm_model: str = "gemini-2.0-flash-exp"
    llm_provider: Literal["google", "anthropic", "kakao"] = "google"
    database_url: str = "sqlite:///./data/travelai.db"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def db_path(self) -> str:
        """sqlite:/// 접두사 제거 후 파일 경로 반환."""
        url = self.database_url
        if url.startswith("sqlite:///"):
            return url.removeprefix("sqlite:///")
        return url

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
