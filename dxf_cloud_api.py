#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF Cloud API - FastAPI 기반 DXF 분석 서버
Author: API Development Team
Version: 1.1.0
"""

import os
import logging
import tempfile
import asyncio
import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Security, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware # CORS 추가
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import jwt # PyJWT
from jwt.exceptions import PyJWTError
from pathlib import Path # UPLOAD_DIR 사용


# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

# 현재 디렉토리를 Python 경로에 추가 (dxf_analyzer 등을 임포트하기 위함)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- 분석 모듈 임포트 ---
ANALYZER_AVAILABLE = False
ADVANCED_ANALYZER_AVAILABLE = False
THREE_D_ANALYZER_AVAILABLE = False

try:
    from dxf_analyzer import DXFAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    logger.warning("DXFAnalyzer 모듈을 임포트할 수 없습니다. 기본 분석 기능이 제한될 수 있습니다.")
    DXFAnalyzer = None # type: ignore

try:
    from dxf_advanced_analyzer import DXFAdvancedAnalyzer
    ADVANCED_ANALYZER_AVAILABLE = True
except ImportError:
    logger.info("DXFAdvancedAnalyzer 모듈을 임포트할 수 없습니다. 고급 분석 기능을 사용할 수 없습니다.")
    DXFAdvancedAnalyzer = None # type: ignore

try:
    from dxf_3d_analyzer import DXF3DAnalyzer
    THREE_D_ANALYZER_AVAILABLE = True
except ImportError:
    logger.info("DXF3DAnalyzer 모듈을 임포트할 수 없습니다. 3D 분석 기능을 사용할 수 없습니다.")
    DXF3DAnalyzer = None # type: ignore


# --- JWT 설정 ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-very-secure-secret-key-for-production") # 실제 운영시에는 환경변수로 설정 필수
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)) # 24시간

security = HTTPBearer()

# 임시 파일 저장 경로 및 작업 상태 저장 (간단한 인메모리 방식)
UPLOAD_DIR = Path(tempfile.gettempdir()) / "dxf_api_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
analysis_jobs: Dict[str, Any] = {}


class TokenData(BaseModel):
    username: Optional[str] = None

class UserCredentials(BaseModel):
    username: str
    password: str


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> TokenData:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token payload: sub field missing")
        return TokenData(username=username)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token has expired")
    except PyJWTError: # PyJWT의 기본 예외
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials, invalid token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- FastAPI 앱 초기화 ---
app = FastAPI(
    title="DXF Analyzer Cloud API",
    version="1.1.0", # 버전 업데이트
    description="DXF 파일 분석 및 관련 기능을 제공하는 API입니다. `/docs` 또는 `/redoc`에서 API 문서를 확인하세요."
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중에는 "*" 사용, 프로덕션에서는 실제 프론트엔드 도메인 지정
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# --- 요청 및 응답 모델 정의 ---
class FileInfo(BaseModel):
    """분석된 파일의 기본 정보"""
    filename: str = Field(..., description="원본 파일의 이름", example="drawing_rev2.dxf")
    size_bytes: int = Field(..., description="파일 크기 (bytes)", example=1024576)
    content_type: Optional[str] = Field(None, description="파일의 MIME 타입", example="application/dxf")

class BasicSummary(BaseModel):
    """DXF 파일의 기본 분석 요약 정보"""
    total_entities: int = Field(..., description="도면 내 총 엔티티(객체) 수", example=1250)
    layer_count: int = Field(..., description="사용된 레이어의 총 수", example=15)
    entity_breakdown: Dict[str, int] = Field(..., description="엔티티 유형별 개수", example={"LINE": 500, "CIRCLE": 120, "TEXT": 80})

class AdvancedSummary(BaseModel):
    """고급 분석 결과 요약 (품질, 표준 등)"""
    quality_score: Optional[float] = Field(None, description="계산된 도면 품질 점수 (0-100)", example=85.5)
    quality_grade: Optional[str] = Field(None, description="도면 품질 등급", example="B+")
    issues_detected: Optional[List[str]] = Field(None, description="발견된 주요 문제점 또는 경고 목록", example=["미참조 레이어: 3개", "중복 객체: 12개"])

class ThreeDSummary(BaseModel):
    """3D 분석 결과 요약"""
    is_3d: bool = Field(..., description="도면이 3D 정보를 포함하는지 여부", example=True)
    bounding_box_diagonal: Optional[float] = Field(None, description="3D 객체들을 포함하는 경계 상자의 대각선 길이", example=1500.75)
    solid_count: Optional[int] = Field(None, description="3D 솔리드 객체의 수", example=5)
    mesh_count: Optional[int] = Field(None, description="메시 객체의 수", example=2)

class AnalysisResultData(BaseModel):
    """최종 분석 결과를 통합하는 모델"""
    file_info: FileInfo = Field(..., description="파일 정보")
    basic_summary: BasicSummary = Field(..., description="기본 분석 요약")
    advanced_summary: Optional[AdvancedSummary] = Field(None, description="고급 분석 결과 (요청 시)")
    three_d_summary: Optional[ThreeDSummary] = Field(None, description="3D 분석 결과 (요청 시)")
    # report_markdown: Optional[str] = Field(None, description="생성된 마크다운 리포트 내용 (필요시)")

class AnalysisJobResponse(BaseModel):
    """분석 작업 요청에 대한 응답 모델"""
    job_id: str = Field(..., description="생성된 분석 작업의 고유 ID", example="a1b2c3d4-e5f6-7890-1234-567890abcdef")
    status: str = Field(..., description="현재 작업 상태 (예: pending, processing)", example="pending")
    message: str = Field(..., description="요청 처리 결과 메시지", example="분석 요청이 접수되었으며 백그라운드에서 처리 중입니다.")
    result_url: Optional[str] = Field(None, description="작업 상태 및 결과 확인을 위한 URL", example="/api/analyze/status/a1b2c3d4-e5f6-7890-1234-567890abcdef")

class AnalysisResultResponse(BaseModel):
    """분석 작업 상태 및 결과 조회 응답 모델"""
    job_id: str = Field(..., description="조회한 분석 작업의 고유 ID")
    status: str = Field(..., description="작업 상태 (예: completed, failed, processing)")
    analysis_data: Optional[AnalysisResultData] = Field(None, description="분석 완료 시 결과 데이터")
    error_message: Optional[str] = Field(None, description="오류 발생 시 오류 메시지")


# --- API 엔드포인트 ---
@app.post("/token", summary="인증 토큰 발급", tags=["인증"])
async def login_for_access_token(form_data: UserCredentials):
    # 실제 애플리케이션에서는 사용자 데이터베이스와 비교하여 인증합니다.
    # 여기서는 데모용으로 간단한 사용자 정보를 사용합니다.
    if form_data.username == "testuser" and form_data.password == "testpass":
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def run_analysis_in_background(job_id: str, file_path: str, include_advanced: bool, include_3d: bool):
    """백그라운드에서 실제 분석을 수행하는 함수"""
    try:
        logger.info(f"[Job {job_id}] 분석 시작: {file_path}")
        analysis_jobs[job_id]['status'] = 'processing'
        
        analyzer = DXFAnalyzer()
        analysis_success = await asyncio.to_thread(analyzer.analyze_dxf_file, file_path)

        if not analysis_success or not analyzer.analysis_data:
            logger.error(f"[Job {job_id}] 기본 분석 실패.")
            analysis_jobs[job_id].update({'status': 'failed', 'error_message': '기본 DXF 분석 실패'})
            return

        basic_data = analyzer.analysis_data
        file_info_data = basic_data.get('file_info', {})
        summary_info_data = basic_data.get('summary_info', {})

        result_data = AnalysisResultData(
            file_info=FileInfo(
                filename=file_info_data.get('filename', Path(file_path).name),
                size_bytes=file_info_data.get('size', 0),
                content_type="application/dxf" # 실제 content_type은 UploadFile에서 가져올 수 있음
            ),
            basic_summary=BasicSummary(
                total_entities=summary_info_data.get('total_entities', 0),
                layer_count=summary_info_data.get('layer_count', 0),
                entity_breakdown=summary_info_data.get('entity_breakdown', {})
            )
        )
        
        # 고급 분석
        if include_advanced and ADVANCED_ANALYZER_AVAILABLE and DXFAdvancedAnalyzer:
            logger.info(f"[Job {job_id}] 고급 분석 수행...")
            adv_analyzer = analyzer.advanced_analyzer # DXFAnalyzer가 생성한 인스턴스 사용
            if adv_analyzer:
                # generate_ai_context가 동기 함수라고 가정하고 to_thread 사용
                adv_context = await asyncio.to_thread(adv_analyzer.generate_ai_context, basic_data)
                result_data.advanced_summary = AdvancedSummary(
                    quality_score=adv_context.get('summary',{}).get('quality_score'),
                    quality_grade=adv_context.get('summary',{}).get('quality_grade'),
                    issues_detected=[item.get('description') for item in adv_context.get('anomalies', [])[:5]] # 상위 5개 이슈
                )
            else:
                 logger.warning(f"[Job {job_id}] 고급 분석기 인스턴스가 없습니다.")
        
        # 3D 분석
        if include_3d and THREE_D_ANALYZER_AVAILABLE and DXF3DAnalyzer:
            logger.info(f"[Job {job_id}] 3D 분석 수행...")
            import ezdxf # msp 객체 필요
            doc = await asyncio.to_thread(ezdxf.readfile, file_path)
            msp = doc.modelspace()
            analyzer_3d = DXF3DAnalyzer()
            three_d_results_dict = await asyncio.to_thread(analyzer_3d.analyze_3d_entities, msp, basic_data.copy())

            bb_diag = None
            if three_d_results_dict.get('spatial_metrics', {}).get('bounds_3d'):
                 # 간단한 대각선 길이 계산 예시 (실제로는 더 복잡할 수 있음)
                 b = three_d_results_dict['spatial_metrics']['bounds_3d']
                 if b['min'] and b['max']:
                    bb_diag = sum([(b['max'][i] - b['min'][i])**2 for i in range(3)])**0.5

            result_data.three_d_summary = ThreeDSummary(
                is_3d=three_d_results_dict.get('is_3d', False),
                bounding_box_diagonal=bb_diag,
                solid_count=three_d_results_dict.get('solids', {}).get('count'),
                mesh_count=three_d_results_dict.get('meshes', {}).get('count')
            )

        analysis_jobs[job_id].update({
            'status': 'completed',
            'analysis_data': result_data,
            'completed_at': datetime.utcnow().isoformat()
        })
        logger.info(f"[Job {job_id}] 분석 완료.")

    except Exception as e:
        logger.error(f"[Job {job_id}] 분석 중 오류 발생: {e}", exc_info=True)
        analysis_jobs[job_id].update({'status': 'failed', 'error_message': str(e)})
    finally:
        # 임시 파일 삭제
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.info(f"[Job {job_id}] 임시 파일 삭제: {file_path}")
            except Exception as e_unlink:
                logger.error(f"[Job {job_id}] 임시 파일 삭제 실패 {file_path}: {e_unlink}")


@app.post("/api/analyze", response_model=AnalysisJobResponse, status_code=status.HTTP_202_ACCEPTED, summary="DXF 파일 분석 요청", tags=["분석"])
async def request_dxf_analysis(
    file: UploadFile = File(..., description="분석할 DXF 파일. 반드시 '.dxf' 확장자를 가져야 합니다."),
    include_advanced: bool = Form(False, description="응답에 고급 분석 결과를 포함할지 여부를 지정합니다. (예: 품질 점수, 이상 징후 등)"),
    include_3d: bool = Form(False, description="응답에 3D 분석 결과를 포함할지 여부를 지정합니다. (예: 3D 객체 정보, Z축 범위 등)"),
    current_user: TokenData = Depends(get_current_user) # JWT 인증 활성화 시 주석 해제하여 사용
):
    """
    DXF 파일을 업로드하여 비동기적으로 분석을 요청합니다.

    - **file**: 분석할 DXF 파일 (multipart/form-data).
    - **include_advanced**: 고급 분석 옵션 (form data).
    - **include_3d**: 3D 분석 옵션 (form data).

    요청이 성공하면, 분석 작업 ID와 상태 확인 URL을 포함하는 응답을 반환합니다.
    실제 분석은 백그라운드에서 수행됩니다.
    """
    if not ANALYZER_AVAILABLE: # DXFAnalyzer 필수
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="분석 서비스 현재 사용 불가")

    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'.dxf' 파일만 업로드 가능합니다.")

    job_id = str(uuid.uuid4())
    file_location = UPLOAD_DIR / f"{job_id}_{file.filename}"

    try:
        # 비동기 파일 저장
        async with open(file_location, "wb") as f:
            await f.write(await file.read())
        logger.info(f"파일 업로드 완료: {file_location} (요청자: {current_user.username})")
        
        analysis_jobs[job_id] = {
            'status': 'pending',
            'original_filename': file.filename,
            'user': current_user.username,
            'created_at': datetime.utcnow().isoformat()
        }
        # 백그라운드 작업으로 분석 실행
        asyncio.create_task(run_analysis_in_background(job_id, str(file_location), include_advanced, include_3d))
        
        return AnalysisJobResponse(
            job_id=job_id,
            status="pending",
            message="분석 요청이 접수되었으며 백그라운드에서 처리 중입니다.",
            result_url=f"/api/analyze/status/{job_id}"
        )
    except Exception as e:
        logger.error(f"파일 업로드 또는 분석 요청 처리 중 오류: {e}", exc_info=True)
        # 실패 시 생성된 임시 파일 삭제 시도
        if os.path.exists(file_location):
            try:
                os.unlink(file_location)
            except Exception as e_unlink:
                 logger.error(f"업로드 실패 후 임시 파일 삭제 오류 {file_location}: {e_unlink}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"서버 오류: {str(e)}")


@app.get("/api/analyze/status/{job_id}", response_model=AnalysisResultResponse, summary="분석 작업 상태 및 결과 확인", tags=["분석"])
async def get_analysis_job_status(job_id: str = Path(..., description="조회할 분석 작업의 고유 ID", example="a1b2c3d4-e5f6-7890-1234-567890abcdef"),
                                current_user: TokenData = Depends(get_current_user)):
    """
    지정된 작업 ID에 대한 분석 진행 상태 및 완료 시 분석 결과를 조회합니다.

    - **job_id**: `/api/analyze` 요청 시 반환받은 작업 ID.

    작업이 `completed` 상태일 경우 `analysis_data` 필드에 분석 결과가 포함됩니다.
    오류 발생 시 `error_message` 필드에 오류 내용이 포함됩니다.
    """
    job = analysis_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 ID의 분석 작업을 찾을 수 없습니다.")
    
    # 요청한 사용자가 작업 소유자인지 확인 (실제 환경에서는 더 견고한 권한 관리 필요)
    if job.get('user') != current_user.username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="이 작업에 접근할 권한이 없습니다.")

    return AnalysisResultResponse(
        job_id=job_id,
        status=job.get('status', 'unknown'),
        analysis_data=job.get('analysis_data'), # Pydantic 모델로 자동 변환/검증됨
        error_message=job.get('error_message')
    )


@app.get("/health", summary="API 상태 확인", tags=["기타"])
async def health_check():
    """
    API 서버의 현재 동작 상태와 주요 백엔드 모듈의 가용성을 확인합니다.
    이 엔드포인트는 서비스 모니터링에 사용될 수 있습니다.
    """
    return {
        "status": "ok",
        "message": "DXF Analyzer API is running.",
        "timestamp": datetime.utcnow().isoformat(),
        "module_availability": {
            "dxf_analyzer": ANALYZER_AVAILABLE,
            "advanced_analyzer": ADVANCED_ANALYZER_AVAILABLE,
            "three_d_analyzer": THREE_D_ANALYZER_AVAILABLE
        },
        "active_jobs": len([job_id for job_id, job_data in analysis_jobs.items() if job_data.get('status') == 'processing']),
        "pending_jobs": len([job_id for job_id, job_data in analysis_jobs.items() if job_data.get('status') == 'pending'])
    }

# Docker 등에서 실행 시: uvicorn dxf_cloud_api:app --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    if JWT_SECRET_KEY == "your-very-secure-secret-key-for-production": # 기본 키와 같은지 확인
        logger.warning("기본 JWT_SECRET_KEY를 사용 중입니다. 프로덕션 환경에서는 반드시 안전한 키로 변경하세요!")

    uvicorn.run("dxf_cloud_api:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)