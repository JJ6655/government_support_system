"""
Gemini API를 활용한 AI 기반 지역 분류 모듈
"""

import os
import json
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    print("google-generativeai 패키지가 설치되지 않았습니다.")
    print("pip install google-generativeai 로 설치해주세요.")
    genai = None

logger = logging.getLogger(__name__)

@dataclass
class AIClassificationResult:
    """AI 분류 결과 데이터 클래스"""
    region_code: str
    confidence: float
    method: str = 'ai'
    reason: str = ''
    api_usage: Dict = None

class GeminiClassifier:
    """Gemini API 기반 지역 분류기"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-lite"):
        if not genai:
            raise ImportError("google-generativeai 패키지가 필요합니다.")
            
        self.api_key = api_key
        self.model_name = model_name
        self.batch_size = 4
        
        # API 설정
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # 지역 코드 매핑 (AI가 이해할 수 있도록 설명 추가)
        self.region_mapping = {
            'ALL': '전국 (모든 지역 대상)',
            'GYEONGNAM': '경상남도 (광역자치단체)',
            'CHANGWON': '창원시 (경남 시)',
            'GIMHAE': '김해시 (경남 시)',
            'JINJU': '진주시 (경남 시)',
            'YANGSAN': '양산시 (경남 시)',
            'GEOJE': '거제시 (경남 시)',
            'TONGYEONG': '통영시 (경남 시)',
            'SACHEON': '사천시 (경남 시)',
            'MIRYANG': '밀양시 (경남 시)',
            'HAMAN': '함안군 (경남 군)',
            'CHANGNYEONG': '창녕군 (경남 군)',
            'GOSEONG': '고성군 (경남 군)',
            'NAMHAE': '남해군 (경남 군)',
            'HADONG': '하동군 (경남 군)',
            'SANCHEONG': '산청군 (경남 군)',
            'HAMYANG': '함양군 (경남 군)',
            'GEOCHANG': '거창군 (경남 군)',
            'HAPCHEON': '합천군 (경남 군)',
            'UIRYEONG': '의령군 (경남 군)',
            # 기타 주요 광역시도
            'SEOUL': '서울특별시',
            'BUSAN': '부산광역시',
            'DAEGU': '대구광역시',
            'INCHEON': '인천광역시',
            'GWANGJU': '광주광역시',
            'DAEJEON': '대전광역시',
            'ULSAN': '울산광역시',
            'SEJONG': '세종특별자치시',
            'GYEONGGI': '경기도',
            'GANGWON': '강원특별자치도',
            'CHUNGBUK': '충청북도',
            'CHUNGNAM': '충청남도',
            'JEONBUK': '전북특별자치도',
            'JEONNAM': '전라남도',
            'GYEONGBUK': '경상북도',
            'JEJU': '제주특별자치도'
        }
        
        # API 사용량 추적
        self.api_usage_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens_used': 0
        }
    
    def classify_batch(self, announcements: List[Dict]) -> List[AIClassificationResult]:
        """
        여러 공고를 배치로 분류합니다.
        
        Args:
            announcements: 분류할 공고 데이터 리스트
            
        Returns:
            List[AIClassificationResult]: 분류 결과 리스트
        """
        results = []
        
        # 배치 크기로 나누어 처리
        for i in range(0, len(announcements), self.batch_size):
            batch = announcements[i:i + self.batch_size]
            
            try:
                batch_results = self._process_batch(batch)
                results.extend(batch_results)
                
                # API 호출 간 잠시 대기 (Rate limiting 방지)
                if i + self.batch_size < len(announcements):
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"배치 처리 오류 (batch {i//self.batch_size + 1}): {e}")
                
                # 실패한 배치는 기본값으로 처리
                for announcement in batch:
                    results.append(AIClassificationResult(
                        region_code=None,
                        confidence=0.0,
                        reason=f"AI 분류 실패: {str(e)}",
                        api_usage={'error': str(e)}
                    ))
        
        return results
    
    def _process_batch(self, batch: List[Dict]) -> List[AIClassificationResult]:
        """배치 데이터를 처리합니다."""
        
        # 프롬프트 생성
        prompt = self._create_batch_prompt(batch)
        
        # API 호출
        start_time = time.time()
        response = self.model.generate_content(prompt)
        end_time = time.time()
        
        # 사용량 통계 업데이트
        self.api_usage_stats['total_requests'] += 1
        
        if response and response.text:
            self.api_usage_stats['successful_requests'] += 1
            
            # 토큰 수 추정 (정확한 값은 API 응답에 따라 다를 수 있음)
            estimated_tokens = len(prompt.split()) + len(response.text.split())
            self.api_usage_stats['total_tokens_used'] += estimated_tokens
            
            # 응답 파싱
            return self._parse_batch_response(response.text, batch, {
                'request_time': end_time - start_time,
                'estimated_tokens': estimated_tokens
            })
        else:
            self.api_usage_stats['failed_requests'] += 1
            raise Exception("API 응답이 비어있습니다.")
    
    def _create_batch_prompt(self, batch: List[Dict]) -> str:
        """배치 처리용 프롬프트를 생성합니다."""
        
        region_list = "\n".join([f"- {code}: {desc}" for code, desc in self.region_mapping.items()])
        
        announcements_text = ""
        for i, announcement in enumerate(batch, 1):
            announcements_text += f"""
