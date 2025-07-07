#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 분석기 v2.0 - 통합 사용 예시
모든 새로운 기능을 보여주는 예시 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 필요한 모듈들 임포트
from dxf_analyzer import DXFAnalyzer
from dxf_advanced_analyzer import DXFAdvancedAnalyzer
from dxf_3d_analyzer import DXF3DAnalyzer
from dxf_comparison import DXFComparison
from dxf_auto_fix import DXFAutoFix
from dxf_ai_integration import DXFAIIntegration


def example_basic_analysis():
    """기본 분석 예시"""
    print("\n=== 1. 기본 분석 ===")
    
    analyzer = DXFAnalyzer()
    success = analyzer.analyze_dxf_file("sample.dxf")
    
    if success:
        print(f"✅ 분석 완료!")
        print(f"- 전체 엔티티: {analyzer.summary_info['total_entities']:,}개")
        print(f"- 레이어 수: {analyzer.summary_info['layer_count']}개")
        if hasattr(analyzer, 'drawing_size'):
            print(f"- 도면 크기: {analyzer.drawing_size['width']:.2f} x {analyzer.drawing_size['height']:.2f}")
        else:
            print(f"- 도면 경계: 분석 중...")
        
        # 리포트 생성
        analyzer.generate_advanced_report("analysis_report.md")
        print("📄 리포트 생성: analysis_report.md")
    else:
        print("❌ 분석 실패")


def example_3d_analysis():
    """3D 분석 예시"""
    print("\n=== 2. 3D 분석 ===")
    
    # 먼저 기본 분석 실행
    analyzer = DXFAnalyzer()
    analyzer.analyze_dxf_file("sample_3d.dxf")
    
    # 3D 분석
    analyzer_3d = DXF3DAnalyzer()
    # 실제로는 msp 객체 전달 필요
    # result_3d = analyzer_3d.analyze_3d_entities(msp, analyzer.analysis_data)
    
    print("🧊 3D 분석 기능:")
    print("- 3D 솔리드 분석")
    print("- 서피스 및 메시 분석")
    print("- Z축 범위 및 부피 추정")
    print("- 공간 복잡도 평가")


