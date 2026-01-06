import os
import certifi
from pymongo import MongoClient
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
from pathlib import Path
###last 2026-01-06
# 환경 변수 로드
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / '.env')

# 1. DB 연결 설정
# MongoDB
mongo_client = MongoClient(os.getenv("MONGO_URL"), tlsCAFile=certifi.where())
db = mongo_client['mock_trading_db']

# Elasticsearch (비밀번호가 없는 현재 상태 기준)
# es = Elasticsearch([os.getenv("ES_URL", "http://localhost:9200")])
es = Elasticsearch([os.getenv("ES_URL", "http://172.26.117.88:9200")])

def sync_data():
    print("🔍 1. 종목 마스터에서 현재가(close) 정보를 가져오는 중...")
    # 종목 코드를 키로, 현재가를 값으로 하는 딕셔너리 생성
    stocks = {s['code']: s.get('close', 0) for s in db['stock_master'].find({}, {"code": 1, "close": 1})}
    
    print(f"📦 2. MongoDB에서 데이터를 읽어 ES로 전송 중... (대상: {len(stocks)}개 종목 참고)")
    
    actions = []
    # summary 테이블의 데이터를 하나씩 읽음
    cursor = db.trade_summary_esc.find()
    
    count = 0
    for doc in cursor:
        code = doc['code']
        current_price = stocks.get(code, 0)
        
        # ES에 저장할 문서 구조 (역정규화: 모든 정보를 한곳에!)
        action = {
            "_index": "trade_summary",
            "_id": f"{doc['user_id']}_{code}", # 유저ID와 종목코드로 유니크 키 설정
            "_source": {
                "user_id": doc['user_id'],
                "code": code,
                "total_buy_qty": doc.get('total_buy_qty', 0),
                "total_buy_amt": doc.get('total_buy_amt', 0),
                "total_sell_qty": doc.get('total_sell_qty', 0),
                "total_sell_amt": doc.get('total_sell_amt', 0),
                "current_price": current_price
            }
        }
        actions.append(action)
        
        # 1000건씩 묶어서 대량 전송 (Bulk)
        if len(actions) >= 1000:
            helpers.bulk(es, actions)
            actions = []
            print(f"   > {count + 1000}건 완료...")
            count += 1000

    # 남은 데이터 전송
    if actions:
        helpers.bulk(es, actions)
    
    print("✅ 모든 데이터 동기화가 완료되었습니다!")

if __name__ == "__main__":
    if es.ping():
        sync_data()
    else:
        print("❌ Elasticsearch에 연결할 수 없습니다. URL을 확인하세요.")