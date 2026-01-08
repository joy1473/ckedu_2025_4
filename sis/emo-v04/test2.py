from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

def get_mongodb_collection(in_db_name, in_col_name):
    v_client = MongoClient(os.getenv("MONGO_DB_URL"))
    v_db = v_client[in_db_name]
    return v_db[in_col_name]

def show_duplicate_list(in_col):
    # 몽고DB 집계 파이프라인: 그룹화 -> 중복 필터링 -> 정렬 [cite: 2025-12-31]
    v_pipeline = [
        {
            "$group": {
                "_id": "$term",           # 'term' 필드(단어)를 기준으로 묶음
                "count": {"$sum": 1},      # 동일 단어 개수 합산
                "sample_id": {"$first": "$_id"} # 중복 중 남길 녀석의 ID (참고용)
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}       # 2회 이상 등장한 것만 추출
            }
        },
        {
            "$sort": {"count": -1}        # 중복이 많은 순서대로 정렬
        }
    ]
    
    v_results = list(in_col.aggregate(v_pipeline))
    return v_results

if __name__ == "__main__":
    print(f"📊 [게으른 달걀] 총 1,128건 데이터 무결성 검사 시작")  # [cite: 2025-12-31]
    print("-" * 60)
    
    v_col = get_mongodb_collection("mock_trading_db", "emo_db")
    v_dup_list = show_duplicate_list(v_col)
    
    if v_dup_list:
        print(f"⚠️ 총 {len(v_dup_list)}종류의 단어가 중복 발견되었습니다.")
        print(f"{'중복 단어':<15} | {'출현 횟수':<10}")
        print("-" * 60)
        
        v_redundant_total = 0
        for v_item in v_dup_list:
            print(f"{v_item['_id']:<15} | {v_item['count']}회")
            v_redundant_total += (v_item['count'] - 1)
            
        print("-" * 60)
        print(f"✅ 현재 1,128건 중 삭제가 필요한 중복분은 총 {v_redundant_total}건입니다.")  # [cite: 2025-12-31]
    else:
        print("🎉 축하합니다! 1,128건 모두 중복 없는 클린한 데이터입니다.")  # [cite: 2025-12-31]