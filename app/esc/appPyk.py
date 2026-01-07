import os
import json
import uuid
from pathlib import Path
from fastapi import FastAPI, Request, Form, Query
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from dotenv import load_dotenv
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
from fastapi.staticfiles import StaticFiles
import pandas as pd
from fastapi.responses import HTMLResponse
import numpy as np
from fastapi import HTTPException
from fastapi.responses import FileResponse
from elasticsearch import Elasticsearch
from fastapi import Response
from pymongo import MongoClient
from cmm.config import MONGO_URI

# MongoDB 연결
MONGO_CLIENT_ESC = MongoClient(MONGO_URI)
DB_COMM = MONGO_CLIENT_ESC.mock_trading_db
DB_ESC = MONGO_CLIENT_ESC.ykpark

# 엘라스틱서치 연결 설정
# es = Elasticsearch(["http://127.0.0.1:9200"], verify_certs=False)
# es = Elasticsearch(
#     ["http://localhost:9200"],
#     # 버전 호환성 에러(version 9 관련) 해결을 위한 헤더 추가
#     headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=7"},
#     verify_certs=False
# )

# es = Elasticsearch(
#     ["http://127.0.0.1:9200"],
#     headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=7"},
#     verify_certs=False
# )

es = Elasticsearch(
    [os.getenv("OPENSEARCH_URL")],
    http_auth=(os.getenv("OPENSEARCH_USER"), os.getenv("OPENSEARCH_PASS")),
    headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=7"},
    verify_certs=True
)
# .env 설정
BASE_DIR_ESC = Path(__file__).resolve().parent.parent.parent
ENV_PATH_ESC = BASE_DIR_ESC / '.env'
load_dotenv(dotenv_path=ENV_PATH_ESC)

# 객체 생성
AI_CLIENT_ESC = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
USERS_COMM = users_collection
USERS_ESC = users_esc_collection
print(f"\n✅ MONGO_CLIENT_ESC: 연결성공")

APP_ESC = FastAPI()

# 경로 설정
CURRENT_DIR_ESC = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(CURRENT_DIR_ESC, "templates")
STATIC_PATH = os.path.join(CURRENT_DIR_ESC, "static")

# 만약 static 폴더가 없으면 에러가 나지 않게 자동으로 생성
if not os.path.exists(STATIC_PATH):
    os.makedirs(STATIC_PATH)

# mount 코드
APP_ESC.mount("/staticEsc", StaticFiles(directory=STATIC_PATH), name="static")
TEMPLATES_ESC = Jinja2Templates(directory=TEMPLATE_PATH)

def get_stock_info_esc(in_ticker):
    """
    # 설명 : get_stock_info_esc - 모의투자-주식최근시세 가져오기
    # 입력 : in_ticker - 주식종목코드
    # 출력 : out_price-주식종목최근시세 (없을 경우 None)
    # 소스 : 금융데이터 라이브러리 yfinance
    """
    try:
        if in_ticker.isdigit(): in_ticker = f"{in_ticker}.KS"
        stock = yf.Ticker(in_ticker)
        data = stock.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return None
        
    except Exception as e:
        print(f"시세 조회 실패 ({in_ticker}): {e}")
        return None

