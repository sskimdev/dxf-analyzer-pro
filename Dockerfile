FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요 패키지 설치
RUN apt-get update && apt-get install -y \
    tk-dev \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 포트 노출 (Streamlit용)
EXPOSE 8501

# 기본 실행 명령어 (웹 버전)
CMD ["python", "dxf_analyzer.py", "--web"]
