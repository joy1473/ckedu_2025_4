from pymongo import MongoClient
import datetime
c=MongoClient('mongodb://localhost:27017/')
col=c['game_db']['game_terms']
start=datetime.datetime(2025,12,31,0,0)
end=datetime.datetime(2026,1,1,0,0)
docs=list(col.find({"ai_updated_at":{'$gte':start,'$lt':end}}))
scores=[d.get('analysis',{}).get('sentiment_score') for d in docs if d.get('analysis',{}).get('sentiment_score') is not None]
print('처리 문서 수:', len(docs))
if scores:
    mn=min(scores)
    cnt=sum(1 for s in scores if abs(s-mn)<1e-6)
    print('min score=',mn,'count with min=',cnt)
    items=[d for d in docs if abs((d.get('analysis',{}).get('sentiment_score') or 0)-mn)<1e-6]
    print('샘플 (최저 점수):')
    for d in items[:30]:
        print('-', d.get('term'))
else:
    print('점수 없음')
