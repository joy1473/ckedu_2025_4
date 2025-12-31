###########################################################################
## 오픈뱅킹 기반 회원가입/조회: 은행/증권 계좌 연동으로 간편 가입. 거래내역 통합 조회
###########################################################################
import requests
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import secrets
import string

# Logger 설정
logging.basicConfig(
  format='%(asctime)s %(levelname)s:%(message)s',
  level=logging.DEBUG,
  datefmt='%m/%d/%Y %I:%M:%S %p',
)
logger = logging.getLogger()
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)
log_file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs/app_1.log'))
logger.debug(f"log_file_name={log_file_name}")
file_handler = logging.FileHandler(filename=log_file_name)
logger.addHandler(file_handler)

# .env 파일에서 정보를 로드합니다.
load_dotenv()
# 금융결제원 설정 값 (오픈뱅킹 포털에서 발급받은 값 입력)
OPENBANK_CLIENT_ID = os.getenv("OPENBANK_CLIENT_ID")
OPENBANK_CLIENT_SECRET = os.getenv("OPENBANK_CLIENT_SECRET")
logger.debug(f"OPENBANK_CLIENT_ID={OPENBANK_CLIENT_ID}")
logger.debug(f"OPENBANK_CLIENT_SECRET={OPENBANK_CLIENT_SECRET}")
OPENBANK_DOMAIN = "https://openapi.openbanking.or.kr"
# 인터넷 회선 기반 API
OPENBANK_DOMAIN = "https://openapi.openbanking.or.kr"
# 테스트 API
OPENBANK_DOMAIN = "https://testapi.openbanking.or.kr"
OPENBANK_REDIRECT_URI = "http://localhost:5050/auth/callback/"
OPENBANK_TOKEN_URL = f"{OPENBANK_DOMAIN}/oauth/2.0/token"
#accountinfo_api_tran_id = os.getenv("accountinfo_api_tran_id")
#accountinfo_list_num = os.getenv("accountinfo_list_num")

def get_user_info(in_user_id: str):
  """사용자 정보 반환 : MongoDB 연결 필요
  
  Args:
    in_user_id (str): 사용자ID (필수)
  
  Returns:
    out_code (str): 인증시 받은 코드
    out_access_token (str): 오픈뱅킹 발급 토큰
    out_user_name (str): 오픈뱅킹 발급 토큰
    out_user_seq_no (str): 오픈뱅킹 사용자일련번호
  """
  logger.debug('*** get_check ***')
  logger.debug(f'in_user_id:{in_user_id}')
  out_code = ''
  out_user_name = ''
  out_user_seq_no = ''
  out_access_token = ''
  return {
    "out_code": out_code,
    "out_access_token": out_access_token,
    "out_user_name": out_user_name,
    "out_user_seq_no": out_user_seq_no
  }

def get_account_list(in_user_id: str, in_sort_order_descending: bool | None = True):
  """오픈뱅킹 등록계좌조회
  
  Args:
    in_user_id (str): 사용자ID (필수)
    in_sort_order_descending (bool): 내림차순 정렬 여부 (디폴트 True)
  
  Returns:
    out_success (bool): 성공 여부
    out_message (str): 에러 메세지
    out_list (list): 계좌 목록
  """
  logger.debug('*** get_account_list ***')
  logger.debug(f'in_user_id:{in_user_id}')
  logger.debug(f'in_sort_order_descending:{in_sort_order_descending}')
  
  result_data = {
    'out_success': False
  }
  
  # 사용자ID가 빈 값일 때 오류
  if not in_user_id: 
    result_data['out_message'] = "in_user_id not found"
    return result_data
  
  # 사용자 정보 조회
  user_data = get_user_info(in_user_id)
  access_token = user_data['out_access_token']
  user_seq_no = user_data['out_user_seq_no']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'user_seq_no:{user_seq_no}')
  sort_order = 'D' if in_sort_order_descending else 'A'

  headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json; charset=UTF-8'
  }
  # user_seq_no Y AN(10) 사용자일련번호
  # include_cancel_yn Y A(1) 해지계좌포함여부
  # - ‘Y’:해지계좌포함, ‘N’:해지계좌불포함
  # sort_order Y A(1)
  # 정렬순서
  # - ‘D’:Descending, ‘A’:Ascending
  # - 정렬 기준: 조회서비스 동의일시, 출금서비스 동의일시 중 최근 값
  params = {
    "user_seq_no": user_seq_no,
    "include_cancel_yn": "N",
    "sort_order": sort_order
  }
  
  query_string = "&".join([f"{k}={v}" for k, v in params.items()])
  url = f"{OPENBANK_DOMAIN}/v2.0/account/list?{query_string}"
  response = requests.get(url, headers=headers)

  if response.status_code == 200:
    result_data['out_success'] = True
    result_data['out_list'] = response.json()
  else:
    result_data['out_message'] = "오픈뱅킹 계좌통합조회 오류"
    #result_data['out_detail'] = response.json()

  return result_data

