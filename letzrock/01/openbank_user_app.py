from flask import Flask, render_template, redirect, request
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json
from app_1 import generate_secure_key

# .env 파일에서 정보를 로드합니다.
load_dotenv()
# 금융결제원 설정 값 (오픈뱅킹 포털에서 발급받은 값 입력)
OPENBANK_CLIENT_ID = os.getenv("OPENBANK_CLIENT_ID")
OPENBANK_CLIENT_SECRET = os.getenv("OPENBANK_CLIENT_SECRET")
OPENBANK_DOMAIN = "https://openapi.openbanking.or.kr"
# 인터넷 회선 기반 API
OPENBANK_DOMAIN = "https://openapi.openbanking.or.kr"
# 테스트 API
OPENBANK_DOMAIN = "https://testapi.openbanking.or.kr"
OPENBANK_REDIRECT_URI = "http://localhost:5050/auth/callback/"
OPENBANK_TOKEN_URL = f"{OPENBANK_DOMAIN}/oauth/2.0/token"
accountinfo_api_tran_id = os.getenv("accountinfo_api_tran_id")
accountinfo_list_num = os.getenv("accountinfo_list_num")

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
  return render_template('index.html')

@app.route("/auth/")
def auth():
  state = generate_secure_key(32)
  ## 계좌통합조회 사용여부 : 'Y' 로 설정하는 경우, 에러 발생
  accountinfo_yn = 'N'
  params = {
    "response_type": "code",
    "client_id": OPENBANK_CLIENT_ID,
    "redirect_uri": OPENBANK_REDIRECT_URI,
    "scope": "login inquiry transfer",  # 필요한 권한 범위 지정
    "state": state,  # CSRF 방지용 랜덤 문자열
    "auth_type": "0",  # 0:최초인증, 1:재인증, 2:인증생략
    "authorized_cert_yn": "N",  # 금융/공인인증서 사용여부
    "accountinfo_yn": accountinfo_yn,
    "accountinfo_api_tran_id":accountinfo_api_tran_id if accountinfo_yn == 'Y' else '',
    "accountinfo_list_num": accountinfo_list_num if accountinfo_yn == 'Y' else '',
  }
  # 쿼리 파라미터 구성
  query_string = "&".join([f"{k}={v}" for k, v in params.items()])
  auth_url = f"{OPENBANK_DOMAIN}/oauth/2.0/authorize?{query_string}"
  print(query_string)
  return redirect(auth_url)

@app.route("/auth/callback/")
def auth_callback():
  """
  2단계: 인증 코드(code)를 받아 Access Token으로 교환
  """
  code = request.args.get("code")
  state = request.args.get("state")
  #client_info = request.args.get("client_info")
  scope = request.args.get("scope")
  error = request.args.get("error")
  error_description = request.args.get("error_description")
  print('*** get_auth_callback ***')
  print(f'code:{code}')
  print(f'scope:{scope}')
  print(f'state:{state}')
  #print(f'client_info:{client_info}')
  print(f'error:{error}')
  print(f'error_description:{error_description}')
  result_data = {
    'result': '0'
  }

  if not code: 
    result_data['message'] = "Authorization code not found"
    return render_template('auth_result.html', result=result_data['result'], message=result_data['message'])

  params = {
    "code": code,
    "client_id": OPENBANK_CLIENT_ID,
    "client_secret": OPENBANK_CLIENT_SECRET,
    "redirect_uri": OPENBANK_REDIRECT_URI,
    "grant_type": "authorization_code"
  }
  
  user_seq_no = ''
  user_access_token = ''
  response = requests.post(OPENBANK_TOKEN_URL, data=params)
  response.raise_for_status()
  if response.status_code == 200:
    token_data = response.json()
    print('사용자 토큰발급 (3-legged) :', token_data)
    user_seq_no = token_data['user_seq_no']
    user_access_token = token_data['access_token']
    token_data['code'] = code
    with open('사용자_토큰_정보.json', 'w', encoding='utf-8') as f:
      f.write(json.dumps(token_data))
      f.close()
  print(f'====== user_seq_no : {user_seq_no}')
  print(f'====== user_access_token : {user_access_token}')
  
  params = {
    "client_id": OPENBANK_CLIENT_ID,
    "client_secret": OPENBANK_CLIENT_SECRET,
    "scope": "oob",
    "grant_type": "client_credentials"
  }
  
  org_access_token = ''
  response = requests.post(OPENBANK_TOKEN_URL, data=params)
  response.raise_for_status()
  if response.status_code == 200:
    token_data = response.json()
    print('자체인증 이용기관 토큰발급 (2-legged) :', token_data)
    org_access_token = token_data['access_token']
    with open('자체인증_이용기관_토큰_정보.json', 'w', encoding='utf-8') as f:
      f.write(json.dumps(token_data))
      f.close()
  print(f'====== org_access_token : {org_access_token}')

  if user_access_token and user_seq_no:
    user_data = get_user_data(user_access_token, user_seq_no)
    if not user_data:
      # 사용자 등록
      set_user_data(org_access_token)
    else:
      if user_data['res_list'] and len(user_data['res_list']) > 0:
        print('\n======== 계좌정보 ========\n', user_data['res_list'][0])
        result_data['bank_name'] = user_data['res_list'][0]['bank_name']
        #if user_data['res_list'][0]['account_num']:
        #  result_data['account_num'] = user_data['res_list'][0]['account_num']
        if user_data['res_list'][0]['account_num_masked']:
          result_data['account_num_masked'] = user_data['res_list'][0]['account_num_masked']
        result_data['account_holder_name'] = user_data['res_list'][0]['account_holder_name']

    result_data['result'] = '1'
  
  return render_template('auth_result.html', data=result_data)

