#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 고급 분석기 - 상용화 수준의 전문 분석 기능
Author: CAD Analysis Expert
Version: 2.0.0
License: MIT
"""

import math
import statistics
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from pathlib import Path
import json
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DXFAdvancedAnalyzer:
    """고급 DXF 분석 기능을 제공하는 클래스"""
    
    def __init__(self):
        """분석기 초기화"""
        self.quality_metrics = {}
        self.complexity_metrics = {}
        self.standards_compliance = {}
        self.anomalies = []
        self.patterns = {}
        self.ai_context = {}
        
    def analyze_drawing_quality(self, analyzer_data: Dict) -> Dict:
        """도면 품질 평가"""
        quality_score = 100
        quality_issues = []
        
        # 1. 레이어 구성 평가
        layers = analyzer_data.get('layers', [])
        layer_score, layer_issues = self._evaluate_layer_organization(layers)
        quality_score -= (100 - layer_score) * 0.2
        quality_issues.extend(layer_issues)
        
        # 2. 치수 정확도 평가
        dimensions = analyzer_data.get('dimensions', [])
        dim_score, dim_issues = self._evaluate_dimensions(dimensions)
        quality_score -= (100 - dim_score) * 0.3
        quality_issues.extend(dim_issues)
        
        # 3. 객체 분포 평가
        entity_breakdown = analyzer_data.get('entity_breakdown', {})
        dist_score, dist_issues = self._evaluate_entity_distribution(entity_breakdown)
        quality_score -= (100 - dist_score) * 0.1
        quality_issues.extend(dist_issues)
        
        # 4. 텍스트 일관성 평가
        texts = analyzer_data.get('texts', [])
        text_score, text_issues = self._evaluate_text_consistency(texts)
        quality_score -= (100 - text_score) * 0.1
        quality_issues.extend(text_issues)
        
        # 5. 도면 복잡도 평가
        complexity = self.calculate_drawing_complexity(analyzer_data)
        overall_complexity = complexity.get('overall_complexity', 0)
        if overall_complexity is not None and overall_complexity > 0.8:
            quality_score -= 10
            quality_issues.append({
                'severity': 'warning',
                'category': '복잡도',
                'message': '도면이 매우 복잡합니다. 가독성 개선이 필요할 수 있습니다.'
            })
        
        self.quality_metrics = {
            'overall_score': max(0, quality_score),
            'layer_score': layer_score,
            'dimension_score': dim_score,
            'distribution_score': dist_score,
            'text_score': text_score,
            'issues': quality_issues,
            'grade': self._get_quality_grade(quality_score)
        }
        
        return self.quality_metrics
    
    def _evaluate_layer_organization(self, layers: List[Dict]) -> Tuple[float, List]:
        """레이어 구성 평가"""
        score = 100
        issues = []
        
        if not layers:
            return 0, [{'severity': 'error', 'category': '레이어', 'message': '레이어가 정의되지 않았습니다.'}]
        
        # 레이어 명명 규칙 검사
        layer_names = [layer['name'] for layer in layers]
        
        # 기본 레이어(0)만 사용하는 경우
        if len(layer_names) == 1 and layer_names[0] == '0':
            score -= 30
            issues.append({
                'severity': 'warning',
                'category': '레이어',
                'message': '기본 레이어(0)만 사용중입니다. 레이어 구분이 필요합니다.'
            })
        
        # 의미있는 레이어명 사용 여부
        meaningful_patterns = [
            r'치수|dimension|dim',
            r'중심선|center|cen',
            r'숨김선|hidden|hid',
            r'텍스트|text|txt',
            r'해치|hatch|hat'
        ]
        
        meaningful_count = sum(1 for name in layer_names 
                              if any(re.search(pattern, name, re.IGNORECASE) 
                                    for pattern in meaningful_patterns))
        
        if meaningful_count < len(layer_names) * 0.5:
            score -= 20
            issues.append({
                'severity': 'info',
                'category': '레이어',
                'message': '레이어명이 체계적이지 않습니다. 표준 명명 규칙 사용을 권장합니다.'
            })
        
        return score, issues
    
    def _evaluate_dimensions(self, dimensions: List[Dict]) -> Tuple[float, List]:
        """치수 정확도 평가"""
        score = 100
        issues = []
        
        if not dimensions:
            return score, issues
        
        # 치수값 분석 (None 값 안전하게 처리)
        measurements = []
        for dim in dimensions:
            measurement = dim.get('measurement')
            if measurement is not None and isinstance(measurement, (int, float)) and measurement > 0:
                measurements.append(measurement)
        
        if measurements and len(measurements) > 1:
            try:
                # 극단적인 값 검사
                mean_val = statistics.mean(measurements)
                std_val = statistics.stdev(measurements) if len(measurements) > 1 else 0
                
                outliers = []
                if std_val > 0:
                    outliers = [m for m in measurements 
                               if abs(m - mean_val) > 3 * std_val]
                
                if outliers:
                    score -= min(20, len(outliers) * 5)
                    issues.append({
                        'severity': 'warning',
                        'category': '치수',
                        'message': f'{len(outliers)}개의 이상 치수값이 발견되었습니다.'
                    })
            except Exception as e:
                logger.warning(f"치수 분석 중 오류: {e}")
        
        return score, issues
    
    def _evaluate_entity_distribution(self, entity_breakdown: Dict) -> Tuple[float, List]:
        """객체 분포 평가"""
        score = 100
        issues = []
        
        if not entity_breakdown:
            return 0, [{'severity': 'error', 'category': '객체', 'message': '객체 정보가 없습니다.'}]
        
        total_entities = sum(entity_breakdown.values())
        
        # 특정 객체 유형이 과도하게 많은 경우
        for entity_type, count in entity_breakdown.items():
            ratio = count / total_entities
            
            if ratio > 0.7:
                score -= 15
                issues.append({
                    'severity': 'info',
                    'category': '객체 분포',
                    'message': f'{entity_type} 객체가 전체의 {ratio*100:.1f}%를 차지합니다.'
                })
        
        return score, issues
    
    def _evaluate_text_consistency(self, texts: List[Dict]) -> Tuple[float, List]:
        """텍스트 일관성 평가"""
        score = 100
        issues = []
        
        if not texts:
            return score, issues
        
        # 텍스트 높이 일관성 검사 (None 값 안전하게 처리)
        heights = []
        for text in texts:
            height = text.get('height')
            if height is not None and isinstance(height, (int, float)) and height > 0:
                heights.append(height)
        
        if heights:
            unique_heights = set(heights)
            
            if len(unique_heights) > 5:
                score -= 10
                issues.append({
                    'severity': 'info',
                    'category': '텍스트',
                    'message': f'{len(unique_heights)}개의 서로 다른 텍스트 높이가 사용되었습니다.'
                })
        
        return score, issues
    
    def _get_quality_grade(self, score: float) -> str:
        """품질 점수에 따른 등급 부여"""
        if score >= 90:
            return 'A (우수)'
        elif score >= 80:
            return 'B (양호)'
        elif score >= 70:
            return 'C (보통)'
        elif score >= 60:
            return 'D (미흡)'
        else:
            return 'F (개선필요)'
    
    def calculate_drawing_complexity(self, analyzer_data: Dict) -> Dict:
        """도면 복잡도 계산"""
        total_entities = analyzer_data.get('summary_info', {}).get('total_entities', 0)
        layer_count = analyzer_data.get('summary_info', {}).get('layer_count', 0)
        entity_types = len(analyzer_data.get('entity_breakdown', {}))
        
        # 복잡도 요소들
        entity_complexity = min(total_entities / 10000, 1.0)  # 10000개 기준
        layer_complexity = min(layer_count / 50, 1.0)  # 50개 레이어 기준
        type_complexity = min(entity_types / 20, 1.0)  # 20종류 기준
        
        # 가중 평균
        overall_complexity = (
            entity_complexity * 0.5 +
            layer_complexity * 0.3 +
            type_complexity * 0.2
        )
        
        self.complexity_metrics = {
            'overall_complexity': overall_complexity,
            'entity_complexity': entity_complexity,
            'layer_complexity': layer_complexity,
            'type_complexity': type_complexity,
            'complexity_level': self._get_complexity_level(overall_complexity)
        }
        
        return self.complexity_metrics
    
    def _get_complexity_level(self, complexity: float) -> str:
        """복잡도 수준 판단"""
        if complexity < 0.2:
            return '매우 단순'
        elif complexity < 0.4:
            return '단순'
        elif complexity < 0.6:
            return '보통'
        elif complexity < 0.8:
            return '복잡'
        else:
            return '매우 복잡'
    
    def check_standards_compliance(self, analyzer_data: Dict, standard: str = 'ISO') -> Dict:
        """설계 표준 준수 검증"""
        compliance_score = 100
        violations = []
        
        # ISO/KS 표준 검증
        if standard == 'ISO':
            # 레이어명 표준
            layer_violations = self._check_iso_layer_standards(analyzer_data.get('layers', []))
            violations.extend(layer_violations)
            compliance_score -= len(layer_violations) * 5
            
            # 선종류 표준
            linetype_violations = self._check_linetype_standards(analyzer_data.get('layers', []))
            violations.extend(linetype_violations)
            compliance_score -= len(linetype_violations) * 3
            
            # 치수 표준
            dim_violations = self._check_dimension_standards(analyzer_data.get('dimensions', []))
            violations.extend(dim_violations)
            compliance_score -= len(dim_violations) * 4
        
        self.standards_compliance = {
            'standard': standard,
            'compliance_score': max(0, compliance_score),
            'violations': violations,
            'compliant': compliance_score >= 80
        }
        
        return self.standards_compliance
    
    def _check_iso_layer_standards(self, layers: List[Dict]) -> List[Dict]:
        """ISO 레이어 표준 검증"""
        violations = []
        
        # ISO 표준 레이어 색상
        iso_colors = {
            '외곽선': [7, 'white'],
            '중심선': [1, 'red'],
            '숨김선': [3, 'green'],
            '치수선': [2, 'yellow'],
            '절단선': [4, 'cyan']
        }
        
        for layer in layers:
            layer_name = layer['name'].lower()
            layer_color = layer.get('color', 7)
            
            # 표준 레이어명 검사
            for std_name, (std_color, color_name) in iso_colors.items():
                if std_name in layer_name and layer_color != std_color:
                    violations.append({
                        'type': 'layer_color',
                        'severity': 'warning',
                        'message': f"레이어 '{layer['name']}'의 색상이 ISO 표준과 다릅니다. (권장: {color_name})"
                    })
        
        return violations
    
    def _check_linetype_standards(self, layers: List[Dict]) -> List[Dict]:
        """선종류 표준 검증"""
        violations = []
        
        # 표준 선종류
        standard_linetypes = {
            '중심선': ['CENTER', 'DASHDOT'],
            '숨김선': ['HIDDEN', 'DASHED'],
            '외곽선': ['CONTINUOUS']
        }
        
        for layer in layers:
            layer_name = layer['name'].lower()
            linetype = layer.get('linetype', 'CONTINUOUS').upper()
            
            for line_type, valid_types in standard_linetypes.items():
                if line_type in layer_name and linetype not in valid_types:
                    violations.append({
                        'type': 'linetype',
                        'severity': 'info',
                        'message': f"레이어 '{layer['name']}'의 선종류가 표준과 다릅니다."
                    })
        
        return violations
    
    def _check_dimension_standards(self, dimensions: List[Dict]) -> List[Dict]:
        """치수 표준 검증"""
        violations = []
        
        # 치수 텍스트 높이 표준 (mm)
        standard_heights = [2.5, 3.5, 5.0, 7.0]
        
        for dim in dimensions:
            # 실제 구현에서는 치수 텍스트 높이 등을 검사
            pass
        
        return violations
    
    def detect_anomalies(self, analyzer_data: Dict) -> List[Dict]:
        """도면 이상 징후 탐지"""
        anomalies = []
        
        # 1. 중복 객체 탐지
        duplicates = self._detect_duplicate_entities(analyzer_data)
        anomalies.extend(duplicates)
        
        # 2. 고립된 객체 탐지
        isolated = self._detect_isolated_entities(analyzer_data)
        anomalies.extend(isolated)
        
        # 3. 비정상적인 스케일 탐지
        scale_issues = self._detect_scale_anomalies(analyzer_data)
        anomalies.extend(scale_issues)
        
        self.anomalies = anomalies
        return anomalies
    
    def _detect_duplicate_entities(self, analyzer_data: Dict) -> List[Dict]:
        """중복 객체 탐지"""
        anomalies = []
        
        # 원/호 중복 검사 (None 값 안전하게 처리)
        circles = analyzer_data.get('circles', [])
        if len(circles) > 1:
            # 동일 위치, 동일 반지름 원 찾기
            seen = {}
            for circle in circles:
                try:
                    center = circle.get('center')
                    radius = circle.get('radius')
                    
                    if (center is not None and len(center) >= 2 and 
                        radius is not None and isinstance(radius, (int, float))):
                        
                        key = (
                            round(float(center[0]), 3),
                            round(float(center[1]), 3),
                            round(float(radius), 3)
                        )
                        
                        if key in seen:
                            anomalies.append({
                                'type': 'duplicate_circle',
                                'severity': 'warning',
                                'message': f"중복된 원이 발견되었습니다. 위치: {center}"
                            })
                        else:
                            seen[key] = True
                except Exception as e:
                    logger.warning(f"원 중복 검사 중 오류: {e}")
                    continue
        
        return anomalies
    
    def _detect_isolated_entities(self, analyzer_data: Dict) -> List[Dict]:
        """고립된 객체 탐지"""
        # 실제 구현에서는 공간 분석을 통해 고립된 객체 탐지
        return []
    
    def _detect_scale_anomalies(self, analyzer_data: Dict) -> List[Dict]:
        """스케일 이상 탐지"""
        anomalies = []
        
        # 텍스트 크기 이상 탐지 (None 값 안전하게 처리)
        texts = analyzer_data.get('texts', [])
        if texts:
            # 유효한 텍스트 높이만 수집
            valid_heights = []
            for text in texts:
                height = text.get('height')
                if height is not None and isinstance(height, (int, float)) and height > 0:
                    valid_heights.append(height)
            
            if valid_heights and len(valid_heights) > 1:
                try:
                    mean_height = statistics.mean(valid_heights)
                    
                    # 평균의 10배 이상 또는 1/10 이하인 텍스트 찾기
                    for text in texts:
                        height = text.get('height')
                        if (height is not None and isinstance(height, (int, float)) and 
                            height > 0 and mean_height > 0):
                            if height > mean_height * 10 or height < mean_height / 10:
                                anomalies.append({
                                    'type': 'text_scale',
                                    'severity': 'info',
                                    'message': f"비정상적인 텍스트 크기: {height:.2f} (평균: {mean_height:.2f})"
                                })
                except Exception as e:
                    logger.warning(f"텍스트 스케일 분석 중 오류: {e}")
        
        return anomalies
    
    def detect_patterns(self, analyzer_data: Dict) -> Dict:
        """도면 패턴 분석"""
        patterns = {
            'repeated_dimensions': self._find_repeated_dimensions(analyzer_data),
            'grid_pattern': self._detect_grid_pattern(analyzer_data),
            'symmetry': self._detect_symmetry(analyzer_data)
        }
        
        self.patterns = patterns
        return patterns
    
    def _find_repeated_dimensions(self, analyzer_data: Dict) -> Dict:
        """반복되는 치수 패턴 찾기"""
        dimensions = analyzer_data.get('dimensions', [])
        
        if not dimensions:
            return {'found': False}
        
        # 치수값 빈도 분석 (None 값 안전하게 처리)
        measurements = []
        for dim in dimensions:
            measurement = dim.get('measurement')
            if measurement is not None and isinstance(measurement, (int, float)) and measurement > 0:
                measurements.append(measurement)
        
        if not measurements:
            return {'found': False}
        
        try:
            freq = Counter(measurements)
            repeated = {k: v for k, v in freq.items() if v > 1}
            
            return {
                'found': bool(repeated),
                'repeated_values': repeated,
                'most_common': freq.most_common(5)
            }
        except Exception as e:
            logger.warning(f"반복 치수 패턴 분석 중 오류: {e}")
            return {'found': False}
    
    def _detect_grid_pattern(self, analyzer_data: Dict) -> Dict:
        """격자 패턴 탐지"""
        # 실제 구현에서는 좌표 분석을 통한 격자 패턴 탐지
        return {'found': False}
    
    def _detect_symmetry(self, analyzer_data: Dict) -> Dict:
        """대칭성 탐지"""
        # 실제 구현에서는 객체 위치 분석을 통한 대칭성 탐지
        return {'found': False}
    
    def generate_ai_context(self, analyzer_data: Dict) -> Dict:
        """AI 분석을 위한 컨텍스트 생성"""
        # 품질 분석
        quality = self.analyze_drawing_quality(analyzer_data)
        
        # 복잡도 분석
        complexity = self.calculate_drawing_complexity(analyzer_data)
        
        # 표준 준수 검증
        compliance = self.check_standards_compliance(analyzer_data)
        
        # 이상 징후 탐지
        anomalies = self.detect_anomalies(analyzer_data)
        
        # 패턴 분석
        patterns = self.detect_patterns(analyzer_data)
        
        # AI를 위한 구조화된 컨텍스트
        self.ai_context = {
            'summary': {
                'file_name': analyzer_data.get('file_info', {}).get('filename', 'unknown'),
                'total_entities': analyzer_data.get('summary_info', {}).get('total_entities', 0),
                'quality_score': quality['overall_score'],
                'quality_grade': quality['grade'],
                'complexity_level': complexity['complexity_level'],
                'standards_compliant': compliance['compliant']
            },
            'quality_analysis': {
                'score': quality['overall_score'],
                'issues': quality['issues'],
                'recommendations': self._generate_quality_recommendations(quality)
            },
            'complexity_analysis': complexity,
            'standards_compliance': compliance,
            'anomalies': anomalies,
            'patterns': patterns,
            'key_insights': self._generate_key_insights(
                quality, complexity, compliance, anomalies, patterns
            ),
            'improvement_suggestions': self._generate_improvement_suggestions(
                quality, complexity, compliance, anomalies
            ),
            # AI 모델이 세밀한 판단을 할 수 있도록 원본 도면 데이터 전체를 포함 (용량 주의)
            'raw_data': analyzer_data
        }
        
        return self.ai_context
    
    def _generate_quality_recommendations(self, quality_metrics: Dict) -> List[str]:
        """품질 개선 권고사항 생성"""
        recommendations = []
        
        if quality_metrics['layer_score'] < 80:
            recommendations.append("레이어 구성을 체계화하고 표준 명명 규칙을 적용하세요.")
        
        if quality_metrics['dimension_score'] < 80:
            recommendations.append("치수 정확도를 검토하고 이상값을 확인하세요.")
        
        if quality_metrics['text_score'] < 80:
            recommendations.append("텍스트 스타일을 통일하여 일관성을 높이세요.")
        
        return recommendations
    
    def _generate_key_insights(self, quality, complexity, compliance, anomalies, patterns) -> List[str]:
        """핵심 인사이트 생성"""
        insights = []
        
        # 품질 인사이트
        if quality['overall_score'] < 70:
            insights.append(f"도면 품질이 {quality['grade']} 등급으로 개선이 필요합니다.")
        elif quality['overall_score'] > 90:
            insights.append("도면 품질이 우수한 수준입니다.")
        
        # 복잡도 인사이트
        overall_complexity = complexity.get('overall_complexity', 0)
        if overall_complexity is not None and overall_complexity > 0.7:
            insights.append("도면이 복잡하여 가독성 개선이 필요할 수 있습니다.")
        
        # 표준 준수 인사이트
        if not compliance['compliant']:
            insights.append(f"{len(compliance['violations'])}개의 표준 위반 사항이 발견되었습니다.")
        
        # 이상 징후 인사이트
        if anomalies:
            insights.append(f"{len(anomalies)}개의 이상 징후가 탐지되었습니다.")
        
        # 패턴 인사이트
        if patterns.get('repeated_dimensions', {}).get('found'):
            insights.append("반복되는 치수 패턴이 발견되어 표준화 가능성이 있습니다.")
        
        return insights
    
    def _generate_improvement_suggestions(self, quality, complexity, compliance, anomalies) -> List[Dict]:
        """개선 제안 생성"""
        suggestions = []
        
        # 우선순위별 개선 제안
        if quality['overall_score'] < 60:
            suggestions.append({
                'priority': 'high',
                'category': '품질',
                'suggestion': '도면 품질 개선이 시급합니다. 레이어 구성과 객체 정리를 우선 진행하세요.',
                'impact': '가독성 및 유지보수성 크게 향상'
            })
        
        overall_complexity = complexity.get('overall_complexity', 0)
        if overall_complexity is not None and overall_complexity > 0.8:
            suggestions.append({
                'priority': 'medium',
                'category': '복잡도',
                'suggestion': '도면을 여러 시트로 분할하거나 상세도를 별도로 작성하는 것을 고려하세요.',
                'impact': '이해도 향상 및 오류 감소'
            })
        
        if not compliance['compliant']:
            suggestions.append({
                'priority': 'medium',
                'category': '표준',
                'suggestion': 'ISO/KS 표준에 맞춰 레이어명과 선종류를 조정하세요.',
                'impact': '호환성 향상 및 협업 효율성 증대'
            })
        
        if anomalies:
            suggestions.append({
                'priority': 'high',
                'category': '이상징후',
                'suggestion': '탐지된 이상 징후들을 검토하고 수정하세요.',
                'impact': '도면 정확도 향상'
            })
        
        return sorted(suggestions, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['priority']])
    
    def export_for_ai(self, analyzer_data: Dict, format: str = 'markdown') -> str:
        """AI 분석을 위한 데이터 내보내기"""
        context = self.generate_ai_context(analyzer_data)
        
        if format == 'markdown':
            return self._export_as_markdown(context, analyzer_data)
        elif format == 'json':
            return json.dumps(context, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")
    
    def _export_as_markdown(self, context: Dict, analyzer_data: Dict) -> str:
        """AI용 마크다운 형식으로 내보내기"""
        md_content = f"""# DXF 도면 고급 분석 리포트