def get_accountinfo_list(in_user_id: str, in_inquiry_bank_type: str, in_trace_no: str, in_inquiry_record_cnt: str):
  """오픈뱅킹 계좌통합조회
  
  Args:
    in_user_id (str): 사용자ID (필수)
    in_inquiry_bank_type (str(1)): 금융기관 업권 구분 (필수 “1”:은행, “2”:상호금융기관, “4”:금융투자회사)
    in_trace_no (str(6)): 지정 번호 (필수). 조회하고자 하는 내역의 시작번호를 입력하며, 첫 요청시에는 ‘1’을 입력해야 함.
    in_inquiry_record_cnt (str): 조회 건수 (필수). 한 번에 조회하려는 데이터 건수를 입력하며, 최대 조회 가능한 건수는 30 건임.
  
  Returns:
    out_success (bool): 성공 여부
    out_message (str): 에러 메세지
    out_list (list): 계좌 목록
  """
  logger.debug('*** get_accountinfo_list ***')
  logger.debug(f'in_user_id:{in_user_id}')
  logger.debug(f'in_inquiry_bank_type:{in_inquiry_bank_type}')
  logger.debug(f'in_trace_no:{in_trace_no}')
  logger.debug(f'in_inquiry_record_cnt:{in_inquiry_record_cnt}')
  
  result_data = {
    'out_success': False
  }
  
  # 사용자ID가 빈 값일 때 오류
  if not in_user_id: 
    result_data['out_message'] = "in_user_id not found"
    return result_data
  
  # 사용자 정보 조회
  user_data = get_user_info(in_user_id)
  access_token = user_data['out_access_token']
  auth_code = user_data['out_code']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'auth_code:{auth_code}')

  headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json; charset=UTF-8'
  }
  params = {
    "auth_code": auth_code,
    "inquiry_bank_type": in_inquiry_bank_type,
    "trace_no": in_trace_no,
    "inquiry_record_cnt": in_inquiry_record_cnt
  }
  
  url = f"{OPENBANK_DOMAIN}/v2.0/accountinfo/list"
  response = requests.post(url, data=params, headers=headers)

  if response.status_code == 200:
    result_data['out_success'] = True
    result_data['out_list'] = response.json()
  else:
    result_data['out_message'] = "오픈뱅킹 계좌통합조회 오류"
    #result_data['out_detail'] = response.json()

  return result_data

