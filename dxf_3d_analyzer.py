#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 3D 분석기 - 3D 엔티티 전문 분석 모듈
Author: 3D CAD Expert
Version: 2.0.0
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class DXF3DAnalyzer:
    """3D DXF 엔티티 분석 클래스"""
    
    def __init__(self):
        """초기화"""
        self.solids = []
        self.surfaces = []
        self.meshes = []
        self.splines = []
        self.regions = []
        self.bodies = []
        self.z_range = {'min': None, 'max': None}
        self.volume_info = {}
        self.is_3d_drawing = False
        
    def analyze_3d_entities(self, msp, analyzer_data: Dict) -> Dict:
        """3D 엔티티 분석"""
        try:
            # 3D 엔티티 수집
            entity_counts = defaultdict(int)
            
            for entity in msp:
                entity_type = entity.dxftype()
                
                # 3D 전용 엔티티 처리
                if entity_type == '3DSOLID':
                    self._process_3d_solid(entity)
                    entity_counts['3DSOLID'] += 1
                    
                elif entity_type == 'SURFACE':
                    self._process_surface(entity)
                    entity_counts['SURFACE'] += 1
                    
                elif entity_type == 'MESH':
                    self._process_mesh(entity)
                    entity_counts['MESH'] += 1
                    
                elif entity_type == 'SPLINE':
                    self._process_spline(entity)
                    entity_counts['SPLINE'] += 1
                    
                elif entity_type == 'REGION':
                    self._process_region(entity)
                    entity_counts['REGION'] += 1
                    
                elif entity_type == 'BODY':
                    self._process_body(entity)
                    entity_counts['BODY'] += 1
                
                # 2D 엔티티의 3D 정보 확인
                elif hasattr(entity.dxf, 'elevation') or hasattr(entity.dxf, 'thickness'):
                    self._check_2d_entity_3d_info(entity)
            
            # 3D 여부 판단
            self.is_3d_drawing = self._determine_if_3d()
            
            # 3D 분석 결과 생성
            analysis_result = {
                'is_3d': self.is_3d_drawing,
                '3d_entity_count': len(self.solids) + len(self.surfaces) + len(self.meshes),
                'solids': self._analyze_solids(),
                'surfaces': self._analyze_surfaces(),
                'meshes': self._analyze_meshes(),
                'z_range': self.z_range,
                'volume_info': self._calculate_volumes(),
                'spatial_metrics': self._calculate_spatial_metrics(),
                '3d_entity_breakdown': dict(entity_counts)
            }
            
            # 기존 분석 데이터에 3D 정보 추가
            analyzer_data['3d_analysis'] = analysis_result
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"3D 엔티티 분석 중 오류: {e}")
            return {'is_3d': False, 'error': str(e)}
    
    def _process_3d_solid(self, entity):
        """3D 솔리드 처리"""
        try:
            solid_info = {
                'type': '3DSOLID',
                'layer': entity.dxf.layer,
                'handle': entity.dxf.handle,
                'properties': {}
            }
            
            # ACIS 데이터가 있는 경우
            if hasattr(entity, 'acis_data'):
                solid_info['has_acis_data'] = True
                
            self.solids.append(solid_info)
            
        except Exception as e:
            logger.warning(f"3D 솔리드 처리 중 오류: {e}")
    
    def _process_surface(self, entity):
        """서피스 처리"""
        try:
            surface_info = {
                'type': entity.dxftype(),
                'layer': entity.dxf.layer,
                'u_degree': getattr(entity.dxf, 'u_degree', None),
                'v_degree': getattr(entity.dxf, 'v_degree', None)
            }
            
            self.surfaces.append(surface_info)
            
        except Exception as e:
            logger.warning(f"서피스 처리 중 오류: {e}")
    
    def _process_mesh(self, entity):
        """메시 처리"""
        try:
            vertices = []
            faces = []
            
            # 메시 정점 수집
            if hasattr(entity, 'vertices'):
                vertices = list(entity.vertices)
            
            # 메시 면 수집
            if hasattr(entity, 'faces'):
                faces = list(entity.faces)
            
            mesh_info = {
                'type': 'MESH',
                'layer': entity.dxf.layer,
                'vertex_count': len(vertices),
                'face_count': len(faces),
                'is_closed': getattr(entity.dxf, 'is_closed', False)
            }
            
            # Z 범위 업데이트
            for vertex in vertices:
                if len(vertex) >= 3:
                    self._update_z_range(vertex[2])
            
            self.meshes.append(mesh_info)
            
        except Exception as e:
            logger.warning(f"메시 처리 중 오류: {e}")
    
    def _process_spline(self, entity):
        """스플라인 처리"""
        try:
            control_points = []
            if hasattr(entity, 'control_points'):
                control_points = list(entity.control_points)
            
            spline_info = {
                'type': 'SPLINE',
                'layer': entity.dxf.layer,
                'degree': getattr(entity.dxf, 'degree', 3),
                'control_point_count': len(control_points),
                'is_closed': getattr(entity.dxf, 'closed', False),
                'is_periodic': getattr(entity.dxf, 'periodic', False)
            }
            
            # 3D 스플라인인지 확인
            is_3d = False
            for point in control_points:
                if len(point) >= 3 and point[2] != 0:
                    is_3d = True
                    self._update_z_range(point[2])
            
            spline_info['is_3d'] = is_3d
            self.splines.append(spline_info)
            
        except Exception as e:
            logger.warning(f"스플라인 처리 중 오류: {e}")
    
    def _process_region(self, entity):
        """리전 처리"""
        try:
            region_info = {
                'type': 'REGION',
                'layer': entity.dxf.layer,
                'handle': entity.dxf.handle
            }
            
            self.regions.append(region_info)
            
        except Exception as e:
            logger.warning(f"리전 처리 중 오류: {e}")
    
    def _process_body(self, entity):
        """바디 처리"""
        try:
            body_info = {
                'type': 'BODY',
                'layer': entity.dxf.layer,
                'handle': entity.dxf.handle
            }
            
            self.bodies.append(body_info)
            
        except Exception as e:
            logger.warning(f"바디 처리 중 오류: {e}")
    
    def _check_2d_entity_3d_info(self, entity):
        """2D 엔티티의 3D 정보 확인"""
        try:
            # Elevation 확인
            if hasattr(entity.dxf, 'elevation'):
                elevation = entity.dxf.elevation
                if elevation != 0:
                    self._update_z_range(elevation)
                    self.is_3d_drawing = True
            
            # Thickness 확인
            if hasattr(entity.dxf, 'thickness'):
                thickness = entity.dxf.thickness
                if thickness != 0:
                    self.is_3d_drawing = True
            
            # 3D 좌표 확인
            if hasattr(entity.dxf, 'start') and hasattr(entity.dxf.start, 'z'):
                z = entity.dxf.start.z
                if z != 0:
                    self._update_z_range(z)
                    self.is_3d_drawing = True
                    
            if hasattr(entity.dxf, 'end') and hasattr(entity.dxf.end, 'z'):
                z = entity.dxf.end.z
                if z != 0:
                    self._update_z_range(z)
                    self.is_3d_drawing = True
                    
        except Exception as e:
            logger.debug(f"2D 엔티티 3D 정보 확인 중 오류: {e}")
    
    def _update_z_range(self, z_value):
        """Z 범위 업데이트"""
        if z_value is None:
            return
            
        if self.z_range['min'] is None or z_value < self.z_range['min']:
            self.z_range['min'] = z_value
            
        if self.z_range['max'] is None or z_value > self.z_range['max']:
            self.z_range['max'] = z_value
    
    def _determine_if_3d(self) -> bool:
        """3D 도면 여부 판단"""
        # 3D 전용 엔티티가 있는 경우
        if self.solids or self.surfaces or self.meshes:
            return True
        
        # 3D 스플라인이 있는 경우
        if any(spline.get('is_3d', False) for spline in self.splines):
            return True
        
        # Z 범위가 0이 아닌 경우
        if (self.z_range['min'] is not None and 
            self.z_range['max'] is not None and 
            self.z_range['min'] != self.z_range['max']):
            return True
        
        return self.is_3d_drawing
    
    def _analyze_solids(self) -> Dict:
        """솔리드 분석"""
        if not self.solids:
            return {'count': 0}
        
        return {
            'count': len(self.solids),
            'layers': list(set(s['layer'] for s in self.solids)),
            'has_acis_data': sum(1 for s in self.solids if s.get('has_acis_data', False))
        }
    
    def _analyze_surfaces(self) -> Dict:
        """서피스 분석"""
        if not self.surfaces:
            return {'count': 0}
        
        return {
            'count': len(self.surfaces),
            'types': list(set(s['type'] for s in self.surfaces)),
            'layers': list(set(s['layer'] for s in self.surfaces))
        }
    
    def _analyze_meshes(self) -> Dict:
        """메시 분석"""
        if not self.meshes:
            return {'count': 0}
        
        total_vertices = sum(m['vertex_count'] for m in self.meshes)
        total_faces = sum(m['face_count'] for m in self.meshes)
        
        return {
            'count': len(self.meshes),
            'total_vertices': total_vertices,
            'total_faces': total_faces,
            'avg_vertices_per_mesh': total_vertices / len(self.meshes) if self.meshes else 0,
            'closed_meshes': sum(1 for m in self.meshes if m.get('is_closed', False))
        }
    
    def _calculate_volumes(self) -> Dict:
        """부피 계산 (추정)"""
        if not self.is_3d_drawing:
            return {'estimated': False}
        
        # Z 범위 기반 추정
        z_height = 0
        if self.z_range['min'] is not None and self.z_range['max'] is not None:
            z_height = abs(self.z_range['max'] - self.z_range['min'])
        
        return {
            'estimated': True,
            'z_height': z_height,
            'solid_count': len(self.solids),
            'note': '정확한 부피 계산을 위해서는 전문 CAD 소프트웨어가 필요합니다.'
        }
    
    def _calculate_spatial_metrics(self) -> Dict:
        """공간 메트릭 계산"""
        metrics = {
            'is_3d': self.is_3d_drawing,
            'z_range': self.z_range,
            '3d_complexity': self._calculate_3d_complexity()
        }
        
        if self.is_3d_drawing and self.z_range['min'] is not None:
            metrics['z_span'] = abs(self.z_range['max'] - self.z_range['min'])
            
        return metrics
    
    def _calculate_3d_complexity(self) -> str:
        """3D 복잡도 계산"""
        score = 0
        
        # 3D 엔티티 종류별 가중치
        score += len(self.solids) * 10
        score += len(self.surfaces) * 8
        score += len(self.meshes) * 6
        score += len([s for s in self.splines if s.get('is_3d', False)]) * 4
        
        if score == 0:
            return "2D 도면"
        elif score < 10:
            return "단순 3D"
        elif score < 50:
            return "보통 3D"
        elif score < 100:
            return "복잡 3D"
        else:
            return "매우 복잡한 3D"
    
    def generate_3d_report(self, analysis_result: Dict) -> str:
        """3D 분석 리포트 생성"""
        report = "\n## 🧊 3D 분석\n\n"
        
        if not analysis_result.get('is_3d', False):
            report += "이 도면은 2D 도면입니다.\n"
            return report
        
        report += f"**3D 도면 확인됨**\n\n"
        
        # 3D 엔티티 요약
        report += "### 3D 엔티티 요약\n"
        report += f"- 전체 3D 엔티티: {analysis_result.get('3d_entity_count', 0)}개\n"
        
        if analysis_result.get('solids', {}).get('count', 0) > 0:
            report += f"- 3D 솔리드: {analysis_result['solids']['count']}개\n"
            
        if analysis_result.get('surfaces', {}).get('count', 0) > 0:
            report += f"- 서피스: {analysis_result['surfaces']['count']}개\n"
            
        if analysis_result.get('meshes', {}).get('count', 0) > 0:
            meshes = analysis_result['meshes']
            report += f"- 메시: {meshes['count']}개 (정점: {meshes['total_vertices']:,}, 면: {meshes['total_faces']:,})\n"
        
        # 공간 정보
        report += "\n### 공간 정보\n"
        z_range = analysis_result.get('z_range', {})
        if z_range.get('min') is not None:
            report += f"- Z축 범위: {z_range['min']:.3f} ~ {z_range['max']:.3f}\n"
            report += f"- Z축 높이: {abs(z_range['max'] - z_range['min']):.3f}\n"
        
        # 복잡도
        spatial = analysis_result.get('spatial_metrics', {})
        report += f"- 3D 복잡도: {spatial.get('3d_complexity', '알 수 없음')}\n"
        
        return report 