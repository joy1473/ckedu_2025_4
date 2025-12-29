# 📈 가상 주식 투자 시뮬레이터 프로젝트 가이드

이 프로젝트는 **FastAPI**, **OpenAI(Whisper, GPT)**, **MongoDB**를 활용한 음성 인식 기반 모의 주식 투자 서비스입니다.

## 📂 1. 프로젝트 구조 (Project Structure)
`.env` 파일은 보안을 위해 **루트(root)**에 두고, 코드는 **`pyk/lzegg/`** 폴더 내에서 관리합니다.

```text
root/                          # [프로젝트 최상위]
├── .env                       # API 키 및 DB 접속 정보
└── pyk/                       
    └── lzegg/               # [프로젝트 메인 폴더]
        ├── README.md          # ← 특정 프로젝트용 설명서
        ├── appPyk.py          # FastAPI 서버 (백엔드)
        ├── trading.py         # 주식 로직 및 DB 연결
        ├── requirements.txt   # 라이브러리 목록
        ├── static/            # 정적 파일 (bg.jpg 등)
        └── templates/         # UI 파일 (index.html)

##.gitignore 파일 내용입니다(git커밋방지)
venv/
.env
__pycache__/
*.pyc
db.sqlite3

##.env 파일 내용입니다
OPENBANK_CLIENT_ID=6f4f10b4-e3dc-4125-8627-0be912f495c5
OPENBANK_CLIENT_SECRET=85ae2d22-60de-4214-917a-3c8e12a96316
OPENAI_API_KEY=sk-proj-Sq6nCoXXVuaaBi...[개인openAI KEY]
MONGO_URL=mongodb+srv://ckedu20254:Xmas1225!@ckedu20254.jdcow7k.mongodb.net/

##requirement.txt 작성법 및 설치명령
pip freeze > requirements.txt
pip install -r requirements.txt

##fastapi 실행명령
cd C:\ckedu_2025_4\
uvicorn pyk.lzegg.appPyk:app --reload

##git 파일전송 방법
1) vsocde에서 ctrl+shift+g 누르세요.
2)상단에 있는 점 세 개(...) 아이콘을 누릅니다.
-[끌어오기(Pull)] 메뉴를 클릭하면 끝! 
-또는 하단 파란색 상태 표시줄에 있는 **동기화 아이콘(새로고침 모양)**을 눌러도 됩니다.
‐--‐‐소스수정  후‐‐---
3) Stage (준비시키기)
 - U 표시가 있는 파일 이름 옆의 + (더하기) 아이콘을 누르세요. 
 - 파일이 '변경 사항'에서 '스테이징된 변경 사항' 섹션으로 올라갑니다. (커밋 전 필수 단계)
4) Commit (내 컴퓨터에 저장): 
- 상단의 입력창에 커밋 메시지(예: "feat:모의투자 첫 업로드")를 적습니다.
-그 위에 있는 [커밋(Commit)] 버튼을 누릅니다. (이제 내 컴퓨터 저장소에만 저장된 상태입니다.)
5) Push (서버로 보내기): 
- 커밋 버튼이 [변경 내용 게시] 또는 **[Sync Changes]**로 바뀔 겁니다. 그 버튼을 누르세요.
- 이제 원격 서버(Git)로 파일이 전송됩니다.

## git 명령어
1) 서버 최신 내용 받기
git pull
2)변경된 모든 파일을 장바구니에 담기 (Stage)
git add .
3)내 컴퓨터 저장소에 확정 기록 (Commit)
git commit -m "feat: 가상 주식 투자 프로젝트 초기화"
4) 원격 서버로 전송 (Push)
git push origin main

##자주 쓰는 커밋 머리말(Prefix) 목록
​보통 타입: 내용 형식으로 작성합니다.
• ​feat: 새로운 기능을 추가했을 때 (예: feat: 음성 인식 주문 기능 추가)
• ​fix: 버그를 수정했을 때 (예: fix: 로그인 오류 수정)
• ​docs: 문서만 수정했을 때 (예: docs: README.md 수정)
• ​style: 코드 의미에 영향을 주지 않는 수정 (오타 수정, 포맷팅 등)
• ​refactor: 코드 리팩토링 (기능은 그대로인데 구조만 개선)
• ​chore: 빌드 업무 수정, 패키지 매니저 설정 등 (예: chore: .env 설정 추가)
