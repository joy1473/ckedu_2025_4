import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import datetime
import time

# 설명 : MongoDB 컬렉션 객체를 반환합니다.
def get_mongodb_collection(in_db_name, in_col_name):
    v_client = MongoClient('mongodb://localhost:27017/')
    v_db = v_client[in_db_name]
    return v_db[in_col_name]

# 설명 : 보안이 낮고 데이터가 확실한 '신조어 저장소'에서 데이터를 긁어옵니다.
def get_safe_slang_data(in_page_num):
    # 타겟: 신조어와 유행어가 잘 정리된 공개 리스트 (예시: 특정 전문 사전 페이지)
    # 404 방지를 위해 현재 살아있는 주식/게임 용어 요약 페이지를 타겟팅합니다.
    v_url = f"https://ko.wiktionary.org/wiki/부록:한국어_신조어_및_유행어_목록"
    v_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    out_data = []
    
    try:
        v_response = requests.get(v_url, headers=v_headers, timeout=10)
        print(f"📡 데이터 수집 중... (상태: {v_response.status_code})")
        
        if v_response.status_code == 200:
            v_soup = BeautifulSoup(v_response.text, 'html.parser')
            # 위키낱말사전의 리스트 구조 파싱 (li 태그 내부의 b 태그 등)
            v_items = v_soup.select('ul > li b a') 
            if not v_items:
                v_items = v_soup.select('ul > li > b') # 구조 대비 2안

            for v_item in v_items:
                v_term = v_item.get_text().strip()
                if v_term and len(v_term) > 1:
                    out_data.append({"term": v_term})
    except Exception as e:
        print(f"🔴 오류: {e}")
        
    return out_data

if __name__ == "__main__":
    print("🚀 [게으른 달걀] 신조어 전수 수집 엔진 가동 (안전 모드)")
    v_col = get_mongodb_collection("game_db", "game_terms")
    
    # 1단계: 공개된 대량 리스트 수집
    v_raw_list = get_safe_slang_data(1)
    
    if v_raw_list:
        v_saved = 0
        for v_item in v_raw_list:
            v_doc = {
                "term": v_item['term'],
                "status": "raw",
                "category": "trend",
                "created_at": datetime.datetime.now()
            }
            # 중복 체크 후 저장
            if not v_col.find_one({"term": v_item['term']}):
                v_col.insert_one(v_doc)
                v_saved += 1
        
        print(f"✅ 수집 완료: 총 {len(v_raw_list)}개 발견 / {v_saved}개 신규 저장")
    else:
        print("🔴 데이터를 가져오지 못했습니다. 주소를 다시 점검합니다.")

    print(f"\n🏁 현재 DB 총 데이터 건수: {v_col.count_documents({})}")