def get_account_balance(in_user_id: str, 
                        in_bank_tran_id: str, in_bank_code_std: str, in_account_num: str):
  """오픈뱅킹 잔액조회
  
  Args:
    in_user_id (str): 사용자ID (필수)
    in_bank_tran_id (str(20)): 거래고유번호(참가기관) (필수)
    in_bank_code_std (str(3)): 개설기관.표준코드 (필수)
    in_account_num (str(16)): 계좌번호 (필수)
  
  Returns:
    out_success : bool 성공 여부
    out_message (str): 에러 메세지
    out_balance_amt (int(13)): 계좌잔액(-금액가능)
    out_available_amt (int(12)): 출금가능금액
  """
  logger.debug('*** get_account_balance ***')
  logger.debug(f'in_user_id:{in_user_id}')
  logger.debug(f'in_bank_tran_id::{in_bank_tran_id:}')
  logger.debug(f'in_bank_code_std:{in_bank_code_std}')
  result_data = {
    'out_success': False
  }
  
  # 사용자ID가 빈 값일 때 오류
  if not in_user_id: 
    result_data['out_message'] = "in_user_id not found"
    return result_data
  
  # 사용자 정보 조회
  user_data = get_user_info(in_user_id)
  access_token = user_data['out_access_token']
  user_seq_no = user_data['out_user_seq_no']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'user_seq_no:{user_seq_no}')
  tran_dtime = format_datetime()
  
  headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json; charset=UTF-8'
  }
  # bank_tran_id Y AN(20) 거래고유번호(참가기관) - 「3.11. 거래고유번호(참가기관) 생성 안내」 참조
  # bank_code_std Y AN(3) 개설기관.표준코드
  # account_num Y AN(16) 계좌번호
  # account_seq N AN(3) 회차번호
  # user_seq_no Y AN(10) 사용자일련번호
  # tran_dtime Y N(14) 요청일시
  # req_from_offline_yn N A(1) 오프라인 영업점으로 부터의 요청 여부
  # - Y/N 으로 설정하며, 공란인 경우 N 으로 간주함
  params = {
    "bank_tran_id": in_bank_tran_id,
    "bank_code_std": in_bank_code_std,
    "account_num": in_account_num,
    "user_seq_no": user_seq_no,
    "tran_dtime": tran_dtime,
    "req_from_offline_yn": "N"
  }
  
  url = f"{OPENBANK_DOMAIN}/v2.0/account/balance/acnt_num"
  response = requests.post(url, data=params, headers=headers)
  
  if response.status_code == 200:
    data = response.json()
    if data["rsp_code"] == "A0000":
      result_data['out_success'] = True
      result_data['out_balance_amt'] = int(data["balance_amt"]) if data["balance_amt"] else 0
      result_data['out_available_amt'] = int(data["available_amt"]) if data["available_amt"] else 0
  else:
    result_data['out_message'] = "오픈뱅킹 잔액조회 오류"
    #result_data['out_detail'] = response.json()

  return result_data
  
