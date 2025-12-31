# 📈 가상 주식 투자 시뮬레이터 프로젝트 가이드

이 프로젝트는 **FastAPI**, **OpenAI(Whisper, GPT)**, **MongoDB**를 활용한 음성 인식 기반 모의 주식 투자 서비스입니다.

---

## 📂 1. 프로젝트 구조 (Project Structure)
`.env` 파일은 보안을 위해 **루트(root)**에 두고, 코드는 **`pyk/lzegg/`** 폴더 내에서 관리합니다.

root/                          # [프로젝트 최상위]
├── .env                       # API 키 및 DB 접속 정보
└── pyk/                       
    └── lzegg/                 # [프로젝트 메인 폴더]
        ├── README.md          # ← 특정 프로젝트용 설명서
        ├── appPyk.py          # FastAPI 서버 (백엔드)
        ├── trading.py         # 주식 로직 및 DB 연결
        ├── requirements.txt   # 라이브러리 목록
        ├── static/            # 정적 파일 (popup.js, css 등)
        └── templates/         # UI 파일 (index.html)

---

## 🔒 2. 보안 설정 (.gitignore)
보안 파일 및 불필요한 캐시 파일이 Git에 올라가지 않도록 관리합니다. 프로젝트 최상위의 `.gitignore` 파일에 아래 내용을 포함하세요.

venv/
.env
__pycache__/
*.pyc
db.sqlite3
*.pem

---

## ⚙️ 3. 환경 변수 설정 (.env)
루트 폴더에 `.env` 파일을 생성하고 아래 형식을 유지하세요. (개인 키는 절대 공유 금지)

OPENBANK_CLIENT_ID=...
OPENBANK_CLIENT_SECRET=...
OPENAI_API_KEY=sk-proj-... [개인 OpenAI KEY]
MONGO_URL=mongodb+srv://계정:비밀번호@ckedu20254.jdcow7k.mongodb.net/

---

## 🚀 4. 설치 및 실행 명령어

### 라이브러리 관리
# 설치된 라이브러리 목록 추출
pip freeze > requirements.txt

# 필요한 라이브러리 일괄 설치
pip install -r requirements.txt

### FastAPI 서버 실행
# 반드시 최상위 경로(root)에서 실행하세요.
uvicorn pyk.lzegg.appPyk:app --reload

---

## 🐙 5. Git 사용 가이드

### VS Code GUI 활용법
1. Pull (가져오기): Ctrl+Shift+G -> 상단 ... 클릭 -> [끌어오기(Pull)] 또는 하단 동기화 아이콘 클릭.
2. Stage (준비): 변경된 파일 옆의 + (더하기) 아이콘 클릭. (파일이 '스테이징된 변경 사항'으로 이동)
3. Commit (저장): 상단 입력창에 메시지 입력 후 [커밋] 버튼 클릭.
4. Push (전송): [Sync Changes] 또는 [변경 내용 게시] 버튼 클릭하여 서버로 전송.

### 터미널 명령어 활용법
# 1. 서버 최신 내용 받기
git pull origin main

# 2. 내 작업 폴더만 정확히 담기 (추천)
git add pyk/lzegg/

# 3. 내 컴퓨터에 기록 남기기
git commit -m "feat: 모의투자 기능 수정"

# 4. 서버(GitHub)로 전송
git push origin main

---

## 💡 유용한 팁 및 규칙

### 한글 파일명 깨짐 방지
터미널에서 한글 파일명이 숫자로 깨져 보인다면 아래 명령어를 입력하세요.
git config --global core.quotepath false

### 자주 쓰는 커밋 머리말(Prefix)
* feat: 새로운 기능 추가
* fix: 버그 수정
* docs: README 등 문서 수정
* style: 코드 의미 없는 수정 (오타, 포맷팅)
* chore: 설정 변경 (.env, 패키지 매니저 등)