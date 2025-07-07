# 🔧 DXF CAD 도면 분석기

AutoCAD DXF 파일을 분석하여 상세한 마크다운 리포트를 생성하는 상용화 가능한 Python 애플리케이션입니다.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## ✨ 주요 기능

### 🎯 핵심 기능
- **자동 DXF 파싱**: ezdxf 라이브러리 기반의 강력한 DXF 파일 분석
- **상세 객체 분석**: 치수, 원/호, 텍스트, 라인 등 모든 CAD 객체 자동 인식
- **레이어 정보 추출**: 색상, 라인타입, 상태 등 레이어 속성 분석
- **통계 정보 제공**: 객체 유형별 개수 및 분포 통계
- **마크다운 리포트 생성**: 전문적인 분석 리포트 자동 생성

### 🖥️ 사용자 인터페이스
- **GUI 버전**: tkinter 기반의 데스크톱 애플리케이션 (`dxf_analyzer_gui.py`)
- **웹 버전**: Streamlit 기반의 웹 애플리케이션 (`dxf_analyzer_webapp.py`)
- **CLI 버전**: 명령줄 인터페이스로 배치 처리 지원 (`dxf_analyzer.py`)
- **Cloud API**: FastAPI 기반의 REST API 제공 (`dxf_cloud_api.py`)
    - DXF 파일 업로드 및 분석 요청 (기본, 고급, 3D 분석 옵션 제공)
    - JWT 기반 인증 (선택적)
    - 비동기 작업 처리 및 상태 조회
    - 자동 생성되는 API 문서 (Swagger UI, ReDoc) 접근 가능 (기본: `http://localhost:8000/docs`)

### 📊 지원 형식
- AutoCAD DXF (Drawing Exchange Format)
- ASCII 및 Binary DXF 파일
- DXF R12, R2000, R2004, R2007, R2010, R2013, R2018

## 🚀 빠른 시작

### 1. 설치

#### Windows
```bash
# Git Clone 또는 파일 다운로드 후
install.bat
```

#### Linux/macOS
```bash
# Git Clone 또는 파일 다운로드 후
chmod +x install.sh
./install.sh
```

#### 수동 설치
```bash
pip install -r requirements.txt
```

### 2. 실행

#### GUI 버전 (추천)
```bash
python dxf_analyzer.py --gui
```

#### 웹 버전
```bash
python dxf_analyzer.py --web
```

#### CLI 버전
```bash
python dxf_analyzer.py --cli input_file.dxf
python dxf_analyzer.py --cli input_file.dxf -o custom_report.md
```

## 📋 사용법

### GUI 버전 사용법
1. 프로그램 실행
2. "찾아보기" 버튼으로 DXF 파일 선택
3. "분석 시작" 버튼 클릭
4. 결과를 탭별로 확인
   - **요약**: 기본 통계 정보
   - **상세 분석**: 객체별 상세 정보
   - **마크다운 미리보기**: 리포트 내용 확인
5. "리포트 내보내기"로 마크다운 파일 저장

### 웹 버전 사용법
1. 웹 브라우저에서 애플리케이션 접속
2. 드래그 앤 드롭으로 DXF 파일 업로드
3. 사이드바에서 분석 옵션 설정
4. "분석 시작" 버튼 클릭
5. 탭별로 결과 확인 및 다운로드

### CLI 버전 사용법
```bash
# 기본 사용법
python dxf_analyzer.py --cli drawing.dxf

# 출력 파일명 지정
python dxf_analyzer.py --cli drawing.dxf -o analysis_report.md

# 자세한 로그 출력
python dxf_analyzer.py --cli drawing.dxf --verbose
```

## 🔧 개발 환경 설정

### 개발 의존성 설치
```bash
make install-dev
# 또는
pip install -e .[dev]
```

### 개발 명령어
```bash
make help           # 사용 가능한 명령어 확인
make test           # 테스트 실행
make lint           # 코드 린팅
make format         # 코드 포맷팅
make build          # 패키지 빌드
make build-exe      # 실행 파일 생성

### 테스트 실행
```bash
# 모든 테스트 실행 (test_*.py 패턴)
python -m unittest discover

# 특정 테스트 파일 실행
python test_dxf_analyzer.py
python test_v2_features.py
```

## 📁 프로젝트 구조

```
dxf-analyzer/
├── dxf_analyzer.py          # 메인 실행 파일
├── dxf_analyzer_webapp.py   # Streamlit 웹 애플리케이션
├── requirements.txt         # 필수 라이브러리 목록
├── setup.py                 # 패키지 설정
├── README.md               # 이 파일
├── install.bat             # Windows 설치 스크립트
├── install.sh              # Linux/macOS 설치 스크립트
├── Makefile                # 개발용 빌드 스크립트
└── examples/               # 예제 파일들
    └── sample.dxf          # 샘플 DXF 파일
```

## 🛠️ 기술 스택

- **Python 3.8+**: 핵심 언어
- **ezdxf**: DXF 파일 파싱 라이브러리
- **tkinter**: GUI 프레임워크 (기본 내장)
- **Streamlit**: 웹 애플리케이션 프레임워크
- **pandas**: 데이터 처리 (웹 버전)
- **PyInstaller**: 실행 파일 생성

## 📈 성능

- **파일 크기**: 최대 100MB DXF 파일 지원
- **처리 속도**: 일반적인 도면 파일(1-10MB) 처리 시간 1-5초
- **메모리 사용**: 파일 크기의 5-10배 RAM 사용
- **호환성**: DXF R12 ~ R2018 모든 버전 지원

## 🎯 사용 사례

### 제조업체
- 도면 검토 및 품질 관리
- 설계 변경사항 추적
- 제조 사양 추출

### 엔지니어링 회사
- 프로젝트 도면 분석
- 설계 표준 준수 확인
- 클라이언트 리포트 생성

### 교육 기관
- CAD 교육 자료 생성
- 학생 과제 평가
- 설계 프로세스 교육

## 🔒 라이선스

MIT License - 상용화 사용 가능

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📞 지원

- **이슈 리포트**: GitHub Issues 사용
- **기능 요청**: GitHub Issues에 "enhancement" 라벨
- **문서**: Wiki 페이지 참조

## 🗺️ 로드맵

### v1.1.0 (계획)
- [ ] 3D 객체 지원 확장
- [ ] DWG 파일 직접 지원
- [ ] PDF 리포트 생성
- [ ] 도면 비교 기능

### v1.2.0 (계획)
- [ ] 클라우드 배포 지원
- [ ] REST API 제공
- [ ] 데이터베이스 연동
- [ ] 다국어 지원

## 📊 예제 출력

```markdown
# CAD 도면 분석 리포트

- **원본 파일:** `example.dxf`
- **리포트 생성일:** `2025-01-01 12:00:00`

## 1. 도면 요약 정보

- **전체 객체 수:** 1,234
- **레이어 수:** 15
- **치수 객체 수:** 45
- **원 객체 수:** 28
- **문자 객체 수:** 156

## 2. 레이어 목록

| No. | 레이어 이름 | 색상 코드 | 라인타입 | 상태 |
|-----|-------------|-----------|----------|------|
| 1   | 0           | 7         | CONTINUOUS | Normal |
| 2   | 치수        | 3         | CONTINUOUS | Normal |
...
```

---

**DXF CAD 도면 분석기** - 설계 효율성을 높이는 스마트 솔루션