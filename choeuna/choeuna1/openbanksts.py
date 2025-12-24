import requests
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# .env에서 키값 가져오기
CLIENT_ID = os.getenv("OPENBANK_CLIENT_ID")
CLIENT_SECRET = os.getenv("OPENBANK_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ .env 파일에 OPENBANK_CLIENT_ID와 OPENBANK_CLIENT_SECRET이 설정되어 있지 않습니다.")
    exit()

# 테스트 환경 토큰 발급 URL
TOKEN_URL = "https://testapi.openbanking.or.kr/oauth/2.0/token"

print("1. Access Token 발급 요청 중...")

# 2-legged 인증 (이용기관 인증)
token_data = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": "oob",
    "grant_type": "client_credentials"
}

token_headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

token_response = requests.post(TOKEN_URL, data=token_data, headers=token_headers)

if token_response.status_code != 200:
    print("❌ 토큰 발급 실패")
    print("Status Code:", token_response.status_code)
    print("Response:", token_response.text)
    exit()

token_json = token_response.json()
access_token = token_json["access_token"]
print("🎉 Access Token 발급 성공!")
print(f"Token (앞 50자리): {access_token[:50]}...")
print(f"만료 시간: {token_json['expires_in']} 초 (약 90일)\n")

# =============================================
# 2. 발급받은 토큰으로 실제 API 호출 (예: 참가은행 상태 조회)
# =============================================

API_URL = "https://testapi.openbanking.or.kr/v2.0/bank/status"

api_headers = {
    "Authorization": f"Bearer {access_token}"
}

print("2. 참가은행 상태 조회 API 호출 중...")

api_response = requests.get(API_URL, headers=api_headers)

if api_response.status_code == 200:
    banks_data = api_response.json()
    print("✅ 참가은행 상태 조회 성공!\n")
    print(f"총 {banks_data['res_cnt']}개 은행")
    print("-" * 50)
    for bank in banks_data["res_list"]:
        status = "🟢 거래가능" if bank["bank_status"] == "Y" else "🔴 장애/종료"
        print(f"{bank['bank_name']:20} ({bank['bank_code_std']}) : {status}")
else:
    print("❌ 참가은행 상태 조회 실패")
    print("Status Code:", api_response.status_code)
    print("Response:", api_response.text)

print("\n🎄 모든 작업 완료! 이제 다른 API도 이 토큰으로 호출할 수 있어요.")