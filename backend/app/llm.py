"""LLM 클라이언트 - 의도 추출 및 동선 생성.

provider 분기 구조:
  google    → google-generativeai SDK (현재 기본값)
  anthropic → anthropic SDK (폴백, 비활성)
  kakao     → NotImplementedError (CBT 통과 시 구현 예정)
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from app.config import get_settings
from app.database import get_llm_cache, set_llm_cache
from app.models import IntentData, PersonalityProfile

# ---------------------------------------------------------------------------
# MBTI 4축 → 여행 스타일 매핑 룰
# ---------------------------------------------------------------------------
_MBTI_AXIS_MAP: dict[str, dict[str, Any]] = {
    "E": {"활동성": 8, "스타일": "활발한 관광지와 대중적 명소 위주"},
    "I": {"활동성": 4, "스타일": "조용한 곳과 여유 있는 일정 위주"},
    "N": {"체험형": 8, "스타일": "독특한 체험과 숨은 명소 위주"},
    "S": {"체험형": 4, "스타일": "검증된 유명 관광지와 실용적 장소 위주"},
    "T": {"감성": 3, "스타일": "역사·문화재·박물관 등 정보 중심"},
    "F": {"감성": 8, "스타일": "감성 카페·예술·경치 등 감성 중심"},
    "J": {"즉흥성": 2, "스타일": "하루 4곳, 이동 최소화, 빈틈없는 일정"},
    "P": {"즉흥성": 8, "스타일": "하루 3곳, 여유 시간 포함, 즉흥 방문 가능 장소"},
}

_BLOOD_TYPE_KEYWORDS: dict[str, str] = {
    "A": "꼼꼼한, 차분한, 전통",
    "B": "자유로운, 개성, 독특한",
    "AB": "다재다능, 복합적, 아트",
    "O": "활발한, 대중적, 맛집",
    "모름": "",
    "": "",
}

_ZODIAC_KEYWORDS: dict[str, str] = {
    "양자리": "모험, 도전적, 액티비티",
    "황소자리": "안정, 미식, 자연",
    "쌍둥이자리": "다양성, 도시, 쇼핑",
    "게자리": "가족, 휴식, 해변",
    "사자자리": "화려함, 명소, 포토스팟",
    "처녀자리": "세심함, 문화재, 박물관",
    "천칭자리": "균형, 예술, 카페",
    "전갈자리": "신비, 야경, 밤거리",
    "사수자리": "자유, 산악, 트레킹",
    "염소자리": "실용, 전통시장, 로컬",
    "물병자리": "독특함, 숨은명소, 갤러리",
    "물고기자리": "감성, 바다, 일출/일몰",
    "": "",
}

# Gemini 모델 우선순위: 기본 모델 실패 시 폴백
_GEMINI_FALLBACK_MODEL = "gemini-1.5-flash"


def _build_personality_rule(profile: PersonalityProfile) -> str:
    """PersonalityProfile → LLM 시스템 프롬프트 주입 룰 문자열 생성."""
    if not profile.mbti:
        return ""

    mbti = profile.mbti
    axes = [mbti[0], mbti[1], mbti[2], mbti[3]]  # E/I, N/S, T/F, J/P

    style_parts: list[str] = []
    for axis in axes:
        info = _MBTI_AXIS_MAP.get(axis, {})
        if "스타일" in info:
            style_parts.append(str(info["스타일"]))

    style_str = "; ".join(style_parts)

    blood_kw = _BLOOD_TYPE_KEYWORDS.get(profile.blood_type, "")
    zodiac_kw = _ZODIAC_KEYWORDS.get(profile.zodiac, "")
    extra_kw_parts = [k for k in [blood_kw, zodiac_kw] if k]
    extra_kw = ", ".join(extra_kw_parts) if extra_kw_parts else "없음"

    note_line = f'- 사용자 메모: "{profile.note}"' if profile.note else ""

    rule = f"""
[성향 매핑 룰 - MBTI: {mbti}]
- 여행 스타일: {style_str}
- 추가 키워드 (혈액형/별자리 참고용, 결과에 직접 언급 금지): {extra_kw}
{note_line}
- 결과 JSON 에 "personality_comment" 필드를 추가하라.
  형식: "{mbti}라 [성향 반영 이유]를 골랐어요" (한 줄, 50자 이내, 한국어)
  예시: "ENFP라 즉흥적으로 들를 만한 카페를 골랐어요"
