#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF CAD 도면 분석기 - 메인 실행 파일
Author: AI Assistant
Version: 1.0.0
License: MIT
"""

import sys
import os
import argparse
import logging
from pathlib import Path
import json
from datetime import datetime
"""tkinter는 데스크톱 GUI에서만 필요하며, 일부 서버 환경(예: Streamlit Cloud)에는 설치되어 있지 않을 수 있습니다.
   불필요한 ImportError를 방지하기 위해 optional import 패턴을 사용합니다."""

try:
    import tkinter as tk  # type: ignore
    from tkinter import ttk, messagebox, filedialog  # type: ignore
    TKINTER_AVAILABLE = True
except ImportError:
    # tkinter가 없는 환경에서도 모듈 임포트가 가능하도록 더미 변수를 정의
    from types import SimpleNamespace

    class _TkDummy(SimpleNamespace):
        """tkinter가 없는 환경에서도 속성 접근 오류를 방지하기 위한 더미 객체"""

        def __getattr__(self, item):  # noqa: D401,E501
            return _TkDummy()

        def __call__(self, *args, **kwargs):  # noqa: D401
            return _TkDummy()

    tk = _TkDummy()  # type: ignore
    ttk = _TkDummy()  # type: ignore
    messagebox = _TkDummy()  # type: ignore
    filedialog = _TkDummy()  # type: ignore
    TKINTER_AVAILABLE = False
import threading
import math

# 고급 분석 기능 임포트 (있을 경우)
try:
    from dxf_advanced_analyzer import DXFAdvancedAnalyzer
    ADVANCED_ANALYSIS_AVAILABLE = True
except ImportError:
    ADVANCED_ANALYSIS_AVAILABLE = False

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dxf_analyzer.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class DXFAnalyzer:
    """DXF 파일 분석기 메인 클래스"""
    
    def __init__(self):
        """분석기 초기화"""
        self.file_info = {}
        self.summary_info = {}
        self.layers = []
        self.dimensions = []
        self.circles = []
        self.arcs = []
        self.texts = []
        self.lines = []
        self.polylines = []
        self.blocks = []
        self.hatches = []
        self.entities_by_layer = {}
        self.entity_breakdown = {}
        self.drawing_bounds = {'min_x': None, 'min_y': None, 'max_x': None, 'max_y': None}
        self.advanced_analyzer = DXFAdvancedAnalyzer() if ADVANCED_ANALYSIS_AVAILABLE else None
        self.analysis_data = None  # 고급 분석을 위한 데이터 저장
        
    def reset_analysis_data(self):
        """분석 데이터 초기화"""
        self.file_info = {}
        self.summary_info = {}
        self.layers = []
        self.dimensions = []
        self.circles = []
        self.arcs = []
        self.texts = []
        self.lines = []
        self.polylines = []
        self.blocks = []
        self.hatches = []
        self.entities_by_layer = {}
        self.entity_breakdown = {}
        self.drawing_bounds = {'min_x': None, 'min_y': None, 'max_x': None, 'max_y': None}
        self.analysis_data = None
    
    def _update_bounds(self, x, y):
        """도면 경계 박스 업데이트"""
        if self.drawing_bounds['min_x'] is None or x < self.drawing_bounds['min_x']:
            self.drawing_bounds['min_x'] = x
        if self.drawing_bounds['max_x'] is None or x > self.drawing_bounds['max_x']:
            self.drawing_bounds['max_x'] = x
        if self.drawing_bounds['min_y'] is None or y < self.drawing_bounds['min_y']:
            self.drawing_bounds['min_y'] = y
        if self.drawing_bounds['max_y'] is None or y > self.drawing_bounds['max_y']:
            self.drawing_bounds['max_y'] = y
    
    def _calculate_drawing_size(self):
        """도면 크기 계산"""
        if (self.drawing_bounds['min_x'] is not None and 
            self.drawing_bounds['max_x'] is not None and
            self.drawing_bounds['min_y'] is not None and 
            self.drawing_bounds['max_y'] is not None):
            
            width = self.drawing_bounds['max_x'] - self.drawing_bounds['min_x']
            height = self.drawing_bounds['max_y'] - self.drawing_bounds['min_y']
            
            return {
                'width': width,
                'height': height,
                'area': width * height,
                'bounds': self.drawing_bounds
            }
        return None
        
    def analyze_dxf_file(self, file_path):
        """DXF 파일 분석"""
        try:
            import ezdxf
            
            # 파일 정보 수집
            file_path = Path(file_path)
            stat = file_path.stat()
            self.file_info = {
                'filename': file_path.name,
                'size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # DXF 파일 로드
            readfile_func = getattr(ezdxf, 'readfile')
            doc = readfile_func(str(file_path))
            msp = doc.modelspace()
            
            # 분석 데이터 초기화
            self.reset_analysis_data()
            
            # 파일 정보 재설정 (reset에서 지워지므로)
            self.file_info = {
                'filename': file_path.name,
                'size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 레이어 정보 수집
            for layer in doc.layers:
                self.layers.append({
                    'name': layer.dxf.name,
                    'color': getattr(layer.dxf, 'color', 7),
                    'linetype': getattr(layer.dxf, 'linetype', 'CONTINUOUS')
                })
            
            # 엔티티 분석
            entity_counts = {}
            for entity in msp:
                entity_type = entity.dxftype()
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
                
                # 특정 엔티티 상세 정보 수집
                if entity_type == 'DIMENSION':
                    # 치수 객체 상세 정보 수집 (측정값, 표기 텍스트, 스타일)
                    try:
                        # ezdxf 1.0+ 에서는 measurement 속성이 제공됨
                        measurement_val = getattr(entity, 'measurement', None)
                        if measurement_val is None:
                            # 일부 버전에서는 actual_measurement 속성에 저장되기도 함
                            measurement_val = getattr(entity.dxf, 'actual_measurement', None)
                    except Exception:
                        measurement_val = None

                    self.dimensions.append({
                        'layer': entity.dxf.layer,
                        'measurement': measurement_val,
                        'text': getattr(entity.dxf, 'text', ''),
                        'style': getattr(entity.dxf, 'dimstyle', ''),
                    })
                elif entity_type == 'CIRCLE':
                    radius_val = entity.dxf.radius
                    self.circles.append({
                        'layer': entity.dxf.layer,
                        'radius': radius_val,
                        'diameter': radius_val * 2,
                        'center': (entity.dxf.center.x, entity.dxf.center.y, getattr(entity.dxf.center, 'z', 0.0)),
                    })
                elif entity_type == 'ARC':
                    self.arcs.append({
                        'layer': entity.dxf.layer,
                        'radius': entity.dxf.radius,
                        'center': (entity.dxf.center.x, entity.dxf.center.y)
                    })
                elif entity_type in ['TEXT', 'MTEXT']:
                    self.texts.append({
                        'type': entity_type,
                        'layer': entity.dxf.layer,
                        'text': getattr(entity.dxf, 'text', ''),
                        'height': getattr(entity.dxf, 'height', 0)
                    })
                elif entity_type == 'LINE':
                    self.lines.append({
                        'layer': entity.dxf.layer,
                        'start': (entity.dxf.start.x, entity.dxf.start.y),
                        'end': (entity.dxf.end.x, entity.dxf.end.y),
                        'length': math.sqrt((entity.dxf.end.x - entity.dxf.start.x)**2 + 
                                          (entity.dxf.end.y - entity.dxf.start.y)**2)
                    })
                    # 경계 박스 업데이트
                    self._update_bounds(entity.dxf.start.x, entity.dxf.start.y)
                    self._update_bounds(entity.dxf.end.x, entity.dxf.end.y)
                elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
                    points = []
                    if hasattr(entity, 'get_points'):
                        points = [(p[0], p[1]) for p in entity.get_points()]
                    self.polylines.append({
                        'layer': entity.dxf.layer,
                        'points': points,
                        'closed': getattr(entity.dxf, 'closed', False),
                        'vertex_count': len(points)
                    })
                elif entity_type == 'INSERT':
                    self.blocks.append({
                        'layer': entity.dxf.layer,
                        'name': entity.dxf.name,
                        'position': (entity.dxf.insert.x, entity.dxf.insert.y),
                        'scale': (getattr(entity.dxf, 'xscale', 1), 
                                 getattr(entity.dxf, 'yscale', 1)),
                        'rotation': getattr(entity.dxf, 'rotation', 0)
                    })
                elif entity_type == 'HATCH':
                    self.hatches.append({
                        'layer': entity.dxf.layer,
                        'pattern': entity.dxf.pattern_name,
                        'solid': entity.dxf.solid_fill,
                        'scale': getattr(entity.dxf, 'pattern_scale', 1)
                    })
                
                # 레이어별 엔티티 분류
                layer_name = entity.dxf.layer
                if layer_name not in self.entities_by_layer:
                    self.entities_by_layer[layer_name] = {}
                self.entities_by_layer[layer_name][entity_type] = \
                    self.entities_by_layer[layer_name].get(entity_type, 0) + 1
            
            # 요약 정보 생성
            self.entity_breakdown = entity_counts
            self.summary_info = {
                'total_entities': sum(entity_counts.values()),
                'layer_count': len(self.layers),
                'dimension_count': len(self.dimensions),
                'circle_count': len(self.circles),
                'arc_count': len(self.arcs),
                'text_count': len(self.texts),
                'line_count': len(self.lines),
                'polyline_count': len(self.polylines),
                'block_count': len(self.blocks),
                'hatch_count': len(self.hatches),
                'entity_breakdown': entity_counts,
                'drawing_size': self._calculate_drawing_size()
            }
            
            # 고급 분석을 위한 데이터 준비
            self.analysis_data = {
                'file_info': self.file_info,
                'summary_info': self.summary_info,
                'layers': self.layers,
                'dimensions': self.dimensions,
                'circles': self.circles,
                'arcs': self.arcs,
                'texts': self.texts,
                'lines': self.lines,
                'polylines': self.polylines,
                'blocks': self.blocks,
                'hatches': self.hatches,
                'entities_by_layer': self.entities_by_layer,
                'entity_breakdown': self.entity_breakdown,
                'drawing_bounds': self.drawing_bounds
            }
            
            logger.info(f"DXF 파일 분석 완료: {len(self.summary_info['entity_breakdown'])}종류, {self.summary_info['total_entities']}개 객체")
            return True
            
        except Exception as e:
            logger.error(f"DXF 파일 분석 중 오류: {e}")
            return False
    
    def generate_markdown_report(self, output_file):
        """마크다운 리포트 생성"""
        try:
            content = self._build_markdown_content()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"마크다운 리포트 생성 완료: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"마크다운 리포트 생성 중 오류: {e}")
            return None
    
    def generate_advanced_report(self, output_file):
        """고급 분석 리포트 생성"""
        if not ADVANCED_ANALYSIS_AVAILABLE or not self.advanced_analyzer:
            logger.warning("고급 분석 기능을 사용할 수 없습니다.")
            return self.generate_markdown_report(output_file)
        
        try:
            # analysis_data가 None인 경우 처리
            if self.analysis_data is None:
                logger.warning("분석 데이터가 없습니다. 기본 리포트를 생성합니다.")
                return self.generate_markdown_report(output_file)
            
            # 고급 분석 실행
            advanced_content = self.advanced_analyzer.export_for_ai(
                self.analysis_data, 
                format='markdown'
            )
            
            # 기본 리포트와 고급 분석 결합
            basic_content = self._build_markdown_content()
            combined_content = basic_content + "\n\n" + advanced_content
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            
            logger.info(f"고급 분석 리포트 생성 완료: {output_file}")
            
            # JSON 형식으로도 저장 (AI 분석용)
            json_file = output_file.replace('.md', '_ai_context.json')
            ai_context = self.advanced_analyzer.generate_ai_context(self.analysis_data)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(ai_context, f, ensure_ascii=False, indent=2)
            
            logger.info(f"AI 컨텍스트 파일 생성 완료: {json_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"고급 분석 리포트 생성 중 오류: {e}")
            return self.generate_markdown_report(output_file)
    
    def _build_markdown_content(self):
        """마크다운 콘텐츠 생성"""
        content = f"""# CAD 도면 분석 리포트

