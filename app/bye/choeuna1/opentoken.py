import requests
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# .env에서 키값 가져오기
CLIENT_ID = os.getenv("OPENBANK_CLIENT_ID")
CLIENT_SECRET = os.getenv("OPENBANK_CLIENT_SECRET")

# 테스트 환경 토큰 발급 URL
TOKEN_URL = "https://testapi.openbanking.or.kr/oauth/2.0/token"

# 2-legged 인증 (이용기관 인증)
data = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": "oob",                    # 이용기관 인증
    "grant_type": "client_credentials"
}

headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

print("토큰 발급 요청 중...")

response = requests.post(TOKEN_URL, data=data, headers=headers)

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data["access_token"]
    print("🎉 Access Token 발급 성공!")
    print("Token:", access_token)
    print("만료 시간:", token_data["expires_in"], "초 (약 90일)")
    print("Scope:", token_data.get("scope", "oob"))
else:
    print("❌ 토큰 발급 실패")
    print("Status Code:", response.status_code)
    print("Response:", response.text)