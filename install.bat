@echo off
echo DXF CAD 도면 분석기 설치 스크립트
echo ====================================

echo.
echo Python 설치 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo Python 3.8 이상을 설치하고 다시 실행해주세요.
    echo 다운로드: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python 설치 확인됨

echo.
echo pip 업그레이드 중...
python -m pip install --upgrade pip

echo.
echo 필수 라이브러리 설치 중...
python -m pip install -r requirements.txt

echo.
echo 설치 완료! 
echo.
echo 사용법:
echo   GUI 버전: python dxf_analyzer.py --gui
echo   웹 버전:  python dxf_analyzer.py --web
echo   CLI 버전: python dxf_analyzer.py --cli [파일명.dxf]
echo.

pause
