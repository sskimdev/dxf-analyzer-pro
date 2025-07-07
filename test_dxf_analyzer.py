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
        self.assertIn('LINE | 50 |', markdown_content) # 엔티티 분석 내용 확인

    def _create_dummy_dxf_file(self, content: str) -> str:
        """테스트용 임시 DXF 파일을 생성하고 경로를 반환합니다."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf", mode="w") as tmp:
            tmp.write(content)
            return tmp.name

    def test_analyze_empty_dxf(self):
        """빈 DXF 파일 분석 테스트"""
        empty_dxf_content = """0
SECTION
2
HEADER
9
$ACADVER
1
AC1009
0
ENDSEC
0
SECTION
2
TABLES
0
ENDSEC
0
SECTION
2
BLOCKS
0
ENDSEC
0
SECTION
2
ENTITIES
0
ENDSEC
0
EOF
"""
        temp_dxf_file = self._create_dummy_dxf_file(empty_dxf_content)
        try:
            success = self.analyzer.analyze_dxf_file(temp_dxf_file)
            self.assertTrue(success, "빈 DXF 파일 분석에 성공해야 합니다.")
            self.assertEqual(self.analyzer.summary_info.get('total_entities'), 0)
            self.assertEqual(len(self.analyzer.layers), 0) # 기본 레이어 '0'은 ezdxf가 자동으로 만들지 않음 (파일에 명시 없으면)
                                                        # 하지만 ezdxf.new()로 만들면 '0' 레이어가 기본 생성됨. readfile은 다를 수 있음.
                                                        # 여기서는 파일 내용 기반이므로 0이 맞을 수 있음.
                                                        # 만약 ezdxf가 '0' 레이어를 항상 추가한다면 1로 변경 필요.
                                                        # 테스트 실행 후 확인 필요.
            self.assertEqual(self.analyzer.summary_info.get('layer_count'), 0) # 위와 동일
        finally:
            os.unlink(temp_dxf_file)

    def test_analyze_dxf_with_lines(self):
        """LINE 엔티티 포함 DXF 파일 분석 테스트"""
        lines_dxf_content = """0
