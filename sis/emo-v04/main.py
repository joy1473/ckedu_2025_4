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

# 1. 초기화 및 보안 설정
load_dotenv()

app = FastAPI(title="Antygravity Professional AI Agent v2.9 (Local)", version="2.9.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    message: str
    case_id: str = "CASE 02"  # 기본값: 직장인 페르소나

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# AI 모델 로딩 (koelectra)
v_model_name = "monologg/koelectra-base-finetuned-nsmc"
v_tokenizer = AutoTokenizer.from_pretrained(v_model_name)
v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name)

# DB 연결 (MongoDB)
client_db = MongoClient(os.getenv("MONGO_DB_URL"))
db = client_db["mock_trading_db"]
log_collection = db["emo_logs"]

# ==========================================
# 2. 핵심 지능 함수 (K-주식 도메인 규칙 및 페르소나 로직)
# ==========================================

def get_ai_agent_mentoring(term: str, score: float, case_id: str = "CASE 02"):
    """
    K-주식 도메인 절대 규칙과 5가지 페르소나 로직을 적용한 멘토링 생성 함수
    """
    
    # [K-주식 도메인 용어 사전] [cite: 2026-01-08]
    STOCK_DICT = {
        "빨간 불": "자산 가치 상승 및 매수세 강화",
        "불기둥": "강력한 주가 상승 모멘텀 확보",
        "파란 불": "주가 하락 및 자산 가치 감소",
        "물렸다": "주가 하락에 따른 비자발적 보유 상태",
        "존버": "비자발적 장기 보유 및 유동성 경색",
        "풀매수": "자산의 집중 매입에 따른 리스크 노출",
        "몰빵": "포트폴리오 집중 투자로 인한 변동성 위험 고조",
        "치킨값": "실현 가능한 소규모 투자 수익"
    }

    # 1. 용어 통역 (Interpretation) 로직 [cite: 2026-01-08]
    interpreted_term = term
    for slang, formal in STOCK_DICT.items():
        if slang in term:
            interpreted_term = interpreted_term.replace(slang, f"'{formal}'")

    # 2. 감성 태그 결정 [cite: 2026-01-08]
    if score >= 0.6: v_final_tag = "EXTREME_POSITIVE"; tag_kr = "강력 매수 우위"
    elif 0.2 <= score < 0.6: v_final_tag = "MODERATE_POSITIVE"; tag_kr = "매수 심리 우세"
    elif -0.2 < score < 0.2: v_final_tag = "NEUTRAL"; tag_kr = "관망세/중립"
    elif -0.6 < score <= -0.2: v_final_tag = "MODERATE_NEGATIVE"; tag_kr = "매도 압력 감지"
    else: v_final_tag = "EXTREME_NEGATIVE"; tag_kr = "공포/패닉 셀링"

    v_interp = f"분석 결과, 입력하신 '{term}'은 금융적으로 {interpreted_term} 상황을 의미하며, 현재 시장에서 {tag_kr}({v_final_tag}) 시그널이 포착되었습니다."

    # 3. 페르소나별 맞춤 조언 (Mentoring)
    mentoring_db = {
        "CASE 01": { # 공격적 MZ
            "POSITIVE": "공격적인 포지션 구축이 유리한 구간입니다. 레버리지 활용 시 변동성에 유의하며 목표 수익률에 집중하시길 권고드립니다.",
            "NEGATIVE": "단기적 하락은 저가 매수의 기회일 수 있으나, 자산 집중 매입에 따른 리스크가 크니 주의 깊게 시장을 주시하시길 바랍니다."
        },
        "CASE 02": { # 꼼꼼한 직장인
            "POSITIVE": "양호한 상승 흐름이 기대됩니다. ETF 및 적립식 투자 원칙을 유지하며 포트폴리오의 펀더멘털을 점검하시길 권장합니다.",
            "NEGATIVE": "시장 심리가 위축되고 있습니다. 무리한 추가 매수보다는 리스크 관리에 집중하며 하락 방어 전략을 검토하시길 바랍니다."
        },
        "CASE 03": { # 안전제일 은퇴자
            "POSITIVE": "시장 분위기가 양호합니다. 하지만 무리한 투자보다는 원금을 잘 지키면서 안정적인 배당 수익을 먼저 고려하시길 권유드립니다.",
            "NEGATIVE": "현재 시장이 많이 불안합니다. 무리하게 대응하지 마시고, 소중한 은퇴 자산을 지키기 위해 안전한 현금 보유를 적극 추천드립니다."
        },
        "CASE 04": { # 사회초년생 입문자
            "POSITIVE": "좋은 투자의 시작입니다. 현재 수익에 안주하기보다 기본 용어를 학습하며 소액 모의투자로 실전 감각을 익혀보시길 권고합니다.",
            "NEGATIVE": "손실에 당황하지 마세요. 현재의 하락을 공부의 기회로 삼으시고, 소액 투자 원칙을 지키며 시장의 원리를 먼저 파악하시길 바랍니다."
        },
        "CASE 05": { # 꿈나무 투자자
            "POSITIVE": "주식 공부하기 좋은 날입니다! 시장의 원리를 익혀보는 학습 위주의 투자를 추천하며, 반드시 보호자님과 상의하시길 바랍니다.",
            "NEGATIVE": "지금처럼 위험한 때는 투자를 잠시 멈추고 공부에 집중하는 것이 좋습니다. 고위험 상품은 차단하고 교육용 콘텐츠에 집중하세요."
        }
    }
    
    current_case = mentoring_db.get(case_id, mentoring_db["CASE 02"])
    tone = "POSITIVE" if score >= 0.2 else ("NEGATIVE" if score <= -0.2 else "NEUTRAL")
    
    if tone == "NEUTRAL":
        v_ans = "현재 시장은 방향성이 뚜렷하지 않은 구간입니다. 섣부른 진입보다는 현금을 보유하며 변동성 확대를 대비하시길 권고드립니다."
    else:
        v_ans = current_case.get(tone, "시장 환경에 맞춘 리스크 관리가 필요합니다. 현재 포트폴리오 상태를 점검하십시오.")

    # [수정] 본문의 중복된 경고 문구 삭제 (Discord Footer에서 통합 처리 예정) [cite: 2026-01-08]
    return v_final_tag, v_interp, v_ans