def get_user_status(in_userId):
    """
    # 설명 : get_user_status - 모의투자-유저 상태 확인 및 초기화
    # 입력 : in_userId - 사용자id
    # 출력 : user - json 정보
    # 소스 : 몽고DB mock_trading_db.users
    """
    # 1. 나의 전용 DB에서 유저 조회
    user = USERS_ESC.find_one({"user_id": in_userId})

    # 2. 내 DB에 유저가 없는 경우 (최초 방문)
    if not user:
        # 공용 DB에서 원본 유저 정보 확인
        comm_user = USERS_COMM.find_one({"user_id": in_userId})
        
        # [에러 처리] 사용자가 DB에 아예 없는 경우
        if not comm_user:
            raise HTTPException(
                status_code=404, 
                detail=f"해당 사용자({in_userId})를 찾을 수 없습니다. 서비스 가입이 필요합니다."
            )
        
        # [기초자산 결정] 공용 DB에 있으면 그 값을, 없으면 기본값 10,000,000원 사용
        initial_cash = comm_user.get("cash_esc", 10000000)

        # [필드 추가] cash_esc ( 모의투자 기초 자산 ) 정보만 체크해서 없으면 업데이트
        if "cash_esc" not in comm_user:
            USERS_COMM.update_one(
                {"user_id": in_userId}, 
                {"$set": {"cash_esc": initial_cash}} # 초기 자산 설정
            )
            print(f"✅ 공용 DB에 기초자산({initial_cash:,.0f}원) 갱신 완료")

        # 업데이트 후 최신 객체 다시 가져오기
        comm_user = USERS_COMM.find_one({"user_id": in_userId})

        # 모의투자 사용자 계정 생성
        new_user_data = {
            "user_id": in_userId,
            "cash_esc": initial_cash,  # 내 DB 전용 잔액 필드명
            "portfolio": {},
            "history": [],             # 거래 내역을 담을 리스트 추가
            "created_at": datetime.now()
        }
        USERS_ESC.insert_one(new_user_data)
        user = new_user_data
        print(f"✅ {in_userId}님의 기초자산을 내 DB로 복사 완료")
    return user

def set_buy_stock(in_userId, in_ticker, in_quantity):
    """
    # 설명 : set_buy_stock - 모의투자-주식 매수
    # 입력 : in_userId-사용자id, in_ticker-종목코드, in_quantity-수량
    # 출력 : out_val-처리결과 메시지
    # 소스 : 몽고DB ykpark.users_esc
    """
    ticker = in_ticker
    if ticker.isdigit(): ticker = f"{ticker}.KS"

    # 1. 시세 및 유저 정보 
    info = get_stock_info_with_name(ticker)
    price = info['price']
    stock_name = info['name']

    if not price or price == 0:
        # get_stock_info_esc로 재시도 (백업)
        price = get_stock_info_esc(ticker)
        if not price: return "시세 정보를 가져올 수 없습니다."
    
    total_cost = price * in_quantity
    user = get_user_status(in_userId)
    if user.get('cash_esc', 0) < total_cost: 
        return f"잔액이 부족합니다. (필요: {total_cost:,.0f}원 / 잔액: {user.get('cash_esc', 0):,.0f}원)"
    
    # 3. 포트폴리오 데이터 준비
    db_ticker = ticker.replace(".", "_")
    portfolio = user.get("portfolio", {})
    stock_data = portfolio.get(db_ticker, {"qty": 0, "avg_price": 0})
    
    new_qty = stock_data['qty'] + in_quantity
    new_avg = round(((stock_data['avg_price'] * stock_data['qty']) + (price * in_quantity)) / new_qty, 2)

    # 4. ESC DB 업데이트 (잔액 차감 및 포트폴리오 갱신)
    USERS_ESC.update_one(
        {"user_id": in_userId},
        {
            "$inc": {"cash_esc": -total_cost}, 
            "$set": {f"portfolio.{db_ticker}": {"qty": new_qty, "avg_price": round(new_avg)}}
        }
    )
    # 5. 거래 이력 저장 (필요 시 주석 해제)
    set_saveHistory(in_userId, "매수", ticker, in_quantity, price, f"{ticker} 매수 완료")
    out_val = f"✅ <b>{stock_name}</b>({ticker}) {in_quantity}주 매수 완료!\n- 매수가: {price:,.0f}원\n- 총 소요: {total_cost:,.0f}원"
    return out_val

