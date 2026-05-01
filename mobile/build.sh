#!/usr/bin/env bash
# Capacitor Android APK 빌드 스크립트
# 사전 요건: Node.js, Java 17+, Android SDK (ANDROID_HOME 설정)
# v2 변경: PersonalityFormPage (/personality) 라우트 포함 확인 단계 추가

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${SCRIPT_DIR}/../frontend"
MOBILE_DIR="${SCRIPT_DIR}"

echo "[build.sh] 1/5 프론트엔드 빌드..."
cd "${FRONTEND_DIR}"
npm ci
npm run build

# v2: /personality 라우트가 번들에 포함됐는지 확인
echo "[build.sh] 1.5/5 v2 라우트 확인 (/personality)..."
if grep -r "PersonalityFormPage\|/personality" dist/ --include="*.js" -l | head -1 | grep -q .; then
  echo "[build.sh] /personality 라우트 번들 포함 확인됨"
else
  echo "[build.sh] WARNING: /personality 라우트가 번들에서 발견되지 않음. App.tsx 를 확인하세요."
  exit 1
fi

echo "[build.sh] 2/5 Capacitor 의존성 설치..."
cd "${MOBILE_DIR}"
npm ci

echo "[build.sh] 3/5 Capacitor sync..."
npx cap sync android

echo "[build.sh] 4/5 Gradle APK 빌드..."
cd android
./gradlew assembleDebug

APK_PATH="$(find . -name '*.apk' | head -1)"
echo "[build.sh] 5/5 완료: ${APK_PATH}"
