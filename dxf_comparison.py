#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 도면 비교 모듈 - 버전 간 차이점 분석
Author: CAD Comparison Expert
Version: 2.0.0
"""

import difflib
from typing import Dict, List, Tuple, Set, Any, Optional
from collections import defaultdict
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DXFComparison:
    """DXF 파일 비교 분석 클래스"""
    
    def __init__(self):
        """초기화"""
        self.file1_data: Optional[Dict] = None
        self.file2_data: Optional[Dict] = None
        self.differences = {
            'added': defaultdict(list),
            'removed': defaultdict(list),
            'modified': defaultdict(list),
            'summary': {}
        }
        
    def compare_dxf_files(self, analyzer1_data: Dict, analyzer2_data: Dict) -> Dict:
        """두 DXF 파일 비교"""
        try:
            self.file1_data = analyzer1_data
            self.file2_data = analyzer2_data
            
            # 파일 정보 비교
            self._compare_file_info()
            
            # 레이어 비교
            self._compare_layers()
            
            # 엔티티 비교
            self._compare_entities()
            
            # 치수 비교
            self._compare_dimensions()
            
            # 텍스트 비교
            self._compare_texts()
            
            # 블록 비교
            self._compare_blocks()
            
            # 요약 생성
            self._generate_summary()
            
            return self.differences
            
        except Exception as e:
            logger.error(f"DXF 파일 비교 중 오류: {e}")
            return {'error': str(e)}
    
    def _compare_file_info(self):
        """파일 정보 비교"""
        file1_info = self.file1_data.get('file_info', {}) if self.file1_data else {}
        file2_info = self.file2_data.get('file_info', {}) if self.file2_data else {}
        
        info_diff = {
            'file1': file1_info.get('filename', 'Unknown'),
            'file2': file2_info.get('filename', 'Unknown'),
            'size_diff': file2_info.get('size', 0) - file1_info.get('size', 0),
            'date1': file1_info.get('modified_time', 'Unknown'),
            'date2': file2_info.get('modified_time', 'Unknown')
        }
        
        self.differences['file_info'] = info_diff
    
    def _compare_layers(self):
        """레이어 비교"""
        if not self.file1_data or not self.file2_data:
            return
            
        layers1 = {layer['name']: layer for layer in self.file1_data.get('layers', [])}
        layers2 = {layer['name']: layer for layer in self.file2_data.get('layers', [])}
        
        # 레이어명 집합
        names1 = set(layers1.keys())
        names2 = set(layers2.keys())
        
        # 추가된 레이어
        added_layers = names2 - names1
        for name in added_layers:
            self.differences['added']['layers'].append(layers2[name])
        
        # 제거된 레이어
        removed_layers = names1 - names2
        for name in removed_layers:
            self.differences['removed']['layers'].append(layers1[name])
        
        # 수정된 레이어 (색상, 선종류 변경)
        common_layers = names1 & names2
        for name in common_layers:
            layer1 = layers1[name]
            layer2 = layers2[name]
            
            changes = []
            if layer1.get('color') != layer2.get('color'):
                changes.append({
                    'property': 'color',
                    'old': layer1.get('color'),
                    'new': layer2.get('color')
                })
            
            if layer1.get('linetype') != layer2.get('linetype'):
                changes.append({
                    'property': 'linetype',
                    'old': layer1.get('linetype'),
                    'new': layer2.get('linetype')
                })
            
            if changes:
                self.differences['modified']['layers'].append({
                    'name': name,
                    'changes': changes
                })
    
    def _compare_entities(self):
        """엔티티 개수 비교"""
        breakdown1 = self.file1_data.get('entity_breakdown', {})
        breakdown2 = self.file2_data.get('entity_breakdown', {})
        
        # 모든 엔티티 타입
        all_types = set(breakdown1.keys()) | set(breakdown2.keys())
        
        entity_changes = []
        for entity_type in all_types:
            count1 = breakdown1.get(entity_type, 0)
            count2 = breakdown2.get(entity_type, 0)
            
            if count1 != count2:
                entity_changes.append({
                    'type': entity_type,
                    'old_count': count1,
                    'new_count': count2,
                    'difference': count2 - count1
                })
        
        self.differences['entity_changes'] = sorted(
            entity_changes, 
            key=lambda x: abs(x['difference']), 
            reverse=True
        )
    
    def _compare_dimensions(self):
        """치수 비교"""
        dims1 = self.file1_data.get('dimensions', [])
        dims2 = self.file2_data.get('dimensions', [])
        
        # 치수값 집합
        values1 = {d.get('measurement', 0) for d in dims1 if d.get('measurement')}
        values2 = {d.get('measurement', 0) for d in dims2 if d.get('measurement')}
        
        # 추가된 치수값
        added_values = values2 - values1
        if added_values:
            self.differences['added']['dimension_values'] = sorted(list(added_values))
        
        # 제거된 치수값
        removed_values = values1 - values2
        if removed_values:
            self.differences['removed']['dimension_values'] = sorted(list(removed_values))
        
        # 치수 개수 변화
        self.differences['dimension_count_change'] = {
            'old': len(dims1),
            'new': len(dims2),
            'difference': len(dims2) - len(dims1)
        }
    
    def _compare_texts(self):
        """텍스트 비교"""
        texts1 = self.file1_data.get('texts', [])
        texts2 = self.file2_data.get('texts', [])
        
        # 텍스트 내용 집합
        content1 = {t.get('text', '').strip() for t in texts1 if t.get('text')}
        content2 = {t.get('text', '').strip() for t in texts2 if t.get('text')}
        
        # 추가된 텍스트
        added_texts = content2 - content1
        if added_texts:
            self.differences['added']['texts'] = sorted(list(added_texts))
        
        # 제거된 텍스트
        removed_texts = content1 - content2
        if removed_texts:
            self.differences['removed']['texts'] = sorted(list(removed_texts))
        
        # 텍스트 개수 변화
        self.differences['text_count_change'] = {
            'old': len(texts1),
            'new': len(texts2),
            'difference': len(texts2) - len(texts1)
        }
    
    def _compare_blocks(self):
        """블록 비교"""
        blocks1 = self.file1_data.get('blocks', [])
        blocks2 = self.file2_data.get('blocks', [])
        
        # 블록명 집합
        names1 = {b.get('name', '') for b in blocks1}
        names2 = {b.get('name', '') for b in blocks2}
        
        # 추가된 블록
        added_blocks = names2 - names1
        if added_blocks:
            self.differences['added']['blocks'] = sorted(list(added_blocks))
        
        # 제거된 블록
        removed_blocks = names1 - names2
        if removed_blocks:
            self.differences['removed']['blocks'] = sorted(list(removed_blocks))
    
    def _generate_summary(self):
        """비교 요약 생성"""
        summary = {
            'total_additions': sum(len(items) for items in self.differences['added'].values()),
            'total_removals': sum(len(items) for items in self.differences['removed'].values()),
            'total_modifications': sum(len(items) for items in self.differences['modified'].values()),
            'has_significant_changes': False,
            'change_level': 'none'
        }
        
        # 변경 수준 판단
        total_changes = summary['total_additions'] + summary['total_removals'] + summary['total_modifications']
        
        if total_changes == 0:
            summary['change_level'] = 'none'
        elif total_changes < 5:
            summary['change_level'] = 'minor'
        elif total_changes < 20:
            summary['change_level'] = 'moderate'
        else:
            summary['change_level'] = 'major'
            summary['has_significant_changes'] = True
        
        # 주요 변경사항 식별
        major_changes = []
        
        # 레이어 변경
        if self.differences['added']['layers'] or self.differences['removed']['layers']:
            major_changes.append('레이어 구조 변경')
        
        # 대량 엔티티 변경
        for change in self.differences.get('entity_changes', []):
            if abs(change['difference']) > 50:
                major_changes.append(f"{change['type']} 대량 변경 ({change['difference']:+d})")
        
        summary['major_changes'] = major_changes
        self.differences['summary'] = summary
    
    def generate_comparison_report(self) -> str:
        """비교 리포트 생성"""
        report = "# DXF 도면 비교 리포트\n\n"
        
        # 파일 정보
        file_info = self.differences.get('file_info', {})
        report += "## 📁 파일 정보\n"
        report += f"- **파일 1**: {file_info.get('file1', 'Unknown')}\n"
        report += f"- **파일 2**: {file_info.get('file2', 'Unknown')}\n"
        report += f"- **크기 차이**: {file_info.get('size_diff', 0):+,} bytes\n\n"
        
        # 요약
        summary = self.differences.get('summary', {})
        report += "## 📊 변경 요약\n"
        report += f"- **변경 수준**: {summary.get('change_level', 'unknown').upper()}\n"
        report += f"- **추가**: {summary.get('total_additions', 0)}개 항목\n"
        report += f"- **제거**: {summary.get('total_removals', 0)}개 항목\n"
        report += f"- **수정**: {summary.get('total_modifications', 0)}개 항목\n"
        
        if summary.get('major_changes'):
            report += "\n### 주요 변경사항\n"
            for change in summary['major_changes']:
                report += f"- {change}\n"
        
        # 레이어 변경
        report += "\n## 🎨 레이어 변경\n"
        
        added_layers = self.differences['added'].get('layers', [])
        if added_layers:
            report += "\n### 추가된 레이어\n"
            for layer in added_layers:
                report += f"- {layer['name']} (색상: {layer.get('color', 'N/A')})\n"
        
        removed_layers = self.differences['removed'].get('layers', [])
        if removed_layers:
            report += "\n### 제거된 레이어\n"
            for layer in removed_layers:
                report += f"- {layer['name']}\n"
        
        modified_layers = self.differences['modified'].get('layers', [])
        if modified_layers:
            report += "\n### 수정된 레이어\n"
            for layer in modified_layers:
                report += f"- **{layer['name']}**:\n"
                for change in layer['changes']:
                    report += f"  - {change['property']}: {change['old']} → {change['new']}\n"
        
        # 엔티티 변경
        entity_changes = self.differences.get('entity_changes', [])
        if entity_changes:
            report += "\n## 📐 엔티티 변경\n"
            report += "| 엔티티 타입 | 이전 | 이후 | 변화량 |\n"
            report += "|------------|------|------|--------|\n"
            
            for change in entity_changes[:10]:  # 상위 10개만 표시
                report += f"| {change['type']} | {change['old_count']} | {change['new_count']} | {change['difference']:+d} |\n"
        
        # 치수 변경
        dim_change = self.differences.get('dimension_count_change', {})
        if dim_change.get('difference', 0) != 0:
            report += "\n## 📏 치수 변경\n"
            report += f"- 치수 개수: {dim_change['old']} → {dim_change['new']} ({dim_change['difference']:+d})\n"
            
            added_dims = self.differences['added'].get('dimension_values', [])
            if added_dims and len(added_dims) <= 10:
                report += "\n추가된 치수값:\n"
                for val in added_dims[:5]:
                    report += f"- {val:.3f}\n"
        
        # 텍스트 변경
        text_change = self.differences.get('text_count_change', {})
        if text_change.get('difference', 0) != 0:
            report += "\n## 📝 텍스트 변경\n"
            report += f"- 텍스트 개수: {text_change['old']} → {text_change['new']} ({text_change['difference']:+d})\n"
            
            added_texts = self.differences['added'].get('texts', [])
            if added_texts and len(added_texts) <= 5:
                report += "\n추가된 텍스트:\n"
                for text in added_texts:
                    report += f"- \"{text}\"\n"
        
        # 블록 변경
        added_blocks = self.differences['added'].get('blocks', [])
        removed_blocks = self.differences['removed'].get('blocks', [])
        
        if added_blocks or removed_blocks:
            report += "\n## 🧩 블록 변경\n"
            if added_blocks:
                report += f"- 추가된 블록: {', '.join(added_blocks[:5])}\n"
            if removed_blocks:
                report += f"- 제거된 블록: {', '.join(removed_blocks[:5])}\n"
        
        report += f"\n---\n*비교 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report
    
    def export_comparison_json(self) -> str:
        """비교 결과를 JSON으로 내보내기"""
        return json.dumps(self.differences, ensure_ascii=False, indent=2) 