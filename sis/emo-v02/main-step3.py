from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import uvicorn
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import datetime

# ==========================================
# 1. FastAPI 및 AI 모델 초기화
# ==========================================
app = FastAPI(title="Antygravity AI Backend", version="1.1.0")

# CORS 설정 [cite: 2026-01-01]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI 모델 로드 (KcELECTRA) [cite: 2025-12-31]
print("🧠 AI 모델(KcELECTRA) 로딩 중... 잠시만 기다려 주세요.")
v_model_name = "monologg/koelectra-base-finetuned-nsmc"
v_tokenizer = AutoTokenizer.from_pretrained(v_model_name)
v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name)
print("✅ AI 모델 로딩 완료!")

# DB 연결 [cite: 2026-01-01]
client = MongoClient("mongodb://localhost:27017/")
db = client["game_db"]
collection = db["game_terms"]

# ==========================================
# 2. AI 감성 분석 핵심 함수
# ==========================================
def get_realtime_sentiment(in_text: str):
    """DB에 없는 단어를 AI가 실시간으로 분석합니다. [cite: 2025-12-31]"""
    v_inputs = v_tokenizer(in_text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        v_outputs = v_model(**v_inputs)
    
    v_probs = F.softmax(v_outputs.logits, dim=-1)
    v_pos_prob = v_probs[0][1].item() # 긍정 확률 (0~1)
    
    # 0~1 사이 확률을 -1.0 ~ 1.0 점수로 변환 [cite: 2025-12-31]
    return round((v_pos_prob * 2) - 1, 3)

# ==========================================
# 3. API 엔드포인트 (지능형 조회 로직)
# ==========================================

@app.get("/search/{term}", tags=["Search"])
def search_slang_with_ai(term: str):
    """
    3단계: DB 조회 후 없으면 실시간 AI 분석 수행 (Fallback 로직) [cite: 2026-01-01]
    """
    # [1단계] MongoDB에서 기존 데이터 확인 [cite: 2025-12-31]
    v_doc = collection.find_one({"term": term}, {"_id": 0})
    
    if v_doc:
        # DB에 데이터가 있는 경우: 즉시 반환 (속도 빠름) [cite: 2026-01-01]
        return {
            "status": "success",
            "source": "database",
            "data": {
                "term": v_doc.get("term"),
                "sentiment_score": v_doc.get("analysis", {}).get("sentiment_score"),
                "description": "정제된 DB 데이터를 기반으로 안내합니다."
            }
        }
    
    # [2단계] DB에 없는 경우: AI 실시간 추론 가동 [cite: 2025-12-31, 2026-01-01]
    print(f"🔍 '{term}' 은(는) DB에 없습니다. 실시간 AI 분석을 시작합니다...")
    v_ai_score = get_realtime_sentiment(term)
    
    return {
        "status": "success",
        "source": "ai_inference",
        "data": {
            "term": term,
            "sentiment_score": v_ai_score,
            "description": "DB에 없는 신규 단어입니다. AI가 문맥을 실시간 분석했습니다."
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)