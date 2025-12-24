# sjhong76/agent/lua_core.py
import os
from openai import OpenAI

class LUAAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    def get_lua_response(self, user_message, current_step):
        """귀여운 LUA가 대화를 이끌며 단계를 전환합니다."""
        system_prompt = f"""
        당신은 1030 초보 투자자를 위한 귀엽고 친절한 AI 조력자 'LUA'입니다.
        주인님과 친구처럼 다정하게 대화하세요. (~예요, ~해요 등 귀여운 말투 사용)
        
        [현재 단계: {current_step}]
        1. 주인님의 질문에 친절하게 답해주세요.
        2. 만약 주인님이 '매수', '잔고 확인' 등 특정 액션을 원하면, 
           "네! 그럼 바로 {current_step}에서 다음 단계로 안내해 드릴게요!"라고 밝게 답하세요.
        3. 절대 30년 베테랑 아저씨처럼 딱딱하거나 훈계하는 말투를 쓰지 마세요.
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content

    def get_veteran_chart_comment(self, ticker, trend_data):
        """차트 요약 전용: 30년 베테랑 아저씨의 날카로운 분석"""
        # 이 부분에서만 아저씨 말투를 사용합니다.
        return f"허허, {ticker}의 흐름을 보니... 이 {trend_data}은 무시 못 하지. 수급이 꼬이지 않게 조심해야 해."