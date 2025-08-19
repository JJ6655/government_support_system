-- 경남 특화 지역 분류 시스템 (21개 지역)
-- Supabase PostgreSQL 스키마

-- 1. regions 테이블 (21개 지역)
CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('national', 'provincial', 'municipal', 'other')) NOT NULL,
    parent_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_code) REFERENCES regions(code)
);

-- 2. announcements 테이블
CREATE TABLE announcements (
    id SERIAL PRIMARY KEY,
    pblancId VARCHAR(50) UNIQUE NOT NULL,
    pblancNm TEXT NOT NULL,
    jrsdInsttNm VARCHAR(200),
    excInsttNm VARCHAR(200),
    bsnsSumryCn TEXT,
    trgetNm VARCHAR(100),
    pblancUrl VARCHAR(500),
    rceptEngnHmpgUrl VARCHAR(500),
    flpthNm TEXT,
    printFlpthNm VARCHAR(500),
    printFileNm VARCHAR(200),
    fileNm TEXT,
    reqstBeginEndDe VARCHAR(50),
    reqstMthPapersCn TEXT,
    refrncNm TEXT,
    pldirSportRealmLclasCodeNm VARCHAR(50),
    pldirSportRealmMlsfcCodeNm VARCHAR(50),
    hashtags TEXT,
    totCnt INTEGER,
    inqireCo INTEGER,
    creatPnttm TIMESTAMP,
    region_code VARCHAR(10),
    classification_method VARCHAR(20) CHECK (classification_method IN ('keyword', 'ai', 'manual')),
    classification_confidence DECIMAL(3,2),
    classification_status VARCHAR(20) CHECK (classification_status IN ('pending', 'classified', 'verified')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- 3. 인덱스 생성
CREATE INDEX idx_regions_code ON regions(code);
CREATE INDEX idx_regions_type ON regions(type);
CREATE INDEX idx_regions_parent_code ON regions(parent_code);

CREATE INDEX idx_announcements_pblancId ON announcements(pblancId);
CREATE INDEX idx_announcements_region_code ON announcements(region_code);
CREATE INDEX idx_announcements_classification_status ON announcements(classification_status);
CREATE INDEX idx_announcements_created_at ON announcements(created_at);

-- 4. 외래키 제약조건
ALTER TABLE announcements 
ADD CONSTRAINT fk_announcements_region 
FOREIGN KEY (region_code) REFERENCES regions(code);

-- 5. 21개 지역 데이터 INSERT

-- 전국 (1개)
INSERT INTO regions (code, name, type, parent_code) VALUES ('ALL', '전국', 'national', NULL);

-- 경상남도 (1개)
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM', '경상남도', 'provincial', NULL);

-- 경남 이외 지역 (1개)
INSERT INTO regions (code, name, type, parent_code) VALUES ('OTHER', '경남 이외 지역', 'other', NULL);

-- 경남 18개 시군 (18개)
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_01', '창원시', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_02', '진주시', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_03', '통영시', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_04', '사천시', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_05', '김해시', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_06', '밀양시', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_07', '거제시', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_08', '양산시', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_09', '의령군', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_10', '함안군', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_11', '창녕군', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_12', '고성군', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_13', '남해군', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_14', '하동군', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_15', '산청군', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_16', '함양군', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_17', '거창군', 'municipal', 'GYEONGNAM');
INSERT INTO regions (code, name, type, parent_code) VALUES ('GYEONGNAM_18', '합천군', 'municipal', 'GYEONGNAM');

-- 총 21개 지역:
-- 1. 전국 (ALL)
-- 2. 경상남도 (GYEONGNAM) 
-- 3. 경남 이외 지역 (OTHER)
-- 4-21. 경남 18개 시군 (GYEONGNAM_01 ~ GYEONGNAM_18)