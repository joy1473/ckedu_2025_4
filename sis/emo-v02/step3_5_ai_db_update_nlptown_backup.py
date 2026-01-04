# Backup of step3_5_ai_db_update.py (state when using nlptown fallback)
# Created automatically before attempting monologg/kcelectra access.
# You can restore this file if needed.

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

v_model_name = "monologg/kcelectra-base-finetuned-nsmc"
try:
    if hf_token:
        print("🔐 Hugging Face token detected in environment; using authenticated download (masking token).")
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
    v_inputs = v_tokenizer(in_text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        v_outputs = v_model(**v_inputs)
    v_probs = torch.nn.functional.softmax(v_outputs.logits, dim=-1)[0].cpu().numpy()

    if (not v_is_fallback_multiclass) and (v_probs.shape[0] == 2):
        v_pos_prob = float(v_probs[1])
        v_final_score = round((v_pos_prob * 2) - 1, 3)
    else:
        classes = v_probs.shape[0]
        expected_rating = sum((i + 1) * float(p) for i, p in enumerate(v_probs))
        mid = (classes + 1) / 2.0
        denom = (classes - 1) / 2.0
        v_final_score = round((expected_rating - mid) / denom, 3)

    return v_final_score

# (Rest of the original file continues...)