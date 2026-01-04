import datetime
from pymongo import MongoClient
from konlpy.tag import Okt

# ==========================================
# 1. DB 연결 설정
# ==========================================
def get_mongodb_collection(in_db_name, in_col_name):
    v_client = MongoClient('mongodb://localhost:27017/')
    v_db = v_client[in_db_name]
    return v_db[in_col_name]

# ==========================================
# 2. 형태소 분석 및 구조 업데이트 엔진
# ==========================================
def set_slang_morph_update(in_col):
    v_okt = Okt()
    # 아직 분석되지 않은(status: raw) 1,127건을 타겟팅합니다. [cite: 2025-12-31]
    v_cursor = in_col.find({"status": "raw"})
    
    v_count = 0
    print("🔍 KoNLPy(Okt) 엔진 가동: 형태소 분석 시작...")

    for v_doc in v_cursor:
        v_id = v_doc["_id"]
        v_term = v_doc["term"]
        
        # [분석] 형태소와 품사를 추출합니다.
        v_pos_tags = v_okt.pos(v_term)
        
        v_morphemes = []
        for v_word, v_pos in v_pos_tags:
            v_morphemes.append({
                "word": v_word,
                "pos": v_pos
            })
            
        # [업데이트] 실전형 구조(analysis 필드) 주입 [cite: 2025-12-31]
        in_col.update_one(
            {"_id": v_id},
            {
                "$set": {
                    "status": "analyzed",
                    "analysis": {
                        "morphemes": v_morphemes,
                        "sentiment_score": 0.0, # Phase 3 대기
                        "embedding_vector": []  # Phase 4 대기
                    },
                    "updated_at": datetime.datetime.now()
                }
            }
        )
        v_count += 1
        if v_count % 100 == 0:
            print(f"📑 {v_count}건 분석 완료...")

    return v_count

if __name__ == "__main__":
    print("🚀 [게으른 달걀] 신조어 데이터 고도화 시작")
    print("-" * 50)
    
    v_col = get_mongodb_collection("game_db", "game_terms")
    v_processed = set_slang_morph_update(v_col)
    
    print("-" * 50)
    print(f"✅ 총 {v_processed}건의 데이터가 '실전형 구조'로 업그레이드되었습니다.")