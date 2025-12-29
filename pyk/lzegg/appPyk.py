import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from .trading import get_user_status, buy_stock, get_stock_info, sell_stock

# 현재 파일(appPyk.py)의 위치를 잡고, 그 부모(상위) 폴더를 찾습니다.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / '.env'

# 상위 폴더의 .env 파일을 명시적으로 로드합니다.
load_dotenv(dotenv_path=env_path)

# 확인용 (서버 켤 때 터미널에 키 앞부분이 나오면 성공!)
api_key = os.getenv("OPENAI_API_KEY")
print(f"--- API 키 로드 확인: {api_key[:10] if api_key else '실패'} ---")

client = OpenAI(api_key=api_key)

app = FastAPI()
# 현재 실행 중인 appPyk.py 파일의 위치를 기준으로 templates 폴더 경로를 잡습니다.
current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

@app.get("/")
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# appPyk.py
@app.post("/chat")
async def chat(message: str = Form(...)):
    #TODO 사용자명 등 파라미터러 받아서 처리
    #TODO 잔고표시수정
    #TODO 투자금액 입력받아 처리
    user_name = "test_user_1"

    # [단계 1] '잔고' 키워드 체크 (가장 먼저 수행)
    if any(keyword in message for keyword in ["잔고", "내 정보", "자산", "포트폴리오"]):
        user_data = get_user_status(user_name)
        if not user_data:
            return {"response": "유저 정보를 찾을 수 없습니다."}
            
        cash = user_data.get('cash', 0)
        portfolio = user_data.get('portfolio', {})
        
        response_text = f"💰 **{user_name}**님의 자산 현황\n"
        response_text += f"━━━━━━━━━━━━━━\n"
        response_text += f"💵 **예수금:** {cash:,.0f}원\n\n"
        
        if portfolio:
            response_text += "📈 **보유 주식 현황**\n"
            total_eval_amount = 0 
            
            # appPyk.py의 for문 내부 수정
            for ticker, data in portfolio.items():
                if isinstance(data, dict):
                    qty = data.get('qty', 0)
                    avg_p = data.get('avg_price', 0)
                # 💡 [추가] 데이터가 숫자인 경우(기존 데이터) 대응
                elif isinstance(data, int) or isinstance(data, float):
                    qty = data
                    avg_p = 0  # 평단가 정보 없음
                    curr_p = get_stock_info(ticker) # 여기서 None이 올 수 있음
                    
                    # 💡 [수정 포인트] 주가 정보를 가져왔을 때만 계산 진행
                    if curr_p is not None:
                        profit_rate = ((curr_p - avg_p) / avg_p) * 100 if avg_p > 0 else 0
                        eval_amount = curr_p * qty
                        total_eval_amount += eval_amount
                        
                        response_text += f"• **{ticker}**: {qty}주\n"
                        response_text += f"  └ 현재가: {curr_p:,}원 ({profit_rate:+.2f}%)\n"
                    else:
                        # 주가를 가져오지 못한 경우
                        response_text += f"• **{ticker}**: {qty}주 (주가 정보 불러오기 실패)\n"
            
            if total_eval_amount > 0:
                response_text += f"\n💰 **총 주식 평가액:** {total_eval_amount:,.0f}원"
        else:
            response_text += "보유 중인 주식이 없습니다."
            
        return {"response": response_text}

    # [단계 2] 그 외 (매수/매도/대화) AI에게 분석 요청
    functions = [
        {
            "name": "buy_stock_api",
            "description": "주식 매수",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "종목코드 (예: 005930.KS)"},
                    "quantity": {"type": "integer", "description": "수량"}
                },
                "required": ["ticker", "quantity"]
            }
        },
        {
            "name": "sell_stock_api",
            "description": "주식 매도",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "종목코드 (예: 005930.KS)"},
                    "quantity": {"type": "integer", "description": "수량"}
                },
                "required": ["ticker", "quantity"]
            }
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 주식 거래 도우미야. 한국 주식은 종목코드 뒤에 .KS를 붙여줘."},
            {"role": "user", "content": message}
        ],
        functions=functions,
        function_call="auto"
    )

    ai_message = response.choices[0].message

    # AI가 함수 실행을 선택한 경우
    if ai_message.function_call:
        import json
        func_name = ai_message.function_call.name
        args = json.loads(ai_message.function_call.arguments)

        if func_name == "buy_stock_api":
            result = buy_stock(user_name, args['ticker'], args['quantity'])
            return {"response": f"✅ 주문 처리 결과: {result}"}
        
        elif func_name == "sell_stock_api":
            result = sell_stock(user_name, args['ticker'], args['quantity'])
            return {"response": result}

    # 일반 대화 응답
    return {"response": ai_message.content}