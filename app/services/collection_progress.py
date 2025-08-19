"""
데이터 수집 진행상황 추적 모듈
"""

import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional


class CollectionProgressTracker:
    """데이터 수집 진행상황 추적 클래스"""
    
    def __init__(self):
        self._progress_data = {}
        self._lock = threading.Lock()
    
    def start_collection(self, job_id: str, total_steps: int = 4) -> None:
        """데이터 수집 시작"""
        with self._lock:
            self._progress_data[job_id] = {
                'status': 'running',
                'current_step': 0,
                'total_steps': total_steps,
                'progress_percent': 0,
                'start_time': datetime.now(),
                'current_message': '데이터 수집 시작...',
                'steps': [],
                'result': None,
                'error': None
            }
    
    def update_step(self, job_id: str, step: int, message: str, details: Dict[str, Any] = None) -> None:
        """진행단계 업데이트"""
        with self._lock:
            if job_id not in self._progress_data:
                return
            
            progress = self._progress_data[job_id]
            progress['current_step'] = step
            progress['current_message'] = message
            progress['progress_percent'] = int((step / progress['total_steps']) * 100)
            
            step_data = {
                'step': step,
                'message': message,
                'timestamp': datetime.now(),
                'details': details or {}
            }
            
            progress['steps'].append(step_data)
    
    def complete_collection(self, job_id: str, result: Dict[str, Any]) -> None:
        """데이터 수집 완료"""
        with self._lock:
            if job_id not in self._progress_data:
                return
            
            progress = self._progress_data[job_id]
            progress['status'] = 'completed'
            progress['current_step'] = progress['total_steps']
            progress['progress_percent'] = 100
            progress['current_message'] = '데이터 수집 완료!'
            progress['result'] = result
            progress['end_time'] = datetime.now()
    
    def fail_collection(self, job_id: str, error_message: str) -> None:
        """데이터 수집 실패"""
        with self._lock:
            if job_id not in self._progress_data:
                return
            
            progress = self._progress_data[job_id]
            progress['status'] = 'failed'
            progress['current_message'] = f'수집 실패: {error_message}'
            progress['error'] = error_message
            progress['end_time'] = datetime.now()
    
    def get_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """진행상황 조회"""
        with self._lock:
            return self._progress_data.get(job_id, None)
    
    def cleanup_old_jobs(self, hours: int = 1) -> None:
        """오래된 작업 정리"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            jobs_to_remove = []
            for job_id, progress in self._progress_data.items():
                if 'start_time' in progress:
                    start_timestamp = progress['start_time'].timestamp()
                    if start_timestamp < cutoff_time:
                        jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self._progress_data[job_id]


# 전역 진행상황 추적기 인스턴스
progress_tracker = CollectionProgressTracker()