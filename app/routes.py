"""
Flask 라우트 정의
"""

import os
from flask import render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import check_password_hash
from datetime import datetime
import logging

from .models.announcement import AnnouncementModel
from .services.data_collector import DataCollectionService
from config.database import test_database_connection

# 로깅 설정
logger = logging.getLogger(__name__)

def login_required(f):
    """로그인 필수 데코레이터"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    """라우트 등록"""
    
    # ===== 인증 관련 =====
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """관리자 로그인"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # 간단한 인증 (실제 환경에서는 데이터베이스 확인)
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            
            if username == admin_username and password == admin_password:
                session['admin_logged_in'] = True
                session['admin_username'] = username
                flash('로그인 성공!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('아이디 또는 비밀번호가 잘못되었습니다.', 'error')
        
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        """로그아웃"""
        session.pop('admin_logged_in', None)
        session.pop('admin_username', None)
        flash('로그아웃되었습니다.', 'info')
        return redirect(url_for('login'))

    # ===== 메인 페이지 =====
    
    @app.route('/')
    def index():
        """메인 페이지 - 사용자 인터페이스"""
        return render_template('index.html')

    @app.route('/api/announcements')
    def api_announcements():
        """공고 데이터 API"""
        try:
            # 여러 지역 지원
            region_codes = request.args.getlist('regions')
            if not region_codes:
                # 단일 지역도 지원 (하위호환성)
                region_code = request.args.get('region', None)
                if region_code:
                    region_codes = [region_code]
            
            limit = int(request.args.get('limit', 50))
            
            announcements = AnnouncementModel.get_announcements_by_regions(region_codes, limit)
            
            return jsonify({
                'success': True,
                'data': announcements,
                'count': len(announcements)
            })
            
        except Exception as e:
            logger.error(f"공고 조회 API 오류: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ===== 관리자 인터페이스 =====
    
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        """관리자 대시보드"""
        try:
            # 분류 통계 조회
            stats = AnnouncementModel.get_classification_stats()
            
            return render_template('admin/dashboard.html', stats=stats)
            
        except Exception as e:
            logger.error(f"관리자 대시보드 오류: {e}")
            flash(f'통계 조회 오류: {e}', 'error')
            return render_template('admin/dashboard.html', stats={})

    @app.route('/admin/announcements')
    @login_required
    def admin_announcements():
        """관리자 - 공고 목록"""
        try:
            page = int(request.args.get('page', 1))
            region_filter = request.args.get('region', None)
            status_filter = request.args.get('status', None)
            
            # TODO: 페이징 처리 및 필터링 구현
            announcements = AnnouncementModel.get_announcements_by_region(region_filter, 50)
            
            return render_template('admin/announcements.html', 
                                 announcements=announcements,
                                 current_page=page,
                                 region_filter=region_filter,
                                 status_filter=status_filter)
            
        except Exception as e:
            logger.error(f"관리자 공고 목록 오류: {e}")
            flash(f'공고 목록 조회 오류: {e}', 'error')
            return render_template('admin/announcements.html', announcements=[])

    @app.route('/admin/classify', methods=['POST'])
    @login_required
    def admin_classify():
        """관리자 - 수동 분류"""
        try:
            announcement_id = request.json.get('announcement_id')
            region_code = request.json.get('region_code')
            
            if not announcement_id or not region_code:
                return jsonify({
                    'success': False,
                    'error': '필수 파라미터가 누락되었습니다.'
                }), 400
            
            # 수동 분류 업데이트
            success = AnnouncementModel.update_classification(
                announcement_id, region_code, 'manual', 1.0
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '분류가 업데이트되었습니다.'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '분류 업데이트에 실패했습니다.'
                }), 500
                
        except Exception as e:
            logger.error(f"수동 분류 오류: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/admin/collect', methods=['POST'])
    @login_required  
    def admin_collect():
        """관리자 - 수동 데이터 수집"""
        import uuid
        import threading
        
        try:
            search_cnt = request.json.get('search_cnt', 50)
            
            # 고유한 작업 ID 생성
            job_id = str(uuid.uuid4())
            
            # 별도 스레드에서 데이터 수집 실행
            def run_collection():
                try:
                    data_service = DataCollectionService()
                    data_service.collect_and_process_data(search_cnt, job_id)
                except Exception as e:
                    from .services.collection_progress import progress_tracker
                    progress_tracker.fail_collection(job_id, str(e))
            
            thread = threading.Thread(target=run_collection)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'message': '데이터 수집이 시작되었습니다.'
            })
            
        except Exception as e:
            logger.error(f"수동 데이터 수집 오류: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/admin/collect/progress/<job_id>')
    @login_required
    def admin_collect_progress(job_id):
        """데이터 수집 진행상황 조회"""
        try:
            from .services.collection_progress import progress_tracker
            progress = progress_tracker.get_progress(job_id)
            
            if not progress:
                return jsonify({
                    'success': False,
                    'error': '해당 작업을 찾을 수 없습니다.'
                }), 404
            
            return jsonify({
                'success': True,
                'progress': progress
            })
            
        except Exception as e:
            logger.error(f"진행상황 조회 오류: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ===== 헬스체크 및 API =====
    
    @app.route('/health')
    def health_check():
        """시스템 헬스체크"""
        try:
            # 데이터베이스 연결 확인
            db_status = test_database_connection()
            
            return jsonify({
                'status': 'healthy' if db_status else 'unhealthy',
                'database': 'connected' if db_status else 'disconnected',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500

    @app.route('/api/stats')
    def api_stats():
        """통계 API"""
        try:
            stats = AnnouncementModel.get_classification_stats()
            return jsonify({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"통계 조회 API 오류: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500