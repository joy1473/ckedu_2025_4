import os
from openai import OpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 주인님이 새로 발급받으신 Job ID입니다.
JOB_ID = "ftjob-ll9IOXPWZ1jcbKmteGEB3ZjO"

def check_lua_growth_status():
    try:
        # OpenAI 서버에 학습 작업 상태 요청
        job = client.fine_tuning.jobs.retrieve(JOB_ID)
        
        print(f"------------------------------------------")
        print(f"📊 LUA 지능 학습 상태: {job.status}")
        
        if job.status == "validating_files":
            print("⏳ 파일 규격을 검사하고 있습니다. (이번엔 통과할 거예요!)")
        elif job.status == "queued":
            print("⏳ 대기열에 등록되었습니다. 곧 학습을 시작합니다.")
        elif job.status == "running":
            print("🏃 현재 데이터를 분석하며 학습 중입니다! (거의 다 왔어요)")
        elif job.status == "succeeded":
            print("🎉 학습 완료! 새로운 모델이 성공적으로 탄생했습니다.")
            print(f"🆔 새로운 모델 ID: {job.fine_tuned_model}")
            print(f"💡 위 ID를 .env 파일의 OPENAI_MODEL 항목에 붙여넣으세요.")
        elif job.status == "failed":
            print(f"❌ 학습 실패: {job.error.message}")
            print("💡 에러 메시지를 복사해서 저에게 알려주세요.")
        
        # 학습 진행 상황 (진행률이 있는 경우)
        if job.trained_tokens:
            print(f"📝 학습된 데이터 규모: {job.trained_tokens} 토큰")
            
        print(f"------------------------------------------")
        
    except Exception as e:
        print(f"❌ 상태 확인 중 오류 발생: {e}")

if __name__ == "__main__":
    check_lua_growth_status()