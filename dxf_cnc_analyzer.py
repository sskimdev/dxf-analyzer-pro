#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF CNC 가공성 분석 모듈
Author: CNC Expert
Version: 1.0.0
"""

import math
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import numpy as np
import ezdxf
from ezdxf.entities import Line, Circle, Arc, LWPolyline, Spline

logger = logging.getLogger(__name__)


@dataclass
class ToolRecommendation:
    """공구 추천 정보"""
    tool_type: str
    diameter: float
    material: str
    coating: str
    cutting_speed: float
    feed_rate: float
    depth_of_cut: float
    reason: str


@dataclass
class MachinabilityScore:
    """가공성 점수"""
    overall_score: float  # 0-100
    complexity_score: float
    tool_access_score: float
    tolerance_score: float
    surface_finish_score: float
    material_removal_score: float
    grade: str  # A-F


class DXFCNCAnalyzer:
    """DXF CNC 가공성 분석기"""
    
    def __init__(self):
        """초기화"""
        # 표준 공구 라이브러리
        self.tool_library = self._init_tool_library()
        
        # 재료별 가공 파라미터
        self.material_params = self._init_material_params()
        
        # 가공 복잡도 가중치
        self.complexity_weights = {
            'small_radius': 2.0,
            'deep_pocket': 1.5,
            'thin_wall': 1.8,
            'tight_tolerance': 1.6,
            'complex_contour': 1.4
        }
    
    def analyze_machinability(self, dxf_file: str, material: str = 'aluminum') -> Dict:
        """가공성 종합 분석"""
        try:
            doc = ezdxf.readfile(dxf_file)
            msp = doc.modelspace()
            
            # 기본 형상 분석
            geometry_analysis = self._analyze_geometry(msp)
            
            # 가공성 점수 계산
            machinability_score = self._calculate_machinability_score(
                geometry_analysis, material
            )
            
            # 공구 추천
            tool_recommendations = self._recommend_tools(
                geometry_analysis, material
            )
            
            # 가공 시간 예측
            machining_time = self._estimate_machining_time(
                geometry_analysis, material, tool_recommendations
            )
            
            # 공구 경로 최적화 제안
            toolpath_optimization = self._analyze_toolpath_optimization(
                geometry_analysis
            )
            
            # 잠재적 문제점 분석
            potential_issues = self._identify_machining_issues(
                geometry_analysis, material
            )
            
            return {
                'material': material,
                'geometry_analysis': geometry_analysis,
                'machinability_score': machinability_score,
                'tool_recommendations': tool_recommendations,
                'machining_time': machining_time,
                'toolpath_optimization': toolpath_optimization,
                'potential_issues': potential_issues,
                'cost_factors': self._calculate_cost_factors(
                    machining_time, tool_recommendations, material
                )
            }
            
        except Exception as e:
            logger.error(f"CNC 분석 중 오류: {e}")
            return {'error': str(e)}
    
    def _analyze_geometry(self, modelspace) -> Dict:
        """형상 분석"""
        analysis = {
            'total_entities': 0,
            'contours': [],
            'pockets': [],
            'holes': [],
            'min_radius': float('inf'),
            'max_depth': 0,
            'min_wall_thickness': float('inf'),
            'total_cut_length': 0,
            'bounding_box': None,
            'complexity_features': []
        }
        
        # 엔티티 분석
        for entity in modelspace:
            analysis['total_entities'] += 1
            
            if entity.dxftype() == 'CIRCLE':
                # 원/구멍 분석
                radius = entity.dxf.radius if hasattr(entity.dxf, 'radius') else 0
                center = entity.dxf.center if hasattr(entity.dxf, 'center') else (0, 0)
                
                analysis['holes'].append({
                    'center': center,
                    'radius': radius,
                    'diameter': radius * 2
                })
                
                if radius < analysis['min_radius']:
                    analysis['min_radius'] = radius
                    
            elif entity.dxftype() == 'ARC':
                # 호 분석
                radius = entity.dxf.radius if hasattr(entity.dxf, 'radius') else 0
                if radius < analysis['min_radius']:
                    analysis['min_radius'] = radius
                    
                # 호 길이 계산
                start_angle = entity.dxf.start_angle if hasattr(entity.dxf, 'start_angle') else 0
                end_angle = entity.dxf.end_angle if hasattr(entity.dxf, 'end_angle') else 0
                arc_length = radius * math.radians(abs(end_angle - start_angle))
                analysis['total_cut_length'] += arc_length
                
            elif entity.dxftype() == 'LINE':
                # 직선 길이
                start = entity.dxf.start if hasattr(entity.dxf, 'start') else (0, 0, 0)
                end = entity.dxf.end if hasattr(entity.dxf, 'end') else (0, 0, 0)
                length = math.sqrt(sum((e - s)**2 for s, e in zip(start, end)))
                analysis['total_cut_length'] += length
                
            elif entity.dxftype() == 'LWPOLYLINE':
                # 폴리라인 분석
                if hasattr(entity, 'get_points'):
                    points = list(entity.get_points())
                    if len(points) > 2:
                        # 폐곡선인지 확인
                        if entity.is_closed:
                            analysis['contours'].append({
                                'type': 'closed_polyline',
                                'points': points,
                                'area': self._calculate_polygon_area(points)
                            })
                        
                        # 전체 길이 계산
                        for i in range(len(points) - 1):
                            length = math.sqrt(
                                (points[i+1][0] - points[i][0])**2 + 
                                (points[i+1][1] - points[i][1])**2
                            )
                            analysis['total_cut_length'] += length
        
        # 복잡도 특징 분석
        if analysis['min_radius'] < 1.0:
            analysis['complexity_features'].append('small_radius_corners')
            
        if len(analysis['holes']) > 20:
            analysis['complexity_features'].append('many_holes')
            
        if analysis['total_cut_length'] > 1000:
            analysis['complexity_features'].append('long_cutting_path')
        
        return analysis
    
    def _calculate_machinability_score(self, geometry: Dict, material: str) -> MachinabilityScore:
        """가공성 점수 계산"""
        # 각 항목별 점수 (0-100)
        complexity_score = self._score_complexity(geometry)
        tool_access_score = self._score_tool_access(geometry)
        tolerance_score = self._score_tolerance_feasibility(geometry)
        surface_finish_score = self._score_surface_finish(geometry)
        material_removal_score = self._score_material_removal(geometry, material)
        
        # 가중 평균
        weights = {
            'complexity': 0.25,
            'tool_access': 0.25,
            'tolerance': 0.20,
            'surface_finish': 0.15,
            'material_removal': 0.15
        }
        
        overall_score = (
            complexity_score * weights['complexity'] +
            tool_access_score * weights['tool_access'] +
            tolerance_score * weights['tolerance'] +
            surface_finish_score * weights['surface_finish'] +
            material_removal_score * weights['material_removal']
        )
        
        # 등급 결정
        if overall_score >= 90:
            grade = 'A'
        elif overall_score >= 80:
            grade = 'B'
        elif overall_score >= 70:
            grade = 'C'
        elif overall_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return MachinabilityScore(
            overall_score=overall_score,
            complexity_score=complexity_score,
            tool_access_score=tool_access_score,
            tolerance_score=tolerance_score,
            surface_finish_score=surface_finish_score,
            material_removal_score=material_removal_score,
            grade=grade
        )
    
    def _recommend_tools(self, geometry: Dict, material: str) -> List[ToolRecommendation]:
        """공구 추천"""
        recommendations = []
        
        # 재료별 기본 공구 추천
        material_tools = self.tool_library.get(material, self.tool_library['aluminum'])
        
        # 윤곽 가공용 엔드밀
        if geometry['contours']:
            recommendations.append(ToolRecommendation(
                tool_type='End Mill',
                diameter=6.0,
                material='Carbide',
                coating='TiAlN',
                cutting_speed=material_tools['cutting_speed'],
                feed_rate=material_tools['feed_rate'],
                depth_of_cut=2.0,
                reason='윤곽 가공 및 포켓 가공용'
            ))
        
        # 구멍 가공용 드릴
        if geometry['holes']:
            hole_diameters = sorted(set(h['diameter'] for h in geometry['holes']))
            for diameter in hole_diameters[:3]:  # 상위 3개 크기만
                recommendations.append(ToolRecommendation(
                    tool_type='Drill',
                    diameter=diameter,
                    material='HSS-Co',
                    coating='TiN',
                    cutting_speed=material_tools['drilling_speed'],
                    feed_rate=material_tools['drilling_feed'],
                    depth_of_cut=diameter * 0.5,
                    reason=f'{diameter}mm 구멍 가공용'
                ))
        
        # 작은 반경용 볼엔드밀
        if geometry['min_radius'] < 3.0:
            recommendations.append(ToolRecommendation(
                tool_type='Ball End Mill',
                diameter=geometry['min_radius'] * 1.5,
                material='Carbide',
                coating='DLC',
                cutting_speed=material_tools['cutting_speed'] * 0.8,
                feed_rate=material_tools['feed_rate'] * 0.6,
                depth_of_cut=geometry['min_radius'] * 0.3,
                reason='작은 반경 코너 가공용'
            ))
        
        return recommendations
    
    def _estimate_machining_time(self, geometry: Dict, material: str, 
                                tools: List[ToolRecommendation]) -> Dict:
        """가공 시간 예측"""
        material_factor = self.material_params[material]['machinability_factor']
        
        # 절삭 시간 계산
        cutting_time = 0
        if tools:
            avg_feed_rate = sum(t.feed_rate for t in tools) / len(tools)
            cutting_time = (geometry['total_cut_length'] / avg_feed_rate) * material_factor
        
        # 공구 교환 시간
        tool_change_time = len(tools) * 1.5  # 1.5분/공구
        
        # 설정 시간
        setup_time = 15.0  # 기본 15분
        if 'complex_contour' in geometry['complexity_features']:
            setup_time += 10.0
        
        # 구멍 가공 시간
        drilling_time = 0
        if geometry['holes']:
            drilling_time = len(geometry['holes']) * 0.5 * material_factor
        
        total_time = cutting_time + tool_change_time + setup_time + drilling_time
        
        return {
            'total_minutes': round(total_time, 1),
            'cutting_time': round(cutting_time, 1),
            'drilling_time': round(drilling_time, 1),
            'tool_change_time': round(tool_change_time, 1),
            'setup_time': round(setup_time, 1),
            'efficiency_tips': self._get_efficiency_tips(geometry, tools)
        }
    
    def _analyze_toolpath_optimization(self, geometry: Dict) -> Dict:
        """공구 경로 최적화 분석"""
        optimization = {
            'current_efficiency': 0,
            'optimization_potential': 0,
            'recommendations': []
        }
        
        # 현재 효율성 평가
        if geometry['total_cut_length'] > 0:
            # 바운딩 박스 대비 실제 절삭 경로 비율
            optimization['current_efficiency'] = 75  # 기본값
            
            # 최적화 가능성
            if len(geometry['holes']) > 10:
                optimization['optimization_potential'] = 20
                optimization['recommendations'].append(
                    '구멍 가공 순서 최적화로 이동 시간 20% 단축 가능'
                )
            
            if 'many_holes' in geometry['complexity_features']:
                optimization['recommendations'].append(
                    '페킹(Pecking) 드릴링 사이클 사용 권장'
                )
            
            if geometry['contours']:
                optimization['recommendations'].append(
                    '적응형 클리어링(Adaptive Clearing) 전략으로 공구 수명 연장'
                )
        
        return optimization
    
    def _identify_machining_issues(self, geometry: Dict, material: str) -> List[Dict]:
        """잠재적 가공 문제점 식별"""
        issues = []
        
        # 작은 반경 문제
        if geometry['min_radius'] < 0.5:
            issues.append({
                'type': 'small_radius',
                'severity': 'high',
                'description': f'최소 반경 {geometry["min_radius"]}mm - 특수 공구 필요',
                'solution': '와이어 EDM 또는 마이크로 엔드밀 사용 검토'
            })
        
        # 얇은 벽 문제
        if geometry.get('min_wall_thickness', float('inf')) < 1.0:
            issues.append({
                'type': 'thin_wall',
                'severity': 'medium',
                'description': '얇은 벽 구조로 진동 및 변형 위험',
                'solution': '저속 가공 및 다단계 절삭 적용'
            })
        
        # 깊은 포켓
        if geometry.get('max_depth', 0) > 50:
            issues.append({
                'type': 'deep_pocket',
                'severity': 'medium',
                'description': '깊은 포켓으로 칩 배출 어려움',
                'solution': '헬리컬 가공 및 충분한 절삭유 공급'
            })
        
        # 재료별 특수 고려사항
        if material == 'stainless_steel':
            issues.append({
                'type': 'material_hardness',
                'severity': 'low',
                'description': '스테인리스강 가공 시 공구 마모 증가',
                'solution': '코팅 공구 사용 및 적절한 절삭 조건 유지'
            })
        
        return issues
    
    def _calculate_cost_factors(self, machining_time: Dict, 
                               tools: List[ToolRecommendation], 
                               material: str) -> Dict:
        """비용 요인 계산"""
        # 시간당 가공 비용 (단위: 원)
        machine_rate = 50000  # 시간당 5만원
        
        # 총 가공 시간 (시간)
        total_hours = machining_time['total_minutes'] / 60
        
        # 가공비
        machining_cost = total_hours * machine_rate
        
        # 공구 비용 (추정)
        tool_cost = len(tools) * 20000  # 공구당 평균 2만원
        
        # 재료 난이도 계수
        material_factor = self.material_params[material]['cost_factor']
        
        return {
            'machining_cost': round(machining_cost),
            'tool_cost': round(tool_cost),
            'material_factor': material_factor,
            'total_estimated_cost': round((machining_cost + tool_cost) * material_factor),
            'cost_breakdown': {
                'labor': round(machining_cost * 0.4),
                'machine': round(machining_cost * 0.6),
                'tooling': round(tool_cost),
                'overhead': round(machining_cost * 0.2)
            }
        }
    
    def _init_tool_library(self) -> Dict:
        """공구 라이브러리 초기화"""
        return {
            'aluminum': {
                'cutting_speed': 300,  # m/min
                'feed_rate': 0.15,    # mm/tooth
                'drilling_speed': 100,
                'drilling_feed': 0.1
            },
            'steel': {
                'cutting_speed': 150,
                'feed_rate': 0.1,
                'drilling_speed': 50,
                'drilling_feed': 0.08
            },
            'stainless_steel': {
                'cutting_speed': 80,
                'feed_rate': 0.08,
                'drilling_speed': 30,
                'drilling_feed': 0.06
            },
            'titanium': {
                'cutting_speed': 50,
                'feed_rate': 0.05,
                'drilling_speed': 20,
                'drilling_feed': 0.04
            }
        }
    
    def _init_material_params(self) -> Dict:
        """재료 파라미터 초기화"""
        return {
            'aluminum': {
                'machinability_factor': 1.0,
                'cost_factor': 1.0
            },
            'steel': {
                'machinability_factor': 1.5,
                'cost_factor': 1.3
            },
            'stainless_steel': {
                'machinability_factor': 2.0,
                'cost_factor': 1.6
            },
            'titanium': {
                'machinability_factor': 3.0,
                'cost_factor': 2.5
            }
        }
    
    def _calculate_polygon_area(self, points: List[Tuple]) -> float:
        """다각형 면적 계산"""
        n = len(points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        return abs(area) / 2.0
    
    def _score_complexity(self, geometry: Dict) -> float:
        """복잡도 점수"""
        score = 100.0
        
        # 복잡도 특징에 따라 감점
        for feature in geometry['complexity_features']:
            if feature in self.complexity_weights:
                score -= self.complexity_weights[feature] * 5
        
        return max(0, score)
    
    def _score_tool_access(self, geometry: Dict) -> float:
        """공구 접근성 점수"""
        score = 100.0
        
        # 작은 반경은 접근성 감소
        if geometry['min_radius'] < 1.0:
            score -= 30
        elif geometry['min_radius'] < 3.0:
            score -= 15
        
        return max(0, score)
    
    def _score_tolerance_feasibility(self, geometry: Dict) -> float:
        """공차 실현 가능성 점수"""
        # 기본적으로 높은 점수, 특수 조건에서 감점
        return 85.0
    
    def _score_surface_finish(self, geometry: Dict) -> float:
        """표면 조도 달성 가능성 점수"""
        return 90.0
    
    def _score_material_removal(self, geometry: Dict, material: str) -> float:
        """재료 제거율 점수"""
        base_score = 100.0
        
        # 재료에 따른 조정
        if material in ['titanium', 'stainless_steel']:
            base_score -= 20
        
        return base_score
    
    def _get_efficiency_tips(self, geometry: Dict, tools: List[ToolRecommendation]) -> List[str]:
        """효율성 향상 팁"""
        tips = []
        
        if len(geometry['holes']) > 20:
            tips.append('TSP 알고리즘으로 구멍 가공 순서 최적화')
        
        if geometry['total_cut_length'] > 500:
            tips.append('고속 가공(HSM) 전략 적용 검토')
        
        if len(tools) > 5:
            tips.append('자동 공구 교환장치(ATC) 활용')
        
        return tips
    
    def generate_cnc_report(self, analysis: Dict) -> str:
        """CNC 분석 리포트 생성"""
        report = "# 🏭 CNC 가공성 분석 리포트\n\n"
        
        if 'error' in analysis:
            report += f"⚠️ 오류: {analysis['error']}\n"
            return report
        
        # 재료 정보
        report += f"**분석 재료**: {analysis['material'].upper()}\n\n"
        
        # 가공성 점수
        score = analysis['machinability_score']
        report += f"## 📊 가공성 평가\n"
        report += f"- **종합 점수**: {score.overall_score:.1f}/100 (등급: {score.grade})\n"
        report += f"- **복잡도**: {score.complexity_score:.1f}/100\n"
        report += f"- **공구 접근성**: {score.tool_access_score:.1f}/100\n"
        report += f"- **공차 실현성**: {score.tolerance_score:.1f}/100\n"
        report += f"- **표면 조도**: {score.surface_finish_score:.1f}/100\n"
        report += f"- **재료 제거율**: {score.material_removal_score:.1f}/100\n\n"
        
        # 공구 추천
        report += "## 🔧 권장 공구\n"
        for tool in analysis['tool_recommendations']:
            report += f"\n### {tool.tool_type}\n"
            report += f"- **직경**: {tool.diameter}mm\n"
            report += f"- **재질**: {tool.material} ({tool.coating} 코팅)\n"
            report += f"- **절삭 속도**: {tool.cutting_speed} m/min\n"
            report += f"- **이송 속도**: {tool.feed_rate} mm/tooth\n"
            report += f"- **절삭 깊이**: {tool.depth_of_cut}mm\n"
            report += f"- **용도**: {tool.reason}\n"
        
        # 가공 시간
        time = analysis['machining_time']
        report += f"\n## ⏱️ 예상 가공 시간\n"
        report += f"- **총 시간**: {time['total_minutes']}분\n"
        report += f"- **절삭 시간**: {time['cutting_time']}분\n"
        report += f"- **드릴링 시간**: {time['drilling_time']}분\n"
        report += f"- **공구 교환**: {time['tool_change_time']}분\n"
        report += f"- **설정 시간**: {time['setup_time']}분\n"
        
        if time['efficiency_tips']:
            report += "\n### 💡 효율성 향상 팁\n"
            for tip in time['efficiency_tips']:
                report += f"- {tip}\n"
        
        # 공구 경로 최적화
        opt = analysis['toolpath_optimization']
        report += f"\n## 🛤️ 공구 경로 최적화\n"
        report += f"- **현재 효율성**: {opt['current_efficiency']}%\n"
        report += f"- **최적화 가능성**: {opt['optimization_potential']}%\n"
        
        if opt['recommendations']:
            report += "\n### 최적화 제안\n"
            for rec in opt['recommendations']:
                report += f"- {rec}\n"
        
        # 잠재적 문제점
        if analysis['potential_issues']:
            report += "\n## ⚠️ 주의사항\n"
            for issue in analysis['potential_issues']:
                severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                icon = severity_icon.get(issue['severity'], '⚪')
                report += f"\n### {icon} {issue['type'].replace('_', ' ').title()}\n"
                report += f"- **설명**: {issue['description']}\n"
                report += f"- **해결책**: {issue['solution']}\n"
        
        # 비용 요인
        cost = analysis['cost_factors']
        report += f"\n## 💰 예상 비용\n"
        report += f"- **가공비**: {cost['machining_cost']:,}원\n"
        report += f"- **공구비**: {cost['tool_cost']:,}원\n"
        report += f"- **재료 난이도 계수**: {cost['material_factor']}x\n"
        report += f"- **총 예상 비용**: {cost['total_estimated_cost']:,}원\n"
        
        return report 