def set_sell_stock(in_userId, in_ticker, in_quantity):
    """
    # 설명 : set_sell_stock - 모의투자-주식 매도
    # 입력 : in_userId-사용자id, in_ticker-종목코드, in_quantity-수량
    # 출력 : out_val-처리결과 메시지
    # 소스 : 몽고DB ykpark.users_esc
    """
    ticker = in_ticker
    if ticker.isdigit(): ticker = f"{ticker}.KS"

    # 1. 시세 조회 및 유저 정보 가져오기
    info = get_stock_info_with_name(ticker)
    price = get_stock_info_esc(ticker)
    stock_name = info['name']

    if not price or price == 0:
        # get_stock_info_esc로 재시도 (백업)
        price = get_stock_info_esc(ticker)
        if not price: return "시세 정보를 가져올 수 없습니다."

    user = get_user_status(in_userId)

    db_ticker = ticker.replace(".", "_")
    stock_data = user.get("portfolio", {}).get(db_ticker)
    
    # 2. 보유 수량 체크
    if not stock_data or stock_data['qty'] < in_quantity: 
        return f"보유 수량이 부족합니다. (보유: {stock_data['qty'] if stock_data else 0}주)"

    total_receive = price * in_quantity
    new_qty = stock_data['qty'] - in_quantity

    if new_qty > 0:
        # 수량이 남은 경우: 잔액 증가($inc) 및 수량 업데이트($set)
        USERS_ESC.update_one(
            {"user_id": in_userId}, 
            {
                "$inc": {"cash_esc": total_receive}, 
                "$set": {f"portfolio.{db_ticker}.qty": new_qty}
            }
        )
    else:
        # 전량 매도인 경우: 잔액 증가($inc) 및 해당 종목 삭제($unset)
        USERS_ESC.update_one(
            {"user_id": in_userId}, 
            {
                "$inc": {"cash_esc": total_receive}, 
                "$unset": {f"portfolio.{db_ticker}": ""}
            }
        )

    # 4. 이력 저장
    set_saveHistory(in_userId, "매도", ticker, in_quantity, price, f"{ticker} 매도 완료")
    out_val = f"✅ <b>{stock_name}</b>({ticker}) {in_quantity}주 매도 완료! (+{total_receive:,.0f}원)"
    return out_val

def set_saveHistory(in_userId, in_type, in_ticker=None, in_quantity=0, in_price=0, in_result_msg=""):
    """
    # 설명 : 모의투자-이력 저장 (MongoDB 저장)
    # 입력 : in_userId-사용자id, in_type(매수/매도/채팅), in_ticker-종목코드, in_quantity-수량, in_price-가격, in_result_msg-챗봇결과 메시지
    # 출력 : None
    # 소스 : 몽고DB ykpark.users_esc
    """
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": "TRADE" if in_ticker else "CHAT", 
        "type": in_type,
        "ticker": in_ticker,
        "quantity": in_quantity,
        "price": in_price,
        "message": in_result_msg
    }

    try:
        USERS_ESC.update_one(
            {"user_id": in_userId},
            {"$push": {"history": entry}}
        )
    except Exception as e:
        print(f"❌ 이력 DB 저장 실패: {e}")

def get_stock_chart_html(in_ticker):
    """
    # 설명 : 모의투자-주식차트 표시 (Plotly 활용)
    # 입력 : in_ticker-종목코드
    # 출력 : out_val-차트 HTML 소스
    """
    try:

        # 1. 티커 형식 보정
        ticker = in_ticker.upper()
        if ticker.isdigit():
            # 보통 6자리 숫자는 한국 주식 (기본 코스피로 시도)
            ticker = f"{ticker}.KS"

        # 2. 데이터 가져오기 (보정된 ticker 변수 사용)
        stock = yf.Ticker(ticker)
        df = stock.history(period="1mo")
        if df.empty and ".KS" in ticker:
            # 코스피(.KS)로 안될 경우 코스닥(.KQ)으로 한 번 더 시도
            ticker = ticker.replace(".KS", ".KQ")
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
        if df.empty:
            return "<div style='padding:20px; text-align:center;'>차트 데이터를 불러올 수 없습니다. (종목코드 확인 필요)</div>"
        
        # 3. 차트 생성
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            increasing_line_color='red', 
            decreasing_line_color='blue'
        )])
        fig.update_layout(
            title=f"📊 {ticker} 최근 1개월 시세",
            xaxis_rangeslider_visible=False,
            height=300,
            margin=dict(l=10, r=10, t=40, b=10),
            template="plotly_white",
            xaxis=dict(
                type='date',
                tickformat='%m-%d'
            )
        )
        # 4. HTML 변환 (include_plotlyjs는 index.html에서 불러오므로 생략 가능하나 안전하게 'cdn' 유지)
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    except Exception as e:
        print(f"❌ 차트 생성 실패: {e}")
        return f"<div>차트 생성 중 오류 발생: {e}</div>"

