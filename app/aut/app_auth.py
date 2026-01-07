###########################################################################
## 오픈뱅킹 기반 회원가입/조회: 은행/증권 계좌 연동으로 간편 가입. 거래내역 통합 조회
###########################################################################
import requests
import os
from dotenv import load_dotenv
import logging
from aut.api_utils import format_datetime
from fastapi import FastAPI

# Logger 설정
logging.basicConfig(
  format='%(asctime)s %(levelname)s:%(message)s',
  level=logging.DEBUG,
  datefmt='%m/%d/%Y %I:%M:%S %p',
)
logger = logging.getLogger()
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)
log_file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), f'logs/app_auth_{format_datetime("%Y%m%d")}.log'))
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
MONGO_URI = os.getenv('MONGO_URI')

user_data = {}

# FastAPI 앱 생성
APP_AUTH = FastAPI(title="Auth API", version="1.0.0")

def get_user_info(in_user_id: str):
  """
  사용자 정보 반환 : MongoDB 연결 필요
  
  Args:
    in_user_id (str): 사용자ID (필수)
  
  Returns:
    out_code (str): 인증시 받은 코드
    out_login_access_token (str): 오픈뱅킹 발급 토큰 (scope = login)
    out_org_access_token (str): 오픈뱅킹 발급 토큰 (scope = oob)
    out_user_name (str): 이름
    out_user_ci (str): 사용자 CI(Connect Info)
    out_user_email (str): 이메일주소
    out_user_seq_no (str): 오픈뱅킹 사용자일련번호
    out_auth_code (str): 어카운트인포 계좌통합조회에 필요한 키
    out_fintech_use_num (str): 핀테크이용번호
    out_account_num (str): 계좌번호
  """
  logger.debug('*** get_check ***')
  logger.debug(f'in_user_id:{in_user_id}')
  
  out_code = ''
  out_user_name = ''
  out_user_ci = ''
  out_user_email = ''
  out_user_seq_no = ''
  out_login_access_token = ''
  out_org_access_token = ''
  out_auth_code = ''
  out_fintech_use_num = ''
  out_bank_code_std = ''

  if in_user_id in user_data:
    out_code = user_data[in_user_id]['code']
    out_login_access_token = user_data[in_user_id]['login_access_token']
    out_org_access_token = user_data[in_user_id]['org_access_token']
    out_user_name = user_data[in_user_id]['user_name']
    out_user_ci = user_data[in_user_id]['user_ci']
    out_user_email = user_data[in_user_id]['user_email']
    out_user_seq_no = user_data[in_user_id]['user_seq_no']
    out_auth_code = user_data[in_user_id]['auth_code']
    out_fintech_use_num = user_data[in_user_id]['fintech_use_num']
    out_bank_code_std = user_data[in_user_id]['bank_code_std']
  else:
    pass
    # client = MongoClient(
    #   MONGO_URI, 
    #   serverSelectionTimeoutMS=5000
    # )
    # try:
    #   database = client.get_database("mock_trading_db")
    #   movies = database.get_collection("users")
    #   # Query for a movie that has the title 'Back to the Future'
    #   query = { "title": "Back to the Future" }
    #   movie = movies.find_one(query)
    #   print(movie)
    # except Exception as e:
    #   raise Exception("Unable to find the document due to the following error: ", e)
    # finally:
    #   if client:
    #     client.close()

  return {
    "out_code": out_code,
    "out_login_access_token": out_login_access_token,
    "out_org_access_token": out_org_access_token,
    "out_user_name": out_user_name,
    "out_user_ci": out_user_ci,
    "out_user_email": out_user_email,
    "out_user_seq_no": out_user_seq_no,
    "out_auth_code": out_auth_code,
    "out_fintech_use_num": out_fintech_use_num,
    "out_bank_code_std": out_bank_code_std
  }

