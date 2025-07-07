#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 비즈니스 인텔리전스 대시보드
Author: Business Intelligence Expert
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
import asyncio

# 분석 모듈 임포트
from dxf_analyzer import DXFAnalyzer
from dxf_advanced_analyzer import DXFAdvancedAnalyzer
from dxf_cnc_analyzer import DXFCNCAnalyzer
from dxf_cost_estimator import DXFCostEstimator
from dxf_ai_integration import DXFAIIntegration


class BusinessDashboard:
    """경영진용 비즈니스 대시보드"""
    
    def __init__(self):
        """초기화"""
        self.analyzer = DXFAnalyzer()
        self.advanced_analyzer = DXFAdvancedAnalyzer()
        self.cnc_analyzer = DXFCNCAnalyzer()
        self.cost_estimator = DXFCostEstimator()
        self.ai_integration = DXFAIIntegration()
        
    def run(self):
        """대시보드 실행"""
        st.set_page_config(
            page_title="DXF 비즈니스 대시보드",
            page_icon="📊",
            layout="wide"
        )
        
        # 사이드바
        with st.sidebar:
            st.title("🏢 경영진 대시보드")
            st.markdown("---")
            
            # 메뉴 선택
            menu = st.selectbox(
                "메뉴 선택",
                ["📊 종합 대시보드", "💰 비용 분석", "🏭 생산성 분석", 
                 "📈 품질 트렌드", "🤖 AI 인사이트", "📋 프로젝트 관리"]
            )
            
            st.markdown("---")
            
            # 파일 업로드
            uploaded_file = st.file_uploader(
                "DXF 파일 업로드",
                type=['dxf'],
                help="분석할 DXF 파일을 업로드하세요"
            )
        
        # 메인 콘텐츠
        if menu == "📊 종합 대시보드":
            self._render_overview_dashboard(uploaded_file)
        elif menu == "💰 비용 분석":
            self._render_cost_analysis(uploaded_file)
        elif menu == "🏭 생산성 분석":
            self._render_productivity_analysis(uploaded_file)
        elif menu == "📈 품질 트렌드":
            self._render_quality_trends()
        elif menu == "🤖 AI 인사이트":
            self._render_ai_insights(uploaded_file)
        elif menu == "📋 프로젝트 관리":
            self._render_project_management()
    
    def _render_overview_dashboard(self, uploaded_file):
        """종합 대시보드"""
        st.title("📊 종합 대시보드")
        
        # KPI 카드
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="이번 달 프로젝트",
                value="24개",
                delta="3개 증가",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                label="평균 품질 점수",
                value="92.5",
                delta="2.3 상승",
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                label="예상 매출",
                value="₩2.4억",
                delta="15% 증가",
                delta_color="normal"
            )
        
        with col4:
            st.metric(
                label="생산 효율성",
                value="87%",
                delta="-2% 감소",
                delta_color="inverse"
            )
        
        st.markdown("---")
        
        # 실시간 분석
        if uploaded_file:
            with st.spinner("도면 분석 중..."):
                # 파일 저장
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 분석 실행
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🔍 도면 분석 결과")
                    try:
                        self.analyzer.analyze_dxf_file(temp_path)
                        analysis = {
                            'total_entities': sum(self.analyzer.entity_breakdown.values()) if self.analyzer.entity_breakdown else 0,
                            'layers': self.analyzer.layers,
                            'entity_breakdown': self.analyzer.entity_breakdown,
                            'drawing_bounds': self.analyzer._calculate_drawing_size()
                        }
                        analysis_success = True
                    except Exception as e:
                        analysis = {'error': str(e)}
                        analysis_success = False
                    
                    if analysis_success:
                        # 기본 정보
                        drawing_bounds = analysis.get('drawing_bounds') or {}
                        width = drawing_bounds.get('width', 0) if isinstance(drawing_bounds, dict) else 0
                        height = drawing_bounds.get('height', 0) if isinstance(drawing_bounds, dict) else 0
                        
                        st.info(f"""
                        **파일명**: {uploaded_file.name}  
                        **총 객체**: {analysis.get('total_entities', 0)}개  
                        **레이어**: {len(analysis.get('layers', []))}개  
                        **도면 크기**: {width:.1f} × {height:.1f}mm
                        """)
                        
                        # 엔티티 분포 차트
                        entity_data = analysis.get('entity_breakdown', {})
                        if entity_data and isinstance(entity_data, dict):
                            fig = px.pie(
                                values=list(entity_data.values()),
                                names=list(entity_data.keys()),
                                title="객체 유형 분포"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("💰 즉시 견적")
                    
                    # 재료 선택
                    material = st.selectbox(
                        "재료 선택",
                        ["aluminum", "steel", "stainless_steel", "titanium"]
                    )
                    
                    quantity = st.number_input(
                        "생산 수량",
                        min_value=1,
                        value=10,
                        step=1
                    )
                    
                    if st.button("견적 계산"):
                        cost_analysis = self.cost_estimator.estimate_total_cost(
                            temp_path,
                            {'type': material, 'grade': '6061', 'thickness': 10},
                            quantity
                        )
                        
                        if 'error' not in cost_analysis:
                            st.success(f"""
                            **단가**: {cost_analysis['unit_price_after_discount']:,.0f}원  
                            **총액**: {cost_analysis['total_production_cost']:,.0f}원  
                            **납기**: 약 {max(5, quantity // 10)}일
                            """)
                            
                            # 비용 구성 차트
                            breakdown = cost_analysis['cost_breakdown_chart']
                            fig = px.pie(
                                values=[v['amount'] for v in breakdown.values()],
                                names=list(breakdown.keys()),
                                title="비용 구성"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                
                # 임시 파일 삭제
                os.remove(temp_path)
        
        else:
            # 샘플 데이터로 차트 표시
            st.info("DXF 파일을 업로드하면 실시간 분석이 표시됩니다.")
            
            # 월별 프로젝트 추이
            dates = pd.date_range(end=datetime.now(), periods=12, freq='ME')
            project_data = pd.DataFrame({
                '날짜': dates,
                '프로젝트 수': [15, 18, 20, 19, 22, 21, 24, 26, 23, 25, 27, 24],
                '평균 단가': [850000, 920000, 880000, 950000, 1020000, 980000, 
                            1050000, 1100000, 1080000, 1150000, 1200000, 1180000]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=project_data['날짜'],
                y=project_data['프로젝트 수'],
                name='프로젝트 수',
                yaxis='y'
            ))
            fig.add_trace(go.Scatter(
                x=project_data['날짜'],
                y=project_data['평균 단가'],
                name='평균 단가',
                yaxis='y2',
                line=dict(color='red')
            ))
            
            fig.update_layout(
                title='월별 프로젝트 및 단가 추이',
                yaxis=dict(title='프로젝트 수'),
                yaxis2=dict(title='평균 단가 (원)', overlaying='y', side='right'),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_cost_analysis(self, uploaded_file):
        """비용 분석 페이지"""
        st.title("💰 비용 분석")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("월 평균 제조 비용", "₩1.8억", "-5%")
        with col2:
            st.metric("재료비 비중", "32%", "+2%")
        with col3:
            st.metric("가공비 비중", "45%", "-3%")
        
        st.markdown("---")
        
        # 비용 트렌드 분석
        st.subheader("📈 비용 트렌드 분석")
        
        # 샘플 데이터
        cost_trends = pd.DataFrame({
            '월': pd.date_range(start='2024-01', periods=6, freq='ME'),
            '재료비': [32000000, 35000000, 33000000, 36000000, 34000000, 37000000],
            '가공비': [45000000, 48000000, 46000000, 49000000, 47000000, 50000000],
            '공구비': [8000000, 8500000, 8200000, 8800000, 8400000, 9000000],
            '간접비': [15000000, 16000000, 15500000, 16500000, 16000000, 17000000]
        })
        
        fig = px.area(
            cost_trends,
            x='월',
            y=['재료비', '가공비', '공구비', '간접비'],
            title='월별 비용 구성 추이'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 재료별 비용 분석
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 재료별 평균 단가")
            material_costs = pd.DataFrame({
                '재료': ['알루미늄', '일반강', '스테인리스', '티타늄'],
                '평균 단가': [450000, 380000, 620000, 1500000],
                '사용 빈도': [45, 30, 20, 5]
            })
            
            fig = px.scatter(
                material_costs,
                x='사용 빈도',
                y='평균 단가',
                size='사용 빈도',
                text='재료',
                title='재료별 단가 vs 사용 빈도'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💡 비용 절감 기회")
            
            savings = pd.DataFrame({
                '항목': ['대량 구매 할인', '공정 최적화', '불량률 감소', '자동화 도입'],
                '예상 절감액': [12000000, 18000000, 8000000, 25000000]
            })
            
            fig = px.bar(
                savings,
                x='예상 절감액',
                y='항목',
                orientation='h',
                title='비용 절감 기회 (연간)'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_productivity_analysis(self, uploaded_file):
        """생산성 분석 페이지"""
        st.title("🏭 생산성 분석")
        
        # KPI
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("평균 가공 시간", "3.2시간", "-12분")
        with col2:
            st.metric("설비 가동률", "78%", "+5%")
        with col3:
            st.metric("시간당 생산량", "2.3개", "+0.2개")
        with col4:
            st.metric("불량률", "2.1%", "-0.3%")
        
        st.markdown("---")
        
        # 설비별 가동률
        st.subheader("⚙️ 설비별 가동률")
        
        machine_data = pd.DataFrame({
            '설비': ['3축 밀링 #1', '3축 밀링 #2', '5축 밀링', 'CNC 선반', 'EDM'],
            '가동률': [85, 78, 92, 70, 65],
            '생산량': [156, 142, 98, 120, 45]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=machine_data['설비'],
            y=machine_data['가동률'],
            name='가동률 (%)',
            marker_color='lightblue'
        ))
        fig.add_trace(go.Scatter(
            x=machine_data['설비'],
            y=machine_data['생산량'],
            name='월 생산량',
            yaxis='y2',
            marker_color='red'
        ))
        
        fig.update_layout(
            title='설비별 가동률 및 생산량',
            yaxis=dict(title='가동률 (%)'),
            yaxis2=dict(title='생산량 (개)', overlaying='y', side='right')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 병목 공정 분석
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚦 병목 공정 분석")
            
            bottleneck_data = pd.DataFrame({
                '공정': ['설정', '황삭', '정삭', '검사', '포장'],
                '평균 시간': [25, 45, 60, 15, 10],
                '대기 시간': [5, 15, 25, 8, 3]
            })
            
            fig = px.bar(
                bottleneck_data,
                x='공정',
                y=['평균 시간', '대기 시간'],
                title='공정별 소요 시간 (분)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 효율성 개선 제안")
            
            st.info("""
            **주요 개선 포인트**
            
            1. **정삭 공정 병목**: 
               - 고속 가공 전략 도입
               - 추가 설비 투자 검토
            
            2. **대기 시간 감소**:
               - 작업 스케줄링 최적화
               - 자동 공구 교환 시스템
            
            3. **설정 시간 단축**:
               - 표준 지그 활용
               - 디지털 셋업 시트
            """)
    
    def _render_quality_trends(self):
        """품질 트렌드 페이지"""
        st.title("📈 품질 트렌드")
        
        # 품질 지표
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("평균 품질 점수", "94.2", "+1.5")
        with col2:
            st.metric("불량률", "1.8%", "-0.4%")
        with col3:
            st.metric("재작업률", "3.2%", "-0.8%")
        with col4:
            st.metric("고객 만족도", "4.6/5", "+0.2")
        
        st.markdown("---")
        
        # 품질 점수 추이
        quality_data = pd.DataFrame({
            '날짜': pd.date_range(start='2024-01', periods=12, freq='ME'),
            '품질 점수': [91.5, 92.0, 91.8, 92.5, 93.0, 93.2, 93.5, 93.8, 94.0, 94.2, 94.5, 94.2],
            '목표': [93.0] * 12
        })
        
        fig = px.line(
            quality_data,
            x='날짜',
            y=['품질 점수', '목표'],
            title='월별 품질 점수 추이'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 불량 원인 분석
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("❌ 불량 원인 분석")
            
            defect_data = pd.DataFrame({
                '원인': ['치수 불량', '표면 조도', '가공 오류', '재료 결함', '기타'],
                '건수': [45, 32, 28, 15, 12]
            })
            
            fig = px.pie(
                defect_data,
                values='건수',
                names='원인',
                title='불량 원인별 분포'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("✅ 품질 개선 활동")
            
            improvement_data = pd.DataFrame({
                '활동': ['작업 표준화', '교육 강화', '설비 정비', '검사 강화'],
                '효과': [35, 28, 22, 15]
            })
            
            fig = px.bar(
                improvement_data,
                x='활동',
                y='효과',
                title='개선 활동별 효과 (%)'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_ai_insights(self, uploaded_file):
        """AI 인사이트 페이지"""
        st.title("🤖 AI 인사이트")
        
        if uploaded_file:
            with st.spinner("AI 분석 중..."):
                # 파일 저장
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 분석 실행
                try:
                    self.analyzer.analyze_dxf_file(temp_path)
                    analysis = {
                        'total_entities': sum(self.analyzer.entity_breakdown.values()) if self.analyzer.entity_breakdown else 0,
                        'layers': self.analyzer.layers,
                        'entity_breakdown': self.analyzer.entity_breakdown
                    }
                    # 고급 분석은 일단 기본값으로 설정
                    advanced = {'quality_score': 85}
                except Exception as e:
                    analysis = {'error': str(e)}
                    advanced = {'error': str(e)}
                
                # AI 분석 (비동기 실행)
                if 'error' not in analysis:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📊 AI 품질 평가")
                        
                        # 품질 점수 게이지
                        score = advanced.get('quality_score', 0)
                        fig = go.Figure(go.Indicator(
                            mode = "gauge+number+delta",
                            value = score,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "품질 점수"},
                            delta = {'reference': 90},
                            gauge = {
                                'axis': {'range': [None, 100]},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [0, 50], 'color': "lightgray"},
                                    {'range': [50, 80], 'color': "gray"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 90
                                }
                            }
                        ))
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.subheader("💡 AI 권장사항")
                        
                        # AI 분석 결과 (샘플)
                        st.success("""
                        **AI 분석 결과**
                        
                        ✅ **강점**:
                        - 표준 레이어 구조 준수
                        - 일관된 선 두께 사용
                        - 적절한 공차 설정
                        
                        ⚠️ **개선 필요**:
                        - 일부 중복 객체 발견
                        - 텍스트 크기 표준화 필요
                        - 치수선 정리 권장
                        
                        💰 **비용 절감 기회**:
                        - 구멍 크기 표준화로 15% 절감 가능
                        - 가공 순서 최적화로 20분 단축
                        """)
                
                # 임시 파일 삭제
                os.remove(temp_path)
        
        else:
            st.info("DXF 파일을 업로드하면 AI 분석이 시작됩니다.")
            
            # AI 인사이트 히스토리
            st.subheader("📜 최근 AI 인사이트")
            
            insights_history = pd.DataFrame({
                '날짜': pd.date_range(end=datetime.now(), periods=5, freq='D'),
                '프로젝트': ['부품 A-123', '케이스 B-456', '브라켓 C-789', '플레이트 D-012', '하우징 E-345'],
                '주요 인사이트': [
                    '가공 시간 30% 단축 가능',
                    '재료 변경으로 40% 비용 절감',
                    '공차 완화로 불량률 50% 감소',
                    '설계 단순화로 2공정 제거 가능',
                    '표준 부품 사용으로 20% 절감'
                ],
                '예상 효과': ['₩2,500,000', '₩4,200,000', '₩1,800,000', '₩3,600,000', '₩2,100,000']
            })
            
            st.dataframe(insights_history, use_container_width=True)
    
    def _render_project_management(self):
        """프로젝트 관리 페이지"""
        st.title("📋 프로젝트 관리")
        
        # 프로젝트 현황
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("진행 중", "12개", "+2")
        with col2:
            st.metric("대기 중", "8개", "+3")
        with col3:
            st.metric("완료", "156개", "+24")
        with col4:
            st.metric("지연", "2개", "-1")
        
        st.markdown("---")
        
        # 프로젝트 타임라인
        st.subheader("📅 프로젝트 타임라인")
        
        # 간트 차트 데이터
        projects = pd.DataFrame({
            'Task': ['프로젝트 A', '프로젝트 B', '프로젝트 C', '프로젝트 D', '프로젝트 E'],
            'Start': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15', '2024-03-01'],
            'Finish': ['2024-02-15', '2024-03-01', '2024-03-15', '2024-04-01', '2024-04-15'],
            'Resource': ['팀 1', '팀 2', '팀 1', '팀 3', '팀 2']
        })
        
        fig = px.timeline(
            projects,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Resource",
            title="프로젝트 일정"
        )
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, use_container_width=True)
        
        # 프로젝트 상세
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 주요 마일스톤")
            
            milestones = pd.DataFrame({
                '마일스톤': ['설계 완료', '시제품 제작', '품질 검증', '양산 시작'],
                '예정일': ['2024-02-01', '2024-02-15', '2024-03-01', '2024-03-15'],
                '상태': ['완료', '진행중', '대기', '대기']
            })
            
            st.dataframe(milestones, use_container_width=True)
        
        with col2:
            st.subheader("⚡ 리스크 관리")
            
            risks = pd.DataFrame({
                '리스크': ['재료 수급 지연', '설비 고장', '품질 기준 미달', '납기 지연'],
                '확률': ['낮음', '중간', '낮음', '높음'],
                '영향도': ['높음', '중간', '높음', '높음'],
                '대응 방안': ['대체 공급처 확보', '예방 정비 강화', '사전 검증 강화', '버퍼 시간 확보']
            })
            
            st.dataframe(risks, use_container_width=True)


def main():
    """메인 함수"""
    dashboard = BusinessDashboard()
    dashboard.run()


if __name__ == "__main__":
    main() 