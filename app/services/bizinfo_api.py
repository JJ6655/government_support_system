"""
기업마당 API 호출 및 데이터 처리 모듈
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlencode
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BizinfoAPI:
    """기업마당 API 클라이언트"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        self.session = requests.Session()
        
    def fetch_announcements(self, search_cnt: int = 50, hashtags: str = None) -> List[Dict]:
        """
        기업마당 API에서 지원사업 공고 데이터를 가져옵니다.
        
        Args:
            search_cnt: 조회할 데이터 수 (기본 50개)
            hashtags: 해시태그 필터링 (예: "경남", "경상남도")
            
        Returns:
            List[Dict]: 공고 데이터 리스트
        """
        try:
            params = {
                'crtfcKey': self.api_key,
                'dataType': 'json',
                'searchCnt': str(search_cnt)
            }
            
            # hashtags 파라미터가 있으면 추가
            if hashtags:
                params['hashtags'] = hashtags
            
            if hashtags:
                logger.info(f"기업마당 API 호출 시작 - 요청 개수: {search_cnt}, 해시태그 필터: '{hashtags}'")
            else:
                logger.info(f"기업마당 API 호출 시작 - 요청 개수: {search_cnt}")
            
            # API 호출
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # JSON 파싱
            data = response.json()
            
            if 'jsonArray' not in data:
                logger.error("API 응답에서 jsonArray를 찾을 수 없습니다.")
                return []
            
            announcements = data['jsonArray']
            logger.info(f"API 응답 성공 - 받은 데이터: {len(announcements)}개")
            
            # 데이터 정제
            processed_announcements = []
            for announcement in announcements:
                processed = self._process_announcement(announcement)
                if processed:
                    processed_announcements.append(processed)
            
            logger.info(f"데이터 처리 완료 - 처리된 데이터: {len(processed_announcements)}개")
            return processed_announcements
            
        except requests.RequestException as e:
            logger.error(f"API 호출 오류: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            return []
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            return []
    
    def _process_announcement(self, raw_data: Dict) -> Optional[Dict]:
        """
        원본 API 데이터를 처리하여 정제된 형태로 변환
        
        Args:
            raw_data: 원본 API 응답 데이터
            
        Returns:
            Dict: 정제된 공고 데이터
        """
        try:
            # 필수 필드 확인
            if not raw_data.get('pblancId'):
                logger.warning("pblancId가 없는 데이터 건너뛰기")
                return None
            
            # 날짜 처리
            created_time = self._parse_datetime(raw_data.get('creatPnttm'))
            
            # 정제된 데이터 구조
            processed_data = {
                'pblancId': (raw_data.get('pblancId') or '').strip(),
                'pblancNm': (raw_data.get('pblancNm') or '').strip(),
                'jrsdInsttNm': (raw_data.get('jrsdInsttNm') or '').strip(),
                'excInsttNm': (raw_data.get('excInsttNm') or '').strip(),
                'bsnsSumryCn': self._clean_html(raw_data.get('bsnsSumryCn') or ''),
                'trgetNm': (raw_data.get('trgetNm') or '').strip(),
                'pblancUrl': self._process_url(raw_data.get('pblancUrl')),
                'rceptEngnHmpgUrl': (raw_data.get('rceptEngnHmpgUrl') or '').strip(),
                'flpthNm': (raw_data.get('flpthNm') or '').strip(),
                'printFlpthNm': (raw_data.get('printFlpthNm') or '').strip(),
                'printFileNm': (raw_data.get('printFileNm') or '').strip(),
                'fileNm': (raw_data.get('fileNm') or '').strip(),
                'reqstBeginEndDe': (raw_data.get('reqstBeginEndDe') or '').strip(),
                'reqstMthPapersCn': (raw_data.get('reqstMthPapersCn') or '').strip(),
                'refrncNm': (raw_data.get('refrncNm') or '').strip(),
                'pldirSportRealmLclasCodeNm': (raw_data.get('pldirSportRealmLclasCodeNm') or '').strip(),
                'pldirSportRealmMlsfcCodeNm': (raw_data.get('pldirSportRealmMlsfcCodeNm') or '').strip(),
                'hashtags': (raw_data.get('hashtags') or '').strip(),
                'totCnt': self._safe_int(raw_data.get('totCnt', 0)),
                'inqireCo': self._safe_int(raw_data.get('inqireCo', 0)),
                'creatPnttm': created_time,
                'fetch_datetime': datetime.now()
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"데이터 처리 오류 (pblancId: {raw_data.get('pblancId')}): {e}")
            return None
    
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거 및 텍스트 정리"""
        if not text:
            return ''
        
        # 간단한 HTML 태그 제거 (더 정교한 처리가 필요하면 BeautifulSoup 사용)
        import re
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """날짜 문자열을 datetime 객체로 변환"""
        if not datetime_str:
            return None
            
        try:
            # "2025-08-07 14:52:17" 형태의 문자열 파싱
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # "20250807" 형태의 날짜만 있는 경우
                return datetime.strptime(datetime_str[:8], "%Y%m%d")
            except:
                logger.warning(f"날짜 파싱 실패: {datetime_str}")
                return None
    
    def _safe_int(self, value) -> int:
        """안전한 정수 변환"""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    def _process_url(self, url: str) -> str:
        """URL 처리 - 기업마당 도메인이 없으면 추가"""
        if not url:
            return ''
        
        url = url.strip()
        if not url:
            return ''
        
        # 이미 http:// 또는 https://로 시작하면 그대로 반환
        if url.startswith(('http://', 'https://')):
            return url
        
        # 기업마당 도메인 추가
        if url.startswith('/'):
            return f"https://www.bizinfo.go.kr{url}"
        else:
            return f"https://www.bizinfo.go.kr/{url}"

class BizinfoDataProcessor:
    """기업마당 데이터 후처리 클래스"""
    
    def __init__(self):
        self.duplicate_check_cache = set()
    
    def filter_new_announcements(self, announcements: List[Dict], existing_ids: set) -> List[Dict]:
        """
        기존 데이터와 중복되지 않는 새로운 공고만 필터링
        
        Args:
            announcements: 새로 가져온 공고 데이터
            existing_ids: 이미 DB에 있는 공고 ID 집합
            
        Returns:
            List[Dict]: 새로운 공고 데이터만
        """
        new_announcements = []
        
        for announcement in announcements:
            pblancId = announcement.get('pblancId')
            if pblancId and pblancId not in existing_ids:
                new_announcements.append(announcement)
                existing_ids.add(pblancId)  # 캐시 업데이트
        
        logger.info(f"중복 제거 완료 - 새로운 공고: {len(new_announcements)}개")
        return new_announcements
    
    def validate_announcement_data(self, announcement: Dict) -> bool:
        """
        공고 데이터 유효성 검사
        
        Args:
            announcement: 공고 데이터
            
        Returns:
            bool: 유효한 데이터 여부
        """
        # 필수 필드 확인
        required_fields = ['pblancId', 'pblancNm', 'jrsdInsttNm']
        
        for field in required_fields:
            if not announcement.get(field):
                logger.warning(f"필수 필드 누락: {field}")
                return False
        
        # pblancId 길이 제한 (데이터베이스 제약사항)
        if len(announcement.get('pblancId', '')) > 50:
            logger.warning(f"pblancId 길이 초과: {announcement.get('pblancId')}")
            return False
            
        return True

def test_bizinfo_api():
    """기업마당 API 테스트 함수"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('BIZINFO_API_KEY')
    
    if not api_key:
        print("BIZINFO_API_KEY가 설정되지 않았습니다.")
        return False
    
    try:
        # API 클라이언트 생성
        api_client = BizinfoAPI(api_key)
        
        # 테스트 1: 경남 필터링으로 5개 데이터 가져오기
        print("=== 경남 필터링 테스트 ===")
        announcements = api_client.fetch_announcements(search_cnt=5, hashtags="경남")
        
        print(f"가져온 데이터 수: {len(announcements)}")
        
        if announcements:
            print("\\n경남 필터링 결과:")
            for i, announcement in enumerate(announcements[:3], 1):
                print(f"{i}. 공고명: {announcement.get('pblancNm')}")
                print(f"   소관기관: {announcement.get('jrsdInsttNm')}")
                print(f"   해시태그: {announcement.get('hashtags')}")
                print()
        
        # 테스트 2: 필터링 없이 비교
        print("=== 필터링 없음 비교 테스트 ===")
        all_announcements = api_client.fetch_announcements(search_cnt=5)
        print(f"전체 데이터 수: {len(all_announcements)}")
        
        if all_announcements:
            print("\\n전체 데이터 예시:")
            for i, announcement in enumerate(all_announcements[:3], 1):
                hashtags = announcement.get('hashtags', '')
                is_gyeongnam = '경남' in hashtags or '경상남도' in hashtags
                print(f"{i}. 공고명: {announcement.get('pblancNm')}")
                print(f"   소관기관: {announcement.get('jrsdInsttNm')}")
                print(f"   경남 관련: {'Yes' if is_gyeongnam else 'No'}")
                print(f"   해시태그: {hashtags}")
                print()
            
        return True
        
    except Exception as e:
        print(f"테스트 실패: {e}")
        return False

if __name__ == "__main__":
    test_bizinfo_api()