#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 자동 수정 모듈 - 간단한 문제 자동 수정
Author: CAD AutoFix Expert
Version: 2.0.0
"""

import ezdxf
from typing import Dict, List, Tuple, Any
import logging
from pathlib import Path
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class DXFAutoFix:
    """DXF 파일 자동 수정 클래스"""
    
    def __init__(self):
        """초기화"""
        self.doc = None
        self.fixes_applied = []
        self.backup_created = False
        
    def load_file(self, file_path: str):
        """DXF 파일 로드"""
        try:
            self.doc = ezdxf.readfile(file_path)
            logger.info(f"DXF 파일 로드 완료: {file_path}")
            return True
        except Exception as e:
            logger.error(f"DXF 파일 로드 실패: {e}")
            return False
    
    def create_backup(self, file_path: str) -> str:
        """백업 파일 생성"""
        try:
            backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(file_path, backup_path)
            self.backup_created = True
            logger.info(f"백업 파일 생성: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"백업 파일 생성 실패: {e}")
            return ""
    
    def auto_fix_all(self, analysis_data: Dict, advanced_analysis: Dict = None) -> Dict:
        """모든 자동 수정 실행"""
        if not self.doc:
            return {'success': False, 'error': 'DXF 문서가 로드되지 않았습니다.'}
        
        fixes = {
            'layer_fixes': self._fix_layer_issues(analysis_data),
            'duplicate_fixes': self._fix_duplicates(advanced_analysis),
            'standard_fixes': self._fix_standard_compliance(advanced_analysis),
            'text_fixes': self._fix_text_issues(analysis_data),
            'zero_length_fixes': self._fix_zero_length_entities(),
            'summary': {}
        }
        
        # 요약 생성
        total_fixes = sum(len(fix_list) if isinstance(fix_list, list) else fix_list.get('count', 0) 
                         for fix_list in fixes.values() if fix_list)
        
        fixes['summary'] = {
            'total_fixes': total_fixes,
            'backup_created': self.backup_created,
            'fixes_applied': self.fixes_applied,
            'success': total_fixes > 0
        }
        
        return fixes
    
    def _fix_layer_issues(self, analysis_data: Dict) -> List[Dict]:
        """레이어 문제 수정"""
        fixes = []
        
        try:
            # 1. 기본 레이어(0)만 사용하는 경우 표준 레이어 생성
            layers = {layer.dxf.name for layer in self.doc.layers}
            
            if len(layers) == 1 and '0' in layers:
                # 표준 레이어 추가
                standard_layers = [
                    ('DIMENSION', 2, 'CONTINUOUS'),  # 치수선 - 노란색
                    ('CENTER', 1, 'CENTER'),         # 중심선 - 빨간색
                    ('HIDDEN', 3, 'HIDDEN'),         # 숨김선 - 녹색
                    ('TEXT', 4, 'CONTINUOUS'),       # 텍스트 - 하늘색
                    ('HATCH', 254, 'CONTINUOUS')     # 해치 - 회색
                ]
                
                for name, color, linetype in standard_layers:
                    self.doc.layers.add(name=name, color=color, linetype=linetype)
                    fixes.append({
                        'type': 'layer_created',
                        'name': name,
                        'color': color,
                        'linetype': linetype
                    })
                
                self.fixes_applied.append('표준 레이어 생성')
            
            # 2. 잘못된 레이어 색상 수정
            for layer in self.doc.layers:
                if '치수' in layer.dxf.name.lower() or 'dim' in layer.dxf.name.lower():
                    if layer.dxf.color != 2:  # 노란색이 아닌 경우
                        old_color = layer.dxf.color
                        layer.dxf.color = 2
                        fixes.append({
                            'type': 'layer_color_fixed',
                            'name': layer.dxf.name,
                            'old_color': old_color,
                            'new_color': 2
                        })
                
                elif '중심' in layer.dxf.name.lower() or 'center' in layer.dxf.name.lower():
                    if layer.dxf.color != 1:  # 빨간색이 아닌 경우
                        old_color = layer.dxf.color
                        layer.dxf.color = 1
                        fixes.append({
                            'type': 'layer_color_fixed',
                            'name': layer.dxf.name,
                            'old_color': old_color,
                            'new_color': 1
                        })
            
        except Exception as e:
            logger.error(f"레이어 수정 중 오류: {e}")
        
        return fixes
    
    def _fix_duplicates(self, advanced_analysis: Dict) -> Dict:
        """중복 객체 제거"""
        if not advanced_analysis:
            return {'count': 0, 'details': []}
        
        removed_count = 0
        details = []
        
        try:
            anomalies = advanced_analysis.get('anomalies', [])
            msp = self.doc.modelspace()
            
            # 중복 원 제거
            duplicate_circles = [a for a in anomalies if a.get('type') == 'duplicate_circle']
            
            if duplicate_circles:
                # 모든 원 수집
                circles = []
                for entity in msp:
                    if entity.dxftype() == 'CIRCLE':
                        circles.append(entity)
                
                # 중복 제거 (동일 위치, 동일 반지름)
                seen = set()
                for circle in circles:
                    key = (
                        round(circle.dxf.center.x, 3),
                        round(circle.dxf.center.y, 3),
                        round(circle.dxf.radius, 3)
                    )
                    
                    if key in seen:
                        msp.delete_entity(circle)
                        removed_count += 1
                        details.append({
                            'type': 'circle',
                            'position': key[:2],
                            'radius': key[2]
                        })
                    else:
                        seen.add(key)
                
                if removed_count > 0:
                    self.fixes_applied.append(f'중복 원 {removed_count}개 제거')
            
        except Exception as e:
            logger.error(f"중복 제거 중 오류: {e}")
        
        return {'count': removed_count, 'details': details}
    
    def _fix_standard_compliance(self, advanced_analysis: Dict) -> List[Dict]:
        """표준 준수 문제 수정"""
        fixes = []
        
        if not advanced_analysis:
            return fixes
        
        try:
            compliance = advanced_analysis.get('standards_compliance', {})
            violations = compliance.get('violations', [])
            
            for violation in violations:
                if violation.get('type') == 'layer_color':
                    # 레이어 색상 표준화
                    layer_name = violation.get('layer_name')
                    if layer_name:
                        for layer in self.doc.layers:
                            if layer.dxf.name == layer_name:
                                # ISO 표준 색상 적용
                                if '중심선' in layer_name:
                                    layer.dxf.color = 1  # 빨간색
                                elif '숨김선' in layer_name:
                                    layer.dxf.color = 3  # 녹색
                                elif '치수선' in layer_name:
                                    layer.dxf.color = 2  # 노란색
                                
                                fixes.append({
                                    'type': 'standard_color_applied',
                                    'layer': layer_name,
                                    'standard': 'ISO'
                                })
                
                elif violation.get('type') == 'linetype':
                    # 선종류 표준화
                    layer_name = violation.get('layer_name')
                    if layer_name:
                        for layer in self.doc.layers:
                            if layer.dxf.name == layer_name:
                                if '중심선' in layer_name or 'center' in layer_name.lower():
                                    layer.dxf.linetype = 'CENTER'
                                elif '숨김선' in layer_name or 'hidden' in layer_name.lower():
                                    layer.dxf.linetype = 'HIDDEN'
                                
                                fixes.append({
                                    'type': 'standard_linetype_applied',
                                    'layer': layer_name,
                                    'standard': 'ISO'
                                })
            
            if fixes:
                self.fixes_applied.append(f'표준 준수 수정 {len(fixes)}건')
                
        except Exception as e:
            logger.error(f"표준 준수 수정 중 오류: {e}")
        
        return fixes
    
    def _fix_text_issues(self, analysis_data: Dict) -> List[Dict]:
        """텍스트 문제 수정"""
        fixes = []
        
        try:
            msp = self.doc.modelspace()
            
            # 1. 너무 작은 텍스트 크기 수정 (최소 2.5mm)
            min_text_height = 2.5
            
            for entity in msp:
                if entity.dxftype() in ['TEXT', 'MTEXT']:
                    if hasattr(entity.dxf, 'height'):
                        if entity.dxf.height < min_text_height:
                            old_height = entity.dxf.height
                            entity.dxf.height = min_text_height
                            fixes.append({
                                'type': 'text_height_fixed',
                                'old_height': old_height,
                                'new_height': min_text_height,
                                'content': getattr(entity.dxf, 'text', '')[:30]
                            })
            
            # 2. 텍스트 레이어 정리
            text_layer_exists = any(layer.dxf.name.upper() == 'TEXT' for layer in self.doc.layers)
            
            if text_layer_exists:
                text_moved = 0
                for entity in msp:
                    if entity.dxftype() in ['TEXT', 'MTEXT']:
                        if entity.dxf.layer != 'TEXT':
                            entity.dxf.layer = 'TEXT'
                            text_moved += 1
                
                if text_moved > 0:
                    fixes.append({
                        'type': 'text_layer_organized',
                        'count': text_moved
                    })
                    self.fixes_applied.append(f'텍스트 {text_moved}개를 TEXT 레이어로 이동')
            
        except Exception as e:
            logger.error(f"텍스트 수정 중 오류: {e}")
        
        return fixes
    
    def _fix_zero_length_entities(self) -> List[Dict]:
        """길이가 0인 엔티티 제거"""
        fixes = []
        removed_count = 0
        
        try:
            msp = self.doc.modelspace()
            entities_to_remove = []
            
            for entity in msp:
                if entity.dxftype() == 'LINE':
                    # 시작점과 끝점이 같은 선
                    if (entity.dxf.start.x == entity.dxf.end.x and 
                        entity.dxf.start.y == entity.dxf.end.y and
                        entity.dxf.start.z == entity.dxf.end.z):
                        entities_to_remove.append(entity)
                        fixes.append({
                            'type': 'zero_length_line',
                            'position': (entity.dxf.start.x, entity.dxf.start.y)
                        })
                
                elif entity.dxftype() == 'CIRCLE':
                    # 반지름이 0인 원
                    if entity.dxf.radius == 0:
                        entities_to_remove.append(entity)
                        fixes.append({
                            'type': 'zero_radius_circle',
                            'position': (entity.dxf.center.x, entity.dxf.center.y)
                        })
                
                elif entity.dxftype() == 'ARC':
                    # 반지름이 0인 호
                    if entity.dxf.radius == 0:
                        entities_to_remove.append(entity)
                        fixes.append({
                            'type': 'zero_radius_arc',
                            'position': (entity.dxf.center.x, entity.dxf.center.y)
                        })
            
            # 엔티티 제거
            for entity in entities_to_remove:
                msp.delete_entity(entity)
                removed_count += 1
            
            if removed_count > 0:
                self.fixes_applied.append(f'길이/크기가 0인 객체 {removed_count}개 제거')
            
        except Exception as e:
            logger.error(f"영길이 엔티티 제거 중 오류: {e}")
        
        return fixes
    
    def save_fixed_file(self, output_path: str = None) -> str:
        """수정된 파일 저장"""
        if not self.doc:
            raise ValueError("DXF 문서가 로드되지 않았습니다.")
        
        try:
            if output_path is None:
                # 원본 파일명에 _fixed 추가
                output_path = "fixed_drawing.dxf"
            
            self.doc.saveas(output_path)
            logger.info(f"수정된 파일 저장 완료: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"파일 저장 중 오류: {e}")
            raise
    
    def generate_fix_report(self, fixes: Dict) -> str:
        """수정 리포트 생성"""
        report = "# DXF 자동 수정 리포트\n\n"
        
        summary = fixes.get('summary', {})
        report += "## 📋 수정 요약\n"
        report += f"- **전체 수정 항목**: {summary.get('total_fixes', 0)}개\n"
        report += f"- **백업 생성**: {'✅' if summary.get('backup_created') else '❌'}\n"
        
        if summary.get('fixes_applied'):
            report += "\n### 적용된 수정사항\n"
            for fix in summary['fixes_applied']:
                report += f"- {fix}\n"
        
        # 레이어 수정
        layer_fixes = fixes.get('layer_fixes', [])
        if layer_fixes:
            report += "\n## 🎨 레이어 수정\n"
            for fix in layer_fixes:
                if fix['type'] == 'layer_created':
                    report += f"- 레이어 생성: {fix['name']} (색상: {fix['color']})\n"
                elif fix['type'] == 'layer_color_fixed':
                    report += f"- 색상 수정: {fix['name']} ({fix['old_color']} → {fix['new_color']})\n"
        
        # 중복 제거
        duplicate_fixes = fixes.get('duplicate_fixes', {})
        if duplicate_fixes.get('count', 0) > 0:
            report += f"\n## 🔄 중복 제거\n"
            report += f"- 제거된 중복 객체: {duplicate_fixes['count']}개\n"
        
        # 표준 준수
        standard_fixes = fixes.get('standard_fixes', [])
        if standard_fixes:
            report += "\n## 📏 표준 준수 수정\n"
            report += f"- ISO 표준 적용: {len(standard_fixes)}건\n"
        
        # 텍스트 수정
        text_fixes = fixes.get('text_fixes', [])
        if text_fixes:
            report += "\n## 📝 텍스트 수정\n"
            height_fixes = [f for f in text_fixes if f.get('type') == 'text_height_fixed']
            if height_fixes:
                report += f"- 텍스트 크기 수정: {len(height_fixes)}개\n"
            
            layer_fixes = [f for f in text_fixes if f.get('type') == 'text_layer_organized']
            if layer_fixes:
                report += f"- TEXT 레이어로 이동: {layer_fixes[0]['count']}개\n"
        
        # 영길이 엔티티
        zero_fixes = fixes.get('zero_length_fixes', [])
        if zero_fixes:
            report += f"\n## 🚫 불필요한 객체 제거\n"
            report += f"- 길이/크기가 0인 객체: {len(zero_fixes)}개 제거\n"
        
        report += f"\n---\n*수정 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report 