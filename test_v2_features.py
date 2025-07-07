#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 분석기 v2.0 신규 기능 테스트 파일
"""

import unittest
import tempfile
import os
import sys
import json
import asyncio # For AI integration tests
from unittest.mock import patch, MagicMock, AsyncMock # Mock 추가

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- 테스트 대상 모듈 임포트 ---
ANALYZER_AVAILABLE = False
DXFAnalyzer = None
try:
    from dxf_analyzer import DXFAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    pass

THREE_D_ANALYZER_AVAILABLE = False
DXF3DAnalyzer = None
try:
    from dxf_3d_analyzer import DXF3DAnalyzer
    THREE_D_ANALYZER_AVAILABLE = True
except ImportError:
    pass

COMPARISON_AVAILABLE = False
DXFComparison = None
try:
    from dxf_comparison import DXFComparison
    COMPARISON_AVAILABLE = True
except ImportError:
    pass

AUTO_FIX_AVAILABLE = False
DXFAutoFix = None
try:
    from dxf_auto_fix import DXFAutoFix
    AUTO_FIX_AVAILABLE = True
except ImportError:
    pass

AI_INTEGRATION_AVAILABLE = False
DXFAIIntegration = None
CLAUDE_AVAILABLE = False
GEMINI_AVAILABLE = False

try:
    from dxf_ai_integration import DXFAIIntegration, CLAUDE_AVAILABLE, GEMINI_AVAILABLE
    AI_INTEGRATION_AVAILABLE = True
except ImportError:
    pass


# --- 테스트용 DXF 생성 헬퍼 ---
def create_test_dxf_file(entities_callback, filename_suffix="test.dxf"):
    import ezdxf
    doc = ezdxf.new()
    msp = doc.modelspace()
    if entities_callback:
        entities_callback(msp)
    
    fd, filepath = tempfile.mkstemp(suffix=f"_{filename_suffix}") # text=True 제거
    os.close(fd)
    doc.saveas(filepath)
    return filepath


# --- DXF3DAnalyzer 테스트 ---
@unittest.skipIf(not THREE_D_ANALYZER_AVAILABLE or not ANALYZER_AVAILABLE, "DXF3DAnalyzer or DXFAnalyzer not available")
class TestDXF3DAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer_3d = DXF3DAnalyzer()

    def test_analyze_simple_3dface(self):
        def add_3dface_entities(msp):
            msp.add_3dface([(0,0,0), (1,0,5), (1,1,5), (0,1,0)])

        dxf_file = create_test_dxf_file(add_3dface_entities, "3dface.dxf")
        
        import ezdxf
        doc = ezdxf.readfile(dxf_file)
        msp = doc.modelspace()
        
        base_analyzer = DXFAnalyzer()
        base_analyzer.analyze_dxf_file(dxf_file)
        self.assertIsNotNone(base_analyzer.analysis_data)

        # 각 테스트마다 새로운 3D 분석기 인스턴스 사용 권장 또는 self.analyzer_3d.reset_data() 같은 메소드 필요
        current_3d_analyzer = DXF3DAnalyzer()
        result = current_3d_analyzer.analyze_3d_entities(msp, base_analyzer.analysis_data)
        
        self.assertTrue(result.get('is_3d'))
        self.assertEqual(result.get('z_range', {}).get('min'), 0)
        self.assertEqual(result.get('z_range', {}).get('max'), 5)
        self.assertIn('3DFACE', result.get('3d_entity_breakdown', {}))
        
        report = current_3d_analyzer.generate_3d_report(result)
        self.assertIn("3D 도면 확인됨", report)
        self.assertIn("Z축 범위: 0.000 ~ 5.000", report)

        os.unlink(dxf_file)

    def test_analyze_mesh_with_bounding_box(self):
        def add_mesh_entities(msp):
            vertices = [(0,0,0), (1,0,0), (1,1,1), (0,1,1), (0.5, 0.5, 2)]
            faces = [[0,1,2,3], [0,1,4], [1,2,4], [2,3,4], [3,0,4]]
            msp.add_mesh(vertices=vertices, faces=faces)

        dxf_file = create_test_dxf_file(add_mesh_entities, "mesh.dxf")
        
        import ezdxf
        doc = ezdxf.readfile(dxf_file)
        msp = doc.modelspace()
        base_analyzer = DXFAnalyzer()
        base_analyzer.analyze_dxf_file(dxf_file)
        self.assertIsNotNone(base_analyzer.analysis_data)

        current_3d_analyzer = DXF3DAnalyzer()
        result = current_3d_analyzer.analyze_3d_entities(msp, base_analyzer.analysis_data)
        
        self.assertTrue(result.get('is_3d'))
        self.assertEqual(result.get('z_range', {}).get('min'), 0)
        self.assertEqual(result.get('z_range', {}).get('max'), 2)
        
        self.assertTrue(len(current_3d_analyzer.meshes) > 0)
        mesh_info = current_3d_analyzer.meshes[0]
        self.assertIsNotNone(mesh_info.get('bounding_box'))
        self.assertEqual(mesh_info['bounding_box']['min'], (0.0, 0.0, 0.0))
        self.assertEqual(mesh_info['bounding_box']['max'], (1.0, 1.0, 2.0))
        
        report = current_3d_analyzer.generate_3d_report(result)
        self.assertIn("예시 메시 경계 상자 (Min): 0.00, 0.00, 0.00", report)
        self.assertIn("예시 메시 경계 상자 (Max): 1.00, 1.00, 2.00", report)

        os.unlink(dxf_file)


# --- DXFComparison 테스트 ---
@unittest.skipIf(not COMPARISON_AVAILABLE or not ANALYZER_AVAILABLE, "DXFComparison or DXFAnalyzer not available")
class TestDXFComparison(unittest.TestCase):
    def setUp(self):
        self.comparator = DXFComparison()
        self.analyzer1 = DXFAnalyzer()
        self.analyzer2 = DXFAnalyzer()

    def test_compare_simple_changes(self):
        # 이 테스트는 DXFComparison 모듈의 실제 구현에 따라 상세한 assert 내용이 달라져야 함
        def dxf1_entities(msp):
            msp.add_line((0,0), (1,1), dxfattribs={'layer': 'L1'})
            msp.add_circle((5,5), 2, dxfattribs={'layer': 'L1'})

        def dxf2_entities(msp):
            msp.add_line((0,0), (1,1), dxfattribs={'layer': 'L1'})
            msp.add_line((2,2), (3,3), dxfattribs={'layer': 'L2'})
            msp.add_circle((5,5), 2.5, dxfattribs={'layer': 'L1'}) # 반지름 변경

        dxf_file1 = create_test_dxf_file(dxf1_entities, "comp1.dxf")
        dxf_file2 = create_test_dxf_file(dxf2_entities, "comp2.dxf")

        self.analyzer1.analyze_dxf_file(dxf_file1)
        self.analyzer2.analyze_dxf_file(dxf_file2)
        self.assertIsNotNone(self.analyzer1.analysis_data)
        self.assertIsNotNone(self.analyzer2.analysis_data)

        diff = self.comparator.compare_dxf_files(self.analyzer1.analysis_data, self.analyzer2.analysis_data)
        
        # DXFComparison의 반환값 구조를 알아야 정확한 테스트 가능
        # 예시: summary의 추가/수정/삭제 카운트 확인
        self.assertIn('summary', diff)
        # self.assertEqual(diff['summary'].get('total_additions',0) > 0, True) # LINE 및 Layer L2 추가
        # self.assertEqual(diff['summary'].get('total_modifications',0) > 0, True) # CIRCLE 수정
        
        report = self.comparator.generate_comparison_report() # diff 객체를 인자로 받을 수도 있음
        self.assertIn("레이어 'L2'가 추가되었습니다.", report)
        self.assertIn("CIRCLE", report) # 변경된 CIRCLE 언급

        os.unlink(dxf_file1)
        os.unlink(dxf_file2)

# --- DXFAutoFix 테스트 ---
@unittest.skipIf(not AUTO_FIX_AVAILABLE or not ANALYZER_AVAILABLE, "DXFAutoFix or DXFAnalyzer not available")
class TestDXFAutoFix(unittest.TestCase):
    def setUp(self):
        self.fixer = DXFAutoFix()
        self.analyzer = DXFAnalyzer()

    def test_conceptual_fix_duplicate_lines(self):
        def duplicate_lines_entities(msp):
            msp.add_line((0,0), (1,1), dxfattribs={'layer': 'L_DUPE'})
            msp.add_line((0,0), (1,1), dxfattribs={'layer': 'L_DUPE'})
            msp.add_line((10,10), (20,20), dxfattribs={'layer': 'L_DUPE'})

        dxf_file = create_test_dxf_file(duplicate_lines_entities, "dupe.dxf")
        
        self.analyzer.analyze_dxf_file(dxf_file)
        self.assertIsNotNone(self.analyzer.analysis_data)

        loaded = self.fixer.load_file(dxf_file)
        self.assertTrue(loaded)
        
        fixes_summary = self.fixer.auto_fix_all(self.analyzer.analysis_data, None)
        self.assertIn('duplicate_entities_removed', fixes_summary.get('fixes_applied', []))

        # 실제 파일 저장 및 검증은 추가 로직 필요
        # fixed_path = self.fixer.save_fixed_file(dxf_file.replace(".dxf", "_fixed.dxf"))
        # ... (fixed_path 분석 후 검증) ...
        # if os.path.exists(fixed_path): os.unlink(fixed_path)
        os.unlink(dxf_file)


# --- DXFAIIntegration 테스트 (Mock 사용) ---
# DXFAIIntegration 테스트는 비동기이므로 unittest.IsolatedAsyncioTestCase 사용
@unittest.skipIf(not AI_INTEGRATION_AVAILABLE, "DXFAIIntegration or dependent AI libraries not available")
class TestDXFAIIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self): # setUp -> asyncSetUp
        self.ai_integration = DXFAIIntegration()
        self.ai_integration.openai_api_key = "FAKE_KEY_FOR_TESTING_OPENAI"
        self.ai_integration.claude_api_key = "FAKE_KEY_FOR_TESTING_CLAUDE"
        self.ai_integration.gemini_api_key = "FAKE_KEY_FOR_TESTING_GEMINI"

        # 실제 클라이언트 대신 Mock 객체 사용
        if CLAUDE_AVAILABLE:
            self.ai_integration.claude_client = MagicMock()
            # messages.create가 비동기 함수처럼 보이게 AsyncMock 사용 또는 to_thread를 고려한 mock
            self.ai_integration.claude_client.messages.create = AsyncMock()
        else:
            self.ai_integration.claude_client = None

        if GEMINI_AVAILABLE:
            self.ai_integration.gemini_model = MagicMock()
            self.ai_integration.gemini_model.generate_content = AsyncMock() # generate_content도 비동기 mock
        else:
            self.ai_integration.gemini_model = None
    
    # OpenAI v0.x.x 용 patch
    @patch('openai.ChatCompletion.create', new_callable=AsyncMock)
    async def test_analyze_with_openai_mocked(self, mock_openai_call):
        if not self.ai_integration.is_api_key_configured('openai'):
            self.skipTest("OpenAI API key not configured for DXFAIIntegration")

        mock_response_content = "OpenAI mock analysis result."
        mock_openai_call.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=mock_response_content))]
        )
        
        sample_data = {'file_info': {}, 'summary_info': {'total_entities': 10}, 'layers':[], 'entity_breakdown':{}}
        # _call_openai_async 내부에서 asyncio.to_thread를 사용하므로, ChatCompletion.create를 mock
        # 이 테스트는 DXFAIIntegration._call_openai_async가 to_thread를 사용하지 않는다고 가정하고 직접 mock
        # 만약 to_thread를 유지한다면, patch 대상이 달라지거나, to_thread 자체를 mock해야 할 수 있음
        # 여기서는 _call_openai_async가 직접 openai.ChatCompletion.create를 호출한다고 가정하고 patch
        
        # DXFAIIntegration._call_openai_async를 직접 mock 하는 방법도 있음
        with patch.object(self.ai_integration, '_call_openai_async', new_callable=AsyncMock) as mock_internal_call:
            mock_internal_call.return_value = mock_response_content # _call_openai_async가 문자열을 반환한다고 가정
            result = await self.ai_integration.analyze_with_openai(sample_data, 'analysis')

            self.assertNotIn('error', result, f"OpenAI 분석 결과에 오류 포함: {result.get('error')}")
            self.assertEqual(result.get('analysis'), mock_response_content)
            mock_internal_call.assert_called_once()


    async def test_analyze_with_claude_mocked(self):
        if not self.ai_integration.is_api_key_configured('claude'):
            self.skipTest("Claude API not configured or client not available for DXFAIIntegration")

        mock_response_content = "Claude mock analysis result."
        if self.ai_integration.claude_client: # claude_client가 None이 아닐 때만 (즉, 라이브러리 존재 시)
             self.ai_integration.claude_client.messages.create.return_value = MagicMock(content=[MagicMock(text=mock_response_content)])

        sample_data = {'file_info': {}, 'summary_info': {'total_entities': 20}, 'layers':[], 'entity_breakdown':{}}
        result = await self.ai_integration.analyze_with_claude(sample_data, 'analysis')

        self.assertNotIn('error', result, f"Claude 분석 결과에 오류 포함: {result.get('error')}")
        self.assertEqual(result.get('analysis'), mock_response_content)
        if self.ai_integration.claude_client:
            self.ai_integration.claude_client.messages.create.assert_called_once()

    async def test_analyze_with_gemini_mocked(self):
        if not self.ai_integration.is_api_key_configured('gemini'):
            self.skipTest("Gemini API not configured or model not available for DXFAIIntegration")

        mock_response_content = "Gemini mock analysis result."
        if self.ai_integration.gemini_model: # gemini_model이 None이 아닐 때만
            self.ai_integration.gemini_model.generate_content.return_value = MagicMock(text=mock_response_content)

        sample_data = {'file_info': {}, 'summary_info': {'total_entities': 30}, 'layers':[], 'entity_breakdown':{}}
        result = await self.ai_integration.analyze_with_gemini(sample_data, 'analysis')

        self.assertNotIn('error', result, f"Gemini 분석 결과에 오류 포함: {result.get('error')}")
        self.assertEqual(result.get('analysis'), mock_response_content)
        if self.ai_integration.gemini_model:
            self.ai_integration.gemini_model.generate_content.assert_called_once()

if __name__ == '__main__':
    if sys.version_info >= (3, 8) and sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # unittest.main()은 기본적으로 IsolatedAsyncioTestCase를 잘 처리함
    unittest.main(verbosity=2)