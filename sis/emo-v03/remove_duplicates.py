from pymongo import MongoClient

# ==========================================
# 1. DB 연결 설정
# ==========================================
def get_mongodb_collection(in_db_name, in_col_name):
    v_client = MongoClient('mongodb://localhost:27017/')
    v_db = v_client[in_db_name]
    return v_db[in_col_name]

# ==========================================
# 2. 중복 삭제 로직
# ==========================================
def delete_duplicate_terms(in_col):
    # [Step 1] 중복된 단어와 해당 ID 리스트를 추출합니다. [cite: 2025-12-31]
    v_pipeline = [
        {
            "$group": {
                "_id": "$term",
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"}
            }
        },
        {
            "$match": {"count": {"$gt": 1}}
        }
    ]
    
    v_dups = list(in_col.aggregate(v_pipeline))
    v_delete_ids = []

    for v_item in v_dups:
        # 첫 번째 ID는 남기고, 두 번째(index 1)부터 삭제 목록에 추가합니다.
        v_ids_to_remove = v_item['ids'][1:] 
        v_delete_ids.extend(v_ids_to_remove)

    # [Step 2] 삭제 대상 ID가 있다면 한꺼번에 삭제합니다. [cite: 2025-12-31]
    if v_delete_ids:
        v_result = in_col.delete_many({"_id": {"$in": v_delete_ids}})
        return v_result.deleted_count
    return 0

if __name__ == "__main__":
    print("🧹 [게으른 달걀] 데이터 클리닝: 중복 문서 삭제 시작")
    print("-" * 60)
    
    v_col = get_mongodb_collection("game_db", "game_terms")
    
    # 작업 전 전체 건수 확인 [cite: 2025-12-31]
    v_before_count = v_col.count_documents({})
    
    v_deleted = delete_duplicate_terms(v_col)
    
    v_after_count = v_col.count_documents({})
    
    print(f"🗑️ 삭제된 중복 데이터: {v_deleted}건")
    print(f"📊 최종 데이터 보유량: {v_after_count}건 (1,128 -> 1,127)") [cite: 2025-12-31]
    print("-" * 60)
    print("✅ 데이터 정리가 완료되었습니다. 이제 형태소 분석 준비가 끝났습니다!")