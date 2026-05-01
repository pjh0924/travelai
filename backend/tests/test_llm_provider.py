"""LLM provider 분기 테스트.

- google provider: google.generativeai mock으로 _call_llm 동작 검증
- anthropic provider: anthropic mock으로 _call_llm 동작 검증
- kakao provider: NotImplementedError 발생 검증
- Gemini 폴백: 첫 번째 모델 NotFound 시 fallback 모델 자동 재시도
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings


# ---------------------------------------------------------------------------
# 헬퍼: Settings를 테스트용으로 오버라이드
# ---------------------------------------------------------------------------

def _make_settings(provider: str, model: str = "gemini-2.0-flash-exp") -> Settings:
    return Settings(
        llm_provider=provider,  # type: ignore[arg-type]
        llm_model=model,
        llm_api_key="test-api-key-xxxx",
        tourapi_key="",
    )


# ---------------------------------------------------------------------------
# Google provider 테스트
# ---------------------------------------------------------------------------

def test_call_google_sync_returns_text() -> None:
    """google provider가 generate_content 결과 텍스트를 반환한다."""
    mock_response = MagicMock()
    mock_response.text = '{"region": "서울", "duration": "1박2일"}'

    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = mock_response

    with (
        patch("google.generativeai.GenerativeModel", return_value=mock_model_instance),
        patch("google.generativeai.GenerationConfig", return_value=MagicMock()),
        patch("google.generativeai.configure"),
    ):
        from app.llm import _call_google_sync
        result = _call_google_sync(
            "gemini-2.0-flash-exp",
            "test-api-key-xxxx",
            "test prompt",
            512,
        )

    assert result == '{"region": "서울", "duration": "1박2일"}'


def test_call_google_sync_fallback_on_not_found() -> None:
    """NotFound 예외 발생 시 fallback 모델로 재시도한다."""
    mock_response = MagicMock()
    mock_response.text = '{"ok": true}'

    primary_model = MagicMock()
    fallback_model = MagicMock()
    fallback_model.generate_content.return_value = mock_response

    from google.api_core import exceptions as gexc

    primary_model.generate_content.side_effect = gexc.NotFound("model not found")

    call_count = 0

    def model_factory(**kwargs: Any) -> MagicMock:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return primary_model
        return fallback_model

    with (
        patch("google.generativeai.GenerativeModel", side_effect=model_factory),
        patch("google.generativeai.GenerationConfig", return_value=MagicMock()),
        patch("google.generativeai.configure"),
    ):
        from app.llm import _call_google_sync
        result = _call_google_sync(
            "gemini-2.0-flash-exp",
            "test-api-key-xxxx",
            "test prompt",
            512,
        )

    assert result == '{"ok": true}'
    assert call_count == 2


# ---------------------------------------------------------------------------
# Anthropic provider 테스트
# ---------------------------------------------------------------------------

def test_call_anthropic_sync_returns_text() -> None:
    """anthropic provider가 messages.create 결과 텍스트를 반환한다."""
    mock_content = MagicMock()
    mock_content.text = '{"region": "부산"}'

    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client_instance = MagicMock()
    mock_client_instance.messages.create.return_value = mock_message

    with patch("anthropic.Anthropic", return_value=mock_client_instance):
        from app.llm import _call_anthropic_sync
        result = _call_anthropic_sync(
            "claude-haiku-4-5",
            "test-api-key-xxxx",
            "test prompt",
            256,
        )

    assert result == '{"region": "부산"}'


# ---------------------------------------------------------------------------
# Kakao provider NotImplementedError 테스트
# ---------------------------------------------------------------------------

def test_dispatch_kakao_raises_not_implemented() -> None:
    """LLM_PROVIDER=kakao 설정 시 NotImplementedError가 발생한다."""
    kakao_settings = _make_settings("kakao")

    with patch("app.llm.get_settings", return_value=kakao_settings):
        from app.llm import _dispatch_llm_sync
        with pytest.raises(NotImplementedError, match="카카오 카나나"):
            _dispatch_llm_sync("some-model", "some-key", "test prompt", 128)


# ---------------------------------------------------------------------------
# _dispatch_llm_sync provider 분기 테스트 (google/anthropic)
# ---------------------------------------------------------------------------

def test_dispatch_google_calls_google_sync() -> None:
    """provider=google이면 _call_google_sync를 호출한다."""
    google_settings = _make_settings("google")

    with (
        patch("app.llm.get_settings", return_value=google_settings),
        patch("app.llm._call_google_sync", return_value='{"ok": true}') as mock_google,
    ):
        from app.llm import _dispatch_llm_sync
        result = _dispatch_llm_sync("gemini-2.0-flash-exp", "key", "prompt", 128)

    assert result == '{"ok": true}'
    mock_google.assert_called_once_with("gemini-2.0-flash-exp", "key", "prompt", 128)


def test_dispatch_anthropic_calls_anthropic_sync() -> None:
    """provider=anthropic이면 _call_anthropic_sync를 호출한다."""
    anthropic_settings = _make_settings("anthropic", model="claude-haiku-4-5")

    with (
        patch("app.llm.get_settings", return_value=anthropic_settings),
        patch("app.llm._call_anthropic_sync", return_value='{"ok": true}') as mock_ant,
    ):
        from app.llm import _dispatch_llm_sync
        result = _dispatch_llm_sync("claude-haiku-4-5", "key", "prompt", 128)

    assert result == '{"ok": true}'
    mock_ant.assert_called_once_with("claude-haiku-4-5", "key", "prompt", 128)


# ---------------------------------------------------------------------------
# _call_llm 캐시 통합 테스트
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_call_llm_uses_cache_on_hit() -> None:
    """캐시 히트 시 LLM SDK를 호출하지 않는다."""
    cached_response = json.dumps({"region": "강원도"})

    with (
        patch("app.llm.get_llm_cache", return_value=cached_response),
        patch("app.llm.set_llm_cache") as mock_set,
        patch("app.llm._dispatch_llm_sync") as mock_dispatch,
    ):
        from app.llm import _call_llm
        result = await _call_llm("test prompt", max_tokens=128)

    assert result == cached_response
    mock_dispatch.assert_not_called()
    mock_set.assert_not_called()


@pytest.mark.asyncio
async def test_call_llm_calls_dispatch_on_cache_miss() -> None:
    """캐시 미스 시 _dispatch_llm_sync를 호출하고 결과를 캐시에 저장한다."""
    llm_response = '{"region": "제주도"}'

    with (
        patch("app.llm.get_llm_cache", return_value=None),
        patch("app.llm.set_llm_cache") as mock_set,
        patch("app.llm._dispatch_llm_sync", return_value=llm_response),
    ):
        from app.llm import _call_llm
        result = await _call_llm("test prompt", max_tokens=128)

    assert result == llm_response
    mock_set.assert_called_once()
