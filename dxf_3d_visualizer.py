#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF 3D 시각화 모듈 - Three.js 기반 웹 뷰어
Author: 3D Visualization Expert
Version: 1.0.0
"""

import os
import json
import math
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import numpy as np
import ezdxf
from ezdxf.addons import Importer
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)


class DXF3DConverter:
    """DXF를 3D 데이터로 변환하는 클래스"""
    
    def __init__(self):
        """초기화"""
        self.default_extrusion_height = 10.0  # 기본 돌출 높이
        self.layer_heights = {}  # 레이어별 높이 설정
        
    def convert_dxf_to_3d(self, dxf_file: str, extrusion_height: float = None) -> Dict:
        """DXF 파일을 3D 데이터로 변환"""
        try:
            doc = ezdxf.readfile(dxf_file)
            msp = doc.modelspace()
            
            if extrusion_height is None:
                extrusion_height = self.default_extrusion_height
            
            # 3D 데이터 구조
            three_js_data = {
                'geometries': [],
                'materials': [],
                'layers': {},
                'bounds': {
                    'min': {'x': float('inf'), 'y': float('inf'), 'z': 0},
                    'max': {'x': float('-inf'), 'y': float('-inf'), 'z': extrusion_height}
                }
            }
            
            # 레이어별 색상 설정
            layer_colors = {}
            for layer in doc.layers:
                color_index = layer.dxf.color
                layer_colors[layer.dxf.name] = self._get_color_from_index(color_index)
            
            # 엔티티 변환
            for entity in msp:
                layer_name = entity.dxf.layer
                color = layer_colors.get(layer_name, 0x808080)
                
                if entity.dxftype() == 'LINE':
                    self._convert_line_to_3d(entity, three_js_data, color, extrusion_height)
                elif entity.dxftype() == 'CIRCLE':
                    self._convert_circle_to_3d(entity, three_js_data, color, extrusion_height)
                elif entity.dxftype() == 'ARC':
                    self._convert_arc_to_3d(entity, three_js_data, color, extrusion_height)
                elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                    self._convert_polyline_to_3d(entity, three_js_data, color, extrusion_height)
                elif entity.dxftype() == 'TEXT':
                    self._convert_text_to_3d(entity, three_js_data, color)
                elif entity.dxftype() == 'INSERT':
                    # 블록 참조는 더 복잡한 처리 필요
                    pass
            
            # 중심점 계산
            bounds = three_js_data['bounds']
            center = {
                'x': (bounds['min']['x'] + bounds['max']['x']) / 2,
                'y': (bounds['min']['y'] + bounds['max']['y']) / 2,
                'z': (bounds['min']['z'] + bounds['max']['z']) / 2
            }
            three_js_data['center'] = center
            
            # 카메라 거리 계산
            diagonal = math.sqrt(
                (bounds['max']['x'] - bounds['min']['x']) ** 2 +
                (bounds['max']['y'] - bounds['min']['y']) ** 2 +
                (bounds['max']['z'] - bounds['min']['z']) ** 2
            )
            three_js_data['camera_distance'] = diagonal * 1.5
            
            return three_js_data
            
        except Exception as e:
            logger.error(f"DXF 3D 변환 오류: {e}")
            return {'error': str(e)}
    
    def _convert_line_to_3d(self, line, data: Dict, color: int, height: float):
        """라인을 3D로 변환 (사각형 박스)"""
        start = line.dxf.start
        end = line.dxf.end
        
        # 라인을 두께가 있는 박스로 변환
        line_thickness = 0.5
        
        # 방향 벡터
        dx = end.x - start.x
        dy = end.y - start.y
        length = math.sqrt(dx**2 + dy**2)
        
        if length > 0:
            # 법선 벡터 (90도 회전)
            nx = -dy / length * line_thickness / 2
            ny = dx / length * line_thickness / 2
            
            # 8개의 정점 (박스)
            vertices = [
                # 하단 면
                [start.x - nx, start.y - ny, 0],
                [start.x + nx, start.y + ny, 0],
                [end.x + nx, end.y + ny, 0],
                [end.x - nx, end.y - ny, 0],
                # 상단 면
                [start.x - nx, start.y - ny, height],
                [start.x + nx, start.y + ny, height],
                [end.x + nx, end.y + ny, height],
                [end.x - nx, end.y - ny, height]
            ]
            
            # 면 인덱스 (삼각형 두 개씩)
            faces = [
                # 하단
                [0, 1, 2], [0, 2, 3],
                # 상단
                [4, 6, 5], [4, 7, 6],
                # 측면
                [0, 4, 5], [0, 5, 1],
                [1, 5, 6], [1, 6, 2],
                [2, 6, 7], [2, 7, 3],
                [3, 7, 4], [3, 4, 0]
            ]
            
            geometry = {
                'type': 'box',
                'vertices': vertices,
                'faces': faces,
                'color': color
            }
            
            data['geometries'].append(geometry)
            self._update_bounds(data['bounds'], vertices)
    
    def _convert_circle_to_3d(self, circle, data: Dict, color: int, height: float):
        """원을 3D 실린더로 변환"""
        center = circle.dxf.center
        radius = circle.dxf.radius
        segments = max(16, int(radius * 4))  # 반지름에 따라 세그먼트 수 조정
        
        vertices = []
        
        # 원의 정점들 (상단과 하단)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            vertices.append([x, y, 0])  # 하단
            vertices.append([x, y, height])  # 상단
        
        # 중심점 추가
        vertices.append([center.x, center.y, 0])  # 하단 중심
        vertices.append([center.x, center.y, height])  # 상단 중심
        
        faces = []
        bottom_center = len(vertices) - 2
        top_center = len(vertices) - 1
        
        for i in range(segments):
            next_i = (i + 1) % segments
            
            # 측면
            faces.append([i*2, next_i*2, next_i*2+1])
            faces.append([i*2, next_i*2+1, i*2+1])
            
            # 하단
            faces.append([i*2, bottom_center, next_i*2])
            
            # 상단
            faces.append([i*2+1, next_i*2+1, top_center])
        
        geometry = {
            'type': 'cylinder',
            'vertices': vertices,
            'faces': faces,
            'color': color
        }
        
        data['geometries'].append(geometry)
        self._update_bounds(data['bounds'], vertices)
    
    def _convert_arc_to_3d(self, arc, data: Dict, color: int, height: float):
        """호를 3D로 변환"""
        center = arc.dxf.center
        radius = arc.dxf.radius
        start_angle = math.radians(arc.dxf.start_angle)
        end_angle = math.radians(arc.dxf.end_angle)
        
        # 각도 정규화
        if end_angle < start_angle:
            end_angle += 2 * math.pi
        
        segments = max(16, int(radius * (end_angle - start_angle) / math.pi))
        thickness = 0.5
        
        vertices = []
        
        # 호의 정점들
        for i in range(segments + 1):
            angle = start_angle + (end_angle - start_angle) * i / segments
            
            # 외부 정점
            x_out = center.x + (radius + thickness/2) * math.cos(angle)
            y_out = center.y + (radius + thickness/2) * math.sin(angle)
            
            # 내부 정점
            x_in = center.x + (radius - thickness/2) * math.cos(angle)
            y_in = center.y + (radius - thickness/2) * math.sin(angle)
            
            vertices.extend([
                [x_out, y_out, 0],
                [x_in, y_in, 0],
                [x_out, y_out, height],
                [x_in, y_in, height]
            ])
        
        faces = []
        for i in range(segments):
            base = i * 4
            
            # 측면
            faces.extend([
                [base, base+4, base+6], [base, base+6, base+2],  # 외부
                [base+1, base+3, base+7], [base+1, base+7, base+5],  # 내부
                [base, base+2, base+3], [base, base+3, base+1],  # 시작
                [base+4, base+5, base+7], [base+4, base+7, base+6]  # 끝
            ])
        
        geometry = {
            'type': 'arc',
            'vertices': vertices,
            'faces': faces,
            'color': color
        }
        
        data['geometries'].append(geometry)
        self._update_bounds(data['bounds'], vertices)
    
    def _convert_polyline_to_3d(self, polyline, data: Dict, color: int, height: float):
        """폴리라인을 3D로 변환"""
        if hasattr(polyline, 'get_points'):
            points = list(polyline.get_points())
            
            if len(points) < 2:
                return
            
            # 각 세그먼트를 라인으로 변환
            for i in range(len(points) - 1):
                # 가상의 LINE 엔티티 생성
                class FakeLine:
                    class dxf:
                        start = type('', (), {'x': points[i][0], 'y': points[i][1], 'z': 0})()
                        end = type('', (), {'x': points[i+1][0], 'y': points[i+1][1], 'z': 0})()
                
                self._convert_line_to_3d(FakeLine(), data, color, height)
            
            # 폐곡선인 경우 마지막 세그먼트 추가
            if polyline.is_closed and len(points) > 2:
                class FakeLine:
                    class dxf:
                        start = type('', (), {'x': points[-1][0], 'y': points[-1][1], 'z': 0})()
                        end = type('', (), {'x': points[0][0], 'y': points[0][1], 'z': 0})()
                
                self._convert_line_to_3d(FakeLine(), data, color, height)
    
    def _convert_text_to_3d(self, text, data: Dict, color: int):
        """텍스트를 3D 마커로 변환"""
        # 텍스트는 간단한 마커로 표시
        insert = text.dxf.insert
        height = getattr(text.dxf, 'height', 2.5)
        
        marker = {
            'type': 'text',
            'position': [insert[0], insert[1], height/2],
            'text': text.dxf.text,
            'size': height,
            'color': color
        }
        
        data['geometries'].append(marker)
        self._update_bounds(data['bounds'], [[insert[0], insert[1], 0]])
    
    def _get_color_from_index(self, index: int) -> int:
        """AutoCAD 색상 인덱스를 RGB로 변환"""
        # 기본 색상 팔레트 (간단한 버전)
        colors = {
            1: 0xFF0000,  # 빨강
            2: 0xFFFF00,  # 노랑
            3: 0x00FF00,  # 녹색
            4: 0x00FFFF,  # 청록
            5: 0x0000FF,  # 파랑
            6: 0xFF00FF,  # 자홍
            7: 0xFFFFFF,  # 흰색
            8: 0x808080,  # 회색
            9: 0xC0C0C0   # 밝은 회색
        }
        return colors.get(index, 0x808080)
    
    def _update_bounds(self, bounds: Dict, vertices: List):
        """경계 상자 업데이트"""
        for vertex in vertices:
            if len(vertex) >= 2:
                bounds['min']['x'] = min(bounds['min']['x'], vertex[0])
                bounds['min']['y'] = min(bounds['min']['y'], vertex[1])
                bounds['max']['x'] = max(bounds['max']['x'], vertex[0])
                bounds['max']['y'] = max(bounds['max']['y'], vertex[1])
                
                if len(vertex) >= 3:
                    bounds['min']['z'] = min(bounds['min']['z'], vertex[2])
                    bounds['max']['z'] = max(bounds['max']['z'], vertex[2])


class DXF3DViewer:
    """Three.js 기반 3D 뷰어 서버"""
    
    def __init__(self):
        """초기화"""
        self.app = FastAPI(title="DXF 3D Viewer")
        self.converter = DXF3DConverter()
        self.setup_routes()
        self.setup_cors()
        
    def setup_cors(self):
        """CORS 설정"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """라우트 설정"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """메인 뷰어 페이지"""
            return self.get_viewer_html()
        
        @self.app.post("/api/convert")
        async def convert_dxf(file_path: str, extrusion_height: float = 10.0):
            """DXF 파일을 3D 데이터로 변환"""
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
            
            result = self.converter.convert_dxf_to_3d(file_path, extrusion_height)
            
            if 'error' in result:
                raise HTTPException(status_code=400, detail=result['error'])
            
            return JSONResponse(content=result)
        
        @self.app.post("/api/convert-file")
        async def convert_dxf_file(
            file: UploadFile = File(...),
            extrusion_height: float = Form(10.0)
        ):
            """(업로드) DXF 파일을 3D 데이터로 변환"""
            temp_path = f"temp_{file.filename}"
            try:
                # 업로드 파일 저장
                with open(temp_path, "wb") as tmp:
                    tmp.write(await file.read())

                # 변환 수행
                result = self.converter.convert_dxf_to_3d(temp_path, extrusion_height)
            finally:
                # 임시 파일 정리
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            if 'error' in result:
                raise HTTPException(status_code=400, detail=result['error'])

            return JSONResponse(content=result)
    
    def get_viewer_html(self) -> str:
        """3D 뷰어 HTML"""
        return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DXF 3D 뷰어</title>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; overflow: hidden; }
        #container { width: 100vw; height: 100vh; position: relative; }
        #canvas { width: 100%; height: 100%; display: block; }
        #controls {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        #info {
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
        }
        button {
            margin: 5px;
            padding: 8px 15px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover { background: #0056b3; }
        input[type="file"] { margin: 10px 0; }
        input[type="range"] { width: 200px; margin: 5px 0; }
        .control-group { margin: 10px 0; }
    </style>
</head>
<body>
    <div id="container">
        <div id="canvas"></div>
        <div id="controls">
            <h3>DXF 3D 뷰어</h3>
            <div class="control-group">
                <input type="file" id="fileInput" accept=".dxf">
                <button onclick="loadFile()">파일 로드</button>
            </div>
            <div class="control-group">
                <label>돌출 높이: <span id="heightValue">10</span>mm</label><br>
                <input type="range" id="heightSlider" min="1" max="100" value="10" 
                       onchange="updateHeight(this.value)">
            </div>
            <div class="control-group">
                <button onclick="resetView()">뷰 초기화</button>
                <button onclick="toggleWireframe()">와이어프레임</button>
                <button onclick="toggleAxes()">축 표시</button>
            </div>
            <div class="control-group">
                <button onclick="exportSTL()">STL 내보내기</button>
                <button onclick="takeScreenshot()">스크린샷</button>
            </div>
        </div>
        <div id="info">
            마우스: 회전 | 휠: 줌 | 우클릭: 이동
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/exporters/STLExporter.js"></script>
    <script>
        let scene, camera, renderer, controls;
        let currentModel = null;
        let wireframeMode = false;
        let axesHelper = null;
        let currentDXFData = null;
        let extrusionHeight = 10;

        // Three.js 초기화
        function init() {
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf0f0f0);
            
            // 카메라 설정
            camera = new THREE.PerspectiveCamera(
                75, window.innerWidth / window.innerHeight, 0.1, 10000
            );
            camera.position.set(100, 100, 100);
            
            // 렌더러 설정
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            document.getElementById('canvas').appendChild(renderer.domElement);
            
            // 컨트롤 설정
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // 조명 설정
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4);
            directionalLight.position.set(100, 100, 50);
            directionalLight.castShadow = true;
            scene.add(directionalLight);
            
            // 그리드 추가
            const gridHelper = new THREE.GridHelper(200, 20);
            scene.add(gridHelper);
            
            // 축 헬퍼
            axesHelper = new THREE.AxesHelper(50);
            scene.add(axesHelper);
            
            // 이벤트 리스너
            window.addEventListener('resize', onWindowResize, false);
            
            animate();
        }
        
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        
        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }
        
        async function loadFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('파일을 선택해주세요');
                return;
            }
            
            // 서버로 파일 업로드 후 3D 데이터 요청
            const formData = new FormData();
            formData.append('file', file);
            formData.append('extrusion_height', extrusionHeight);

            try {
                const response = await fetch('/api/convert-file', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json();
                    alert('변환 실패: ' + (error.detail || response.statusText));
                    return;
                }

                const data = await response.json();
                createGeometryFromData(data);
            } catch (err) {
                console.error(err);
                alert('파일 업로드 중 오류가 발생했습니다');
            }
        }
        
        function createGeometryFromData(data) {
            if (currentModel) {
                scene.remove(currentModel);
            }
            
            const group = new THREE.Group();
            
            data.geometries.forEach(geom => {
                if (geom.type === 'text') {
                    // 텍스트는 스프라이트로 표시
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    canvas.width = 256;
                    canvas.height = 64;
                    
                    context.fillStyle = '#' + geom.color.toString(16).padStart(6, '0');
                    context.font = '24px Arial';
                    context.fillText(geom.text, 10, 40);
                    
                    const texture = new THREE.CanvasTexture(canvas);
                    const spriteMaterial = new THREE.SpriteMaterial({ map: texture });
                    const sprite = new THREE.Sprite(spriteMaterial);
                    sprite.position.set(...geom.position);
                    sprite.scale.set(geom.size * 5, geom.size, 1);
                    
                    group.add(sprite);
                } else {
                    // 메시 생성
                    const geometry = new THREE.BufferGeometry();
                    const vertices = new Float32Array(geom.vertices.flat());
                    const indices = new Uint16Array(geom.faces.flat());
                    
                    geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
                    geometry.setIndex(new THREE.BufferAttribute(indices, 1));
                    geometry.computeVertexNormals();
                    
                    const material = new THREE.MeshPhongMaterial({
                        color: geom.color,
                        side: THREE.DoubleSide,
                        wireframe: wireframeMode
                    });
                    
                    const mesh = new THREE.Mesh(geometry, material);
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;
                    
                    group.add(mesh);
                }
            });
            
            // 중심 맞추기
            if (data.center) {
                group.position.set(-data.center.x, -data.center.y, -data.center.z);
            }
            
            currentModel = group;
            scene.add(currentModel);
            
            // 카메라 위치 조정
            if (data.camera_distance) {
                camera.position.set(
                    data.camera_distance,
                    data.camera_distance,
                    data.camera_distance
                );
                camera.lookAt(0, 0, 0);
            }
        }
        
        function updateHeight(value) {
            document.getElementById('heightValue').textContent = value;
            extrusionHeight = value;
        }
        
        function resetView() {
            camera.position.set(100, 100, 100);
            camera.lookAt(0, 0, 0);
            controls.reset();
        }
        
        function toggleWireframe() {
            wireframeMode = !wireframeMode;
            if (currentModel) {
                currentModel.traverse(child => {
                    if (child.isMesh) {
                        child.material.wireframe = wireframeMode;
                    }
                });
            }
        }
        
        function toggleAxes() {
            axesHelper.visible = !axesHelper.visible;
        }
        
        function exportSTL() {
            if (!currentModel) {
                alert('먼저 모델을 로드해주세요');
                return;
            }
            
            const exporter = new THREE.STLExporter();
            const stlString = exporter.parse(currentModel);
            
            const blob = new Blob([stlString], { type: 'text/plain' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'model.stl';
            link.click();
        }
        
        function takeScreenshot() {
            renderer.render(scene, camera);
            renderer.domElement.toBlob(blob => {
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'screenshot.png';
                link.click();
            });
        }
        
        // 초기화
        init();
        
        // 테스트용 샘플 데이터
        const sampleData = {
            geometries: [
                {
                    type: 'box',
                    vertices: [
                        [0, 0, 0], [50, 0, 0], [50, 50, 0], [0, 50, 0],
                        [0, 0, 20], [50, 0, 20], [50, 50, 20], [0, 50, 20]
                    ],
                    faces: [
                        [0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
                        [0, 4, 5], [0, 5, 1], [1, 5, 6], [1, 6, 2],
                        [2, 6, 7], [2, 7, 3], [3, 7, 4], [3, 4, 0]
                    ],
                    color: 0x00ff00
                }
            ],
            center: { x: 25, y: 25, z: 10 },
            camera_distance: 150
        };
        
        // 샘플 데이터로 시작
        createGeometryFromData(sampleData);
    </script>
</body>
</html>
"""
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """서버 실행"""
        logger.info(f"3D 뷰어 서버 시작: http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


def main():
    """메인 함수"""
    viewer = DXF3DViewer()
    viewer.run()


if __name__ == "__main__":
    main() 