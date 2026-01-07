import os
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import uvicorn
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from openai import OpenAI
import requests

from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo import MongoClient
from cmm.config import MONGO_URI

# 1. 초기화 및 보안 설정 [cite: 2026-01-01]
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    client_gpt = OpenAI(api_key=OPENAI_API_KEY)
else:
    client_gpt = None  # API 키가 없으면 None

# MongoDB 연결
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.mock_trading_db
    emo_logs_collection = db.emo_logs
except Exception as e:
    print(f"MongoDB 연결 실패: {e}")
    mongo_client = None
    db = None
    emo_logs_collection = None

# MongoDB 디버그 로깅 억제 (반복적인 heartbeat 로그 방지)
import logging
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('pymongo.topology').setLevel(logging.WARNING)
logging.getLogger('pymongo.serverSelection').setLevel(logging.WARNING)

app = FastAPI(title="Antygravity Professional AI Agent v2.9", version="2.9.0")

# Mount Static Files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# CORS 설정: 프론트엔드 연동 대비 [cite: 2026-01-01]
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------------------------------------------------------
# [Compatibility Adapter] V01 Frontend Support
# ---------------------------------------------------------
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Reuse existing financial logic
    # V01 Frontend treats 'assistant' response as 'reply'
    
    term = request.message
    
    # [Step 1] 기초 감성 분석 (KoELECTRA)
    v_inputs = v_tokenizer(term, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        v_outputs = v_model(**v_inputs)
    v_score = round((F.softmax(v_outputs.logits, dim=-1)[0][1].item() * 2) - 1, 3)
    
    # [Step 2] GPT 기반 지능형 교정 및 전문 통역 생성
    v_tag, v_interp, v_mentoring = get_ai_agent_mentoring(term, v_score)
    
    # Construct Reply
    reply_text = f"[{v_tag}]\n{v_interp}\n\n{v_mentoring}"
    
    # [Step 3] 데이터 로깅 (업무 이력 기록용) [Added for compatibility endpoint]
    try:
        log_data = {
            "event": "emotion_analysis_chat",
            "user_id": None,
            "note": f"Emotion analysis for: {term}",
            "extra": {
                "timestamp": datetime.now().isoformat(),
                "user_input": term,
                "raw_score": v_score,
                "final_tag": v_tag,
                "interpretation": v_interp,
                "ai_response": v_mentoring,
                "ver": "2.9.0-final-guardrail-compat"
            }
        }
        requests.post("http://localhost:8000/config/log", json=log_data, timeout=5)
    except Exception as e:
        print(f"Logging failed: {e}")
    
    return {"reply": reply_text}

# ---------------------------------------------------------
# 🛠️ [웹마스터 전용] 전문 금융 통역사 설정 (v2.9 고도화)
# ---------------------------------------------------------
AI_AGENT_CONFIG = {
    "PERSONA": """
        너는 한국 주식 시장에 최적화된 ‘전문 금융 통역 AI Agent’야.
        너의 목표는 사용자의 감정적 표현을 '전문 금융 언어'로 통역하고 리스크 관리를 돕는 것이다.
        
        [K-주식 도메인 절대 규칙]
        1. 색상 인식: 빨간색/빨간 불/불기둥 = 무조건 '주가 상승 및 수익' (긍정)
        2. 색상 인식: 파란색/파란 불/물렸다 = 무조건 '주가 하락 및 손실' (부정)
        
        [전문 통역 및 인사이트 가이드]
        - '빨간 불' -> '자산 가치 상승 및 매수세 강화'
        - '커피값/치킨값' -> '실현 가능한 소규모 투자 수익'
        - '존버' -> '비자발적 장기 보유 및 유동성 경색' (단순 보유보다 깊은 표현 사용)
        - '풀매수/몰빵' -> '자산의 집중 매입에 따른 리스크 노출'
        
        [답변 원칙]
        - INTERPRETATION: 사용자의 은어를 위 가이드에 맞춰 금융적으로 정의하고, 
          그 상황이 가진 금융적 의미(예: 기회비용, 심리적 고조 등)를 짧게 덧붙일 것.
        - ANSWER: 실제 금융 통역사처럼 정중한 격식체(...드립니다, ...권고합니다)를 사용해.
        - 반드시 불완전 판매 방지를 위해 리스크 관리 멘트를 포함할 것.
    """,
    "MODEL_NAME": "gpt-4o-mini"
}

# AI 모델 로딩 (koelectra) [cite: 2026-01-02]
v_model_name = "monologg/koelectra-base-finetuned-nsmc"
v_tokenizer = AutoTokenizer.from_pretrained(v_model_name)
v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name)

