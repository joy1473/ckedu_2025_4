import os
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
TARGET_MODEL = os.getenv('OPENAI_MODEL')

def diagnose_access():
    print(f"--- 🩺 LUA 모델 접근 권한 진단 ---")
    print(f"🔑 API Key 일부: {os.getenv('OPENAI_API_KEY')[:10]}...")
    
    try:
        # 현재 키로 접근 가능한 모델 목록 가져오기
        models = client.models.list()
        ft_models = [m.id for m in models.data if "ft:" in m.id]
        
        print(f"✅ 접근 가능한 커스텀 모델 목록:")
        if not ft_models:
            print("   -> ❌ 현재 키로 접근 가능한 학습 모델이 하나도 없습니다!")
        else:
            for mid in ft_models:
                status = "🎯 일치" if mid == TARGET_MODEL else "   -"
                print(f"   {status} {mid}")
        
        if TARGET_MODEL not in ft_models:
            print(f"\n💡 해결책: OpenAI 대시보드에서 프로젝트 설정을 확인하고,")
            print(f"   학습된 모델이 있는 '정확한 프로젝트'의 API Key를 사용하세요.")
            
    except Exception as e:
        print(f"❌ API 통신 중 에러 발생: {e}")

if __name__ == "__main__":
    diagnose_access()