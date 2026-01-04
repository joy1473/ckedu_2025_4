"""Reprocess already-analyzed documents using current AI model.
This script updates documents whose status is in ["ai_analyzed","sentiment_completed"].
It uses get_ai_sentiment_score from step3_5_ai_db_update.py.
"""
from pymongo import MongoClient
import datetime
import step3_5_ai_db_update as s

v_client = MongoClient('mongodb://localhost:27017/')
v_db = v_client['game_db']
v_col = v_db['game_terms']

query = {"status": {"$in": ["ai_analyzed", "sentiment_completed"]}}
total = v_col.count_documents(query)
print(f"대상 문서 수: {total}")

if total == 0:
    print("재처리할 문서가 없습니다.")
else:
    processed = 0
    for doc in v_col.find(query):
        try:
            _id = doc["_id"]
            term = doc.get("term", "")
            score = s.get_ai_sentiment_score(term)
            v_col.update_one({"_id": _id}, {"$set": {"analysis.sentiment_score": score, "ai_updated_at": datetime.datetime.now()}})
            processed += 1
            if processed % 10 == 0 or processed == total:
                print(f"📑 [{processed}/{total}] '{term}' 재분석 완료 -> 점수: {score}")
        except Exception as e:
            print(f"문서 {_id} 처리 중 오류: {e}")
    print(f"완료: 총 {processed}/{total} 건 재처리 완료")
