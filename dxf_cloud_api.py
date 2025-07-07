#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 분석기 클라우드 API 서버
Author: Cloud API Expert
Version: 2.0.0
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import tempfile
import os
import uuid
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import PyJWTError
import asyncio
import aiofiles
from pathlib import Path
import logging

# 로컬 모듈 임포트
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dxf_analyzer import DXFAnalyzer, ADVANCED_ANALYSIS_AVAILABLE
from dxf_comparison import DXFComparison
from dxf_auto_fix import DXFAutoFix

logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="DXF Analyzer Cloud API",
    description="Professional DXF CAD Drawing Analysis API",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보안 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
security = HTTPBearer()

# 임시 파일 저장 경로
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 분석 작업 저장소 (실제로는 Redis 등 사용)
analysis_jobs = {}


class AnalysisRequest(BaseModel):
    """분석 요청 모델"""
    include_advanced: bool = True
    include_3d: bool = True
    output_format: str = "json"  # json, markdown


class ComparisonRequest(BaseModel):
    """비교 요청 모델"""
    file1_id: str
    file2_id: str


class AnalysisResponse(BaseModel):
    """분석 응답 모델"""
    job_id: str
    status: str
    message: str
    result: Optional[Dict] = None
    
    
class AutoFixRequest(BaseModel):
    """자동 수정 요청 모델"""
    file_id: str
    fix_duplicates: bool = True
    fix_standards: bool = True
    fix_layers: bool = True
    fix_texts: bool = True
    create_backup: bool = True


def create_access_token(data: dict):
    """액세스 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """토큰 검증"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )


@app.get("/")
async def root():
    """API 루트"""
    return {
        "message": "DXF Analyzer Cloud API",
        "version": "2.0.0",
        "endpoints": {
            "analyze": "/api/analyze",
            "compare": "/api/compare",
            "autofix": "/api/autofix",
            "status": "/api/status/{job_id}",
            "download": "/api/download/{job_id}"
        }
    }