async def get_transaction_list(in_user_id: str, in_bank_tran_id: str, in_bank_code_std: str,
                               in_account_num: str, in_inquiry_type: str, 
                               in_from_date: str, in_to_date: str, 
                               in_befor_inquiry_trace_info: str | None = None,
                               in_sort_order_descending: bool | None = True):
  """오픈뱅킹 거래내역조회
  
  Args:
    in_user_id (str): 사용자ID (필수)
    in_bank_tran_id (str(20)): 거래고유번호(참가기관) (필수)
    in_bank_code_std (str(3)): 개설기관.표준코드 (필수)
    in_account_num (str(16)): 계좌번호 (필수)
    in_inquiry_type (str(1)): 조회구분코드 (필수 "A”:All, "I”:입금, "O”:출금)
    in_from_date (str(8)): 조회시작일자 (필수)
    in_to_date (str(8)): 조회종료일자 (필수)
    in_befor_inquiry_trace_info (str(20)): 직전조회추적정보(다음페이지 존재여부에 따라 값 설정)
    in_sort_order_descending (bool): 내림차순 정렬 여부 (디폴트 True)
  
  Returns:
    out_success (bool): 성공 여부
    out_message (str): 에러 메세지
    out_page_record_cnt (str(2)): 현재페이지 레코드건수 - 한 페이지는 최대 25건 가능
    out_next_page_yn (str(1)): 다음페이지 존재여부
    out_befor_inquiry_trace_info (str(20)): 직전조회추적정보
    out_res_list (list): 조회된 거래내역
  """
  logger.debug('*** get_transaction_list ***')
  logger.debug(f'in_user_id:{in_user_id}')
  logger.debug(f'in_bank_tran_id::{in_bank_tran_id:}')
  logger.debug(f'in_bank_code_std:{in_bank_code_std}')
  logger.debug(f'in_account_num:{in_account_num}')
  logger.debug(f'in_inquiry_type:{in_inquiry_type}')
  logger.debug(f'in_from_date:{in_from_date}')
  logger.debug(f'in_to_date:{in_to_date}')
  logger.debug(f'in_befor_inquiry_trace_info:{in_befor_inquiry_trace_info}')
  logger.debug(f'in_sort_order_descending:{in_sort_order_descending}')
  result_data = {
    'out_success': False
  }
  
  # 사용자ID가 빈 값일 때 오류
  if not in_user_id: 
    result_data['out_message'] = "in_user_id not found"
    return result_data
  
  # 사용자 정보 조회
  user_data = get_user_info(in_user_id)
  access_token = user_data['out_access_token']
  user_seq_no = user_data['out_user_seq_no']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'user_seq_no:{user_seq_no}')
  sort_order = 'D' if in_sort_order_descending else 'A'
  tran_dtime = format_datetime()
  
  headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json; charset=UTF-8'
  }
  # bank_tran_id Y AN(20) 거래고유번호(참가기관) - 「3.11. 거래고유번호(참가기관) 생성 안내」 참조
  # bank_code_std Y AN(3) 개설기관.표준코드
  # account_num Y AN(16) 계좌번호
  # account_seq N AN(3) 회차번호
  # user_seq_no Y AN(10) 사용자일련번호
  # inquiry_type Y A(1) 조회구분코드
  # - "A”:All, "I”:입금, "O”:출금
  # inquiry_base Y A(1) 조회기준코드주 1) - "D”:일자, "T”:시간
  # from_date Y N(8) 조회시작일자
  # from_time N N(6) 조회시작시간주 1)
  # to_date Y N(8) 조회종료일자
  # to_time N N(6) 조회종료시간주 1)
  # sort_order Y A(1) 정렬순서
  # D:Descending, A:Ascending
  # tran_dtime Y N(14) 요청일시
  # befor_inquiry_trace_info N AN(20)
  # 직전조회추적정보
  # - 다음 페이지 요청 시에 직전 조회의 응답에서 얻은 값을그대로 세팅, 다음 페이지 요청이 아닌 경우에는 파라미터
  # 자체를 설정하지 않음
  # req_from_offline_yn N A(1) 오프라인 영업점으로 부터의 요청 여부
  # - Y/N 으로 설정하며, 공란인 경우 N 으로 간주함
  params = {
    "bank_tran_id": in_bank_tran_id,
    "bank_code_std": in_bank_code_std,
    "account_num": in_account_num,
    "inquiry_type": in_inquiry_type,
    "inquiry_base": "D",
    "from_date": in_from_date,
    "to_date": in_to_date,
    "sort_order": sort_order,
    "tran_dtime": tran_dtime,
    "req_from_offline_yn": "N"
  }
  if in_befor_inquiry_trace_info:
    params['befor_inquiry_trace_info'] = in_befor_inquiry_trace_info
  
  url = f"{OPENBANK_DOMAIN}/v2.0/account/transaction_list/acnt_num"
  response = requests.post(url, data=params, headers=headers)
  
  if response.status_code == 200:
    data = response.json()
    if data["rsp_code"] == "A0000":
      result_data['out_success'] = True
      result_data['out_page_record_cnt'] = data["page_record_cnt"]
      result_data['out_next_page_yn'] = data["next_page_yn"]
      result_data['out_befor_inquiry_trace_info'] = data["befor_inquiry_trace_info"]
      result_data['out_res_list'] = data["res_list"]
  else:
    result_data['out_message'] = "오픈뱅킹 거래내역조회 오류"
    #result_data['out_detail'] = response.json()

  return result_data

