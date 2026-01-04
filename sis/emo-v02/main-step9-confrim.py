import os
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import uvicorn
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from openai import OpenAI

# 1. 초기화 및 보안 설정 [cite: 2026-01-01]
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client_gpt = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="Antygravity Professional AI Agent v2.9", version="2.9.0")

# CORS 설정: 프론트엔드 연동 대비 [cite: 2026-01-01]
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
client_db = MongoClient("mongodb://localhost:27017/")
db = client_db["game_db"]
log_collection = db["test_logs"]

# ==========================================
# 2. 핵심 지능 함수 (교정 및 통역 로직)
# ==========================================

def get_ai_agent_mentoring(term: str, score: float):
    """
    GPT가 원문을 분석하여 모델 점수를 교정하고, 
    [금융 통역]과 [전문 조언]을 생성하는 핵심 로직입니다. [cite: 2026-01-04]
    """
    v_system_content = f"""
    {AI_AGENT_CONFIG["PERSONA"]}
    
    [분석 미션]
    - 입력값: "{term}" (기초 AI 점수: {score})
    
    [출력 형식 - 엄격 준수]
    TAG: (EXTREME_NEGATIVE / MODERATE_NEGATIVE / NEUTRAL / MODERATE_POSITIVE / EXTREME_POSITIVE)
    INTERPRETATION: (상황에 대한 금융 표준어 통역 및 의미 분석)
    ANSWER: (격조 있는 전문 조언)
    """
    
    try:
        response = client_gpt.chat.completions.create(
            model=AI_AGENT_CONFIG["MODEL_NAME"],
            messages=[{"role": "system", "content": v_system_content}],
            temperature=0.1 # 논리적 일관성을 위해 낮게 고정
        )
        res_text = response.choices[0].message.content
        
        # 텍스트 파싱 처리
        v_final_tag, v_interp, v_ans = "NEUTRAL", "분석 실패", "조언 생성 중 오류"
        lines = res_text.split('\n')
        for line in lines:
            if line.startswith("TAG:"): v_final_tag = line.replace("TAG:", "").strip()
            if line.startswith("INTERPRETATION:"): v_interp = line.replace("INTERPRETATION:", "").strip()
            if line.startswith("ANSWER:"): v_ans = line.replace("ANSWER:", "").strip()
            
        return v_final_tag, v_interp, v_ans
    except Exception as e:
        return "ERROR", f"통역 엔진 오류: {str(e)}", "시스템 점검 중입니다."

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