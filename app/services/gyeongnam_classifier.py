"""
경남 특화 지역 분류기
21개 지역 시스템용
"""

from .gyeongnam_region_service import gyeongnam_region_service
from .gemini_classifier import GeminiClassifier
import logging

logger = logging.getLogger(__name__)

class GyeongnamRegionClassifier:
    """경남 특화 지역 분류기"""
    
    def __init__(self):
        self.region_service = gyeongnam_region_service
        
        # Gemini API 키가 있는 경우에만 AI 분류기 초기화
        import os
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if gemini_api_key:
            try:
                self.ai_classifier = GeminiClassifier(gemini_api_key)
            except Exception as e:
                logger.warning(f"Gemini AI 분류기 초기화 실패: {e}")
                self.ai_classifier = None
        else:
            self.ai_classifier = None
    
    def classify_announcement(self, announcement_data):
        """공고 데이터 지역 분류"""
        try:
            # 1차: 키워드 기반 분류
            result = self.region_service.classify_announcement(announcement_data)
            
            # 신뢰도가 높으면 키워드 분류 결과 반환
            if result['confidence'] >= 0.7:
                return ClassificationResult(
                    region_code=result['region_code'],
                    confidence=result['confidence'],
                    method='keyword'
                )
            
            # 2차: AI 분류 (신뢰도가 낮은 경우)
            if self.ai_classifier:
                try:
                    ai_result = self.ai_classifier.classify_region(announcement_data)
                    if ai_result and ai_result.confidence >= 0.6:
                        # AI 결과를 경남 21개 지역 시스템에 매핑
                        mapped_code = self._map_ai_result_to_gyeongnam(ai_result.region_code)
                        return ClassificationResult(
                            region_code=mapped_code,
                            confidence=ai_result.confidence,
                            method='ai'
                        )
                except Exception as e:
                    logger.warning(f"AI 분류 실패: {e}")
            
            # 기본값: 전국
            return ClassificationResult(
                region_code='ALL',
                confidence=0.1,
                method='default'
            )
            
        except Exception as e:
            logger.error(f"지역 분류 오류: {e}")
            return ClassificationResult(
                region_code='ALL',
                confidence=0.0,
                method='error'
            )
    
    def _map_ai_result_to_gyeongnam(self, ai_region_code):
        """AI 분류 결과를 경남 시스템에 매핑"""
        # 경남 관련 코드 매핑
        gyeongnam_mapping = {
            'GYEONGNAM': 'GYEONGNAM',
            'GYEONGNAM_01': 'GYEONGNAM_01',  # 창원
            'GYEONGNAM_02': 'GYEONGNAM_02',  # 진주
            # ... 기타 경남 지역 매핑
        }
        
        # AI가 경남 지역으로 분류했으면 해당 코드 반환
        if ai_region_code in gyeongnam_mapping:
            return gyeongnam_mapping[ai_region_code]
        
        # AI가 경남 이외 지역으로 분류했으면 OTHER 반환
        if ai_region_code and ai_region_code != 'ALL':
            return 'OTHER'
        
        # 그 외는 전국
        return 'ALL'

class ClassificationResult:
    """분류 결과 클래스"""
    
    def __init__(self, region_code, confidence, method):
        self.region_code = region_code
        self.confidence = confidence
        self.method = method
        
        # 지역 정보 추가
        region_info = gyeongnam_region_service.get_region_info(region_code)
        self.region_name = region_info['name'] if region_info else '알 수 없음'
        self.region_type = region_info['type'] if region_info else 'unknown'