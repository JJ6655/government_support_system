"""
공고 데이터 모델
"""

from datetime import datetime
from typing import List, Dict, Optional
from config.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class AnnouncementModel:
    """공고 데이터베이스 모델"""
    
    @staticmethod
    def get_existing_ids() -> set:
        """
        데이터베이스에 이미 존재하는 공고 ID들을 가져옵니다.
        
        Returns:
            set: 기존 공고 ID 집합
        """
        try:
            with DatabaseManager.get_db_cursor() as (cursor, connection):
                cursor.execute("SELECT pblancId FROM announcements WHERE is_active = true")
                results = cursor.fetchall()
                return {row['pblancId'] for row in results}
        except Exception as e:
            logger.error(f"기존 공고 ID 조회 오류: {e}")
            return set()
    
    @staticmethod
    def insert_announcement(data: Dict) -> bool:
        """
        새로운 공고를 데이터베이스에 삽입합니다.
        
        Args:
            data: 공고 데이터
            
        Returns:
            bool: 삽입 성공 여부
        """
        try:
            with DatabaseManager.get_db_cursor() as (cursor, connection):
                sql = """
                INSERT INTO announcements (
                    pblancId, pblancNm, jrsdInsttNm, excInsttNm, bsnsSumryCn, trgetNm,
                    pblancUrl, rceptEngnHmpgUrl, flpthNm, printFlpthNm, printFileNm, fileNm,
                    reqstBeginEndDe, reqstMthPapersCn, refrncNm, pldirSportRealmLclasCodeNm,
                    pldirSportRealmMlsfcCodeNm, hashtags, totCnt, inqireCo, creatPnttm
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                values = (
                    data.get('pblancId'), data.get('pblancNm'), data.get('jrsdInsttNm'),
                    data.get('excInsttNm'), data.get('bsnsSumryCn'), data.get('trgetNm'),
                    data.get('pblancUrl'), data.get('rceptEngnHmpgUrl'), data.get('flpthNm'),
                    data.get('printFlpthNm'), data.get('printFileNm'), data.get('fileNm'),
                    data.get('reqstBeginEndDe'), data.get('reqstMthPapersCn'), data.get('refrncNm'),
                    data.get('pldirSportRealmLclasCodeNm'), data.get('pldirSportRealmMlsfcCodeNm'),
                    data.get('hashtags'), data.get('totCnt'), data.get('inqireCo'),
                    data.get('creatPnttm')
                )
                
                cursor.execute(sql, values)
                connection.commit()
                return True
                
        except Exception as e:
            logger.error(f"공고 삽입 오류 (pblancId: {data.get('pblancId')}): {e}")
            return False
    
    @staticmethod
    def bulk_insert_announcements(announcements: List[Dict]) -> int:
        """
        여러 공고를 한 번에 삽입합니다.
        
        Args:
            announcements: 공고 데이터 리스트
            
        Returns:
            int: 성공적으로 삽입된 공고 수
        """
        success_count = 0
        
        try:
            with DatabaseManager.get_db_cursor() as (cursor, connection):
                sql = """
                INSERT INTO announcements (
                    pblancId, pblancNm, jrsdInsttNm, excInsttNm, bsnsSumryCn, trgetNm,
                    pblancUrl, rceptEngnHmpgUrl, flpthNm, printFlpthNm, printFileNm, fileNm,
                    reqstBeginEndDe, reqstMthPapersCn, refrncNm, pldirSportRealmLclasCodeNm,
                    pldirSportRealmMlsfcCodeNm, hashtags, totCnt, inqireCo, creatPnttm
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                for data in announcements:
                    try:
                        values = (
                            data.get('pblancId'), data.get('pblancNm'), data.get('jrsdInsttNm'),
                            data.get('excInsttNm'), data.get('bsnsSumryCn'), data.get('trgetNm'),
                            data.get('pblancUrl'), data.get('rceptEngnHmpgUrl'), data.get('flpthNm'),
                            data.get('printFlpthNm'), data.get('printFileNm'), data.get('fileNm'),
                            data.get('reqstBeginEndDe'), data.get('reqstMthPapersCn'), data.get('refrncNm'),
                            data.get('pldirSportRealmLclasCodeNm'), data.get('pldirSportRealmMlsfcCodeNm'),
                            data.get('hashtags'), data.get('totCnt'), data.get('inqireCo'),
                            data.get('creatPnttm')
                        )
                        
                        cursor.execute(sql, values)
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"개별 공고 삽입 오류 (pblancId: {data.get('pblancId')}): {e}")
                        continue
                
                connection.commit()
                
        except Exception as e:
            logger.error(f"배치 삽입 오류: {e}")
        
        logger.info(f"배치 삽입 완료 - 성공: {success_count}개 / 전체: {len(announcements)}개")
        return success_count
    
    @staticmethod
    def get_unclassified_announcements(limit: int = 50) -> List[Dict]:
        """
        지역 분류가 되지 않은 공고들을 가져옵니다.
        
        Args:
            limit: 가져올 공고 수 제한
            
        Returns:
            List[Dict]: 미분류 공고 리스트
        """
        try:
            with DatabaseManager.get_db_cursor() as (cursor, connection):
                sql = """
                SELECT id, pblancId, pblancNm, jrsdInsttNm, excInsttNm, 
                       bsnsSumryCn, hashtags, refrncNm
                FROM announcements 
                WHERE region_code IS NULL 
                  AND is_active = true
                  AND classification_status = 'pending'
                ORDER BY created_at DESC
                LIMIT %s
                """
                
                cursor.execute(sql, (limit,))
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"미분류 공고 조회 오류: {e}")
            return []
    
    @staticmethod
    def update_classification(announcement_id: int, region_code: str, 
                            method: str, confidence: float = None) -> bool:
        """
        공고의 지역 분류 결과를 업데이트합니다.
        
        Args:
            announcement_id: 공고 ID
            region_code: 지역 코드
            method: 분류 방법 (keyword, ai, manual)
            confidence: 분류 신뢰도 (0.00-1.00)
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            with DatabaseManager.get_db_cursor() as (cursor, connection):
                sql = """
                UPDATE announcements 
                SET region_code = %s, 
                    classification_method = %s,
                    classification_confidence = %s,
                    classification_status = 'classified',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                
                cursor.execute(sql, (region_code, method, confidence, announcement_id))
                connection.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"분류 결과 업데이트 오류 (ID: {announcement_id}): {e}")
            return False
    
    @staticmethod
    def get_announcements_by_region(region_code: str = None, limit: int = 100) -> List[Dict]:
        """
        지역별 공고를 조회합니다.
        
        Args:
            region_code: 지역 코드 (None이면 전체)
            limit: 가져올 공고 수 제한
            
        Returns:
            List[Dict]: 공고 리스트
        """
        try:
            with DatabaseManager.get_db_cursor() as (cursor, connection):
                if region_code:
                    sql = """
                    SELECT a.*, r.name as region_name
                    FROM announcements a
                    LEFT JOIN regions r ON a.region_code = r.code
                    WHERE a.region_code = %s AND a.is_active = true
                    ORDER BY a.created_at DESC
                    LIMIT %s
                    """
                    cursor.execute(sql, (region_code, limit))
                else:
                    sql = """
                    SELECT a.*, r.name as region_name
                    FROM announcements a
                    LEFT JOIN regions r ON a.region_code = r.code
                    WHERE a.is_active = true
                    ORDER BY a.created_at DESC
                    LIMIT %s
                    """
                    cursor.execute(sql, (limit,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"지역별 공고 조회 오류 (region_code: {region_code}): {e}")
            return []
    
    @staticmethod
    def get_announcements_by_regions(region_codes: List[str] = None, limit: int = 100) -> List[Dict]:
        """
        여러 지역의 공고를 조회합니다.
        
        Args:
            region_codes: 지역 코드 리스트 (None이면 전체)
            limit: 가져올 공고 수 제한
            
        Returns:
            List[Dict]: 공고 리스트
        """
        try:
            with DatabaseManager.get_db_cursor() as (cursor, connection):
                if region_codes and len(region_codes) > 0:
                    # 여러 지역 조회
                    placeholders = ','.join(['%s'] * len(region_codes))
                    sql = f"""
                    SELECT a.*, r.name as region_name
                    FROM announcements a
                    LEFT JOIN regions r ON a.region_code = r.code
                    WHERE a.region_code IN ({placeholders}) AND a.is_active = true
                    ORDER BY a.created_at DESC
                    LIMIT %s
                    """
                    cursor.execute(sql, region_codes + [limit])
                else:
                    # 전체 조회
                    sql = """
                    SELECT a.*, r.name as region_name
                    FROM announcements a
                    LEFT JOIN regions r ON a.region_code = r.code
                    WHERE a.is_active = true
                    ORDER BY a.created_at DESC
                    LIMIT %s
                    """
                    cursor.execute(sql, (limit,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"여러 지역 공고 조회 오류 (region_codes: {region_codes}): {e}")
            return []
    
    @staticmethod
    def get_classification_stats() -> Dict:
        """
        분류 통계를 가져옵니다.
        
        Returns:
            Dict: 분류 통계 정보
        """
        try:
            with DatabaseManager.get_db_cursor() as (cursor, connection):
                # 전체 통계
                cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN region_code IS NOT NULL THEN 1 ELSE 0 END) as classified,
                    SUM(CASE WHEN region_code IS NULL THEN 1 ELSE 0 END) as unclassified
                FROM announcements 
                WHERE is_active = true
                """)
                
                total_stats = cursor.fetchone()
                
                # 지역별 통계
                cursor.execute("""
                SELECT r.name, r.code, COUNT(a.id) as count
                FROM regions r
                LEFT JOIN announcements a ON r.code = a.region_code AND a.is_active = true
                GROUP BY r.code, r.name
                ORDER BY count DESC
                """)
                
                region_stats = cursor.fetchall()
                
                # 분류 방법별 통계
                cursor.execute("""
                SELECT classification_method, COUNT(*) as count
                FROM announcements 
                WHERE region_code IS NOT NULL AND is_active = true
                GROUP BY classification_method
                """)
                
                method_stats = cursor.fetchall()
                
                return {
                    'total': total_stats,
                    'by_region': region_stats,
                    'by_method': method_stats
                }
                
        except Exception as e:
            logger.error(f"분류 통계 조회 오류: {e}")
            return {}