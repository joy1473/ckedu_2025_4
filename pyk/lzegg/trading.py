import os
import yfinance as yf
from pymongo import MongoClient
from pathlib import Path
from dotenv import load_dotenv


# 1. 상위 폴더의 .env 로드
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 2. MongoDB 접속
mongo_url = os.getenv("MONGO_URL")
client = MongoClient(mongo_url)

# 3. 데이터베이스와 컬렉션(테이블) 지정
db = client['ykpark']  # DB 이름
users = db['user']           # 사용자 저장소 이름

# 1. 사용자 생성 (회원가입 기능으로 남겨둠)
def create_user(username):
    if users.find_one({"username": username}):
        return None # 이미 있으면 패스
    
    new_user = {
        "username": username,
        "cash": 10000000,
        "portfolio": {},
        "history": []
    }
    users.insert_one(new_user)
    return username
def get_stock_info(ticker):
    """주식의 현재가와 이름을 가져옵니다."""
    try:
        stock = yf.Ticker(ticker)
        # 한국 주식(005930.KS)과 미국 주식(AAPL) 모두 대응
        price = stock.fast_info['last_price']
        return round(price, 2)
    except Exception as e:
        print(f"주가 정보 로드 에러: {e}")
        return None
    
def create_first_user(name):
    # 이미 있는지 확인
    if users.find_one({"username": name}):
        return "이미 가입된 사용자입니다."
    
    # 데이터 생성
    user_data = {
        "username": name,
        "cash": 10000000,      # 가상 현금 1,000만원
        "portfolio": {},       # 처음엔 빈 주머니
        "history": []          # 거래 내역
    }
    
    # DB에 넣기
    users.insert_one(user_data)
    return f"축하합니다! {name}님께 가상 현금 1,000만원이 지급되었습니다."
def buy_stock(username, ticker, quantity):
    price = get_stock_info(ticker)
    total_cost = price * quantity
    user = users.find_one({"username": username})

    if user['cash'] < total_cost:
        return "잔액이 부족합니다."

    # 기존 포트폴리오 가져오기
    portfolio = user.get("portfolio", {})
    
    # 새로운 평단가 계산 로직 (기존 보유량 + 신규 매수량 합산)
    if ticker in portfolio and isinstance(portfolio[ticker], dict):
        old_qty = portfolio[ticker]['qty']
        old_avg_price = portfolio[ticker]['avg_price']
        new_qty = old_qty + quantity
        new_avg_price = ((old_avg_price * old_qty) + (price * quantity)) / new_qty
    else:
        new_qty = quantity
        new_avg_price = price

    # DB 업데이트 (평단가와 수량을 같이 저장)
    users.update_one(
        {"username": username},
        {
            "$inc": {"cash": -total_cost},
            "$set": {f"portfolio.{ticker}": {"qty": new_qty, "avg_price": new_avg_price}}
        }
    )
    return f"✅ {ticker} {quantity}주 매수 완료! (매수가: {price:,}원)"
def get_user_status(username):
    """사용자의 잔액과 포트폴리오 정보를 가져오는 함수"""
    user = users.find_one({"username": username})
    if user:
        return user
    else:
        # 1. 사용자가 없으면 새로 생성
        print(f"✨ {username} 사용자가 없어 새로 생성합니다.")
        create_user(username)
        
        # 2. 방금 생성된 정보를 다시 DB에서 꺼내옵니다.
        new_user = users.find_one({"username": username})
        return new_user
def get_stock_info(ticker):
    try:
        # 숫자로만 되어 있다면 한국 주식(.KS)으로 간주하여 보정
        if ticker.isdigit():
            ticker = f"{ticker}.KS"
            
        stock = yf.Ticker(ticker)
        # fast_info 대신 가장 최근 종가(history)를 가져오는 것이 더 안정적입니다.
        data = stock.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return None
    except Exception as e:
        print(f"주가 정보 로드 에러 ({ticker}): {e}")
        return None
def sell_stock(username, ticker, quantity):
    try:
        # 1. 현재 주가 가져오기
        price = get_stock_info(ticker)
        if not price:
            return "❌ 주가 정보를 가져올 수 없습니다."

        # 2. 유저 정보 가져오기
        user = users.find_one({"username": username})
        if not user:
            return "❌ 사용자를 찾을 수 없습니다."

        # 3. 포트폴리오 가져오기 및 보유 수량 확인
        # portfolio 필드가 아예 없을 경우를 대비해 {}를 기본값으로 설정
        portfolio = user.get("portfolio", {})
        current_qty = portfolio.get(ticker, 0)

        if current_qty < quantity:
            return f"❌ 매도 실패: 보유 수량이 부족합니다. (현재 {current_qty}주 보유)"

        # 4. 금액 계산
        total_receive = int(price * quantity)

        # 5. DB 업데이트
        # 현금은 늘리고
        users.update_one({"username": username}, {"$inc": {"cash": total_receive}})
        
        # 주식 수량 줄이기
        new_qty = current_qty - quantity
        if new_qty > 0:
            # MongoDB에서 점(.)이 포함된 키를 수정할 때는 아래와 같이 처리합니다.
            users.update_one(
                {"username": username}, 
                {"$set": {f"portfolio.{ticker}.qty": new_qty}}
            )
        else:
            # 0주가 되면 해당 종목 삭제
            users.update_one(
                {"username": username}, 
                {"$unset": {f"portfolio.{ticker}": ""}}
            )

        return f"✅ {ticker} {quantity}주 매도 완료! (+{total_receive:,}원)"

    except Exception as e:
        return f"🚨 매도 중 시스템 오류 발생: {str(e)}"
# 실행 테스트
if __name__ == "__main__":
    my_name = "test_user_1"  # 여기서 이름을 정의함
    # 1. 꼬인 데이터가 있다면 먼저 삭제 (005930 등)
    users.update_one({"username": my_name}, {"$unset": {"portfolio.005930": ""}})
    
    # 2. 기존 숫자 데이터를 딕셔너리 구조로 업데이트 (삼성전자 11주)
    users.update_one(
        {"username": my_name},
        {"$set": {
            "portfolio.005930.KS": {
                "qty": 11, 
                "avg_price": 111100.0
            }
        }}
    )
    print("✅ 데이터 변환 완료! 이제 0주로 나오지 않을 것입니다.")
    
    # 1. 정보 조회
    user_info = get_user_status(my_name) # my_name 사용
   
    if user_info:
        print(f"✅ {my_name}님의 정보 조회 성공!")
        print(f"잔액: {user_info['cash']}원")
        print(f"보유 주식: {user_info['portfolio']}")
    else:
        print(f"❌ {my_name} 사용자를 찾을 수 없습니다.")

    # 2. 삼성전자 현재가 확인
    samsung_price = get_stock_info("005930.KS")
    print(f"현재 삼성전자 주가: {samsung_price}원")
    
    # 3. 삼성전자 10주 매수 시도 (name -> my_name으로 변경)
    print(buy_stock(my_name, "005930.KS", 10))
    
    # 4. 최종 상태 확인 (name -> my_name으로 변경)
    updated_user = users.find_one({"username": my_name})
    print(f"최종 잔액: {updated_user['cash']}원")
    print(f"보유 주식: {updated_user['portfolio']}")