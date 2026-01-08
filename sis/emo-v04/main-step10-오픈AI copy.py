import os
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
import uvicorn
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 1. 초기화 및 보안 설정 [cite: 2026-01-01]
load_dotenv()

app = FastAPI(title="Antygravity Professional AI Agent v2.9", version="2.9.0")

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

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
    log_collection.insert_one({
        "timestamp": datetime.now(),
        "user_input": term,
        "raw_score": v_score,
        "final_tag": v_tag,
        "interpretation": v_interp,
        "ai_response": v_mentoring,
        "ver": "2.9.0-final-guardrail-compat"
    })
    
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

# DB 연결 (MongoDB) [cite: 2026-01-01]
client_db = MongoClient(os.getenv("MONGO_DB_URL"))
db = client_db["mock_trading_db"]
log_collection = db["emo_logs"]

# ==========================================
# 2. 핵심 지능 함수 (교정 및 통역 로직)
# ==========================================

def get_ai_agent_mentoring(term: str, score: float):
    """
    GPT가 원문을 분석하여 모델 점수를 교정하고, 
    [금융 통역]과 [전문 조언]을 생성하는 핵심 로직입니다. [cite: 2026-01-04]
    """
    # 규칙 기반 태깅 및 전문 조언 생성 (OpenAI 미사용)
    if score >= 0.6:
        v_final_tag = "EXTREME_POSITIVE"
        tag_kr = "강력 매수 우위"
    elif 0.2 <= score < 0.6:
        v_final_tag = "MODERATE_POSITIVE"
        tag_kr = "매수 심리 우세"
    elif -0.2 < score < 0.2:
        v_final_tag = "NEUTRAL"
        tag_kr = "관망세/중립"
    elif -0.6 < score <= -0.2:
        v_final_tag = "MODERATE_NEGATIVE"
        tag_kr = "매도 압력 감지"
    else:
        v_final_tag = "EXTREME_NEGATIVE"
        tag_kr = "공포/패닉 셀링"

    v_interp = f"입력하신 '{term}'에서 {tag_kr} 시그널({v_final_tag})이 포착되었습니다. (AI 점수: {score})"

    if v_final_tag == "EXTREME_POSITIVE":
        v_ans = "시장의 긍정적 에너지가 최고조입니다. 다만, 과열권 진입 가능성을 염두에 두고 차익 실현 계획을 점검하십시오."
    elif v_final_tag == "MODERATE_POSITIVE":
        v_ans = "양호한 상승 흐름이 기대됩니다. 펀더멘털을 점검하며 추세 추종 전략을 유지하는 것을 권장합니다."
    elif v_final_tag == "NEUTRAL":
        v_ans = "방향성이 뚜렷하지 않은 구간입니다. 섣부른 진입보다는 현금을 보유하며 변동성 확대를 대비하십시오."
    elif v_final_tag == "MODERATE_NEGATIVE":
        v_ans = "시장 심리가 위축되고 있습니다. 공격적인 투자는 지양하고 리스크 관리에 집중할 시점입니다."
    else:
        v_ans = "극도의 공포 심리가 지배적입니다. 투매에 동참하기보다 냉철하게 시장을 주시하며 자산 방어에 힘쓰십시오."

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
    log_collection.insert_one({
        "timestamp": datetime.now(),
        "user_input": term,
        "raw_score": v_score,
        "final_tag": v_tag,
        "interpretation": v_interp,
        "ai_response": v_mentoring,
        "ver": "2.9.0-final-guardrail"
    })
    
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