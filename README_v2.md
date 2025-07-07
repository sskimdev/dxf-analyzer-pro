# DXF CAD 도면 분석기 v2.0 - Enhanced Edition

## 🎯 소개

DXF CAD 도면 분석기 v2.0은 AutoCAD DXF 파일을 종합적으로 분석하는 전문 도구입니다. 
이번 버전에서는 3D 지원, 도면 비교, 자동 수정, 클라우드 API, AI 통합 등 혁신적인 기능들이 추가되었습니다.

## 🆕 v2.0 주요 신기능

### 1. 🧊 3D 엔티티 분석
- 3D 솔리드, 서피스, 메시 분석
- Z축 범위 및 공간 메트릭
- 3D 복잡도 평가
- 부피 추정 (베타)

### 2. 📊 도면 버전 비교
- 두 DXF 파일 간 상세 비교
- 추가/제거/수정된 요소 추적
- 변경 수준 평가
- 비교 리포트 생성

### 3. 🔧 자동 수정
- 표준 미준수 자동 수정
- 중복 객체 제거
- 레이어 구조 정리
- 텍스트 크기 표준화

### 4. ☁️ 클라우드 API
- RESTful API 서버
- JWT 인증
- 비동기 처리
- 대용량 파일 지원

### 5. 🤖 AI 통합
- OpenAI GPT-4 연동
- Claude 3 연동
- 전문가 수준 분석
- 대화형 Q&A

## 📋 요구사항

### 필수
- Python 3.8+
- ezdxf >= 1.1.0

### 선택 (기능별)
```bash
# API 서버
pip install fastapi uvicorn aiofiles pyjwt

# AI 통합
pip install openai anthropic

# 전체 설치
pip install -r requirements.txt
```

## 🚀 빠른 시작

### 1. GUI 실행 (v2.0 Enhanced)
```bash
python dxf_analyzer.py --gui
```

### 2. API 서버 시작
```bash
python dxf_cloud_api.py
# http://localhost:8000/docs 에서 API 문서 확인
```

### 3. 통합 예시 실행
```bash
python example_usage_v2.py
```

## 📖 상세 사용법

### 3D 분석
```python
from dxf_3d_analyzer import DXF3DAnalyzer

analyzer_3d = DXF3DAnalyzer()
result_3d = analyzer_3d.analyze_3d_entities(msp, analysis_data)

if result_3d['is_3d']:
    print(f"3D 엔티티: {result_3d['3d_entity_count']}개")
    print(f"Z축 범위: {result_3d['z_range']['min']} ~ {result_3d['z_range']['max']}")
```

### 도면 비교
```python
from dxf_comparison import DXFComparison

comparator = DXFComparison()
differences = comparator.compare_dxf_files(analysis1, analysis2)

print(f"변경 수준: {differences['summary']['change_level']}")
report = comparator.generate_comparison_report()
```

### 자동 수정
```python
from dxf_auto_fix import DXFAutoFix

fixer = DXFAutoFix()
fixer.load_file("problematic.dxf")
backup = fixer.create_backup("problematic.dxf")
fixes = fixer.auto_fix_all(analysis_data)
fixer.save_fixed_file("fixed.dxf")
```

### AI 분석
```python
from dxf_ai_integration import DXFAIIntegration
import asyncio

ai = DXFAIIntegration()
result = await ai.analyze_with_both(analysis_data, 'analysis')
report = ai.generate_ai_report(result)

# 대화형 질의
answer = await ai.interactive_chat("도면 품질을 개선하려면?", analysis_data)
```

### API 사용
```bash
# 인증
curl -X POST "http://localhost:8000/api/auth/token" \
  -d "username=demo&password=demo123"

# 분석
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample.dxf" \
  -F "include_advanced=true" \
  -F "include_3d=true"

# 비교
curl -X POST "http://localhost:8000/api/compare" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file1=@v1.dxf" \
  -F "file2=@v2.dxf"
```

## 🌐 환경 변수

```bash
# AI API 키 (선택사항)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# API 서버 설정
export SECRET_KEY="your-secret-key"
```

## 📊 분석 가능 항목

### 기본 분석 (v1.0)
- 파일 정보 및 메타데이터
- 레이어 구조
- 엔티티 분류 및 통계
- 치수, 텍스트, 블록 정보
- 도면 경계 및 크기

### 고급 분석 (v1.0)
- 도면 품질 평가 (A~F 등급)
- ISO/KS 표준 준수 검증
- 이상 징후 탐지
- 패턴 분석
- AI 컨텍스트 생성

### 신규 분석 (v2.0)
- **3D 분석**: 솔리드, 서피스, 메시, 공간 메트릭
- **비교 분석**: 버전 간 차이점, 변경 추적
- **자동 수정**: 문제 자동 해결, 표준화
- **AI 인사이트**: GPT-4/Claude 기반 전문가 분석

## 🛠️ 개발자 가이드

### 모듈 구조
```
dxf-analyzer-v2/
├── dxf_analyzer.py          # 메인 분석 엔진
├── dxf_advanced_analyzer.py # 고급 분석
├── dxf_3d_analyzer.py       # 3D 분석 (신규)
├── dxf_comparison.py        # 비교 엔진 (신규)
├── dxf_auto_fix.py         # 자동 수정 (신규)
├── dxf_cloud_api.py        # API 서버 (신규)
├── dxf_ai_integration.py   # AI 통합 (신규)
└── example_usage_v2.py     # 통합 예시 (신규)
```