## 파일 정보
- **파일명**: {self.file_info.get('filename', 'N/A')}
- **파일 크기**: {self.file_info.get('size', 0):,} bytes
- **수정 시간**: {self.file_info.get('modified_time', 'N/A')}

## 분석 요약
- **전체 객체 수**: {self.summary_info.get('total_entities', 0):,}
- **레이어 수**: {self.summary_info.get('layer_count', 0)}
- **치수 수**: {self.summary_info.get('dimension_count', 0)}
- **원/호 수**: {self.summary_info.get('circle_count', 0) + self.summary_info.get('arc_count', 0)}
- **텍스트 수**: {self.summary_info.get('text_count', 0)}

## 객체 유형별 분석
"""
        
        if self.entity_breakdown:
            content += "| 객체 유형 | 개수 | 비율 |\n"
            content += "|-----------|------|------|\n"
            
            total = sum(self.entity_breakdown.values())
            for entity_type, count in sorted(self.entity_breakdown.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total * 100) if total > 0 else 0
                content += f"| {entity_type} | {count:,} | {percentage:.1f}% |\n"
        
        content += "\n## 레이어 정보\n"
        if self.layers:
            content += "| 레이어명 | 색상 | 선종류 |\n"
            content += "|----------|------|--------|\n"
            for layer in self.layers:
                content += f"| {layer['name']} | {layer['color']} | {layer['linetype']} |\n"
        else:
            content += "레이어 정보가 없습니다.\n"
        
        content += "\n## 3. 치수 (DIMENSION) 객체 정보\n\n"
        if self.dimensions:
            content += "| No. | 측정값 | 도면 표기 텍스트 | 치수 스타일 | 레이어 |\n"
            content += "|-----|--------|-----------------|-------------|--------|\n"
            for idx, dim in enumerate(self.dimensions, start=1):
                content += f"| {idx} | {dim.get('measurement', '')} | {dim.get('text', '').replace('|', '\\|')} | {dim.get('style', '')} | {dim.get('layer', '')} |\n"
        else:
            content += "치수 객체가 없습니다.\n"

        content += "\n## 4. 원 (CIRCLE) 객체 정보\n\n"
        if self.circles:
            content += "| No. | 중심점 (X, Y, Z) | 반지름 | 지름 | 레이어 |\n"
            content += "|-----|--------------------|--------|------|--------|\n"
            for idx, circ in enumerate(self.circles, start=1):
                center_fmt = f"({circ['center'][0]:.3f}, {circ['center'][1]:.3f}, {circ['center'][2]:.3f})"
                content += f"| {idx} | {center_fmt} | {circ['radius']:.3f} | {circ['diameter']:.3f} | {circ['layer']} |\n"
        else:
            content += "원 객체가 없습니다.\n"
        
        content += f"\n---\n*리포트 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return content


# (DXFAnalyzerGUI class definition removed)

def check_dependencies():
    """필요한 라이브러리 설치 확인"""
    required_packages = {
        'ezdxf': 'pip install ezdxf',
        'tkinter': '기본 내장 (추가 설치 불필요)',
        'streamlit': 'pip install streamlit (웹 버전용)',
        'pandas': 'pip install pandas (웹 버전용)'
    }

    missing_packages = []

    try:
        import ezdxf
        logger.info(f"✓ ezdxf {getattr(ezdxf, '__version__', 'unknown')} 설치됨")
    except ImportError:
        missing_packages.append('ezdxf')

    try:
        import tkinter
        logger.info("✓ tkinter 사용 가능")
    except ImportError:
        missing_packages.append('tkinter')

    if missing_packages:
        logger.error("❌ 필수 라이브러리가 설치되지 않았습니다:")
        for pkg in missing_packages:
            logger.error(f"  - {pkg}: {required_packages[pkg]}")
        return False

    return True

def run_gui_version():
    """GUI 버전 실행"""
    try:
        logger.info("GUI 버전을 시작합니다...")

        logger.info("GUI 버전을 시작합니다...")

        if not TKINTER_AVAILABLE: # tkinter 사용 가능 여부 먼저 확인
            logger.error("tkinter를 사용할 수 없어 GUI 버전을 실행할 수 없습니다.")
            # 사용자에게 알림 (예: 콘솔 메시지 또는 messagebox가 있다면 그것 사용)
            if messagebox: # messagebox가 임포트 되었다면 (즉, tkinter 사용 가능 환경이었다면)
                 messagebox.showerror("GUI 실행 불가", "tkinter 라이브러리를 찾을 수 없어 GUI를 시작할 수 없습니다.")
            return False

        # tkinter 관련 모듈 임포트 확인 후 DXFAnalyzerGUI 임포트
        try:
            from dxf_analyzer_gui import DXFAnalyzerGUI
        except ImportError as e:
            logger.error(f"DXFAnalyzerGUI를 임포트할 수 없습니다: {e}")
            if messagebox:
                messagebox.showerror("GUI 실행 오류", f"GUI 모듈을 불러오는 중 오류 발생: {e}")
            return False

        root = tk.Tk()

        # 의존성 확인 (ezdxf 등 핵심 라이브러리)
        if not check_dependencies(): # check_dependencies는 ezdxf 등을 확인
            messagebox.showerror(
                "의존성 오류",
                "필수 라이브러리(예: ezdxf)가 설치되지 않았습니다.\n"
                "콘솔 로그를 확인하고 필요한 패키지를 설치해주세요."
            )
            root.destroy() # 의존성 오류 시 root 창 닫기
            return False

        app = DXFAnalyzerGUI(root)

        # 예외 처리
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            logger.error("처리되지 않은 예외 발생:", exc_info=(exc_type, exc_value, exc_traceback))
            messagebox.showerror("오류", f"예기치 않은 오류가 발생했습니다:\n{exc_value}")

        sys.excepthook = handle_exception

        logger.info("GUI 애플리케이션이 시작되었습니다")
        root.mainloop()

        return True

    except ImportError as e:
        logger.error(f"GUI 버전 실행 실패: {e}")
        return False
    except Exception as e:
        logger.error(f"GUI 버전 실행 중 오류: {e}")
        return False

def run_web_version():
    """웹 버전 실행"""
    try:
        import subprocess
        import sys

        logger.info("웹 버전을 시작합니다...")

        # streamlit 설치 확인
        try:
            import streamlit
        except ImportError:
            logger.error("Streamlit이 설치되지 않았습니다. 'pip install streamlit' 실행 후 다시 시도하세요.")
            return False

        # 웹 애플리케이션 파일 확인
        webapp_file = Path("dxf_analyzer_webapp.py")
        if not webapp_file.exists():
            logger.error(f"웹 애플리케이션 파일을 찾을 수 없습니다: {webapp_file}")
            return False

        # Streamlit 실행
        cmd = [sys.executable, "-m", "streamlit", "run", str(webapp_file)]
        logger.info(f"실행 명령어: {' '.join(cmd)}")

        subprocess.run(cmd)
        return True

    except Exception as e:
        logger.error(f"웹 버전 실행 중 오류: {e}")
        return False

def run_cli_version(input_file, output_file=None):
    """CLI 버전 실행"""
    try:
        logger.info(f"CLI 버전으로 파일 분석: {input_file}")

        if not Path(input_file).exists():
            logger.error(f"입력 파일을 찾을 수 없습니다: {input_file}")
            return False

        # 분석기 인스턴스 생성
        analyzer = DXFAnalyzer()

        # 분석 실행
        success = analyzer.analyze_dxf_file(input_file)

        if not success:
            logger.error("DXF 파일 분석에 실패했습니다")
            return False

        # 출력 파일명 결정
        if output_file is None:
            base_name = Path(input_file).stem
            output_file = f"{base_name}_Analysis_Report.md"

        # 리포트 생성 (고급 분석 가능한 경우 고급 리포트 생성)
        if ADVANCED_ANALYSIS_AVAILABLE:
            result_path = analyzer.generate_advanced_report(output_file)
        else:
            result_path = analyzer.generate_markdown_report(output_file)

        if result_path:
            logger.info(f"✓ 분석 완료. 리포트 파일: {result_path}")

            # 간단한 요약 출력
            print("\n=== 분석 요약 ===")
            print(f"전체 객체 수: {analyzer.summary_info['total_entities']:,}")
            print(f"레이어 수: {analyzer.summary_info['layer_count']}")
            print(f"치수 수: {analyzer.summary_info['dimension_count']}")
            print(f"원/호 수: {analyzer.summary_info['circle_count'] + analyzer.summary_info['arc_count']}")
            print(f"텍스트 수: {analyzer.summary_info['text_count']}")
            print(f"\n상세 리포트: {result_path}")

            return True
        else:
            logger.error("리포트 생성에 실패했습니다")
            return False

    except Exception as e:
        logger.error(f"CLI 버전 실행 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="DXF CAD 도면 분석기 - AutoCAD DXF 파일을 분석하여 상세 리포트를 생성합니다",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  %(prog)s --gui                           # GUI 버전 실행
  %(prog)s --web                           # 웹 버전 실행  
  %(prog)s --cli input.dxf                 # CLI 버전으로 분석
  %(prog)s --cli input.dxf -o report.md   # 출력 파일명 지정
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--gui', action='store_true', help='GUI 버전 실행')
    group.add_argument('--web', action='store_true', help='웹 버전 실행')
    group.add_argument('--cli', metavar='INPUT_FILE', help='CLI 버전으로 DXF 파일 분석')

    parser.add_argument('-o', '--output', metavar='OUTPUT_FILE', 
                       help='출력 파일명 (CLI 모드에서만 사용)')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='자세한 로그 출력')
    parser.add_argument('--version', action='version', version='DXF 분석기 v1.0.0')

    args = parser.parse_args()

    # 로그 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("DXF CAD 도면 분석기 v1.0.0 시작")

    # 기본 의존성 확인 (ezdxf는 모든 버전에서 필요)
    try:
        import ezdxf
    except ImportError:
        logger.error("❌ ezdxf 라이브러리가 설치되지 않았습니다. 'pip install ezdxf'로 설치해주세요.")
        return 1

    # 실행 모드에 따른 분기
    try:
        if args.gui:
            success = run_gui_version()
        elif args.web:
            success = run_web_version()
        elif args.cli:
            success = run_cli_version(args.cli, args.output)
        else:
            parser.print_help()
            return 1

        if success:
            logger.info("프로그램이 성공적으로 완료되었습니다")
            return 0
        else:
            logger.error("프로그램 실행 중 오류가 발생했습니다")
            return 1

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다")
        return 0
    except Exception as e:
        logger.error(f"예기치 않은 오류: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
