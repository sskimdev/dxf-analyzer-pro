#!/bin/bash

echo "DXF CAD 도면 분석기 설치 스크립트"
echo "===================================="

echo
echo "Python 설치 확인 중..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3이 설치되지 않았습니다."
    echo "Python 3.8 이상을 설치하고 다시 실행해주세요."

    # OS별 설치 가이드
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-tk"
        echo "CentOS/RHEL: sudo yum install python3 python3-pip tkinter"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS: brew install python-tk"
        echo "또는 https://www.python.org/downloads/ 에서 다운로드"
    fi

    exit 1
fi

echo "✓ Python3 설치 확인됨"

echo
echo "pip 업그레이드 중..."
python3 -m pip install --upgrade pip

echo
echo "필수 라이브러리 설치 중..."
python3 -m pip install -r requirements.txt

echo
echo "설치 완료!"
echo
echo "사용법:"
echo "  GUI 버전: python3 dxf_analyzer.py --gui"
echo "  웹 버전:  python3 dxf_analyzer.py --web"
echo "  CLI 버전: python3 dxf_analyzer.py --cli [파일명.dxf]"
echo

# 실행 권한 부여
chmod +x dxf_analyzer.py

echo "📝 참고: GUI 버전을 사용하려면 tkinter가 설치되어 있어야 합니다."
echo "문제가 있다면 OS별 tkinter 설치 가이드를 참조하세요."
