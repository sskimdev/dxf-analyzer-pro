#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 제조 비용 예측 모듈
Author: Manufacturing Cost Expert
Version: 1.0.0
"""

import math
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime
import ezdxf
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MaterialCost:
    """재료 비용 정보"""
    material_type: str
    raw_stock_size: Tuple[float, float, float]  # L x W x H
    volume_used: float
    volume_waste: float
    unit_price: float
    total_cost: float


@dataclass
class MachiningCost:
    """가공 비용 정보"""
    setup_time: float
    cutting_time: float
    tool_change_time: float
    machine_rate: float
    labor_rate: float
    total_cost: float


@dataclass
class ToolingCost:
    """공구 비용 정보"""
    tools_required: List[Dict]
    tool_wear_cost: float
    consumables_cost: float
    total_cost: float


class DXFCostEstimator:
    """DXF 제조 비용 예측기"""
    
    def __init__(self):
        """초기화"""
        # 재료 단가 데이터베이스 (원/kg)
        self.material_prices = {
            'aluminum': {
                '6061': 8000,
                '7075': 12000,
                '5052': 7500
            },
            'steel': {
                'mild_steel': 3000,
                'carbon_steel': 4500,
                'alloy_steel': 6000
            },
            'stainless_steel': {
                '304': 8500,
                '316': 11000,
                '430': 7000
            },
            'titanium': {
                'grade2': 50000,
                'grade5': 65000
            },
            'plastic': {
                'pom': 5000,
                'nylon': 4500,
                'peek': 150000
            }
        }
        
        # 재료 밀도 (g/cm³)
        self.material_density = {
            'aluminum': 2.7,
            'steel': 7.85,
            'stainless_steel': 7.9,
            'titanium': 4.5,
            'plastic': 1.4
        }
        
        # 가공 시간당 비용 (원/시간)
        self.machine_rates = {
            '3axis_mill': 50000,
            '5axis_mill': 80000,
            'lathe': 45000,
            'edm': 70000,
            'laser': 60000
        }
        
        # 작업자 시급 (원/시간)
        self.labor_rates = {
            'operator': 25000,
            'skilled_machinist': 35000,
            'cnc_programmer': 40000
        }
    
    def estimate_total_cost(self, dxf_file: str, material_spec: Dict, 
                          production_qty: int = 1) -> Dict:
        """총 제조 비용 예측"""
        try:
            doc = ezdxf.readfile(dxf_file)
            msp = doc.modelspace()
            
            # 형상 분석
            geometry = self._analyze_geometry(msp)
            
            # 재료비 계산
            material_cost = self._calculate_material_cost(
                geometry, material_spec, production_qty
            )
            
            # 가공비 계산
            machining_cost = self._calculate_machining_cost(
                geometry, material_spec, production_qty
            )
            
            # 공구비 계산
            tooling_cost = self._calculate_tooling_cost(
                geometry, material_spec, production_qty
            )
            
            # 추가 비용 계산
            additional_costs = self._calculate_additional_costs(
                material_cost, machining_cost, tooling_cost
            )
            
            # 수량별 할인 적용
            quantity_discount = self._apply_quantity_discount(production_qty)
            
            # 총 비용 집계
            total_unit_cost = (
                material_cost.total_cost + 
                machining_cost.total_cost + 
                tooling_cost.total_cost +
                additional_costs['total']
            )
            
            total_production_cost = total_unit_cost * production_qty * (1 - quantity_discount)
            
            return {
                'production_quantity': production_qty,
                'material_cost': material_cost,
                'machining_cost': machining_cost,
                'tooling_cost': tooling_cost,
                'additional_costs': additional_costs,
                'unit_cost': total_unit_cost,
                'quantity_discount': quantity_discount * 100,
                'total_production_cost': total_production_cost,
                'unit_price_after_discount': total_production_cost / production_qty,
                'cost_breakdown_chart': self._generate_cost_breakdown(
                    material_cost, machining_cost, tooling_cost, additional_costs
                ),
                'cost_reduction_suggestions': self._suggest_cost_reduction(
                    geometry, material_spec, production_qty
                )
            }
            
        except Exception as e:
            logger.error(f"비용 예측 중 오류: {e}")
            return {'error': str(e)}
    
    def _analyze_geometry(self, modelspace) -> Dict:
        """형상 분석 (비용 계산용)"""
        bounds = {'min_x': float('inf'), 'min_y': float('inf'), 'min_z': 0,
                 'max_x': float('-inf'), 'max_y': float('-inf'), 'max_z': 0}
        
        features = {
            'holes': [],
            'pockets': [],
            'contours': [],
            'total_cut_length': 0,
            'surface_area': 0,
            'complexity_score': 0
        }
        
        # 경계 상자 계산
        for entity in modelspace:
            if entity.dxftype() in ['LINE', 'CIRCLE', 'ARC', 'LWPOLYLINE']:
                # 경계 업데이트 로직
                if hasattr(entity, 'dxf'):
                    if entity.dxftype() == 'LINE':
                        start = entity.dxf.start
                        end = entity.dxf.end
                        bounds['min_x'] = min(bounds['min_x'], start[0], end[0])
                        bounds['max_x'] = max(bounds['max_x'], start[0], end[0])
                        bounds['min_y'] = min(bounds['min_y'], start[1], end[1])
                        bounds['max_y'] = max(bounds['max_y'], start[1], end[1])
                        
                        # 절삭 길이
                        length = math.sqrt(sum((e - s)**2 for s, e in zip(start, end)))
                        features['total_cut_length'] += length
                        
                    elif entity.dxftype() == 'CIRCLE':
                        center = entity.dxf.center
                        radius = entity.dxf.radius
                        bounds['min_x'] = min(bounds['min_x'], center[0] - radius)
                        bounds['max_x'] = max(bounds['max_x'], center[0] + radius)
                        bounds['min_y'] = min(bounds['min_y'], center[1] - radius)
                        bounds['max_y'] = max(bounds['max_y'], center[1] + radius)
                        
                        features['holes'].append({
                            'diameter': radius * 2,
                            'depth': 10  # 기본값
                        })
                        
                        # 원주 길이
                        features['total_cut_length'] += 2 * math.pi * radius
        
        # 바운딩 박스 크기
        features['bounding_box'] = {
            'length': bounds['max_x'] - bounds['min_x'],
            'width': bounds['max_y'] - bounds['min_y'],
            'height': 10  # 기본 두께
        }
        
        # 복잡도 점수 계산
        features['complexity_score'] = self._calculate_complexity_score(features)
        
        return features
    
    def _calculate_material_cost(self, geometry: Dict, material_spec: Dict, qty: int) -> MaterialCost:
        """재료비 계산"""
        material_type = material_spec.get('type', 'aluminum')
        material_grade = material_spec.get('grade', '6061')
        
        # 원재료 크기 계산 (여유율 포함)
        margin = 5  # 5mm 여유
        raw_length = geometry['bounding_box']['length'] + 2 * margin
        raw_width = geometry['bounding_box']['width'] + 2 * margin
        raw_height = material_spec.get('thickness', 10)
        
        # 부피 계산 (cm³)
        raw_volume = (raw_length * raw_width * raw_height) / 1000
        
        # 실제 사용 부피 (대략적 계산)
        used_volume = raw_volume * 0.7  # 30% 재료 제거 가정
        waste_volume = raw_volume - used_volume
        
        # 무게 계산 (kg)
        density = self.material_density.get(material_type, 2.7)
        raw_weight = raw_volume * density / 1000
        
        # 단가 적용
        unit_price = self.material_prices.get(material_type, {}).get(material_grade, 8000)
        total_cost = raw_weight * unit_price
        
        # 수량 할인 (원재료 구매)
        if qty > 100:
            total_cost *= 0.9
        elif qty > 50:
            total_cost *= 0.95
        
        return MaterialCost(
            material_type=f"{material_type} {material_grade}",
            raw_stock_size=(raw_length, raw_width, raw_height),
            volume_used=used_volume,
            volume_waste=waste_volume,
            unit_price=unit_price,
            total_cost=total_cost
        )
    
    def _calculate_machining_cost(self, geometry: Dict, material_spec: Dict, qty: int) -> MachiningCost:
        """가공비 계산"""
        material_type = material_spec.get('type', 'aluminum')
        machine_type = material_spec.get('machine', '3axis_mill')
        
        # 재료별 가공 난이도 계수
        material_factors = {
            'aluminum': 1.0,
            'steel': 1.5,
            'stainless_steel': 2.0,
            'titanium': 3.0,
            'plastic': 0.8
        }
        
        material_factor = material_factors.get(material_type, 1.0)
        
        # 설정 시간 (분)
        base_setup_time = 30  # 기본 30분
        if geometry['complexity_score'] > 7:
            base_setup_time += 20
        elif geometry['complexity_score'] > 5:
            base_setup_time += 10
        
        # 가공 시간 계산 (분)
        # 절삭 속도 기준 계산
        cutting_speed = 300 / material_factor  # mm/min
        cutting_time = (geometry['total_cut_length'] / cutting_speed) * 1.5  # 여유율
        
        # 구멍 가공 시간
        drilling_time = len(geometry['holes']) * 2 * material_factor
        
        # 공구 교환 시간
        tool_changes = max(3, len(geometry['holes']) // 10 + 2)
        tool_change_time = tool_changes * 2  # 2분/교환
        
        total_time = base_setup_time + cutting_time + drilling_time + tool_change_time
        
        # 수량에 따른 설정 시간 분산
        if qty > 1:
            setup_time_per_unit = base_setup_time / qty
        else:
            setup_time_per_unit = base_setup_time
        
        # 시간당 비용
        machine_rate = self.machine_rates.get(machine_type, 50000)
        labor_rate = self.labor_rates.get('skilled_machinist', 35000)
        
        # 총 비용
        total_hours = total_time / 60
        total_cost = total_hours * (machine_rate + labor_rate)
        
        return MachiningCost(
            setup_time=setup_time_per_unit,
            cutting_time=cutting_time,
            tool_change_time=tool_change_time,
            machine_rate=machine_rate,
            labor_rate=labor_rate,
            total_cost=total_cost
        )
    
    def _calculate_tooling_cost(self, geometry: Dict, material_spec: Dict, qty: int) -> ToolingCost:
        """공구비 계산"""
        tools_required = []
        
        # 필요 공구 목록
        # 엔드밀
        tools_required.append({
            'type': 'End Mill 6mm',
            'unit_cost': 50000,
            'life_parts': 500,
            'quantity': 2
        })
        
        # 드릴
        if geometry['holes']:
            unique_diameters = min(5, len(set(h['diameter'] for h in geometry['holes'])))
            for i in range(unique_diameters):
                tools_required.append({
                    'type': f'Drill Bit {i+1}',
                    'unit_cost': 20000,
                    'life_parts': 200,
                    'quantity': 1
                })
        
        # 공구 마모 비용 계산
        tool_wear_cost = 0
        for tool in tools_required:
            wear_per_part = tool['unit_cost'] / tool['life_parts']
            tool_wear_cost += wear_per_part * tool['quantity']
        
        # 소모품 비용 (절삭유, 냉각수 등)
        consumables_cost = geometry['total_cut_length'] * 0.5  # 0.5원/mm
        
        total_cost = tool_wear_cost + consumables_cost
        
        return ToolingCost(
            tools_required=tools_required,
            tool_wear_cost=tool_wear_cost,
            consumables_cost=consumables_cost,
            total_cost=total_cost
        )
    
    def _calculate_additional_costs(self, material: MaterialCost, 
                                  machining: MachiningCost, 
                                  tooling: ToolingCost) -> Dict:
        """추가 비용 계산"""
        subtotal = material.total_cost + machining.total_cost + tooling.total_cost
        
        additional = {
            'quality_control': subtotal * 0.05,  # 5%
            'overhead': subtotal * 0.15,  # 15%
            'profit_margin': subtotal * 0.20,  # 20%
        }
        
        additional['total'] = sum(additional.values())
        
        return additional
    
    def _apply_quantity_discount(self, qty: int) -> float:
        """수량 할인율 계산"""
        if qty >= 1000:
            return 0.25  # 25% 할인
        elif qty >= 500:
            return 0.20
        elif qty >= 100:
            return 0.15
        elif qty >= 50:
            return 0.10
        elif qty >= 10:
            return 0.05
        else:
            return 0.0
    
    def _calculate_complexity_score(self, features: Dict) -> float:
        """복잡도 점수 계산 (1-10)"""
        score = 1.0
        
        # 구멍 개수
        if len(features['holes']) > 20:
            score += 2
        elif len(features['holes']) > 10:
            score += 1
        
        # 절삭 길이
        if features['total_cut_length'] > 1000:
            score += 2
        elif features['total_cut_length'] > 500:
            score += 1
        
        # 크기
        bbox = features['bounding_box']
        if bbox['length'] * bbox['width'] > 10000:
            score += 1
        
        return min(10, score)
    
    def _generate_cost_breakdown(self, material: MaterialCost, 
                               machining: MachiningCost, 
                               tooling: ToolingCost,
                               additional: Dict) -> Dict:
        """비용 구성 차트 데이터"""
        total = (material.total_cost + machining.total_cost + 
                tooling.total_cost + additional['total'])
        
        return {
            'material': {
                'amount': material.total_cost,
                'percentage': (material.total_cost / total) * 100
            },
            'machining': {
                'amount': machining.total_cost,
                'percentage': (machining.total_cost / total) * 100
            },
            'tooling': {
                'amount': tooling.total_cost,
                'percentage': (tooling.total_cost / total) * 100
            },
            'quality_control': {
                'amount': additional['quality_control'],
                'percentage': (additional['quality_control'] / total) * 100
            },
            'overhead': {
                'amount': additional['overhead'],
                'percentage': (additional['overhead'] / total) * 100
            },
            'profit': {
                'amount': additional['profit_margin'],
                'percentage': (additional['profit_margin'] / total) * 100
            }
        }
    
    def _suggest_cost_reduction(self, geometry: Dict, material_spec: Dict, qty: int) -> List[str]:
        """비용 절감 제안"""
        suggestions = []
        
        # 수량 기반 제안
        if qty < 10:
            suggestions.append("수량을 10개 이상으로 늘리면 단가를 5% 절감할 수 있습니다")
        elif qty < 50:
            suggestions.append("수량을 50개 이상으로 늘리면 단가를 추가 5% 절감할 수 있습니다")
        
        # 재료 기반 제안
        if material_spec.get('type') == 'stainless_steel':
            suggestions.append("일반 강재로 변경 후 표면처리하면 30% 비용 절감 가능")
        elif material_spec.get('type') == 'titanium':
            suggestions.append("알루미늄 합금으로 대체 검토 시 60% 비용 절감 가능")
        
        # 설계 기반 제안
        if len(geometry['holes']) > 20:
            suggestions.append("구멍 개수를 줄이거나 표준 크기로 통일하면 가공비 20% 절감")
        
        if geometry['complexity_score'] > 7:
            suggestions.append("설계 단순화로 가공 시간 30% 단축 가능")
        
        # 가공 방법 제안
        if geometry['bounding_box']['length'] * geometry['bounding_box']['width'] < 100:
            suggestions.append("레이저 커팅으로 전환 시 소량 생산 비용 절감")
        
        return suggestions
    
    def generate_cost_report(self, estimation: Dict) -> str:
        """비용 예측 리포트 생성"""
        report = "# 💰 제조 비용 예측 리포트\n\n"
        
        if 'error' in estimation:
            report += f"⚠️ 오류: {estimation['error']}\n"
            return report
        
        # 기본 정보
        report += f"**생산 수량**: {estimation['production_quantity']}개\n"
        report += f"**단가**: {estimation['unit_cost']:,.0f}원\n"
        report += f"**수량 할인**: {estimation['quantity_discount']:.1f}%\n"
        report += f"**할인 후 단가**: {estimation['unit_price_after_discount']:,.0f}원\n"
        report += f"**총 생산 비용**: {estimation['total_production_cost']:,.0f}원\n\n"
        
        # 재료비
        material = estimation['material_cost']
        report += "## 📦 재료비\n"
        report += f"- **재료**: {material.material_type}\n"
        report += f"- **원재료 크기**: {material.raw_stock_size[0]:.1f} × {material.raw_stock_size[1]:.1f} × {material.raw_stock_size[2]:.1f}mm\n"
        report += f"- **재료 단가**: {material.unit_price:,}원/kg\n"
        report += f"- **재료비**: {material.total_cost:,.0f}원\n\n"
        
        # 가공비
        machining = estimation['machining_cost']
        report += "## ⚙️ 가공비\n"
        report += f"- **설정 시간**: {machining.setup_time:.1f}분\n"
        report += f"- **절삭 시간**: {machining.cutting_time:.1f}분\n"
        report += f"- **공구 교환**: {machining.tool_change_time:.1f}분\n"
        report += f"- **기계 시급**: {machining.machine_rate:,}원/시간\n"
        report += f"- **인건비**: {machining.labor_rate:,}원/시간\n"
        report += f"- **가공비**: {machining.total_cost:,.0f}원\n\n"
        
        # 공구비
        tooling = estimation['tooling_cost']
        report += "## 🔧 공구비\n"
        report += f"- **공구 마모비**: {tooling.tool_wear_cost:,.0f}원\n"
        report += f"- **소모품비**: {tooling.consumables_cost:,.0f}원\n"
        report += f"- **총 공구비**: {tooling.total_cost:,.0f}원\n\n"
        
        # 비용 구성
        report += "## 📊 비용 구성\n"
        breakdown = estimation['cost_breakdown_chart']
        for category, data in breakdown.items():
            report += f"- **{category.replace('_', ' ').title()}**: {data['amount']:,.0f}원 ({data['percentage']:.1f}%)\n"
        report += "\n"
        
        # 비용 절감 제안
        if estimation['cost_reduction_suggestions']:
            report += "## 💡 비용 절감 제안\n"
            for suggestion in estimation['cost_reduction_suggestions']:
                report += f"- {suggestion}\n"
        
        return report
    
    def export_quotation(self, estimation: Dict, customer_info: Dict) -> str:
        """견적서 생성"""
        quotation = f"""
