#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNC 특화 기능 테스트 스크립트
"""

import asyncio
from dxf_analyzer import DXFAnalyzer
from dxf_cnc_analyzer import DXFCNCAnalyzer
from dxf_cost_estimator import DXFCostEstimator
from dxf_ai_integration import DXFAIIntegration

def test_cnc_analysis():
    """CNC 가공성 분석 테스트"""
    print("=" * 50)
    print("🏭 CNC 가공성 분석 테스트")
    print("=" * 50)
    
    # CNC 분석기 초기화
    cnc_analyzer = DXFCNCAnalyzer()
    
    # 알루미늄 재료로 분석
    result = cnc_analyzer.analyze_machinability(
        "sample_drawing.dxf",
        material="aluminum"
    )
    
    if 'error' not in result:
        score = result['machinability_score']
        print(f"\n📊 가공성 평가:")
        print(f"  - 종합 점수: {score.overall_score:.1f}/100 (등급: {score.grade})")
        print(f"  - 복잡도: {score.complexity_score:.1f}")
        print(f"  - 공구 접근성: {score.tool_access_score:.1f}")
        
        print(f"\n⏱️ 예상 가공 시간:")
        time = result['machining_time']
        print(f"  - 총 시간: {time['total_minutes']}분")
        print(f"  - 절삭: {time['cutting_time']}분")
        print(f"  - 설정: {time['setup_time']}분")
        
        print(f"\n🔧 권장 공구:")
        for tool in result['tool_recommendations'][:2]:
            print(f"  - {tool.tool_type}: Ø{tool.diameter}mm ({tool.coating} 코팅)")
    else:
        print(f"오류: {result['error']}")
    
    return result

def test_cost_estimation():
    """비용 예측 테스트"""
    print("\n" + "=" * 50)
    print("💰 제조 비용 예측 테스트")
    print("=" * 50)
    
    # 비용 예측기 초기화
    cost_estimator = DXFCostEstimator()
    
    # 알루미늄 6061, 100개 생산
    result = cost_estimator.estimate_total_cost(
        "sample_drawing.dxf",
        material_spec={
            'type': 'aluminum',
            'grade': '6061',
            'thickness': 10,
            'machine': '3axis_mill'
        },
        production_qty=100
    )
    
    if 'error' not in result:
        print(f"\n📊 비용 분석 (100개 생산):")
        print(f"  - 단가: {result['unit_cost']:,.0f}원")
        print(f"  - 수량 할인: {result['quantity_discount']:.1f}%")
        print(f"  - 할인 후 단가: {result['unit_price_after_discount']:,.0f}원")
        print(f"  - 총 생산 비용: {result['total_production_cost']:,.0f}원")
        
        print(f"\n💡 비용 절감 제안:")
        for i, suggestion in enumerate(result['cost_reduction_suggestions'][:3], 1):
            print(f"  {i}. {suggestion}")
    else:
        print(f"오류: {result['error']}")
    
    return result

async def test_ai_analysis():
    """AI 통합 분석 테스트"""
    print("\n" + "=" * 50)
    print("🤖 AI 통합 분석 테스트")
    print("=" * 50)
    
    # 기본 분석 먼저 실행
    analyzer = DXFAnalyzer()
    basic_analysis = analyzer.analyze("sample_drawing.dxf")
    
    # AI 통합 분석
    ai_integration = DXFAIIntegration()
    
    # API 키 확인
    if ai_integration.gemini_model:
        print("\n✅ Gemini API 연결됨")
        
        # CNC 특화 분석 요청
        result = await ai_integration.analyze_with_gemini(
            basic_analysis,
            prompt_type='cnc_analysis'
        )
        
        if 'error' not in result:
            print(f"\n📝 AI 분석 결과:")
            print(result['analysis'][:500] + "...")
            
            if result.get('recommendations'):
                print(f"\n💡 AI 권장사항:")
                for rec in result['recommendations'][:3]:
                    print(f"  - {rec}")
        else:
            print(f"오류: {result['error']}")
    else:
        print("\n⚠️ Gemini API 키가 설정되지 않았습니다.")
        print("환경 변수 설정: export GOOGLE_API_KEY='your-api-key'")
    
    return result

def main():
    """메인 테스트 함수"""
    print("\n🚀 DXF CNC 특화 기능 테스트 시작\n")
    
    # 1. CNC 가공성 분석
    cnc_result = test_cnc_analysis()
    
    # 2. 비용 예측
    cost_result = test_cost_estimation()
    
    # 3. AI 분석 (비동기)
    try:
        ai_result = asyncio.run(test_ai_analysis())
    except Exception as e:
        print(f"\nAI 분석 중 오류 발생: {e}")
    
    print("\n" + "=" * 50)
    print("✅ 테스트 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main() 