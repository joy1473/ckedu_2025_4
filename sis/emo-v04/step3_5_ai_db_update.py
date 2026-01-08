import datetime
import torch
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F

# ==========================================
# 1. AI 모델 로드 (KcELECTRA Finetuned)
# ==========================================
# 기본: monologg/kcelectra-base-finetuned-nsmc (해당 repo가 private/gated일 수 있음)
# 로드에 실패하면 공개 sentiment 모델로 폴백합니다.
from dotenv import load_dotenv
import os
load_dotenv()

# 우선순위: HUGGINGFACE_TOKEN 또는 HF_TOKEN 환경변수
hf_token = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")

# 모델 접근 사전 체크: Hugging Face API로 repo info 확인
from huggingface_hub import HfApi

def check_repo_access(repo_id, token=None):
    api = HfApi()
    try:
        api.model_info(repo_id, token=token)
        return True
    except Exception as e:
        print(f"⚠️ 모델 접근 체크 실패: {e}")
        return False

v_model_name = "monologg/koelectra-base-finetuned-nsmc"
try:
    if hf_token:
        print("🔐 Hugging Face token detected in environment; checking repo access...")
        if not check_repo_access(v_model_name, token=hf_token):
            raise Exception(f"모델 {v_model_name} 접근 불가(토큰 권한 부족 또는 repo 없음).")
        # use `token=` (newer API) and fallback to `use_auth_token=` for compatibility
        try:
            v_tokenizer = AutoTokenizer.from_pretrained(v_model_name, token=hf_token)
            v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name, token=hf_token)
        except TypeError:
            v_tokenizer = AutoTokenizer.from_pretrained(v_model_name, use_auth_token=hf_token)
            v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name, use_auth_token=hf_token)
    else:
        v_tokenizer = AutoTokenizer.from_pretrained(v_model_name)
        v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name)
    v_is_fallback_multiclass = False
except Exception as e:
    import sys
    print(f"⚠️ 모델 로드 오류: {e}")
    print("해결책: 1) 이 모델이 private/gated이면 Hugging Face 토큰을 발급해서 .env에 `HUGGINGFACE_TOKEN=hf_xxx`로 설정하거나, CLI로 로그인하세요.")
    print("         2) CLI 로그인: `huggingface-cli login` (권한 있는 토큰으로 로그인)")
    print("         3) 또는 공개 모델로 폴백합니다: nlptown/bert-base-multilingual-uncased-sentiment")

    # 공개 폴백 모델 (다중 클래스: 1~5점)
    v_model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
    try:
        if hf_token:
            try:
                v_tokenizer = AutoTokenizer.from_pretrained(v_model_name, token=hf_token)
                v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name, token=hf_token)
            except TypeError:
                v_tokenizer = AutoTokenizer.from_pretrained(v_model_name, use_auth_token=hf_token)
                v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name, use_auth_token=hf_token)
        else:
            v_tokenizer = AutoTokenizer.from_pretrained(v_model_name)
            v_model = AutoModelForSequenceClassification.from_pretrained(v_model_name)
        v_is_fallback_multiclass = True
        print(f"폴백 모델 로드 성공: {v_model_name}")
    except Exception as e2:
        print("⚠️ 폴백 모델 로드 중 오류가 발생했습니다:", e2)
        print("가능한 원인: PyTorch/torchvision의 버전 불일치 또는 설치 문제.")
        print("해결: 아래 명령어로 PyTorch와 torchvision을 호환 버전으로 재설치하세요 (예시):")
        print("  pip uninstall torchvision && pip install --upgrade --force-reinstall torch torchvision")
        print("또는 환경 정보(파이썬, torch, torchvision 버전)를 제공해 주세요.")
        sys.exit(1)

print(f"Loaded model: {v_model_name}")

# ==========================================
# 2. 감성 분석 엔진 함수 (AI 뇌)
# ==========================================

def get_ai_sentiment_score(in_text):
    # 텍스트를 AI가 이해할 수 있는 숫자로 변환
    v_inputs = v_tokenizer(in_text, return_tensors="pt", truncation=True, max_length=128)
    
    with torch.no_grad():
        v_outputs = v_model(**v_inputs)
    
    # 확률값 계산 (Softmax)
    v_probs = F.softmax(v_outputs.logits, dim=-1)[0].cpu().numpy()

    # 이진 분류(neg,pos) 모델이면 index 1이 긍정 확률
    if (not v_is_fallback_multiclass) and (v_probs.shape[0] == 2):
        v_pos_prob = float(v_probs[1])
        # 0~1 -> -1~1
        v_final_score = round((v_pos_prob * 2) - 1, 3)
    else:
        # 다중 클래스(예: 1~N rating) 모델: 기대 평점(expected_rating)을 계산해 -1..1로 매핑
        classes = v_probs.shape[0]
        expected_rating = sum((i + 1) * float(p) for i, p in enumerate(v_probs))  # 1..N
        mid = (classes + 1) / 2.0
        denom = (classes - 1) / 2.0
        v_final_score = round((expected_rating - mid) / denom, 3)

    return v_final_score

# ==========================================
# 3. DB 업데이트 메인 로직
# ==========================================
def run_ai_db_enrichment():
    v_client = MongoClient(os.getenv("MONGO_DB_URL"))
    v_db = v_client['mock_trading_db']
    v_col = v_db['emo_db']
    
    # 1,127건 전체 또는 점수가 0이었던 데이터 대상 [cite: 2025-12-31]
    v_cursor = v_col.find({"status": "sentiment_completed"})
    
    v_total = v_col.count_documents({"status": "sentiment_completed"})
    v_count = 0

    print(f"🚀 AI 모델 가동: 총 {v_total}건의 데이터 고도화 시작...")

    for v_doc in v_cursor:
        v_id = v_doc["_id"]
        v_term = v_doc["term"]
        
        # AI 점수 계산 [cite: 2025-12-31]
        v_ai_score = get_ai_sentiment_score(v_term)
        
        # [업데이트] AI 점수 반영 및 상태 업데이트
        v_col.update_one(
            {"_id": v_id},
            {
                "$set": {
                    "analysis.sentiment_score": v_ai_score,
                    "status": "ai_analyzed", # AI 분석 완료 상태
                    "ai_updated_at": datetime.datetime.now()
                }
            }
        )
        
        v_count += 1
        if v_count % 10 == 0:
            print(f"📑 [{v_count}/{v_total}] '{v_term}' 분석 완료 -> 점수: {v_ai_score}")

    return v_count

if __name__ == "__main__":
    print("🧠 [게으른 달걀] Phase 3.5: AI 지능 주입 프로세스 실행")
    print("-" * 60)
    
    v_processed = run_ai_db_enrichment()
    
    print("-" * 60)
    print(f"✅ 총 {v_processed}건의 데이터가 AI 점수로 정밀 업데이트되었습니다.") 
    print("🏁 이제 '파도 파도 괴담'을 검색해서 점수가 어떻게 변했는지 확인해 보세요!")