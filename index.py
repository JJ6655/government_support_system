"""
Vercel 배포용 진입점
"""

from app import app

# Vercel이 자동으로 감지할 수 있도록
application = app

if __name__ == "__main__":
    app.run()