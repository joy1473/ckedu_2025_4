from pymongo import MongoClient
import datetime
import csv
import statistics
import os
from bson.json_util import dumps

# Environment
today = datetime.datetime.now().date()
start = datetime.datetime.combine(today, datetime.time.min)
end = start + datetime.timedelta(days=1)

client = MongoClient('mongodb://localhost:27017/')
col = client['game_db']['game_terms']

query = {"ai_updated_at": {"$gte": start, "$lt": end}}
docs = list(col.find(query))
count = len(docs)

scores = [d.get('analysis', {}).get('sentiment_score') for d in docs if d.get('analysis', {}).get('sentiment_score') is not None]

summary_lines = []
summary_lines.append(f"# AI 재처리 요약 ({today})\n")
summary_lines.append(f"- 실행 시간 범위: {start} ~ {end}")
summary_lines.append(f"- 처리 문서 수: {count}")
summary_lines.append(f"- 모델: monologg/koelectra-base-finetuned-nsmc")

if scores:
    s_min = min(scores)
    s_max = max(scores)
    s_mean = statistics.mean(scores)
    s_median = statistics.median(scores)
    s_stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0
    summary_lines.append(f"- 점수 통계: min={s_min:.3f}, max={s_max:.3f}, mean={s_mean:.3f}, median={s_median:.3f}, stdev={s_stdev:.3f}")

    # top/bottom samples
    top = sorted(docs, key=lambda d: d.get('analysis', {}).get('sentiment_score', 0), reverse=True)[:10]
    bottom = sorted(docs, key=lambda d: d.get('analysis', {}).get('sentiment_score', 0))[:10]

    summary_lines.append('\n## 상위(긍정) 10개')
    for d in top:
        ts = d.get('analysis', {}).get('sentiment_score')
        summary_lines.append(f"- {d.get('term')} -> {ts}")

    summary_lines.append('\n## 하위(부정) 10개')
    for d in bottom:
        ts = d.get('analysis', {}).get('sentiment_score')
        summary_lines.append(f"- {d.get('term')} -> {ts}")
else:
    summary_lines.append('\n(금일 업데이트된 문서가 없습니다.)')

# Write markdown summary
fname_md = f"reprocess_summary_{today}.md"
with open(fname_md, 'w', encoding='utf-8') as f:
    f.write('\n'.join(summary_lines))

# Write CSV details
fname_csv = f"reprocess_details_{today}.csv"
with open(fname_csv, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['_id', 'term', 'sentiment_score', 'status', 'ai_updated_at'])
    for d in docs:
        writer.writerow([str(d.get('_id')), d.get('term'), d.get('analysis', {}).get('sentiment_score'), d.get('status'), d.get('ai_updated_at')])

print(f"생성 완료: {fname_md}, {fname_csv}")
print('요약 내용:\n')
print('\n'.join(summary_lines[:20]))
