import os
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

app = FastAPI(title="WOW-Point Financial AI Agent", version="1.5.0")

# CORS 설정 (Antygravity 연동용) [cite: 2026-01-01]
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# AI 모델 로딩 (koelectra 반영) [cite: 2026-01-02]
v_model_name = "monologg/koelectra-base-finetuned-nsmc"
v_tokenizer = AutoTokenizer.from_pretrained(v_model_name)
v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name)

# DB 연결 [cite: 2026-01-01]
client_db = MongoClient(os.getenv("MONGO_DB_URL"))
db = client_db["mock_trading_db"]
collection = db["emo_db"]

# ==========================================
# 2. 시나리오 판단 로직 (Brain Layer) [cite: 2026-01-04]
# ==========================================
def get_scenario_strategy(score: float):
    """감성 점수에 따라 대응 전략을 결정합니다. [cite: 2026-01-04]"""
    if score <= -0.7:
        return "EXTREME_NEGATIVE", "강력한 정서적 위로와 매매 중단(휴식) 권고"
    elif -0.7 < score <= -0.1:
        return "MODERATE_NEGATIVE", "손실에 대한 공감 및 리스크 관리 기반의 선회 방법 제안"
    elif 0.1 <= score < 0.7:
        return "MODERATE_POSITIVE", "안정적인 수익 축하 및 단계별 자산 배분 가이드"
    elif score >= 0.7:
        return "EXTREME_POSITIVE", "최고의 성취감 공감 및 후속 투자 포트폴리오 추천"
    else:
        return "NEUTRAL", "객관적인 시장 정보 전달 및 관망 권유"

# ==========================================
# 3. 전문 금융 통역사 멘토링 생성 [cite: 2026-01-04]
# ==========================================
def get_ai_agent_mentoring(term: str, score: float):
    v_type, v_strategy = get_scenario_strategy(score)
    
    # RAG 개념을 활용한 시스템 프롬프트 (표준 스크립트 기반) [cite: 2026-01-04]
    v_system_prompt = f"""
    너는 고객의 페인포인트를 WOW 포인트로 바꾸는 '전문 금융 통역 AI Agent'야.
    사용자의 감성 점수는 {score}점이며, 현재 전략은 '{v_strategy}'이야.
    
    [준수 사항]
    1. 금융 은어를 표준화된 한국어 금융 스크립트로 변환하여 명확하게 설명할 것. [cite: 2026-01-04]
    2. 불완전 판매 방지를 위해 근거 없는 확신보다는 리스크 관리 중심의 조언을 할 것. [cite: 2026-01-04]
    3. 실제 전문 통역사처럼 친절하고 품격 있는 언어를 사용할 것.
    """
    
    v_user_prompt = f"사용자가 지금 '{term}'과 관련해 힘들어하거나 즐거워하고 있어. 이 상황에 맞는 조언을 2~3문장으로 해줘."
    
    try:
        response = client_gpt.chat.completions.create(
            model="gpt-4o-mini", # 가성비 모델 반영 [cite: 2026-01-03]
            messages=[
                {"role": "system", "content": v_system_prompt},
                {"role": "user", "content": v_user_prompt}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content, v_type
    except Exception as e:
        return f"통역 엔진 오류: {str(e)}", "ERROR"

# ==========================================
# 4. 통합 API 엔드포인트 [cite: 2026-01-01]
# ==========================================
@app.get("/agent/consult", tags=["AI Agent"])
def financial_consultation(term: str):
    # 1. DB 조회 및 AI 감성 분석 [cite: 2025-12-31]
    v_inputs = v_tokenizer(term, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        v_outputs = v_model(**v_inputs)
    v_score = round((F.softmax(v_outputs.logits, dim=-1)[0][1].item() * 2) - 1, 3)
    
    # 2. 시나리오 기반 멘토링 생성 [cite: 2026-01-04]
    v_mentoring, v_scenario = get_ai_agent_mentoring(term, v_score)
    
    return {
        "status": "success",
        "analysis": {
            "term": term,
            "sentiment_score": v_score,
            "scenario_tag": v_scenario
        },
        "wow_point_response": v_mentoring # 고객에게 전달될 WOW 포인트 답변 [cite: 2026-01-04]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)