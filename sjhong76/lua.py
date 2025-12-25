import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import random
import time
import re
from agent.lua_core import LUAAgent
from utils.parser import parse_user_profile

# 1. 페이지 설정
st.set_page_config(page_title="Lazy yoU Agent", page_icon="🌙", layout="wide")

# --- 최상단 디자인 타이틀 ---
st.markdown("<h1 style='text-align: center; color: #FFD700;'>🌙 Lazy yoU Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #AAAAAA;'>피곤한 당신을 위한 가장 스마트한 금융 조력자</p>", unsafe_allow_html=True)
st.write("---")

# 세션 상태 초기화
if "messages" not in st.session_state: st.session_state.messages = []
if "step" not in st.session_state: st.session_state.step = "STEP_1"
if "user_info" not in st.session_state: st.session_state.user_info = {"name": None, "dob": None}
if "current_ticker" not in st.session_state: st.session_state.current_ticker = "^KS11"
if "current_name" not in st.session_state: st.session_state.current_name = "코스피"
if "balance" not in st.session_state: st.session_state.balance = 100_000_000 
if "portfolio" not in st.session_state: st.session_state.portfolio = {} # {name: {'qty': x, 'avg_price': y}}

agent = LUAAgent()

# 종목명-티커 매핑
TICKER_MAP = {"삼성전자": "005930.KS", "하이닉스": "000660.KS", "카카오": "035720.KS", "네이버": "035420.KS", "코스피": "^KS11"}

# --- 상단: 3년 주봉 캔들 차트 및 수익률 배지 영역 ---
chart_area = st.container()
with chart_area:
    ticker = st.session_state.current_ticker
    display_name = st.session_state.current_name
    
    # 1. 차트 타이틀과 수익률 배지 배치
    col_title, col_badge = st.columns([3, 1])
    col_title.subheader(f"📈 {display_name} 시장 흐름 분석 (3년 주봉)")
    
    try:
        df = yf.download(ticker, period="3y", interval="1wk")
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        if not df.empty:
            current_price = df['Close'].iloc[-1]
            
            # 수익률 배지 로직 (보유 중일 때만 표시)
            if display_name in st.session_state.portfolio:
                stock_info = st.session_state.portfolio[display_name]
                avg_price = stock_info['avg_price']
                qty = stock_info['qty']
                roi = ((current_price - avg_price) / avg_price) * 100
                profit = (current_price - avg_price) * qty
                
                color = "red" if roi >= 0 else "blue"
                col_badge.metric(f"{display_name} 수익률", f"{roi:.2f}%", f"{profit:,.0f} 원", delta_color="normal")

            # 캔들스틱 차트 출력
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='red', decreasing_line_color='blue')])
            fig.update_layout(height=400, xaxis_rangeslider_visible=False, template="plotly_dark", margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"> **👴 여의도 베테랑 아저씨:** 허허, {display_name} 흐름을 보게나. 주봉이 살아있으니 피곤해도 내일은 밝을 거야. 이 줄기는 꼭 잡아야 해.")
    except Exception as e: st.error(f"차트 로드 실패: {e}")

st.divider()

# --- 중단: 채팅 이력 출력 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

# --- 하단: STEP별 화면 렌더링 ---

# [STEP 1] 오프닝 (기존 멘트 100% 유지)
if st.session_state.step == "STEP_1" and not st.session_state.messages:
    opening = (
        "안녕하세요, LUA(루아)예요! 😊 원하시는 걸 대화로 편하게 도와드릴게요.\n\n"
        "시세 확인부터 시장 요약까지, 필요한 금융 정보를 바로 정리해드려요.\n\n"
        "이름과 생년월일(6자리)을 알려주시면 바로 필요하신 내용을 안내해드릴게요!"
    )
    st.session_state.messages.append({"role": "assistant", "content": opening}); st.rerun()

# [STEP 3] 메뉴 분기
elif st.session_state.step == "STEP_3":
    with st.chat_message("assistant"):
        st.write(f"✨ **{st.session_state.user_info['name']}**님, 무엇부터 도와드릴까요?")
        c1, c2, c3 = st.columns(3)
        if c1.button("🎮 모의투자 시작"):
            st.session_state.messages.append({"role": "assistant", "content": "🎮 **모의투자**를 시작할게요! 가상 원금 1억 원을 입금 완료했어요!"})
            st.session_state.step = "STEP_MOCK"; st.rerun()
        if c2.button("📝 실전 준비 안내"):
            st.session_state.messages.append({"role": "assistant", "content": "📝 **실전 거래 가이드** 화면으로 이동합니다."})
            st.session_state.step = "STEP_PREP"; st.rerun()
        if c3.button("📊 시장 요약"):
            st.session_state.messages.append({"role": "assistant", "content": "📊 **오늘의 시장 브리핑**을 요약해 드릴게요!"})
            st.session_state.step = "STEP_10"; st.rerun()

