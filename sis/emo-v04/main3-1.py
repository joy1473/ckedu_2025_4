from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import uvicorn
import os
from dotenv import load_dotenv
load_dotenv()
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

# 정적 파일 및 템플릿 설정 [cite: 2026-01-07]
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# AI 모델 로드 (KcELECTRA) [cite: 2025-12-31]
print("🧠 AI 모델(KcELECTRA) 로딩 중... 잠시만 기다려 주세요.")
v_model_name = "monologg/koelectra-base-finetuned-nsmc"
v_tokenizer = AutoTokenizer.from_pretrained(v_model_name)
v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name)
print("✅ AI 모델 로딩 완료!")

# DB 연결 [cite: 2026-01-01]
client = MongoClient(os.getenv("MONGO_DB_URL"))
db = client["mock_trading_db"]
collection = db["emo_db"]

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

@app.get("/", tags=["Page"])
async def read_root(request: Request):
    """메인 페이지 (index.html) 렌더링 [cite: 2026-01-07]"""
    return templates.TemplateResponse("index.html", {"request": request})

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

# ==========================================
# 4. 채팅 엔드포인트 (Frontend 연결)
# ==========================================

class UserMessage(BaseModel):
    message: str

@app.post("/chat", tags=["Chat"])
async def chat_endpoint(user_msg: UserMessage):
    """
    프론트엔드 채팅 요청 처리 [cite: 2026-01-07]
    - 사용자 메시지를 받아 감성 분석 수행
    - DB 조회 및 AI 분석 결과를 바탕으로 답변 생성
    """
    msg = user_msg.message.strip()
    
    if not msg:
        return {"reply": "말씀이 없으시네요... 듣고 있어요."}

    # 1. 감성 분석 수행
    sentiment_score = get_realtime_sentiment(msg)
    
    # 2. DB 검색 (키워드 추출이 필요하지만, 여기서는 전체 문장을 검색어로 시도하거나 
    #    간단히 메시지 내용을 반영하여 응답)
    #    (실제로는 형태소 분석기로 명사 추출 후 검색하는 것이 좋음, 여기선 단순화)
    
    response_text = ""
    
    # 감정 점수에 따른 기본 반응
    if sentiment_score > 0.5:
        response_text = "기분이 좋아 보이시네요! 긍정적인 에너지가 느껴져요. 🐣"
    elif sentiment_score < -0.5:
        response_text = "저런... 힘든 일이 있으셨나요? 제가 들어드릴게요. 🍳"
    else:
        response_text = "그렇군요. 조금 더 자세히 이야기해 주시겠어요?"

    # AI 점수 정보 추가 (디버깅용, 나중에 제거 가능)
    # response_text += f"\n(감정 점수: {sentiment_score})"

    return {"reply": response_text}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)