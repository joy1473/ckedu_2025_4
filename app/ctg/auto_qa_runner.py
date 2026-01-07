import os
import time
import json
import random
import requests
from openai import OpenAI
from dotenv import load_dotenv

# 1. 환경 설정
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
LUA_BACKEND_URL = "http://localhost:8000/lua/stock"

# 테스트할 종목 리스트 (공공데이터 API 조회용)
STOCK_SAMPLES = ["삼성전자", "SK하이닉스", "카카오", "NAVER", "에어부산", "현대차", "대한항공"]

# 페르소나 리스트
CASES = ["CASE_01", "CASE_02", "CASE_03", "CASE_04", "CASE_05"]

def generate_automated_qa():
    print("🤖 LUA 자율 QA 시뮬레이션을 시작합니다 (24시간 자동 모드)")
    
    while True:
        try:
            # 1단계: 무작위 페르소나 및 종목 선택
            selected_case = random.choice(CASES)
            selected_stock = random.choice(STOCK_SAMPLES)
            
            # 2단계: 질문 생성기 AI가 질문을 만듦
            question_prompt = f"""
            너는 주식 투자를 고민하는 유저야. 아래 조건으로 LUA에게 던질 질문을 딱 한 문장으로 만들어줘.
            - 페르소나: {selected_case}
            - 관심종목: {selected_stock}
            - 요구사항: 질문에 반드시 종목명이 포함되어야 함.
            """
            
            question_res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": question_prompt}]
            )
            user_question = question_res.choices[0].message.content.strip()
            print(f"\n👤 유저({selected_case}): {user_question}")

            # 3단계: 백엔드 서버(api_server.py) 호출하여 데이터 및 LUA 답변 생성
            # 기준 데이터 요청
            res = requests.get(LUA_BACKEND_URL, params={
                "itmsNm": selected_stock,
                "case_id": selected_case,
                "user_msg": user_question
            })
            
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    print(f"✨ LUA 응답 생성 및 학습 데이터 저장 완료: {selected_stock}")
                else:
                    print(f"⚠️ 데이터 조회 실패: {data.get('message')}")
            
            # 4단계: 서버 부하 방지를 위한 휴식 (10초~30초 랜덤)
            # 공공데이터 API의 초당 트랜잭션(30 TPS) 제한 준수
            wait_time = random.randint(10, 30)
            print(f"😴 {wait_time}초 대기 중...")
            time.sleep(wait_time)

        except Exception as e:
            print(f"❌ 시뮬레이션 중 오류 발생: {e}")
            time.sleep(60) # 오류 발생 시 1분 휴식

if __name__ == "__main__":
    # api_server.py가 먼저 실행 중이어야 합니다.
    generate_automated_qa()