""".strip()

    return rule


def _make_cache_key(prompt: str) -> str:
    settings = get_settings()
    return f"{settings.llm_provider}:{settings.llm_model}:{prompt.strip().lower()}"


# ---------------------------------------------------------------------------
# Google Generative AI (provider="google")
# ---------------------------------------------------------------------------

def _call_google_sync(model: str, api_key: str, prompt: str, max_tokens: int) -> str:
    """google-generativeai SDK 동기 호출.

    structured output (JSON) 강제를 위해 response_mime_type 설정.
    기본 모델 실패(ResourceExhausted/NotFound) 시 fallback 모델 1회 재시도.
    """
    import importlib

    from google.api_core import exceptions as gexc

    # google.generativeai 의 타입 스텁이 불완전하므로 동적 접근 사용
    genai = importlib.import_module("google.generativeai")

    genai.configure(api_key=api_key)

    generation_config = genai.GenerationConfig(
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
    )

    def _try_model(model_name: str) -> str:
        gmodel = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
        )
        response = gmodel.generate_content(prompt)
        return str(response.text)

    try:
        return _try_model(model)
    except (gexc.NotFound, gexc.ResourceExhausted, gexc.InvalidArgument) as first_err:
        if model == _GEMINI_FALLBACK_MODEL:
            key_prefix = api_key[:4] if len(api_key) >= 4 else "****"
            raise RuntimeError(
                f"Gemini 호출 실패 (key={key_prefix}***): {first_err}"
            ) from first_err
        try:
            return _try_model(_GEMINI_FALLBACK_MODEL)
        except Exception as fallback_err:
            key_prefix = api_key[:4] if len(api_key) >= 4 else "****"
            raise RuntimeError(
                f"Gemini 폴백 모델({_GEMINI_FALLBACK_MODEL})도 실패 (key={key_prefix}***): {fallback_err}"
            ) from fallback_err


# ---------------------------------------------------------------------------
# Anthropic (provider="anthropic") - 폴백용, 비활성 기본값
# ---------------------------------------------------------------------------

def _call_anthropic_sync(model: str, api_key: str, prompt: str, max_tokens: int) -> str:
    """anthropic SDK 동기 호출 (provider="anthropic" 시 활성화)."""
    import anthropic as _anthropic  # noqa: PLC0415

    client = _anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    content = message.content[0]
    if hasattr(content, "text"):
        return str(content.text)
    return ""


# ---------------------------------------------------------------------------
# 통합 LLM 디스패처
# ---------------------------------------------------------------------------

def _dispatch_llm_sync(model: str, api_key: str, prompt: str, max_tokens: int) -> str:
    """provider 설정에 따라 적절한 LLM SDK를 호출한다."""
    settings = get_settings()
    provider = settings.llm_provider

    if provider == "google":
        return _call_google_sync(model, api_key, prompt, max_tokens)
    elif provider == "anthropic":
        return _call_anthropic_sync(model, api_key, prompt, max_tokens)
    elif provider == "kakao":
        # TODO: 카카오 카나나-o CBT 통과 후 구현 예정
        raise NotImplementedError(
            "카카오 카나나 provider는 CBT 통과 후 구현 예정입니다. "
            "현재는 LLM_PROVIDER=google 또는 anthropic을 사용하세요."
        )
    else:
        raise ValueError(f"알 수 없는 LLM provider: {provider}")


async def _call_llm(prompt: str, max_tokens: int = 512) -> str:
    """캐시를 먼저 확인하고, MISS 시 LLM 동기 호출을 스레드에서 실행한다."""
    cache_key = _make_cache_key(prompt)
    cached = await get_llm_cache(cache_key)
    if cached:
        return cached

    settings = get_settings()
    raw = await asyncio.to_thread(
        _dispatch_llm_sync,
        settings.llm_model,
        settings.llm_api_key,
        prompt,
        max_tokens,
    )
    await set_llm_cache(cache_key, raw)
    return raw


def _parse_json_response(raw: str) -> dict[str, Any]:
    """마크다운 코드 블록 제거 후 JSON 파싱."""
    cleaned = re.sub(r"```json\s*|\s*```", "", raw).strip()
    result: dict[str, Any] = json.loads(cleaned)
    return result


async def extract_intent(
    query: str,
    personality_profile: PersonalityProfile | None = None,
) -> IntentData:
    """자연어 쿼리에서 여행 의도를 추출한다.

    v2: personality_profile 이 있으면 MBTI 정보를 컨텍스트로 추가한다.
    """
    personality_ctx = ""
    if personality_profile and personality_profile.mbti:
        personality_ctx = (
            f'\n참고 성향 정보: MBTI={personality_profile.mbti}'
            + (f", 혈액형={personality_profile.blood_type}" if personality_profile.blood_type else "")
            + (f", 별자리={personality_profile.zodiac}" if personality_profile.zodiac else "")
            + (f', 메모="{personality_profile.note}"' if personality_profile.note else "")
        )

    prompt = f"""다음 자연어 여행 요청에서 여행 의도를 JSON으로 추출하라.

