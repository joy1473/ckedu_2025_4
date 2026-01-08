from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import uvicorn
import os
from dotenv import load_dotenv
load_dotenv()

# ==========================================
# 1. FastAPI 서버 초기화
# ==========================================
app = FastAPI(
    title="Antygravity AI Backend",
    description="2단계: MongoDB 상세 조회 API 연동 단계",
    version="1.0.0"
)

# [중요] Antygravity 프론트엔드와 포트가 달라도 통신이 가능하도록 CORS 허용 [cite: 2026-01-01]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 테스트 단계이므로 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. MongoDB 연결 설정 (집 PC 환경) [cite: 2026-01-01]
# ==========================================
MONGO_URL = os.getenv("MONGO_DB_URL")
client = MongoClient(MONGO_URL)
db = client["mock_trading_db"]
collection = db["emo_db"]

# ==========================================
# 3. API 엔드포인트 정의
# ==========================================

@app.get("/", tags=["System"])
def root():
    """서버 연결 상태 확인용"""
    return {"message": "Antygravity AI Backend is Running!"}

@app.get("/db-check", tags=["System"])
def check_db_connection():
    """1단계: DB 연결 및 데이터 건수 확인 테스트"""
    try:
        client.admin.command('ping')
        count = collection.count_documents({})
        return {
            "db_status": "Connected",
            "total_terms": count,
            "message": "데이터베이스 연결에 성공했습니다."
        }
    except Exception as e:
        return {"db_status": "Disconnected", "error": str(e)}

@app.get("/search/{term}", tags=["Search"])
def search_slang(term: str):
    """
    2단계: 사용자가 입력한 단어(term)를 DB에서 상세 검색 [cite: 2026-01-01]
    """
    # MongoDB에서 단어 검색 (정확히 일치하는 데이터 탐색)
    # _id 필드는 JSON 변환이 안 되므로 제외하고 가져옵니다. [cite: 2026-01-01]
    v_doc = collection.find_one({"term": term}, {"_id": 0})
    
    # 데이터가 없는 경우 404 에러 반환 (예외 처리) [cite: 2026-01-01]
    if not v_doc:
        raise HTTPException(
            status_code=404, 
            detail=f"'{term}'에 대한 데이터를 찾을 수 없습니다. 신조어 제보를 해주세요!"
        )
    
    # 성공 시 데이터 구조를 정리하여 반환 [cite: 2025-12-31]
    return {
        "status": "success",
        "data": {
            "term": v_doc.get("term"),
            "category": v_doc.get("category"),
            "sentiment_score": v_doc.get("analysis", {}).get("sentiment_score", 0.0),
            "morphemes": v_doc.get("analysis", {}).get("morphemes", []),
            "current_status": v_doc.get("status")
        }
    }

# ==========================================
# 4. 서버 실행 엔진
# ==========================================
if __name__ == "__main__":
    # reload=True 설정으로 코드 수정 시 서버가 자동 재시작됩니다. [cite: 2026-01-01]
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)