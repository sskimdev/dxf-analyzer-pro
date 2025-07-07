
import streamlit as st
import os
import tempfile
from datetime import datetime
import logging
import io
import zipfile

# 페이지 설정
st.set_page_config(
    page_title="DXF CAD 도면 분석기",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바에 설정 옵션
st.sidebar.title("📐 DXF 분석기")
st.sidebar.markdown("---")

# 분석 옵션
analysis_options = st.sidebar.expander("분석 옵션", expanded=True)
with analysis_options:
    include_dimensions = st.checkbox("치수 정보 포함", value=True)
    include_circles = st.checkbox("원/호 정보 포함", value=True)
    include_texts = st.checkbox("텍스트 정보 포함", value=True)
    max_display_items = st.slider("최대 표시 항목 수", 10, 100, 50)

# 리포트 옵션
report_options = st.sidebar.expander("리포트 옵션", expanded=False)
with report_options:
    include_summary = st.checkbox("요약 정보", value=True)
    include_layers = st.checkbox("레이어 목록", value=True)
    include_entity_breakdown = st.checkbox("객체 유형별 분석", value=True)

st.sidebar.markdown("---")
st.sidebar.info("💡 **사용법:**\n1. DXF 파일 업로드\n2. 분석 옵션 설정\n3. '분석 시작' 버튼 클릭")

# 메인 제목
st.title("🔧 DXF CAD 도면 분석기")
st.markdown("### AutoCAD DXF 파일을 업로드하여 상세한 분석 리포트를 생성하세요")

# 파일 업로드
uploaded_file = st.file_uploader(
    "DXF 파일을 선택하세요",
    type=['dxf'],
    help="AutoCAD Drawing Exchange Format 파일을 업로드하세요"
)

if uploaded_file is not None:
    # 파일 정보 표시
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("파일명", uploaded_file.name)
    with col2:
        st.metric("파일 크기", f"{uploaded_file.size:,} bytes")
    with col3:
        st.metric("파일 타입", uploaded_file.type)

    # 분석 시작 버튼
    if st.button("🚀 분석 시작", type="primary", use_container_width=True):

        # 진행률 표시
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("파일 준비 중...")
            progress_bar.progress(10)

            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name

            status_text.text("DXF 파일 분석 중...")
            progress_bar.progress(30)

            # 분석기 인스턴스 생성 (dxf_analyzer 모듈에서 임포트)
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            from dxf_analyzer import DXFAnalyzer, ADVANCED_ANALYSIS_AVAILABLE
            analyzer = DXFAnalyzer()

            # 분석 실행
            success = analyzer.analyze_dxf_file(tmp_file_path)
            progress_bar.progress(70)

            if success:
                status_text.text("결과 처리 중...")
                progress_bar.progress(90)

                # 결과 표시
                st.success("✅ 분석이 성공적으로 완료되었습니다!")
                progress_bar.progress(100)
                status_text.text("완료!")

                # 탭으로 결과 구분
                tab1, tab2, tab3, tab4 = st.tabs(["📊 요약", "📋 상세 정보", "📝 마크다운", "💾 다운로드"])

                with tab1:
                    st.header("📊 분석 요약")

                    # 메트릭 표시
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "전체 객체 수",
                            f"{analyzer.summary_info['total_entities']:,}",
                            help="DXF 파일에 포함된 모든 객체의 수"
                        )

                    with col2:
                        st.metric(
                            "레이어 수",
                            analyzer.summary_info['layer_count'],
                            help="도면에서 사용된 레이어의 수"
                        )

                    with col3:
                        st.metric(
                            "치수 객체",
                            analyzer.summary_info['dimension_count'],
                            help="치수 정보를 담고 있는 객체의 수"
                        )

                    with col4:
                        st.metric(
                            "텍스트 객체",
                            analyzer.summary_info['text_count'],
                            help="텍스트 및 주석 객체의 수"
                        )

                    # 객체 유형별 분포 차트
                    if include_entity_breakdown:
                        st.subheader("객체 유형별 분포")

                        # 차트 데이터 준비
                        entity_data = analyzer.summary_info['entity_breakdown']
                        if entity_data:
                            import pandas as pd
                            df = pd.DataFrame(
                                list(entity_data.items()),
                                columns=['객체 유형', '개수']
                            ).sort_values('개수', ascending=False)

                            # 바차트
                            st.bar_chart(df.set_index('객체 유형'))

                            # 데이터 테이블
                            st.dataframe(df, use_container_width=True)

                with tab2:
                    st.header("📋 상세 분석 정보")

                    # 레이어 정보
                    if include_layers and analyzer.layers:
                        st.subheader("🎨 레이어 정보")

                        layer_df = pd.DataFrame(analyzer.layers)
                        layer_df.index = layer_df.index + 1
                        st.dataframe(layer_df, use_container_width=True)

                    # 치수 정보
                    if include_dimensions and analyzer.dimensions:
                        st.subheader("📏 치수 정보")

                        dim_data = []
                        for i, dim in enumerate(analyzer.dimensions[:max_display_items], 1):
                            dim_data.append({
                                'No.': i,
                                '측정값': f"{dim['measurement']:.3f}" if dim['measurement'] else "N/A",
                                '텍스트': dim['text_override'][:30] + "..." if len(dim['text_override']) > 30 else dim['text_override'],
                                '스타일': dim['style'],
                                '레이어': dim['layer']
                            })

                        dim_df = pd.DataFrame(dim_data)
                        st.dataframe(dim_df, use_container_width=True)

                        if len(analyzer.dimensions) > max_display_items:
                            st.info(f"처음 {max_display_items}개 항목만 표시됩니다. (전체: {len(analyzer.dimensions)}개)")

                    # 원/호 정보
                    if include_circles and analyzer.circles:
                        st.subheader("⭕ 원/호 정보")

                        circle_data = []
                        for i, circle in enumerate(analyzer.circles[:max_display_items], 1):
                            circle_data.append({
                                'No.': i,
                                '중심점 X': f"{circle['center'][0]:.3f}",
                                '중심점 Y': f"{circle['center'][1]:.3f}",
                                '반지름': f"{circle['radius']:.3f}",
                                '지름': f"{circle['diameter']:.3f}",
                                '레이어': circle['layer']
                            })

                        circle_df = pd.DataFrame(circle_data)
                        st.dataframe(circle_df, use_container_width=True)

                        if len(analyzer.circles) > max_display_items:
                            st.info(f"처음 {max_display_items}개 항목만 표시됩니다. (전체: {len(analyzer.circles)}개)")

                    # 텍스트 정보
                    if include_texts and analyzer.texts:
                        st.subheader("📝 텍스트 정보")

                        text_data = []
                        for i, text in enumerate(analyzer.texts[:max_display_items], 1):
                            content = text['content'][:100] + "..." if len(text['content']) > 100 else text['content']
                            text_data.append({
                                'No.': i,
                                '내용': content,
                                '높이': f"{text['height']:.2f}",
                                '레이어': text['layer'],
                                '스타일': text['style']
                            })

                        text_df = pd.DataFrame(text_data)
                        st.dataframe(text_df, use_container_width=True)

                        if len(analyzer.texts) > max_display_items:
                            st.info(f"처음 {max_display_items}개 항목만 표시됩니다. (전체: {len(analyzer.texts)}개)")

                with tab3:
                    st.header("📝 마크다운 리포트 미리보기")

                    # 마크다운 내용 생성
                    markdown_content = analyzer._build_markdown_content()

                    # 코드 블록으로 표시 (편집 가능)
                    edited_markdown = st.text_area(
                        "마크다운 내용 (편집 가능)",
                        value=markdown_content,
                        height=400,
                        help="내용을 편집한 후 다운로드할 수 있습니다"
                    )

                    # 마크다운 렌더링 미리보기
                    with st.expander("📖 렌더링 미리보기", expanded=False):
                        st.markdown(edited_markdown)

                with tab4:
                    st.header("💾 다운로드")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("📄 마크다운 리포트")

                        # 마크다운 파일 다운로드
                        markdown_content = analyzer._build_markdown_content()

                        st.download_button(
                            label="📥 마크다운 파일 다운로드 (.md)",
                            data=markdown_content,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_Analysis_Report.md",
                            mime="text/markdown",
                            help="마크다운 형식의 분석 리포트를 다운로드합니다"
                        )

                    with col2:
                        st.subheader("📊 데이터 내보내기")

                        # JSON 형태로 원시 데이터 제공
                        raw_data = {
                            'file_info': analyzer.file_info,
                            'summary_info': analyzer.summary_info,
                            'layers': analyzer.layers,
                            'dimensions': analyzer.dimensions[:100],  # 최대 100개
                            'circles': analyzer.circles[:100],  # 최대 100개
                            'texts': analyzer.texts[:100]  # 최대 100개
                        }

                        # 날짜/시간 객체를 문자열로 변환
                        if 'modified_time' in raw_data['file_info']:
                            raw_data['file_info']['modified_time'] = raw_data['file_info']['modified_time'].isoformat()

                        import json
                        json_data = json.dumps(raw_data, ensure_ascii=False, indent=2)

                        st.download_button(
                            label="📥 JSON 데이터 다운로드 (.json)",
                            data=json_data,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_data.json",
                            mime="application/json",
                            help="구조화된 JSON 형식으로 분석 데이터를 다운로드합니다"
                        )

            else:
                st.error("❌ DXF 파일 분석에 실패했습니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.")
                progress_bar.progress(0)
                status_text.text("분석 실패")

        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
            progress_bar.progress(0)
            status_text.text("오류 발생")

        finally:
            # 임시 파일 정리
            try:
                if 'tmp_file_path' in locals():
                    os.unlink(tmp_file_path)
            except:
                pass

