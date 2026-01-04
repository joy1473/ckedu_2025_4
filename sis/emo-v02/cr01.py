import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import datetime
import time

# ==========================================
# 1. DB 연결 함수 (Get)
# ==========================================
# 설명 : 로컬 MongoDB에 접속하여 지정된 컬렉션 객체를 반환합니다.
# 입력 : in_db_name (DB명), in_col_name (컬렉션명)
# 출력 : out_collection (컬렉션 객체)
# 소스 : 로컬 MongoDB (game_db)
def get_mongodb_collection(in_db_name, in_col_name):
    v_client = MongoClient('mongodb://localhost:27017/')
    v_db = v_client[in_db_name]
    out_collection = v_db[in_col_name]
    return out_collection

# ==========================================
# 2. 페이징 지원 수집 함수 (Get)
# ==========================================
# 설명 : 나무위키의 복잡한 페이징 버튼을 정밀 추적하여 단어와 다음 페이지 URL을 추출합니다.
# 입력 : in_url (현재 수집할 URL)
# 출력 : out_data (단어 리스트), out_next_url (다음 페이지 주소)
# 소스 : 나무위키(namu.wiki) - 게임 용어 분류
# 설명 : 나무위키 분류 페이지에서 단어와 다음 페이지를 '전수 조사' 방식으로 추출합니다.
def get_web_slang_with_paging(in_url):
    v_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://namu.wiki/",
    }
    out_data = []
    out_next_url = None
    
    try:
        v_session = requests.Session()
        v_response = v_session.get(in_url, headers=v_headers, timeout=20)
        
        # [디버깅] 실제 수신된 HTML의 길이를 확인합니다.
        print(f"📡 접속 상태: {v_response.status_code} (HTML 길이: {len(v_response.text)})")
        
        v_soup = BeautifulSoup(v_response.text, 'html.parser')
        
        # 모든 a 태그를 가져와서 분석합니다.
        v_all_links = v_soup.find_all('a')
        
        for v_link in v_all_links:
            v_text = v_link.get_text().strip()
            v_href = v_link.get('href', '')
            
            # 1. 단어 추출 로직: 링크 주소에 '/w/'가 포함되어 있고 '분류:'가 없는 것
            if "/w/" in v_href and "분류:" not in v_href and "특수:" not in v_href:
                # 너무 짧거나 의미 없는 텍스트는 제외
                if len(v_text) > 1 and v_text not in ["다음 페이지", "이전 페이지"]:
                    out_data.append({
                        "term": v_text,
                        "link": "https://namu.wiki" + v_href
                    })
            
            # 2. 다음 페이지 추출 로직: 텍스트에 '다음 페이지'가 포함된 경우
            if "다음 페이지" in v_text and not out_next_url:
                out_next_url = "https://namu.wiki" + v_href
                
    except Exception as e:
        print(f"🔴 오류 발생: {e}")
        
    return out_data, out_next_url

# ==========================================
# 3. 데이터 저장 함수 (Set)
# ==========================================
# 설명 : 수집된 데이터를 중복 없이 DB에 저장합니다.
# 입력 : in_col (컬렉션), in_data_list (데이터 리스트)
# 출력 : out_count (신규 저장 개수)
# 소스 : MongoDB (game_terms)
def set_slang_to_db(in_col, in_data_list):
    v_success_count = 0
    for v_item in in_data_list:
        v_doc = {
            "term": v_item['term'],
            "source_link": v_item['link'],
            "status": "raw", 
            "created_at": datetime.datetime.now()
        }
        if not in_col.find_one({"term": v_item['term']}):
            in_col.insert_one(v_doc)
            v_success_count += 1
    return v_success_count

# ==========================================
# 메인 실행 엔진
# ==========================================
if __name__ == "__main__":
    print("🚀 [게으른 달걀] 663개 전수 수집 엔진 가동")
    print("-" * 50)

    # DB 컬렉션 확보 (이 부분이 호출되기 전에 함수가 정의되어 있어야 합니다)
    v_col = get_mongodb_collection("game_db", "game_terms")
    
    v_current_url = "https://namu.wiki/w/분류:게임%20용어"
    v_total_new_saved = 0
    v_page_num = 1

    while v_current_url:
        print(f"\n📄 {v_page_num}페이지 수집 시도 중...")
        v_page_data, v_next_page = get_web_slang_with_paging(v_current_url)
        
        if v_page_data:
            v_saved = set_slang_to_db(v_col, v_page_data)
            v_total_new_saved += v_saved
            print(f"✅ {len(v_page_data)}개 추출 성공 / {v_saved}개 신규 저장")
        
        v_current_url = v_next_page
        v_page_num += 1
        
        if v_current_url:
            print(f"⏳ 다음 페이지 발견! 3초 후 이동합니다...")
            time.sleep(3)

    print("-" * 50)
    print(f"🏁 전수 수집 종료! 이번 회차 신규 저장: {v_total_new_saved}건")