### 확장 개발
```python
# 커스텀 분석기 추가
class MyCustomAnalyzer:
    def analyze(self, dxf_data):
        # 커스텀 분석 로직
        return results

# AI 프롬프트 커스터마이징
ai = DXFAIIntegration()
ai.prompts['custom'] = "당신의 커스텀 프롬프트..."
```

## 📈 성능 최적화

- **병렬 처리**: 대용량 파일 분석 시 멀티스레딩
- **캐싱**: 반복 분석 시 결과 캐싱
- **스트리밍**: API에서 대용량 파일 스트리밍 처리
- **비동기**: AI 분석 및 API 요청 비동기 처리

## 🔒 보안

- JWT 기반 API 인증
- 파일 업로드 크기 제한
- 입력 검증 및 sanitization
- API 요청 속도 제한 (Rate Limiting)

## 🐛 문제 해결

### AI API 키 오류
```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

### 3D 분석 메모리 부족
```python
# 청크 단위로 분석
analyzer_3d.chunk_size = 1000
```

### API 서버 포트 충돌
```python
# dxf_cloud_api.py 수정
uvicorn.run(app, port=8001)  # 다른 포트 사용
```

## 📜 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

## 🤝 기여

기여를 환영합니다! Pull Request를 보내주세요.

## 📞 지원

- 이슈: GitHub Issues
- 이메일: support@dxfanalyzer.com
- 문서: https://docs.dxfanalyzer.com

---

**DXF Analyzer v2.0** - CAD 도면 분석의 새로운 표준 🚀 

## 🤖 AI 통합 (v2.0)

### 지원 AI 모델
- **OpenAI GPT-4**: 고급 도면 분석 및 설계 검토
- **Claude 3**: 복잡한 제조 문제 해결
- **Google Gemini**: 빠른 분석 및 실시간 인사이트

### AI 기능
- 도면 품질 자동 평가
- 설계 개선 제안
- 제조 가능성 검토
- 비용 최적화 제안
- 대화형 질의응답

### 환경 변수 설정
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-claude-key"
export GOOGLE_API_KEY="your-gemini-key"
```

## 🏭 CNC 특화 기능 (v2.1)

### CNC 가공성 분석
```python
from dxf_cnc_analyzer import DXFCNCAnalyzer

analyzer = DXFCNCAnalyzer()
result = analyzer.analyze_machinability(
    "drawing.dxf",
    material="aluminum"
)

# 가공성 점수 (A-F 등급)
print(f"가공성 등급: {result['machinability_score'].grade}")
print(f"예상 가공 시간: {result['machining_time']['total_minutes']}분")
```

### 주요 분석 항목
- **가공성 평가**: 복잡도, 공구 접근성, 공차 실현성
- **공구 추천**: 재료별 최적 공구 및 가공 조건
- **가공 시간 예측**: 설정, 절삭, 공구 교환 시간
- **공구 경로 최적화**: 효율성 개선 제안
- **문제점 식별**: 잠재적 가공 이슈 사전 감지

## 💰 제조 비용 예측 (v2.1)

### 비용 예측 기능
```python
from dxf_cost_estimator import DXFCostEstimator

estimator = DXFCostEstimator()
cost = estimator.estimate_total_cost(
    "drawing.dxf",
    material_spec={
        'type': 'aluminum',
        'grade': '6061',
        'thickness': 10
    },
    production_qty=100
)

print(f"단가: {cost['unit_price_after_discount']:,}원")
print(f"총 비용: {cost['total_production_cost']:,}원")
```

### 비용 분석 요소
- **재료비**: 원재료, 재료 손실률
- **가공비**: 기계 시간, 인건비
- **공구비**: 공구 마모, 소모품
- **추가 비용**: 품질관리, 간접비, 이익
- **수량 할인**: 대량 생산 시 할인율

## 📊 비즈니스 대시보드 (v2.1)

### 경영진용 대시보드
```bash
# Streamlit 대시보드 실행
streamlit run dxf_business_dashboard.py
```

### 주요 기능
- **종합 대시보드**: KPI, 실시간 분석
- **비용 분석**: 비용 구성, 절감 기회
- **생산성 분석**: 설비 가동률, 병목 공정
- **품질 트렌드**: 품질 지표, 불량 원인
- **AI 인사이트**: 자동 분석 및 제안
- **프로젝트 관리**: 일정, 리스크 관리

## 🔄 통합 워크플로우

### 전체 분석 파이프라인
```python
from dxf_analyzer import DXFAnalyzer
from dxf_advanced_analyzer import DXFAdvancedAnalyzer
from dxf_cnc_analyzer import DXFCNCAnalyzer
from dxf_cost_estimator import DXFCostEstimator
from dxf_ai_integration import DXFAIIntegration

# 1. 기본 분석
analyzer = DXFAnalyzer()
basic_analysis = analyzer.analyze_dxf("drawing.dxf")

# 2. 고급 분석
advanced = DXFAdvancedAnalyzer()
quality_analysis = advanced.analyze_quality("drawing.dxf")

# 3. CNC 분석
cnc = DXFCNCAnalyzer()
cnc_analysis = cnc.analyze_machinability("drawing.dxf", "aluminum")

# 4. 비용 예측
estimator = DXFCostEstimator()
cost_analysis = estimator.estimate_total_cost(
    "drawing.dxf",
    {'type': 'aluminum', 'grade': '6061'},
    100
)

# 5. AI 통합 분석
ai = DXFAIIntegration()
ai_insights = await ai.analyze_with_all(
    basic_analysis,
    prompt_type='cnc_analysis'
)
``` 