else:
    # 파일이 업로드되지 않은 경우
    st.info("👆 위에서 DXF 파일을 업로드하여 분석을 시작하세요")

    # 샘플 정보 표시
    with st.expander("📖 DXF 분석기 정보", expanded=False):
        st.markdown("""
        ### 🔧 주요 기능
        - **자동 객체 인식**: 치수, 원/호, 텍스트, 라인 등 모든 CAD 객체 자동 분석
        - **레이어 분석**: 색상, 라인타입, 상태 등 레이어 정보 상세 분석
        - **통계 정보**: 객체 유형별 개수 및 분포 통계
        - **마크다운 리포트**: 전문적인 분석 리포트 자동 생성
        - **데이터 내보내기**: 마크다운, JSON 형식으로 데이터 내보내기

        ### 📋 지원 형식
        - AutoCAD DXF (Drawing Exchange Format)
        - ASCII 및 Binary DXF 파일
        - DXF R12, R2000, R2004, R2007, R2010, R2013, R2018

        ### 💡 사용 팁
        - 대용량 파일의 경우 분석에 시간이 걸릴 수 있습니다
        - 사이드바에서 분석 옵션을 조정할 수 있습니다
        - 마크다운 탭에서 리포트 내용을 편집할 수 있습니다
        """)

# 푸터
st.markdown("---")
st.markdown(
    "💻 **DXF CAD 도면 분석기** | "
    "Built with [Streamlit](https://streamlit.io) & [ezdxf](https://github.com/mozman/ezdxf)"
)