def example_comparison():
    """도면 비교 예시"""
    print("\n=== 3. 도면 비교 ===")
    
    # 두 파일 분석
    analyzer1 = DXFAnalyzer()
    analyzer2 = DXFAnalyzer()
    
    analyzer1.analyze_dxf_file("drawing_v1.dxf")
    analyzer2.analyze_dxf_file("drawing_v2.dxf")
    
    # 비교 실행
    comparator = DXFComparison()
    differences = comparator.compare_dxf_files(
        analyzer1.analysis_data,
        analyzer2.analysis_data
    )
    
    print("📊 비교 결과:")
    summary = differences.get('summary', {})
    print(f"- 변경 수준: {summary.get('change_level', 'unknown').upper()}")
    print(f"- 추가된 항목: {summary.get('total_additions', 0)}개")
    print(f"- 제거된 항목: {summary.get('total_removals', 0)}개")
    print(f"- 수정된 항목: {summary.get('total_modifications', 0)}개")
    
    # 비교 리포트 생성
    report = comparator.generate_comparison_report()
    with open("comparison_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("📄 비교 리포트 생성: comparison_report.md")


def example_auto_fix():
    """자동 수정 예시"""
    print("\n=== 4. 자동 수정 ===")
    
    # 분석 실행
    analyzer = DXFAnalyzer()
    analyzer.analyze_dxf_file("problematic_drawing.dxf")
    
    # 자동 수정
    fixer = DXFAutoFix()
    if fixer.load_file("problematic_drawing.dxf"):
        # 백업 생성
        backup_path = fixer.create_backup("problematic_drawing.dxf")
        print(f"💾 백업 생성: {backup_path}")
        
        # 자동 수정 실행
        fixes = fixer.auto_fix_all(analyzer.analysis_data)
        
        # 수정된 파일 저장
        fixed_path = fixer.save_fixed_file("problematic_drawing_fixed.dxf")
        print(f"✅ 수정 완료: {fixed_path}")
        
        # 수정 내역
        print("\n🔧 수정 내역:")
        for fix_type in fixes.get('fixes_applied', []):
            print(f"  - {fix_type}")


async def example_ai_analysis():
    """AI 분석 예시"""
    print("\n=== 5. AI 분석 ===")
    
    # 분석 실행
    analyzer = DXFAnalyzer()
    analyzer.analyze_dxf_file("sample.dxf")
    
    # AI 통합
    ai_integration = DXFAIIntegration()
    
    # API 키 확인
    if not ai_integration.openai_api_key and not ai_integration.claude_client:
        print("⚠️  AI API 키가 설정되지 않았습니다.")
        print("환경 변수에 OPENAI_API_KEY 또는 ANTHROPIC_API_KEY를 설정해주세요.")
        return
    
    # AI 분석 실행
    print("🤖 AI 분석 중...")
    result = await ai_integration.analyze_with_both(
        analyzer.analysis_data,
        'analysis'
    )
    
    # 결과 표시
    if 'error' not in result:
        print(f"✅ AI 분석 완료!")
        print(f"- 사용 모델: {', '.join(result.get('models_used', []))}")
        
        # AI 리포트 생성
        report = ai_integration.generate_ai_report(result)
        with open("ai_analysis_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("📄 AI 리포트 생성: ai_analysis_report.md")
        
        # 대화형 질문
        question = "이 도면의 품질을 개선하려면 어떻게 해야 할까요?"
        answer = await ai_integration.interactive_chat(question, analyzer.analysis_data)
        print(f"\n💬 Q: {question}")
        print(f"💡 A: {answer[:200]}...")
    else:
        print(f"❌ AI 분석 실패: {result['error']}")


def example_api_usage():
    """API 서버 사용 예시"""
    print("\n=== 6. API 서버 ===")
    
    print("🌐 API 서버 기능:")
    print("- RESTful API 엔드포인트")
    print("- JWT 인증")
    print("- 비동기 파일 분석")
    print("- 백그라운드 작업 처리")
    
    print("\n시작 명령어:")
    print("$ python dxf_cloud_api.py")
    print("\nAPI 문서:")
    print("http://localhost:8000/docs")
    
    print("\n예시 요청:")
    print("""
curl -X POST "http://localhost:8000/api/analyze" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -F "file=@sample.dxf" \\
  -F "include_advanced=true" \\
  -F "include_3d=true"
""")


def main():
    """메인 함수"""
    print("=" * 60)
    print("DXF 분석기 v2.0 - 통합 사용 예시")
    print("=" * 60)
    
    # 샘플 파일 생성 (없는 경우)
    if not Path("sample.dxf").exists():
        print("⚠️  샘플 파일이 없습니다. create_sample_dxf.py를 먼저 실행하세요.")
        return
    
    try:
        # 1. 기본 분석
        example_basic_analysis()
        
        # 2. 3D 분석
        example_3d_analysis()
        
        # 3. 도면 비교 (파일이 있는 경우)
        if Path("drawing_v1.dxf").exists() and Path("drawing_v2.dxf").exists():
            example_comparison()
        else:
            print("\n⏭️  도면 비교 예시 건너뜀 (비교할 파일 없음)")
        
        # 4. 자동 수정 (문제 파일이 있는 경우)
        if Path("problematic_drawing.dxf").exists():
            example_auto_fix()
        else:
            print("\n⏭️  자동 수정 예시 건너뜀 (수정할 파일 없음)")
        
        # 5. AI 분석 (비동기)
        print("\n🤖 AI 분석을 실행하려면 'y'를 입력하세요 (API 키 필요): ", end="")
        if input().lower() == 'y':
            asyncio.run(example_ai_analysis())
        
        # 6. API 사용법
        example_api_usage()
        
        print("\n" + "=" * 60)
        print("✅ 모든 예시 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 