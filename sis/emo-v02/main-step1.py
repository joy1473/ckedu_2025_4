from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import uvicorn

# ==========================================
# 1. 서버 초기화 및 기획자 설정
# ==========================================
app = FastAPI(
    title="Antygravity AI Backend",
    description="20년 베테랑 웹마스터의 AI 에이전트 서비스 백엔드",
    version="1.0.0"
)

# [중요] Antygravity UI와 통신을 위한 CORS 설정
# 포트가 다르더라도 통신을 허용해줍니다. [cite: 2026-01-01]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 테스트 단계에서는 모두 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. MongoDB 연결 (집 PC 로컬 환경)
# ==========================================
MONGO_URL = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URL)
db = client["game_db"]
collection = db["game_terms"]

# ==========================================
# 3. 테스트용 엔드포인트 (Health Check)
# ==========================================
@app.get("/", tags=["Health Check"])
def root():
    """서버 생존 확인용 루트 경로"""
    return {"message": "Antygravity AI Backend is Running!", "status": "online"}

@app.get("/db-check", tags=["Health Check"])
def check_db_connection():
    """DB 연결 상태 및 데이터 건수 테스트"""
    try:
        # DB에 핑을 날려 연결 확인
        client.admin.command('ping')
        # 총 데이터 건수 확인 [cite: 2025-12-31]
        count = collection.count_documents({})
        return {
            "db_status": "Connected",
            "database": "game_db",
            "total_terms": count,
            "message": "데이터베이스 연결에 성공했습니다."
        }
    except Exception as e:
        return {"db_status": "Disconnected", "error": str(e)}

# ==========================================
# 4. 서버 실행 엔진
# ==========================================
if __name__ == "__main__":
    # uvicorn을 통해 8000번 포트로 서버를 띄웁니다.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)