def get_account_balance(in_user_id: str, in_bank_tran_id: str, in_bank_code_std: str, 
                        in_account_num: str, in_account_holder_info_type: str):
  """오픈뱅킹 계좌실명조회
  
  Args:
    in_user_id (str): 사용자ID (필수)
    in_bank_tran_id (str(20)): 거래고유번호(참가기관) (필수)
    in_bank_code_std (str(3)): 개설기관.표준코드 (필수)
    in_account_num (str(16)): 계좌번호 (필수)
    in_account_holder_info_type (str(1)): 예금주 실명번호 구분코드 (필수)
        코드            실명번호
    -----------------------------------------------------
        " "(SPACE)   | 생년월일(실명번호 앞 6 자리)
        "1"          | 주민등록번호
        "2"          | 외국인등록번호
        "3"          | 국내거소신고번호
        "4"          | 조합주민번호
        "5"          | 여권번호
        "6"          | 사업자등록번호
        "E"          | 기타 (외국인투자등록증번호, 외국인투자신고수리서(인가서)번호 등)
        "N"          | 실명번호 구분코드 및 실명번호 검사 생략 (예금주 실명번호 세팅 안함)
  
  Returns:
    out_success : bool 성공 여부
    out_message (str): 에러 메세지
    out_account_holder_info (str(13)): 계좌잔액(-금액가능)
    out_account_holder_name (str(20)): 예금주성명
    out_account_type (str(1)): 계좌종류 (“1”:수시입출금, “2”:예적금, “6”:수익증권, “T”:종합계좌)
  """
  logger.debug('*** get_account_balance ***')
  logger.debug(f'in_user_id:{in_user_id}')
  logger.debug(f'in_bank_tran_id::{in_bank_tran_id:}')
  logger.debug(f'in_bank_code_std:{in_bank_code_std}')
  logger.debug(f'in_account_num:{in_account_num}')
  logger.debug(f'in_account_holder_info_type:{in_account_holder_info_type}')
  result_data = {
    'out_success': False
  }
  
  # 사용자ID가 빈 값일 때 오류
  if not in_user_id: 
    result_data['out_message'] = "in_user_id not found"
    return result_data
  
  # 사용자 정보 조회
  user_data = get_user_info(in_user_id)
  access_token = user_data['out_access_token']
  user_seq_no = user_data['out_user_seq_no']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'user_seq_no:{user_seq_no}')
  tran_dtime = format_datetime()
  
  headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json; charset=UTF-8'
  }
  # bank_tran_id Y AN(20) 거래고유번호(참가기관) - 「3.11. 거래고유번호(참가기관) 생성 안내」 참조
  # bank_code_std Y AN(3) 개설기관.표준코드
  # account_num Y AN(16) 계좌번호
  # account_seq N AN(3) 회차번호
  # user_seq_no Y AN(10) 사용자일련번호
  # tran_dtime Y N(14) 요청일시
  # req_from_offline_yn N A(1) 오프라인 영업점으로 부터의 요청 여부
  # - Y/N 으로 설정하며, 공란인 경우 N 으로 간주함
  params = {
    "bank_tran_id": in_bank_tran_id,
    "bank_code_std": in_bank_code_std,
    "account_num": in_account_num,
    "account_holder_info_type": in_account_holder_info_type,
    "tran_dtime": tran_dtime
  }
  
  url = f"{OPENBANK_DOMAIN}/v2.0/inquiry/real_name"
  response = requests.post(url, data=params, headers=headers)
  
  if response.status_code == 200:
    data = response.json()
    if data["rsp_code"] == "A0000":
      result_data['out_success'] = True
      result_data['out_account_holder_info'] = data["account_holder_info"]
      result_data['out_account_holder_name'] = data["account_holder_name"]
      result_data['out_account_type'] = data["account_type"]
  else:
    result_data['out_message'] = "오픈뱅킹 계좌실명조회 오류"
    #result_data['out_detail'] = response.json()

  return result_data
  
def get_account_cancel(in_user_id: str, in_bank_tran_id: str):
  """오픈뱅킹 계좌해지
  
  Args:
  # in_user_id (str): 사용자ID (옵션)
  # in_access_token : 오픈뱅킹 발급 토큰 (옵션)
  
  Returns:
  """
  logger.debug('*** get_account_cancel ***')
  logger.debug(f'in_user_id:{in_user_id}')
  result_data = {
    'out_success': False
  }
  
  # 사용자ID가 빈 값일 때 오류
  if not in_user_id: 
    result_data['out_message'] = "in_user_id not found"
    return result_data
  
  # 사용자 정보 조회
  user_data = get_user_info(in_user_id)
  access_token = user_data['out_access_token']
  user_seq_no = user_data['out_user_seq_no']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'user_seq_no:{user_seq_no}')
  
  # 조회서비스 해지
  inquiry_data = private_auth_account_cancel(in_user_id, in_bank_tran_id, 'inquiry')
  inquiry_result = 0
  if inquiry_data['out_success']:
    inquiry_result = 1
  # 출금서비스 해지
  transfer_data = private_auth_account_cancel(in_user_id, in_bank_tran_id, 'transfer')
  transfer_result = 0
  if transfer_data['out_success']:
    transfer_result = 1
  return result_data