=====================================
           제조 견적서
=====================================

견적 번호: Q{datetime.now().strftime('%Y%m%d%H%M')}
견적 일자: {datetime.now().strftime('%Y년 %m월 %d일')}

【 고객 정보 】
회사명: {customer_info.get('company', '미지정')}
담당자: {customer_info.get('contact', '미지정')}
연락처: {customer_info.get('phone', '미지정')}

【 제품 정보 】
제품명: {customer_info.get('product_name', 'DXF 가공품')}
수량: {estimation['production_quantity']}개
재료: {estimation['material_cost'].material_type}

【 견적 내역 】
1. 재료비: {estimation['material_cost'].total_cost:,.0f}원
2. 가공비: {estimation['machining_cost'].total_cost:,.0f}원
3. 공구비: {estimation['tooling_cost'].total_cost:,.0f}원
4. 품질관리비: {estimation['additional_costs']['quality_control']:,.0f}원
5. 간접비: {estimation['additional_costs']['overhead']:,.0f}원
─────────────────────────────────
소계: {estimation['unit_cost'] - estimation['additional_costs']['profit_margin']:,.0f}원
이익: {estimation['additional_costs']['profit_margin']:,.0f}원
─────────────────────────────────
단가: {estimation['unit_cost']:,.0f}원

【 수량 할인 】
할인율: {estimation['quantity_discount']:.1f}%
할인 후 단가: {estimation['unit_price_after_discount']:,.0f}원

【 총 금액 】
{estimation['total_production_cost']:,.0f}원
(부가세 별도)

【 납기 】
예상 납기: 발주 후 {max(5, estimation['production_quantity'] // 10)}일

【 비고 】
- 본 견적은 30일간 유효합니다
- 설계 변경 시 견적이 변동될 수 있습니다
- 운송비는 별도입니다

=====================================
"""
        return quotation 