## 📋 기본 정보
- **파일명**: {context['summary']['file_name']}
- **전체 객체 수**: {context['summary']['total_entities']:,}
- **분석 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 종합 평가
- **품질 등급**: {context['summary']['quality_grade']} ({context['summary']['quality_score']:.1f}점)
- **복잡도**: {context['summary']['complexity_level']}
- **표준 준수**: {'준수' if context['summary']['standards_compliant'] else '미준수'}

## 💡 핵심 인사이트
"""
        for insight in context['key_insights']:
            md_content += f"- {insight}\n"
        
        md_content += "\n## 🔍 상세 분석\n\n"
        
        # 품질 분석
        md_content += "### 품질 분석\n"
        if context['quality_analysis']['issues']:
            md_content += "**발견된 문제점:**\n"
            for issue in context['quality_analysis']['issues']:
                md_content += f"- [{issue['severity']}] {issue['category']}: {issue['message']}\n"
        
        if context['quality_analysis']['recommendations']:
            md_content += "\n**개선 권고사항:**\n"
            for rec in context['quality_analysis']['recommendations']:
                md_content += f"- {rec}\n"
        
        # 이상 징후
        if context['anomalies']:
            md_content += "\n### 이상 징후\n"
            for anomaly in context['anomalies']:
                md_content += f"- [{anomaly['severity']}] {anomaly['type']}: {anomaly['message']}\n"
        
        # 개선 제안
        md_content += "\n## 📈 개선 제안\n"
        for suggestion in context['improvement_suggestions']:
            md_content += f"\n### {suggestion['priority'].upper()} - {suggestion['category']}\n"
            md_content += f"**제안**: {suggestion['suggestion']}\n"
            md_content += f"**기대 효과**: {suggestion['impact']}\n"
        
        # AI 프롬프트용 컨텍스트
        md_content += "\n## 🤖 AI 분석을 위한 컨텍스트\n"
        md_content += "```json\n"
        md_content += json.dumps(context, ensure_ascii=False, indent=2)
        md_content += "\n```\n"
        
        # ---- 추가 상세 테이블 (치수 & 원) ----
        # 너무 큰 도면의 경우 표가 과도하게 길어지는 것을 방지하기 위해 최대 100행까지만 표시
        dim_max = 100
        circ_max = 100

        dimensions = analyzer_data.get('dimensions', [])
        if dimensions:
            md_content += "\n---\n\n### 📐 치수 (DIMENSION) 상세\n\n"
            md_content += "| No. | 측정값 | 도면 표기 텍스트 | 치수 스타일 | 레이어 |\n"
            md_content += "|-----|--------|-----------------|-------------|--------|\n"
            for idx, dim in enumerate(dimensions[:dim_max], start=1):
                text_val = str(dim.get('text', '')).replace('|', '\\|').replace('\n', ' ')
                md_content += f"| {idx} | {dim.get('measurement', '')} | {text_val} | {dim.get('style', '')} | {dim.get('layer', '')} |\n"
            if len(dimensions) > dim_max:
                md_content += f"| ... | ... | (총 {len(dimensions)}개) | ... | ... | ... |\n"

        circles = analyzer_data.get('circles', [])
        if circles:
            md_content += "\n### 🔵 원 (CIRCLE) 상세\n\n"
            md_content += "| No. | 중심점 (X, Y, Z) | 반지름 | 지름 | 레이어 |\n"
            md_content += "|-----|--------------------|--------|------|--------|\n"
            for idx, circ in enumerate(circles[:circ_max], start=1):
                cx, cy, cz = circ.get('center', (0, 0, 0))
                md_content += f"| {idx} | ({cx:.3f}, {cy:.3f}, {cz:.3f}) | {circ.get('radius', 0):.3f} | {circ.get('diameter', 0):.3f} | {circ.get('layer', '')} |\n"
            if len(circles) > circ_max:
                md_content += f"| ... | ... | ... | (총 {len(circles)}개) | ... |\n"

        md_content += "\n"
        
        return md_content 