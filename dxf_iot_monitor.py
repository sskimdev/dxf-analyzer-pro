#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF IoT 실시간 모니터링 모듈
Author: IoT Integration Expert
Version: 1.0.0
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import pandas as pd
import numpy as np

# MQTT 클라이언트
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

# 웹소켓 서버
try:
    import websockets
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SensorData:
    """센서 데이터 클래스"""
    timestamp: datetime
    machine_id: str
    sensor_type: str
    value: float
    unit: str
    status: str  # normal, warning, critical


@dataclass
class MachineStatus:
    """기계 상태 정보"""
    machine_id: str
    status: str  # idle, running, error, maintenance
    current_operation: str
    spindle_speed: float
    feed_rate: float
    tool_number: int
    coolant_flow: float
    temperature: float
    vibration: float
    power_consumption: float
    cycle_time: float
    parts_completed: int
    efficiency: float


class IoTMonitor:
    """IoT 실시간 모니터링 클래스"""
    
    def __init__(self, mqtt_broker: str = "localhost", mqtt_port: int = 1883):
        """초기화"""
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.websocket_server = None
        self.connected_clients = set()
        
        # 데이터 저장소
        self.sensor_data_buffer = []
        self.machine_status = {}
        self.alert_history = []
        
        # 임계값 설정
        self.thresholds = {
            'temperature': {'warning': 60, 'critical': 80},
            'vibration': {'warning': 5.0, 'critical': 8.0},
            'spindle_speed_deviation': {'warning': 100, 'critical': 200},
            'power_consumption': {'warning': 80, 'critical': 95}  # 정격 대비 %
        }
        
        # 모니터링 설정
        self.monitoring_config = {
            'buffer_size': 1000,
            'data_retention_hours': 24,
            'alert_cooldown_minutes': 5
        }
        
    def start_mqtt_client(self):
        """MQTT 클라이언트 시작"""
        if not MQTT_AVAILABLE:
            logger.error("MQTT 라이브러리가 설치되지 않았습니다. pip install paho-mqtt")
            return False
        
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            logger.info(f"MQTT 클라이언트 시작: {self.mqtt_broker}:{self.mqtt_port}")
            return True
        except Exception as e:
            logger.error(f"MQTT 연결 실패: {e}")
            return False
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT 연결 콜백"""
        if rc == 0:
            logger.info("MQTT 브로커 연결 성공")
            # 토픽 구독
            topics = [
                "cnc/+/status",
                "cnc/+/sensor/+",
                "cnc/+/alert",
                "cnc/+/production"
            ]
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"구독: {topic}")
        else:
            logger.error(f"MQTT 연결 실패: {rc}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT 메시지 수신 콜백"""
        try:
            topic_parts = msg.topic.split('/')
            payload = json.loads(msg.payload.decode())
            
            if len(topic_parts) >= 3:
                machine_id = topic_parts[1]
                message_type = topic_parts[2]
                
                if message_type == 'status':
                    self._update_machine_status(machine_id, payload)
                elif message_type == 'sensor':
                    sensor_type = topic_parts[3] if len(topic_parts) > 3 else 'unknown'
                    self._process_sensor_data(machine_id, sensor_type, payload)
                elif message_type == 'alert':
                    self._process_alert(machine_id, payload)
                elif message_type == 'production':
                    self._update_production_data(machine_id, payload)
                
                # WebSocket으로 실시간 전송
                asyncio.create_task(self._broadcast_update({
                    'type': message_type,
                    'machine_id': machine_id,
                    'data': payload,
                    'timestamp': datetime.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT 연결 해제 콜백"""
        logger.warning(f"MQTT 연결 해제: {rc}")
        if rc != 0:
            # 재연결 시도
            logger.info("MQTT 재연결 시도...")
            time.sleep(5)
            try:
                client.reconnect()
            except:
                pass
    
    def _update_machine_status(self, machine_id: str, data: Dict):
        """기계 상태 업데이트"""
        self.machine_status[machine_id] = MachineStatus(
            machine_id=machine_id,
            status=data.get('status', 'unknown'),
            current_operation=data.get('operation', ''),
            spindle_speed=data.get('spindle_speed', 0),
            feed_rate=data.get('feed_rate', 0),
            tool_number=data.get('tool_number', 0),
            coolant_flow=data.get('coolant_flow', 0),
            temperature=data.get('temperature', 0),
            vibration=data.get('vibration', 0),
            power_consumption=data.get('power_consumption', 0),
            cycle_time=data.get('cycle_time', 0),
            parts_completed=data.get('parts_completed', 0),
            efficiency=data.get('efficiency', 0)
        )
        
        # 이상 상태 확인
        self._check_anomalies(machine_id)
    
    def _process_sensor_data(self, machine_id: str, sensor_type: str, data: Dict):
        """센서 데이터 처리"""
        sensor_data = SensorData(
            timestamp=datetime.now(),
            machine_id=machine_id,
            sensor_type=sensor_type,
            value=data.get('value', 0),
            unit=data.get('unit', ''),
            status='normal'
        )
        
        # 임계값 확인
        if sensor_type in self.thresholds:
            if sensor_data.value >= self.thresholds[sensor_type]['critical']:
                sensor_data.status = 'critical'
            elif sensor_data.value >= self.thresholds[sensor_type]['warning']:
                sensor_data.status = 'warning'
        
        # 버퍼에 저장
        self.sensor_data_buffer.append(sensor_data)
        
        # 버퍼 크기 관리
        if len(self.sensor_data_buffer) > self.monitoring_config['buffer_size']:
            self.sensor_data_buffer.pop(0)
    
    def _process_alert(self, machine_id: str, data: Dict):
        """알림 처리"""
        alert = {
            'timestamp': datetime.now(),
            'machine_id': machine_id,
            'type': data.get('type', 'unknown'),
            'severity': data.get('severity', 'info'),
            'message': data.get('message', ''),
            'acknowledged': False
        }
        
        self.alert_history.append(alert)
        
        # 중요 알림은 즉시 처리
        if alert['severity'] in ['critical', 'error']:
            logger.warning(f"중요 알림: {machine_id} - {alert['message']}")
    
    def _update_production_data(self, machine_id: str, data: Dict):
        """생산 데이터 업데이트"""
        if machine_id in self.machine_status:
            status = self.machine_status[machine_id]
            status.parts_completed = data.get('parts_completed', status.parts_completed)
            status.cycle_time = data.get('cycle_time', status.cycle_time)
            status.efficiency = data.get('efficiency', status.efficiency)
    
    def _check_anomalies(self, machine_id: str):
        """이상 상태 감지"""
        if machine_id not in self.machine_status:
            return
        
        status = self.machine_status[machine_id]
        anomalies = []
        
        # 온도 이상
        if status.temperature > self.thresholds['temperature']['critical']:
            anomalies.append({
                'type': 'temperature',
                'severity': 'critical',
                'message': f'온도 이상: {status.temperature}°C'
            })
        
        # 진동 이상
        if status.vibration > self.thresholds['vibration']['critical']:
            anomalies.append({
                'type': 'vibration',
                'severity': 'critical',
                'message': f'진동 이상: {status.vibration}mm/s'
            })
        
        # 스핀들 속도 편차
        if status.current_operation == 'cutting' and status.spindle_speed == 0:
            anomalies.append({
                'type': 'spindle',
                'severity': 'error',
                'message': '가공 중 스핀들 정지'
            })
        
        # 알림 생성
        for anomaly in anomalies:
            self._process_alert(machine_id, anomaly)
    
    async def start_websocket_server(self, host: str = "localhost", port: int = 8765):
        """WebSocket 서버 시작"""
        if not WEBSOCKET_AVAILABLE:
            logger.error("WebSocket 라이브러리가 설치되지 않았습니다. pip install websockets")
            return
        
        async def handle_client(websocket, path):
            """클라이언트 처리"""
            self.connected_clients.add(websocket)
            logger.info(f"WebSocket 클라이언트 연결: {websocket.remote_address}")
            
            try:
                # 초기 데이터 전송
                await websocket.send(json.dumps({
                    'type': 'initial',
                    'machines': self._get_all_machine_status(),
                    'recent_alerts': self._get_recent_alerts()
                }))
                
                # 연결 유지
                async for message in websocket:
                    # 클라이언트 요청 처리
                    data = json.loads(message)
                    response = await self._handle_client_request(data)
                    await websocket.send(json.dumps(response))
                    
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.connected_clients.remove(websocket)
                logger.info(f"WebSocket 클라이언트 연결 해제: {websocket.remote_address}")
        
        self.websocket_server = await websockets.serve(handle_client, host, port)
        logger.info(f"WebSocket 서버 시작: ws://{host}:{port}")
    
    async def _broadcast_update(self, data: Dict):
        """모든 클라이언트에 업데이트 전송"""
        if self.connected_clients:
            message = json.dumps(data)
            await asyncio.gather(
                *[client.send(message) for client in self.connected_clients],
                return_exceptions=True
            )
    
    async def _handle_client_request(self, request: Dict) -> Dict:
        """클라이언트 요청 처리"""
        request_type = request.get('type')
        
        if request_type == 'get_history':
            machine_id = request.get('machine_id')
            hours = request.get('hours', 1)
            return {
                'type': 'history',
                'data': self._get_sensor_history(machine_id, hours)
            }
        
        elif request_type == 'acknowledge_alert':
            alert_id = request.get('alert_id')
            return {
                'type': 'alert_acknowledged',
                'success': self._acknowledge_alert(alert_id)
            }
        
        elif request_type == 'get_analytics':
            return {
                'type': 'analytics',
                'data': self._get_analytics()
            }
        
        return {'type': 'error', 'message': 'Unknown request type'}
    
    def _get_all_machine_status(self) -> List[Dict]:
        """모든 기계 상태 조회"""
        return [
            {
                'machine_id': status.machine_id,
                'status': status.status,
                'operation': status.current_operation,
                'efficiency': status.efficiency,
                'temperature': status.temperature,
                'vibration': status.vibration,
                'parts_completed': status.parts_completed
            }
            for status in self.machine_status.values()
        ]
    
    def _get_recent_alerts(self, limit: int = 20) -> List[Dict]:
        """최근 알림 조회"""
        return [
            {
                'timestamp': alert['timestamp'].isoformat(),
                'machine_id': alert['machine_id'],
                'type': alert['type'],
                'severity': alert['severity'],
                'message': alert['message'],
                'acknowledged': alert['acknowledged']
            }
            for alert in self.alert_history[-limit:]
        ]
    
    def _get_sensor_history(self, machine_id: str, hours: int) -> List[Dict]:
        """센서 이력 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            {
                'timestamp': data.timestamp.isoformat(),
                'sensor_type': data.sensor_type,
                'value': data.value,
                'unit': data.unit,
                'status': data.status
            }
            for data in self.sensor_data_buffer
            if data.machine_id == machine_id and data.timestamp >= cutoff_time
        ]
    
    def _acknowledge_alert(self, alert_id: str) -> bool:
        """알림 확인 처리"""
        # 실제로는 alert_id로 찾아야 하지만, 간단히 구현
        for alert in self.alert_history:
            if not alert['acknowledged']:
                alert['acknowledged'] = True
                return True
        return False
    
    def _get_analytics(self) -> Dict:
        """분석 데이터 생성"""
        if not self.machine_status:
            return {}
        
        # 전체 효율성
        efficiencies = [s.efficiency for s in self.machine_status.values()]
        avg_efficiency = np.mean(efficiencies) if efficiencies else 0
        
        # 가동률
        running_machines = sum(1 for s in self.machine_status.values() if s.status == 'running')
        total_machines = len(self.machine_status)
        utilization = (running_machines / total_machines * 100) if total_machines > 0 else 0
        
        # 생산량
        total_parts = sum(s.parts_completed for s in self.machine_status.values())
        
        # 알림 통계
        alert_counts = {'info': 0, 'warning': 0, 'error': 0, 'critical': 0}
        for alert in self.alert_history[-100:]:  # 최근 100개
            severity = alert['severity']
            if severity in alert_counts:
                alert_counts[severity] += 1
        
        return {
            'average_efficiency': round(avg_efficiency, 1),
            'utilization_rate': round(utilization, 1),
            'total_parts_today': total_parts,
            'running_machines': running_machines,
            'total_machines': total_machines,
            'alert_summary': alert_counts
        }
    
    def simulate_sensor_data(self, machine_id: str):
        """센서 데이터 시뮬레이션 (테스트용)"""
        import random
        
        # 기계 상태 시뮬레이션
        status_data = {
            'status': random.choice(['idle', 'running', 'running', 'running']),
            'operation': random.choice(['cutting', 'drilling', 'milling']),
            'spindle_speed': random.randint(1000, 3000),
            'feed_rate': random.uniform(100, 500),
            'tool_number': random.randint(1, 20),
            'coolant_flow': random.uniform(10, 30),
            'temperature': random.uniform(20, 70),
            'vibration': random.uniform(0, 6),
            'power_consumption': random.uniform(30, 90),
            'cycle_time': random.uniform(60, 300),
            'parts_completed': random.randint(0, 100),
            'efficiency': random.uniform(70, 95)
        }
        
        # 가끔 이상 상태 생성
        if random.random() < 0.1:
            status_data['temperature'] = random.uniform(75, 85)
        if random.random() < 0.05:
            status_data['vibration'] = random.uniform(7, 10)
        
        # MQTT 메시지처럼 처리
        self._update_machine_status(machine_id, status_data)
        
        # 센서 데이터 시뮬레이션
        sensors = ['temperature', 'vibration', 'pressure', 'current']
        for sensor in sensors:
            sensor_data = {
                'value': status_data.get(sensor, random.uniform(0, 100)),
                'unit': {'temperature': '°C', 'vibration': 'mm/s', 
                        'pressure': 'bar', 'current': 'A'}.get(sensor, '')
            }
            self._process_sensor_data(machine_id, sensor, sensor_data)
    
    def get_dashboard_data(self) -> Dict:
        """대시보드용 데이터 조회"""
        return {
            'machines': self._get_all_machine_status(),
            'alerts': self._get_recent_alerts(),
            'analytics': self._get_analytics(),
            'sensor_trends': self._get_sensor_trends()
        }
    
    def _get_sensor_trends(self) -> Dict:
        """센서 트렌드 데이터"""
        trends = {}
        
        # 최근 1시간 데이터로 트렌드 생성
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_data = [d for d in self.sensor_data_buffer if d.timestamp >= cutoff_time]
        
        if recent_data:
            df = pd.DataFrame([
                {
                    'timestamp': d.timestamp,
                    'machine_id': d.machine_id,
                    'sensor_type': d.sensor_type,
                    'value': d.value
                }
                for d in recent_data
            ])
            
            # 기계별, 센서별 평균
            for machine_id in df['machine_id'].unique():
                machine_data = df[df['machine_id'] == machine_id]
                trends[machine_id] = {}
                
                for sensor_type in machine_data['sensor_type'].unique():
                    sensor_data = machine_data[machine_data['sensor_type'] == sensor_type]
                    trends[machine_id][sensor_type] = {
                        'avg': sensor_data['value'].mean(),
                        'min': sensor_data['value'].min(),
                        'max': sensor_data['value'].max(),
                        'count': len(sensor_data)
                    } 