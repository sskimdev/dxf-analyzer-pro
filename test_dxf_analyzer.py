#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 분석기 테스트 파일
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestDXFAnalyzer(unittest.TestCase):
    """DXF 분석기 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        try:
            from dxf_analyzer import DXFAnalyzer
            self.analyzer = DXFAnalyzer()
        except ImportError:
            self.skipTest("DXFAnalyzer 클래스를 import할 수 없습니다")

    def test_analyzer_initialization(self):
        """분석기 초기화 테스트"""
        self.assertIsNotNone(self.analyzer)
        self.assertEqual(len(self.analyzer.layers), 0)
        self.assertEqual(len(self.analyzer.dimensions), 0)
        self.assertEqual(len(self.analyzer.circles), 0)
        self.assertEqual(len(self.analyzer.texts), 0)

    def test_reset_analysis_data(self):
        """분석 데이터 초기화 테스트"""
        # 더미 데이터 추가
        self.analyzer.layers.append({'name': 'test'})
        self.analyzer.dimensions.append({'measurement': 100})

        # 초기화
        self.analyzer.reset_analysis_data()

        # 확인
        self.assertEqual(len(self.analyzer.layers), 0)
        self.assertEqual(len(self.analyzer.dimensions), 0)

    def test_markdown_generation(self):
        """마크다운 생성 테스트"""
        # 더미 데이터 설정
        self.analyzer.file_info = {
            'filename': 'test.dxf',
            'size': 1024,
            'modified_time': '2025-01-01 12:00:00'
        }
        self.analyzer.summary_info = {
            'total_entities': 100,
            'layer_count': 5,
            'dimension_count': 10,
            'circle_count': 20,
            'arc_count': 5,
            'text_count': 15,
            'entity_breakdown': {'LINE': 50, 'CIRCLE': 20}
        }

        # 마크다운 생성
        markdown_content = self.analyzer._build_markdown_content()

        # 확인
        self.assertIn('# CAD 도면 분석 리포트', markdown_content)
        self.assertIn('test.dxf', markdown_content)
        self.assertIn('전체 객체 수:', markdown_content)

class TestUtilityFunctions(unittest.TestCase):
    """유틸리티 함수 테스트"""

    def test_file_existence_check(self):
        """파일 존재 확인 테스트"""
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # 파일 존재 확인
            self.assertTrue(os.path.exists(tmp_path))

            # 파일 삭제 후 확인
            os.unlink(tmp_path)
            self.assertFalse(os.path.exists(tmp_path))
        finally:
            # 정리
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

if __name__ == '__main__':
    unittest.main()
