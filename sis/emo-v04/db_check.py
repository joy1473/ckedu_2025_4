from pymongo import MongoClient
from bson.json_util import dumps

import os
from dotenv import load_dotenv
load_dotenv()
c = MongoClient(os.getenv("MONGO_DB_URL"))
col = c['mock_trading_db']['emo_db']

print("전체 문서 수:", col.count_documents({}))
print("status='sentiment_completed':", col.count_documents({"status":"sentiment_completed"}))
print("status='ai_analyzed':", col.count_documents({"status":"ai_analyzed"}))

print('\n상태별 분포:')
for s in col.aggregate([{"$group":{"_id":"$status","count":{"$sum":1}}}]):
    print(f"  {s['_id']}: {s['count']}")

print('\n최근 ai_updated_at 기준 샘플 5건:')
for d in col.find({"ai_updated_at":{"$exists": True}}).sort("ai_updated_at", -1).limit(5):
    out = {
        "_id": str(d.get("_id")),
        "term": d.get("term"),
        "sentiment_score": d.get("analysis", {}).get("sentiment_score"),
        "status": d.get("status"),
        "ai_updated_at": str(d.get("ai_updated_at"))
    }
    print(dumps(out, indent=2))

print('\n샘플: status="sentiment_completed" 문서 5건 (있으면):')
for d in col.find({"status":"sentiment_completed"}).limit(5):
    out = {"_id": str(d.get("_id")), "term": d.get("term"), "status": d.get("status")}
    print(dumps(out, indent=2))
