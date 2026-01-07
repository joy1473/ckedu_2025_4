# app.py

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from dotenv import load_dotenv
import os
import urllib.parse
import secrets
import string

load_dotenv()

app = FastAPI(title="OpenBank Callback App", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# .env에서 키 로드
CLIENT_ID = os.getenv("OPENBANK_CLIENT_ID")
CLIENT_SECRET = os.getenv("OPENBANK_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5050/auth/callback"  # 콜백 주소

# 테스트 환경 URL
AUTH_URL = "https://testapi.openbanking.or.kr/oauth/2.0/authorize"
TOKEN_URL = "https://testapi.openbanking.or.kr/oauth/2.0/token"

accountinfo_api_tran_id = os.getenv("accountinfo_api_tran_id")
accountinfo_list_num = os.getenv("accountinfo_list_num")
print(CLIENT_ID)
print(CLIENT_SECRET)
print(accountinfo_api_tran_id)
print(accountinfo_list_num)

# 안전한 랜덤 키 생성 함수 (문자 포함)
def generate_secure_key(length=12):
  # 랜덤 문자열 생성 (문자, 숫자, 특수문자 포함)
  alphabet = string.ascii_letters + string.digits
  random_key = ''.join(secrets.choice(alphabet) for i in range(length))
  return random_key

# 메인 페이지 - 인증 시작 버튼
@app.get("/", response_class=HTMLResponse)
async def home():
    #print(CLIENT_ID)
    return """
    <h1>오픈뱅킹 3-legged 인증 테스트</h1>
    <p><a href="/login">
        <button style="padding:15px 30px; font-size:18px;">오픈뱅킹 인증 시작</button>
    </a></p>
    <p>클릭하면 오픈뱅킹 인증 페이지로 이동합니다.</p>
    """

# 1. 인증 시작 (사용자 동의 유도)
@app.get("/login")
async def login():
    accountinfo_yn = 'Y'
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "login inquiry transfer",
        "state": generate_secure_key(32),
        "auth_type": "0",  # 최초인증
        "accountinfo_yn": accountinfo_yn,
        "accountinfo_api_tran_id":accountinfo_api_tran_id if accountinfo_yn == 'Y' else '',
        "accountinfo_list_num": accountinfo_list_num if accountinfo_yn == 'Y' else '',
    }

    auth_url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    #auth_url = get_auth_url()
    print("인증 URL:", auth_url)
    return RedirectResponse(url=auth_url)

# 2. 콜백 처리 (code 받기 → 토큰 발급)
@app.get("/auth/callback/")
async def callback(code: str = None, state: str = None, error: str = None, error_description: str = None):
    print(f"code:{code}")
    print(f"state:{state}")
    print(f"error:{error}")
    print(f"error_description:{error_description}")

    if error:
        return HTMLResponse(f"<h2>오픈뱅킹 인증 실패</h2><p>Error: {error}</p>")

    if not code:
        return HTMLResponse("<h2>코드가 없습니다. 인증 실패</h2>")

    print("받은 code:", code)
    print("state:", state)

    # 토큰 발급 요청
    token_data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    token_response = requests.post(TOKEN_URL, data=token_data)

    if token_response.status_code != 200:
        return HTMLResponse(f"""
        <h2>토큰 발급 실패</h2>
        <pre>{token_response.text}</pre>
        """)

    token_json = token_response.json()
    access_token = token_json["access_token"]
    user_seq_no = token_json.get("user_seq_no", "없음")

    # 토큰으로 참가은행 상태 조회 테스트
    api_response = requests.get(
        "https://testapi.openbanking.or.kr/v2.0/bank/status",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if api_response.status_code == 200:
        banks = api_response.json()
        bank_list = "<br>".join([
            f"{b['bank_name']} ({b['bank_code_std']}): {'거래가능' if b['bank_status']=='Y' else '장애'}"
            for b in banks["res_list"]
        ])
    else:
        bank_list = f"API 호출 실패: {api_response.status_code}<br>{api_response.text}"

    return HTMLResponse(f"""
    <h1>🎉 오픈뱅킹 인증 및 토큰 발급 성공!</h1>
    <h3>사용자 일련번호: {user_seq_no}</h3>
    <p><strong>Access Token :</strong> {access_token}...</p>
    <h3>참가은행 상태</h3>
    <p>{bank_list}</p>
    <hr>
    <a href="/">홈으로 돌아가기</a>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)