from pymongo import MongoClient
from cmm.config import MONGO_URI
from datetime import datetime
import pprint  # 예쁘게 출력용

# MongoDB 연결
client = MongoClient(MONGO_URI)

# 연결 테스트
try:
    client.admin.command('ping')
    print("🎉 MongoDB Atlas 연결 성공!")
except Exception as e:
    print("❌ 연결 실패:", e)
    exit()

# 데이터베이스와 컬렉션 선택
db = client["choeuna"]          # DB 이름 ALias _ 
collection = db["test"]         # 컬렉션 이름 (없으면 자동 생성)

print("\n--- 데이터 삽입 시작 ---")

# 삽입할 샘플 모의 트레이딩 데이터
sample_trades = [
    {
        "user_id": "user001",
        "stock": "AAPL",
        "action": "buy",
        "quantity": 10,
        "price": 175.50,
        "timestamp": datetime.now(),
        "tags": ["tech", "long_term"]
    },
    {
        "user_id": "user001",
        "stock": "TSLA",
        "action": "sell",
        "quantity": 5,
        "price": 240.30,
        "timestamp": datetime.now(),
        "tags": ["ev", "short_term"]
    },
    {
        "user_id": "user002",
        "stock": "005930.KS",  # 삼성전자
        "action": "buy",
        "quantity": 20,
        "price": 75000,
        "timestamp": datetime.now(),
        "tags": ["korea", "semiconductor"]
    }
]

# 데이터 삽입
result = collection.insert_many(sample_trades)
print(f"✅ {len(result.inserted_ids)}개의 데이터 삽입 완료!")

print("\n--- 데이터 읽기 (전체 조회) ---")
for trade in collection.find():
    pprint.pprint(trade)

print("\n--- 조건으로 조회 (AAPL만) ---")
aapl_trades = collection.find({"stock": "AAPL"})
for trade in aapl_trades:
    pprint.pprint(trade)

print("\n--- 특정 사용자 거래 내역 (user001) ---")
user_trades = collection.find({"user_id": "user001"}).sort("timestamp", -1)  # 최신순
for trade in user_trades:
    pprint.pprint(trade)

print("\n--- 데이터 개수 ---")
print(f"총 거래 수: {collection.count_documents({})}")

print("\n🎄 모든 작업 완료! Merry Christmas!")