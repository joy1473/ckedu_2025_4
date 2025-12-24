import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import asyncio
import random
import time
from agent.lua_core import LUAAgent
from utils.parser import parse_user_profile

# 1. 페이지 설정
st.set_page_config(page_title="Lazy User Agent", page_icon="🌙", layout="wide")

# --- 최상단 디자인 타이틀 ---
st.markdown("<h1 style='text-align: center; color: #FFD700;'>🌙 Lazy User Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #AAAAAA;'>피곤한 당신을 위한 가장 스마트한 금융 조력자</p>", unsafe_allow_html=True)
st.write("---")

# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step" not in st.session_state:
    st.session_state.step = "STEP_1"
if "user_info" not in st.session_state:
    st.session_state.user_info = {"name": None, "dob": None}
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = "^KS11" 

agent = LUAAgent()

# --- 상단: 3년 주봉 캔들 차트 & 아저씨의 코멘트 ---
chart_area = st.container()
with chart_area:
    ticker = st.session_state.current_ticker
    st.subheader(f"📈 {ticker} 시장 흐름 분석")
    
    try:
        df = yf.download(ticker, period="3y", interval="1wk")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        if not df.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                increasing_line_color='red', decreasing_line_color='blue'
            )])
            fig.update_layout(height=400, xaxis_rangeslider_visible=False, template="plotly_dark", margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            # [역할] 아저씨의 요약 (30년 베테랑 모드)
            st.markdown(f"""
            > **👴 여의도 베테랑 아저씨의 한마디:**
            > 허허, {ticker}의 주봉 흐름이 아주 묵직하구먼. 3년이라는 세월이 캔들 하나하나에 다 녹아있어. 
            > 피곤할 땐 이런 큰 흐름을 봐야 마음이 편안해지는 법이지. 
            > 지금 시장은 중요한 갈림길에 있으니 너무 조급해하지 말게나. 자, 루아랑 대화 이어가봐!
            """)
    except Exception as e:
        st.error(f"차트 로드 실패: {e}")

st.divider()

# --- 중단: 채팅 내역 출력 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 하단: STEP별 화면 출력 로직 (여기가 먹통 해결 핵심!) ---

# [STEP 1] 오프닝
if st.session_state.step == "STEP_1" and not st.session_state.messages:
    opening = "안녕하세요, LUA(루아)예요! 😊 원하시는 걸 대화로 편하게 도와드릴게요.\n\n시세 확인부터 시장 요약까지, 필요한 금융 정보를 바로 정리해드려요.\n\n이름과 생년월일(6자리)을 알려주시면 바로 안내해 드릴게요!"
    st.session_state.messages.append({"role": "assistant", "content": opening})
    st.rerun()

# [STEP 3] 메뉴 분기
elif st.session_state.step == "STEP_3":
    with st.chat_message("assistant"):
        st.write(f"✨ **{st.session_state.user_info['name']}**님, 무엇부터 도와드릴까요?")
        c1, c2, c3 = st.columns(3)
        if c1.button("🎮 모의투자"): st.session_state.step = "STEP_MOCK"; st.rerun()
        if c2.button("📝 실전 준비"): st.session_state.step = "STEP_PREP"; st.rerun()
        if c3.button("📊 시장 요약"): st.session_state.step = "STEP_10"; st.rerun()

# [STEP_PREP] 실전 준비 안내 화면 (새로 추가!)
elif st.session_state.step == "STEP_PREP":
    with st.chat_message("assistant"):
        st.write("📝 **실전 거래를 위한 준비 단계예요!**")
        st.info("실전 거래를 위해서는 키움증권 계좌 개설과 API 서비스 신청이 필요해요. 루아가 단계별 가이드를 메일로 보내드릴까요?")
        if st.button("메인 메뉴로 돌아가기"): st.session_state.step = "STEP_3"; st.rerun()

# [STEP_MOCK] 모의 투자 화면 (새로 추가!)
elif st.session_state.step == "STEP_MOCK":
    with st.chat_message("assistant"):
        st.write("🎮 **루아와 함께하는 신나는 모의투자!**")
        st.success("주인님께 가상 원금 1억 원을 지급해 드렸어요! 첫 번째로 매수하고 싶은 종목이 있나요?")
        if st.button("메인 메뉴로 돌아가기"): st.session_state.step = "STEP_3"; st.rerun()

# [STEP_10] 시장 요약 화면
elif st.session_state.step == "STEP_10":
    with st.chat_message("assistant"):
        st.write("📊 **오늘의 시장 브리핑을 준비했어요!**")
        st.info("KOSPI 지수는 현재 견조한 흐름을 유지하고 있어요. 피곤한 주인님을 대신해 루아가 주요 뉴스를 요약 중이에요!")
        if st.button("메인 메뉴로 돌아가기"): st.session_state.step = "STEP_3"; st.rerun()

# --- 공통 채팅 입력 처리 ---
if prompt := st.chat_input("LUA에게 메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        # 재치 있는 로딩 시스템 (Witty Loading)
        witty_phrases = [
            "루아가 차트 요정을 부르고 있어요! ✨",
            "아저씨가 돋보기를 닦고 계시네요... 🔍",
            "비밀 정보를 루아가 몰래 가져오는 중이에요! 🤫",
            "잠시만요! 루아가 주식 시장에 다녀올게요! 🏃‍♀️",
            "피곤한 주인님을 위해 루아가 열심히 분석 중이에요! 💪"
        ]
        
        status_area = st.status("LUA가 생각 중이에요...", expanded=True)
        for _ in range(3):
            status_area.write(f"🌙 {random.choice(witty_phrases)}")
            time.sleep(0.7)
        
        # 실제 로직 처리
        lower_prompt = prompt.lower()
        if any(w in lower_prompt for w in ["시장", "요약", "브리핑"]):
            st.session_state.step = "STEP_10"
        elif st.session_state.step == "STEP_1":
            name, dob = parse_user_profile(prompt)
            if name: st.session_state.user_info["name"] = name
            if dob: st.session_state.user_info["dob"] = dob
            if st.session_state.user_info["name"] and st.session_state.user_info["dob"]:
                st.session_state.step = "STEP_3"
            else:
                res = agent.get_lua_response(prompt, "STEP_1")
                st.session_state.messages.append({"role": "assistant", "content": res})
        else:
            res = agent.get_lua_response(prompt, st.session_state.step)
            st.session_state.messages.append({"role": "assistant", "content": res})
        
        status_area.update(label="분석 완료!", state="complete", expanded=False)
        
    st.rerun()