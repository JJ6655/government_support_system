"""
정부지원사업 지역분류 시스템 - Flask 애플리케이션
"""

import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import check_password_hash
from datetime import datetime
import logging

from app.models.announcement import AnnouncementModel
from app.services.data_collector import DataCollectionService
from config.database import test_database_connection

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Flask 앱 팩토리"""
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    
    # 설정
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    app.config['ENV'] = os.getenv('FLASK_ENV', 'development')
    
    return app

app = create_app()

# ===== 인증 관련 =====

def login_required(f):
    """로그인 필수 데코레이터"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
        region_code = request.args.get('region', None)
        limit = int(request.args.get('limit', 20))
        
        announcements = AnnouncementModel.get_announcements_by_region(region_code, limit)
        
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
        
        success = AnnouncementModel.update_classification(
            announcement_id, region_code, 'manual', 1.0
        )
        
        if success:
            return jsonify({'success': True, 'message': '분류 완료'})
        else:
            return jsonify({'success': False, 'error': '분류 실패'}), 500
            
    except Exception as e:
        logger.error(f"수동 분류 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/collect', methods=['POST'])
@login_required
def admin_collect_data():
    """관리자 - 수동 데이터 수집"""
    try:
        search_cnt = int(request.json.get('search_cnt', 20))
        
        # 데이터 수집 서비스 실행
        service = DataCollectionService()
        result = service.collect_and_process_data(search_cnt)
        
        return jsonify({
            'success': True,
            'result': {
                'total_fetched': result.get('total_fetched', 0),
                'new_announcements': result.get('new_announcements', 0),
                'keyword_classified': result.get('keyword_classified', 0),
                'ai_classified': result.get('ai_classified', 0),
                'classification_failed': result.get('classification_failed', 0),
                'errors': result.get('errors', [])
            }
        })
        
    except Exception as e:
        logger.error(f"데이터 수집 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== 시스템 상태 확인 =====

@app.route('/health')
def health_check():
    """시스템 상태 확인"""
    try:
        # 데이터베이스 연결 테스트
        db_status = test_database_connection()
        
        # 기본 통계 조회
        stats = AnnouncementModel.get_classification_stats()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected' if db_status else 'disconnected',
            'total_announcements': stats.get('total', {}).get('total', 0)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ===== 에러 핸들러 =====

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, error_message='페이지를 찾을 수 없습니다.'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message='내부 서버 오류가 발생했습니다.'), 500

# ===== 컨텍스트 프로세서 =====

@app.context_processor
def inject_common_vars():
    """템플릿에서 공통으로 사용할 변수들"""
    return {
        'current_year': datetime.now().year,
        'app_name': '정부지원사업 지역분류 시스템'
    }

# Vercel용 핸들러
def handler(request):
    """Vercel 서버리스 함수 핸들러"""
    return app

# 로컬 개발용
if __name__ == '__main__':
    # 개발 서버 실행
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    logger.info("Flask 애플리케이션 시작")
    logger.info(f"Debug 모드: {debug_mode}")
    
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=debug_mode
    )