# ---------------------------------------------------------
# 3. 통합 API 엔드포인트
# ---------------------------------------------------------

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    term = request.message
    v_inputs = v_tokenizer(term, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        v_outputs = v_model(**v_inputs)
    v_score = round((F.softmax(v_outputs.logits, dim=-1)[0][1].item() * 2) - 1, 3)
    
    v_tag, v_interp, v_mentoring = get_ai_agent_mentoring(term, v_score, request.case_id)
    reply_text = f"[{v_tag}]\n{v_interp}\n\n{v_mentoring}"
    
    log_collection.insert_one({
        "timestamp": datetime.now(),
        "user_input": term,
        "case_id": request.case_id,
        "raw_score": v_score,
        "final_tag": v_tag,
        "ai_response": v_mentoring,
        "ver": "2.9.0-final-guardrail-compat"
    })
    
    return {"reply": reply_text}

@app.get("/agent/consult", tags=["AI Agent"])
def financial_consultation(term: str, case_id: str = "CASE 02"):
    v_inputs = v_tokenizer(term, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        v_outputs = v_model(**v_inputs)
    v_score = round((F.softmax(v_outputs.logits, dim=-1)[0][1].item() * 2) - 1, 3)
    
    v_tag, v_interp, v_mentoring = get_ai_agent_mentoring(term, v_score, case_id)
    
    log_collection.insert_one({
        "timestamp": datetime.now(),
        "user_input": term,
        "case_id": case_id,
        "raw_score": v_score,
        "final_tag": v_tag,
        "ver": "2.9.0-final-guardrail"
    })
    
    return {
        "status": "success",
        "analysis": {"term": term, "raw_sentiment_score": v_score, "case": case_id},
        "emotion_interpretation": v_interp,
        "professional_response": v_mentoring
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)