def get_account_list(in_user_id: str, in_sort_order_descending: bool | None = True):
  """
  오픈뱅킹 등록계좌조회 : scope = login, sa
  설명 : 오픈뱅킹센터에 등록된 사용자의 계좌목록을 조회합니다. 해지계좌 포함여부 및 정렬순서를 지정할 수 있습니다.
  
  Args:
    in_user_id (str): 사용자ID (필수)
    in_sort_order_descending (bool): 내림차순 정렬 여부 (디폴트 True)
  
  Returns:
    out_success (bool): 성공 여부
    out_message (str): 에러 메세지
    out_cnt (int): 사용자 등록계좌 개수
    out_list (list): 사용자 등록계좌 목록
      --fintech_use_num (str): 핀테크이용번호
      --account_alias (str): 계좌별명(Alias)
      --bank_code_std (str): 출금(개설)기관.대표코드
      --bank_code_sub (str): 출금(개설)기관.점별코드
      --bank_name (str): 출금(개설)기관명
      --savings_bank_name (str): 개별저축은행명 - 계좌 개설기관이 저축은행(bank_code_tran=‘050’) 인 경우에만 제공되며, 계좌의 개별저축은행명이 확인되지 않는 경우에는 공란(빈값)이 전송됨.
      --account_num (선택) (str): 계좌번호주 1)
      --account_num_masked (str): 마스킹된 출력용 계좌번호
      --account_seq (str): 회차번호주 1) - 동일 계좌번호 내에서 회차별 특성이 상이한 상품인 경우 회차번호가 제공되며, 대상 계좌는 예금으로 한정함.
      --account_holder_name (str): 계좌예금주명
      --account_holder_type (str): 계좌구분(P:개인)
      --account_type (str): 계좌종류
                            - ‘1’:수시입출금, ‘2’:예적금, ‘6’:수익증권, ‘T’:종합계좌
                            - 2020.12월부터 등록하는 계좌에 대해 추가로 제공하는 정보로, 그 이전에 등록된 계좌에 대해서는 해당 정보가 제공되지 않을 수 있음.
      --inquiry_agree_yn (str): 조회서비스 동의여부
      --inquiry_agree_dtime (str): 조회서비스 동의일시
      --transfer_agree_yn (str): 출금서비스 동의여부
      --transfer_agree_dtime (str): 출금서비스 동의일시
      --account_state (str): 계좌상태 - ‘01’:사용, ‘09’:해지
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
  access_token = user_data['out_login_access_token']
  user_seq_no = user_data['out_user_seq_no']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'user_seq_no:{user_seq_no}')
  sort_order = 'D' if in_sort_order_descending else 'A'

  headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json; charset=UTF-8'
  }
  params = {
    "user_seq_no": user_seq_no,
    "include_cancel_yn": "N",
    "sort_order": sort_order
  }
  
  query_string = "&".join([f"{k}={v}" for k, v in params.items()])
  url = f"{OPENBANK_DOMAIN}/v2.0/account/list?{query_string}"
  response = requests.get(url, headers=headers)
  response.raise_for_status()

  if response.status_code == 200:
    data = response.json()
    if data['rsp_code'] and data['rsp_code'] == 'A0000':
      result_data['out_success'] = True
      result_data['out_cnt'] = int(data['res_cnt'])
      result_data['out_list'] = data['res_list']
  else:
    result_data['out_message'] = "오픈뱅킹 등록계좌조회 오류"
    #result_data['out_detail'] = response.json()

  return result_data

def get_accountinfo_list(in_user_id: str, in_inquiry_bank_type: str, in_trace_no: str, in_inquiry_record_cnt: str):
  """
  어카운트인포 계좌통합조회 : scope = sa, oob
  설명 : 사용자정보확인 API의 처리 결과로 수신한 키를 사용하여 고객의 계좌 리스트를 조회할 수 있습니다
  
  Args:
    in_user_id (str): 사용자ID (필수)
    in_inquiry_bank_type (str(1)): 금융기관 업권 구분 (필수 “1”:은행, “2”:상호금융기관, “4”:금융투자회사)
    in_trace_no (str(6)): 지정 번호 (필수). 조회하고자 하는 내역의 시작번호를 입력하며, 첫 요청시에는 ‘1’을 입력해야 함.
    in_inquiry_record_cnt (str(6)): 조회 건수 (필수). 한 번에 조회하려는 데이터 건수를 입력하며, 최대 조회 가능한 건수는 30 건임.

    auth_code Y 사용자정보확인으로 수신한 키
  
  Returns:
    out_success (bool): 성공 여부
    out_message (str): 에러 메세지
    out_ainfo_tran_id (str(12)): 전문관리번호
    out_ainfo_tran_date (str(8)): 거래일자(계좌통합)
    out_rsp_type (str(1)): 응답코드 부여 기관주 1) - “0”:계좌통합센터, “1”:금융기관
    out_ainfo_rsp_code (str(4)): 응답코드(계좌통합)주 1)
    out_ainfo_rsp_message (str(100)): 응답메시지(계좌통합)주 1)
    out_inquiry_bank_type (str(1)): 금융기관 구분
    out_exclude_cnt (str(2)): 조회 제외기관 수주 2)
    out_exclude_list (list): 조회 제외기관 목록
      --exclude_bank_code (str(3)): 조회 제외기관 코드주 3)
      --exclude_savings_bank_code (str(3)): 조회 제외기관 개별 저축은행코드주 4)
    out_org_ainfo_tran_id (str(12)): 조회 원거래 전문관리번호
    out_trace_no (str(6)): 지정 번호
    out_total_record_cnt (str(6)): 총 조회 건수주 5)
    out_page_record_cnt (str(6)): 현재 페이지 조회 건수
    out_res_list (list): 조회 계좌 목록
      --list_num (str(3)): 목록 순번주 15)
      --bank_code_std (str(3)): 개설기관 코드주 6)
      --activity_type (str(1)): 유형구분 - “A”:활동성계좌, “I”:비활동성계좌
      --account_type (str(1)): 계좌종류주 7)
      --account_num (str(20)): 계좌번호주 8)
      --account_num_masked (str(20)): 마스킹된 출력용 계좌번호주 15)
      --account_seq (str(2)): 회차번호주 9)
      --account_local_code (str(7)): 계좌 관리점 코드
      --account_issue_date (str(8)): 계좌개설일
      --maturity_date (str(8)): 만기일 (YYYYMMDD) - 만기일자가 있는 경우 세팅됨
      --last_tran_date (str(8)): 최종거래일주 10)
      --product_name (str(100)): 상품명(계좌명) -product_sub_name AH(10) 부기명주 12)
      --dormancy_yn (str(1)): 휴면계좌 여부주 13)
      --balance_amt (str(15)): 계좌잔액(-금액가능)주 14)
      --deposit_amt (str(15)): (금투사) 예수금 잔고 - 잔고 산출 기준 1, 2에 따른 원장 기준 예수금(CMA 평가 금액 포함) 잔고 정보를 수록
        * 원금 및 이자 등이 지급되어 원가화된 금액을 포함하며, 잔고 산출 기준 1, 2 외의 평가 기준(기준 환율 등)은 각 사 대고객 채널(HTS, MTS 등)에서 제공하는 기준과 동일하게 적용
        * 업권구분이 ‘4’(금투사)인 경우 수록
      --balance_calc_basis_1 (str(1)): (금투사) 잔고 산출 기준1 -“S”:결제 기준, “C”:체결 기준 *업권구분이 ‘4’(금투사)인 경우 수록
      --balance_calc_basis_2 (str(1)): (금투사) 잔고 산출 기준2 - “N”:순자산 기준(부채 반영), “C”:일반 기준(부채 미반영) * 업권구분이 ‘4’(금투사)인 경우 수록
      --investment_linked_yn (str(1)): (금투사) 투자재산 연계여부 - “Y”:투자재산 연계, “N”:해당 없음 * 업권구분이 ‘4’(금투사)인 경우 수록
      --bank_linked_yn (str(1)): (금투사) 은행 제휴 계좌 여부 - “Y”:은행 제휴 계좌, “N”:은행 제휴 계좌 아님 * 업권구분이 ‘4’(금투사)인 경우 수록
      --balance_after_cancel_yn (str(1)): (금투사) 해지 후 잔고 발생 여부 - “Y”:해지 후 잔고 발생, “N”:해당 없음 * 업권구분이 ‘4’(금투사)인 경우 수록
      --savings_bank_code (str(3)): 저축은행 코드 - 업권구분이 ‘2’(상호저축은행)인 경우 저축은행 코드 3자리 수록 - 「3.25. 계좌통합관리시스템 저축은행코드 안내」 참조 
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
  access_token = user_data['out_org_access_token']
  auth_code = user_data['out_auth_code']
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
  response.raise_for_status()

  if response.status_code == 200:
    data = response.json()
    if data['rsp_code'] and data['rsp_code'] == 'A0000':
      result_data['out_success'] = True
      result_data['out_cnt'] = int(data['res_cnt'])
      result_data['out_list'] = data['res_list']
  else:
    result_data['out_message'] = "어카운트인포 계좌통합조회 오류"
    #result_data['out_detail'] = response.json()

  return result_data