# [STEP_PREP] 실전 준비 (메일 제안 멘트 및 화면 100% 유지)
elif st.session_state.step == "STEP_PREP":
    with st.chat_message("assistant"):
        st.write("📝 **실전 거래를 위한 준비 단계예요!**")
        st.info("실전 거래를 위해서는 키움증권 계좌 개설과 API 서비스 신청이 필요해요. 루아가 단계별 가이드를 메일로 보내드릴까요?")
        email = st.text_input("가이드를 받을 이메일 주소를 입력해 주세요:")
        if st.button("가이드 발송 요청"):
            if "@" in email: st.success(f"✅ 확인했어요! {email}로 실전 거래 가이드를 보내드릴게요. 조금만 기다려주세요!")
            else: st.error("올바른 이메일 형식을 입력해 주세요.")
        if st.button("처음으로 돌아가기"): st.session_state.step = "STEP_3"; st.rerun()

# [STEP_MOCK] 모의투자 현황
elif st.session_state.step == "STEP_MOCK":
    with st.chat_message("assistant"):
        st.subheader("💰 내 모의투자 현황")
        col_bal, col_port = st.columns(2)
        col_bal.metric("가상 잔고", f"{st.session_state.balance:,} 원")
        if st.session_state.portfolio:
            for stock, info in st.session_state.portfolio.items():
                st.write(f"- {stock}: {info['qty']}주 (평균단가: {info['avg_price']:,}원)")
        else: st.write("보유 종목이 아직 없어요. 🛒")
        st.info("💡 '삼성전자 10주 사줘'라고 말씀해 보세요! 상단에 수익률 배지가 나타납니다.")
        if st.button("처음으로 돌아가기"): st.session_state.step = "STEP_3"; st.rerun()

# [STEP 10] 시장 브리핑
elif st.session_state.step == "STEP_10":
    with st.chat_message("assistant"):
        insight, news = agent.get_market_briefing()
        st.success(f"👴 **베테랑의 시황 데스크**\n\n{insight}")
        st.write("✨ **LUA의 3줄 뉴스**")
        for n in news: st.markdown(f"> {n}")
        if st.button("처음으로 돌아가기"): st.session_state.step = "STEP_3"; st.rerun()

# --- 채팅 입력 및 매수 로직 처리 ---
if prompt := st.chat_input("LUA에게 궁금한 걸 물어보세요! 🌙"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        with st.status("LUA가 분석 중이에요...", expanded=True) as s:
            # 1. 매수 의도 파싱 (예: 삼성전자 10주 사줘)
            buy_match = re.search(r'([가-힣]+)\s*(\d+)\s*주\s*(사줘|매수)', prompt)
            
            if buy_match and st.session_state.step == "STEP_MOCK":
                stock_name = buy_match.group(1); quantity = int(buy_match.group(2))
                ticker = TICKER_MAP.get(stock_name, "005930.KS")
                st.session_state.current_ticker = ticker
                st.session_state.current_name = stock_name
                
                stock_info_data = yf.Ticker(ticker)
                current_price = stock_info_data.history(period="1d")['Close'].iloc[-1]
                total_cost = int(current_price * quantity)
                
                if st.session_state.balance >= total_cost:
                    st.session_state.balance -= total_cost
                    
                    # 평균 단가 및 보유량 업데이트
                    old_info = st.session_state.portfolio.get(stock_name, {'qty': 0, 'avg_price': 0})
                    new_qty = old_info['qty'] + quantity
                    new_avg = ((old_info['avg_price'] * old_info['qty']) + (current_price * quantity)) / new_qty
                    st.session_state.portfolio[stock_name] = {'qty': new_qty, 'avg_price': int(new_avg)}
                    
                    res = f"✅ **매수 성공!** {stock_name} {quantity}주를 {total_cost:,}원에 구매했어요. 이제 차트 옆에서 실시간 수익률을 확인할 수 있어요! ✨"
                else: res = f"❌ **잔고 부족!** {total_cost:,}원이 필요하지만 잔고가 부족해요. 😢"
                st.session_state.messages.append({"role": "assistant", "content": res})
            else:
                # 2. 일반 대화 및 로딩 멘트
                phrases = ["차트 요정이 분석 중이에요! ✨", "아저씨가 돋보기를 닦고 계세요 🔍", "루아가 시장에 다녀오는 중! 🏃‍♀️"]
                st.write(f"🌙 {random.choice(phrases)}")
                if st.session_state.step == "STEP_1":
                    name, dob = parse_user_profile(prompt)
                    if name: st.session_state.user_info["name"] = name; st.session_state.user_info["dob"] = dob
                    if st.session_state.user_info["name"] and st.session_state.user_info["dob"]: st.session_state.step = "STEP_3"
                    else: st.session_state.messages.append({"role": "assistant", "content": agent.get_lua_response(prompt, "STEP_1")})
                else: st.session_state.messages.append({"role": "assistant", "content": agent.get_lua_response(prompt, st.session_state.step)})
            s.update(label="분석 완료!", state="complete")
    st.rerun()