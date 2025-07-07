#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DXF AI 통합 모듈 - OpenAI, Claude 및 Gemini API 연동
Author: AI Integration Expert
Version: 2.1.0
"""

import os
import json
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime
import asyncio
import aiohttp

# OpenAI
import openai

# Claude (Anthropic)
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    
logger = logging.getLogger(__name__)


class DXFAIIntegration:
    """DXF 분석 AI 통합 클래스"""
    
    def __init__(self):
        """초기화"""
        # API 키 설정
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        
        # 클라이언트 초기화
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            
        if self.claude_api_key and CLAUDE_AVAILABLE:
            self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
        else:
            self.claude_client = None
            
        if self.gemini_api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None
            
        # 프롬프트 템플릿
        self.prompts = self._load_prompts()
        self.default_timeout = 60 # 초 단위 타임아웃 기본값

    def is_api_key_configured(self, model_type: Optional[str] = None) -> bool:
        """지정된 모델 또는 전체 AI 서비스 API 키 설정 여부 확인"""
        if model_type == 'openai':
            return bool(self.openai_api_key)
        if model_type == 'claude':
            return bool(self.claude_api_key and CLAUDE_AVAILABLE and self.claude_client)
        if model_type == 'gemini':
            return bool(self.gemini_api_key and GEMINI_AVAILABLE and self.gemini_model)

        # 특정 모델이 지정되지 않으면 하나라도 사용 가능한지 확인
        return bool(self.openai_api_key or \
                    (self.claude_api_key and CLAUDE_AVAILABLE and self.claude_client) or \
                    (self.gemini_api_key and GEMINI_AVAILABLE and self.gemini_model))

    def _load_prompts(self) -> Dict[str, str]:
        """프롬프트 템플릿 로드"""
        return {
            'analysis': """당신은 전문 CAD 도면 분석 전문가입니다. 다음 DXF 도면 분석 데이터를 검토하고 전문가 의견을 제시해주세요:

{analysis_data}

다음 관점에서 분석해주세요:
1. 도면 품질 평가
2. 잠재적 문제점
3. 개선 제안사항
4. 업계 표준 준수 여부
5. 설계 효율성

전문가 답변:""",

            'comparison': """두 DXF 도면의 비교 분석 결과입니다:

{comparison_data}

다음을 분석해주세요:
1. 주요 변경사항의 의미
2. 설계 개선 여부
3. 잠재적 문제나 위험
4. 버전 관리 제안

전문가 의견:""",

            'autofix': """다음 DXF 도면의 문제점들이 발견되었습니다:

{issues_data}

각 문제에 대해:
1. 문제의 심각도 평가
2. 권장 수정 방법
3. 수정 우선순위
4. 예방 방법

전문가 조언:""",

            'design_review': """DXF 도면의 설계 검토를 요청합니다:

{design_data}

검토 항목:
1. 설계 무결성
2. 제조 가능성
3. 비용 효율성
4. 안전성 고려사항
5. 최적화 가능성

설계 검토 의견:""",

            'cnc_analysis': """당신은 CNC 가공 전문가입니다. 다음 DXF 도면을 CNC 가공 관점에서 분석해주세요:

{analysis_data}

다음을 평가해주세요:
1. 가공성 (Machinability) 평가
2. 권장 공구 및 가공 조건
3. 예상 가공 시간
4. 잠재적 가공 문제점
5. 공구 경로 최적화 제안

CNC 전문가 분석:""",

            'cost_estimation': """당신은 제조 비용 전문가입니다. 다음 DXF 도면의 제조 비용을 분석해주세요:

{analysis_data}

다음을 추정해주세요:
1. 재료 비용
2. 가공 시간 및 인건비
3. 공구 및 소모품 비용
4. 설정 시간 (Setup time)
5. 총 제조 비용 범위