def get_account_balance(in_user_id: str, 
                        in_bank_tran_id: str, in_fintech_use_num: str, in_req_from_offline_yn: str):
  """
  오픈뱅킹 잔액조회 : scope = inquiry, sa
  설명 : 사용자 계좌의 잔액을 조회합니다. 계좌종류 및 상품명이 함께 전달됩니다. 등록된 핀테크이용번호로 요청하는 경우(/fin_num)와 실 계좌번호로 요청하는 경우(/acnt_num)의 두 가지 기능을 각각 제공합니다.
  
  Args:
    in_user_id (str): 사용자ID (필수)
    in_bank_tran_id (str(20)): 거래고유번호(참가기관) (필수)
    in_fintech_use_num (str(24)): 핀테크이용번호
    in_req_from_offline_yn (str(1)): 오프라인 영업점으로 부터의 요청 여부 - Y/N 으로 설정하며, 공란인 경우 N 으로 간주함
  
  Returns:
    out_success : bool 성공 여부
    out_message (str): 에러 메세지
    out_balance_amt (int(13)): 계좌잔액(-금액가능)
    out_available_amt (int(12)): 출금가능금액
  """
  logger.debug('*** get_account_balance ***')
  logger.debug(f'in_user_id:{in_user_id}')
  logger.debug(f'in_bank_tran_id::{in_bank_tran_id:}')
  logger.debug(f'in_fintech_use_num:{in_fintech_use_num}')
  logger.debug(f'in_req_from_offline_yn:{in_req_from_offline_yn}')
  result_data = {
    'out_success': False
  }
  
  # 사용자ID가 빈 값일 때 오류
  if not in_user_id: 
    result_data['out_message'] = "in_user_id not found"
    return result_data
  
  # 사용자 정보 조회
  user_data = get_user_info(in_user_id)
  access_token = user_data['out_login_access_token']
  if not in_fintech_use_num or in_fintech_use_num == '':
    in_fintech_use_num = user_data['out_fintech_use_num']
  logger.debug(f'access_token:{access_token}')
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
    "fintech_use_num": in_fintech_use_num,
    "tran_dtime": tran_dtime,
    "req_from_offline_yn": in_req_from_offline_yn
  }
  
  query_string = "&".join([f"{k}={v}" for k, v in params.items()])
  url = f"{OPENBANK_DOMAIN}/v2.0/account/balance/fin_num?{query_string}"
  response = requests.get(url, headers=headers)
  response.raise_for_status()
  print(f'status_code : {response.status_code}')
  
  if response.status_code == 200:
    data = response.json()
    print(data)
    if data["rsp_code"] == "A0000":
      result_data['out_success'] = True
      result_data['out_balance_amt'] = int(data["balance_amt"]) if data["balance_amt"] else 0
      result_data['out_available_amt'] = int(data["available_amt"]) if data["available_amt"] else 0
  else:
    result_data['out_message'] = "오픈뱅킹 잔액조회 오류"
    #result_data['out_detail'] = response.json()

  return result_data

