# 트레블AI (TravelAI)

> 2026 한국관광공사 × 카카오 관광데이터 활용 공모전 (웹·앱 개발 부문) 출품작

자연어 한 문장 또는 MBTI 입력으로 8초 안에 일자별 여행 동선을 자동 생성하는 AI 여행 코스 추천 서비스.

## 핵심 기능

- **자연어 코스 생성** — "2박3일 강원도 부모님 모시고 무릎 안 좋으세요" → 무장애 친화 동선 자동 생성
- **MBTI 성향 매칭** — MBTI 16종 + 혈액형 + 별자리 입력으로 성향 반영 코스
- **카카오맵 동선 시각화** — 마커 + 폴리라인 + 일자별 이동 시간
- **공유 가능한 코스 URL** — `/trip/<uuid>` 정적 라우트
- **무장애 정보 카드** — 휠체어·엘리베이터·주차 매칭

## 기술 스택

| 영역 | 선택 |
|---|---|
| 프론트 | React + Vite + TypeScript + Tailwind + shadcn/ui |
| 지도 | react-kakao-maps-sdk |
| 백엔드 | FastAPI + Python 3.11 |
| LLM | Google Gemini 2.0 Flash (메인) / Anthropic Claude (폴백) / Kakao Kanana-o (CBT 통과 시 활성화) |
| DB | SQLite (P0) → PostgreSQL (P1) |
| 모바일 | Capacitor 6 + Android |
| 배포 | Vercel (프론트) + Fly.io (API) |

## 데이터 출처

- **한국관광공사 TourAPI 4.0** — `areaBasedList2`, `searchKeyword2`, `detailCommon2`, `detailIntro2`, `detailImage2`
- **카카오 OpenAPI** — 카카오맵 JS SDK, 카카오 OAuth(P1)

## 폴더 구조

```
code/
├── backend/         # FastAPI 서버 + LLM 파이프라인
├── frontend/        # React + Vite + Capacitor 셸
├── mobile/          # Capacitor Android 빌드
└── db/              # SQLite 마이그레이션
```

## 로컬 실행

```bash
# 백엔드
cd backend
cp .env.example .env  # TOURAPI_KEY, LLM_API_KEY 채우기
pip install -r requirements.txt
python ../db/migrate.py && python ../db/migrate_v2.py
uvicorn app.main:app --reload --port 8000

# 프론트엔드
cd frontend
cp .env.example .env  # VITE_KAKAO_MAP_KEY 채우기
npm install
npm run dev
```

브라우저에서 http://localhost:5173 접속.

## LLM Provider 전환

```bash
# .env
LLM_PROVIDER=google      # 기본 (Gemini 2.0 Flash)
LLM_PROVIDER=anthropic   # 폴백 (Claude)
LLM_PROVIDER=kakao       # 카카오 카나나-o CBT 통과 후 활성화 예정
```

## 7월 구현 부문 확장 로드맵

- 카카오 카나나-o LLM 정식 통합 (CBT 통과 시)
- 멀티모달 입력: 음성 + 이미지로 코스 생성
- 카카오 OAuth 로그인 + 내 코스 저장
- 동행자 협업 편집
- 외국인 별자리 추천으로 글로벌 확장

## License

MIT