SECTION
2
ENTITIES
0
LINE
8
Layer1
10
0.0
20
0.0
30
0.0
11
10.0
21
10.0
31
0.0
0
LINE
8
Layer1
10
5.0
20
5.0
30
0.0
11
15.0
21
15.0
31
0.0
0
ENDSEC
0
EOF
"""
        # 참고: 위 DXF는 최소한의 필수 헤더/테이블 섹션이 없어 ezdxf에서 오류 발생 가능.
        # ezdxf가 정상적으로 읽으려면 최소한의 구조가 필요.
        # create_sample_dxf.py를 참고하여 유효한 최소 DXF 생성 권장.
        # 여기서는 ezdxf.new()를 사용하여 프로그래밍 방식으로 생성하는 것을 가정.

        # 더 나은 접근: ezdxf를 사용하여 테스트용 DXF 객체 직접 생성
        import ezdxf
        doc = ezdxf.new()
        msp = doc.modelspace()
        msp.add_line((0, 0), (10, 10), dxfattribs={'layer': 'Layer1'})
        msp.add_line((5, 5), (15, 15), dxfattribs={'layer': 'Layer1'})

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            doc.saveas(tmp.name)
            temp_dxf_file = tmp.name

        try:
            success = self.analyzer.analyze_dxf_file(temp_dxf_file)
            self.assertTrue(success)
            self.assertEqual(self.analyzer.summary_info.get('total_entities'), 2)
            self.assertEqual(self.analyzer.summary_info.get('line_count'), 2)
            self.assertEqual(self.analyzer.entity_breakdown.get('LINE'), 2)
            self.assertEqual(len(self.analyzer.lines), 2)
            # Layer1과 기본 '0' 레이어가 있을 수 있음
            self.assertTrue(any(layer['name'] == 'Layer1' for layer in self.analyzer.layers))
        finally:
            os.unlink(temp_dxf_file)

    def test_analyze_dxf_with_circles(self):
        """CIRCLE 엔티티 포함 DXF 파일 분석 테스트"""
        import ezdxf
        doc = ezdxf.new()
        msp = doc.modelspace()
        msp.add_circle((5, 5), radius=2.5, dxfattribs={'layer': 'CirclesLayer'})

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            doc.saveas(tmp.name)
            temp_dxf_file = tmp.name

        try:
            success = self.analyzer.analyze_dxf_file(temp_dxf_file)
            self.assertTrue(success)
            self.assertEqual(self.analyzer.summary_info.get('total_entities'), 1)
            self.assertEqual(self.analyzer.summary_info.get('circle_count'), 1)
            self.assertEqual(self.analyzer.entity_breakdown.get('CIRCLE'), 1)
            self.assertEqual(len(self.analyzer.circles), 1)
            self.assertEqual(self.analyzer.circles[0]['radius'], 2.5)
            self.assertTrue(any(layer['name'] == 'CirclesLayer' for layer in self.analyzer.layers))
        finally:
            os.unlink(temp_dxf_file)

    def test_layer_information(self):
        """레이어 정보 추출 테스트"""
        import ezdxf
        doc = ezdxf.new()
        doc.layers.new('MyLayer1', dxfattribs={'color': 1, 'linetype': 'DASHED'})
        doc.layers.new('MyLayer2', dxfattribs={'color': 2, 'linetype': 'CENTER'})
        msp = doc.modelspace()
        msp.add_line((0,0), (1,1), dxfattribs={'layer': 'MyLayer1'})

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            doc.saveas(tmp.name)
            temp_dxf_file = tmp.name

        try:
            success = self.analyzer.analyze_dxf_file(temp_dxf_file)
            self.assertTrue(success)
            # ezdxf는 기본 '0' 레이어를 포함하여 레이어 목록을 반환할 수 있음
            # 또한 사용된 레이어 외에 정의된 모든 레이어를 반환할 수 있음
            self.assertGreaterEqual(len(self.analyzer.layers), 2) # '0', 'MyLayer1', 'MyLayer2'

            layer_names = [l['name'] for l in self.analyzer.layers]
            self.assertIn('MyLayer1', layer_names)
            self.assertIn('MyLayer2', layer_names)

            my_layer1_info = next(l for l in self.analyzer.layers if l['name'] == 'MyLayer1')
            self.assertEqual(my_layer1_info['color'], 1)
            self.assertEqual(my_layer1_info['linetype'], 'DASHED')
        finally:
            os.unlink(temp_dxf_file)

    def test_drawing_bounds_calculation(self):
        """도면 경계 및 크기 계산 테스트"""
        import ezdxf
        doc = ezdxf.new()
        msp = doc.modelspace()
        msp.add_line((-5, -10), (15, 20)) # X 범위: -5 ~ 15 (20), Y 범위: -10 ~ 20 (30)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            doc.saveas(tmp.name)
            temp_dxf_file = tmp.name

        try:
            success = self.analyzer.analyze_dxf_file(temp_dxf_file)
            self.assertTrue(success)

            drawing_size_info = self.analyzer.summary_info.get('drawing_size')
            self.assertIsNotNone(drawing_size_info)

            bounds = drawing_size_info['bounds']
            self.assertAlmostEqual(bounds['min_x'], -5)
            self.assertAlmostEqual(bounds['min_y'], -10)
            self.assertAlmostEqual(bounds['max_x'], 15)
            self.assertAlmostEqual(bounds['max_y'], 20)

            self.assertAlmostEqual(drawing_size_info['width'], 20)
            self.assertAlmostEqual(drawing_size_info['height'], 30)
            self.assertAlmostEqual(drawing_size_info['area'], 600)

        finally:
            os.unlink(temp_dxf_file)


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