async def get_transaction_list(in_user_id: str, in_bank_tran_id: str, in_fintech_use_num: str,
                               in_inquiry_type: str, in_inquiry_base: str, 
                               in_from_date: str, in_to_date: str, 
                               in_befor_inquiry_trace_info: str = '', in_req_from_offline_yn: str = 'N',
                               in_sort_order_descending: bool = True):
  """
  오픈뱅킹 거래내역조회 : scope = inquiry, sa
  설명 : 사용자가 등록한 계좌의 거래내역을 조회합니다. 등록된 핀테크이용번호로 요청하는 경우(/fin_num)와실 계좌번호로 요청하는 경우(/acnt_num)의 두 가지 기능을 각각 제공합니다.
  
  Args:
    in_user_id (str): 사용자ID (필수)
    in_bank_tran_id (str(20)): 거래고유번호(참가기관) (필수)
    in_fintech_use_num (str(24)): 핀테크이용번호 (필수)
    in_inquiry_type (str(1)): 조회구분코드 (필수) - “A”:All, “I”:입금, “O”:출금
    in_inquiry_base (str(1)): 조회기준코드주 (필수) 1) - “D”:일자, “T”:시간
    in_from_date (str(8)): 조회시작일자 (필수)
    in_to_date (str(8)): 조회종료일자 (필수)
    in_befor_inquiry_trace_info (str(20)): 직전조회추적정보 - 다음 페이지 요청 시에 직전 조회의 응답에서 얻은 값을그대로 세팅, 다음 페이지 요청이 아닌 경우에는 파라미터
    자체를 설정하지 않음
    in_req_from_offline_yn (str(1)): 오프라인 영업점으로 부터의 요청 여부 - Y/N 으로 설정하며, 공란인 경우 N 으로 간주함
    in_sort_order_descending (bool): 내림차순 정렬 여부 (디폴트 True)
  
  Returns:
    out_success (bool): 성공 여부
    out_message (str): 에러 메세지
    out_page_record_cnt (str(2)): 현재페이지 레코드건수 - 한 페이지는 최대 25건 가능
    out_next_page_yn (str(1)): 다음페이지 존재여부
    out_befor_inquiry_trace_info (str(20)): 직전조회추적정보
    out_res_list (list): 조회된 거래내역
      --tran_date N(8) 거래일자
      --tran_time N(6) 거래시간
      --inout_type AH(8) 입출금구분 - 입금, 출금, 지급, 기타 - 입출금구분이 ‘기타’인 경우에는 ‘거래금액’이 0원으로 세팅됨
      --tran_type AH(10) 거래구분 - 현금, 대체, 급여, 타행환, F/B출금 등 (참가기관에서 직접 세팅)
      --print_content AH(20) 통장인자내용 - 1 원 인증 등 이체용도가 인증(AU)인 경우 ‘****’로 조회될 수 있음.
      --tran_amt N(12) 거래금액
      --after_balance_amt SN(13) 거래후잔액(-금액가능)
      --branch_name AH(20) 거래점명
  """
  logger.debug('*** get_transaction_list ***')
  logger.debug(f'in_user_id:{in_user_id}')
  logger.debug(f'in_bank_tran_id::{in_bank_tran_id:}')
  logger.debug(f'in_fintech_use_num:{in_fintech_use_num}')
  logger.debug(f'in_inquiry_type:{in_inquiry_type}')
  logger.debug(f'in_inquiry_base:{in_inquiry_base}')
  logger.debug(f'in_from_date:{in_from_date}')
  logger.debug(f'in_to_date:{in_to_date}')
  logger.debug(f'in_befor_inquiry_trace_info:{in_befor_inquiry_trace_info}')
  logger.debug(f'in_req_from_offline_yn:{in_req_from_offline_yn}')
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
  access_token = user_data['out_login_access_token']
  logger.debug(f'access_token:{access_token}')
  if not in_fintech_use_num or in_fintech_use_num == '':
    in_fintech_use_num = user_data['out_fintech_use_num']
  sort_order = 'D' if in_sort_order_descending else 'A'
  tran_dtime = format_datetime()
  
  headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json; charset=UTF-8'
  }
  params = {
    "bank_tran_id": in_bank_tran_id,
    "fintech_use_num": in_fintech_use_num,
    "inquiry_type": in_inquiry_type,
    "inquiry_base": in_inquiry_base,
    "from_date": in_from_date,
    "to_date": in_to_date,
    "sort_order": sort_order,
    "tran_dtime": tran_dtime,
    "req_from_offline_yn": in_req_from_offline_yn
  }
  if in_befor_inquiry_trace_info:
    params['befor_inquiry_trace_info'] = in_befor_inquiry_trace_info
  
  query_string = "&".join([f"{k}={v}" for k, v in params.items()])
  url = f"{OPENBANK_DOMAIN}/v2.0/account/transaction_list/fin_num?{query_string}"
  response = requests.get(url, headers=headers)
  response.raise_for_status()
  
  if response.status_code == 200:
    data = response.json()
    print(data)
    if data["rsp_code"] and data["rsp_code"] == "A0000":
      result_data['out_success'] = True
      result_data['out_page_record_cnt'] = data["page_record_cnt"]
      result_data['out_next_page_yn'] = data["next_page_yn"]
      result_data['out_befor_inquiry_trace_info'] = data["befor_inquiry_trace_info"]
      result_data['out_res_list'] = data["res_list"]
  else:
    result_data['out_message'] = "오픈뱅킹 거래내역조회 오류"
    #result_data['out_detail'] = response.json()

  return result_data

