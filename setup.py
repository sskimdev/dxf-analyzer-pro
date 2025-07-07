#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF CAD 도면 분석기 - 설치 스크립트
"""

from setuptools import setup, find_packages
from pathlib import Path

# README 파일 읽기
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

setup(
    name="dxf-analyzer",
    version="1.0.0",
    author="AI Assistant",
    author_email="ai@example.com",
    description="DXF CAD 파일을 분석하여 마크다운 리포트를 생성하는 상용화 가능한 Python 애플리케이션",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/dxf-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: CAD",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "ezdxf>=1.1.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "web": ["streamlit>=1.28.0", "pandas>=1.5.0"],
        "dev": ["pytest>=7.0.0", "black>=22.0.0", "flake8>=5.0.0"],
        "build": ["pyinstaller>=5.0.0", "setuptools>=65.0.0", "wheel>=0.38.0"],
    },
    entry_points={
        "console_scripts": [
            "dxf-analyzer=dxf_analyzer:main",
            "dxf-analyze=dxf_analyzer:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords="dxf cad analysis autocad dwg engineering report markdown",
    project_urls={
        "Bug Reports": "https://github.com/example/dxf-analyzer/issues",
        "Source": "https://github.com/example/dxf-analyzer/",
        "Documentation": "https://github.com/example/dxf-analyzer/wiki",
    },
)