=== 공고 {i} ===
공고명: {announcement.get('pblancNm', '')}
소관기관: {announcement.get('jrsdInsttNm', '')}
수행기관: {announcement.get('excInsttNm', '')}
사업개요: {announcement.get('bsnsSumryCn', '')[:200]}...
문의처: {announcement.get('refrncNm', '')}

"""
        
        prompt = f"""
당신은 한국의 정부지원사업 데이터를 지역별로 분류하는 전문가입니다.

다음 지원사업 공고들을 분석하여 각각 어느 지역에 해당하는지 분류해주세요.

【분류 기준】
1. 공고명에 [지역명] 패턴이 있으면 최우선 적용
2. 소관기관이 중앙부처면 보통 전국(ALL) 사업
3. 소관기관이 지방자치단체면 해당 지역 사업
4. 수행기관의 지역성 고려
5. 사업 내용에서 특정 지역 언급 확인

【가능한 지역 코드】
{region_list}

【분류할 공고 데이터】
{announcements_text}

【응답 형식】 (JSON 형태로만 응답)
{{
  "results": [
    {{
      "announcement_id": 1,
      "region_code": "GYEONGNAM",
      "confidence": 0.85,
      "reason": "공고명에 [경남] 패턴 확인, 사천시는 경남소속"
    }},
    {{
      "announcement_id": 2,
      "region_code": "ALL", 
      "confidence": 0.90,
      "reason": "중앙부처 소관으로 전국 사업 판단"
    }}
  ]
}}

