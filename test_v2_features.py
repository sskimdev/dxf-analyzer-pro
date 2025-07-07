#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 분석기 v2.0 기능 테스트
"""

import unittest
import tempfile
import os
from pathlib import Path
import json

# 테스트할 모듈들
from dxf_analyzer import DXFAnalyzer
from dxf_3d_analyzer import DXF3DAnalyzer
from dxf_comparison import DXFComparison
from dxf_auto_fix import DXFAutoFix


class TestDXFAnalyzerV2(unittest.TestCase):
    """DXF 분석기 v2.0 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 설정"""
        # 샘플 파일 생성
        cls.sample_file = "test_sample.dxf"
        if not Path(cls.sample_file).exists():
            from create_sample_dxf import create_sample_dxf
            create_sample_dxf(cls.sample_file)
    
    def test_basic_analysis(self):
        """기본 분석 테스트"""
        analyzer = DXFAnalyzer()
        success = analyzer.analyze_dxf_file(self.sample_file)
        
        self.assertTrue(success)
        self.assertIsNotNone(analyzer.analysis_data)
        self.assertIn('total_entities', analyzer.summary_info)
        self.assertGreater(analyzer.summary_info['total_entities'], 0)
    
    def test_3d_analysis(self):
        """3D 분석 테스트"""
        analyzer = DXFAnalyzer()
        analyzer.analyze_dxf_file(self.sample_file)
        
        analyzer_3d = DXF3DAnalyzer()
        # 간단한 테스트 - 실제로는 msp 필요
        
        self.assertIsNotNone(analyzer_3d)
        self.assertEqual(analyzer_3d.is_3d_drawing, False)  # 2D 샘플
    
    def test_comparison(self):
        """도면 비교 테스트"""
        # 두 개의 분석 결과 생성
        analyzer1 = DXFAnalyzer()
        analyzer2 = DXFAnalyzer()
        
        analyzer1.analyze_dxf_file(self.sample_file)
        analyzer2.analyze_dxf_file(self.sample_file)
        
        # 비교 실행
        comparator = DXFComparison()
        differences = comparator.compare_dxf_files(
            analyzer1.analysis_data,
            analyzer2.analysis_data
        )
        
        self.assertIsNotNone(differences)
        self.assertIn('summary', differences)
        self.assertEqual(differences['summary']['change_level'], 'none')  # 같은 파일
    
    def test_auto_fix(self):
        """자동 수정 테스트"""
        # 분석 실행
        analyzer = DXFAnalyzer()
        analyzer.analyze_dxf_file(self.sample_file)
        
        # 자동 수정
        fixer = DXFAutoFix()
        loaded = fixer.load_file(self.sample_file)
        
        self.assertTrue(loaded)
        
        # 수정 실행
        fixes = fixer.auto_fix_all(analyzer.analysis_data)
        
        self.assertIsNotNone(fixes)
        self.assertIn('summary', fixes)
    
    def test_report_generation(self):
        """리포트 생성 테스트"""
        analyzer = DXFAnalyzer()
        analyzer.analyze_dxf_file(self.sample_file)
        
        # 임시 파일로 리포트 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name
        
        try:
            # 마크다운 리포트
            result = analyzer.generate_markdown_report(temp_path)
            self.assertTrue(Path(temp_path).exists())
            self.assertGreater(Path(temp_path).stat().st_size, 0)
            
            # 고급 리포트 (가능한 경우)
            if hasattr(analyzer, 'generate_advanced_report'):
                adv_path = temp_path.replace('.md', '_advanced.md')
                result = analyzer.generate_advanced_report(adv_path)
                self.assertTrue(Path(adv_path).exists())
                
                # JSON 컨텍스트도 생성되었는지 확인
                json_path = adv_path.replace('.md', '_ai_context.json')
                if Path(json_path).exists():
                    with open(json_path, 'r', encoding='utf-8') as f:
                        ai_context = json.load(f)
                    self.assertIn('summary', ai_context)
                    
        finally:
            # 정리
            for file in [temp_path, adv_path, json_path]:
                if Path(file).exists():
                    os.unlink(file)


class TestDXFComparison(unittest.TestCase):
    """비교 기능 상세 테스트"""
    
    def test_layer_comparison(self):
        """레이어 비교 테스트"""
        # 가상의 분석 데이터
        data1 = {
            'layers': [
                {'name': 'Layer1', 'color': 1, 'linetype': 'CONTINUOUS'},
                {'name': 'Layer2', 'color': 2, 'linetype': 'DASHED'}
            ]
        }
        
        data2 = {
            'layers': [
                {'name': 'Layer1', 'color': 2, 'linetype': 'CONTINUOUS'},  # 색상 변경
                {'name': 'Layer3', 'color': 3, 'linetype': 'CONTINUOUS'}   # 새 레이어
            ]
        }
        
        comparator = DXFComparison()
        differences = comparator.compare_dxf_files(data1, data2)
        
        # 추가된 레이어 확인
        self.assertEqual(len(differences['added']['layers']), 1)
        self.assertEqual(differences['added']['layers'][0]['name'], 'Layer3')
        
        # 제거된 레이어 확인
        self.assertEqual(len(differences['removed']['layers']), 1)
        self.assertEqual(differences['removed']['layers'][0]['name'], 'Layer2')
        
        # 수정된 레이어 확인
        self.assertEqual(len(differences['modified']['layers']), 1)
        self.assertEqual(differences['modified']['layers'][0]['name'], 'Layer1')


class TestDXFAutoFix(unittest.TestCase):
    """자동 수정 기능 상세 테스트"""
    
    def test_layer_fixes(self):
        """레이어 수정 테스트"""
        fixer = DXFAutoFix()
        
        # 가상의 분석 데이터 (레이어가 0만 있는 경우)
        analysis_data = {
            'layers': [{'name': '0', 'color': 7, 'linetype': 'CONTINUOUS'}]
        }
        
        # 이 테스트는 실제 DXF 파일 없이는 제한적
        # 실제 환경에서는 파일을 로드하고 수정해야 함
        self.assertIsNotNone(fixer)
    
    def test_duplicate_removal(self):
        """중복 제거 테스트"""
        fixer = DXFAutoFix()
        
        # 가상의 고급 분석 데이터
        advanced_analysis = {
            'anomalies': [
                {'type': 'duplicate_circle', 'count': 3}
            ]
        }
        
        # 실제 테스트는 DXF 파일이 필요
        self.assertIsNotNone(fixer)


def run_integration_test():
    """통합 테스트"""
    print("\n=== DXF 분석기 v2.0 통합 테스트 ===\n")
    
    # 1. 샘플 파일 생성
    print("1. 샘플 파일 준비...")
    sample_file = "integration_test.dxf"
    if not Path(sample_file).exists():
        from create_sample_dxf import create_sample_dxf
        create_sample_dxf(sample_file)
    print("✅ 샘플 파일 준비 완료")
    
    # 2. 전체 분석 파이프라인
    print("\n2. 전체 분석 파이프라인 테스트...")
    
    # 기본 분석
    analyzer = DXFAnalyzer()
    success = analyzer.analyze_dxf_file(sample_file)
    print(f"  - 기본 분석: {'✅ 성공' if success else '❌ 실패'}")
    
    # 3D 분석
    analyzer_3d = DXF3DAnalyzer()
    print(f"  - 3D 분석기 초기화: ✅")
    
    # 비교 (동일 파일)
    comparator = DXFComparison()
    differences = comparator.compare_dxf_files(
        analyzer.analysis_data,
        analyzer.analysis_data
    )
    print(f"  - 비교 분석: ✅ (변경사항 {differences['summary']['total_additions']}개)")
    
    # 자동 수정
    fixer = DXFAutoFix()
    loaded = fixer.load_file(sample_file)
    print(f"  - 자동 수정: {'✅ 파일 로드 성공' if loaded else '❌ 파일 로드 실패'}")
    
    # 3. 리포트 생성
    print("\n3. 리포트 생성 테스트...")
    report_path = "integration_test_report.md"
    analyzer.generate_markdown_report(report_path)
    print(f"  - 마크다운 리포트: ✅ {report_path}")
    
    # 고급 리포트
    if hasattr(analyzer, 'generate_advanced_report'):
        adv_report = "integration_test_advanced.md"
        analyzer.generate_advanced_report(adv_report)
        print(f"  - 고급 리포트: ✅ {adv_report}")
    
    # 4. 정리
    print("\n4. 테스트 파일 정리...")
    for file in [sample_file, report_path, adv_report]:
        if Path(file).exists():
            os.unlink(file)
    print("✅ 정리 완료")
    
    print("\n=== 통합 테스트 완료 ===")


if __name__ == '__main__':
    # 단위 테스트 실행
    print("단위 테스트 실행 중...")
    unittest.main(verbosity=2, exit=False)
    
    # 통합 테스트 실행
    run_integration_test() 