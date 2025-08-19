"""
데이터 수집 스케줄링 서비스
"""

import os
import logging
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
# SQLAlchemy jobstore 제거하여 메모리 기반만 사용
from apscheduler.executors.pool import ThreadPoolExecutor
from dotenv import load_dotenv

from .data_collector import DataCollectionService

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollectionScheduler:
    """데이터 수집 스케줄러"""
    
    def __init__(self):
        self.scheduler = None
        self.data_service = None
        self.is_running = False
        
        # 스케줄러 설정
        self._setup_scheduler()
        
    def _setup_scheduler(self):
        """스케줄러 초기 설정"""
        try:
            # Job Store 설정 (메모리 기반으로 단순화)
            jobstores = {
                'default': {'type': 'memory'}
            }
            
            # Executor 설정
            executors = {
                'default': ThreadPoolExecutor(max_workers=2)
            }
            
            # 스케줄러 생성
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                timezone='Asia/Seoul'
            )
            
            # 데이터 수집 서비스 초기화
            self.data_service = DataCollectionService()
            
            logger.info("스케줄러 초기화 완료")
            
        except Exception as e:
            logger.error(f"스케줄러 초기화 오류: {e}")
            raise e
    
    def start(self):
        """스케줄러 시작"""
        if self.is_running:
            logger.warning("스케줄러가 이미 실행 중입니다.")
            return
        
        try:
            # 기본 스케줄 추가
            self._add_default_jobs()
            
            # 스케줄러 시작
            self.scheduler.start()
            self.is_running = True
            
            logger.info("데이터 수집 스케줄러 시작됨")
            logger.info("등록된 작업:")
            for job in self.scheduler.get_jobs():
                logger.info(f"  - {job.id}: {job.next_run_time}")
            
        except Exception as e:
            logger.error(f"스케줄러 시작 오류: {e}")
            raise e
    
    def stop(self):
        """스케줄러 중지"""
        if not self.is_running:
            logger.warning("스케줄러가 실행되고 있지 않습니다.")
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("데이터 수집 스케줄러 중지됨")
            
        except Exception as e:
            logger.error(f"스케줄러 중지 오류: {e}")
    
    def _add_default_jobs(self):
        """기본 스케줄 작업 추가"""
        
        # 오전 9시 10분 데이터 수집
        self.scheduler.add_job(
            func=self._scheduled_data_collection,
            trigger='cron',
            hour=9,
            minute=10,
            id='morning_collection',
            name='오전 데이터 수집',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300  # 5분 지연 허용
        )
        
        # 오후 5시 30분 데이터 수집
        self.scheduler.add_job(
            func=self._scheduled_data_collection,
            trigger='cron',
            hour=17,
            minute=30,
            id='evening_collection',
            name='오후 데이터 수집',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300  # 5분 지연 허용
        )
        
        # 매일 자정 시스템 상태 확인 (옵션)
        self.scheduler.add_job(
            func=self._system_health_check,
            trigger='cron',
            hour=0,
            minute=0,
            id='health_check',
            name='시스템 상태 확인',
            max_instances=1,
            coalesce=True
        )
        
        # 주간 데이터 정리 (옵션) - 매주 일요일 새벽 2시
        self.scheduler.add_job(
            func=self._weekly_cleanup,
            trigger='cron',
            day_of_week=6,  # 일요일
            hour=2,
            minute=0,
            id='weekly_cleanup',
            name='주간 데이터 정리',
            max_instances=1,
            coalesce=True
        )
    
    def _scheduled_data_collection(self):
        """스케줄된 데이터 수집 작업"""
        try:
            logger.info("=== 스케줄된 데이터 수집 시작 ===")
            
            # 수집할 데이터 수 (환경변수에서 설정 가능)
            search_cnt = int(os.getenv('SCHEDULED_SEARCH_COUNT', 50))
            
            # 데이터 수집 실행
            result = self.data_service.collect_and_process_data(search_cnt)
            
            # 결과 로깅
            logger.info(f"스케줄된 데이터 수집 완료:")
            logger.info(f"  - 총 수집: {result.get('total_fetched', 0)}개")
            logger.info(f"  - 신규 공고: {result.get('new_announcements', 0)}개")
            logger.info(f"  - 키워드 분류: {result.get('keyword_classified', 0)}개")
            logger.info(f"  - AI 분류: {result.get('ai_classified', 0)}개")
            logger.info(f"  - 분류 실패: {result.get('classification_failed', 0)}개")
            
            if result.get('errors'):
                for error in result['errors']:
                    logger.error(f"  - 오류: {error}")
            
            return result
            
        except Exception as e:
            logger.error(f"스케줄된 데이터 수집 오류: {e}")
            return {'error': str(e)}
    
    def _system_health_check(self):
        """시스템 상태 확인 작업"""
        try:
            logger.info("=== 시스템 상태 확인 시작 ===")
            
            # 데이터베이스 연결 확인
            from config.database import test_database_connection
            db_status = test_database_connection()
            logger.info(f"데이터베이스 상태: {'정상' if db_status else '오류'}")
            
            # 분류 통계 확인
            from app.models.announcement import AnnouncementModel
            stats = AnnouncementModel.get_classification_stats()
            
            if stats and stats.get('total'):
                total = stats['total']
                logger.info(f"공고 통계: 전체 {total.get('total', 0)}개, "
                           f"분류 완료 {total.get('classified', 0)}개, "
                           f"미분류 {total.get('unclassified', 0)}개")
            
            logger.info("시스템 상태 확인 완료")
            
        except Exception as e:
            logger.error(f"시스템 상태 확인 오류: {e}")
    
    def _weekly_cleanup(self):
        """주간 데이터 정리 작업"""
        try:
            logger.info("=== 주간 데이터 정리 시작 ===")
            
            # 2년 이상 된 데이터 정리 (현재는 로깅만)
            # TODO: 실제 데이터 정리 로직 구현
            
            cutoff_date = datetime.now() - timedelta(days=730)  # 2년
            logger.info(f"정리 기준 날짜: {cutoff_date}")
            
            # 현재는 로깅만 하고 실제 삭제는 하지 않음
            logger.info("주간 데이터 정리 완료 (현재는 로깅만)")
            
        except Exception as e:
            logger.error(f"주간 데이터 정리 오류: {e}")
    
    def add_custom_job(self, job_id, func, trigger, **kwargs):
        """사용자 정의 작업 추가"""
        try:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                max_instances=1,
                coalesce=True,
                **kwargs
            )
            logger.info(f"사용자 정의 작업 추가됨: {job_id}")
            
        except Exception as e:
            logger.error(f"사용자 정의 작업 추가 오류: {e}")
    
    def remove_job(self, job_id):
        """작업 제거"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"작업 제거됨: {job_id}")
            
        except Exception as e:
            logger.error(f"작업 제거 오류: {e}")
    
    def get_jobs_status(self):
        """작업 상태 조회"""
        if not self.scheduler:
            return []
        
        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return jobs_info
    
    def run_job_now(self, job_id):
        """즉시 작업 실행"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.func()
                logger.info(f"작업 즉시 실행 완료: {job_id}")
                return True
            else:
                logger.error(f"작업을 찾을 수 없음: {job_id}")
                return False
                
        except Exception as e:
            logger.error(f"작업 즉시 실행 오류: {e}")
            return False

# 전역 스케줄러 인스턴스
_scheduler_instance = None

def get_scheduler():
    """전역 스케줄러 인스턴스 반환"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DataCollectionScheduler()
    return _scheduler_instance

def start_scheduler():
    """스케줄러 시작"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler

def stop_scheduler():
    """스케줄러 중지"""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop()
        _scheduler_instance = None

# 스탠드얼론 실행을 위한 메인 함수
def main():
    """스케줄러 메인 실행"""
    logger.info("데이터 수집 스케줄러 시작...")
    
    try:
        scheduler = start_scheduler()
        
        logger.info("스케줄러가 시작되었습니다. 종료하려면 Ctrl+C를 누르세요.")
        
        # 무한 대기
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단되었습니다.")
        
    except Exception as e:
        logger.error(f"스케줄러 실행 오류: {e}")
    
    finally:
        logger.info("스케줄러 종료 중...")
        stop_scheduler()
        logger.info("스케줄러가 종료되었습니다.")

if __name__ == "__main__":
    main()