#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
샘플 DXF 파일 생성 스크립트
"""

import ezdxf

# 새 DXF 문서 생성
doc = ezdxf.new('R2018')
msp = doc.modelspace()

# 레이어 추가
doc.layers.add(name='치수선', color=2, linetype='CONTINUOUS')
doc.layers.add(name='중심선', color=1, linetype='CENTER')
doc.layers.add(name='외곽선', color=7, linetype='CONTINUOUS')
doc.layers.add(name='숨김선', color=3, linetype='HIDDEN')
doc.layers.add(name='텍스트', color=4, linetype='CONTINUOUS')

# 외곽선 그리기 (사각형)
msp.add_line((0, 0), (100, 0), dxfattribs={'layer': '외곽선'})
msp.add_line((100, 0), (100, 80), dxfattribs={'layer': '외곽선'})
msp.add_line((100, 80), (0, 80), dxfattribs={'layer': '외곽선'})
msp.add_line((0, 80), (0, 0), dxfattribs={'layer': '외곽선'})

# 원 추가
msp.add_circle((30, 40), 15, dxfattribs={'layer': '외곽선'})
msp.add_circle((70, 40), 15, dxfattribs={'layer': '외곽선'})

# 중심선 추가
msp.add_line((30, 20), (30, 60), dxfattribs={'layer': '중심선'})
msp.add_line((10, 40), (50, 40), dxfattribs={'layer': '중심선'})
msp.add_line((70, 20), (70, 60), dxfattribs={'layer': '중심선'})
msp.add_line((50, 40), (90, 40), dxfattribs={'layer': '중심선'})

# 치수 추가
dim1 = msp.add_linear_dim(
    base=(50, -10),
    p1=(0, 0),
    p2=(100, 0),
    dxfattribs={'layer': '치수선'}
)
dim1.render()

dim2 = msp.add_linear_dim(
    base=(110, 40),
    p1=(100, 0),
    p2=(100, 80),
    angle=90,
    dxfattribs={'layer': '치수선'}
)
dim2.render()

# 지름 치수
dim3 = msp.add_diameter_dim(
    center=(30, 40),
    radius=15,
    location=(45, 55),
    dxfattribs={'layer': '치수선'}
)
dim3.render()

# 텍스트 추가
msp.add_text(
    'SAMPLE DRAWING',
    height=5,
    dxfattribs={
        'layer': '텍스트',
        'style': 'STANDARD'
    }
).set_placement((50, 90))

msp.add_text(
    'HOLE Ø30',
    height=3,
    dxfattribs={
        'layer': '텍스트',
        'style': 'STANDARD'
    }
).set_placement((30, 10))

msp.add_text(
    'HOLE Ø30',
    height=3,
    dxfattribs={
        'layer': '텍스트',
        'style': 'STANDARD'
    }
).set_placement((70, 10))

# 해치 패턴 추가
hatch = msp.add_hatch(color=254, dxfattribs={'layer': '외곽선'})
hatch.paths.add_polyline_path([(10, 65), (20, 65), (20, 75), (10, 75)], is_closed=True)
hatch.set_pattern_fill('ANSI31', scale=0.5)

# 파일 저장
doc.saveas('sample_drawing.dxf')
print("샘플 DXF 파일이 생성되었습니다: sample_drawing.dxf") 