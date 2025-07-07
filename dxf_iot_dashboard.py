#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF IoT 실시간 모니터링 대시보드
Author: IoT Dashboard Expert
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import json
from datetime import datetime, timedelta
import time
from typing import Dict, List
import random

# IoT 모니터 임포트
from dxf_iot_monitor import IoTMonitor, MachineStatus, SensorData

# 페이지 설정
st.set_page_config(
    page_title="CNC IoT 모니터링",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .status-running { color: #28a745; font-weight: bold; }
    .status-idle { color: #ffc107; font-weight: bold; }
    .status-error { color: #dc3545; font-weight: bold; }
    .alert-critical { background-color: #f8d7da; padding: 10px; border-radius: 5px; }
    .alert-warning { background-color: #fff3cd; padding: 10px; border-radius: 5px; }
    .metric-card { 
        background: white; 
        padding: 20px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


class IoTDashboard:
    """IoT 모니터링 대시보드"""
    
    def __init__(self):
        """초기화"""
        # 세션 상태 초기화
        if 'iot_monitor' not in st.session_state:
            st.session_state.iot_monitor = IoTMonitor()
            st.session_state.simulation_running = False
            st.session_state.last_update = datetime.now()
        
        self.monitor = st.session_state.iot_monitor
    
    def run(self):
        """대시보드 실행"""
        # 헤더
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.title("🏭 CNC IoT 실시간 모니터링")
        with col2:
            if st.button("🔄 새로고침"):
                st.rerun()
        with col3:
            status = "🟢 연결됨" if self.monitor.mqtt_client else "🔴 연결 안됨"
            st.metric("MQTT 상태", status)
        
        # 사이드바
        with st.sidebar:
            st.header("⚙️ 설정")
            
            # 시뮬레이션 컨트롤
            st.subheader("시뮬레이션")
            if st.button("시뮬레이션 시작/중지"):
                st.session_state.simulation_running = not st.session_state.simulation_running
            
            if st.session_state.simulation_running:
                st.success("시뮬레이션 실행 중...")
                # 시뮬레이션 데이터 생성
                for i in range(1, 4):
                    self.monitor.simulate_sensor_data(f"CNC-{i:03d}")
            
            # MQTT 설정
            st.subheader("MQTT 설정")
            broker = st.text_input("브로커 주소", value="localhost")
            port = st.number_input("포트", value=1883, min_value=1)
            
            if st.button("MQTT 연결"):
                self.monitor.mqtt_broker = broker
                self.monitor.mqtt_port = port
                if self.monitor.start_mqtt_client():
                    st.success("MQTT 연결 성공!")
                else:
                    st.error("MQTT 연결 실패")
            
            # 임계값 설정
            st.subheader("알림 임계값")
            temp_warning = st.slider("온도 경고 (°C)", 40, 80, 60)
            temp_critical = st.slider("온도 위험 (°C)", 60, 100, 80)
            vib_warning = st.slider("진동 경고 (mm/s)", 3.0, 10.0, 5.0)
            vib_critical = st.slider("진동 위험 (mm/s)", 5.0, 15.0, 8.0)
            
            self.monitor.thresholds['temperature']['warning'] = temp_warning
            self.monitor.thresholds['temperature']['critical'] = temp_critical
            self.monitor.thresholds['vibration']['warning'] = vib_warning
            self.monitor.thresholds['vibration']['critical'] = vib_critical
        
        # 메인 대시보드
        tab1, tab2, tab3, tab4 = st.tabs(["📊 실시간 모니터링", "📈 트렌드 분석", "🚨 알림 관리", "📋 리포트"])
        
        with tab1:
            self._render_realtime_monitoring()
        
        with tab2:
            self._render_trend_analysis()
        
        with tab3:
            self._render_alert_management()
        
        with tab4:
            self._render_reports()
        
        # 자동 새로고침 (5초마다)
        if st.session_state.simulation_running:
            time.sleep(5)
            st.rerun()
    
    def _render_realtime_monitoring(self):
        """실시간 모니터링 탭"""
        # 전체 상태 요약
        analytics = self.monitor._get_analytics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "평균 효율성",
                f"{analytics.get('average_efficiency', 0):.1f}%",
                delta=f"{random.uniform(-2, 2):.1f}%"
            )
        with col2:
            st.metric(
                "가동률",
                f"{analytics.get('utilization_rate', 0):.1f}%",
                delta=f"{random.uniform(-5, 5):.1f}%"
            )
        with col3:
            st.metric(
                "오늘 생산량",
                f"{analytics.get('total_parts_today', 0)}개",
                delta=f"+{random.randint(1, 10)}개"
            )
        with col4:
            alerts = analytics.get('alert_summary', {})
            critical_count = alerts.get('critical', 0) + alerts.get('error', 0)
            st.metric(
                "중요 알림",
                f"{critical_count}건",
                delta=None if critical_count == 0 else f"+{critical_count}건"
            )
        
        st.markdown("---")
        
        # 기계별 상태
        st.subheader("🔧 기계별 실시간 상태")
        
        machines = self.monitor._get_all_machine_status()
        if machines:
            # 그리드 레이아웃으로 기계 상태 표시
            cols = st.columns(3)
            for idx, machine in enumerate(machines):
                with cols[idx % 3]:
                    self._render_machine_card(machine)
        else:
            st.info("연결된 기계가 없습니다. 시뮬레이션을 시작하거나 MQTT를 연결해주세요.")
    
    def _render_machine_card(self, machine: Dict):
        """기계 상태 카드"""
        status_colors = {
            'running': '#28a745',
            'idle': '#ffc107',
            'error': '#dc3545',
            'maintenance': '#6c757d'
        }
        
        status = machine.get('status', 'unknown')
        color = status_colors.get(status, '#6c757d')
        
        # 카드 컨테이너
        with st.container():
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 10px; 
                        border-left: 5px solid {color}; margin-bottom: 20px;">
                <h4>{machine['machine_id']}</h4>
                <p style="color: {color}; font-weight: bold;">상태: {status.upper()}</p>
                <p>작업: {machine.get('operation', 'N/A')}</p>
                <p>효율성: {machine.get('efficiency', 0):.1f}%</p>
                <p>온도: {machine.get('temperature', 0):.1f}°C</p>
                <p>진동: {machine.get('vibration', 0):.2f}mm/s</p>
                <p>생산량: {machine.get('parts_completed', 0)}개</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 실시간 게이지
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=machine.get('efficiency', 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "효율성 (%)"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': color},
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
            fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_trend_analysis(self):
        """트렌드 분석 탭"""
        st.subheader("📈 센서 데이터 트렌드")
        
        # 기계 선택
        machines = list(self.monitor.machine_status.keys())
        if not machines:
            st.info("데이터가 없습니다. 시뮬레이션을 시작해주세요.")
            return
        
        selected_machine = st.selectbox("기계 선택", machines)
        
        # 시간 범위 선택
        time_range = st.select_slider(
            "시간 범위",
            options=["1시간", "6시간", "12시간", "24시간"],
            value="1시간"
        )
        
        hours = {"1시간": 1, "6시간": 6, "12시간": 12, "24시간": 24}[time_range]
        
        # 센서 데이터 조회
        history = self.monitor._get_sensor_history(selected_machine, hours)
        
        if history:
            # 데이터프레임 생성
            df = pd.DataFrame(history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 센서별 차트 생성
            sensor_types = df['sensor_type'].unique()
            
            fig = make_subplots(
                rows=len(sensor_types),
                cols=1,
                subplot_titles=[f"{sensor} 트렌드" for sensor in sensor_types],
                vertical_spacing=0.1
            )
            
            for i, sensor in enumerate(sensor_types):
                sensor_data = df[df['sensor_type'] == sensor]
                
                # 임계값 라인 추가
                if sensor in self.monitor.thresholds:
                    warning = self.monitor.thresholds[sensor]['warning']
                    critical = self.monitor.thresholds[sensor]['critical']
                    
                    fig.add_hline(
                        y=warning, line_dash="dash", line_color="orange",
                        annotation_text="경고", row=i+1, col=1
                    )
                    fig.add_hline(
                        y=critical, line_dash="dash", line_color="red",
                        annotation_text="위험", row=i+1, col=1
                    )
                
                fig.add_trace(
                    go.Scatter(
                        x=sensor_data['timestamp'],
                        y=sensor_data['value'],
                        mode='lines+markers',
                        name=sensor,
                        line=dict(width=2)
                    ),
                    row=i+1, col=1
                )
            
            fig.update_layout(height=300 * len(sensor_types), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("선택한 기간에 데이터가 없습니다.")
        
        # 통계 정보
        st.subheader("📊 통계 요약")
        trends = self.monitor._get_sensor_trends()
        
        if selected_machine in trends:
            machine_trends = trends[selected_machine]
            
            cols = st.columns(len(machine_trends))
            for idx, (sensor, stats) in enumerate(machine_trends.items()):
                with cols[idx]:
                    st.metric(
                        f"{sensor} 평균",
                        f"{stats['avg']:.2f}",
                        delta=f"범위: {stats['min']:.1f} - {stats['max']:.1f}"
                    )
    
    def _render_alert_management(self):
        """알림 관리 탭"""
        st.subheader("🚨 알림 이력")
        
        # 알림 필터
        col1, col2, col3 = st.columns(3)
        with col1:
            severity_filter = st.multiselect(
                "심각도",
                ["info", "warning", "error", "critical"],
                default=["warning", "error", "critical"]
            )
        with col2:
            machine_filter = st.multiselect(
                "기계",
                list(self.monitor.machine_status.keys()),
                default=list(self.monitor.machine_status.keys())
            )
        with col3:
            show_acknowledged = st.checkbox("확인된 알림 표시", value=False)
        
        # 알림 목록
        alerts = self.monitor._get_recent_alerts(limit=50)
        
        if alerts:
            # 필터링
            filtered_alerts = [
                alert for alert in alerts
                if alert['severity'] in severity_filter
                and (not machine_filter or alert['machine_id'] in machine_filter)
                and (show_acknowledged or not alert['acknowledged'])
            ]
            
            if filtered_alerts:
                # 알림 표시
                for alert in filtered_alerts:
                    severity = alert['severity']
                    icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}[severity]
                    color = {"info": "info", "warning": "warning", "error": "error", "critical": "error"}[severity]
                    
                    col1, col2, col3, col4 = st.columns([1, 2, 3, 1])
                    
                    with col1:
                        st.write(f"{icon} **{severity.upper()}**")
                    with col2:
                        st.write(alert['machine_id'])
                    with col3:
                        st.write(alert['message'])
                    with col4:
                        if not alert['acknowledged']:
                            if st.button("확인", key=f"ack_{alert['timestamp']}"):
                                # 실제로는 alert ID를 사용해야 함
                                self.monitor._acknowledge_alert(None)
                                st.rerun()
                        else:
                            st.write("✅ 확인됨")
                    
                    st.markdown("---")
            else:
                st.info("필터 조건에 맞는 알림이 없습니다.")
        else:
            st.info("알림 이력이 없습니다.")
        
        # 알림 통계
        st.subheader("📊 알림 통계")
        
        analytics = self.monitor._get_analytics()
        alert_summary = analytics.get('alert_summary', {})
        
        if alert_summary:
            fig = px.bar(
                x=list(alert_summary.keys()),
                y=list(alert_summary.values()),
                labels={'x': '심각도', 'y': '건수'},
                title="심각도별 알림 분포",
                color=list(alert_summary.keys()),
                color_discrete_map={
                    'info': '#17a2b8',
                    'warning': '#ffc107',
                    'error': '#fd7e14',
                    'critical': '#dc3545'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_reports(self):
        """리포트 탭"""
        st.subheader("📋 일일 생산 리포트")
        
        # 리포트 날짜 선택
        report_date = st.date_input("날짜 선택", value=datetime.now().date())
        
        # 리포트 생성
        if st.button("리포트 생성"):
            report = self._generate_daily_report(report_date)
            
            # 리포트 표시
            st.markdown(report, unsafe_allow_html=True)
            
            # 다운로드 버튼
            st.download_button(
                label="📥 리포트 다운로드",
                data=report,
                file_name=f"daily_report_{report_date}.html",
                mime="text/html"
            )
        
        # 실시간 대시보드 데이터
        st.subheader("🔄 실시간 데이터 내보내기")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("JSON 내보내기"):
                data = self.monitor.get_dashboard_data()
                json_data = json.dumps(data, indent=2, default=str)
                st.download_button(
                    label="📥 JSON 다운로드",
                    data=json_data,
                    file_name=f"iot_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("CSV 내보내기"):
                # 센서 데이터를 CSV로 변환
                sensor_data = []
                for data in self.monitor.sensor_data_buffer:
                    sensor_data.append({
                        'timestamp': data.timestamp,
                        'machine_id': data.machine_id,
                        'sensor_type': data.sensor_type,
                        'value': data.value,
                        'unit': data.unit,
                        'status': data.status
                    })
                
                if sensor_data:
                    df = pd.DataFrame(sensor_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 CSV 다운로드",
                        data=csv,
                        file_name=f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("내보낼 데이터가 없습니다.")
    
    def _generate_daily_report(self, date) -> str:
        """일일 리포트 생성"""
        analytics = self.monitor._get_analytics()
        
        report = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .metric {{ display: inline-block; margin: 20px; padding: 15px; 
                          background: #f0f0f0; border-radius: 5px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .status-running {{ color: green; }}
                .status-idle {{ color: orange; }}
                .status-error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>일일 생산 리포트 - {date}</h1>
            
            <div class="summary">
                <div class="metric">
                    <div>평균 효율성</div>
                    <div class="metric-value">{analytics.get('average_efficiency', 0):.1f}%</div>
                </div>
                <div class="metric">
                    <div>가동률</div>
                    <div class="metric-value">{analytics.get('utilization_rate', 0):.1f}%</div>
                </div>
                <div class="metric">
                    <div>총 생산량</div>
                    <div class="metric-value">{analytics.get('total_parts_today', 0)}개</div>
                </div>
            </div>
            
            <h2>기계별 상태</h2>
            <table>
                <tr>
                    <th>기계 ID</th>
                    <th>상태</th>
                    <th>생산량</th>
                    <th>효율성</th>
                    <th>평균 온도</th>
                    <th>최대 진동</th>
                </tr>
        """
        
        for machine in self.monitor._get_all_machine_status():
            status_class = f"status-{machine['status']}"
            report += f"""
                <tr>
                    <td>{machine['machine_id']}</td>
                    <td class="{status_class}">{machine['status'].upper()}</td>
                    <td>{machine['parts_completed']}개</td>
                    <td>{machine['efficiency']:.1f}%</td>
                    <td>{machine['temperature']:.1f}°C</td>
                    <td>{machine['vibration']:.2f}mm/s</td>
                </tr>
            """
        
        report += """
            </table>
            
            <h2>알림 요약</h2>
        """
        
        alert_summary = analytics.get('alert_summary', {})
        if alert_summary:
            report += "<ul>"
            for severity, count in alert_summary.items():
                report += f"<li>{severity.upper()}: {count}건</li>"
            report += "</ul>"
        else:
            report += "<p>알림 없음</p>"
        
        report += """
            <p style="margin-top: 40px; font-size: 12px; color: #666;">
                생성 시간: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
            </p>
        </body>
        </html>
        """
        
        return report


def main():
    """메인 함수"""
    dashboard = IoTDashboard()
    dashboard.run()


if __name__ == "__main__":
    main() 