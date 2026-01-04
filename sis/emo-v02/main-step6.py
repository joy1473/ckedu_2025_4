import os
from datetime import datetime # 시간 기록용 추가
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

app = FastAPI(title="WOW-Point AI Agent with Logging", version="1.6.0")

# CORS 설정
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# AI 모델 로딩 (koelectra) [cite: 2026-01-02]
v_model_name = "monologg/koelectra-base-finetuned-nsmc"
v_tokenizer = AutoTokenizer.from_pretrained(v_model_name)
v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name)

# DB 연결 및 컬렉션 설정 [cite: 2026-01-01]
client_db = MongoClient("mongodb://localhost:27017/")
db = client_db["game_db"]
collection = db["game_terms"]
log_collection = db["test_logs"] # 로그 저장을 위한 새 컬렉션 [cite: 2026-01-04]

# ==========================================
# 2. 유틸리티 함수 (시나리오 및 멘토링) [cite: 2026-01-04]
# ==========================================
def get_scenario_strategy(score: float):
    if score <= -0.7: return "EXTREME_NEGATIVE", "정서적 위로 및 휴식 권고"
    elif -0.7 < score <= -0.1: return "MODERATE_NEGATIVE", "리스크 관리 기반 선회 제안"
    elif 0.1 <= score < 0.7: return "MODERATE_POSITIVE", "수익 축하 및 단계별 가이드"
    elif score >= 0.7: return "EXTREME_POSITIVE", "성취감 공감 및 포트폴리오 추천"
    return "NEUTRAL", "객관적 정보 전달 및 관망"

def get_ai_agent_mentoring(term: str, score: float):
    v_type, v_strategy = get_scenario_strategy(score)
    v_system_prompt = f"너는 금융 통역 AI Agent야. 전략: {v_strategy}. 표준 스크립트를 사용하되 친절하게 답변해줘."
    v_user_prompt = f"사용자의 상황: '{term}'. 이 상황에 맞는 조언을 2~3문장으로 해줘."
    
    try:
        response = client_gpt.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": v_system_prompt}, {"role": "user", "content": v_user_prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content, v_type
    except Exception as e:
        return f"오류 발생: {str(e)}", "ERROR"

# ==========================================
# 3. 통합 API 및 로깅 엔드포인트
# ==========================================
@app.get("/agent/consult", tags=["AI Agent"])
def financial_consultation(term: str):
    # [1] AI 감성 분석 수행 [cite: 2025-12-31]
    v_inputs = v_tokenizer(term, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        v_outputs = v_model(**v_inputs)
    v_score = round((F.softmax(v_outputs.logits, dim=-1)[0][1].item() * 2) - 1, 3)
    
    # [2] 시나리오 기반 멘토링 생성 [cite: 2026-01-04]
    v_mentoring, v_scenario = get_ai_agent_mentoring(term, v_score)
    
    # [3] 데이터 로깅 (MongoDB 저장) [cite: 2026-01-04]
    # 나중에 엑셀로 뽑거나 통계 내기 좋게 구조화합니다.
    v_log_data = {
        "timestamp": datetime.now(), # 기록 일시
        "user_input": term,          # 사용자 입력값
        "sentiment_score": v_score,  # AI 감성 점수
        "scenario_tag": v_scenario,  # 판정된 시나리오
        "ai_response": v_mentoring,  # 최종 멘토링 답변
        "model_info": {
            "sentiment_model": "KoELECTRA",
            "chat_model": "gpt-4o-mini"
        }
    }
    log_collection.insert_one(v_log_data) # DB에 기록 저장
    
    return {
        "status": "success",
        "analysis": {
            "term": term,
            "sentiment_score": v_score,
            "scenario_tag": v_scenario
        },
        "wow_point_response": v_mentoring
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)