@app.post("/api/auth/token")
async def login(username: str, password: str):
    """인증 토큰 발급"""
    # 실제로는 데이터베이스에서 사용자 확인
    if username == "demo" and password == "demo123":
        access_token = create_access_token(data={"sub": username})
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_dxf(
    file: UploadFile = File(...),
    request: AnalysisRequest = AnalysisRequest(),
    current_user: dict = Depends(verify_token)
):
    """DXF 파일 분석"""
    if not file.filename or not file.filename.lower().endswith('.dxf'):
        raise HTTPException(
            status_code=400,
            detail="Only DXF files are supported"
        )
    
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    try:
        # 임시 파일 저장
        temp_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
        
        async with aiofiles.open(temp_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # 백그라운드 분석 시작
        asyncio.create_task(
            analyze_file_async(job_id, str(temp_path), request)
        )
        
        # 작업 상태 초기화
        analysis_jobs[job_id] = {
            'status': 'processing',
            'created_at': datetime.now(),
            'filename': file.filename,
            'user': current_user.get('sub')
        }
        
        return AnalysisResponse(
            job_id=job_id,
            status="processing",
            message="Analysis started"
        )
        
    except Exception as e:
        logger.error(f"분석 시작 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


async def analyze_file_async(job_id: str, file_path: str, request: AnalysisRequest):
    """비동기 파일 분석"""
    try:
        # DXF 분석 실행
        analyzer = DXFAnalyzer()
        success = analyzer.analyze_dxf_file(file_path)
        
        if not success:
            analysis_jobs[job_id]['status'] = 'failed'
            analysis_jobs[job_id]['error'] = 'Failed to analyze DXF file'
            return
        
        result = {
            'basic_analysis': analyzer.analysis_data,
            'summary': analyzer.summary_info
        }
        
        # 고급 분석
        if request.include_advanced and ADVANCED_ANALYSIS_AVAILABLE:
            from dxf_advanced_analyzer import DXFAdvancedAnalyzer
            advanced = DXFAdvancedAnalyzer()
            ai_context = advanced.generate_ai_context(analyzer.analysis_data)
            result['advanced_analysis'] = ai_context
        
        # 3D 분석
        if request.include_3d:
            from dxf_3d_analyzer import DXF3DAnalyzer
            analyzer_3d = DXF3DAnalyzer()
            # 실제 구현에서는 msp 전달 필요
            # result['3d_analysis'] = analyzer_3d.analyze_3d_entities(msp, analyzer.analysis_data)
        
        # 결과 저장
        if request.output_format == 'markdown':
            if request.include_advanced and hasattr(analyzer, 'generate_advanced_report'):
                report_path = file_path.replace('.dxf', '_report.md')
                analyzer.generate_advanced_report(report_path)
                result['report_path'] = report_path
        
        analysis_jobs[job_id]['status'] = 'completed'
        analysis_jobs[job_id]['result'] = result
        analysis_jobs[job_id]['completed_at'] = datetime.now()
        
    except Exception as e:
        logger.error(f"분석 중 오류: {e}")
        analysis_jobs[job_id]['status'] = 'failed'
        analysis_jobs[job_id]['error'] = str(e)
    
    finally:
        # 임시 파일 정리 (선택적)
        pass


@app.get("/api/status/{job_id}")
async def get_analysis_status(
    job_id: str,
    current_user: dict = Depends(verify_token)
):
    """분석 작업 상태 확인"""
    if job_id not in analysis_jobs:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job = analysis_jobs[job_id]
    
    # 사용자 확인
    if job.get('user') != current_user.get('sub'):
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )
    
    return {
        'job_id': job_id,
        'status': job['status'],
        'created_at': job['created_at'],
        'completed_at': job.get('completed_at'),
        'result': job.get('result') if job['status'] == 'completed' else None,
        'error': job.get('error')
    }


@app.post("/api/compare")
async def compare_dxf_files(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    current_user: dict = Depends(verify_token)
):
    """두 DXF 파일 비교"""
    job_id = str(uuid.uuid4())
    
    try:
        # 임시 파일 저장
        temp_path1 = UPLOAD_DIR / f"{job_id}_1_{file1.filename}"
        temp_path2 = UPLOAD_DIR / f"{job_id}_2_{file2.filename}"
        
        async with aiofiles.open(temp_path1, 'wb') as f:
            await f.write(await file1.read())
        
        async with aiofiles.open(temp_path2, 'wb') as f:
            await f.write(await file2.read())
        
        # 분석 실행
        analyzer1 = DXFAnalyzer()
        analyzer2 = DXFAnalyzer()
        
        success1 = analyzer1.analyze_dxf_file(str(temp_path1))
        success2 = analyzer2.analyze_dxf_file(str(temp_path2))
        
        if not success1 or not success2:
            raise ValueError("Failed to analyze one or both files")
        
        # 비교 실행
        comparator = DXFComparison()
        differences = comparator.compare_dxf_files(
            analyzer1.analysis_data,
            analyzer2.analysis_data
        )
        
        # 리포트 생성
        report = comparator.generate_comparison_report()
        
        return {
            'job_id': job_id,
            'status': 'completed',
            'differences': differences,
            'report': report
        }
        
    except Exception as e:
        logger.error(f"비교 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )


@app.post("/api/autofix")
async def auto_fix_dxf(
    request: AutoFixRequest,
    current_user: dict = Depends(verify_token)
):
    """DXF 파일 자동 수정"""
    job_id = str(uuid.uuid4())
    
    # 여기서는 간단한 구현만 제공
    # 실제로는 파일 업로드와 분석 결과를 기반으로 수정
    
    return {
        'job_id': job_id,
        'status': 'processing',
        'message': 'Auto-fix feature is under development'
    }


@app.get("/api/download/{job_id}")
async def download_result(
    job_id: str,
    format: str = "json",
    current_user: dict = Depends(verify_token)
):
    """분석 결과 다운로드"""
    if job_id not in analysis_jobs:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job = analysis_jobs[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail="Analysis not completed"
        )
    
    if format == "markdown" and 'report_path' in job.get('result', {}):
        return FileResponse(
            job['result']['report_path'],
            media_type='text/markdown',
            filename=f"analysis_report_{job_id}.md"
        )
    
    return JSONResponse(
        content=job['result'],
        media_type='application/json'
    )


@app.delete("/api/cleanup/{job_id}")
async def cleanup_job(
    job_id: str,
    current_user: dict = Depends(verify_token)
):
    """작업 정리"""
    if job_id in analysis_jobs:
        # 관련 파일 삭제
        for file in UPLOAD_DIR.glob(f"{job_id}_*"):
            file.unlink()
        
        del analysis_jobs[job_id]
        
        return {"message": "Job cleaned up successfully"}
    
    raise HTTPException(
        status_code=404,
        detail="Job not found"
    )


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len(analysis_jobs)
    }


# 서버 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "dxf_cloud_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 