def get_inquiry_real_name(in_user_id: str, in_bank_tran_id: str, in_bank_code_std: str, 
                        in_account_num: str, in_account_holder_info_type: str):
  """
  오픈뱅킹 계좌실명조회 : scope = oob, sa
  설명 : 이용기관이 특정 계좌의 계좌번호와 예금주 실명번호를 보유하고 있는 경우 해당 계좌의 유효성 및 예금주성명을 확인합니다.
  
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
  logger.debug('*** get_inquiry_real_name ***')
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
  access_token = user_data['out_login_access_token']
  user_seq_no = user_data['out_user_seq_no']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'user_seq_no:{user_seq_no}')
  tran_dtime = format_datetime()
  
  headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json; charset=UTF-8'
  }
  params = {
    "bank_tran_id": in_bank_tran_id,
    "bank_code_std": in_bank_code_std,
    "account_num": in_account_num,
    "account_holder_info_type": in_account_holder_info_type,
    "tran_dtime": tran_dtime
  }
  
  url = f"{OPENBANK_DOMAIN}/v2.0/inquiry/real_name"
  response = requests.post(url, data=params, headers=headers)
  response.raise_for_status()
  
  if response.status_code == 200:
    data = response.json()
    if data["rsp_code"] and data["rsp_code"] == "A0000":
      result_data['out_success'] = True
      result_data['out_account_holder_info'] = data["account_holder_info"]
      result_data['out_account_holder_name'] = data["account_holder_name"]
      result_data['out_account_type'] = data["account_type"]
  else:
    result_data['out_message'] = "오픈뱅킹 계좌실명조회 오류"
    #result_data['out_detail'] = response.json()

  return result_data
  
def get_account_cancel(in_user_id: str, in_bank_tran_id: str, 
                       in_fintech_use_num: str, in_bank_code_std: str, in_account_num: str):
  """
  오픈뱅킹 계좌해지 : scope = login, sa
  설명 : 오픈뱅킹에 등록된 사용자의 계좌를 해지(등록삭제 및 동의해지)합니다. 계좌해지는 참가기관에 등록된 내역까지 해지합니다.

  ※ 사용자정보조회 API 및 등록계좌조회 API에서 계좌가 존재하지 않거나 해지된 계좌로 응답 받은 경우, 이용기관은 그 계좌를 해지 완료된 것으로 처리할 수 있습니다.
  
  ※ 그 외의 경우, 이용기관은 계좌 해지를 위해 계좌해지 API를 필수로 요청해야 하며, 해지 API 응답 시 응답코드(참가기관)가 아래와 같은 경우, 해지 완료된 것으로 처리합니다.
    - 551: 기 해지 사용자
    - 555: 해당 사용자 없음
    - 556: 사용자 미등록
  
  Args:
    in_user_id (str): 사용자ID (필수)
    in_bank_tran_id (str(20)): 거래고유번호(참가기관) (필수)
    in_fintech_use_num (str(24)): 핀테크이용번호
    in_bank_code_std (str(3)): 계좌개설기관.표준코드
    in_account_num (str(16)): 계좌번호
  
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
  access_token = user_data['out_login_access_token']
  user_seq_no = user_data['out_user_seq_no']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'user_seq_no:{user_seq_no}')
  
  # 조회서비스 해지
  inquiry_data = private_auth_account_cancel(in_user_id, in_bank_tran_id, 'inquiry', in_fintech_use_num, in_bank_code_std, in_account_num)
  inquiry_result = 0
  if inquiry_data['out_success']:
    inquiry_result = 1
  # 출금서비스 해지
  transfer_data = private_auth_account_cancel(in_user_id, in_bank_tran_id, 'transfer', in_fintech_use_num, in_bank_code_std, in_account_num)
  transfer_result = 0
  if transfer_data['out_success']:
    transfer_result = 1
  return result_data

