import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def run_auto_train():
    while True:
        # 1. 수집된 로그 파일 크기 확인 (예: 50개 이상의 로그가 쌓이면 학습)
        if os.path.exists("learning_data.jsonl"):
            with open("learning_data.jsonl", "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if len(lines) >= 50:
                print(f"🚀 {len(lines)}개의 데이터 감지. 자동 학습을 시작합니다.")
                
                # 2. OpenAI에 학습 파일 업로드
                file_upload = client.files.create(
                    file=open("learning_data.jsonl", "rb"),
                    purpose="fine-tune"
                )
                
                # 3. 파인튜닝 작업 생성
                client.fine_tuning.jobs.create(
                    training_file=file_upload.id,
                    model="gpt-4o-mini-2024-07-18"
                )
                
                # 4. 로그 파일 초기화 (백업 후 삭제)
                os.rename("learning_data.jsonl", f"backup_train_{int(time.time())}.jsonl")
                print("✅ 학습 요청 완료 및 로그 초기화.")
        
        # 24시간 간격으로 체크 (86400초)
        time.sleep(86400)

if __name__ == "__main__":
    run_auto_train()