def private_auth_account_cancel(in_user_id: str, in_bank_tran_id: str, in_scope: str):
  """오픈뱅킹 계좌해지를 요청 처리

  Args:
    in_user_id (str): 사용자ID (필수)
    in_bank_tran_id (str(20)): 거래고유번호(참가기관) (필수)
    in_scope (str(3)): 개설기관.표준코드 (필수)
  
  Returns:
  """
  result_data = {
    'out_success': False
  }
  
  # 사용자ID가 빈 값일 때 오류
  if not in_user_id: 
    result_data['out_message'] = "in_user_id not found"
    return result_data
  
  # 사용자 정보 조회
  user_data = get_user_info(in_user_id)
  access_token = user_data['out_access_token']
  user_seq_no = user_data['out_user_seq_no']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'user_seq_no:{user_seq_no}')
  
  headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json; charset=UTF-8'
  }
  # bank_tran_id Y AN(20) 거래고유번호(참가기관) - 「3.11. 거래고유번호(참가기관) 생성 안내」 참조
  # scope Y
  # 서비스구분
  # - ‘inquiry’: 조회서비스
  # - ‘transfer’: 출금서비스
  # fintech_use_num N AN(24) 핀테크이용번호
  # user_seq_no N AN(10) 사용자일련번호
  # bank_code_std N AN(3) 계좌개설기관.표준코드
  # account_num N AN(16) 계좌번호
  # account_seq N AN(3)
  # 회차번호
  # - 출금서비스(transfer)용 계좌 해지 시 회차번호가 설정되는
  # 경우 오류로 응답
  params = {
    "bank_tran_id": in_bank_tran_id,
    "scope": in_scope
  }
  
  
  url = f"{OPENBANK_DOMAIN}/v2.0/account/cancel"
  response = requests.post(url, data=params, headers=headers)
  
  if response.status_code != 200:
    #return {"error": "Failed to get access token", "details": response.json()}
    return {
      "message": "Failed to get access token",
      "details": response.json(),
      "result": "0"
    }
  # api_tran_id aNS(40) 거래고유번호(API)
  # api_tran_dtm N(17) 거래일시(밀리세컨드)
  # rsp_code AN(5) 응답코드(API)
  # rsp_message AH(300) 응답메시지(API)
  # bank_tran_id AN(20) 거래고유번호(참가기관)
  # bank_tran_date N(8) 거래일자(참가기관)
  # bank_code_tran AN(3) 응답코드를 부여한 참가기관.표준코드
  # bank_rsp_code AN(3) 응답코드(참가기관)
  # bank_rsp_message AH(100) 응답메시지(참가기관)
  data = response.json()
  if (data['rsp_code'] == "A0000" or data['rsp_code'] == "551" or data['rsp_code'] == "555" or data['rsp_code'] == "556"):
    result_data['out_success'] = True
  
  return result_data

def format_datetime(format: str | None):
  """현재 날짜를 형식에 맞춰 문자로 반환  
  
  Args:
    format (str): 날짜 형식
  
  Returns:
    strftime (str): 날짜
  """
  if not format:
    format = '%Y%m%d%H%M%S'
  now = datetime.now()
  return now.strftime(format=format)

def generate_secure_key(length=12):
  """안전한 랜덤 키 생성 함수 (문자 포함)
  
  Args:
    length (nt): 문자 길이
  
  Returns:
    random_key (str): 랜덤 키
  """
  # 랜덤 문자열 생성 (문자, 숫자, 특수문자 포함)
  alphabet = string.ascii_letters + string.digits
  random_key = ''.join(secrets.choice(alphabet) for i in range(length))
  return random_key
