from pymongo import MongoClient
from cmm.config import MONGO_URI, es
from elasticsearch import helpers
import os
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# MongoDB 연결
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.mock_trading_db

# .env 로드
load_dotenv()

# 컬렉션 → 인덱스 마이그레이션 함수
def migrate_collection(collection_name, index_name):
    collection = db[collection_name]
    actions = []
    for doc in collection.find():
        # _id는 문자열로 변환 (ES ID 제한)
        doc_id = str(doc.pop('_id')) if '_id' in doc else None
        action = {
            '_index': index_name,
            '_id': doc_id,
            '_source': doc
        }
        actions.append(action)
    
    if actions:
        helpers.bulk(es, actions)
        print(f"✅ {collection_name} → {index_name}로 {len(actions)}개 문서 마이그레이션 완료")

# 실행: 테이블(컬렉션) 매핑
migrate_collection('trade_esc_history', 'trade_esc_history')
migrate_collection('trade_summary_esc', 'trade_summary')  # 이름 맞춤
migrate_collection('stock_master', 'stock_master')

# 옵션: 인덱스 매핑 사전 설정 (성능 최적화, 실제 필드에 맞게)
# es.indices.create(index='trade_esc_history', body={'mappings': {'properties': {'timestamp': {'type': 'date'}, 'profit': {'type': 'float'}}}})