# ==========================================
# 2. 핵심 지능 함수 (교정 및 통역 로직)
# ==========================================

def get_ai_agent_mentoring(term: str, score: float):
    """
    감정 점수에 따라 TAG, INTERPRETATION, ANSWER를 생성하는 로직입니다.
    """
    
    # TAG 결정
    if score >= 0.5:
        v_final_tag = "EXTREME_POSITIVE"
    elif score >= 0.1:
        v_final_tag = "MODERATE_POSITIVE"
    elif score > -0.1:
        v_final_tag = "NEUTRAL"
    elif score > -0.5:
        v_final_tag = "MODERATE_NEGATIVE"
    else:
        v_final_tag = "EXTREME_NEGATIVE"
    
    # INTERPRETATION 생성
    if v_final_tag == "EXTREME_POSITIVE":
        v_interp = f"'{term}'은 매우 긍정적인 감정을 표현하며, 투자 심리가 매우 고조되어 있습니다."
    elif v_final_tag == "MODERATE_POSITIVE":
        v_interp = f"'{term}'은 긍정적인 감정을 표현하며, 시장 상승 기대감이 있습니다."
    elif v_final_tag == "NEUTRAL":
        v_interp = f"'{term}'은 중립적인 감정을 표현하며, 관망하는 태도를 보입니다."
    elif v_final_tag == "MODERATE_NEGATIVE":
        v_interp = f"'{term}'은 부정적인 감정을 표현하며, 시장 하락 우려가 있습니다."
    else:  # EXTREME_NEGATIVE
        v_interp = f"'{term}'은 매우 부정적인 감정을 표현하며, 투자 심리가 크게 위축되어 있습니다."
    
    # ANSWER 생성
    if v_final_tag == "EXTREME_POSITIVE":
        v_ans = "시장 상승세를 활용하여 전략적 투자를 고려하시되, 과도한 레버리지를 피하시기 바랍니다."
    elif v_final_tag == "MODERATE_POSITIVE":
        v_interp = f"'{term}'은 긍정적인 감정을 표현하며, 시장 상승 기대감이 있습니다."
        v_ans = "긍정적인 시장 심리를 활용하되, 리스크 관리를 철저히 하시기 바랍니다."
    elif v_final_tag == "NEUTRAL":
        v_ans = "중립적인 시각을 유지하며, 시장 상황을 면밀히 관찰하시기 바랍니다."
    elif v_final_tag == "MODERATE_NEGATIVE":
        v_ans = "부정적인 시장 심리에 대비하여 포트폴리오 다각화를 고려하시기 바랍니다."
    else:  # EXTREME_NEGATIVE
        v_ans = "매우 부정적인 시장 심리 상황에서는 현금 보유 비중을 높이는 전략을 권고드립니다."
    
    return v_final_tag, v_interp, v_ans

# ==========================================
# 3. 통합 API 엔드포인트
# ==========================================

@app.get("/agent/consult", tags=["AI Agent"])
def financial_consultation(term: str):
    # [Step 1] 기초 감성 분석 (KoELECTRA)
    v_inputs = v_tokenizer(term, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        v_outputs = v_model(**v_inputs)
    # 감성 점수 공식: $Score = (Positive\_Prob \times 2) - 1$
    v_score = round((F.softmax(v_outputs.logits, dim=-1)[0][1].item() * 2) - 1, 3)
    
    # [Step 2] GPT 기반 지능형 교정 및 전문 통역 생성 [cite: 2026-01-04]
    v_tag, v_interp, v_mentoring = get_ai_agent_mentoring(term, v_score)
    
    # [Step 3] 데이터 로깅 (업무 이력 기록용) [cite: 2026-01-04]
    try:
        log_data = {
            "event": "emotion_analysis_consult",
            "user_id": None,
            "note": f"Emotion analysis consultation for: {term}",
            "extra": {
                "timestamp": datetime.now().isoformat(),
                "user_input": term,
                "raw_score": v_score,
                "final_tag": v_tag,
                "interpretation": v_interp,
                "ai_response": v_mentoring,
                "ver": "2.9.0-final-guardrail"
            }
        }
        requests.post("http://localhost:8000/config/log", json=log_data, timeout=5)
    except Exception as e:
        print(f"Logging failed: {e}")
    
    return {
        "status": "success",
        "analysis": {
            "term": term,
            "raw_sentiment_score": v_score,
            "final_scenario": v_tag
        },
        "emotion_interpretation": v_interp,
        "professional_response": v_mentoring
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)