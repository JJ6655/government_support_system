"""
데이터베이스 연결 설정 - Supabase PostgreSQL
"""

import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 데이터베이스 설정
DB_CONFIG = {
    'host': os.getenv('SUPABASE_HOST'),
    'user': os.getenv('SUPABASE_USER', 'postgres'),
    'password': os.getenv('SUPABASE_PASSWORD'),
    'database': os.getenv('SUPABASE_DB', 'postgres'),
    'port': int(os.getenv('SUPABASE_PORT', '5432'))
}

class DatabaseManager:
    """데이터베이스 연결 관리자 - PostgreSQL"""
    
    @staticmethod
    def get_connection():
        """데이터베이스 연결 반환"""
        try:
            connection = psycopg2.connect(**DB_CONFIG)
            connection.autocommit = True
            return connection
        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            raise e
    
    @staticmethod
    @contextmanager
    def get_db_connection():
        """Context manager로 데이터베이스 연결 관리"""
        connection = None
        try:
            connection = DatabaseManager.get_connection()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection:
                connection.close()
    
    @staticmethod
    @contextmanager
    def get_db_cursor(connection=None):
        """Context manager로 커서 관리"""
        should_close_connection = connection is None
        cursor = None
        
        try:
            if connection is None:
                connection = DatabaseManager.get_connection()
            
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            yield cursor, connection
            
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if should_close_connection and connection:
                connection.close()

def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        with DatabaseManager.get_db_cursor() as (cursor, connection):
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("Supabase PostgreSQL 연결 성공!")
            return True
    except Exception as e:
        print(f"Supabase PostgreSQL 연결 실패: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()