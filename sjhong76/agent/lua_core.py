import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LUAAgent:
    def __init__(self):
        # API 키 로드 (환경변수 또는 Streamlit Secrets)
        api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            st.error("🔑 OpenAI API 키가 설정되지 않았습니다!")
            st.stop()
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def get_lua_response(self, user_message, current_step):
        """귀여운 LUA의 페르소나 응답"""
        system_prompt = f"""
        당신은 '피곤한 주인님'을 돕는 친절한 AI 조력자 'LUA'입니다. 
        항상 다정하고 귀여운 말투(~예요, ~해요)를 사용하세요. 
        매수 성공 시 "주인님! 포트폴리오에 예쁘게 담았어요! ✨ 상단 차트에서 확인해 보세요!"라고 말해주세요.
        현재 단계: {current_step}
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
        )
        return response.choices[0].message.content

    def get_market_briefing(self):
        """아저씨의 시황 분석 데스크"""
        insight = (
            "허허, 오늘 삼성전자에 수급이 몰리는 걸 보니 개미들이 바빠지겠구먼. "
            "주봉상 20선 지지가 확인되었으니 당분간은 하방 경직성이 확보된 셈이야. "
            "피곤할 땐 이런 큰 줄기만 보고 푹 쉬는 게 최고지. 안 그래?"
        )
        news = [
            "✅ 반도체 수출 실적 역대 최고치 경신! 우리 반도체주들 힘내고 있어요! 🚀",
            "✅ 미 연준 금리 동결 가능성 상승! 시장이 한숨 돌리는 분위기예요. ☕",
            "✅ K-푸드 열풍에 식품주 신고가 행진! 주인님 맛있는 거 드셔야겠어요! 🍜"
        ]
        return insight, news