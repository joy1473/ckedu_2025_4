import json
import collections
import random
import os

# 1. 설정
input_file = 'pure_train_data.jsonl'
output_file = 'pure_train_data_500.jsonl'
target_total = 500

if not os.path.exists(input_file):
    print(f"❌ '{input_file}' 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
    exit()

data_by_persona = collections.defaultdict(list)

# 2. 데이터 분석 및 페르소나별 분류
print("🔍 1,721개 데이터를 분석하여 최정예 500개를 선별 중입니다...")
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            item = json.loads(line)
            persona = "Unknown"
            # 시스템 메시지에서 페르소나 이름 추출
            for msg in item["messages"]:
                if msg["role"] == "system" and "페르소나:" in msg["content"]:
                    persona = msg["content"].split("페르소나:")[1].strip().split("\n")[0]
                    break
            
            # 답변 길이를 기준으로 저장 (길수록 상세하고 양질의 데이터로 간주)
            assistant_content = next(m["content"] for m in item["messages"] if m["role"] == "assistant")
            data_by_persona[persona].append((len(assistant_content), item))
        except:
            continue

# 3. 비율에 맞춰 선별
total_available = sum(len(v) for v in data_by_persona.values())
selected_items = []

for persona, items in data_by_persona.items():
    # 원본의 페르소나 비율 유지
    ratio = len(items) / total_available
    persona_target = int(target_total * ratio)
    
    # 답변이 상세한 순서대로 정렬하여 상위권 선점
    items.sort(key=lambda x: x[0], reverse=True)
    selected_items.extend([x[1] for x in items[:persona_target]])

# 부족한 개수 채우기 (반올림 오차 대비)
if len(selected_items) < target_total:
    all_remaining = []
    for persona, items in data_by_persona.items():
        ratio = len(items) / total_available
        persona_target = int(target_total * ratio)
        all_remaining.extend(items[persona_target:])
    all_remaining.sort(key=lambda x: x[0], reverse=True)
    selected_items.extend([x[1] for x in all_remaining[:target_total - len(selected_items)]])

# 4. 결과 저장
random.shuffle(selected_items) # 학습 효과를 위해 순서 섞기
with open(output_file, 'w', encoding='utf-8') as f:
    for item in selected_items:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"✅ 작업 완료!")
print(f"📊 원본 데이터: {total_available}개")
print(f"🎯 압축 데이터: {len(selected_items)}개 (상세 답변 위주 선별)")
print(f"💾 생성된 파일명: {output_file}")