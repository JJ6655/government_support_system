# app 패키지 초기화

def create_app():
    """Flask 앱 팩토리 함수"""
    import os
    from flask import Flask
    
    # Flask 앱 생성 (template와 static 폴더 경로 설정)
    app = Flask(__name__, 
                template_folder='templates', 
                static_folder='static')
    
    # 설정
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    app.config['ENV'] = os.getenv('FLASK_ENV', 'development')
    
    # 라우트 등록
    from . import routes
    routes.register_routes(app)
    
    return app