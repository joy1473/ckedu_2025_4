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

# 1. 초기화 및 보안 설정
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client_gpt = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="Antygravity K-Stock AI Agent v2.8", version="2.8.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---------------------------------------------------------
# 🛠️ [웹마스터 전용] K-주식 도메인 가드레일 (절대 규칙)
# ---------------------------------------------------------
AI_AGENT_CONFIG = {
    "PERSONA": """
        너는 한국 주식 시장에 특화된 ‘전문 금융 통역 AI Agent’야.
        글로벌 표준(빨간색=하락)을 완전히 잊고, 오직 한국 시장의 규칙을 따른다.
        
        [K-주식 절대 원칙]
        1. 색상 문맥: 빨간색/빨간 불/불기둥 = 무조건 '자산 가치 상승' 및 '수익'. (긍정 시나리오)
        2. 색상 문맥: 파란색/파란 불/물렸다 = 무조건 '자산 가치 하락' 및 '손실'. (부정 시나리오)
        
        [금융 통역 사전 - 필수 치환]
        - '빨간 불/불기둥' -> '주가 상승에 따른 매수세 강화'
        - '파란 불/파랑새' -> '주가 하락에 따른 매도세 우위'
        - '커피값/치킨값' -> '실현 가능한 소액 투자 수익'
        - '존버' -> '장기 보유를 통한 인내 투자'
        - '풀매수/몰빵' -> '자산의 집중 매입'
        
        [답변 가이드]
        - INTERPRETATION: 사용자의 감정과 은어를 위 사전에 따라 금융 표준어로 '통역'해.
        - ANSWER: 실제 통역사처럼 정중한 격식체(...드립니다, ...권고합니다)를 사용해.
        - 반드시 불완전 판매 방지를 위해 리스크 관리 멘트를 포함해.
    """
}

# AI 모델 로딩 (koelectra)
v_model_name = "monologg/koelectra-base-finetuned-nsmc"
v_tokenizer = AutoTokenizer.from_pretrained(v_model_name)
v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name)

# DB 연결
client_db = MongoClient("mongodb://localhost:27017/")
db = client_db["game_db"]
log_collection = db["test_logs"]

# ==========================================
# 2. 지능형 통역 및 시나리오 교정 함수
# ==========================================

def get_ai_agent_mentoring(term: str, score: float):
    """
    GPT가 원문의 'Intent'를 분석하여 모델의 오판을 교정하고 
    전문적인 금융 통역 결과를 생성함. [cite: 2026-01-04]
    """
    v_system_content = f"""
    {AI_AGENT_CONFIG["PERSONA"]}
    
    [실시간 분석 지침]
    - 입력: "{term}" (AI 점수: {score})
    - 만약 입력에 '빨간' 혹은 상승 의미가 있다면 AI 점수가 낮아도 무조건 POSITIVE 태그를 부여해.
    
    출력 형식:
    TAG: (EXTREME_NEGATIVE / MODERATE_NEGATIVE / NEUTRAL / MODERATE_POSITIVE / EXTREME_POSITIVE)
    INTERPRETATION: (감정 상태의 금융적 통역)
    ANSWER: (격조 있는 전문 조언)
    """
    
    try:
        response = client_gpt.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": v_system_content}],
            temperature=0.0 # 일관성을 위해 무작위성 제거
        )
        res_text = response.choices[0].message.content
        
        v_tag, v_interp, v_ans = "NEUTRAL", "분석 중...", "조언 준비 중..."
        for line in res_text.split('\n'):
            if line.startswith("TAG:"): v_tag = line.replace("TAG:", "").strip()
            if line.startswith("INTERPRETATION:"): v_interp = line.replace("INTERPRETATION:", "").strip()
            if line.startswith("ANSWER:"): v_ans = line.replace("ANSWER:", "").strip()
            
        return v_tag, v_interp, v_ans
    except Exception as e:
        return "ERROR", str(e), "시스템 일시 오류"

# ==========================================
# 3. 통합 API 엔드포인트
# ==========================================

@app.get("/agent/consult", tags=["AI Agent"])
def financial_consultation(term: str):
    # [1] 기초 감성 분석
    v_inputs = v_tokenizer(term, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        v_outputs = v_model(**v_inputs)
    v_score = round((F.softmax(v_outputs.logits, dim=-1)[0][1].item() * 2) - 1, 3)
    
    # [2] GPT 기반 지능형 교정 및 통역
    v_tag, v_interp, v_mentoring = get_ai_agent_mentoring(term, v_score)
    
    # [3] 로깅 (팀원들과 공유할 핵심 데이터)
    log_collection.insert_one({
        "timestamp": datetime.now(),
        "user_input": term,
        "raw_score": v_score,
        "final_tag": v_tag,
        "interpretation": v_interp,
        "ai_response": v_mentoring,
        "version": "2.8.0-final-guardrail"
    })
    
    return {
        "status": "success",
        "analysis": {"term": term, "score": v_score, "tag": v_tag},
        "emotion_interpretation": v_interp,
        "professional_response": v_mentoring
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)