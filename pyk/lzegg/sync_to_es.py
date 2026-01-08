import os
import certifi
from pymongo import MongoClient
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
from pathlib import Path

# 환경 변수 로드
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 1. DB 연결 설정
mongo_client = MongoClient(os.getenv("MONGO_URL"), tlsCAFile=certifi.where())
db = mongo_client['mock_trading_db']

# [수정] 헤더 호환성 설정 추가
es = Elasticsearch(
    [os.getenv("ES_URL", "http://172.26.117.88:9200")],
    headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=7"}
)

def sync_data():
    actions = []
    print("📋 1. stock_master 데이터 동기화 시작...")
    
    # stock_master 동기화 로직
    master_cursor = db['stock_master'].find()
    stocks_for_summary = {}

    for stock in master_cursor:
        code = stock['code']
        close_price = stock.get('close', 0)
        name = stock.get('name', '알수없음')
        stocks_for_summary[code] = close_price

        actions.append({
            "_index": "stock_master",
            "_id": code,
            "_source": {
                "code": code,
                "name": name,
                "close": close_price,
                "market": stock.get('market', ''),
                "updated_at": stock.get('updated_at', '')
            }
        })
        if len(actions) >= 500:
            helpers.bulk(es, actions)
            actions = []
    
    if actions:
        helpers.bulk(es, actions)
        actions = []
    print(f"✅ stock_master 동기화 완료!")

    # trade_summary 동기화 로직
    print("📦 2. trade_summary 데이터 동기화 시작...")
    summary_cursor = db.trade_summary_esc.find()
    
    for doc in summary_cursor:
        code = doc['code']
        current_price = stocks_for_summary.get(code, 0)
        
        actions.append({
            "_index": "trade_summary",
            "_id": f"{doc['user_id']}_{code}",
            "_source": {
                "user_id": doc['user_id'],
                "code": code,
                "total_buy_qty": doc.get('total_buy_qty', 0),
                "total_buy_amt": doc.get('total_buy_amt', 0),
                "total_sell_qty": doc.get('total_sell_qty', 0),
                "total_sell_amt": doc.get('total_sell_amt', 0),
                "current_price": current_price
            }
        })
        if len(actions) >= 500:
            helpers.bulk(es, actions)
            actions = []

    if actions:
        helpers.bulk(es, actions)
    
    print("✅ 모든 데이터 동기화가 완료되었습니다!")

if __name__ == "__main__":
    try:
        # 간단한 연결 체크
        if es.ping():
            sync_data()
        else:
            print("❌ Elasticsearch 연결 실패: 서버 상태를 확인하세요.")
    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")