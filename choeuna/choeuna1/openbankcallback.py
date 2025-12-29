# app.py

from flask import Flask, request, redirect, jsonify
import requests
from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()

app = Flask(__name__)

# .env에서 키 로드
CLIENT_ID = os.getenv("OPENBANK_CLIENT_ID")
CLIENT_SECRET = os.getenv("OPENBANK_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5050/auth/callback/"  # 콜백 주소

# 테스트 환경 URL
AUTH_URL = "https://testapi.openbanking.or.kr/oauth/2.0/authorize"
TOKEN_URL = "https://testapi.openbanking.or.kr/oauth/2.0/token"

# 메인 페이지 - 인증 시작 버튼
@app.route("/")
def home():
    return """
    <h1>오픈뱅킹 3-legged 인증 테스트</h1>
    <p><a href="/login">
        <button style="padding:15px 30px; font-size:18px;">오픈뱅킹 인증 시작</button>
    </a></p>
    <p>클릭하면 오픈뱅킹 인증 페이지로 이동합니다.</p>
    """

# 1. 인증 시작 (사용자 동의 유도)
@app.route("/login")
def login():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "login inquiry transfer",
        "state": "random_state_123",
        "auth_type": "0"   # 최초인증
    }
    
    auth_url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print("인증 URL:", auth_url)
    return redirect(auth_url)

# 2. 콜백 처리 (code 받기 → 토큰 발급)
@app.route("/auth/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")

    if error:
        return f"<h2>오픈뱅킹 인증 실패</h2><p>Error: {error}</p>"

    if not code:
        return "<h2>코드가 없습니다. 인증 실패</h2>"

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
        return f"""
        <h2>토큰 발급 실패</h2>
        <pre>{token_response.text}</pre>
        """

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

    return f"""
    <h1>🎉 오픈뱅킹 인증 및 토큰 발급 성공!</h1>
    <h3>사용자 일련번호: {user_seq_no}</h3>
    <p><strong>Access Token (앞 50자리):</strong> {access_token[:50]}...</p>
    <h3>참가은행 상태</h3>
    <p>{bank_list}</p>
    <hr>
    <a href="/">홈으로 돌아가기</a>
    """

if __name__ == "__main__":
    # http://localhost:5050
    app.run(host="0.0.0.0", port=5050, debug=True)