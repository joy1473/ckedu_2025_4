import requests
from bs4 import BeautifulSoup
from konlpy.tag import Okt
from pymongo import MongoClient
import datetime
import sys

# ==========================================
# 1. DB 연결 함수
# ==========================================
# 설명 : MongoDB에 접속하여 지정된 컬렉션(Table) 객체를 반환합니다.
# 입력 : in_db_name (데이터베이스명), in_col_name (컬렉션명)
# 출력 : out_collection (MongoDB 컬렉션 객체)
# 소스 : 로컬 MongoDB (game_db)
def get_mongodb_collection(in_db_name, in_col_name):
    try:
        v_client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        v_db = v_client[in_db_name]
        out_collection = v_db[in_col_name]
        # 연결 테스트
        v_client.server_info() 
        return out_collection
    except Exception as e:
        print(f"🔴 DB 연결 실패: {e}")
        sys.exit()

# ==========================================
# 2. 웹 데이터 수집 함수
# ==========================================
# 설명 : 특정 웹 페이지에서 게임 용어와 설명 리스트를 추출합니다.
# 입력 : in_url (수집 대상 URL)
# 출력 : out_raw_list (단어와 설명이 담긴 딕셔너리 리스트)
# 소스 : BeautifulSoup4 (Web Scraper)
def get_web_term_list(in_url):
    # 실제 운영 시에는 해당 사이트의 HTML 구조에 맞게 Selector 수정이 필요합니다.
    # 아래는 구조 이해를 위한 샘플 데이터 생성 로직입니다.
    print(f"🌐 '{in_url}'에서 데이터 수집 중...")
    
    # 실습을 위한 가상 데이터 (실제 크롤링 시 requests.get 사용)
    out_raw_list = [
        {"term": "개추", "desc": "개념글 추천의 줄임말로 강한 찬성을 의미"},
        {"term": "지린다", "desc": "매우 놀랍거나 대단한 상황을 표현"},
        {"term": "하드캐리", "desc": "혼자서 팀 전체를 승리로 이끄는 활약"},
        {"term": "중꺾마", "desc": "중요한 것은 꺾이지 않는 마음의 줄임말"}
    ]
    return out_raw_list

# ==========================================
# 3. 형태소 분석 함수
# ==========================================
# 설명 : 신조어를 분석하여 품사 태그와 어근을 추출합니다.
# 입력 : in_text (분석할 단어)
# 출력 : out_analysis (분석 결과 딕셔너리)
# 소스 : KoNLPy (Okt 분석기)
def get_morpheme_analysis(in_text):
    v_okt = Okt()
    
    v_pos = v_okt.pos(in_text) # 품사 태깅
    v_stems = v_okt.morphs(in_text, stem=True) # 어근 추출
    
    out_analysis = {
        "pos_tags": v_pos,
        "stems": v_stems
    }
    return out_analysis

# ==========================================
# 4. 개별 데이터 저장 함수
# ==========================================
# 설명 : 분석된 단일 신조어 데이터를 MongoDB에 저장합니다.
# 입력 : in_col (컬렉션), in_term (단어), in_desc (설명), in_analysis (분석데이터)
# 출력 : out_id (저장된 문서의 고유 ID)
# 소스 : game_terms (Collection)
def set_game_term_data(in_col, in_term, in_desc, in_analysis):
    v_doc = {
        "term": in_term,
        "definition": in_desc,
        "analysis": in_analysis,
        "sentiment_score": 0.0, # 향후 KcELECTRA 연동을 위한 예비 필드
        "created_at": datetime.datetime.now()
    }
    
    v_result = in_col.insert_one(v_doc)
    out_id = v_result.inserted_id
    return out_id

# ==========================================
# 5. 대량 데이터 일괄 처리 함수
# ==========================================
# 설명 : 리스트 데이터를 순회하며 분석 및 저장을 일괄 수행합니다.
# 입력 : in_col (컬렉션), in_raw_list (원천 데이터 리스트)
# 출력 : out_count (성공 개수)
# 소스 : Data Pipeline Controller
def set_bulk_game_terms(in_col, in_raw_list):
    v_success_count = 0
    
    for v_item in in_raw_list:
        # 1. 분석 (Get)
        v_analysis = get_morpheme_analysis(v_item['term'])
        
        # 2. 저장 (Set)
        v_id = set_game_term_data(in_col, v_item['term'], v_item['desc'], v_analysis)
        
        if v_id:
            v_success_count += 1
            print(f"📦 [{v_success_count}] '{v_item['term']}' 처리 및 저장 완료")
            
    out_count = v_success_count
    return out_count

# ==========================================
# 메인 실행 엔진
# ==========================================
if __name__ == "__main__":
    print("🚀 Genesis AI: 게임 신조어 수집 파이프라인 시작")
    print("-" * 50)

    # [STEP 1] DB 연결
    v_col = get_mongodb_collection("game_db", "game_terms")

    # [STEP 2] 웹 데이터 수집 (크롤링)
    v_target_url = "https://namu.wiki/w/분류:게임%20용어"
    v_raw_data = get_web_term_list(v_target_url)

    # [STEP 3] 대량 분석 및 저장
    v_total_saved = set_bulk_game_terms(v_col, v_raw_data)

    print("-" * 50)
    print(f"✨ 작업 종료: 총 {v_total_saved}개의 데이터가 DB에 반영되었습니다.")