요청: "{query}"{personality_ctx}

반드시 다음 JSON 형식으로만 답하라. 설명 없이 JSON만:
{{
  "region": "지역명 (예: 강원도, 제주도, 서울)",
  "duration": "기간 (예: 2박3일, 당일치기)",
  "companions": ["동행자 유형 배열 (예: 부모님, 어린이, 혼자)"],
  "constraints": ["제약 조건 배열 (예: 무릎통증, 유모차동반, 허리통증)"],
  "preferences": ["선호 유형 배열 (예: 맛집, 자연, 역사, 체험)"]
}}"""

    raw = await _call_llm(prompt, max_tokens=512)
    data = _parse_json_response(raw)
    return IntentData(**data)


async def generate_course(
    intent: IntentData,
    candidates: list[dict[str, Any]],
    personality_profile: PersonalityProfile | None = None,
) -> dict[str, Any]:
    """후보 관광지와 의도에서 일자별 동선 JSON을 생성한다.

    v2: personality_profile 이 있으면 MBTI 4축 매핑 룰을 시스템 프롬프트에 주입한다.
    candidates 는 TourAPI 에서 반환한 contentId 범위 내의 장소만 포함한다.
    LLM 이 임의 장소를 생성하지 않도록 제약 프롬프트를 사용한다.
    """
    candidates_json = json.dumps(candidates[:30], ensure_ascii=False, indent=2)

    duration = intent.duration or "1박2일"
    num_days = _parse_days(duration)
    constraints_str = ", ".join(intent.constraints) if intent.constraints else "없음"
    preferences_str = ", ".join(intent.preferences) if intent.preferences else "일반"
    companions_str = ", ".join(intent.companions) if intent.companions else "혼자"

    # v2: 성향 매핑 룰 블록
    personality_rule = ""
    personality_comment_instruction = ""
    if personality_profile and personality_profile.mbti:
        personality_rule = _build_personality_rule(personality_profile)
        personality_comment_instruction = (
            '\n  "personality_comment": "MBTI라 ... 골랐어요 (한 줄, 50자 이내)",'
        )
    else:
        personality_comment_instruction = '\n  "personality_comment": "",'

    personality_section = f"\n{personality_rule}\n" if personality_rule else ""

    prompt = f"""다음 조건으로 여행 코스 JSON을 만들어라.

조건:
- 지역: {intent.region}
- 기간: {duration} ({num_days}일)
- 동행자: {companions_str}
- 제약: {constraints_str}
- 선호: {preferences_str}
{personality_section}
반드시 아래 후보 장소 목록에서만 선택하라. 후보에 없는 장소를 임의로 추가하지 말라.

후보 장소 목록 (contentId, name, lat, lng, address 포함):
{candidates_json}

반드시 다음 JSON 형식으로만 답하라. 설명 없이 JSON만:
{{
  "title": "코스 제목",
  "region": "{intent.region}",
  "duration": "{duration}",
  "summary": "코스 요약 한 줄",{personality_comment_instruction}
  "days": [
    {{
      "day": 1,
      "date_label": "1일차",
      "places": [
        {{
          "order": 1,
          "content_id": "후보의 contentId",
          "name": "장소명",
          "address": "주소",
          "lat": 37.0,
          "lng": 127.0,
          "image_url": "",
          "open_hours": "운영시간 또는 빈 문자열",
          "recommendation": "추천 사유 (제약 조건 반영)",
          "barrier_free": {{
            "certified": false,
            "wheelchair_rental": false,
            "parking_accessible": false,
            "note": ""
          }},
          "travel_to_next": {{
            "mode": "차량",
            "minutes": 15
          }}
        }}
      ]
    }}
  ]
}}

일자 수: {num_days}일, 하루 3~4곳 배치. 이동 거리 최소화."""

    raw = await _call_llm(prompt, max_tokens=4096)
    return _parse_json_response(raw)


def _parse_days(duration: str) -> int:
    """'2박3일' → 3, '당일치기' → 1."""
    if "당일" in duration:
        return 1
    match = re.search(r"(\d+)일", duration)
    if match:
        return int(match.group(1))
    match_bak = re.search(r"(\d+)박", duration)
    if match_bak:
        return int(match_bak.group(1)) + 1
    return 2
