import discord
import os
import requests
import json
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
KIS_APPKEY = os.getenv('KIS_APPKEY')
KIS_SECRET = os.getenv('KIS_SECRET')
KIS_CANO = os.getenv('KIS_CANO')
KIS_ACNT_PRDT_CD = os.getenv('KIS_ACNT_PRDT_CD', '01')
KIS_URL = os.getenv('KIS_URL', 'https://openapi.koreainvestment.com:9443')

# 2. 전역 변수 및 OpenAI 설정
client = OpenAI(api_key=OPENAI_API_KEY)
user_conversations = {}
ACCESS_TOKEN = None

# 3. KIS 접근 토큰 발급 (명세서 규격 적용)
def get_kis_access_token():
    global ACCESS_TOKEN
    try:
        url = f"{KIS_URL}/oauth2/tokenP"
        # 명세서 헤더 규격 준수 (charset=utf-8 포함)
        headers = {"content-type": "application/json; charset=utf-8"}
        payload = {
            "grant_type": "client_credentials",
            "appkey": KIS_APPKEY,
            "secretkey": KIS_SECRET
        }
        res = requests.post(url, headers=headers, data=json.dumps(payload))
        ACCESS_TOKEN = res.json().get('access_token')
        if ACCESS_TOKEN:
            print("✅ KIS 토큰 발급 성공")
        return ACCESS_TOKEN
    except Exception as e:
        print(f"❌ KIS 토큰 발급 오류: {e}")
        return None

# 4. 주식 일자별 시세 조회 (명세서 FHKST01010400 규격 엄격 적용)
def get_stock_daily_price(stock_code):
    if not ACCESS_TOKEN:
        get_kis_access_token()
    
    # 명세서 기준 URL 및 필수 헤더 (custtype: P 포함)
    url = f"{KIS_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": KIS_APPKEY,
        "appsecret": KIS_SECRET,
        "tr_id": "FHKST01010400", # 명세서상 실전/모의 동일 TR_ID
        "custtype": "P"
    }
    
    # 명세서 Layout 기반 필수(Required) 파라미터 (10자리 규격 준수)
    params = {
        "FID_COND_MRKT_DIV": "J",             # 시장 구분 (J: 주식)
        "FID_INPUT_ISCD": stock_code,         # 종목코드 (6자리)
        "FID_PERIOD_DIV_CODE": "D",           # 기간 구분 (D: 일별)
        "FID_ORG_ADJ_PRC": "0000000001"       # 명세서 예시 기준 (수정주가 미반영)
    }
    
    res = requests.get(url, headers=headers, params=params)
    data = res.json()
    
    if data.get('rt_cd') == '0':
        output = data.get('output', [])
        return output[0] if output else None
    else:
        # 실패 시 상세 로그를 터미널에 출력하여 주인님께서 확인 가능하게 함
        print(f"⚠️ KIS 시세 조회 실패: {data}")
        return None

# 5. 계좌 잔액 조회
def get_balance():
    if not ACCESS_TOKEN: get_kis_access_token()
    url = f"{KIS_URL}/uapi/domestic-stock/v1/trading/inquire-balance"
    tr_id = "VTTC8434R" if "vts" in KIS_URL else "TTTC8434R"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": KIS_APPKEY, "appsecret": KIS_SECRET,
        "tr_id": tr_id, "custtype": "P"
    }
    params = {
        "CANO": str(KIS_CANO), "ACNT_PRDT_CD": str(KIS_ACNT_PRDT_CD),
        "AFHR_FLG": "N", "OFRT_WTHR_ITM_GUBUN": "N", "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01", "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""
    }
    res = requests.get(url, headers=headers, params=params)
    output2 = res.json().get('output2', [])
    return output2[0].get('dnca_tot_amt') if output2 else "0"

# 6. XML 프롬프트 로드
def load_lua_prompt(file_path='prompt.xml'):
    if not os.path.exists(file_path):
        return "당신은 금융 조력자 LUA입니다."
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 7. 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'------------------------------------------')
    print(f'🚀 LUA 금융 시스템 통합 가동 성공!')
    print(f'📡 계좌번호: {KIS_CANO} | 모델: gpt-4o-mini')
    print(f'------------------------------------------')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    async with message.channel.typing():
        try:
            lua_rules = load_lua_prompt()
            channel_id = str(message.channel.id)
            if channel_id not in user_conversations:
                user_conversations[channel_id] = []

            # AI 의도 파악 (주가조회, 잔액조회 등)
            intent_res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "주가조회면 'STOCK:종목코드6자리', 잔액조회면 'BALANCE', 기타 'ETC'"},
                          {"role": "user", "content": message.content}]
            ).choices[0].message.content.strip()

            financial_info = ""
            if "STOCK" in intent_res:
                stock_code = intent_res.split(':')[-1]
                if len(stock_code) == 6:
                    recent_data = get_stock_daily_price(stock_code)
                    if recent_data:
                        # 명세서 필드: stck_clpr(종가), prdy_vrss(대비)
                        financial_info = f"\n[데이터: 종가 {recent_data.get('stck_clpr')}원, 전일대비 {recent_data.get('prdy_vrss')}원]"
                    else:
                        financial_info = "\n[시세 정보를 가져오지 못했습니다. 종목코드를 확인해 주세요.]"
            elif "BALANCE" in intent_res:
                balance_amt = get_balance()
                financial_info = f"\n[현재 계좌 잔액: {balance_amt}원]"

            # 최종 답변 생성 (LUA 페르소나 및 대화 기록 적용)
            user_conversations[channel_id].append({"role": "user", "content": message.content})
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"당신은 아래 XML 규칙을 엄격히 따르는 LUA입니다:\n\n{lua_rules}"},
                    {"role": "system", "content": f"참고 금융 데이터: {financial_info}"}
                ] + user_conversations[channel_id][-10:],
                temperature=0.5
            )
            
            ai_answer = response.choices[0].message.content
            user_conversations[channel_id].append({"role": "assistant", "content": ai_answer})
            await message.reply(ai_answer)
            
        except Exception as e:
            print(f"❌ 시스템 오류: {e}")
            await message.channel.send("LUA 시스템 통신 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)