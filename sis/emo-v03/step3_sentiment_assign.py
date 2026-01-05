import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

# ==========================================
# 1. DB 연결 설정
# ==========================================
def get_mongodb_collection(in_db_name, in_col_name):
    # 로컬 MongoDB에 접속하여 컬렉션 객체를 반환합니다.
    v_client = MongoClient(os.getenv("MONGO_DB_URL"))
    v_db = v_client[in_db_name]
    return v_db[in_col_name]

# ==========================================
# 2. 고도화된 감성 사전 (Sentiment Dictionary)
# ==========================================
# 웹마스터님의 피드백을 반영하여 게임/주식 관련 키워드를 보강했습니다. [cite: 2025-12-31]
v_pos_keywords = [
    '수익', '상승', '떡상', '이익', '호재', '상한가', '매수', '성공', '급등', 
    '우상향', '갓겜', '꿀잼', '대박', '승리', '존버성공', '풀매수'
]

v_neg_keywords = [
    '손실', '하락', '떡락', '손절', '악재', '하한가', '매도', '실패', '급락', 
    '억까', '나락', '괴담', '파파괴', '혐오', '최악', '망겜', '노잼', '패배',
    '지옥', '거품', '폭락', '삭제', '민폐'
]

# ==========================================
# 3. 감성 점수 부여 엔진 (Main Logic)
# ==========================================
def run_sentiment_assignment(in_col):
    # 분석은 완료되었으나 아직 점수가 0인 데이터들을 다시 순회합니다. [cite: 2025-12-31]
    v_cursor = in_col.find({"status": "analyzed"})
    
    # 이미 'sentiment_completed'인 데이터도 사전을 보강했으니 다시 돌리고 싶다면
    # 아래 주석을 풀고 실행하세요. (전체 재계산 모드)
    # v_cursor = in_col.find({"status": {"$in": ["analyzed", "sentiment_completed"]}})

    v_count = 0
    print("📊 [게으른 달걀] 감성 분석 엔진 가동 시작 (사전 보강 완료)...")

    for v_doc in v_cursor:
        v_id = v_doc["_id"]
        v_term = v_doc["term"]
        v_morphemes = v_doc.get("analysis", {}).get("morphemes", [])
        
        v_score = 0.0
        
        # 형태소 리스트를 돌며 사전과 매칭합니다.
        for v_item in v_morphemes:
            v_word = v_item["word"]
            
            if v_word in v_pos_keywords:
                v_score += 1.0  # 긍정 단어 발견 시 +1
            elif v_word in v_neg_keywords:
                v_score -= 1.0  # 부정 단어 발견 시 -1
        
        # [업데이트] 계산된 점수를 반영하고 최종 상태로 변경합니다. [cite: 2025-12-31]
        in_col.update_one(
            {"_id": v_id},
            {
                "$set": {
                    "analysis.sentiment_score": v_score,
                    "status": "sentiment_completed", 
                    "analyzed_at": datetime.datetime.now()
                }
            }
        )
        v_count += 1
        if v_count % 100 == 0:
            print(f"📑 {v_count}건 감성 분석 처리 중...")

    return v_count

# ==========================================
# 메인 실행 엔진
# ==========================================
if __name__ == "__main__":
    print("🚀 Phase 3: 데이터 가치 고도화 실행")
    print("-" * 50)
    
    # DB 및 컬렉션 지정
    v_col = get_mongodb_collection("mock_trading_db", "emo_db")
    
    v_result = run_sentiment_assignment(v_col)
    
    print("-" * 50)
    print(f"✅ 총 {v_result}건의 데이터에 감성 점수가 새롭게 부여되었습니다.")
    print("🏁 [파도 파도 괴담]과 같은 단어들의 점수가 바뀌었는지 확인해 보세요!")