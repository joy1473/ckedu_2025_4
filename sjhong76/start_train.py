import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# [✅ 중요: 순수 학습용 파일만 지정]
TRAIN_FILE = "pure_train_data_500.jsonl"

def upload_and_train():
    if not os.path.exists(TRAIN_FILE):
        print(f"❌ '{TRAIN_FILE}' 파일이 없습니다. 데이터를 먼저 쌓아주세요.")
        return

    with open(TRAIN_FILE, "r", encoding="utf-8") as f:
        data_count = len(f.readlines())
    
    print(f"📊 학습용 순수 데이터 개수: {data_count}개")

    if data_count < 10:
        print("⚠️ 데이터가 최소 10개 이상 필요합니다.")
        return

    try:
        print("🚀 OpenAI 서버로 순수 데이터 전송 중...")
        file_info = client.files.create(
            file=open(TRAIN_FILE, "rb"),
            purpose="fine-tune"
        )
        
        job = client.fine_tuning.jobs.create(
            training_file=file_info.id,
            model="gpt-4o-mini-2024-07-18"
        )
        print(f"🎉 학습 시작 성공! Job ID: {job.id}")
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    upload_and_train()