def get_stock_info_with_name(in_ticker):
    """
    # 설명 : 모의투자-주식종목명 가져오기 (Plotly 활용)
    # 입력 : in_ticker-종목코드
    # 출력 : 종멱명, 가격 리턴
    """
    try:
        stock = yf.Ticker(in_ticker)
        # info에서 shortName(종목명)을 가져옵니다.
        name = stock.info.get('shortName', in_ticker) 
        price = stock.fast_info['last_price']
        return {"name": name, "price": price}
    except:
        return {"name": in_ticker, "price": 0}
    
# --- FastAPI 경로 ---

@APP_ESC.get("/")
def get_chat_page(request: Request):
    """
    # 설명 : 모의투자-루트 경로 페이지
    # 입력 : request
    # 출력 : test.html 페이지
    # 소스 : 
    """
    # return TEMPLATES_ESC.TemplateResponse("test.html", {"request": request})
    file_path = os.path.join(STATIC_PATH, "test.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        return {"error": f"파일을 찾을 수 없습니다. 시도한 경로: {file_path}"}

@APP_ESC.post("/esc/chatEsc")
async def chatEsc(
    in_message: str = Form(...),
    in_user_id: str = Form(None),
    in_invest_amount: str = Form("10000000")
):
    """
    # 설명 : 모의투자-챗봇 채팅 메시지
    # 입력 : request
    # 출력 : response json
    # 소스 : 
    """
    try:
        user_id = in_user_id
        if not user_id or user_id == "null":
            user_id = f"user-{str(uuid.uuid4())[:8]}"
        
        user_data = get_user_status(user_id)
        set_saveHistory(user_id, "질문", in_result_msg=in_message)

        # 1. 잔고 확인 키워드 처리
        if any(keyword in in_message for keyword in ["잔고", "내 정보", "자산", "포트폴리오"]):
            cash = user_data.get('cash_esc', 10000000)
            portfolio = user_data.get('portfolio', {})
            
            html = f"""
            <div style="min-width: 260px; font-family: 'Malgun Gothic', sans-serif;">
                <div style="background: #4a90e2; color: white; padding: 10px; border-radius: 8px 8px 0 0; font-weight: bold;">
                    💰 {user_id}님 모의투자 자산 현황
                </div>
                <div style="padding: 15px; background: white; border: 1px solid #4a90e2; border-top: none; border-radius: 0 0 8px 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>보유 모의투자 예수금</span>
                        <strong>{cash:,.0f}원</strong>
                    </div>
            """
            if portfolio:
                html += "<div style='border-top: 1px solid #eee; padding-top: 10px; margin-top: 10px;'><b>📈 보유 모의투자 종목</b></div>"
                total_eval = 0
                for ticker, data in portfolio.items():
                    display_ticker = ticker.replace("_", ".")
                    lookup_ticker = display_ticker if "." in display_ticker else f"{display_ticker}.KS"
                    qty = data.get('qty', 0)
                    avg_p = data.get('avg_price', 0)

                    info = get_stock_info_with_name(lookup_ticker)
                    stock_name = info['name']
                    
                    curr_p = get_stock_info_esc(lookup_ticker) or avg_p
                    eval_p = curr_p * qty
                    profit_rate = ((curr_p - avg_p) / avg_p * 100) if avg_p > 0 else 0
                    total_eval += eval_p
                    color = "#e74c3c" if profit_rate > 0 else ("#3498db" if profit_rate < 0 else "#666")
                    
                    html += f"""
                    <div style="margin-top: 10px; padding: 8px; background: #f8f9fa; border-radius: 5px;">
                        <div style="display: flex; justify-content: space-between; font-weight: bold;">
                            <span>{stock_name} {display_ticker} <small>({qty}주)</small></span>
                            <span style="color: {color};">{profit_rate:+.2f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.85em; color: #555;">
                            <span>현재가: {curr_p:,.0f}원</span>
                            <span>평가액: {eval_p:,.0f}원</span>
                        </div>
                    </div>
                    """
                html += f"<div style='margin-top:15px; text-align:right; border-top:2px solid #4a90e2;'><b>총 모의투자 자산: {cash + total_eval:,.0f}원</b></div>"
            else:
                html += "<div style='color:#999; text-align:center; margin-top:10px;'>보유 모의투자 주식이 없습니다.</div>"
            
            html += "</div></div>"
            return {"response": html}

        # 2. AI 및 주문 처리
        functions = [
            {
                "name": "set_buy_stock_api", 
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "in_ticker": {"type": "string"}, 
                        "in_quantity": {"type": "integer"}
                    }, 
                    "required": ["in_ticker", "in_quantity"]
                }
            },
            {
                "name": "set_sell_stock_api", 
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "in_ticker": {"type": "string"}, 
                        "in_quantity": {"type": "integer"}
                    }, 
                    "required": ["in_ticker", "in_quantity"]
                }
            }
        ]

        ai_res = AI_CLIENT_ESC.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        f"당신은 주식 거래 전문가입니다. 사용자는 {user_id}입니다. "
                        "종목 코드를 추출할 때 반드시 최신 정보를 바탕으로 정확한 6자리 숫자를 찾으세요. "
                        "예: 삼성전자는 005930.KS, 한국전력은 015760.KS입니다. "  # 가이드 추가
                        "만약 사용자가 보유한 종목의 코드를 정확히 모른다면, '자산 현황'에 표시된 티커를 우선적으로 참고하세요."
                    )
                },
                {"role": "user", "content": in_message}
            ],
            functions=functions, 
            function_call="auto"
        )

        ai_msg = ai_res.choices[0].message

        if ai_msg.function_call:
            args = json.loads(ai_msg.function_call.arguments)
            ticker = args.get('in_ticker')
            qty = args.get('in_quantity')
            
            # 차트 생성
            # chart_html = get_stock_chart_html(ticker)
            
            if ai_msg.function_call.name == "set_buy_stock_api":
                result = set_buy_stock(user_id, ticker, qty)
                bg, border, title = "#ebf5fb", "#aed6f1", "✅ 모의투자 매수 완료"
                icon = "📈"  # 여기서 icon 정의
                color = "#e74c3c" # 강조색 (빨강)
            else:
                result = set_sell_stock(user_id, ticker, qty)
                bg, border, title = "#fef9e7", "#f9e79f", "💰 모의투자 매도 완료"
                icon = "📉"  # 여기서 icon 정의
                color = "#3498db" # 강조색 (파랑)
            # 차트 대신 요약 카드를 반환
            res_html = f"""
                    <div style="padding: 15px; border-radius: 12px; background: {bg}; border: 2px solid {border}; font-family: 'Malgun Gothic', sans-serif;">
                        <div style="font-size: 1.1em; font-weight: bold; margin-bottom: 8px; color: #2c3e50; display: flex; align-items: center;">
                            <span style="font-size: 1.3em; margin-right: 8px;">{icon}</span> 
                            <span style="color: {color};">{title}</span>
                        </div>
                        <div style="color: #34495e; line-height: 1.6;">
                            <strong>{result}</strong>
                        </div>
                        <div style="margin-top: 10px; font-size: 0.85em; color: #7f8c8d; border-top: 1px dotted {border}; padding-top: 8px;">
                            실시간 시세가 반영된 결과입니다.
                        </div>
                    </div>
            """
            set_saveHistory(user_id, "답변", in_result_msg=result)
            return {"response": res_html}

        # 2. AI 일반 응답 저장
        ans_content = ai_msg.content if ai_msg.content else "죄송합니다. 요청을 이해하지 못했습니다."
        set_saveHistory(user_id, "답변", in_result_msg=ans_content)
        return {"response": ans_content}
    except Exception as e:
        print(f"🔥 서버 내부 에러: {e}")
        return {"response": f"죄송합니다. 처리 중 오류가 발생했습니다. (사유: {str(e)})"}
    
