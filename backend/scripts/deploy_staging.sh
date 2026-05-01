#!/usr/bin/env bash
# 스테이징 배포 스크립트 (devops 전용)
# 사전 요건: fly CLI 설치 및 로그인, Vercel CLI 설치 및 로그인

set -euo pipefail

TASK_ID="T20260501-001"
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${BACKEND_DIR}/../frontend"

echo "[deploy] === ${TASK_ID} 스테이징 배포 시작 ==="

# 1. 백엔드 Fly.io 배포
echo "[deploy] 1/3 백엔드 Fly.io 배포..."
cd "${BACKEND_DIR}"
fly deploy --remote-only --app travelai-api 2>&1 || {
    echo "[deploy] Fly.io CLI 미설치 또는 미로그인. 수동 배포 필요."
    echo "[deploy] 명령: cd code/backend && fly deploy"
}

# 2. 프론트엔드 Vercel 배포
echo "[deploy] 2/3 프론트엔드 Vercel 배포..."
cd "${FRONTEND_DIR}"
npm ci
npm run build
vercel deploy --prebuilt --token "${VERCEL_TOKEN:-}" 2>&1 || {
    echo "[deploy] Vercel CLI 미설치 또는 토큰 없음. 수동 배포 필요."
    echo "[deploy] 명령: cd code/frontend && vercel deploy"
}

echo "[deploy] 3/3 완료"
echo "[deploy] 스테이징 URL:"
echo "  백엔드:  https://travelai-api.fly.dev"
echo "  프론트:  https://travelai-staging.vercel.app"
echo "[deploy] 운영 배포는 사용자 /promote-to-prod ${TASK_ID} 명령 후 진행"