비용 분석:"""
        }
    
    async def analyze_with_openai(self, analysis_data: Dict, prompt_type: str = 'analysis') -> Dict:
        """OpenAI를 사용한 분석"""
        if not self.openai_api_key:
            return {'error': 'OpenAI API 키가 설정되지 않았습니다.'}
        
        try:
            # 분석 데이터를 간결하게 요약
            summary = self._prepare_data_for_ai(analysis_data)
            
            # 프롬프트 생성
            prompt = self.prompts[prompt_type].format(
                analysis_data=json.dumps(summary, ensure_ascii=False, indent=2)
            )
            
            # OpenAI API 호출
            response = await self._call_openai_async(prompt)
            
            # 응답 파싱
            ai_analysis = {
                'model': 'gpt-4',
                'timestamp': datetime.now().isoformat(),
                'prompt_type': prompt_type,
                'analysis': response,
                'recommendations': self._extract_recommendations(response),
                'issues': self._extract_issues(response)
            }
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"OpenAI 분석 중 오류: {e}")
            return {'error': str(e)}
    
    async def analyze_with_claude(self, analysis_data: Dict, prompt_type: str = 'analysis') -> Dict:
        """Claude를 사용한 분석"""
        if not self.claude_client:
            return {'error': 'Claude API가 사용 불가능합니다.'}
        
        try:
            # 분석 데이터 준비
            summary = self._prepare_data_for_ai(analysis_data)
            
            # 프롬프트 생성
            prompt = self.prompts[prompt_type].format(
                analysis_data=json.dumps(summary, ensure_ascii=False, indent=2)
            )
            
            # Claude API 호출
            response = await self._call_claude_async(prompt)
            
            # 응답 파싱
            ai_analysis = {
                'model': 'claude-3',
                'timestamp': datetime.now().isoformat(),
                'prompt_type': prompt_type,
                'analysis': response,
                'recommendations': self._extract_recommendations(response),
                'issues': self._extract_issues(response)
            }
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Claude 분석 중 오류: {e}")
            return {'error': str(e)}
    
    async def analyze_with_gemini(self, analysis_data: Dict, prompt_type: str = 'analysis') -> Dict:
        """Gemini를 사용한 분석"""
        if not self.gemini_model:
            return {'error': 'Gemini API가 사용 불가능합니다.'}
        
        try:
            # 분석 데이터 준비
            summary = self._prepare_data_for_ai(analysis_data)
            
            # 프롬프트 생성
            prompt = self.prompts[prompt_type].format(
                analysis_data=json.dumps(summary, ensure_ascii=False, indent=2)
            )
            
            # Gemini API 호출
            response = await self._call_gemini_async(prompt)
            
            # 응답 파싱
            ai_analysis = {
                'model': 'gemini-pro',
                'timestamp': datetime.now().isoformat(),
                'prompt_type': prompt_type,
                'analysis': response,
                'recommendations': self._extract_recommendations(response),
                'issues': self._extract_issues(response)
            }
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Gemini 분석 중 오류: {e}")
            return {'error': str(e)}
    
    async def analyze_with_all(self, analysis_data: Dict, prompt_type: str = 'analysis') -> Dict:
        """모든 AI 모델을 사용한 분석"""
        tasks = []
        
        if self.openai_api_key:
            tasks.append(self.analyze_with_openai(analysis_data, prompt_type))
            
        if self.claude_client:
            tasks.append(self.analyze_with_claude(analysis_data, prompt_type))
            
        if self.gemini_model:
            tasks.append(self.analyze_with_gemini(analysis_data, prompt_type))
        
        if not tasks:
            return {'error': 'AI API가 설정되지 않았습니다.'}
        
        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        combined_analysis = {
            'timestamp': datetime.now().isoformat(),
            'models_used': [],
            'analyses': []
        }
        
        for result in results:
            if isinstance(result, dict) and 'error' not in result:
                combined_analysis['models_used'].append(result.get('model'))
                combined_analysis['analyses'].append(result)
        
        # 통합 인사이트 생성
        if len(combined_analysis['analyses']) > 1:
            combined_analysis['combined_insights'] = self._combine_insights(
                combined_analysis['analyses']
            )
        
        return combined_analysis
    
    def _prepare_data_for_ai(self, analysis_data: Dict) -> Dict:
        """AI 분석을 위한 데이터 준비 (토큰 제한 고려)"""
        summary = {
            'file_info': analysis_data.get('file_info', {}),
            'summary': analysis_data.get('summary', {}),
            'entity_breakdown': analysis_data.get('entity_breakdown', {}),
            'layer_count': len(analysis_data.get('layers', [])),
            'total_entities': analysis_data.get('total_entities', 0)
        }
        
        # 고급 분석 데이터가 있으면 추가
        if 'quality_score' in analysis_data:
            summary['quality'] = {
                'score': analysis_data.get('quality_score'),
                'grade': analysis_data.get('quality_grade')
            }
            
        if 'anomalies' in analysis_data:
            summary['anomaly_count'] = len(analysis_data.get('anomalies', []))
            summary['anomaly_types'] = list(set(
                a.get('type') for a in analysis_data.get('anomalies', [])
            ))
        
        return summary
    
    async def _call_openai_async(self, prompt: str) -> str:
        """비동기 OpenAI API 호출 (타임아웃 및 상세 오류 처리 추가)"""
        if not self.is_api_key_configured('openai'):
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
        try:
            api_call_task = asyncio.to_thread(
                openai.ChatCompletion.create, # openai 라이브러리 v0.x.x 기준
                                             # openai v1.x.x 이상은 openai.chat.completions.create 사용
                model="gpt-4", # 또는 "gpt-3.5-turbo" 등 사용 가능한 모델
                messages=[
                    {"role": "system", "content": "당신은 전문 CAD 도면 분석가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            response = await asyncio.wait_for(api_call_task, timeout=self.default_timeout)
            return response.choices[0].message.content

        except openai.error.AuthenticationError as e:
            logger.error(f"OpenAI API 인증 오류: {e}")
            raise ConnectionRefusedError(f"OpenAI API 인증 실패: {e}") # 좀 더 일반적인 예외로 변환 가능
        except openai.error.RateLimitError as e:
            logger.error(f"OpenAI API 속도 제한 오류: {e}")
            raise ConnectionAbortedError(f"OpenAI API 속도 제한 초과: {e}") # 좀 더 일반적인 예외로 변환 가능
        except openai.error.APIError as e:
            logger.error(f"OpenAI API 일반 오류: {e}")
            raise RuntimeError(f"OpenAI API 오류: {e}")
        except asyncio.TimeoutError:
            logger.error("OpenAI API 호출 시간 초과")
            raise TimeoutError("OpenAI API 호출 시간 초과")
        except Exception as e: # 그 외 예상치 못한 오류
            logger.error(f"OpenAI API 호출 중 알 수 없는 오류: {e}")
            raise RuntimeError(f"OpenAI API 호출 중 알 수 없는 오류: {e}")
    
    async def _call_claude_async(self, prompt: str) -> str:
        """비동기 Claude API 호출 (타임아웃 및 상세 오류 처리 추가)"""
        if not self.is_api_key_configured('claude'):
            raise ValueError("Claude API 키가 설정되지 않았거나 클라이언트 초기화에 실패했습니다.")
        try:
            api_call_task = asyncio.to_thread(
                self.claude_client.messages.create,
                model="claude-3-sonnet-20240229", # 또는 다른 claude 모델
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            response = await asyncio.wait_for(api_call_task, timeout=self.default_timeout)
            return response.content[0].text
            
        except anthropic.APIConnectionError as e:
            logger.error(f"Claude API 연결 오류: {e}")
            raise ConnectionError(f"Claude API 연결 실패: {e}")
        except anthropic.RateLimitError as e:
            logger.error(f"Claude API 속도 제한 오류: {e}")
            raise ConnectionAbortedError(f"Claude API 속도 제한 초과: {e}")
        except anthropic.APIStatusError as e: # 일반적인 API 오류 (HTTP 상태 코드 4xx, 5xx 등)
            logger.error(f"Claude API 상태 오류 (status_code={e.status_code}): {e.message}")
            raise RuntimeError(f"Claude API 오류 (status={e.status_code}): {e.message}")
        except asyncio.TimeoutError:
            logger.error("Claude API 호출 시간 초과")
            raise TimeoutError("Claude API 호출 시간 초과")
        except Exception as e:
            logger.error(f"Claude API 호출 중 알 수 없는 오류: {e}")
            raise RuntimeError(f"Claude API 호출 중 알 수 없는 오류: {e}")
    
    async def _call_gemini_async(self, prompt: str) -> str:
        """비동기 Gemini API 호출 (타임아웃 및 상세 오류 처리 추가)"""
        if not self.is_api_key_configured('gemini'):
            raise ValueError("Gemini API 키가 설정되지 않았거나 모델 초기화에 실패했습니다.")
        try:
            api_call_task = asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    max_output_tokens=1500,
                    temperature=0.7
                )
            )
            response = await asyncio.wait_for(api_call_task, timeout=self.default_timeout)
            return response.text
            
        except google.api_core.exceptions.GoogleAPIError as e: # Gemini API의 일반적인 예외
            logger.error(f"Gemini API 오류: {e}")
            if isinstance(e, google.api_core.exceptions.PermissionDenied):
                 raise ConnectionRefusedError(f"Gemini API 접근 거부: {e}")
            elif isinstance(e, google.api_core.exceptions.ResourceExhausted):
                 raise ConnectionAbortedError(f"Gemini API 리소스 고갈 (속도 제한 등): {e}")
            raise RuntimeError(f"Gemini API 오류: {e}")
        except asyncio.TimeoutError:
            logger.error("Gemini API 호출 시간 초과")
            raise TimeoutError("Gemini API 호출 시간 초과")
        except Exception as e:
            logger.error(f"Gemini API 호출 중 알 수 없는 오류: {e}")
            raise RuntimeError(f"Gemini API 호출 중 알 수 없는 오류: {e}")
    
    def _extract_recommendations(self, ai_response: str) -> List[str]:
        """AI 응답에서 권장사항 추출"""
        recommendations = []
        
        # 간단한 패턴 매칭으로 권장사항 추출
        lines = ai_response.split('\n')
        in_recommendations = False
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['권장', '제안', '추천', 'recommend']):
                in_recommendations = True
                continue
                
            if in_recommendations and line.strip():
                if line.strip().startswith(('-', '*', '•', '1', '2', '3')):
                    recommendations.append(line.strip().lstrip('-*•0123456789. '))
                elif len(recommendations) > 0:
                    break
        
        return recommendations[:5]  # 상위 5개만
    
    def _extract_issues(self, ai_response: str) -> List[str]:
        """AI 응답에서 문제점 추출"""
        issues = []
        
        lines = ai_response.split('\n')
        in_issues = False
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['문제', '이슈', 'issue', 'problem']):
                in_issues = True
                continue
                
            if in_issues and line.strip():
                if line.strip().startswith(('-', '*', '•', '1', '2', '3')):
                    issues.append(line.strip().lstrip('-*•0123456789. '))
                elif len(issues) > 0:
                    break
        
        return issues[:5]
    
    def _combine_insights(self, analyses: List[Dict]) -> Dict:
        """여러 AI 분석 결과 통합"""
        combined = {
            'common_issues': [],
            'common_recommendations': [],
            'confidence_level': 'high' if len(analyses) > 1 else 'medium'
        }
        
        # 공통 이슈 찾기
        all_issues = []
        for analysis in analyses:
            all_issues.extend(analysis.get('issues', []))
        
        # 중복 제거하고 빈도순 정렬
        issue_counts = {}
        for issue in all_issues:
            # 유사한 이슈 그룹화 (간단한 구현)
            key = issue.lower()[:30]
            issue_counts[key] = issue_counts.get(key, 0) + 1
        
        combined['common_issues'] = [
            issue for issue, count in sorted(
                issue_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
        ]
        
        # 공통 권장사항도 동일하게 처리
        all_recommendations = []
        for analysis in analyses:
            all_recommendations.extend(analysis.get('recommendations', []))
        
        rec_counts = {}
        for rec in all_recommendations:
            key = rec.lower()[:30]
            rec_counts[key] = rec_counts.get(key, 0) + 1
        
        combined['common_recommendations'] = [
            rec for rec, count in sorted(
                rec_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
        ]
        
        return combined
    
    def generate_ai_report(self, ai_analysis: Dict) -> str:
        """AI 분석 리포트 생성"""
        report = "# 🤖 AI 도면 분석 리포트\n\n"
        
        if 'error' in ai_analysis:
            report += f"⚠️ 오류: {ai_analysis['error']}\n"
            return report
        
        # 단일 모델 분석
        if 'model' in ai_analysis:
            report += f"**분석 모델**: {ai_analysis['model']}\n"
            report += f"**분석 시간**: {ai_analysis['timestamp']}\n\n"
            
            report += "## 📊 분석 결과\n"
            report += ai_analysis.get('analysis', '분석 결과 없음')
            report += "\n\n"
            
            if ai_analysis.get('issues'):
                report += "## 🚨 발견된 문제점\n"
                for issue in ai_analysis['issues']:
                    report += f"- {issue}\n"
                report += "\n"
            
            if ai_analysis.get('recommendations'):
                report += "## 💡 권장사항\n"
                for rec in ai_analysis['recommendations']:
                    report += f"- {rec}\n"
                report += "\n"
        
        # 복수 모델 분석
        elif 'analyses' in ai_analysis:
            report += f"**사용 모델**: {', '.join(ai_analysis.get('models_used', []))}\n"
            report += f"**분석 시간**: {ai_analysis['timestamp']}\n\n"
            
            # 각 모델별 분석
            for i, analysis in enumerate(ai_analysis['analyses'], 1):
                report += f"### {analysis['model']} 분석\n"
                report += analysis.get('analysis', '')[:500] + "...\n\n"
            
            # 통합 인사이트
            if 'combined_insights' in ai_analysis:
                insights = ai_analysis['combined_insights']
                
                report += "## 🔍 통합 인사이트\n"
                
                if insights.get('common_issues'):
                    report += "\n### 공통 문제점\n"
                    for issue in insights['common_issues']:
                        report += f"- {issue}\n"
                
                if insights.get('common_recommendations'):
                    report += "\n### 공통 권장사항\n"
                    for rec in insights['common_recommendations']:
                        report += f"- {rec}\n"
                
                report += f"\n**신뢰도**: {insights.get('confidence_level', 'medium').upper()}\n"
        
        return report
    
    async def interactive_chat(self, question: str, context: Dict) -> str:
        """대화형 질의응답"""
        prompt = f"""DXF 도면 분석 컨텍스트:
{json.dumps(self._prepare_data_for_ai(context), ensure_ascii=False, indent=2)}

사용자 질문: {question}

전문가 답변:"""
        
        if self.openai_api_key:
            try:
                response = await self._call_openai_async(prompt)
                return response
            except:
                pass
        
        if self.claude_client:
            try:
                response = await self._call_claude_async(prompt)
                return response
            except:
                pass
        
        return "AI API가 사용 불가능합니다." 