@APP_ESC.get("/esc/initEsc")
async def initEsc(in_userId: str = Query(None), in_phone: str = Query(...)):
    """
    # 설명 : 모의투자-초기화함수
    # 입력 : in_userId-사용자ID, in_phone-폰번호
    # 출력 : response json
    # 소스 : 
    """
    userId=in_userId
    if not userId or userId == "null" or userId.strip() == "":
        userId = f"user-{str(uuid.uuid4())[:8]}"
    get_user_status(userId)
    return {"message": f"🌟 {userId}님 환영합니다!\n현재 10,000,000원의 투자금이 설정되었습니다.", "userId": userId}

@APP_ESC.get("/apiEsc/popup-status")
async def get_popup_status(in_userId: str = Query(...)):
    """
    # 설명 : 모의투자-수익률 팝업용 데이터 제공 (Elasticsearch 연동 버전)
    # 입력 : in_userId - 사용자id
    # 출력 : response - 엘라스틱서치 trade_esc_history 기반 자산 분석 리스트
    """
    try:
        index_name = "trade_esc_history"
        
        # 1위 유저 식별
        top_res = es.search(index=index_name, body={
            "size": 1,
            "query": {"exists": {"field": "rate"}},
            "sort": [{"rate": {"order": "desc"}}]
        })
        if not top_res['hits']['hits']: return []
        target_uid = top_res['hits']['hits'][0]['_source'].get('uid')

        # 해당 유저의 모든 데이터 가져오기
        res = es.search(index=index_name, body={
            "size": 500,
            "query": { "match_phrase": { "uid": target_uid } }
        })
        
        user_hits = res['hits']['hits']
        processed_data = []

        for h in user_hits:
            s = h['_source']
            try:
                # 모든 수치형 데이터에 대해 None 체크 수행
                buy_p = s.get('buy_p')
                sell_p = s.get('sell_p')
                rate = s.get('rate')
                qty = s.get('qty')

                processed_data.append({
                    "date": s.get('buy_dt', '2025-01-01'),
                    "name": s.get('sn', '알 수 없음'),
                    "ticker": s.get('ticker', '005930.KS'),
                    "code": s.get('ticker', '005930.KS'),
                    "buyPrice": float(buy_p) if buy_p is not None else 0.0,
                    "quantity": int(qty) if qty is not None else 0,
                    "currentPrice": float(sell_p) if sell_p is not None else (float(buy_p) if buy_p is not None else 0.0),
                    "returnRate": float(rate) if rate is not None else 0.0
                })
            except (ValueError, TypeError):
                continue

        print(f"✅ [DEBUG] {target_uid} 유저의 데이터 {len(processed_data)}건 가공 완료")
        return processed_data

    except Exception as e:
        print(f"🔥 팝업 상태 API 에러: {e}")
        return []
    
