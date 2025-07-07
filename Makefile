# DXF 분석기 Makefile

.PHONY: install install-dev test lint format build clean help

# 기본 설치
install:
	pip install -r requirements.txt

# 개발 환경 설치
install-dev:
	pip install -r requirements.txt
	pip install -e .[dev]

# 웹 버전 의존성 설치
install-web:
	pip install -e .[web]

# 테스트 실행
test:
	pytest tests/ -v

# 코드 린팅
lint:
	flake8 *.py
	black --check *.py

# 코드 포맷팅
format:
	black *.py

# 패키지 빌드
build:
	python setup.py sdist bdist_wheel

# 실행 파일 생성 (PyInstaller)
build-exe:
	pyinstaller --onefile --windowed --name "DXF분석기" dxf_analyzer.py

# GUI 버전 실행
run-gui:
	python dxf_analyzer.py --gui

# 웹 버전 실행  
run-web:
	python dxf_analyzer.py --web

# 정리
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf __pycache__/ .pytest_cache/
	find . -name "*.pyc" -delete

# 도움말
help:
	@echo "DXF 분석기 Makefile"
	@echo "사용 가능한 명령어:"
	@echo "  install     - 기본 설치"
	@echo "  install-dev - 개발 환경 설치"
	@echo "  install-web - 웹 버전 의존성 설치"
	@echo "  test        - 테스트 실행"
	@echo "  lint        - 코드 린팅"
	@echo "  format      - 코드 포맷팅"
	@echo "  build       - 패키지 빌드"
	@echo "  build-exe   - 실행파일 생성"
	@echo "  run-gui     - GUI 버전 실행"
	@echo "  run-web     - 웹 버전 실행"
	@echo "  clean       - 빌드 파일 정리"
	@echo "  help        - 이 도움말 표시"
