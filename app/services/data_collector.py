"""
데이터 수집 및 분류 통합 서비스
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Tuple
from dotenv import load_dotenv

from .bizinfo_api import BizinfoAPI, BizinfoDataProcessor
from .gyeongnam_classifier import GyeongnamRegionClassifier
from .gemini_classifier import GeminiClassifier
from .collection_progress import progress_tracker
from ..models.announcement import AnnouncementModel

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCollectionService:
    """데이터 수집 및 분류 통합 서비스"""
    
    def __init__(self):
        # API 키 설정
        self.bizinfo_api_key = os.getenv('BIZINFO_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.bizinfo_api_key:
            raise ValueError("BIZINFO_API_KEY가 설정되지 않았습니다.")
        
        # 서비스 초기화
        self.bizinfo_api = BizinfoAPI(self.bizinfo_api_key)
        self.data_processor = BizinfoDataProcessor()
        self.keyword_classifier = GyeongnamRegionClassifier()
        
        # Gemini API가 설정된 경우에만 초기화
        self.ai_classifier = None
        if self.gemini_api_key:
            try:
                self.ai_classifier = GeminiClassifier(self.gemini_api_key)
                logger.info("Gemini AI 분류기 초기화 성공")
            except Exception as e:
                logger.warning(f"Gemini AI 분류기 초기화 실패: {e}")
        else:
            logger.warning("GEMINI_API_KEY가 설정되지 않아 AI 분류 기능을 사용할 수 없습니다.")
    
    def collect_and_process_data(self, search_cnt: int = 50, job_id: str = None) -> Dict:
        """
        데이터 수집부터 분류까지 전체 프로세스 실행
        
        Args:
            search_cnt: 수집할 데이터 수
            job_id: 진행상황 추적을 위한 작업 ID
            
        Returns:
            Dict: 처리 결과 통계
        """
        logger.info(f"=== 데이터 수집 및 분류 프로세스 시작 ({search_cnt}개) ===")
        
        # 진행상황 추적 시작
        if job_id:
            progress_tracker.start_collection(job_id, total_steps=4)
        
        stats = {
            'start_time': datetime.now(),
            'total_fetched': 0,
            'new_announcements': 0,
            'keyword_classified': 0,
            'ai_classified': 0,
            'classification_failed': 0,
            'db_inserted': 0,
            'errors': []
        }
        
        try:
            # 1단계: 기업마당 API에서 데이터 수집
            logger.info("1단계: 기업마당 API 데이터 수집 중...")
            if job_id:
                progress_tracker.update_step(job_id, 1, f"기업마당 API에서 {search_cnt}개 데이터 수집 중...")
            
            # 경상남도 지역 필터링으로 데이터 수집
            announcements = self.bizinfo_api.fetch_announcements(search_cnt, hashtags="경남")
            stats['total_fetched'] = len(announcements)
            
            if not announcements:
                logger.warning("수집된 데이터가 없습니다.")
                if job_id:
                    progress_tracker.complete_collection(job_id, stats)
                return stats
            
            # 2단계: 중복 데이터 필터링
            logger.info("2단계: 중복 데이터 필터링 중...")
            if job_id:
                progress_tracker.update_step(job_id, 2, f"수집된 {len(announcements)}개 데이터에서 중복 제거 중...", 
                                           {'total_fetched': len(announcements)})
            
            existing_ids = AnnouncementModel.get_existing_ids()
            new_announcements = self.data_processor.filter_new_announcements(
                announcements, existing_ids
            )
            stats['new_announcements'] = len(new_announcements)
            
            if not new_announcements:
                logger.info("새로운 공고가 없습니다.")
                if job_id:
                    progress_tracker.complete_collection(job_id, stats)
                return stats
            
            # 3단계: 데이터베이스에 삽입 (분류 전)
            logger.info("3단계: 새로운 공고 데이터베이스 삽입 중...")
            if job_id:
                progress_tracker.update_step(job_id, 3, f"{len(new_announcements)}개 신규 공고를 데이터베이스에 저장 중...",
                                           {'new_announcements': len(new_announcements)})
            
            valid_announcements = [
                ann for ann in new_announcements 
                if self.data_processor.validate_announcement_data(ann)
            ]
            
            inserted_count = AnnouncementModel.bulk_insert_announcements(valid_announcements)
            stats['db_inserted'] = inserted_count
            
            if inserted_count == 0:
                logger.error("데이터베이스 삽입 실패")
                if job_id:
                    progress_tracker.fail_collection(job_id, "데이터베이스 삽입 실패")
                return stats
            
            # 4단계: 지역 분류 수행
            logger.info("4단계: 지역 분류 수행 중...")
            if job_id:
                progress_tracker.update_step(job_id, 4, f"{inserted_count}개 공고에 대한 지역 분류 진행 중...",
                                           {'db_inserted': inserted_count})
            
            self._classify_announcements(stats)
            
            # 완료
            stats['end_time'] = datetime.now()
            stats['total_duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
            
            logger.info("=== 데이터 수집 및 분류 프로세스 완료 ===")
            self._log_final_stats(stats)
            
            if job_id:
                progress_tracker.complete_collection(job_id, stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"데이터 수집 프로세스 오류: {e}")
            stats['errors'].append(str(e))
            if job_id:
                progress_tracker.fail_collection(job_id, str(e))
            return stats
    
    def _classify_announcements(self, stats: Dict):
        """미분류 공고들에 대해 지역 분류 수행"""
        
        # 미분류 공고 조회
        unclassified = AnnouncementModel.get_unclassified_announcements(limit=100)
        
        if not unclassified:
            logger.info("분류할 공고가 없습니다.")
            return
        
        logger.info(f"미분류 공고 {len(unclassified)}개에 대해 분류 시작")
        
        keyword_classified = []
        ai_targets = []
        
        # 키워드 기반 분류
        for announcement in unclassified:
            result = self.keyword_classifier.classify_announcement(announcement)
            
            if result.region_code and result.confidence >= 0.6:
                # 키워드 분류 성공
                success = AnnouncementModel.update_classification(
                    announcement['id'], 
                    result.region_code, 
                    'keyword', 
                    result.confidence
                )
                
                if success:
                    keyword_classified.append(announcement['id'])
                    logger.debug(f"키워드 분류 성공: {announcement['pblancNm']} -> {result.region_code}")
                else:
                    logger.error(f"키워드 분류 결과 저장 실패: {announcement['id']}")
            else:
                # AI 분류 대상
                ai_targets.append(announcement)
        
        stats['keyword_classified'] = len(keyword_classified)
        logger.info(f"키워드 기반 분류 완료: {len(keyword_classified)}개")
        
        # AI 기반 분류 (Gemini API)
        if ai_targets and self.ai_classifier:
            logger.info(f"AI 분류 시작: {len(ai_targets)}개")
            ai_classified_count = self._perform_ai_classification(ai_targets)
            stats['ai_classified'] = ai_classified_count
        elif ai_targets:
            logger.warning(f"AI 분류기가 없어 {len(ai_targets)}개 공고를 분류하지 못했습니다.")
            stats['classification_failed'] = len(ai_targets)
        
        # 분류 실패 건수 계산
        total_classified = stats['keyword_classified'] + stats.get('ai_classified', 0)
        stats['classification_failed'] = len(unclassified) - total_classified
    
    def _perform_ai_classification(self, announcements: List[Dict]) -> int:
        """AI 기반 분류 수행"""
        
        try:
            # 배치 단위로 AI 분류 수행
            ai_results = self.ai_classifier.classify_batch(announcements)
            
            classified_count = 0
            for announcement, result in zip(announcements, ai_results):
                if result.region_code and result.confidence >= 0.5:
                    success = AnnouncementModel.update_classification(
                        announcement['id'],
                        result.region_code,
                        'ai',
                        result.confidence
                    )
                    
                    if success:
                        classified_count += 1
                        logger.debug(f"AI 분류 성공: {announcement['pblancNm']} -> {result.region_code}")
                    else:
                        logger.error(f"AI 분류 결과 저장 실패: {announcement['id']}")
                else:
                    logger.warning(f"AI 분류 실패: {announcement['pblancNm']} (confidence: {result.confidence})")
            
            # AI 사용량 통계 로깅
            usage_stats = self.ai_classifier.get_usage_stats()
            logger.info(f"AI API 사용량 - 요청: {usage_stats['total_requests']}, "
                       f"성공률: {usage_stats['success_rate']}%, "
                       f"토큰: {usage_stats['total_tokens_used']}")
            
            return classified_count
            
        except Exception as e:
            logger.error(f"AI 분류 수행 오류: {e}")
            return 0
    
    def _log_final_stats(self, stats: Dict):
        """최종 통계 로깅"""
        logger.info("=" * 50)
        logger.info("데이터 수집 및 분류 완료 통계:")
        logger.info(f"  • 총 수집: {stats['total_fetched']}개")
        logger.info(f"  • 신규 공고: {stats['new_announcements']}개")
        logger.info(f"  • DB 삽입: {stats['db_inserted']}개")
        logger.info(f"  • 키워드 분류: {stats['keyword_classified']}개")
        logger.info(f"  • AI 분류: {stats.get('ai_classified', 0)}개")
        logger.info(f"  • 분류 실패: {stats['classification_failed']}개")
        logger.info(f"  • 처리 시간: {stats.get('total_duration', 0):.2f}초")
        
        if stats.get('errors'):
            logger.warning(f"  • 오류 발생: {len(stats['errors'])}건")
            for error in stats['errors']:
                logger.warning(f"    - {error}")
        
        logger.info("=" * 50)
    
    def get_classification_summary(self) -> Dict:
        """분류 현황 요약 정보 반환"""
        try:
            return AnnouncementModel.get_classification_stats()
        except Exception as e:
            logger.error(f"분류 통계 조회 오류: {e}")
            return {}

def run_data_collection():
    """데이터 수집 실행 함수 (스케줄러나 수동 실행용)"""
    try:
        service = DataCollectionService()
        
        # 기본 50개 데이터 수집
        result = service.collect_and_process_data(search_cnt=50)
        
        return result
        
    except Exception as e:
        logger.error(f"데이터 수집 실행 오류: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    # 직접 실행시 데이터 수집 수행
    result = run_data_collection()
    print("\\n데이터 수집 결과:", result)