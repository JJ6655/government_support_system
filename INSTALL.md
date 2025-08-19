# 🚀 정부지원사업 경남 특화 시스템 설치 가이드

이 가이드는 초보자도 쉽게 따라할 수 있도록 단계별로 설명합니다.

## 📋 목차
1. [시스템 요구사항](#시스템-요구사항)
2. [사전 준비](#사전-준비)
3. [Supabase 설정](#supabase-설정)
4. [API 키 발급](#api-키-발급)
5. [로컬 개발 환경 설정](#로컬-개발-환경-설정)
6. [Vercel 배포](#vercel-배포)
7. [테스트 및 확인](#테스트-및-확인)
8. [문제 해결](#문제-해결)

---

## 📦 시스템 요구사항

### 필수 소프트웨어
- **Python**: 3.9 이상
- **Git**: 최신 버전
- **웹 브라우저**: Chrome, Firefox, Safari 등
- **텍스트 에디터**: VS Code 권장

### 권장 사양
- **메모리**: 4GB 이상
- **저장공간**: 1GB 이상 여유 공간
- **인터넷**: 안정적인 인터넷 연결

---

## 🛠 사전 준비

### 1. 필요한 계정 생성
다음 사이트에서 무료 계정을 만드세요:

#### 🗄️ Supabase (데이터베이스)
1. [supabase.com](https://supabase.com) 접속
2. **"Start your project"** 클릭
3. GitHub 계정으로 로그인 (없으면 GitHub 계정 먼저 생성)

#### 🚀 Vercel (배포)
1. [vercel.com](https://vercel.com) 접속
2. **"Sign Up"** 클릭
3. GitHub 계정으로 로그인

#### 🤖 Google AI Studio (AI 분류용)
1. [aistudio.google.com](https://aistudio.google.com) 접속
2. Google 계정으로 로그인
3. **"Get API key"** 클릭

#### 🏢 기업마당 API (데이터 수집용)
1. [www.bizinfo.go.kr](https://www.bizinfo.go.kr) 접속
2. 회원가입 후 API 키 신청
3. 승인 대기 (보통 1-2일 소요)

---

## 🗄️ Supabase 설정

### 1단계: 프로젝트 생성
1. **Supabase 대시보드**에서 **"New project"** 클릭
2. 프로젝트 정보 입력:
   ```
   Name: government-support-gyeongnam
   Database Password: 강력한 비밀번호 설정 (꼭 기억해두세요!)
   Region: Northeast Asia (Seoul) 선택
   ```
3. **"Create new project"** 클릭
4. ⏰ **2-3분 대기** (프로젝트 생성 중)

### 2단계: 데이터베이스 스키마 생성
1. 프로젝트 생성 완료 후 **"SQL Editor"** 클릭
2. **"New query"** 클릭
3. `gyeongnam_schema.sql` 파일 내용을 복사해서 붙여넣기
4. **"Run"** 버튼 클릭 (▶️)
5. ✅ **"Success"** 메시지 확인

### 3단계: 연결 정보 확인
1. **"Settings"** → **"Database"** 클릭
2. **"Connection string"** 섹션에서 다음 정보 복사:
   ```
   Host: db.xxxxxxxxxx.supabase.co
   Database name: postgres
   Port: 5432
   User: postgres
   Password: [설정한 비밀번호]
   ```
3. **"Settings"** → **"API"** 클릭
4. 다음 정보 복사:
   ```
   Project URL: https://xxxxxxxxxx.supabase.co
   anon public key: eyJ0eXAi... (긴 문자열)
   ```

> 💡 **팁**: 이 정보들을 메모장에 저장해두세요!

---

## 🔑 API 키 발급

### 1. Google Gemini API 키
1. [aistudio.google.com](https://aistudio.google.com) 접속
2. **"Get API key"** 클릭
3. **"Create API key"** → **"Create API key in new project"** 선택
4. 생성된 키 복사 (예: `AIzaSyC...`)

### 2. 기업마당 API 키
1. [www.bizinfo.go.kr](https://www.bizinfo.go.kr) 접속
2. 로그인 후 **"API 서비스"** 메뉴
3. **"API 키 신청"** 후 승인 대기
4. 승인 후 키 확인 (예: `abc123...`)

---

## 💻 로컬 개발 환경 설정

### 1단계: 프로젝트 다운로드
```bash
# 터미널/명령 프롬프트 열기
git clone [저장소 URL]
cd government_support_system
```

### 2단계: Python 가상환경 생성
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux  
python -m venv venv
source venv/bin/activate
```

### 3단계: 패키지 설치
```bash
pip install -r requirements.txt
```

### 4단계: 환경변수 설정
`.env` 파일을 열고 실제 값으로 수정:

```env
# Supabase 데이터베이스 (위에서 복사한 정보)
SUPABASE_HOST=db.xxxxxxxxxx.supabase.co
SUPABASE_USER=postgres
SUPABASE_PASSWORD=설정한_비밀번호
SUPABASE_DB=postgres
SUPABASE_PORT=5432
SUPABASE_URL=https://xxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ0eXAi...

# API 키 (위에서 발급받은 키들)
BIZINFO_API_KEY=발급받은_기업마당_API_키
GEMINI_API_KEY=AIzaSyC...

# Flask 설정
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# 관리자 계정
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

> ⚠️ **주의**: 실제 키 값을 입력하세요. `your_xxx` 같은 템플릿 텍스트는 작동하지 않습니다!

### 5단계: 로컬 테스트
```bash
python app.py
```

브라우저에서 `http://localhost:5000` 접속하여 확인

---

## 🚀 Vercel 배포

### 1단계: Vercel CLI 설치
```bash
npm install -g vercel
```

### 2단계: Vercel 로그인
```bash
vercel login
```
브라우저에서 GitHub 계정으로 로그인

### 3단계: 프로젝트 배포
```bash
vercel
```

질문에 답변:
- **Set up and deploy?** → Y
- **Which scope?** → 개인 계정 선택
- **Link to existing project?** → N
- **Project name?** → government-support-gyeongnam
- **Directory?** → Enter (현재 디렉토리)

### 4단계: 환경변수 설정
Vercel 대시보드에서:
1. 배포된 프로젝트 클릭
2. **"Settings"** → **"Environment Variables"** 클릭
3. 다음 환경변수들 추가:

```
SUPABASE_HOST = db.xxxxxxxxxx.supabase.co
SUPABASE_USER = postgres  
SUPABASE_PASSWORD = 설정한_비밀번호
SUPABASE_DB = postgres
SUPABASE_PORT = 5432
SUPABASE_URL = https://xxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY = eyJ0eXAi...
BIZINFO_API_KEY = 발급받은_기업마당_API_키
GEMINI_API_KEY = AIzaSyC...
FLASK_SECRET_KEY = your-secret-key-here
ADMIN_USERNAME = admin
ADMIN_PASSWORD = admin123
```

### 5단계: 재배포
환경변수 설정 후:
```bash
vercel --prod
```

---

## ✅ 테스트 및 확인

### 1. 웹사이트 접속
배포된 URL (예: `https://government-support-gyeongnam.vercel.app`)에 접속

### 2. 시스템 상태 확인
`https://your-domain.vercel.app/health` 접속하여 다음 확인:
```json
{
  "status": "healthy",
  "database": "connected",
  "total_announcements": 0
}
```

### 3. 관리자 로그인 테스트
1. `/login` 페이지 접속
2. 설정한 관리자 계정으로 로그인
3. 대시보드 접속 확인

### 4. 데이터 수집 테스트
관리자 대시보드에서:
1. **"수동 데이터 수집"** 버튼 클릭
2. 검색 개수 설정 (예: 10개)
3. 수집 결과 확인

---

## 🔧 문제 해결

### 자주 발생하는 문제들

#### 1. 데이터베이스 연결 오류
**증상**: `connection failed` 에러
**해결법**:
- Supabase 연결 정보 재확인
- 방화벽 설정 확인
- 비밀번호에 특수문자가 있다면 URL 인코딩

#### 2. API 키 오류  
**증상**: `API key invalid` 에러
**해결법**:
- API 키 재확인 (공백 없이 정확히 입력)
- API 키 사용 권한 확인
- 일일 사용량 한도 확인

#### 3. Vercel 배포 실패
**증상**: 배포 중 오류 발생
**해결법**:
- `requirements.txt` 패키지 버전 확인
- Python 버전 호환성 확인 (3.9+)
- 로그 확인: `vercel logs`

#### 4. 환경변수 인식 안됨
**증상**: `None` 값 오류
**해결법**:
- `.env` 파일 위치 확인 (프로젝트 루트)
- 환경변수 이름 정확히 입력
- Vercel 환경변수 저장 후 재배포

### 디버깅 팁

#### 로컬 환경 디버그
```bash
# 환경변수 확인
python -c "import os; print(os.getenv('SUPABASE_HOST'))"

# 데이터베이스 연결 테스트
python -c "from config.database import test_database_connection; test_database_connection()"
```

#### Vercel 환경 디버그
```bash
# 배포 로그 확인
vercel logs

# 특정 함수 로그 확인  
vercel logs --follow
```

---

## 🆘 도움이 필요할 때

### 공식 문서
- [Supabase 공식 문서](https://supabase.com/docs)
- [Vercel 공식 문서](https://vercel.com/docs)
- [Flask 공식 문서](https://flask.palletsprojects.com/)

### 커뮤니티 지원
- [Supabase Discord](https://discord.supabase.com/)
- [Vercel Discord](https://discord.gg/vercel)
- Stack Overflow

### 이슈 신고
시스템 관련 문제는 GitHub Issues에 신고해주세요.

---

## 🎉 축하합니다!

설치가 완료되었습니다! 이제 경남 특화 정부지원사업 분류 시스템을 사용할 수 있습니다.

### 다음 단계
1. 실제 데이터 수집 시작
2. 분류 정확도 모니터링  
3. 필요에 따라 키워드 매핑 조정
4. 정기적인 백업 설정

### 유지보수 팁
- 주기적으로 시스템 상태 확인 (`/health`)
- API 사용량 모니터링
- 데이터베이스 용량 관리
- 보안 업데이트 적용

**🚀 즐거운 개발되세요!**