중요: 
- 반드시 JSON 형식으로만 응답
- 17개 광역시도 코드만 사용 (기초지자체 코드 금지)
- 고령군, 봉화군 등 기초지자체는 GYEONGBUK으로 분류
- 창원시, 진주시 등 경남 시군은 GYEONGNAM으로 분류
- 확신이 없는 경우 confidence를 낮게 설정
"""
        
        return prompt
    
    def _parse_batch_response(self, response_text: str, batch: List[Dict], usage_info: Dict) -> List[AIClassificationResult]:
        """API 응답을 파싱하여 결과를 반환합니다."""
        
        try:
            # JSON 응답 파싱
            # 응답에서 JSON 부분만 추출
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("JSON 형식을 찾을 수 없습니다.")
            
            json_text = response_text[json_start:json_end]
            response_data = json.loads(json_text)
            
            if 'results' not in response_data:
                raise ValueError("응답에 results 키가 없습니다.")
            
            results = []
            for i, result_data in enumerate(response_data['results']):
                if i >= len(batch):
                    break
                
                region_code = result_data.get('region_code')
                confidence = float(result_data.get('confidence', 0.0))
                reason = result_data.get('reason', '')
                
                # 지역 코드 유효성 검사
                if region_code not in self.region_mapping:
                    logger.warning(f"유효하지 않은 지역 코드: {region_code}")
                    region_code = None
                    confidence = 0.0
                    reason = f"유효하지 않은 지역 코드: {region_code}"
                
                results.append(AIClassificationResult(
                    region_code=region_code,
                    confidence=confidence,
                    reason=reason,
                    api_usage={
                        **usage_info,
                        'model': self.model_name,
                        'timestamp': datetime.now().isoformat()
                    }
                ))
            
            # 결과 수가 배치 크기와 다를 경우 부족한 부분을 기본값으로 채움
            while len(results) < len(batch):
                results.append(AIClassificationResult(
                    region_code=None,
                    confidence=0.0,
                    reason="AI 응답 파싱 오류 - 결과 누락",
                    api_usage=usage_info
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"응답 파싱 오류: {e}")
            logger.error(f"응답 텍스트: {response_text[:500]}...")
            
            # 파싱 실패시 기본값 반환
            return [AIClassificationResult(
                region_code=None,
                confidence=0.0,
                reason=f"AI 응답 파싱 실패: {str(e)}",
                api_usage={**usage_info, 'parse_error': str(e)}
            ) for _ in batch]
    
    def get_usage_stats(self) -> Dict:
        """API 사용량 통계를 반환합니다."""
        success_rate = 0
        if self.api_usage_stats['total_requests'] > 0:
            success_rate = (self.api_usage_stats['successful_requests'] / 
                          self.api_usage_stats['total_requests']) * 100
        
        return {
            **self.api_usage_stats,
            'success_rate': round(success_rate, 2),
            'average_tokens_per_request': (
                self.api_usage_stats['total_tokens_used'] // 
                max(self.api_usage_stats['successful_requests'], 1)
            )
        }
    
    def reset_usage_stats(self):
        """사용량 통계를 초기화합니다."""
        self.api_usage_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens_used': 0
        }

def test_gemini_classifier():
    """Gemini 분류기 테스트 함수"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("GEMINI_API_KEY가 설정되지 않았습니다.")
        return False
    
    try:
        classifier = GeminiClassifier(api_key)
        
        # 테스트 데이터
        test_announcements = [
            {
                'pblancNm': '[경남] 사천시 2025년 중소기업 지원사업',
                'jrsdInsttNm': '사천시',
                'excInsttNm': '사천시산업진흥원',
                'bsnsSumryCn': '사천시 소재 중소기업을 대상으로 하는 지원사업입니다.',
                'refrncNm': '사천시청 경제정책과 055-831-2345'
            },
            {
                'pblancNm': '2025년 AI 기술개발 지원사업',
                'jrsdInsttNm': '과학기술정보통신부',
                'excInsttNm': '정보통신산업진흥원',
                'bsnsSumryCn': '전국의 AI 기업을 대상으로 하는 기술개발 지원사업입니다.',
                'refrncNm': 'NIPA 담당자 043-931-5823'
            }
        ]
        
        print("Gemini API 분류 테스트 시작...")
        results = classifier.classify_batch(test_announcements)
        
        print(f"\\n분류 결과: {len(results)}개")
        for i, result in enumerate(results, 1):
            print(f"\\n공고 {i}:")
            print(f"  지역 코드: {result.region_code}")
            print(f"  신뢰도: {result.confidence:.2f}")
            print(f"  근거: {result.reason}")
        
        # 사용량 통계
        stats = classifier.get_usage_stats()
        print(f"\\nAPI 사용량 통계:")
        print(f"  총 요청: {stats['total_requests']}")
        print(f"  성공률: {stats['success_rate']}%")
        print(f"  추정 토큰 사용량: {stats['total_tokens_used']}")
        
        return True
        
    except Exception as e:
        print(f"테스트 실패: {e}")
        return False

if __name__ == "__main__":
    test_gemini_classifier()