# 2. 특정 종목의 과거 차트 데이터 가져오기 (Plotly용)
@APP_ESC.get("/apiEsc/stock-chart-data")
async def get_stock_chart_data(in_code: str = Query(...)):
    """
    # 설명 : 모의투자-특정종목의 과거 차트 데이터 가져오기
    # 입력 : in_code-종목코드
    # 출력 : response-차트 데이터
    """
    try:
        # 매수 시점 전후의 데이터를 보여주기 위해 기간 설정
        stock = yf.Ticker(in_code)
        # 성공 사례가 3월이므로 2024년 전체 데이터를 가져오거나 최근 1년치를 가져옴
        # df = stock.history(start="2024-01-01", end="2024-12-31")
        df = stock.history(period="1y") # 고정 날짜 대신 최근 1년치 데이터 가져오기
        
        if df.empty:
            return {"error": "데이터가 없습니다."}
        
        df = df.dropna(subset=['Close'])
        chart_data = {
            "dates": df.index.strftime('%Y-%m-%d').tolist(),
            "closes": [float(x) for x in df['Close'].tolist()]
        }
        return chart_data
    except Exception as e:
        return {"error": str(e)}

@APP_ESC.get("/show-popupEsc", response_class=HTMLResponse)
async def get_popup_page(in_userId: str):
    """
    # 설명 : 모의투자-팝업 페이지 호출
    # 입력 : in_userId-사용자코드
    # 출력 : response-차트 데이터
    """
    userId = in_userId
    # f-string 안에서 자바스크립트/CSS 중괄호는 반드시 {{ }} 로 써야 합니다.
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>자산 분석 리포트</title>
        <script src="https://cdn.plot.ly/plotly-2.24.2.min.js"></script>
        <style>
            body {{ 
                margin: 0; 
                padding: 0; 
                background: #0f172a !important; 
                overflow: hidden; 
            }}
            #modalContainer {{ 
                background: #0f172a; 
                width: 100vw; 
                height: 100vh; 
            }}
        </style>
    </head>
    <body>
        <div id="modalContainer"></div>
        <script src="/staticEsc/popup.js"></script>
        <script>
            window.onload = function() {{
                if (typeof getStockModalDOM === 'function') {{
                    getStockModalDOM('{userId}');
                    
                    setTimeout(() => {{
                        const modal = document.getElementById('stockModal');
                        if (modal) {{
                            modal.style.position = 'fixed';
                            modal.style.top = '0';
                            modal.style.left = '0';
                            modal.style.transform = 'none';
                            modal.style.width = '100vw';
                            modal.style.height = '100vh';
                            modal.style.maxWidth = 'none';
                            modal.style.borderRadius = '0';
                        }}
                        const overlay = document.getElementById('modalOverlay');
                        if (overlay) {{
                            overlay.style.display = 'none';
                        }}
                    }}, 200);
                }}
            }};
        </script>
    </body>
    </html>
    """
# 2. 본인의 테스트 페이지 (index.html 역할)
@APP_ESC.get("/test-page", response_class=HTMLResponse)
async def get_test_page():
    """
    # 설명 : 모의투자-테스트 html 페이지
    # 입력 : None
    # 출력 : None
    """
    # 위에서 만든 test.html을 읽어서 반환하거나 직접 문자열로 넣어도 됩니다.
    # 여기서는 간단하게 위 html 코드를 그대로 반환한다고 가정합니다.
    with open(os.path.join(CURRENT_DIR_ESC, "static", "test.html"), "r", encoding="utf-8") as f:
        return f.read()
    
@APP_ESC.get("/apiEsc/total-rank-top1")
async def get_total_rank_top1(response: Response, t: str = Query(None)):
    """
    # 설명 : get_total_rank_top1 - ES 집계를 이용한 전체 수익금 1위 조회
    # 입력 : response (FastAPI Response 객체), t (캐시 방지용 타임스탬프)
    # 출력 : top_user 정보 (ID, 이름, 총수익금)
    # 소스 : Elasticsearch trade_esc_history 인덱스
    """
    # 캐시 방지 헤더 설정
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"

    try:
        # trade_summary 인덱스를 사용하여 실시간 자산 가치 계산
        body = {
            "size": 0,
            "aggs": {
                "top_earner": {
                    "terms": {
                        "field": "user_id", # .keyword가 필요하면 user_id.keyword
                        "size": 1,
                        "order": { "total_valuation": "desc" }
                    },
                    "aggs": {
                        "total_valuation": {
                            "sum": {
                                "script": {
                                    # 실현손익(매도-매수) + 평가손익(보유량 * 현재가)
                                    "source": """
                                        double realized = doc['total_sell_amt'].value - doc['total_buy_amt'].value;
                                        double hold_qty = doc['total_buy_qty'].value - doc['total_sell_qty'].value;
                                        return realized + (hold_qty * doc['current_price'].value);
                                    """
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # trade_summary 인덱스에서 조회 (기존 history 인덱스보다 훨씬 정확함)
        res = es.search(index="trade_summary", body=body)
        buckets = res.get('aggregations', {}).get('top_earner', {}).get('buckets', [])
        
        if buckets:
            top_user = buckets[0]
            u_id = top_user['key']
            # 원금 10억을 더해서 노출할지, 순수익만 노출할지 결정하세요. 
            # 여기서는 '순수익'만 일단 계산합니다.
            u_profit = top_user['total_valuation']['value'] 
            
            print(f"📡 [RANKING] 실시간 1위 추출: {u_id}, 총수익: {u_profit}")

            return {
                "error": False,
                "user_id": u_id,
                "user_name": u_id, # 이름 필드가 따로 없다면 ID로 대체
                "total_profit": int(u_profit) # 가독성을 위해 정수화
            }
        else:
            return {"error": True, "message": "No users found."}

    except Exception as e:
        print(f"❌ [RANKING ERROR] {str(e)}")
        return {"error": True, "message": str(e)}

# 새 엔드포인트: trade_esc_history 모든 데이터 기반 차트
@APP_ESC.get("/esc/api/chart/trade_history", response_class=HTMLResponse)
def get_trade_history_chart():
    # OpenSearch 쿼리: 모든 데이터 가져오기 (size=1000 제한, 대량이면 aggregation 사용)
    body = {
        "query": {"match_all": {}},
        "size": 1000,  # 모든 데이터지만 안전하게 제한
        "sort": [{"timestamp": {"order": "asc"}}]  # timestamp 필드 가정
    }
    res = es.search(index="trade_esc_history", body=body)
    hits = res['hits']['hits']
    
    if not hits:
        return HTMLResponse("<div>데이터가 없습니다.</div>")
    
    # 데이터 추출 (필드 가정: timestamp, rate, ticker 등)
    dates = [hit['_source'].get('timestamp') for hit in hits]
    rates = [hit['_source'].get('rate', 0) for hit in hits]  # 수익률 예시
    tickers = [hit['_source'].get('ticker') for hit in hits]
    
    # Plotly 차트 생성 (라인 차트 예시)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=rates, mode='lines+markers',
        text=tickers,  # 호버 시 ticker 표시
        name='수익률 추이'
    ))
    fig.update_layout(
        title="Trade History: 전체 수익률 추이",
        xaxis_title="날짜",
        yaxis_title="수익률 (%)",
        height=500,
        template="plotly_white"
    )
    
    # HTML로 리턴 (클라이언트에서 embed 가능)
    return HTMLResponse(fig.to_html(full_html=False, include_plotlyjs='cdn'))

# 비슷하게 trade_summary 차트 (예: 요약 바 차트)
@APP_ESC.get("/esc/api/chart/trade_summary", response_class=HTMLResponse)
def get_trade_summary_chart():
    body = {"query": {"match_all": {}}, "size": 1000}
    res = es.search(index="trade_summary", body=body)
    hits = res['hits']['hits']
    
    users = [hit['_source'].get('user_id') for hit in hits]
    total_profits = [hit['_source'].get('total_profit', 0) for hit in hits]  # 필드 가정
    
    fig = go.Figure(data=go.Bar(x=users, y=total_profits))
    fig.update_layout(title="Trade Summary: 사용자별 총 수익")
    
    return HTMLResponse(fig.to_html(full_html=False, include_plotlyjs='cdn'))

# stock_master 차트 (예: 주식 마스터 가격 분포)
@APP_ESC.get("/esc/api/chart/stock_master", response_class=HTMLResponse)
def get_stock_master_chart():
    body = {
        "query": {"match_all": {}},
        "aggs": {
            "price_buckets": {
                "histogram": {"field": "price", "interval": 10000}  # 가격 히스토그램 (필드 가정)
            }
        }
    }
    res = es.search(index="stock_master", body=body)
    
    buckets = res['aggregations']['price_buckets']['buckets']
    keys = [b['key'] for b in buckets]
    counts = [b['doc_count'] for b in buckets]
    
    fig = go.Figure(data=go.Bar(x=keys, y=counts))
    fig.update_layout(title="Stock Master: 가격 분포 히스토그램")
    
    return HTMLResponse(fig.to_html(full_html=False, include_plotlyjs='cdn'))