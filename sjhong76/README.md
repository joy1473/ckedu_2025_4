# LUA (Lazy User Agent) 🌙
> **"복잡함은 AI가, 당신은 대화만"** - 채팅형 주식 트레이딩 플랫폼

## 🛠 Tech Stack
- **Frontend**: Streamlit
- **Backend**: Python (FastAPI logic)
- **AI**: OpenAI (GPT-4o-mini)
- **Database/Search**: MongoDB, Elasticsearch (Planned)

## 🚀 How to Run
1. 라이브러리 설치: `pip install -r requirements.txt`
2. 환경 변수 설정: `.env` 파일에 `OPENAI_API_KEY` 입력
3. 실행: `streamlit run lua.py`

```text
ckedu_2025_4/ (Root)
├── hongsangjin/         # [신규 생성] 주인님 전용 폴더
│   ├── lua.py
│   ├── agent/
│   │   └── lua_core.py
│   └── utils/
│       ├── parser.py
│       └── db_handler.py
├── requirements.txt     # (필요시 루트 파일에 내용 추가)
└── .gitignore           # (보안 설정 확인)