# 사용자계좌등록 (자체인증 이용기관용)
@app.route("/user/register/", methods=['POST'])
def user_register(access_token, register_account_num, register_account_seq, 
                  user_info, user_name, user_ci, user_email):
  inquiry_data = set_user_data(access_token, register_account_num, register_account_seq, 
                               user_info, user_name, user_ci, user_email, 'inquiry')
  transfer_data = set_user_data(access_token, register_account_num, register_account_seq, 
                               user_info, user_name, user_ci, user_email, 'transfer')
  return {
    'success': True if inquiry_data and transfer_data else False
  }

def set_user_data(access_token, register_account_num, register_account_seq, 
                  user_info, user_name, user_ci, user_email, scope):
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': f'Bearer {access_token}',
  }
  params = {
    "bank_tran_id": accountinfo_api_tran_id,
    "bank_code_std": accountinfo_list_num,
    "register_account_num": register_account_num,
    "register_account_seq": register_account_seq,
    "user_info": user_info,
    "user_name": user_name,
    "user_ci": user_ci,
    "user_email": user_email,
    "scope": scope,
    "info_prvd_agmt_yn": "Y",
    "wd_agmt_yn": "Y",
    "agmt_data_type": "3"
  }
  
  url = f'{OPENBANK_DOMAIN}/v2.0/user/register'
  response = requests.post(url, data=params, headers=headers)
  response.raise_for_status()
  user_data = None
  if response.status_code == 200:
    user_data = response.json()
    print('사용자 정보 :', user_data)
    if user_data and user_data['user_ci']:
      with open('사용자_정보.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(user_data))
        f.close()
  
  return user_data

# 사용자 정보 조회 후 파일로 저장
def get_user_data(access_token, user_seq_no):
  print('*** get_user_data ***')
  print(f'====== access_token : {access_token}')
  print(f'====== user_seq_no : {user_seq_no}')
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': f'Bearer {access_token}'
  }
  print(headers)
  url = f"{OPENBANK_DOMAIN}/v2.0/user/me?user_seq_no={user_seq_no}"
  response = requests.get(url, headers=headers)
  response.raise_for_status()
  user_data = None
  if response.status_code == 200:
    user_data = response.json()
    print('사용자 정보 :', user_data)
    if user_data and user_data['user_ci']:
      if user_data['res_list'] and len(user_data['res_list']) > 1:
        user_data['res_cnt'] = 1
        del user_data['res_list'][1:]
      with open('사용자_정보.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(user_data))
        f.close()
  return user_data

if __name__ == "__main__":
    # http://localhost:5050
    app.run(host="0.0.0.0", port=5050, debug=True)
