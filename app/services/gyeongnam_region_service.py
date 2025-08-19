"""
경상남도 특화 지역 분류 서비스
21개 지역으로 단순화된 시스템
"""

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

class GyeongnamRegionMapper:
    """경남 특화 지역 매핑 클래스"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('SUPABASE_HOST'),
            'user': os.getenv('SUPABASE_USER', 'postgres'),
            'password': os.getenv('SUPABASE_PASSWORD'),
            'database': os.getenv('SUPABASE_DB', 'postgres'),
            'port': int(os.getenv('SUPABASE_PORT', '5432'))
        }
        
        # 21개 지역 데이터
        self.regions = {
            'ALL': {'name': '전국', 'type': 'national', 'parent': None},
            'GYEONGNAM': {'name': '경상남도', 'type': 'provincial', 'parent': None},
            'OTHER': {'name': '경남 이외 지역', 'type': 'other', 'parent': None},
            'GYEONGNAM_01': {'name': '창원시', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_02': {'name': '진주시', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_03': {'name': '통영시', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_04': {'name': '사천시', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_05': {'name': '김해시', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_06': {'name': '밀양시', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_07': {'name': '거제시', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_08': {'name': '양산시', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_09': {'name': '의령군', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_10': {'name': '함안군', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_11': {'name': '창녕군', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_12': {'name': '고성군', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_13': {'name': '남해군', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_14': {'name': '하동군', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_15': {'name': '산청군', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_16': {'name': '함양군', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_17': {'name': '거창군', 'type': 'municipal', 'parent': 'GYEONGNAM'},
            'GYEONGNAM_18': {'name': '합천군', 'type': 'municipal', 'parent': 'GYEONGNAM'}
        }
        
        # 경남 지역 키워드 매핑
        self.keyword_mappings = {
            # 시 지역
            '창원': 'GYEONGNAM_01',
            '진주': 'GYEONGNAM_02', 
            '통영': 'GYEONGNAM_03',
            '사천': 'GYEONGNAM_04',
            '김해': 'GYEONGNAM_05',
            '밀양': 'GYEONGNAM_06',
            '거제': 'GYEONGNAM_07',
            '양산': 'GYEONGNAM_08',
            
            # 군 지역
            '의령': 'GYEONGNAM_09',
            '함안': 'GYEONGNAM_10',
            '창녕': 'GYEONGNAM_11',
            '고성': 'GYEONGNAM_12',
            '남해': 'GYEONGNAM_13',
            '하동': 'GYEONGNAM_14',
            '산청': 'GYEONGNAM_15',
            '함양': 'GYEONGNAM_16',
            '거창': 'GYEONGNAM_17',
            '합천': 'GYEONGNAM_18',
            
            # 상위 지역
            '경남': 'GYEONGNAM',
            '경상남도': 'GYEONGNAM',
            '전국': 'ALL',
            '전 지역': 'ALL',
            '모든 지역': 'ALL'
        }
        
        # 다른 지역 키워드 (경남 이외)
        self.other_region_keywords = [
            '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종',
            '경기', '강원', '충북', '충남', '전북', '전남', '경북', '제주',
            '수도권', '영남권', '호남권', '충청권'
        ]
    
    def get_region_info(self, region_code):
        """지역 정보 조회"""
        return self.regions.get(region_code)
    
    def get_all_regions(self):
        """모든 지역 정보 반환"""
        return self.regions
    
    def get_gyeongnam_cities(self):
        """경남 18개 시군 반환"""
        return {code: info for code, info in self.regions.items() 
                if info['type'] == 'municipal'}
    
    def classify_by_keywords(self, text):
        """키워드 기반 지역 분류"""
        if not text:
            return None, 0.0
        
        text = text.lower()
        
        # 경남 세부 지역 먼저 확인
        for keyword, region_code in self.keyword_mappings.items():
            if keyword in text:
                confidence = 0.9 if len(keyword) >= 2 else 0.7
                return region_code, confidence
        
        # 경남 이외 지역 키워드 확인
        for keyword in self.other_region_keywords:
            if keyword in text:
                return 'OTHER', 0.8
        
        return None, 0.0
    
    def classify_announcement(self, announcement_data):
        """공고 데이터 기반 지역 분류"""
        # 분류할 텍스트 수집
        search_text = ""
        
        if announcement_data.get('pblancNm'):
            search_text += announcement_data['pblancNm'] + " "
        if announcement_data.get('jrsdInsttNm'):
            search_text += announcement_data['jrsdInsttNm'] + " "
        if announcement_data.get('excInsttNm'):
            search_text += announcement_data['excInsttNm'] + " "
        if announcement_data.get('bsnsSumryCn'):
            search_text += announcement_data['bsnsSumryCn'] + " "
        
        # 키워드 기반 분류
        region_code, confidence = self.classify_by_keywords(search_text)
        
        if region_code:
            return {
                'region_code': region_code,
                'region_name': self.regions[region_code]['name'],
                'confidence': confidence,
                'method': 'keyword'
            }
        
        # 분류 실패 시 전국으로 분류
        return {
            'region_code': 'ALL',
            'region_name': '전국',
            'confidence': 0.1,
            'method': 'default'
        }

# 글로벌 인스턴스
gyeongnam_region_service = GyeongnamRegionMapper()