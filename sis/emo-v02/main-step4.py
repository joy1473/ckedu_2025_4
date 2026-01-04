import os
from dotenv import load_dotenv # 라이브러리 추가 [cite: 2026-01-01]
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import uvicorn
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from openai import OpenAI

# 1. 환경 변수 로드 (.env 파일 읽기) [cite: 2026-01-01]
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Antygravity AI Mentor Backend", version="1.2.1")

# CORS 설정 [cite: 2026-01-01]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI 클라이언트 (보안 방식 반영) [cite: 2026-01-01]
client_gpt = OpenAI(api_key=OPENAI_API_KEY)

# AI 감성 분석 모델 (경로 반영: koelectra) [cite: 2026-01-02]
v_model_name = "monologg/koelectra-base-finetuned-nsmc"
v_tokenizer = AutoTokenizer.from_pretrained(v_model_name)
v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name)

# DB 연결 [cite: 2026-01-01]
client_db = MongoClient("mongodb://localhost:27017/")
db = client_db["game_db"]
collection = db["game_terms"]

# [생략] get_realtime_sentiment 함수 (기존과 동일) [cite: 2025-12-31]

def get_ai_mentor_response(term: str, score: float):
    """추천받으신 gpt-4o-mini 모델을 사용하여 조언을 생성합니다."""
    v_status = "긍정적" if score > 0.1 else "부정적" if score < -0.1 else "중립적"
    
    v_prompt = f"너는 20년 경력의 주식 투자 멘토야. '{term}'의 심리 점수가 {score}점({v_status})으로 분석되었어. 전문가다운 조언을 2~3문장으로 해줘."
    
    try:
        response = client_gpt.chat.completions.create(
            model="gpt-4o-mini", # 모델 변경 반영 [cite: 2026-01-01]
            messages=[{"role": "user", "content": v_prompt}],
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"멘토링 생성 중 오류: {str(e)}"

@app.get("/search/{term}", tags=["Search"])
def search_and_mentoring(term: str):
    # [Step 1] DB 조회 [cite: 2026-01-01]
    v_doc = collection.find_one({"term": term}, {"_id": 0})
    
    if v_doc:
        v_score = v_doc.get("analysis", {}).get("sentiment_score", 0.0)
        v_source = "database"
    else:
        # [Step 2] 실시간 분석 [cite: 2025-12-31]
        v_score = round((F.softmax(v_model(**v_tokenizer(term, return_tensors="pt"))[0], dim=-1)[0][1].item() * 2) - 1, 3)
        v_source = "ai_inference"
    
    # [Step 3] GPT 멘토링 [cite: 2026-01-01]
    v_mentoring = get_ai_mentor_response(term, v_score)
    
    return {
        "status": "success",
        "source": v_source,
        "data": {
            "term": term,
            "sentiment_score": v_score,
            "ai_mentor_speech": v_mentoring
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)