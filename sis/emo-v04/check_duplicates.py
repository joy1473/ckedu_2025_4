from pymongo import MongoClient

# ==========================================
# 1. DB 연결 설정
# ==========================================
def get_mongodb_collection(in_db_name, in_col_name):
    v_client = MongoClient('mongodb://localhost:27017/')
    v_db = v_client[in_db_name]
    return v_db[in_col_name]

# ==========================================
# 2. 중복 리스트 추출 함수 (Aggregation 활용)
# ==========================================
def get_duplicate_report(in_col):
    # 몽고DB 파이프라인 설계: 그룹화 -> 카운트 -> 1보다 큰 것 필터링 [cite: 2025-12-31]
    v_pipeline = [
        {
            "$group": {
                "_id": "$term",           # 'term' 필드를 기준으로 그룹화
                "count": {"$sum": 1},      # 각 그룹의 문서 개수를 합산
                "ids": {"$push": "$_id"}   # (참고용) 해당 단어들의 고유 ID 보관
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}       # 카운트가 1보다 큰(중복된) 데이터만 매칭
            }
        },
        {
            "$sort": {"count": -1}        # 중복이 많이 된 순서대로 정렬
        }
    ]
    
    v_duplicates = list(in_col.aggregate(v_pipeline))
    return v_duplicates

# ==========================================
# 메인 실행 엔진
# ==========================================
if __name__ == "__main__":
    print("🔍 [게으른 달걀] 데이터 무결성 체크: 중복 리스트 분석 시작")
    print("-" * 60)
    
    v_col = get_mongodb_collection("game_db", "game_terms")
    v_dup_list = get_duplicate_report(v_col)
    
    if v_dup_list:
        print(f"⚠️ 총 {len(v_dup_list)} 종류의 중복 단어가 발견되었습니다.")
        print(f"{'중복 단어':<15} | {'중복 횟수':<10}")
        print("-" * 60)
        
        v_total_redundant = 0
        for v_item in v_dup_list:
            print(f"{v_item['_id']:<15} | {v_item['count']}회")
            v_total_redundant += (v_item['count'] - 1)
        
        print("-" * 60)
        print(f"💡 팁: 현재 DB에서 제거해야 할 총 중복 문서는 {v_total_redundant}건입니다.")
    else:
        print("✅ 축하합니다! 중복된 단어가 하나도 없습니다.")
    
    print("-" * 60)