def private_auth_account_cancel(in_user_id: str, in_bank_tran_id: str, in_scope: str, 
                                in_fintech_use_num: str, in_bank_code_std: str, in_account_num: str):
  """
  오픈뱅킹 계좌해지 요청 처리

  Args:
    in_user_id (str): 사용자ID (필수)
    in_bank_tran_id (str(20)): 거래고유번호(참가기관) (필수)
    in_scope (str(3)): 개설기관.표준코드 (필수)
    in_fintech_use_num (str(24)): 핀테크이용번호
    in_bank_code_std (str(3)): 계좌개설기관.표준코드
    in_account_num (str(16)): 계좌번호
  
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
  access_token = user_data['out_login_access_token']
  user_seq_no = user_data['out_user_seq_no']
  logger.debug(f'access_token:{access_token}')
  logger.debug(f'user_seq_no:{user_seq_no}')
  
  headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json; charset=UTF-8'
  }
  params = {
    "bank_tran_id": in_bank_tran_id,
    "scope": in_scope,
    "fintech_use_num": in_fintech_use_num,
    "bank_code_std": in_bank_code_std,
    "account_num": in_account_num,
  }

  url = f"{OPENBANK_DOMAIN}/v2.0/account/cancel"
  response = requests.post(url, data=params, headers=headers)
  response.raise_for_status()
  
  if response.status_code != 200:
    #return {"error": "Failed to get access token", "details": response.json()}
    return {
      "message": "Failed to get access token",
      "details": response.json(),
      "result": "0"
    }
  data = response.json()
  if (data['rsp_code'] == "A0000" or data['rsp_code'] == "551" or data['rsp_code'] == "555" or data['rsp_code'] == "556"):
    result_data['out_success'] = True
  
  return result_data

# --- FastAPI 엔드포인트 ---

@APP_AUTH.get("/auth/user/{user_id}")
def get_user_endpoint(user_id: str):
    """
    사용자 정보 조회 엔드포인트
    """
    return get_user_info(user_id)

@APP_AUTH.post("/auth/register")
def register_user():
    """
    사용자 등록 엔드포인트 (구현 필요)
    """
    return {"message": "User registration endpoint"}

# 추가 엔드포인트 필요 시 여기에 추가

