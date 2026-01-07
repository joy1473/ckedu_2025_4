from pymongo import MongoClient
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from elasticsearch import Elasticsearch

load_dotenv()

# MongoDB URI from .env
MONGO_URI = os.getenv("MONGO_URI")

# Elasticsearch/OpenSearch 연결
es = Elasticsearch(
    [os.getenv("OPENSEARCH_URL")],
    http_auth=(os.getenv("OPENSEARCH_USER"), os.getenv("OPENSEARCH_PASS")),
    headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=7"},
    verify_certs=True
)

# # 컬렉션 정의
client = MongoClient(MONGO_URI)
db = client.mock_trading_db
config_collection = db.users_config  # 시스템 설정 컬렉션
trades_collection = db.trades        # 이벤트 로그 컬렉션
emo_logs_collection = db.emo_logs    # 감정 분석 로그 컬렉션
users_collection = db.users          # 사용자 컬렉션

# FastAPI 앱 생성
app = FastAPI(title="Config Management API", version="1.0.0")

# Pydantic 모델
class ConfigResponse(BaseModel):
    out_config: Dict[str, Any]

class ValueResponse(BaseModel):
    out_value: Any

class LogEventRequest(BaseModel):
    event: str
    user_id: Optional[str] = None
    note: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class LogEventResponse(BaseModel):
    out_success: bool
    out_inserted_id: Optional[str] = None
    out_error: Optional[str] = None

_cache: Dict[str, Any] = {}

@app.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """
    시스템 설정 불러오기 (캐싱 포함)
    """
    global _cache
    if _cache:
        return ConfigResponse(out_config=_cache)

    doc = config_collection.find_one({"_id": "config"})
    if not doc:
        raise HTTPException(status_code=404, detail="mock_trading_db.users_config에 '_id: config' 문서가 없습니다. 설정을 삽입해주세요.")

    _cache = {k: v for k, v in doc.items() if k != "_id"}
    return ConfigResponse(out_config=_cache)

@app.get("/config/{key}", response_model=ValueResponse)
async def get_value(key: str, default: Optional[Any] = None) -> ValueResponse:
    """
    특정 설정값 가져오기
    """
    config = await get_config()
    value = config.out_config.get(key, default)
    return ValueResponse(out_value=value)

@app.post("/log", response_model=LogEventResponse)
async def log_event(request: LogEventRequest) -> LogEventResponse:
    """
    이벤트 로그 저장
    """
    log_doc = {
        "event": request.event,
        "timestamp": datetime.utcnow(),
        "user_id": request.user_id,
        "note": request.note,
        **(request.extra or {})
    }

    try:
        result = trades_collection.insert_one(log_doc)
        return LogEventResponse(
            out_success=True,
            out_inserted_id=str(result.inserted_id)
        )
    except Exception as e:
        return LogEventResponse(
            out_success=False,
            out_error=str(e)
        )