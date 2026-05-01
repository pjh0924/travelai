FROM python:3.12-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사
COPY app/ ./app/

# DB 스키마 복사 (백엔드와 별도 경로에서 참조)
COPY ../db/schema.sql ./db/schema.sql 2>/dev/null || true

# 데이터 디렉토리 생성
RUN mkdir -p /app/data

ENV DATABASE_URL="sqlite:////app/data/travelai.db"
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
