from pymongo import MongoClient
import json
from bson import json_util

# ==========================================
# 1. DB 연결 설정
# ==========================================
def get_mongodb_collection(in_db_name, in_col_name):
    v_client = MongoClient('mongodb://localhost:27017/')
    v_db = v_client[in_db_name]
    return v_db[in_col_name]

# ==========================================
# 2. 특정 단어 검색 엔진
# ==========================================
def find_term_info(in_col, in_target_term):
    # 정확히 일치하는 단어를 찾습니다.
    v_doc = in_col.find_one({"term": in_target_term})
    
    if v_doc:
        print(f"🔍 '{in_target_term}' 검색 결과입니다.")
        print("-" * 50)
        # 데이터를 보기 좋게 정렬해서 출력합니다.
        print(json.dumps(v_doc, indent=2, ensure_ascii=False, default=json_util.default))
        print("-" * 50)
    else:
        print(f"❌ '{in_target_term}' 단어를 DB에서 찾을 수 없습니다.")
        # 혹시 띄어쓰기 문제일 수 있으니 유사 검색도 함께 실행합니다.
        v_similar = list(in_col.find({"term": {"$regex": in_target_term.replace(" ", "")}}))
        if v_similar:
            print(f"💡 띄어쓰기가 다른 유사한 단어를 {len(v_similar)}건 발견했습니다.")

if __name__ == "__main__":
    v_target = "파도 파도 괴담"
    
    # DB 및 컬렉션 지정
    v_col = get_mongodb_collection("game_db", "game_terms")
    
    find_term_info(v_col, v_target)