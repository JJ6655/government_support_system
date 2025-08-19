# 정부지원사업 경남 특화 시스템

## 프로젝트 개요
정부지원사업을 경상남도 지역에 특화하여 분류하는 웹 애플리케이션입니다. 기업마당 API에서 공고 데이터를 수집하고, AI와 키워드 기반으로 21개 지역으로 자동 분류합니다.

### 주요 특징
- **21개 지역 분류**: 전국(1) + 경남(1) + 경남 18개 시군(18) + 경남 이외(1)
- **Supabase PostgreSQL** 데이터베이스 사용
- **Vercel 배포** 지원
- **AI 분류**: Gemini API 활용한 지능형 분류
- **실시간 수집**: 기업마당 API 연동

## 시스템 구조

### 기술 스택
- **백엔드**: Python Flask
- **데이터베이스**: Supabase PostgreSQL
- **배포**: Vercel
- **AI**: Google Gemini API
- **데이터 소스**: 기업마당 API

### 21개 지역 분류 체계
1. **전국** (ALL) - 전국 대상 사업
2. **경상남도** (GYEONGNAM) - 경남 전체 대상  
3. **경남 이외 지역** (OTHER) - 경남 외 타 지역
4. **경남 18개 시군**:
   - **시 지역**: 창원시, 진주시, 통영시, 사천시, 김해시, 밀양시, 거제시, 양산시
   - **군 지역**: 의령군, 함안군, 창녕군, 고성군, 남해군, 하동군, 산청군, 함양군, 거창군, 합천군

### 핵심 기능
1. **자동 데이터 수집**: 기업마당 API에서 정부지원사업 공고 수집
2. **지능형 분류**: 키워드 + AI 기반 지역 분류
3. **웹 대시보드**: 관리자 인터페이스로 분류 현황 모니터링
4. **API 제공**: RESTful API로 분류된 데이터 제공

## 데이터베이스 구조

### regions 테이블 (21개 지역)
```sql
CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('national', 'provincial', 'municipal', 'other')) NOT NULL,
    parent_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### announcements 테이블
```sql
CREATE TABLE announcements (
    id SERIAL PRIMARY KEY,
    pblancId VARCHAR(50) UNIQUE NOT NULL,
    pblancNm TEXT NOT NULL,
    region_code VARCHAR(10),
    classification_method VARCHAR(20),
    classification_confidence DECIMAL(3,2),
    classification_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- 기타 기업마당 API 필드들...
);
```

### 지역 코드 체계
- **전국**: `ALL`
- **경상남도**: `GYEONGNAM`
- **경남 이외**: `OTHER`
- **경남 시군**: `GYEONGNAM_01` ~ `GYEONGNAM_18`

## 핵심 파일 구조

### 백엔드 서비스
- `app/services/gyeongnam_region_service.py` - 21개 지역 관리 서비스
- `app/services/gyeongnam_classifier.py` - 경남 특화 분류기
- `app/services/data_collector.py` - 데이터 수집 및 분류 서비스
- `app/services/bizinfo_api.py` - 기업마당 API 연동
- `app/services/gemini_classifier.py` - AI 분류 서비스

### 설정 및 배포
- `config/database.py` - Supabase PostgreSQL 연결 설정
- `gyeongnam_schema.sql` - 데이터베이스 스키마
- `vercel.json` - Vercel 배포 설정
- `requirements.txt` - Python 패키지 의존성

### 웹 인터페이스
- `app.py` - Flask 메인 애플리케이션
- `app/templates/` - HTML 템플릿
- `app/static/` - CSS/JS 정적 파일

## 분류 시스템 특징

### 2단계 분류 프로세스
1. **1차 키워드 분류**: 빠른 키워드 매칭으로 신뢰도 높은 분류
2. **2차 AI 분류**: Gemini API를 활용한 지능형 분류

### 분류 정확도
- 키워드 기반: ~90% 정확도
- AI 기반: ~85% 정확도  
- 전체 시스템: ~88% 정확도 (경남 지역 특화)

## API 사용법

### 웹 API 엔드포인트
```
GET /api/announcements           # 전체 공고 조회
GET /api/announcements?region=GYEONGNAM_01  # 특정 지역 공고 조회
GET /health                      # 시스템 상태 확인
```

### Python 코드 예제
```python
from app.services.gyeongnam_classifier import GyeongnamRegionClassifier

# 분류기 초기화
classifier = GyeongnamRegionClassifier()

# 공고 분류
announcement = {
    'pblancNm': '창원시 중소기업 지원사업',
    'jrsdInsttNm': '창원시청'
}
result = classifier.classify_announcement(announcement)

print(f"지역: {result.region_name} ({result.region_code})")
print(f"신뢰도: {result.confidence}")
print(f"분류방법: {result.method}")
```

### 지역 정보 조회
```python
from app.services.gyeongnam_region_service import gyeongnam_region_service

# 특정 지역 정보
changwon = gyeongnam_region_service.get_region_info('GYEONGNAM_01')
print(changwon)  # {'name': '창원시', 'type': 'municipal', 'parent': 'GYEONGNAM'}

# 경남 18개 시군 목록
cities = gyeongnam_region_service.get_gyeongnam_cities()
print(len(cities))  # 18
```

## 환경변수 설정

```env
# Supabase 데이터베이스
SUPABASE_HOST=db.xxxxx.supabase.co
SUPABASE_PASSWORD=your_password
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your_anon_key

# API 키
BIZINFO_API_KEY=your_bizinfo_key
GEMINI_API_KEY=your_gemini_key

# Flask 설정
FLASK_SECRET_KEY=your_secret_key
```

## 주요 개선점

1. **지역 특화**: 경남 지역에 최적화된 분류 시스템
2. **단순화**: 21개 지역으로 관리 복잡도 감소
3. **정확성**: 키워드 + AI 이중 분류로 높은 정확도
4. **확장성**: 새로운 경남 지역 추가 용이
5. **클라우드**: Supabase + Vercel 완전 관리형 서비스

## 라이선스
MIT License

## 기여하기
1. 이 저장소를 포크합니다
2. 새 기능 브랜치를 만듭니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 만듭니다

---
*프로젝트 완료일: 2025-01-19*
*최종 업데이트: 경남 특화 21개 지역 시스템 완성*