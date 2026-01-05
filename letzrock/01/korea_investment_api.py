import requests
import os
import logging
from api_utils import format_datetime

# Logger 설정
logging.basicConfig(
  format='%(asctime)s %(levelname)s:%(message)s',
  level=logging.DEBUG,
  datefmt='%m/%d/%Y %I:%M:%S %p',
)
logger = logging.getLogger()
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)
log_file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), f'logs/korea_investment_api_{format_datetime('%Y%m%d')}.log'))
file_handler = logging.FileHandler(filename=log_file_name)
logger.addHandler(file_handler)

class KoreaInvestmentAPI():
  """
  한국투자증권 REST API 서버와 직접 요청과 응답을 주고받는 클래스
  API 신청 계좌만 조회 가능
  """
  def __init__(self, in_app_key: str, in_app_secret: str):
    """
    한국투자증권 REST API init

    Args:
      in_app_key (str): 한국투자증권 API 신청 계좌의 앱키
      in_app_secret (str): 한국투자증권 API 신청 계좌의 시크릿키
    """
    # 한국투자증권 API 신청 키
    self.app_key = in_app_key
    self.app_secret = in_app_secret
    ## 실전
    self.base_url = "https://openapi.koreainvestment.com:9443"
    ## 모의
    #self.base_url = "https://openapivts.koreainvestment.com:29443"
    # 토큰 정보
    self.token_data = None
    self.connect()
  
  def _send_request(self, url: str, method: str, params: dict, headers: dict):
    """
    내부 공통 요청 처리 함수
    """
    
    if method.upper() == 'POST':
      full_url = f"{self.base_url}{url}"
      response = requests.post(full_url, headers=headers, params=params)
    else:
      # 쿼리 파라미터 구성
      query_string = ''
      if params and params.keys():
        query_string = '?' + "&".join([f"{k}={v}" for k, v in params.items()])
      full_url = f"{self.base_url}{url}{query_string}"
      response = requests.get(full_url, headers=headers)
    response.raise_for_status()
    if response.status_code == 200:
      return response.headers(), response.json()
    else:
      return None, None
  
  def connect(self):
    """
    한국투자증권 REST API 토큰을 발급받습니다.
    본인 계좌에 필요한 인증 절차로, 인증을 통해 접근 토큰을 부여받아 오픈API 활용이 가능합니다.

    1. 접근토큰(access_token)의 유효기간은 24시간 이며(1일 1회발급 원칙) 
       갱신발급주기는 6시간 입니다.(6시간 이내는 기존 발급키로 응답)

    2. 접근토큰발급(/oauth2/tokenP) 시 접근토큰값(access_token)과 함께 수신되는 
       접근토큰 유효기간(acess_token_token_expired)을 이용해 접근토큰을 관리하실 수 있습니다.

    Raises:
      RuntimeError: 토큰을 발급받지 못한 경우
    """
    
    headers = {
      'Content-Type': 'application/json;charset=UTF-8'
    }
    params = {
      "grant_type": "client_credentials",
      "appkey": self.app_key,
      "appsecret": self.app_secret,
    }
    url = '/oauth2/tokenP'
    header_data, token_data = self._send_request(url, 'POST', params, headers)
    
    if token_data and token_data['access_token']:
      self.token_data = token_data
    else:
      self.token_data = None
      raise RuntimeError("Not connected: token is not available.")
  
  def close(self):
    """
    리소스를 정리합니다.
    """
    self.token_data = None

  def get_trading_order_cash(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_PDNO: str, in_SLL_TYPE: str, in_ORD_DVSN: str, in_ORD_QTY: str, in_ORD_UNPR: str, in_CNDT_PRIC: str, in_EXCG_ID_DVSN_CD: str):
    """
    주식주문(현금)
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : (매도) TTTC0011U (매수) TTTC0012U
    - 모의 TR_ID : (매도) VTTC0011U (매수) VTTC0012U
    
    개요 : 국내주식주문(현금) API 입니다. 
      ※ TTC0802U(현금매수) 사용하셔서 미수매수 가능합니다. 단, 거래하시는 계좌가 증거금40%계좌로 신청이 되어있어야 가능합니다. 
      ※ 신용매수는 별도의 API가 준비되어 있습니다.
      ※ ORD_QTY(주문수량), ORD_UNPR(주문단가) 등을 String으로 전달해야 함에 유의 부탁드립니다.
      ※ ORD_UNPR(주문단가)가 없는 주문은 상한가로 주문금액을 선정하고 이후 체결이되면 체결금액로 정산됩니다.
      ※ POST API의 경우 BODY값의 key값들을 대문자로 작성하셔야 합니다.
         (EX. "CANO" : "12345678", "ACNT_PRDT_CD": "01",...)
      ※ 종목코드 마스터파일 파이썬 정제코드는 한국투자증권 Github 참고 부탁드립니다.
         https://github.com/koreainvestment/open-trading-api/tree/main/stocks_info
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). '※ 구TR은 사전고지 없이 막힐 수 있으므로 반드시 신TR로 변경이용 부탁드립니다. [실전투자] 국내주식주문 매도 : (구)TTTC0801U → (신)TTTC0011U 국내주식주문 매도(모의투자) : (구)VTTC0801U → (신)VTTC0011U 국내주식주문 매수 : (구)TTTC0802U → (신)TTTC0012U 국내주식주문 매수(모의투자) : (구)VTTC0802U → (신)VTTC0012U'
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 종합계좌번호
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 상품유형코드
      in_PDNO (str(12)): 상품번호(필수). 종목코드(6자리) , ETN의 경우 7자리 입력
      in_SLL_TYPE (str(2)): 매도유형 (매도주문 시). 01@일반매도 02@임의매매 05@대차매도 → 미입력시 01 일반매도로 진행
      in_ORD_DVSN (str(2)): 주문구분(필수). [KRX] 00 : 지정가 01 : 시장가 02 : 조건부지정가 03 : 최유리지정가 04 : 최우선지정가 05 : 장전 시간외 06 : 장후 시간외 07 : 시간외 단일가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소) 21 : 중간가 22 : 스톱지정가 23 : 중간가IOC 24 : 중간가FOK  [NXT] 00 : 지정가 03 : 최유리지정가 04 : 최우선지정가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소) 21 : 중간가 22 : 스톱지정가 23 : 중간가IOC 24 : 중간가FOK  [SOR] 00 : 지정가 01 : 시장가 03 : 최유리지정가 04 : 최우선지정가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소)
      in_ORD_QTY (str(10)): 주문수량(필수). 주문수량
      in_ORD_UNPR (str(19)): 주문단가(필수). 주문단가 시장가 등 주문시, "0"으로 입력
      in_CNDT_PRIC (str(19)): 조건가격. 스탑지정가호가 주문 (ORD_DVSN이 22) 사용 시에만 필수
      in_EXCG_ID_DVSN_CD (str(3)): 거래소ID구분코드. 한국거래소 : KRX 대체거래소 (넥스트레이드) : NXT SOR (Smart Order Routing) : SOR → 미입력시 KRX로 진행되며, 모의투자는 KRX만 가능
    
    Returns:
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output (str): 응답상세. single
      out_KRX_FWDG_ORD_ORGNO (str(5)): 거래소코드
      out_ODNO (str(10)): 주문번호
      out_ORD_TMD (str(6)): 주문시간
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'api-id': 'v1_국내주식-001',
    }
    params = {
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'PDNO': in_PDNO,
      'SLL_TYPE': in_SLL_TYPE,
      'ORD_DVSN': in_ORD_DVSN,
      'ORD_QTY': in_ORD_QTY,
      'ORD_UNPR': in_ORD_UNPR,
      'CNDT_PRIC': in_CNDT_PRIC,
      'EXCG_ID_DVSN_CD': in_EXCG_ID_DVSN_CD,
    }
    url = '/uapi/domestic-stock/v1/trading/order-cash'
    
    header_data, out_data = self._send_request(url, 'POST', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_KRX_FWDG_ORD_ORGNO'] = out_data['KRX_FWDG_ORD_ORGNO']
    return_data['out_ODNO'] = out_data['ODNO']
    return_data['out_ORD_TMD'] = out_data['ORD_TMD']
    
    return return_data

  def get_trading_order_credit(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_PDNO: str, in_SLL_TYPE: str, in_CRDT_TYPE: str, in_LOAN_DT: str, in_ORD_DVSN: str, in_ORD_QTY: str, in_ORD_UNPR: str, in_RSVN_ORD_YN: str, in_EMGC_ORD_YN: str, in_PGTR_DVSN: str, in_MGCO_APTM_ODNO: str, in_LQTY_TR_NGTN_DTL_NO: str, in_LQTY_TR_AGMT_NO: str, in_LQTY_TR_NGTN_ID: str, in_LP_ORD_YN: str, in_MDIA_ODNO: str, in_ORD_SVR_DVSN_CD: str, in_PGM_NMPR_STMT_DVSN_CD: str, in_CVRG_SLCT_RSON_CD: str, in_CVRG_SEQ: str, in_EXCG_ID_DVSN_CD: str, in_CNDT_PRIC: str):
    """
    주식주문(신용)
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : (매도) TTTC0051U (매수) TTTC0052U
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 국내주식주문(신용) API입니다. 
      ※ 모의투자는 사용 불가합니다.
      ※ POST API의 경우 BODY값의 key값들을 대문자로 작성하셔야 합니다.
         (EX. "CANO" : "12345678", "ACNT_PRDT_CD": "01",...)
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). '※ 구TR은 사전고지 없이 막힐 수 있으므로 반드시 신TR로 변경이용 부탁드립니다. [실전투자] 매도 : (구)TTTC0851U → (신)TTTC0051U 매수 : (구)TTTC0852U → (신)TTTC0052U '
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_PDNO (str(5)): 상품번호(필수). 종목코드(6자리)
      in_SLL_TYPE (str(10)): 매도유형. 공란 입력
      in_CRDT_TYPE (str(2)): 신용유형(필수). [매도] 22 : 유통대주신규, 24 : 자기대주신규, 25 : 자기융자상환, 27 : 유통융자상환 [매수] 21 : 자기융자신규, 23 : 유통융자신규 , 26 : 유통대주상환, 28 : 자기대주상환
      in_LOAN_DT (str(2)): 대출일자(필수). [신용매수]  신규 대출로, 오늘날짜(yyyyMMdd)) 입력   [신용매도]  매도할 종목의 대출일자(yyyyMMdd)) 입력
      in_ORD_DVSN (str(8)): 주문구분(필수). [KRX] 00 : 지정가 01 : 시장가 02 : 조건부지정가 03 : 최유리지정가 04 : 최우선지정가 05 : 장전 시간외 06 : 장후 시간외 07 : 시간외 단일가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소) 21 : 중간가 22 : 스톱지정가 23 : 중간가IOC 24 : 중간가FOK  [NXT] 00 : 지정가 03 : 최유리지정가 04 : 최우선지정가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소) 21 : 중간가 22 : 스톱지정가 23 : 중간가IOC 24 : 중간가FOK  [SOR] 00 : 지정가 01 : 시장가 03 : 최유리지정가 04 : 최우선지정가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소)
      in_ORD_QTY (str(2)): 주문수량(필수)
      in_ORD_UNPR (str(5)): 주문단가(필수). 1주당 가격  * 장전 시간외, 장후 시간외, 시장가의 경우 1주당 가격을 공란으로 비우지 않음 "0"으로 입력 권고
      in_RSVN_ORD_YN (str(2)): 예약주문여부. 정규 증권시장이 열리지 않는 시간 (15:10분 ~ 익일 7:30분) 에 주문을 미리 설정 하여 다음 영업일 또는 설정한 기간 동안 아침 동시 호가에 주문하는 것  Y : 예약주문  N : 신용주문
      in_EMGC_ORD_YN (str(2)): 비상주문여부
      in_PGTR_DVSN (str(10)): 프로그램매매구분
      in_MGCO_APTM_ODNO (str(19)): 운용사지정주문번호
      in_LQTY_TR_NGTN_DTL_NO (str(1)): 대량거래협상상세번호
      in_LQTY_TR_AGMT_NO (str(20)): 대량거래협정번호
      in_LQTY_TR_NGTN_ID (str(19)): 대량거래협상자Id
      in_LP_ORD_YN (str(3)): LP주문여부
      in_MDIA_ODNO (str(10)): 매체주문번호
      in_ORD_SVR_DVSN_CD (str(19)): 주문서버구분코드
      in_PGM_NMPR_STMT_DVSN_CD (str(1)): 프로그램호가신고구분코드
      in_CVRG_SLCT_RSON_CD (str(20)): 반대매매선정사유코드
      in_CVRG_SEQ (str(19)): 반대매매순번
      in_EXCG_ID_DVSN_CD (str(3)): 거래소ID구분코드. 한국거래소 : KRX 대체거래소 (넥스트레이드) : NXT SOR (Smart Order Routing) : SOR → 미입력시 KRX로 진행되며, 모의투자는 KRX만 가능
      in_CNDT_PRIC (str(19)): 조건가격. 스탑지정가호가에서 사용
    
    Returns:
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output (str): 응답상세. single
      out_krx_fwdg_ord_orgno (str(5)): 한국거래소전송주문조직번호
      out_odno (str(10)): 주문번호
      out_ord_tmd (str(6)): 주문시간
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'api-id': 'v1_국내주식-002',
    }
    params = {
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'PDNO': in_PDNO,
      'SLL_TYPE': in_SLL_TYPE,
      'CRDT_TYPE': in_CRDT_TYPE,
      'LOAN_DT': in_LOAN_DT,
      'ORD_DVSN': in_ORD_DVSN,
      'ORD_QTY': in_ORD_QTY,
      'ORD_UNPR': in_ORD_UNPR,
      'RSVN_ORD_YN': in_RSVN_ORD_YN,
      'EMGC_ORD_YN': in_EMGC_ORD_YN,
      'PGTR_DVSN': in_PGTR_DVSN,
      'MGCO_APTM_ODNO': in_MGCO_APTM_ODNO,
      'LQTY_TR_NGTN_DTL_NO': in_LQTY_TR_NGTN_DTL_NO,
      'LQTY_TR_AGMT_NO': in_LQTY_TR_AGMT_NO,
      'LQTY_TR_NGTN_ID': in_LQTY_TR_NGTN_ID,
      'LP_ORD_YN': in_LP_ORD_YN,
      'MDIA_ODNO': in_MDIA_ODNO,
      'ORD_SVR_DVSN_CD': in_ORD_SVR_DVSN_CD,
      'PGM_NMPR_STMT_DVSN_CD': in_PGM_NMPR_STMT_DVSN_CD,
      'CVRG_SLCT_RSON_CD': in_CVRG_SLCT_RSON_CD,
      'CVRG_SEQ': in_CVRG_SEQ,
      'EXCG_ID_DVSN_CD': in_EXCG_ID_DVSN_CD,
      'CNDT_PRIC': in_CNDT_PRIC,
    }
    url = '/uapi/domestic-stock/v1/trading/order-credit'
    
    header_data, out_data = self._send_request(url, 'POST', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_krx_fwdg_ord_orgno'] = out_data['krx_fwdg_ord_orgno']
    return_data['out_odno'] = out_data['odno']
    return_data['out_ord_tmd'] = out_data['ord_tmd']
    
    return return_data

  def get_trading_order_rvsecncl(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_KRX_FWDG_ORD_ORGNO: str, in_ORGN_ODNO: str, in_ORD_DVSN: str, in_RVSE_CNCL_DVSN_CD: str, in_ORD_QTY: str, in_ORD_UNPR: str, in_QTY_ALL_ORD_YN: str, in_CNDT_PRIC: str, in_EXCG_ID_DVSN_CD: str):
    """
    주식주문(정정취소)
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC0013U
    - 모의 TR_ID : VTTC0013U
    
    개요 : 주문 건에 대하여 정정 및 취소하는 API입니다. 단, 이미 체결된 건은 정정 및 취소가 불가합니다.
      ※ 정정은 원주문에 대한 주문단가 혹은 주문구분을 변경하는 사항으로, 정정이 가능한 수량은 원주문수량을 초과 할 수 없습니다.
      ※ 주식주문(정정취소) 호출 전에 반드시 주식정정취소가능주문조회 호출을 통해 정정취소가능수량(output &gt; psbl_qty)을 확인하신 후 정정취소주문 내시기 바랍니다.
      ※ POST API의 경우 BODY값의 key값들을 대문자로 작성하셔야 합니다.
         (EX. "CANO" : "12345678", "ACNT_PRDT_CD": "01",...)
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). ※ 구TR은 사전고지 없이 막힐 수 있으므로 반드시 신TR로 변경이용 부탁드립니다. [실전투자] 정정/취소 (구)TTTC0803U → (신)TTTC0013U 정정/취소 (모의투자) (구)VTTC0803U → (신)VTTC0013U
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 종합계좌번호
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 상품유형코드
      in_KRX_FWDG_ORD_ORGNO (str(5)): 한국거래소전송주문조직번호(필수)
      in_ORGN_ODNO (str(10)): 원주문번호(필수). 원주문번호
      in_ORD_DVSN (str(2)): 주문구분(필수). [KRX] 00 : 지정가 01 : 시장가 02 : 조건부지정가 03 : 최유리지정가 04 : 최우선지정가 05 : 장전 시간외 06 : 장후 시간외 07 : 시간외 단일가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소) 21 : 중간가 22 : 스톱지정가 23 : 중간가IOC 24 : 중간가FOK  [NXT] 00 : 지정가 03 : 최유리지정가 04 : 최우선지정가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소) 21 : 중간가 22 : 스톱지정가 23 : 중간가IOC 24 : 중간가FOK  [SOR] 00 : 지정가 01 : 시장가 03 : 최유리지정가 04 : 최우선지정가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소)
      in_RVSE_CNCL_DVSN_CD (str(2)): 정정취소구분코드(필수). 01@정정 02@취소
      in_ORD_QTY (str(10)): 주문수량(필수). 주문수량
      in_ORD_UNPR (str(19)): 주문단가(필수). 주문단가
      in_QTY_ALL_ORD_YN (str(1)): 잔량전부주문여부(필수). 'Y@전량 N@일부'
      in_CNDT_PRIC (str(19)): 조건가격. 스탑지정가호가에서 사용
      in_EXCG_ID_DVSN_CD (str(3)): 거래소ID구분코드. 한국거래소 : KRX 대체거래소 (넥스트레이드) : NXT SOR (Smart Order Routing) : SOR → 미입력시 KRX로 진행되며, 모의투자는 KRX만 가능
    
    Returns:
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output (str): 응답상세. single
      out_krx_fwdg_ord_orgno (str(5)): 한국거래소전송주문조직번호
      out_odno (str(10)): 주문번호
      out_ord_tmd (str(6)): 주문시각
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'api-id': 'v1_국내주식-003',
    }
    params = {
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'KRX_FWDG_ORD_ORGNO': in_KRX_FWDG_ORD_ORGNO,
      'ORGN_ODNO': in_ORGN_ODNO,
      'ORD_DVSN': in_ORD_DVSN,
      'RVSE_CNCL_DVSN_CD': in_RVSE_CNCL_DVSN_CD,
      'ORD_QTY': in_ORD_QTY,
      'ORD_UNPR': in_ORD_UNPR,
      'QTY_ALL_ORD_YN': in_QTY_ALL_ORD_YN,
      'CNDT_PRIC': in_CNDT_PRIC,
      'EXCG_ID_DVSN_CD': in_EXCG_ID_DVSN_CD,
    }
    url = '/uapi/domestic-stock/v1/trading/order-rvsecncl'
    
    header_data, out_data = self._send_request(url, 'POST', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_krx_fwdg_ord_orgno'] = out_data['krx_fwdg_ord_orgno']
    return_data['out_odno'] = out_data['odno']
    return_data['out_ord_tmd'] = out_data['ord_tmd']
    
    return return_data

  def get_trading_inquire_psbl_rvsecncl(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_CTX_AREA_FK100: str, in_CTX_AREA_NK100: str, in_INQR_DVSN_1: str, in_INQR_DVSN_2: str):
    """
    주식정정취소가능주문조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC0084R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 주식정정취소가능주문조회 API입니다. 한 번의 호출에 최대 50건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다.
      ※ 주식주문(정정취소) 호출 전에 반드시 주식정정취소가능주문조회 호출을 통해 정정취소가능수량(output &gt; psbl_qty)을 확인하신 후 정정취소주문 내시기 바랍니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). ※ 구TR은 사전고지 없이 막힐 수 있으므로 반드시 신TR로 변경이용 부탁드립니다. [실전투자] (구)TTTC8036R → (신)TTTC0084R
      in_tr_cont (str(1)): 연속 거래 여부. 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우)
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_CTX_AREA_FK100 (str(100)): 연속조회검색조건100(필수). '공란 : 최초 조회시는  이전 조회 Output CTX_AREA_FK100 값 : 다음페이지 조회시(2번째부터)'
      in_CTX_AREA_NK100 (str(100)): 연속조회키100(필수). '공란 : 최초 조회시  이전 조회 Output CTX_AREA_NK100 값 : 다음페이지 조회시(2번째부터)'
      in_INQR_DVSN_1 (str(1)): 조회구분1(필수). '0 주문 1 종목'
      in_INQR_DVSN_2 (str(1)): 조회구분2(필수). '0 전체 1 매도 2 매수'
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. F or M : 다음 데이터 있음 D or E : 마지막 데이터
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output (str): 응답상세. array
      out_ord_gno_brno (str(5)): 주문채번지점번호. 주문시 한국투자증권 시스템에서 지정된 영업점코드
      out_odno (str(10)): 주문번호. 주문시 한국투자증권 시스템에서 채번된 주문번호
      out_orgn_odno (str(6)): 원주문번호. 정정/취소주문 인경우 원주문번호
      out_ord_dvsn_name (str(5)): 주문구분명
      out_pdno (str(10)): 상품번호. 종목번호(뒤 6자리만 해당)
      out_prdt_name (str(6)): 상품명. 종목명
      out_rvse_cncl_dvsn_name (str(5)): 정정취소구분명. 정정 또는 취소 여부 표시
      out_ord_qty (str(10)): 주문수량
      out_ord_unpr (str(6)): 주문단가. 1주당 주문가격
      out_ord_tmd (str(5)): 주문시각. 주문시각(시분초HHMMSS)
      out_tot_ccld_qty (str(10)): 총체결수량. 주문 수량 중 체결된 수량
      out_tot_ccld_amt (str(6)): 총체결금액. 주문금액 중 체결금액
      out_psbl_qty (str(5)): 가능수량. 정정/취소 주문 가능 수량
      out_sll_buy_dvsn_cd (str(10)): 매도매수구분코드. 01 : 매도 / 02 : 매수
      out_ord_dvsn_cd (str(6)): 주문구분코드. [KRX] 00 : 지정가 01 : 시장가 02 : 조건부지정가 03 : 최유리지정가 04 : 최우선지정가 05 : 장전 시간외 06 : 장후 시간외 07 : 시간외 단일가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소) 21 : 중간가 22 : 스톱지정가 23 : 중간가IOC 24 : 중간가FOK  [NXT] 00 : 지정가 03 : 최유리지정가 04 : 최우선지정가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소) 21 : 중간가 22 : 스톱지정가 23 : 중간가IOC 24 : 중간가FOK  [SOR] 00 : 지정가 01 : 시장가 03 : 최유리지정가 04 : 최우선지정가 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소)
      out_mgco_aptm_odno (str(5)): 운용사지정주문번호
      out_excg_dvsn_cd (str(2)): 거래소구분코드
      out_excg_id_dvsn_cd (str(3)): 거래소ID구분코드
      out_excg_id_dvsn_name (str(100)): 거래소ID구분명
      out_stpm_cndt_pric (str(9)): 스톱지정가조건가격
      out_stpm_efct_occr_yn (str(1)): 스톱지정가효력발생여부
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'CTX_AREA_FK100': in_CTX_AREA_FK100,
      'CTX_AREA_NK100': in_CTX_AREA_NK100,
      'INQR_DVSN_1': in_INQR_DVSN_1,
      'INQR_DVSN_2': in_INQR_DVSN_2,
      'api-id': 'v1_국내주식-004',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_ord_gno_brno'] = out_data['ord_gno_brno']
    return_data['out_odno'] = out_data['odno']
    return_data['out_orgn_odno'] = out_data['orgn_odno']
    return_data['out_ord_dvsn_name'] = out_data['ord_dvsn_name']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_prdt_name'] = out_data['prdt_name']
    return_data['out_rvse_cncl_dvsn_name'] = out_data['rvse_cncl_dvsn_name']
    return_data['out_ord_qty'] = out_data['ord_qty']
    return_data['out_ord_unpr'] = out_data['ord_unpr']
    return_data['out_ord_tmd'] = out_data['ord_tmd']
    return_data['out_tot_ccld_qty'] = out_data['tot_ccld_qty']
    return_data['out_tot_ccld_amt'] = out_data['tot_ccld_amt']
    return_data['out_psbl_qty'] = out_data['psbl_qty']
    return_data['out_sll_buy_dvsn_cd'] = out_data['sll_buy_dvsn_cd']
    return_data['out_ord_dvsn_cd'] = out_data['ord_dvsn_cd']
    return_data['out_mgco_aptm_odno'] = out_data['mgco_aptm_odno']
    return_data['out_excg_dvsn_cd'] = out_data['excg_dvsn_cd']
    return_data['out_excg_id_dvsn_cd'] = out_data['excg_id_dvsn_cd']
    return_data['out_excg_id_dvsn_name'] = out_data['excg_id_dvsn_name']
    return_data['out_stpm_cndt_pric'] = out_data['stpm_cndt_pric']
    return_data['out_stpm_efct_occr_yn'] = out_data['stpm_efct_occr_yn']
    
    return return_data

  def get_trading_inquire_daily_ccld(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_INQR_STRT_DT: str, in_INQR_END_DT: str, in_SLL_BUY_DVSN_CD: str, in_PDNO: str, in_ORD_GNO_BRNO: str, in_ODNO: str, in_CCLD_DVSN: str, in_INQR_DVSN: str, in_INQR_DVSN_1: str, in_INQR_DVSN_3: str, in_EXCG_ID_DVSN_CD: str, in_CTX_AREA_FK100: str, in_CTX_AREA_NK100: str):
    """
    주식일별주문체결조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : (3개월이내) TTTC0081R (3개월이전) CTSC9215R
    - 모의 TR_ID : (3개월이내) VTTC0081R (3개월이전) VTSC9215R
    
    개요 : 주식일별주문체결조회 API입니다. 
      실전계좌의 경우, 한 번의 호출에 최대 100건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다. 
      모의계좌의 경우, 한 번의 호출에 최대 15건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다. 
      * 다만, 3개월 이전 체결내역 조회(CTSC9115R) 의 경우, 
      장중에는 많은 거래량으로 인해 순간적으로 DB가 밀렸거나 응답을 늦게 받거나 하는 등의 이슈가 있을 수 있어
      ① 가급적 장 종료 이후(15:30 이후) 조회하시고 
      ② 조회기간(INQR_STRT_DT와 INQR_END_DT 사이의 간격)을 보다 짧게 해서 조회하는 것을
      권유드립니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). ※ 구TR은 사전고지 없이 막힐 수 있으므로 반드시 신TR로 변경이용 부탁드립니다. [실전투자] 3개월이내 (구)TTTC8001R → (신)TTTC0081R  3개월이전 (구)CTSC9115R → (신)CTSC9215R [모의투자] 3개월이내 (구)VTTC8001R → (신)VTTC0081R  3개월이전 (구)VTSC9115R → (신)VTSC9215R
      in_tr_cont (str(1)): 연속 거래 여부. 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우)
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_INQR_STRT_DT (str(8)): 조회시작일자(필수). YYYYMMDD
      in_INQR_END_DT (str(8)): 조회종료일자(필수). YYYYMMDD
      in_SLL_BUY_DVSN_CD (str(2)): 매도매수구분코드(필수). 00 : 전체 / 01 : 매도 / 02 : 매수
      in_PDNO (str(12)): 상품번호. 종목번호(6자리)
      in_ORD_GNO_BRNO (str(5)): 주문채번지점번호(필수). 주문시 한국투자증권 시스템에서 지정된 영업점코드
      in_ODNO (str(10)): 주문번호. 주문시 한국투자증권 시스템에서 채번된 주문번호
      in_CCLD_DVSN (str(2)): 체결구분(필수). '00 전체 01 체결 02 미체결'
      in_INQR_DVSN (str(2)): 조회구분(필수). '00 역순 01 정순'
      in_INQR_DVSN_1 (str(1)): 조회구분1(필수). '없음: 전체 1: ELW 2: 프리보드'
      in_INQR_DVSN_3 (str(2)): 조회구분3(필수). '00 전체 01 현금 02 신용 03 담보 04 대주 05 대여 06 자기융자신규/상환 07 유통융자신규/상환'
      in_EXCG_ID_DVSN_CD (str(3)): 거래소ID구분코드(필수). 한국거래소 : KRX 대체거래소 (NXT) : NXT SOR (Smart Order Routing) : SOR ALL : 전체 ※ 모의투자는 KRX만 제공
      in_CTX_AREA_FK100 (str(100)): 연속조회검색조건100(필수). '공란 : 최초 조회시는  이전 조회 Output CTX_AREA_FK100 값 : 다음페이지 조회시(2번째부터)'
      in_CTX_AREA_NK100 (str(100)): 연속조회키100(필수). '공란 : 최초 조회시  이전 조회 Output CTX_AREA_NK100 값 : 다음페이지 조회시(2번째부터)'
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. F or M : 다음 데이터 있음 D or E : 마지막 데이터
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output1 (str): 응답상세. array
      out_ord_dt (str(8)): 주문일자
      out_ord_gno_brno (str(5)): 주문채번지점번호
      out_odno (str(10)): 주문번호
      out_orgn_odno (str(10)): 원주문번호
      out_ord_dvsn_name (str(60)): 주문구분명
      out_sll_buy_dvsn_cd (str(2)): 매도매수구분코드
      out_sll_buy_dvsn_cd_name (str(60)): 매도매수구분코드명
      out_pdno (str(12)): 상품번호
      out_prdt_name (str(60)): 상품명
      out_ord_qty (str(10)): 주문수량
      out_ord_unpr (str(19)): 주문단가
      out_ord_tmd (str(6)): 주문시각
      out_tot_ccld_qty (str(10)): 총체결수량
      out_avg_prvs (str(19)): 평균가
      out_cncl_yn (str(1)): 취소여부
      out_tot_ccld_amt (str(19)): 총체결금액
      out_loan_dt (str(8)): 대출일자
      out_ordr_empno (str(60)): 주문자사번
      out_ord_dvsn_cd (str(2)): 주문구분코드
      out_cnc_cfrm_qty (str(10)): 취소확인수량
      out_rmn_qty (str(10)): 잔여수량
      out_rjct_qty (str(10)): 거부수량
      out_ccld_cndt_name (str(10)): 체결조건명
      out_inqr_ip_addr (str(15)): 조회IP주소
      out_cpbc_ordp_ord_rcit_dvsn_cd (str(2)): 전산주문표주문접수구분코드
      out_cpbc_ordp_infm_mthd_dvsn_cd (str(2)): 전산주문표통보방법구분코드
      out_infm_tmd (str(6)): 통보시각
      out_ctac_tlno (str(20)): 연락전화번호
      out_prdt_type_cd (str(3)): 상품유형코드
      out_excg_dvsn_cd (str(2)): 거래소구분코드
      out_cpbc_ordp_mtrl_dvsn_cd (str(2)): 전산주문표자료구분코드
      out_ord_orgno (str(5)): 주문조직번호
      out_rsvn_ord_end_dt (str(8)): 예약주문종료일자
      out_excg_id_dvsn_Cd (str(3)): 거래소ID구분코드
      out_stpm_cndt_pric (str(9)): 스톱지정가조건가격
      out_stpm_efct_occr_dtmd (str(9)): 스톱지정가효력발생상세시각
      out_output2 (str): 응답상세. single
      out_tot_ord_qty (str(10)): 총주문수량
      out_tot_ccld_qty (str(10)): 총체결수량
      out_tot_ccld_amt (str(19)): 매입평균가격
      out_prsm_tlex_smtl (str(19)): 총체결금액
      out_pchs_avg_pric (str(184)): 추정제비용합계
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'INQR_STRT_DT': in_INQR_STRT_DT,
      'INQR_END_DT': in_INQR_END_DT,
      'SLL_BUY_DVSN_CD': in_SLL_BUY_DVSN_CD,
      'PDNO': in_PDNO,
      'ORD_GNO_BRNO': in_ORD_GNO_BRNO,
      'ODNO': in_ODNO,
      'CCLD_DVSN': in_CCLD_DVSN,
      'INQR_DVSN': in_INQR_DVSN,
      'INQR_DVSN_1': in_INQR_DVSN_1,
      'INQR_DVSN_3': in_INQR_DVSN_3,
      'EXCG_ID_DVSN_CD': in_EXCG_ID_DVSN_CD,
      'CTX_AREA_FK100': in_CTX_AREA_FK100,
      'CTX_AREA_NK100': in_CTX_AREA_NK100,
      'api-id': 'v1_국내주식-005',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/inquire-daily-ccld'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output1'] = out_data['output1']
    return_data['out_ord_dt'] = out_data['ord_dt']
    return_data['out_ord_gno_brno'] = out_data['ord_gno_brno']
    return_data['out_odno'] = out_data['odno']
    return_data['out_orgn_odno'] = out_data['orgn_odno']
    return_data['out_ord_dvsn_name'] = out_data['ord_dvsn_name']
    return_data['out_sll_buy_dvsn_cd'] = out_data['sll_buy_dvsn_cd']
    return_data['out_sll_buy_dvsn_cd_name'] = out_data['sll_buy_dvsn_cd_name']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_prdt_name'] = out_data['prdt_name']
    return_data['out_ord_qty'] = out_data['ord_qty']
    return_data['out_ord_unpr'] = out_data['ord_unpr']
    return_data['out_ord_tmd'] = out_data['ord_tmd']
    return_data['out_tot_ccld_qty'] = out_data['tot_ccld_qty']
    return_data['out_avg_prvs'] = out_data['avg_prvs']
    return_data['out_cncl_yn'] = out_data['cncl_yn']
    return_data['out_tot_ccld_amt'] = out_data['tot_ccld_amt']
    return_data['out_loan_dt'] = out_data['loan_dt']
    return_data['out_ordr_empno'] = out_data['ordr_empno']
    return_data['out_ord_dvsn_cd'] = out_data['ord_dvsn_cd']
    return_data['out_cnc_cfrm_qty'] = out_data['cnc_cfrm_qty']
    return_data['out_rmn_qty'] = out_data['rmn_qty']
    return_data['out_rjct_qty'] = out_data['rjct_qty']
    return_data['out_ccld_cndt_name'] = out_data['ccld_cndt_name']
    return_data['out_inqr_ip_addr'] = out_data['inqr_ip_addr']
    return_data['out_cpbc_ordp_ord_rcit_dvsn_cd'] = out_data['cpbc_ordp_ord_rcit_dvsn_cd']
    return_data['out_cpbc_ordp_infm_mthd_dvsn_cd'] = out_data['cpbc_ordp_infm_mthd_dvsn_cd']
    return_data['out_infm_tmd'] = out_data['infm_tmd']
    return_data['out_ctac_tlno'] = out_data['ctac_tlno']
    return_data['out_prdt_type_cd'] = out_data['prdt_type_cd']
    return_data['out_excg_dvsn_cd'] = out_data['excg_dvsn_cd']
    return_data['out_cpbc_ordp_mtrl_dvsn_cd'] = out_data['cpbc_ordp_mtrl_dvsn_cd']
    return_data['out_ord_orgno'] = out_data['ord_orgno']
    return_data['out_rsvn_ord_end_dt'] = out_data['rsvn_ord_end_dt']
    return_data['out_excg_id_dvsn_Cd'] = out_data['excg_id_dvsn_Cd']
    return_data['out_stpm_cndt_pric'] = out_data['stpm_cndt_pric']
    return_data['out_stpm_efct_occr_dtmd'] = out_data['stpm_efct_occr_dtmd']
    return_data['out_output2'] = out_data['output2']
    return_data['out_tot_ord_qty'] = out_data['tot_ord_qty']
    return_data['out_tot_ccld_qty'] = out_data['tot_ccld_qty']
    return_data['out_tot_ccld_amt'] = out_data['tot_ccld_amt']
    return_data['out_prsm_tlex_smtl'] = out_data['prsm_tlex_smtl']
    return_data['out_pchs_avg_pric'] = out_data['pchs_avg_pric']
    
    return return_data

  def get_trading_inquire_balance(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_AFHR_FLPR_YN: str, in_OFL_YN: str, in_INQR_DVSN: str, in_UNPR_DVSN: str, in_FUND_STTL_ICLD_YN: str, in_FNCG_AMT_AUTO_RDPT_YN: str, in_PRCS_DVSN: str, in_CTX_AREA_FK100: str, in_CTX_AREA_NK100: str):
    """
    주식잔고조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC8434R
    - 모의 TR_ID : VTTC8434R
    
    개요 : 주식 잔고조회 API입니다. 
      실전계좌의 경우, 한 번의 호출에 최대 50건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다. 
      모의계좌의 경우, 한 번의 호출에 최대 20건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다. 
      * 당일 전량매도한 잔고도 보유수량 0으로 보여질 수 있으나, 해당 보유수량 0인 잔고는 최종 D-2일 이후에는 잔고에서 사라집니다.
      ※ 중요 : 해당 API는 제공 정보량이 많아 조회속도가 느린 API입니다. 단순 주문 준비를 위해서는 주식매수/매도가능수량 조회 TR 사용을 권장 드립니다.
    
    Args:
      in_content_type (str(40)): 컨텐츠타입. application/json; charset=utf-8
      in_tr_id (str(13)): 거래ID(필수). [실전투자] TTTC8434R : 주식 잔고 조회  [모의투자] VTTC8434R : 주식 잔고 조회
      in_tr_cont (str(1)): 연속 거래 여부. 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우)
      in_custtype (str(1)): 고객타입. B : 법인 P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_AFHR_FLPR_YN (str(1)): 시간외단일가, 거래소여부(필수). N : 기본값, Y : 시간외단일가, X : NXT 정규장 (프리마켓, 메인, 애프터마켓) ※ NXT 선택 시 : NXT 거래종목만 시세 등 정보가 NXT 기준으로 변동됩니다. KRX 종목들은 그대로 유지
      in_OFL_YN (str(1)): 오프라인여부. 공란(Default)
      in_INQR_DVSN (str(2)): 조회구분(필수). 01 : 대출일별 02 : 종목별
      in_UNPR_DVSN (str(2)): 단가구분(필수). 01 : 기본값
      in_FUND_STTL_ICLD_YN (str(1)): 펀드결제분포함여부(필수). N : 포함하지 않음 Y :  포함
      in_FNCG_AMT_AUTO_RDPT_YN (str(1)): 융자금액자동상환여부(필수). N : 기본값
      in_PRCS_DVSN (str(2)): 처리구분(필수). 00 :  전일매매포함 01 : 전일매매미포함
      in_CTX_AREA_FK100 (str(100)): 연속조회검색조건100. 공란 : 최초 조회시 이전 조회 Output CTX_AREA_FK100 값 : 다음페이지 조회시(2번째부터)
      in_CTX_AREA_NK100 (str(100)): 연속조회키100. 공란 : 최초 조회시 이전 조회 Output CTX_AREA_NK100 값 : 다음페이지 조회시(2번째부터)
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. F or M : 다음 데이터 있음 D or E : 마지막 데이터
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부. 0 : 성공 0 이외의 값 : 실패
      out_msg_cd (str(8)): 응답코드. 응답코드
      out_msg1 (str(80)): 응답메세지. 응답메세지
      out_ctx_area_fk100 (str(100)): 연속조회검색조건100
      out_ctx_area_nk100 (str(100)): 연속조회키100
      out_output1 (str): 응답상세1. Array
      out_pdno (str(12)): 상품번호. 종목번호(뒷 6자리)
      out_prdt_name (str(60)): 상품명. 종목명
      out_trad_dvsn_name (str(60)): 매매구분명. 매수매도구분
      out_bfdy_buy_qty (str(10)): 전일매수수량
      out_bfdy_sll_qty (str(10)): 전일매도수량
      out_thdt_buyqty (str(10)): 금일매수수량
      out_thdt_sll_qty (str(10)): 금일매도수량
      out_hldg_qty (str(19)): 보유수량
      out_ord_psbl_qty (str(10)): 주문가능수량
      out_pchs_avg_pric (str(22)): 매입평균가격. 매입금액 / 보유수량
      out_pchs_amt (str(19)): 매입금액
      out_prpr (str(19)): 현재가
      out_evlu_amt (str(19)): 평가금액
      out_evlu_pfls_amt (str(19)): 평가손익금액. 평가금액 - 매입금액
      out_evlu_pfls_rt (str(9)): 평가손익율
      out_evlu_erng_rt (str(31)): 평가수익율. 미사용항목(0으로 출력)
      out_loan_dt (str(8)): 대출일자. INQR_DVSN(조회구분)을 01(대출일별)로 설정해야 값이 나옴
      out_loan_amt (str(19)): 대출금액
      out_stln_slng_chgs (str(19)): 대주매각대금
      out_expd_dt (str(8)): 만기일자
      out_fltt_rt (str(31)): 등락율
      out_bfdy_cprs_icdc (str(19)): 전일대비증감
      out_item_mgna_rt_name (str(20)): 종목증거금율명
      out_grta_rt_name (str(20)): 보증금율명
      out_sbst_pric (str(19)): 대용가격. 증권매매의 위탁보증금으로서 현금 대신에 사용되는 유가증권 가격
      out_stck_loan_unpr (str(22)): 주식대출단가
      out_output2 (str): 응답상세2. Array
      out_dnca_tot_amt (str(19)): 예수금총금액. 예수금
      out_nxdy_excc_amt (str(19)): 익일정산금액. D+1 예수금
      out_prvs_rcdl_excc_amt (str(19)): 가수도정산금액. D+2 예수금
      out_cma_evlu_amt (str(19)): CMA평가금액
      out_bfdy_buy_amt (str(19)): 전일매수금액
      out_thdt_buy_amt (str(19)): 금일매수금액
      out_nxdy_auto_rdpt_amt (str(19)): 익일자동상환금액
      out_bfdy_sll_amt (str(19)): 전일매도금액
      out_thdt_sll_amt (str(19)): 금일매도금액
      out_d2_auto_rdpt_amt (str(19)): D+2자동상환금액
      out_bfdy_tlex_amt (str(19)): 전일제비용금액
      out_thdt_tlex_amt (str(19)): 금일제비용금액
      out_tot_loan_amt (str(19)): 총대출금액
      out_scts_evlu_amt (str(19)): 유가평가금액
      out_tot_evlu_amt (str(19)): 총평가금액. 유가증권 평가금액 합계금액 + D+2 예수금
      out_nass_amt (str(19)): 순자산금액
      out_fncg_gld_auto_rdpt_yn (str(1)): 융자금자동상환여부. 보유현금에 대한 융자금만 차감여부 신용융자 매수체결 시점에서는 융자비율을 매매대금 100%로 계산 하였다가 수도결제일에 보증금에 해당하는 금액을 고객의 현금으로 충당하여 융자금을 감소시키는 업무
      out_pchs_amt_smtl_amt (str(19)): 매입금액합계금액
      out_evlu_amt_smtl_amt (str(19)): 평가금액합계금액. 유가증권 평가금액 합계금액
      out_evlu_pfls_smtl_amt (str(19)): 평가손익합계금액
      out_tot_stln_slng_chgs (str(19)): 총대주매각대금
      out_bfdy_tot_asst_evlu_amt (str(19)): 전일총자산평가금액
      out_asst_icdc_amt (str(19)): 자산증감액
      out_asst_icdc_erng_rt (str(31)): 자산증감수익율. 데이터 미제공
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'AFHR_FLPR_YN': in_AFHR_FLPR_YN,
      'OFL_YN': in_OFL_YN,
      'INQR_DVSN': in_INQR_DVSN,
      'UNPR_DVSN': in_UNPR_DVSN,
      'FUND_STTL_ICLD_YN': in_FUND_STTL_ICLD_YN,
      'FNCG_AMT_AUTO_RDPT_YN': in_FNCG_AMT_AUTO_RDPT_YN,
      'PRCS_DVSN': in_PRCS_DVSN,
      'CTX_AREA_FK100': in_CTX_AREA_FK100,
      'CTX_AREA_NK100': in_CTX_AREA_NK100,
      'api-id': 'v1_국내주식-006',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/inquire-balance'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_ctx_area_fk100'] = out_data['ctx_area_fk100']
    return_data['out_ctx_area_nk100'] = out_data['ctx_area_nk100']
    return_data['out_output1'] = out_data['output1']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_prdt_name'] = out_data['prdt_name']
    return_data['out_trad_dvsn_name'] = out_data['trad_dvsn_name']
    return_data['out_bfdy_buy_qty'] = out_data['bfdy_buy_qty']
    return_data['out_bfdy_sll_qty'] = out_data['bfdy_sll_qty']
    return_data['out_thdt_buyqty'] = out_data['thdt_buyqty']
    return_data['out_thdt_sll_qty'] = out_data['thdt_sll_qty']
    return_data['out_hldg_qty'] = out_data['hldg_qty']
    return_data['out_ord_psbl_qty'] = out_data['ord_psbl_qty']
    return_data['out_pchs_avg_pric'] = out_data['pchs_avg_pric']
    return_data['out_pchs_amt'] = out_data['pchs_amt']
    return_data['out_prpr'] = out_data['prpr']
    return_data['out_evlu_amt'] = out_data['evlu_amt']
    return_data['out_evlu_pfls_amt'] = out_data['evlu_pfls_amt']
    return_data['out_evlu_pfls_rt'] = out_data['evlu_pfls_rt']
    return_data['out_evlu_erng_rt'] = out_data['evlu_erng_rt']
    return_data['out_loan_dt'] = out_data['loan_dt']
    return_data['out_loan_amt'] = out_data['loan_amt']
    return_data['out_stln_slng_chgs'] = out_data['stln_slng_chgs']
    return_data['out_expd_dt'] = out_data['expd_dt']
    return_data['out_fltt_rt'] = out_data['fltt_rt']
    return_data['out_bfdy_cprs_icdc'] = out_data['bfdy_cprs_icdc']
    return_data['out_item_mgna_rt_name'] = out_data['item_mgna_rt_name']
    return_data['out_grta_rt_name'] = out_data['grta_rt_name']
    return_data['out_sbst_pric'] = out_data['sbst_pric']
    return_data['out_stck_loan_unpr'] = out_data['stck_loan_unpr']
    return_data['out_output2'] = out_data['output2']
    return_data['out_dnca_tot_amt'] = out_data['dnca_tot_amt']
    return_data['out_nxdy_excc_amt'] = out_data['nxdy_excc_amt']
    return_data['out_prvs_rcdl_excc_amt'] = out_data['prvs_rcdl_excc_amt']
    return_data['out_cma_evlu_amt'] = out_data['cma_evlu_amt']
    return_data['out_bfdy_buy_amt'] = out_data['bfdy_buy_amt']
    return_data['out_thdt_buy_amt'] = out_data['thdt_buy_amt']
    return_data['out_nxdy_auto_rdpt_amt'] = out_data['nxdy_auto_rdpt_amt']
    return_data['out_bfdy_sll_amt'] = out_data['bfdy_sll_amt']
    return_data['out_thdt_sll_amt'] = out_data['thdt_sll_amt']
    return_data['out_d2_auto_rdpt_amt'] = out_data['d2_auto_rdpt_amt']
    return_data['out_bfdy_tlex_amt'] = out_data['bfdy_tlex_amt']
    return_data['out_thdt_tlex_amt'] = out_data['thdt_tlex_amt']
    return_data['out_tot_loan_amt'] = out_data['tot_loan_amt']
    return_data['out_scts_evlu_amt'] = out_data['scts_evlu_amt']
    return_data['out_tot_evlu_amt'] = out_data['tot_evlu_amt']
    return_data['out_nass_amt'] = out_data['nass_amt']
    return_data['out_fncg_gld_auto_rdpt_yn'] = out_data['fncg_gld_auto_rdpt_yn']
    return_data['out_pchs_amt_smtl_amt'] = out_data['pchs_amt_smtl_amt']
    return_data['out_evlu_amt_smtl_amt'] = out_data['evlu_amt_smtl_amt']
    return_data['out_evlu_pfls_smtl_amt'] = out_data['evlu_pfls_smtl_amt']
    return_data['out_tot_stln_slng_chgs'] = out_data['tot_stln_slng_chgs']
    return_data['out_bfdy_tot_asst_evlu_amt'] = out_data['bfdy_tot_asst_evlu_amt']
    return_data['out_asst_icdc_amt'] = out_data['asst_icdc_amt']
    return_data['out_asst_icdc_erng_rt'] = out_data['asst_icdc_erng_rt']
    
    return return_data

  def get_trading_inquire_psbl_order(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_PDNO: str, in_ORD_UNPR: str, in_ORD_DVSN: str, in_CMA_EVLU_AMT_ICLD_YN: str, in_OVRS_ICLD_YN: str):
    """
    매수가능조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC8908R
    - 모의 TR_ID : VTTC8908R
    
    개요 : 매수가능 조회 API입니다. 
      실전계좌/모의계좌의 경우, 한 번의 호출에 최대 1건까지 확인 가능합니다.
      
      1) 매수가능금액 확인
       . 미수 사용 X: nrcvb_buy_amt(미수없는매수금액) 확인
       . 미수 사용 O: max_buy_amt(최대매수금액) 확인
      
      2) 매수가능수량 확인
       . 특정 종목 전량매수 시 가능수량을 확인하실 경우 ORD_DVSN:00(지정가)는 종목증거금율이 반영되지 않습니다. 
         따라서 "반드시" ORD_DVSN:01(시장가)로 지정하여 종목증거금율이 반영된 가능수량을 확인하시기 바랍니다. 
         (다만, 조건부지정가 등 특정 주문구분(ex.IOC)으로 주문 시 가능수량을 확인할 경우 주문 시와 동일한 주문구분(ex.IOC) 입력하여 가능수량 확인)
       . 미수 사용 X: ORD_DVSN:01(시장가) or 특정 주문구분(ex.IOC)로 지정하여 nrcvb_buy_qty(미수없는매수수량) 확인
       . 미수 사용 O: ORD_DVSN:01(시장가) or 특정 주문구분(ex.IOC)로 지정하여 max_buy_qty(최대매수수량) 확인
    
    Args:
      in_content_type (str(40)): 컨텐츠타입. application/json; charset=utf-8
      in_tr_id (str(13)): 거래ID(필수). [실전투자] TTTC8908R : 매수 가능 조회  [모의투자] VTTC8908R : 매수 가능 조회
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객타입. B : 법인 P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_PDNO (str(12)): 상품번호(필수). 종목번호(6자리) * PDNO, ORD_UNPR 공란 입력 시, 매수수량 없이 매수금액만 조회됨
      in_ORD_UNPR (str(19)): 주문단가(필수). 1주당 가격 * 시장가(ORD_DVSN:01)로 조회 시, 공란으로 입력 * PDNO, ORD_UNPR 공란 입력 시, 매수수량 없이 매수금액만 조회됨
      in_ORD_DVSN (str(2)): 주문구분(필수). * 특정 종목 전량매수 시 가능수량을 확인할 경우     00:지정가는 증거금율이 반영되지 않으므로     증거금율이 반영되는 01: 시장가로 조회 * 다만, 조건부지정가 등 특정 주문구분(ex.IOC)으로 주문 시 가능수량을 확인할 경우 주문 시와 동일한 주문구분(ex.IOC) 입력하여 가능수량 확인 * 종목별 매수가능수량 조회 없이 매수금액만 조회하고자 할 경우 임의값(00) 입력 00 : 지정가 01 : 시장가 02 : 조건부지정가 03 : 최유리지정가 04 : 최우선지정가 05 : 장전 시간외 06 : 장후 시간외 07 : 시간외 단일가 08 : 자기주식 09 : 자기주식S-Option 10 : 자기주식금전신탁 11 : IOC지정가 (즉시체결,잔량취소) 12 : FOK지정가 (즉시체결,전량취소) 13 : IOC시장가 (즉시체결,잔량취소) 14 : FOK시장가 (즉시체결,전량취소) 15 : IOC최유리 (즉시체결,잔량취소) 16 : FOK최유리 (즉시체결,전량취소) 51 : 장중대량 52 : 장중바스켓 62 : 장개시전 시간외대량 63 : 장개시전 시간외바스켓 67 : 장개시전 금전신탁자사주 69 : 장개시전 자기주식 72 : 시간외대량 77 : 시간외자사주신탁 79 : 시간외대량자기주식 80 : 바스켓
      in_CMA_EVLU_AMT_ICLD_YN (str(1)): CMA평가금액포함여부(필수). Y : 포함 N : 포함하지 않음
      in_OVRS_ICLD_YN (str(1)): 해외포함여부(필수). Y : 포함 N : 포함하지 않음
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부. 0 : 성공 0 이외의 값 : 실패
      out_msg_cd (str(8)): 응답코드. 응답코드
      out_msg1 (str(80)): 응답메세지. 응답메세지
      out_output (str): 응답상세. Single
      out_ord_psbl_cash (str(19)): 주문가능현금. 예수금으로 계산된 주문가능금액
      out_ord_psbl_sbst (str(19)): 주문가능대용
      out_ruse_psbl_amt (str(19)): 재사용가능금액. 전일/금일 매도대금으로 계산된 주문가능금액
      out_fund_rpch_chgs (str(19)): 펀드환매대금
      out_psbl_qty_calc_unpr (str(19)): 가능수량계산단가
      out_nrcvb_buy_amt (str(19)): 미수없는매수금액. 미수를 사용하지 않으실 경우 nrcvb_buy_amt(미수없는매수금액)을 확인
      out_nrcvb_buy_qty (str(10)): 미수없는매수수량. 미수를 사용하지 않으실 경우 nrcvb_buy_qty(미수없는매수수량)을 확인  * 특정 종목 전량매수 시 가능수량을 확인하실 경우   조회 시 ORD_DVSN:01(시장가)로 지정 필수 * 다만, 조건부지정가 등 특정 주문구분(ex.IOC)으로 주문 시 가능수량을 확인할 경우 주문 시와 동일한 주문구분(ex.IOC) 입력
      out_max_buy_amt (str(19)): 최대매수금액. 미수를 사용하시는 경우 max_buy_amt(최대매수금액)를 확인
      out_max_buy_qty (str(10)): 최대매수수량. 미수를 사용하시는 경우 max_buy_qty(최대매수수량)를 확인  * 특정 종목 전량매수 시 가능수량을 확인하실 경우   조회 시 ORD_DVSN:01(시장가)로 지정 필수 * 다만, 조건부지정가 등 특정 주문구분(ex.IOC)으로 주문 시 가능수량을 확인할 경우 주문 시와 동일한 주문구분(ex.IOC) 입력
      out_cma_evlu_amt (str(19)): CMA평가금액
      out_ovrs_re_use_amt_wcrc (str(19)): 해외재사용금액원화
      out_ord_psbl_frcr_amt_wcrc (str(19)): 주문가능외화금액원화
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'PDNO': in_PDNO,
      'ORD_UNPR': in_ORD_UNPR,
      'ORD_DVSN': in_ORD_DVSN,
      'CMA_EVLU_AMT_ICLD_YN': in_CMA_EVLU_AMT_ICLD_YN,
      'OVRS_ICLD_YN': in_OVRS_ICLD_YN,
      'api-id': 'v1_국내주식-007',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/inquire-psbl-order'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_ord_psbl_cash'] = out_data['ord_psbl_cash']
    return_data['out_ord_psbl_sbst'] = out_data['ord_psbl_sbst']
    return_data['out_ruse_psbl_amt'] = out_data['ruse_psbl_amt']
    return_data['out_fund_rpch_chgs'] = out_data['fund_rpch_chgs']
    return_data['out_psbl_qty_calc_unpr'] = out_data['psbl_qty_calc_unpr']
    return_data['out_nrcvb_buy_amt'] = out_data['nrcvb_buy_amt']
    return_data['out_nrcvb_buy_qty'] = out_data['nrcvb_buy_qty']
    return_data['out_max_buy_amt'] = out_data['max_buy_amt']
    return_data['out_max_buy_qty'] = out_data['max_buy_qty']
    return_data['out_cma_evlu_amt'] = out_data['cma_evlu_amt']
    return_data['out_ovrs_re_use_amt_wcrc'] = out_data['ovrs_re_use_amt_wcrc']
    return_data['out_ord_psbl_frcr_amt_wcrc'] = out_data['ord_psbl_frcr_amt_wcrc']
    
    return return_data

  def get_trading_inquire_psbl_sell(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_PDNO: str):
    """
    매도가능수량조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC8408R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 매도가능수량조회 API입니다. 
      한국투자 HTS(eFriend Plus) &gt; [0971] 주식 매도 화면에서 종목코드 입력 후 "가능" 클릭 시 매도가능수량이 확인되는 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
      특정종목 매도가능수량 확인 시, 매도주문 내시려는 주문종목(PDNO)으로 API 호출 후 
      output &gt; ord_psbl_qty(주문가능수량) 확인하실 수 있습니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC8408R
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 종합계좌번호
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌상품코드
      in_PDNO (str(12)): 종목번호(필수). 보유종목 코드 ex)000660
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output1 (str): 응답상세
      out_pdno (str(12)): 상품번호
      out_prdt_name (str(60)): 상품명
      out_buy_qty (str(10)): 매수수량
      out_sll_qty (str(10)): 매도수량
      out_cblc_qty (str(19)): 잔고수량
      out_nsvg_qty (str(19)): 비저축수량
      out_ord_psbl_qty (str(10)): 주문가능수량
      out_pchs_avg_pric (str(184)): 매입평균가격
      out_pchs_amt (str(19)): 매입금액
      out_now_pric (str(8)): 현재가
      out_evlu_amt (str(19)): 평가금액
      out_evlu_pfls_amt (str(19)): 평가손익금액
      out_evlu_pfls_rt (str(72)): 평가손익율
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'PDNO': in_PDNO,
      'api-id': '국내주식-165',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/inquire-psbl-sell'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output1'] = out_data['output1']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_prdt_name'] = out_data['prdt_name']
    return_data['out_buy_qty'] = out_data['buy_qty']
    return_data['out_sll_qty'] = out_data['sll_qty']
    return_data['out_cblc_qty'] = out_data['cblc_qty']
    return_data['out_nsvg_qty'] = out_data['nsvg_qty']
    return_data['out_ord_psbl_qty'] = out_data['ord_psbl_qty']
    return_data['out_pchs_avg_pric'] = out_data['pchs_avg_pric']
    return_data['out_pchs_amt'] = out_data['pchs_amt']
    return_data['out_now_pric'] = out_data['now_pric']
    return_data['out_evlu_amt'] = out_data['evlu_amt']
    return_data['out_evlu_pfls_amt'] = out_data['evlu_pfls_amt']
    return_data['out_evlu_pfls_rt'] = out_data['evlu_pfls_rt']
    
    return return_data

  def get_trading_inquire_credit_psamount(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_PDNO: str, in_ORD_UNPR: str, in_ORD_DVSN: str, in_CRDT_TYPE: str, in_CMA_EVLU_AMT_ICLD_YN: str, in_OVRS_ICLD_YN: str):
    """
    신용매수가능조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC8909R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 신용매수가능조회 API입니다.
      신용매수주문 시 주문가능수량과 금액을 확인하실 수 있습니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC8909R
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_PDNO (str(12)): 상품번호(필수). 종목코드(6자리)
      in_ORD_UNPR (str(19)): 주문단가(필수). 1주당 가격  * 장전 시간외, 장후 시간외, 시장가의 경우 1주당 가격을 공란으로 비우지 않음 "0"으로 입력 권고
      in_ORD_DVSN (str(2)): 주문구분(필수). 00 : 지정가  01 : 시장가  02 : 조건부지정가  03 : 최유리지정가  04 : 최우선지정가  05 : 장전 시간외  06 : 장후 시간외  07 : 시간외 단일가  등
      in_CRDT_TYPE (str(2)): 신용유형(필수). 21 : 자기융자신규  23 : 유통융자신규  26 : 유통대주상환  28 : 자기대주상환  25 : 자기융자상환  27 : 유통융자상환  22 : 유통대주신규  24 : 자기대주신규
      in_CMA_EVLU_AMT_ICLD_YN (str(1)): CMA평가금액포함여부(필수). Y/N
      in_OVRS_ICLD_YN (str(1)): 해외포함여부(필수). Y/N
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부. 0 : 성공 0 이외의 값 : 실패
      out_msg_cd (str(8)): 응답코드. 응답코드
      out_msg1 (str(80)): 응답메세지. 응답메시지
      out_output (str): 응답상세
      out_ord_psbl_cash (str(19)): 주문가능현금
      out_ord_psbl_sbst (str(19)): 주문가능대용
      out_ruse_psbl_amt (str(19)): 재사용가능금액
      out_fund_rpch_chgs (str(19)): 펀드환매대금
      out_psbl_qty_calc_unpr (str(19)): 가능수량계산단가
      out_nrcvb_buy_amt (str(19)): 미수없는매수금액
      out_nrcvb_buy_qty (str(10)): 미수없는매수수량
      out_max_buy_amt (str(19)): 최대매수금액
      out_max_buy_qty (str(10)): 최대매수수량
      out_cma_evlu_amt (str(19)): CMA평가금액
      out_ovrs_re_use_amt_wcrc (str(19)): 해외재사용금액원화
      out_ord_psbl_frcr_amt_wcrc (str(19)): 주문가능외화금액원화
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'PDNO': in_PDNO,
      'ORD_UNPR': in_ORD_UNPR,
      'ORD_DVSN': in_ORD_DVSN,
      'CRDT_TYPE': in_CRDT_TYPE,
      'CMA_EVLU_AMT_ICLD_YN': in_CMA_EVLU_AMT_ICLD_YN,
      'OVRS_ICLD_YN': in_OVRS_ICLD_YN,
      'api-id': 'v1_국내주식-042',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/inquire-credit-psamount'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_ord_psbl_cash'] = out_data['ord_psbl_cash']
    return_data['out_ord_psbl_sbst'] = out_data['ord_psbl_sbst']
    return_data['out_ruse_psbl_amt'] = out_data['ruse_psbl_amt']
    return_data['out_fund_rpch_chgs'] = out_data['fund_rpch_chgs']
    return_data['out_psbl_qty_calc_unpr'] = out_data['psbl_qty_calc_unpr']
    return_data['out_nrcvb_buy_amt'] = out_data['nrcvb_buy_amt']
    return_data['out_nrcvb_buy_qty'] = out_data['nrcvb_buy_qty']
    return_data['out_max_buy_amt'] = out_data['max_buy_amt']
    return_data['out_max_buy_qty'] = out_data['max_buy_qty']
    return_data['out_cma_evlu_amt'] = out_data['cma_evlu_amt']
    return_data['out_ovrs_re_use_amt_wcrc'] = out_data['ovrs_re_use_amt_wcrc']
    return_data['out_ord_psbl_frcr_amt_wcrc'] = out_data['ord_psbl_frcr_amt_wcrc']
    
    return return_data

  def get_trading_order_resv(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_PDNO: str, in_ORD_QTY: str, in_ORD_UNPR: str, in_SLL_BUY_DVSN_CD: str, in_ORD_DVSN_CD: str, in_ORD_OBJT_CBLC_DVSN_CD: str, in_LOAN_DT: str, in_RSVN_ORD_END_DT: str, in_LDNG_DT: str):
    """
    주식예약주문
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : CTSC0008U
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 국내주식 예약주문 매수/매도 API 입니다.
      ※ POST API의 경우 BODY값의 key값들을 대문자로 작성하셔야 합니다.
         (EX. "CANO" : "12345678", "ACNT_PRDT_CD": "01",...)
      ※ 유의사항
       1. 예약주문 가능시간 : 15시 40분 ~ 다음 영업일 7시 30분 
          (단, 서버 초기화 작업 시 예약주문 불가 : 23시 40분 ~ 00시 10분)
          ※ 예약주문 처리내역은 통보되지 않으므로 주문처리일 장 시작전에 반드시 주문처리 결과를 확인하시기 바랍니다.
       2. 예약주문 안내
         - 예약종료일 미입력 시 일반예약주문으로 최초 도래하는 영업일에 주문 전송됩니다.
         - 예약종료일 입력 시 기간예약주문으로 최초 예약주문수량 중 미체결 된 수량에 대해 예약종료일까지 매 영업일 주문이
            실행됩니다. (예약종료일은 익영업일부터 달력일 기준으로 공휴일 포함하여 최대 30일이 되는 일자까지 입력가능)
         - 예약주문 접수 처리순서는 일반/기간예약주문 중 신청일자가 빠른 주문이 우선합니다.
            단, 기간예약주문 자동배치시간(약 15시35분 ~ 15시55분)사이 접수되는 주문의 경우 당일에 한해 순서와 상관없이
            처리될 수 있습니다.
         - 기간예약주문 자동배치시간(약 15시35분 ~ 15시55분)에는 예약주문 조회가 제한 될 수 있습니다.
         - 기간예약주문은 계좌 당 주문건수 최대 1,000건으로 제한됩니다.
      3. 예약주문 접수내역 중 아래의 사유 등으로 인해 주문이 거부될 수 있사오니, 주문처리일 장 시작전에 반드시
          주문처리 결과를 확인하시기 바랍니다.
          * 주문처리일 기준 : 매수가능금액 부족, 매도가능수량 부족, 주문수량/호가단위 오류, 대주 호가제한, 
                                    신용/대주가능종목 변경, 상/하한폭 변경, 시가형성 종목(신규상장 등)의 시장가, 거래서비스 미신청 등
       4. 익일 예상 상/하한가는 조회시점의 현재가로 계산되며 익일의 유/무상증자, 배당, 감자, 합병, 액면변경 등에 의해
          변동될 수 있으며 이로 인해 상/하한가를 벗어나 주문이 거부되는 경우가 발생할 수 있사오니, 주문처리일 장 시작전에
          반드시 주문처리결과를 확인하시기 바랍니다.
       5. 정리매매종목, ELW, 신주인수권증권, 신주인수권증서 등은 가격제한폭(상/하한가) 적용 제외됩니다.
       6. 영업일 장 시작 후 [기간예약주문] 내역 취소는 해당시점 이후의 예약주문이 취소되는 것으로, 
          일반주문으로 이미 전환된 주문에는 영향을 미치지 않습니다. 반드시 장 시작전 주문처리결과를 확인하시기 바랍니다.
    
    Args:
      in_content_type (str(40)): 컨텐츠타입. application/json; charset=utf-8
      in_tr_id (str(13)): 거래ID(필수). [실전투자] CTSC0008U : 국내예약매수입력/주문예약매도입력
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객타입. B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_PDNO (str(12)): 종목코드(6자리)(필수)
      in_ORD_QTY (str(10)): 주문수량(필수). 주문주식수
      in_ORD_UNPR (str(19)): 주문단가(필수). 1주당 가격  * 장전 시간외, 시장가의 경우 1주당 가격을 공란으로 비우지 않음 "0"으로 입력 권고
      in_SLL_BUY_DVSN_CD (str(2)): 매도매수구분코드(필수). 01 : 매도 02 : 매수
      in_ORD_DVSN_CD (str(2)): 주문구분코드(필수). 00 : 지정가 01 : 시장가 02 : 조건부지정가 05 : 장전 시간외
      in_ORD_OBJT_CBLC_DVSN_CD (str(2)): 주문대상잔고구분코드(필수). [매도매수구분코드 01:매도/02:매수시 사용] 10 : 현금   [매도매수구분코드 01:매도시 사용] 12 : 주식담보대출  14 : 대여상환 21 : 자기융자신규 22 : 유통대주신규 23 : 유통융자신규 24 : 자기대주신규 25 : 자기융자상환 26 : 유통대주상환 27 : 유통융자상환 28 : 자기대주상환
      in_LOAN_DT (str(8)): 대출일자
      in_RSVN_ORD_END_DT (str(8)): 예약주문종료일자. (YYYYMMDD) 현재 일자보다 이후로 설정해야 함 * RSVN_ORD_END_DT(예약주문종료일자)를 안 넣으면 다음날 주문처리되고 예약주문은 종료됨 * RSVN_ORD_END_DT(예약주문종료일자)는 익영업일부터 달력일 기준으로 공휴일 포함하여 최대 30일이 되는 일자까지 입력 가능
      in_LDNG_DT (str(8)): 대여일자
    
    Returns:
      out_rt_cd (str(1)): 성공 실패 여부. 0 : 성공  0 이외의 값 : 실패
      out_msg_cd (str(8)): 응답코드
      out_msg (str(80)): 응답메세지
      out_output (str): 응답상세. Array
      out_rsvn_ord_seq (str(10)): 예약주문 순번
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'api-id': 'v1_국내주식-017',
    }
    params = {
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'PDNO': in_PDNO,
      'ORD_QTY': in_ORD_QTY,
      'ORD_UNPR': in_ORD_UNPR,
      'SLL_BUY_DVSN_CD': in_SLL_BUY_DVSN_CD,
      'ORD_DVSN_CD': in_ORD_DVSN_CD,
      'ORD_OBJT_CBLC_DVSN_CD': in_ORD_OBJT_CBLC_DVSN_CD,
      'LOAN_DT': in_LOAN_DT,
      'RSVN_ORD_END_DT': in_RSVN_ORD_END_DT,
      'LDNG_DT': in_LDNG_DT,
    }
    url = '/uapi/domestic-stock/v1/trading/order-resv'
    
    header_data, out_data = self._send_request(url, 'POST', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg'] = out_data['msg']
    return_data['out_output'] = out_data['output']
    return_data['out_rsvn_ord_seq'] = out_data['rsvn_ord_seq']
    
    return return_data

  def get_trading_order_resv_rvsecncl(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_PDNO: str, in_ORD_QTY: str, in_ORD_UNPR: str, in_SLL_BUY_DVSN_CD: str, in_ORD_DVSN_CD: str, in_ORD_OBJT_CBLC_DVSN_CD: str, in_LOAN_DT: str, in_RSVN_ORD_END_DT: str, in_CTAL_TLNO: str, in_RSVN_ORD_SEQ: str, in_RSVN_ORD_ORGNO: str, in_RSVN_ORD_ORD_DT: str):
    """
    주식예약주문정정취소
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : (예약취소) CTSC0009U (예약정정) CTSC0013U
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 국내주식 예약주문 정정/취소 API 입니다.
      *  정정주문은 취소주문에 비해 필수 입력값이 추가 됩니다. 
         하단의 입력값을 참조하시기 바랍니다.
      ※ POST API의 경우 BODY값의 key값들을 대문자로 작성하셔야 합니다.
         (EX. "CANO" : "12345678", "ACNT_PRDT_CD": "01",...)
    
    Args:
      in_content_type (str(40)): 컨텐츠타입. application/json; charset=utf-8
      in_tr_id (str(13)): 거래ID(필수). [실전투자] CTSC0009U : 국내주식예약취소주문 CTSC0013U : 국내주식예약정정주문 * 모의투자 사용 불가
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객타입. B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). [정정/취소] 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). [정정/취소] 계좌번호 체계(8-2)의 뒤 2자리
      in_PDNO (str(12)): 종목코드(6자리)(필수). [정정]
      in_ORD_QTY (str(10)): 주문수량(필수). [정정] 주문주식수
      in_ORD_UNPR (str(19)): 주문단가(필수). [정정] 1주당 가격  * 장전 시간외, 시장가의 경우 1주당 가격을 공란으로 비우지 않음 "0"으로 입력 권고
      in_SLL_BUY_DVSN_CD (str(2)): 매도매수구분코드(필수). [정정] 01 : 매도 02 : 매수
      in_ORD_DVSN_CD (str(2)): 주문구분코드(필수). [정정] 00 : 지정가 01 : 시장가 02 : 조건부지정가 05 : 장전 시간외
      in_ORD_OBJT_CBLC_DVSN_CD (str(2)): 주문대상잔고구분코드(필수). [정정] 10 : 현금 12 : 주식담보대출 14 : 대여상환 21 : 자기융자신규 22 : 유통대주신규 23 : 유통융자신규 24 : 자기대주신규 25 : 자기융자상환 26 : 유통대주상환 27 : 유통융자상환 28 : 자기대주상환
      in_LOAN_DT (str(8)): 대출일자. [정정]
      in_RSVN_ORD_END_DT (str(8)): 예약주문종료일자. [정정]
      in_CTAL_TLNO (str(20)): 연락전화번호. [정정]
      in_RSVN_ORD_SEQ (str(10)): 예약주문순번(필수). [정정/취소]
      in_RSVN_ORD_ORGNO (str(5)): 예약주문조직번호. [정정/취소]
      in_RSVN_ORD_ORD_DT (str(8)): 예약주문주문일자. [정정/취소]
    
    Returns:
      out_rt_cd (str(1)): 성공 실패 여부. 0 : 성공  0 이외의 값 : 실패
      out_msg_cd (str(8)): 응답코드
      out_msg (str(80)): 응답메세지
      out_output (str): 응답상세
      out_nrml_prcs_yn (str(1)): 정상처리여부
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'api-id': 'v1_국내주식-018,019',
    }
    params = {
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'PDNO': in_PDNO,
      'ORD_QTY': in_ORD_QTY,
      'ORD_UNPR': in_ORD_UNPR,
      'SLL_BUY_DVSN_CD': in_SLL_BUY_DVSN_CD,
      'ORD_DVSN_CD': in_ORD_DVSN_CD,
      'ORD_OBJT_CBLC_DVSN_CD': in_ORD_OBJT_CBLC_DVSN_CD,
      'LOAN_DT': in_LOAN_DT,
      'RSVN_ORD_END_DT': in_RSVN_ORD_END_DT,
      'CTAL_TLNO': in_CTAL_TLNO,
      'RSVN_ORD_SEQ': in_RSVN_ORD_SEQ,
      'RSVN_ORD_ORGNO': in_RSVN_ORD_ORGNO,
      'RSVN_ORD_ORD_DT': in_RSVN_ORD_ORD_DT,
    }
    url = '/uapi/domestic-stock/v1/trading/order-resv-rvsecncl'
    
    header_data, out_data = self._send_request(url, 'POST', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg'] = out_data['msg']
    return_data['out_output'] = out_data['output']
    return_data['out_nrml_prcs_yn'] = out_data['nrml_prcs_yn']
    
    return return_data

  def get_trading_order_resv_ccnl(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_RSVN_ORD_ORD_DT: str, in_RSVN_ORD_END_DT: str, in_RSVN_ORD_SEQ: str, in_TMNL_MDIA_KIND_CD: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_PRCS_DVSN_CD: str, in_CNCL_YN: str, in_PDNO: str, in_SLL_BUY_DVSN_CD: str, in_CTX_AREA_FK200: str, in_CTX_AREA_NK200: str):
    """
    주식예약주문조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : CTSC0004R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 국내예약주문 처리내역 조회 API 입니다.
      실전계좌/모의계좌의 경우, 한 번의 호출에 최대 20건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다.
    
    Args:
      in_content_type (str(40)): 컨텐츠타입. application/json; charset=utf-8
      in_tr_id (str(13)): 거래ID(필수). [실전투자] CTSC0004R : 국내주식예약주문조회 * 모의투자 사용 불가
      in_tr_cont (str(1)): 연속 거래 여부. 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우)
      in_custtype (str(1)): 고객타입. B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_RSVN_ORD_ORD_DT (str(8)): 예약주문시작일자(필수)
      in_RSVN_ORD_END_DT (str(8)): 예약주문종료일자(필수)
      in_RSVN_ORD_SEQ (str(10)): 예약주문순번(필수)
      in_TMNL_MDIA_KIND_CD (str(2)): 단말매체종류코드(필수). "00" 입력
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_PRCS_DVSN_CD (str(2)): 처리구분코드(필수). 0: 전체 1: 처리내역 2: 미처리내역
      in_CNCL_YN (str(1)): 취소여부(필수). "Y" 유효한 주문만 조회
      in_PDNO (str(12)): 상품번호(필수). 종목코드(6자리) (공백 입력 시 전체 조회)
      in_SLL_BUY_DVSN_CD (str(2)): 매도매수구분코드(필수)
      in_CTX_AREA_FK200 (str(200)): 연속조회검색조건200(필수). 다음 페이지 조회시 사용
      in_CTX_AREA_NK200 (str(200)): 연속조회키200(필수). 다음 페이지 조회시 사용
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. F or M : 다음 데이터 있음 D or E : 마지막 데이터
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부. 0 : 성공  0 이외의 값 : 실패
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output (str): 응답상세
      out_rsvn_ord_seq (str(10)): 예약주문 순번
      out_rsvn_ord_ord_dt (str(8)): 예약주문주문일자
      out_rsvn_ord_rcit_dt (str(8)): 예약주문접수일자
      out_pdno (str(12)): 상품번호
      out_ord_dvsn_cd (str(2)): 주문구분코드
      out_ord_rsvn_qty (str(10)): 주문예약수량
      out_tot_ccld_qty (str(10)): 총체결수량
      out_cncl_ord_dt (str(8)): 취소주문일자
      out_ord_tmd (str(6)): 주문시각
      out_ctac_tlno (str(20)): 연락전화번호
      out_rjct_rson2 (str(200)): 거부사유2
      out_odno (str(10)): 주문번호
      out_rsvn_ord_rcit_tmd (str(6)): 예약주문접수시각
      out_kor_item_shtn_name (str(60)): 한글종목단축명
      out_sll_buy_dvsn_cd (str(2)): 매도매수구분코드
      out_ord_rsvn_unpr (str(19)): 주문예약단가
      out_tot_ccld_amt (str(19)): 총체결금액
      out_loan_dt (str(8)): 대출일자
      out_cncl_rcit_tmd (str(6)): 취소접수시각
      out_prcs_rslt (str(60)): 처리결과
      out_ord_dvsn_name (str(60)): 주문구분명
      out_tmnl_mdia_kind_cd (str(2)): 단말매체종류코드
      out_rsvn_end_dt (str(8)): 예약종료일자
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'RSVN_ORD_ORD_DT': in_RSVN_ORD_ORD_DT,
      'RSVN_ORD_END_DT': in_RSVN_ORD_END_DT,
      'RSVN_ORD_SEQ': in_RSVN_ORD_SEQ,
      'TMNL_MDIA_KIND_CD': in_TMNL_MDIA_KIND_CD,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'PRCS_DVSN_CD': in_PRCS_DVSN_CD,
      'CNCL_YN': in_CNCL_YN,
      'PDNO': in_PDNO,
      'SLL_BUY_DVSN_CD': in_SLL_BUY_DVSN_CD,
      'CTX_AREA_FK200': in_CTX_AREA_FK200,
      'CTX_AREA_NK200': in_CTX_AREA_NK200,
      'api-id': 'v1_국내주식-020',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/order-resv-ccnl'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_rsvn_ord_seq'] = out_data['rsvn_ord_seq']
    return_data['out_rsvn_ord_ord_dt'] = out_data['rsvn_ord_ord_dt']
    return_data['out_rsvn_ord_rcit_dt'] = out_data['rsvn_ord_rcit_dt']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_ord_dvsn_cd'] = out_data['ord_dvsn_cd']
    return_data['out_ord_rsvn_qty'] = out_data['ord_rsvn_qty']
    return_data['out_tot_ccld_qty'] = out_data['tot_ccld_qty']
    return_data['out_cncl_ord_dt'] = out_data['cncl_ord_dt']
    return_data['out_ord_tmd'] = out_data['ord_tmd']
    return_data['out_ctac_tlno'] = out_data['ctac_tlno']
    return_data['out_rjct_rson2'] = out_data['rjct_rson2']
    return_data['out_odno'] = out_data['odno']
    return_data['out_rsvn_ord_rcit_tmd'] = out_data['rsvn_ord_rcit_tmd']
    return_data['out_kor_item_shtn_name'] = out_data['kor_item_shtn_name']
    return_data['out_sll_buy_dvsn_cd'] = out_data['sll_buy_dvsn_cd']
    return_data['out_ord_rsvn_unpr'] = out_data['ord_rsvn_unpr']
    return_data['out_tot_ccld_amt'] = out_data['tot_ccld_amt']
    return_data['out_loan_dt'] = out_data['loan_dt']
    return_data['out_cncl_rcit_tmd'] = out_data['cncl_rcit_tmd']
    return_data['out_prcs_rslt'] = out_data['prcs_rslt']
    return_data['out_ord_dvsn_name'] = out_data['ord_dvsn_name']
    return_data['out_tmnl_mdia_kind_cd'] = out_data['tmnl_mdia_kind_cd']
    return_data['out_rsvn_end_dt'] = out_data['rsvn_end_dt']
    
    return return_data

  def get_trading_pension_inquire_present_balance(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_USER_DVSN_CD: str, in_CTX_AREA_FK100: str, in_CTX_AREA_NK100: str):
    """
    퇴직연금 체결기준잔고
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC2202R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : ​※ 55번 계좌(DC가입자계좌)의 경우 해당 API 이용이 불가합니다.
      KIS Developers API의 경우 HTS ID에 반드시 연결되어있어야만 API 신청 및 앱정보 발급이 가능한 서비스로 개발되어서 실물계좌가 아닌 55번 계좌는 API 이용이 불가능한 점 양해 부탁드립니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC2202R
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수)
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 29
      in_USER_DVSN_CD (str(2)): 사용자구분코드(필수). 00
      in_CTX_AREA_FK100 (str(100)): 연속조회검색조건100(필수)
      in_CTX_AREA_NK100 (str(100)): 연속조회키100(필수)
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output1 (str): 응답상세1. Array
      out_cblc_dvsn (str(2)): 잔고구분
      out_cblc_dvsn_name (str(60)): 잔고구분명
      out_pdno (str(12)): 상품번호
      out_prdt_name (str(60)): 상품명
      out_hldg_qty (str(19)): 보유수량
      out_slpsb_qty (str(10)): 매도가능수량
      out_pchs_avg_pric (str(184)): 매입평균가격
      out_evlu_pfls_amt (str(19)): 평가손익금액
      out_evlu_pfls_rt (str(72)): 평가손익율
      out_prpr (str(19)): 현재가
      out_evlu_amt (str(19)): 평가금액
      out_pchs_amt (str(19)): 매입금액
      out_cblc_weit (str(238)): 잔고비중
      out_output2 (str): 응답상세2. Array
      out_pchs_amt_smtl_amt (str(19)): 매입금액합계금액
      out_evlu_amt_smtl_amt (str(19)): 평가금액합계금액
      out_evlu_pfls_smtl_amt (str(19)): 평가손익합계금액
      out_trad_pfls_smtl (str(19)): 매매손익합계
      out_thdt_tot_pfls_amt (str(19)): 당일총손익금액
      out_pftrt (str(238)): 수익률
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'USER_DVSN_CD': in_USER_DVSN_CD,
      'CTX_AREA_FK100': in_CTX_AREA_FK100,
      'CTX_AREA_NK100': in_CTX_AREA_NK100,
      'api-id': 'v1_국내주식-032',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/pension/inquire-present-balance'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output1'] = out_data['output1']
    return_data['out_cblc_dvsn'] = out_data['cblc_dvsn']
    return_data['out_cblc_dvsn_name'] = out_data['cblc_dvsn_name']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_prdt_name'] = out_data['prdt_name']
    return_data['out_hldg_qty'] = out_data['hldg_qty']
    return_data['out_slpsb_qty'] = out_data['slpsb_qty']
    return_data['out_pchs_avg_pric'] = out_data['pchs_avg_pric']
    return_data['out_evlu_pfls_amt'] = out_data['evlu_pfls_amt']
    return_data['out_evlu_pfls_rt'] = out_data['evlu_pfls_rt']
    return_data['out_prpr'] = out_data['prpr']
    return_data['out_evlu_amt'] = out_data['evlu_amt']
    return_data['out_pchs_amt'] = out_data['pchs_amt']
    return_data['out_cblc_weit'] = out_data['cblc_weit']
    return_data['out_output2'] = out_data['output2']
    return_data['out_pchs_amt_smtl_amt'] = out_data['pchs_amt_smtl_amt']
    return_data['out_evlu_amt_smtl_amt'] = out_data['evlu_amt_smtl_amt']
    return_data['out_evlu_pfls_smtl_amt'] = out_data['evlu_pfls_smtl_amt']
    return_data['out_trad_pfls_smtl'] = out_data['trad_pfls_smtl']
    return_data['out_thdt_tot_pfls_amt'] = out_data['thdt_tot_pfls_amt']
    return_data['out_pftrt'] = out_data['pftrt']
    
    return return_data

  def get_trading_pension_inquire_daily_ccld(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_USER_DVSN_CD: str, in_SLL_BUY_DVSN_CD: str, in_CCLD_NCCS_DVSN: str, in_INQR_DVSN_3: str, in_CTX_AREA_FK100: str, in_CTX_AREA_NK100: str):
    """
    퇴직연금 미체결내역
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC2201R(기존 KRX만 가능), TTTC2210R (KRX,NXT/SOR)
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : ​※ 55번 계좌(DC가입자계좌)의 경우 해당 API 이용이 불가합니다.
      KIS Developers API의 경우 HTS ID에 반드시 연결되어있어야만 API 신청 및 앱정보 발급이 가능한 서비스로 개발되어서 실물계좌가 아닌 55번 계좌는 API 이용이 불가능한 점 양해 부탁드립니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC2201R(기존 KRX만 가능), TTTC2210R (KRX,NXT/SOR)
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수)
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 29
      in_USER_DVSN_CD (str(2)): 사용자구분코드(필수). %%
      in_SLL_BUY_DVSN_CD (str(2)): 매도매수구분코드(필수). 00 : 전체 / 01 : 매도 / 02 : 매수
      in_CCLD_NCCS_DVSN (str(2)): 체결미체결구분(필수). %% : 전체 / 01 : 체결 / 02 : 미체결
      in_INQR_DVSN_3 (str(2)): 조회구분3(필수). 00 : 전체
      in_CTX_AREA_FK100 (str(100)): 연속조회검색조건100(필수)
      in_CTX_AREA_NK100 (str(100)): 연속조회키100(필수)
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output (str): 응답상세1. Array
      out_ord_gno_brno (str(5)): 주문채번지점번호
      out_sll_buy_dvsn_cd (str(2)): 매도매수구분코드
      out_trad_dvsn_name (str(60)): 매매구분명
      out_odno (str(10)): 주문번호
      out_pdno (str(12)): 상품번호
      out_prdt_name (str(60)): 상품명
      out_ord_unpr (str(19)): 주문단가
      out_ord_qty (str(10)): 주문수량
      out_tot_ccld_qty (str(10)): 총체결수량
      out_nccs_qty (str(10)): 미체결수량
      out_ord_dvsn_cd (str(2)): 주문구분코드
      out_ord_dvsn_name (str(60)): 주문구분명
      out_orgn_odno (str(10)): 원주문번호
      out_ord_tmd (str(6)): 주문시각
      out_objt_cust_dvsn_name (str(10)): 대상고객구분명
      out_pchs_avg_pric (str(184)): 매입평균가격
      out_stpm_cndt_pric (str(9)): 스톱지정가조건가격. 신규 API용 필드
      out_stpm_efct_occr_dtmd (str(9)): 스톱지정가효력발생상세시각. 신규 API용 필드
      out_stpm_efct_occr_yn (str(1)): 스톱지정가효력발생여부. 신규 API용 필드
      out_excg_id_dvsn_cd (str(3)): 거래소ID구분코드. 신규 API용 필드
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'USER_DVSN_CD': in_USER_DVSN_CD,
      'SLL_BUY_DVSN_CD': in_SLL_BUY_DVSN_CD,
      'CCLD_NCCS_DVSN': in_CCLD_NCCS_DVSN,
      'INQR_DVSN_3': in_INQR_DVSN_3,
      'CTX_AREA_FK100': in_CTX_AREA_FK100,
      'CTX_AREA_NK100': in_CTX_AREA_NK100,
      'api-id': 'v1_국내주식-033',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/pension/inquire-daily-ccld'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_ord_gno_brno'] = out_data['ord_gno_brno']
    return_data['out_sll_buy_dvsn_cd'] = out_data['sll_buy_dvsn_cd']
    return_data['out_trad_dvsn_name'] = out_data['trad_dvsn_name']
    return_data['out_odno'] = out_data['odno']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_prdt_name'] = out_data['prdt_name']
    return_data['out_ord_unpr'] = out_data['ord_unpr']
    return_data['out_ord_qty'] = out_data['ord_qty']
    return_data['out_tot_ccld_qty'] = out_data['tot_ccld_qty']
    return_data['out_nccs_qty'] = out_data['nccs_qty']
    return_data['out_ord_dvsn_cd'] = out_data['ord_dvsn_cd']
    return_data['out_ord_dvsn_name'] = out_data['ord_dvsn_name']
    return_data['out_orgn_odno'] = out_data['orgn_odno']
    return_data['out_ord_tmd'] = out_data['ord_tmd']
    return_data['out_objt_cust_dvsn_name'] = out_data['objt_cust_dvsn_name']
    return_data['out_pchs_avg_pric'] = out_data['pchs_avg_pric']
    return_data['out_stpm_cndt_pric'] = out_data['stpm_cndt_pric']
    return_data['out_stpm_efct_occr_dtmd'] = out_data['stpm_efct_occr_dtmd']
    return_data['out_stpm_efct_occr_yn'] = out_data['stpm_efct_occr_yn']
    return_data['out_excg_id_dvsn_cd'] = out_data['excg_id_dvsn_cd']
    
    return return_data

  def get_trading_pension_inquire_psbl_order(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_PDNO: str, in_ACCA_DVSN_CD: str, in_CMA_EVLU_AMT_ICLD_YN: str, in_ORD_DVSN: str, in_ORD_UNPR: str):
    """
    퇴직연금 매수가능조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC0503R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : ​※ 55번 계좌(DC가입자계좌)의 경우 해당 API 이용이 불가합니다.
      KIS Developers API의 경우 HTS ID에 반드시 연결되어있어야만 API 신청 및 앱정보 발급이 가능한 서비스로 개발되어서 실물계좌가 아닌 55번 계좌는 API 이용이 불가능한 점 양해 부탁드립니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC0503R
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수)
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 29
      in_PDNO (str(12)): 상품번호(필수)
      in_ACCA_DVSN_CD (str(2)): 적립금구분코드(필수). 00
      in_CMA_EVLU_AMT_ICLD_YN (str(1)): CMA평가금액포함여부(필수)
      in_ORD_DVSN (str(2)): 주문구분(필수). 00 : 지정가 / 01 : 시장가
      in_ORD_UNPR (str(19)): 주문단가(필수)
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output (str): 응답상세1
      out_ord_psbl_cash (str(19)): 주문가능현금
      out_ruse_psbl_amt (str(19)): 재사용가능금액
      out_psbl_qty_calc_unpr (str(19)): 가능수량계산단가
      out_max_buy_amt (str(19)): 최대매수금액
      out_max_buy_qty (str(10)): 최대매수수량
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'PDNO': in_PDNO,
      'ACCA_DVSN_CD': in_ACCA_DVSN_CD,
      'CMA_EVLU_AMT_ICLD_YN': in_CMA_EVLU_AMT_ICLD_YN,
      'ORD_DVSN': in_ORD_DVSN,
      'ORD_UNPR': in_ORD_UNPR,
      'api-id': 'v1_국내주식-034',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/pension/inquire-psbl-order'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_ord_psbl_cash'] = out_data['ord_psbl_cash']
    return_data['out_ruse_psbl_amt'] = out_data['ruse_psbl_amt']
    return_data['out_psbl_qty_calc_unpr'] = out_data['psbl_qty_calc_unpr']
    return_data['out_max_buy_amt'] = out_data['max_buy_amt']
    return_data['out_max_buy_qty'] = out_data['max_buy_qty']
    
    return return_data

  def get_trading_pension_inquire_deposit(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_ACCA_DVSN_CD: str):
    """
    퇴직연금 예수금조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC0506R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : ​※ 55번 계좌(DC가입자계좌)의 경우 해당 API 이용이 불가합니다.
      KIS Developers API의 경우 HTS ID에 반드시 연결되어있어야만 API 신청 및 앱정보 발급이 가능한 서비스로 개발되어서 실물계좌가 아닌 55번 계좌는 API 이용이 불가능한 점 양해 부탁드립니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC0506R
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수)
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 29
      in_ACCA_DVSN_CD (str(2)): 적립금구분코드(필수). 00
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output (str): 응답상세1
      out_dnca_tota (str(19)): 예수금총액
      out_nxdy_excc_amt (str(19)): 익일정산액
      out_nxdy_sttl_amt (str(19)): 익일결제금액
      out_nx2_day_sttl_amt (str(19)): 2익일결제금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'ACCA_DVSN_CD': in_ACCA_DVSN_CD,
      'api-id': 'v1_국내주식-035',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/pension/inquire-deposit'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_dnca_tota'] = out_data['dnca_tota']
    return_data['out_nxdy_excc_amt'] = out_data['nxdy_excc_amt']
    return_data['out_nxdy_sttl_amt'] = out_data['nxdy_sttl_amt']
    return_data['out_nx2_day_sttl_amt'] = out_data['nx2_day_sttl_amt']
    
    return return_data

  def get_trading_pension_inquire_balance(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_ACCA_DVSN_CD: str, in_INQR_DVSN: str, in_CTX_AREA_FK100: str, in_CTX_AREA_NK100: str):
    """
    퇴직연금 잔고조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC2208R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 주식, ETF, ETN만 조회 가능하며 펀드는 조회 불가합니다.
      ​※ 55번 계좌(DC가입자계좌)의 경우 해당 API 이용이 불가합니다.
      KIS Developers API의 경우 HTS ID에 반드시 연결되어있어야만 API 신청 및 앱정보 발급이 가능한 서비스로 개발되어서 실물계좌가 아닌 55번 계좌는 API 이용이 불가능한 점 양해 부탁드립니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC2208R
      in_tr_cont (str(1)): 연속 거래 여부. 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우)
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수)
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 29
      in_ACCA_DVSN_CD (str(2)): 적립금구분코드(필수). 00
      in_INQR_DVSN (str(2)): 조회구분(필수). 00 : 전체
      in_CTX_AREA_FK100 (str(100)): 연속조회검색조건100(필수)
      in_CTX_AREA_NK100 (str(100)): 연속조회키100(필수)
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. F or M : 다음 데이터 있음 D or E : 마지막 데이터
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output1 (str): 응답상세. Array
      out_cblc_dvsn_name (str(60)): 잔고구분명
      out_prdt_name (str(60)): 상품명
      out_pdno (str(12)): 상품번호
      out_item_dvsn_name (str(60)): 종목구분명
      out_thdt_buyqty (str(10)): 금일매수수량
      out_thdt_sll_qty (str(10)): 금일매도수량
      out_hldg_qty (str(19)): 보유수량
      out_ord_psbl_qty (str(10)): 주문가능수량
      out_pchs_avg_pric (str(184)): 매입평균가격
      out_pchs_amt (str(19)): 매입금액
      out_prpr (str(19)): 현재가
      out_evlu_amt (str(19)): 평가금액
      out_evlu_pfls_amt (str(19)): 평가손익금액
      out_evlu_erng_rt (str(238)): 평가수익율
      out_output2 (str): 응답상세2
      out_dnca_tot_amt (str(19)): 예수금총금액
      out_nxdy_excc_amt (str(19)): 익일정산금액
      out_prvs_rcdl_excc_amt (str(19)): 가수도정산금액
      out_thdt_buy_amt (str(19)): 금일매수금액
      out_thdt_sll_amt (str(19)): 금일매도금액
      out_thdt_tlex_amt (str(19)): 금일제비용금액
      out_scts_evlu_amt (str(19)): 유가평가금액
      out_tot_evlu_amt (str(19)): 총평가금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'ACCA_DVSN_CD': in_ACCA_DVSN_CD,
      'INQR_DVSN': in_INQR_DVSN,
      'CTX_AREA_FK100': in_CTX_AREA_FK100,
      'CTX_AREA_NK100': in_CTX_AREA_NK100,
      'api-id': 'v1_국내주식-036',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/pension/inquire-balance'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output1'] = out_data['output1']
    return_data['out_cblc_dvsn_name'] = out_data['cblc_dvsn_name']
    return_data['out_prdt_name'] = out_data['prdt_name']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_item_dvsn_name'] = out_data['item_dvsn_name']
    return_data['out_thdt_buyqty'] = out_data['thdt_buyqty']
    return_data['out_thdt_sll_qty'] = out_data['thdt_sll_qty']
    return_data['out_hldg_qty'] = out_data['hldg_qty']
    return_data['out_ord_psbl_qty'] = out_data['ord_psbl_qty']
    return_data['out_pchs_avg_pric'] = out_data['pchs_avg_pric']
    return_data['out_pchs_amt'] = out_data['pchs_amt']
    return_data['out_prpr'] = out_data['prpr']
    return_data['out_evlu_amt'] = out_data['evlu_amt']
    return_data['out_evlu_pfls_amt'] = out_data['evlu_pfls_amt']
    return_data['out_evlu_erng_rt'] = out_data['evlu_erng_rt']
    return_data['out_output2'] = out_data['output2']
    return_data['out_dnca_tot_amt'] = out_data['dnca_tot_amt']
    return_data['out_nxdy_excc_amt'] = out_data['nxdy_excc_amt']
    return_data['out_prvs_rcdl_excc_amt'] = out_data['prvs_rcdl_excc_amt']
    return_data['out_thdt_buy_amt'] = out_data['thdt_buy_amt']
    return_data['out_thdt_sll_amt'] = out_data['thdt_sll_amt']
    return_data['out_thdt_tlex_amt'] = out_data['thdt_tlex_amt']
    return_data['out_scts_evlu_amt'] = out_data['scts_evlu_amt']
    return_data['out_tot_evlu_amt'] = out_data['tot_evlu_amt']
    
    return return_data

  def get_trading_inquire_balance_rlz_pl(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_AFHR_FLPR_YN: str, in_OFL_YN: str, in_INQR_DVSN: str, in_UNPR_DVSN: str, in_FUND_STTL_ICLD_YN: str, in_FNCG_AMT_AUTO_RDPT_YN: str, in_PRCS_DVSN: str, in_COST_ICLD_YN: str, in_CTX_AREA_FK100: str, in_CTX_AREA_NK100: str):
    """
    주식잔고조회_실현손익
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC8494R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 주식잔고조회_실현손익 API입니다.
      한국투자 HTS(eFriend Plus) [0800] 국내 체결기준잔고 화면을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
      (참고: 포럼 - 공지사항 - 신규 API 추가 안내(주식잔고조회_실현손익 외 1건))
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC8494R
      in_tr_cont (str(1)): 연속 거래 여부. F or M : 다음 데이터 있음 D or E : 마지막 데이터
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_AFHR_FLPR_YN (str(1)): 시간외단일가여부(필수). 'N : 기본값  Y : 시간외단일가'
      in_OFL_YN (str(1)): 오프라인여부(필수). 공란
      in_INQR_DVSN (str(2)): 조회구분(필수). 00 : 전체
      in_UNPR_DVSN (str(2)): 단가구분(필수). 01 : 기본값
      in_FUND_STTL_ICLD_YN (str(1)): 펀드결제포함여부(필수). N : 포함하지 않음  Y : 포함
      in_FNCG_AMT_AUTO_RDPT_YN (str(1)): 융자금액자동상환여부(필수). N : 기본값
      in_PRCS_DVSN (str(2)): PRCS_DVSN(필수). 00 : 전일매매포함  01 : 전일매매미포함
      in_COST_ICLD_YN (str(1)): 비용포함여부(필수)
      in_CTX_AREA_FK100 (str(100)): 연속조회검색조건100(필수). 공란 : 최초 조회시  이전 조회 Output CTX_AREA_FK100 값 : 다음페이지 조회시(2번째부터)
      in_CTX_AREA_NK100 (str(100)): 연속조회키100(필수). 공란 : 최초 조회시  이전 조회 Output CTX_AREA_NK100 값 : 다음페이지 조회시(2번째부터)
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output1 (str): 응답상세. Array
      out_pdno (str(12)): 상품번호. 종목번호(뒷 6자리)
      out_prdt_name (str(60)): 상품명. 종목명
      out_trad_dvsn_name (str(60)): 매매구분명. 매수매도구분
      out_bfdy_buy_qty (str(10)): 전일매수수량
      out_bfdy_sll_qty (str(10)): 전일매도수량
      out_thdt_buyqty (str(10)): 금일매수수량
      out_thdt_sll_qty (str(10)): 금일매도수량
      out_hldg_qty (str(19)): 보유수량
      out_ord_psbl_qty (str(10)): 주문가능수량
      out_pchs_avg_pric (str(23)): 매입평균가격. 매입금액 / 보유수량
      out_pchs_amt (str(19)): 매입금액
      out_prpr (str(19)): 현재가
      out_evlu_amt (str(19)): 평가금액
      out_evlu_pfls_amt (str(19)): 평가손익금액. 평가금액 - 매입금액
      out_evlu_pfls_rt (str(10)): 평가손익율
      out_evlu_erng_rt (str(32)): 평가수익율
      out_loan_dt (str(8)): 대출일자
      out_loan_amt (str(19)): 대출금액
      out_stln_slng_chgs (str(19)): 대주매각대금. 신용 거래에서, 고객이 증권 회사로부터 대부받은 주식의 매각 대금
      out_expd_dt (str(8)): 만기일자
      out_stck_loan_unpr (str(23)): 주식대출단가
      out_bfdy_cprs_icdc (str(19)): 전일대비증감
      out_fltt_rt (str(32)): 등락율
      out_output2 (str): 응답상세2. Array
      out_dnca_tot_amt (str(19)): 예수금총금액
      out_nxdy_excc_amt (str(19)): 익일정산금액
      out_prvs_rcdl_excc_amt (str(19)): 가수도정산금액
      out_cma_evlu_amt (str(19)): CMA평가금액
      out_bfdy_buy_amt (str(19)): 전일매수금액
      out_thdt_buy_amt (str(19)): 금일매수금액
      out_nxdy_auto_rdpt_amt (str(19)): 익일자동상환금액
      out_bfdy_sll_amt (str(19)): 전일매도금액
      out_thdt_sll_amt (str(19)): 금일매도금액
      out_d2_auto_rdpt_amt (str(19)): D+2자동상환금액
      out_bfdy_tlex_amt (str(19)): 전일제비용금액
      out_thdt_tlex_amt (str(19)): 금일제비용금액
      out_tot_loan_amt (str(19)): 총대출금액
      out_scts_evlu_amt (str(19)): 유가평가금액
      out_tot_evlu_amt (str(19)): 총평가금액
      out_nass_amt (str(19)): 순자산금액
      out_fncg_gld_auto_rdpt_yn (str(1)): 융자금자동상환여부
      out_pchs_amt_smtl_amt (str(19)): 매입금액합계금액
      out_evlu_amt_smtl_amt (str(19)): 평가금액합계금액
      out_evlu_pfls_smtl_amt (str(19)): 평가손익합계금액
      out_tot_stln_slng_chgs (str(19)): 총대주매각대금
      out_bfdy_tot_asst_evlu_amt (str(19)): 전일총자산평가금액
      out_asst_icdc_amt (str(19)): 자산증감액
      out_asst_icdc_erng_rt (str(32)): 자산증감수익율
      out_rlzt_pfls (str(19)): 실현손익
      out_rlzt_erng_rt (str(32)): 실현수익율
      out_real_evlu_pfls (str(19)): 실평가손익
      out_real_evlu_pfls_erng_rt (str(32)): 실평가손익수익율
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'AFHR_FLPR_YN': in_AFHR_FLPR_YN,
      'OFL_YN': in_OFL_YN,
      'INQR_DVSN': in_INQR_DVSN,
      'UNPR_DVSN': in_UNPR_DVSN,
      'FUND_STTL_ICLD_YN': in_FUND_STTL_ICLD_YN,
      'FNCG_AMT_AUTO_RDPT_YN': in_FNCG_AMT_AUTO_RDPT_YN,
      'PRCS_DVSN': in_PRCS_DVSN,
      'COST_ICLD_YN': in_COST_ICLD_YN,
      'CTX_AREA_FK100': in_CTX_AREA_FK100,
      'CTX_AREA_NK100': in_CTX_AREA_NK100,
      'api-id': 'v1_국내주식-041',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output1'] = out_data['output1']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_prdt_name'] = out_data['prdt_name']
    return_data['out_trad_dvsn_name'] = out_data['trad_dvsn_name']
    return_data['out_bfdy_buy_qty'] = out_data['bfdy_buy_qty']
    return_data['out_bfdy_sll_qty'] = out_data['bfdy_sll_qty']
    return_data['out_thdt_buyqty'] = out_data['thdt_buyqty']
    return_data['out_thdt_sll_qty'] = out_data['thdt_sll_qty']
    return_data['out_hldg_qty'] = out_data['hldg_qty']
    return_data['out_ord_psbl_qty'] = out_data['ord_psbl_qty']
    return_data['out_pchs_avg_pric'] = out_data['pchs_avg_pric']
    return_data['out_pchs_amt'] = out_data['pchs_amt']
    return_data['out_prpr'] = out_data['prpr']
    return_data['out_evlu_amt'] = out_data['evlu_amt']
    return_data['out_evlu_pfls_amt'] = out_data['evlu_pfls_amt']
    return_data['out_evlu_pfls_rt'] = out_data['evlu_pfls_rt']
    return_data['out_evlu_erng_rt'] = out_data['evlu_erng_rt']
    return_data['out_loan_dt'] = out_data['loan_dt']
    return_data['out_loan_amt'] = out_data['loan_amt']
    return_data['out_stln_slng_chgs'] = out_data['stln_slng_chgs']
    return_data['out_expd_dt'] = out_data['expd_dt']
    return_data['out_stck_loan_unpr'] = out_data['stck_loan_unpr']
    return_data['out_bfdy_cprs_icdc'] = out_data['bfdy_cprs_icdc']
    return_data['out_fltt_rt'] = out_data['fltt_rt']
    return_data['out_output2'] = out_data['output2']
    return_data['out_dnca_tot_amt'] = out_data['dnca_tot_amt']
    return_data['out_nxdy_excc_amt'] = out_data['nxdy_excc_amt']
    return_data['out_prvs_rcdl_excc_amt'] = out_data['prvs_rcdl_excc_amt']
    return_data['out_cma_evlu_amt'] = out_data['cma_evlu_amt']
    return_data['out_bfdy_buy_amt'] = out_data['bfdy_buy_amt']
    return_data['out_thdt_buy_amt'] = out_data['thdt_buy_amt']
    return_data['out_nxdy_auto_rdpt_amt'] = out_data['nxdy_auto_rdpt_amt']
    return_data['out_bfdy_sll_amt'] = out_data['bfdy_sll_amt']
    return_data['out_thdt_sll_amt'] = out_data['thdt_sll_amt']
    return_data['out_d2_auto_rdpt_amt'] = out_data['d2_auto_rdpt_amt']
    return_data['out_bfdy_tlex_amt'] = out_data['bfdy_tlex_amt']
    return_data['out_thdt_tlex_amt'] = out_data['thdt_tlex_amt']
    return_data['out_tot_loan_amt'] = out_data['tot_loan_amt']
    return_data['out_scts_evlu_amt'] = out_data['scts_evlu_amt']
    return_data['out_tot_evlu_amt'] = out_data['tot_evlu_amt']
    return_data['out_nass_amt'] = out_data['nass_amt']
    return_data['out_fncg_gld_auto_rdpt_yn'] = out_data['fncg_gld_auto_rdpt_yn']
    return_data['out_pchs_amt_smtl_amt'] = out_data['pchs_amt_smtl_amt']
    return_data['out_evlu_amt_smtl_amt'] = out_data['evlu_amt_smtl_amt']
    return_data['out_evlu_pfls_smtl_amt'] = out_data['evlu_pfls_smtl_amt']
    return_data['out_tot_stln_slng_chgs'] = out_data['tot_stln_slng_chgs']
    return_data['out_bfdy_tot_asst_evlu_amt'] = out_data['bfdy_tot_asst_evlu_amt']
    return_data['out_asst_icdc_amt'] = out_data['asst_icdc_amt']
    return_data['out_asst_icdc_erng_rt'] = out_data['asst_icdc_erng_rt']
    return_data['out_rlzt_pfls'] = out_data['rlzt_pfls']
    return_data['out_rlzt_erng_rt'] = out_data['rlzt_erng_rt']
    return_data['out_real_evlu_pfls'] = out_data['real_evlu_pfls']
    return_data['out_real_evlu_pfls_erng_rt'] = out_data['real_evlu_pfls_erng_rt']
    
    return return_data

  def get_trading_inquire_account_balance(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_INQR_DVSN_1: str, in_BSPR_BF_DT_APLY_YN: str):
    """
    투자계좌자산현황조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : CTRP6548R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 투자계좌자산현황조회 API입니다.
      output1은 한국투자 HTS(eFriend Plus) &gt; [0891] 계좌 자산비중(결제기준) 화면 아래 테이블의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). CTRP6548R
      in_tr_cont (str(1)): 연속 거래 여부. 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우)
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_INQR_DVSN_1 (str(1)): 조회구분1(필수). 공백입력
      in_BSPR_BF_DT_APLY_YN (str(1)): 기준가이전일자적용여부(필수). 공백입력
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. F or M : 다음 데이터 있음 D or E : 마지막 데이터
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_Output1 (str): 응답상세. Array [아래 순서대로 출력 : 20항목] 1: 주식 2: 펀드/MMW 3: IMA 4: 채권 5: ELS/DLS 6: WRAP 7: 신탁 8: RP/발행어음 9: 해외주식 10: 해외채권 11: 금현물 12: CD/CP 13: 전자단기사채 14: 타사상품 15: 외화전자단기사채 16: 외화 ELS/DLS 17: 외화 18: 예수금 19: 청약자예수금 20: 합계  [21번 계좌일 경우 : 17항목] 1: 수익증권 2: IMA 3: 채권 4: ELS/DLS 5: WRAP 6: 신탁 7: RP 8: 외화rp 9: 해외채권 10: CD/CP 11: 전자단기사채 12: 외화전자단기사채 13: 외화ELS/DLS 14: 외화평가금액 15: 예수금+cma 16: 청약자예수금 17: 합계
      out_pchs_amt (str(19)): 매입금액
      out_evlu_amt (str(19)): 평가금액
      out_evlu_pfls_amt (str(19)): 평가손익금액
      out_crdt_lnd_amt (str(19)): 신용대출금액
      out_real_nass_amt (str(19)): 실제순자산금액
      out_whol_weit_rt (str(228)): 전체비중율
      out_Output2 (str): 응답상세2
      out_pchs_amt_smtl (str(19)): 매입금액합계. 유가매입금액
      out_nass_tot_amt (str(19)): 순자산총금액
      out_loan_amt_smtl (str(19)): 대출금액합계
      out_evlu_pfls_amt_smtl (str(19)): 평가손익금액합계. 평가손익금액
      out_evlu_amt_smtl (str(19)): 평가금액합계. 유가평가금액
      out_tot_asst_amt (str(19)): 총자산금액. 총 자산금액
      out_tot_lnda_tot_ulst_lnda (str(19)): 총대출금액총융자대출금액
      out_cma_auto_loan_amt (str(19)): CMA자동대출금액
      out_tot_mgln_amt (str(19)): 총담보대출금액
      out_stln_evlu_amt (str(19)): 대주평가금액
      out_crdt_fncg_amt (str(19)): 신용융자금액
      out_ocl_apl_loan_amt (str(19)): OCL_APL대출금액
      out_pldg_stup_amt (str(19)): 질권설정금액
      out_frcr_evlu_tota (str(19)): 외화평가총액
      out_tot_dncl_amt (str(19)): 총예수금액
      out_cma_evlu_amt (str(19)): CMA평가금액
      out_dncl_amt (str(19)): 예수금액
      out_tot_sbst_amt (str(19)): 총대용금액
      out_thdt_rcvb_amt (str(20)): 당일미수금액
      out_ovrs_stck_evlu_amt1 (str(236)): 해외주식평가금액1
      out_ovrs_bond_evlu_amt (str(236)): 해외채권평가금액
      out_mmf_cma_mgge_loan_amt (str(19)): MMFCMA담보대출금액
      out_sbsc_dncl_amt (str(19)): 청약예수금액
      out_pbst_sbsc_fnds_loan_use_amt (str(20)): 공모주청약자금대출사용금액
      out_etpr_crdt_grnt_loan_amt (str(19)): 기업신용공여대출금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'INQR_DVSN_1': in_INQR_DVSN_1,
      'BSPR_BF_DT_APLY_YN': in_BSPR_BF_DT_APLY_YN,
      'api-id': 'v1_국내주식-048',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/inquire-account-balance'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_Output1'] = out_data['Output1']
    return_data['out_pchs_amt'] = out_data['pchs_amt']
    return_data['out_evlu_amt'] = out_data['evlu_amt']
    return_data['out_evlu_pfls_amt'] = out_data['evlu_pfls_amt']
    return_data['out_crdt_lnd_amt'] = out_data['crdt_lnd_amt']
    return_data['out_real_nass_amt'] = out_data['real_nass_amt']
    return_data['out_whol_weit_rt'] = out_data['whol_weit_rt']
    return_data['out_Output2'] = out_data['Output2']
    return_data['out_pchs_amt_smtl'] = out_data['pchs_amt_smtl']
    return_data['out_nass_tot_amt'] = out_data['nass_tot_amt']
    return_data['out_loan_amt_smtl'] = out_data['loan_amt_smtl']
    return_data['out_evlu_pfls_amt_smtl'] = out_data['evlu_pfls_amt_smtl']
    return_data['out_evlu_amt_smtl'] = out_data['evlu_amt_smtl']
    return_data['out_tot_asst_amt'] = out_data['tot_asst_amt']
    return_data['out_tot_lnda_tot_ulst_lnda'] = out_data['tot_lnda_tot_ulst_lnda']
    return_data['out_cma_auto_loan_amt'] = out_data['cma_auto_loan_amt']
    return_data['out_tot_mgln_amt'] = out_data['tot_mgln_amt']
    return_data['out_stln_evlu_amt'] = out_data['stln_evlu_amt']
    return_data['out_crdt_fncg_amt'] = out_data['crdt_fncg_amt']
    return_data['out_ocl_apl_loan_amt'] = out_data['ocl_apl_loan_amt']
    return_data['out_pldg_stup_amt'] = out_data['pldg_stup_amt']
    return_data['out_frcr_evlu_tota'] = out_data['frcr_evlu_tota']
    return_data['out_tot_dncl_amt'] = out_data['tot_dncl_amt']
    return_data['out_cma_evlu_amt'] = out_data['cma_evlu_amt']
    return_data['out_dncl_amt'] = out_data['dncl_amt']
    return_data['out_tot_sbst_amt'] = out_data['tot_sbst_amt']
    return_data['out_thdt_rcvb_amt'] = out_data['thdt_rcvb_amt']
    return_data['out_ovrs_stck_evlu_amt1'] = out_data['ovrs_stck_evlu_amt1']
    return_data['out_ovrs_bond_evlu_amt'] = out_data['ovrs_bond_evlu_amt']
    return_data['out_mmf_cma_mgge_loan_amt'] = out_data['mmf_cma_mgge_loan_amt']
    return_data['out_sbsc_dncl_amt'] = out_data['sbsc_dncl_amt']
    return_data['out_pbst_sbsc_fnds_loan_use_amt'] = out_data['pbst_sbsc_fnds_loan_use_amt']
    return_data['out_etpr_crdt_grnt_loan_amt'] = out_data['etpr_crdt_grnt_loan_amt']
    
    return return_data

  def get_trading_inquire_period_profit(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_ACNT_PRDT_CD: str, in_CANO: str, in_INQR_STRT_DT: str, in_PDNO: str, in_CTX_AREA_NK100: str, in_INQR_END_DT: str, in_SORT_DVSN: str, in_INQR_DVSN: str, in_CBLC_DVSN: str, in_CTX_AREA_FK100: str):
    """
    기간별손익일별합산조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC8708R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 기간별손익일별합산조회 API입니다.
      한국투자 HTS(eFriend Plus) &gt; [0856] 기간별 매매손익 화면 에서 "일별" 클릭 시의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC8708R
      in_tr_cont (str(1)): 연속 거래 여부. 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우)
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수)
      in_CANO (str(8)): 종합계좌번호(필수)
      in_INQR_STRT_DT (str(8)): 조회시작일자(필수)
      in_PDNO (str(12)): 상품번호(필수). ""공란입력 시, 전체
      in_CTX_AREA_NK100 (str(100)): 연속조회키100(필수)
      in_INQR_END_DT (str(8)): 조회종료일자(필수)
      in_SORT_DVSN (str(2)): 정렬구분(필수). 00: 최근 순, 01: 과거 순, 02: 최근 순
      in_INQR_DVSN (str(2)): 조회구분(필수). 00 입력
      in_CBLC_DVSN (str(2)): 잔고구분(필수). 00: 전체
      in_CTX_AREA_FK100 (str(100)): 연속조회검색조건100(필수)
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. F or M : 다음 데이터 있음 D or E : 마지막 데이터
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output1 (str): 응답상세. array
      out_trad_dt (str(8)): 매매일자
      out_buy_amt (str(19)): 매수금액
      out_sll_amt (str(19)): 매도금액
      out_rlzt_pfls (str(19)): 실현손익
      out_fee (str(19)): 수수료
      out_loan_int (str(19)): 대출이자
      out_tl_tax (str(19)): 제세금
      out_pfls_rt (str(238)): 손익률
      out_sll_qty1 (str(19)): 매도수량1
      out_buy_qty1 (str(9)): 매수수량1
      out_output2 (str): 응답상세2
      out_sll_qty_smtl (str(19)): 매도수량합계
      out_sll_tr_amt_smtl (str(19)): 매도거래금액합계
      out_sll_fee_smtl (str(19)): 매도수수료합계
      out_sll_tltx_smtl (str(19)): 매도제세금합계
      out_sll_excc_amt_smtl (str(19)): 매도정산금액합계
      out_buy_qty_smtl (str(19)): 매수수량합계
      out_buy_tr_amt_smtl (str(19)): 매수거래금액합계
      out_buy_fee_smtl (str(19)): 매수수수료합계
      out_buy_tax_smtl (str(19)): 매수제세금합계
      out_buy_excc_amt_smtl (str(19)): 매수정산금액합계
      out_tot_qty (str(10)): 총수량
      out_tot_tr_amt (str(19)): 총거래금액
      out_tot_fee (str(19)): 총수수료
      out_tot_tltx (str(19)): 총제세금
      out_tot_excc_amt (str(19)): 총정산금액
      out_tot_rlzt_pfls (str(19)): 총실현손익. ※ HTS[0856] 기간별 매매손익 '일별' 화면의 우측 하단 '총손익률' 항목은  기간별매매손익현황조회(TTTC8715R) > output2 > tot_pftrt(총수익률) 으로 확인 가능
      out_loan_int (str(19)): 대출이자
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'CANO': in_CANO,
      'INQR_STRT_DT': in_INQR_STRT_DT,
      'PDNO': in_PDNO,
      'CTX_AREA_NK100': in_CTX_AREA_NK100,
      'INQR_END_DT': in_INQR_END_DT,
      'SORT_DVSN': in_SORT_DVSN,
      'INQR_DVSN': in_INQR_DVSN,
      'CBLC_DVSN': in_CBLC_DVSN,
      'CTX_AREA_FK100': in_CTX_AREA_FK100,
      'api-id': 'v1_국내주식-052',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/inquire-period-profit'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output1'] = out_data['output1']
    return_data['out_trad_dt'] = out_data['trad_dt']
    return_data['out_buy_amt'] = out_data['buy_amt']
    return_data['out_sll_amt'] = out_data['sll_amt']
    return_data['out_rlzt_pfls'] = out_data['rlzt_pfls']
    return_data['out_fee'] = out_data['fee']
    return_data['out_loan_int'] = out_data['loan_int']
    return_data['out_tl_tax'] = out_data['tl_tax']
    return_data['out_pfls_rt'] = out_data['pfls_rt']
    return_data['out_sll_qty1'] = out_data['sll_qty1']
    return_data['out_buy_qty1'] = out_data['buy_qty1']
    return_data['out_output2'] = out_data['output2']
    return_data['out_sll_qty_smtl'] = out_data['sll_qty_smtl']
    return_data['out_sll_tr_amt_smtl'] = out_data['sll_tr_amt_smtl']
    return_data['out_sll_fee_smtl'] = out_data['sll_fee_smtl']
    return_data['out_sll_tltx_smtl'] = out_data['sll_tltx_smtl']
    return_data['out_sll_excc_amt_smtl'] = out_data['sll_excc_amt_smtl']
    return_data['out_buy_qty_smtl'] = out_data['buy_qty_smtl']
    return_data['out_buy_tr_amt_smtl'] = out_data['buy_tr_amt_smtl']
    return_data['out_buy_fee_smtl'] = out_data['buy_fee_smtl']
    return_data['out_buy_tax_smtl'] = out_data['buy_tax_smtl']
    return_data['out_buy_excc_amt_smtl'] = out_data['buy_excc_amt_smtl']
    return_data['out_tot_qty'] = out_data['tot_qty']
    return_data['out_tot_tr_amt'] = out_data['tot_tr_amt']
    return_data['out_tot_fee'] = out_data['tot_fee']
    return_data['out_tot_tltx'] = out_data['tot_tltx']
    return_data['out_tot_excc_amt'] = out_data['tot_excc_amt']
    return_data['out_tot_rlzt_pfls'] = out_data['tot_rlzt_pfls']
    return_data['out_loan_int'] = out_data['loan_int']
    
    return return_data

  def get_trading_inquire_period_trade_profit(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_SORT_DVSN: str, in_ACNT_PRDT_CD: str, in_PDNO: str, in_INQR_STRT_DT: str, in_INQR_END_DT: str, in_CTX_AREA_NK100: str, in_CBLC_DVSN: str, in_CTX_AREA_FK100: str):
    """
    기간별매매손익현황조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC8715R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 기간별매매손익현황조회 API입니다.
      한국투자 HTS(eFriend Plus) &gt; [0856] 기간별 매매손익 화면 에서 "종목별" 클릭 시의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC8715R
      in_tr_cont (str(1)): 연속 거래 여부. 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우)
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수)
      in_SORT_DVSN (str(2)): 정렬구분(필수). 00: 최근 순, 01: 과거 순, 02: 최근 순
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수)
      in_PDNO (str(12)): 상품번호(필수). ""공란입력 시, 전체
      in_INQR_STRT_DT (str(8)): 조회시작일자(필수)
      in_INQR_END_DT (str(8)): 조회종료일자(필수)
      in_CTX_AREA_NK100 (str(100)): 연속조회키100(필수)
      in_CBLC_DVSN (str(2)): 잔고구분(필수). 00: 전체
      in_CTX_AREA_FK100 (str(100)): 연속조회검색조건100(필수)
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. F or M : 다음 데이터 있음 D or E : 마지막 데이터
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_ctx_area_nk100 (str(100)): 연속조회키100
      out_ctx_area_fk100 (str(100)): 연속조회검색조건100
      out_output1 (str): 응답상세. array
      out_trad_dt (str(8)): 매매일자
      out_pdno (str(12)): 상품번호. 종목번호(뒤 6자리만 해당)
      out_prdt_name (str(60)): 상품명
      out_trad_dvsn_name (str(60)): 매매구분명
      out_loan_dt (str(8)): 대출일자
      out_hldg_qty (str(19)): 보유수량
      out_pchs_unpr (str(19)): 매입단가
      out_buy_qty (str(10)): 매수수량
      out_buy_amt (str(19)): 매수금액
      out_sll_pric (str(10)): 매도가격
      out_sll_qty (str(10)): 매도수량
      out_sll_amt (str(19)): 매도금액
      out_rlzt_pfls (str(19)): 실현손익
      out_pfls_rt (str(238)): 손익률
      out_fee (str(19)): 수수료
      out_tl_tax (str(19)): 제세금
      out_loan_int (str(19)): 대출이자
      out_output2 (str): 응답상세2
      out_sll_qty_smtl (str(19)): 매도수량합계
      out_sll_tr_amt_smtl (str(19)): 매도거래금액합계
      out_sll_fee_smtl (str(19)): 매도수수료합계
      out_sll_tltx_smtl (str(19)): 매도제세금합계
      out_sll_excc_amt_smtl (str(19)): 매도정산금액합계
      out_buyqty_smtl (str(8)): 매수수량합계
      out_buy_tr_amt_smtl (str(19)): 매수거래금액합계
      out_buy_fee_smtl (str(19)): 매수수수료합계
      out_buy_tax_smtl (str(19)): 매수제세금합계
      out_buy_excc_amt_smtl (str(19)): 매수정산금액합계
      out_tot_qty (str(10)): 총수량
      out_tot_tr_amt (str(19)): 총거래금액
      out_tot_fee (str(19)): 총수수료
      out_tot_tltx (str(19)): 총제세금
      out_tot_excc_amt (str(19)): 총정산금액
      out_tot_rlzt_pfls (str(19)): 총실현손익
      out_loan_int (str(19)): 대출이자
      out_tot_pftrt (str(238)): 총수익률
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'SORT_DVSN': in_SORT_DVSN,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'PDNO': in_PDNO,
      'INQR_STRT_DT': in_INQR_STRT_DT,
      'INQR_END_DT': in_INQR_END_DT,
      'CTX_AREA_NK100': in_CTX_AREA_NK100,
      'CBLC_DVSN': in_CBLC_DVSN,
      'CTX_AREA_FK100': in_CTX_AREA_FK100,
      'api-id': 'v1_국내주식-060',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/inquire-period-trade-profit'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_ctx_area_nk100'] = out_data['ctx_area_nk100']
    return_data['out_ctx_area_fk100'] = out_data['ctx_area_fk100']
    return_data['out_output1'] = out_data['output1']
    return_data['out_trad_dt'] = out_data['trad_dt']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_prdt_name'] = out_data['prdt_name']
    return_data['out_trad_dvsn_name'] = out_data['trad_dvsn_name']
    return_data['out_loan_dt'] = out_data['loan_dt']
    return_data['out_hldg_qty'] = out_data['hldg_qty']
    return_data['out_pchs_unpr'] = out_data['pchs_unpr']
    return_data['out_buy_qty'] = out_data['buy_qty']
    return_data['out_buy_amt'] = out_data['buy_amt']
    return_data['out_sll_pric'] = out_data['sll_pric']
    return_data['out_sll_qty'] = out_data['sll_qty']
    return_data['out_sll_amt'] = out_data['sll_amt']
    return_data['out_rlzt_pfls'] = out_data['rlzt_pfls']
    return_data['out_pfls_rt'] = out_data['pfls_rt']
    return_data['out_fee'] = out_data['fee']
    return_data['out_tl_tax'] = out_data['tl_tax']
    return_data['out_loan_int'] = out_data['loan_int']
    return_data['out_output2'] = out_data['output2']
    return_data['out_sll_qty_smtl'] = out_data['sll_qty_smtl']
    return_data['out_sll_tr_amt_smtl'] = out_data['sll_tr_amt_smtl']
    return_data['out_sll_fee_smtl'] = out_data['sll_fee_smtl']
    return_data['out_sll_tltx_smtl'] = out_data['sll_tltx_smtl']
    return_data['out_sll_excc_amt_smtl'] = out_data['sll_excc_amt_smtl']
    return_data['out_buyqty_smtl'] = out_data['buyqty_smtl']
    return_data['out_buy_tr_amt_smtl'] = out_data['buy_tr_amt_smtl']
    return_data['out_buy_fee_smtl'] = out_data['buy_fee_smtl']
    return_data['out_buy_tax_smtl'] = out_data['buy_tax_smtl']
    return_data['out_buy_excc_amt_smtl'] = out_data['buy_excc_amt_smtl']
    return_data['out_tot_qty'] = out_data['tot_qty']
    return_data['out_tot_tr_amt'] = out_data['tot_tr_amt']
    return_data['out_tot_fee'] = out_data['tot_fee']
    return_data['out_tot_tltx'] = out_data['tot_tltx']
    return_data['out_tot_excc_amt'] = out_data['tot_excc_amt']
    return_data['out_tot_rlzt_pfls'] = out_data['tot_rlzt_pfls']
    return_data['out_loan_int'] = out_data['loan_int']
    return_data['out_tot_pftrt'] = out_data['tot_pftrt']
    
    return return_data

  def get_trading_intgr_margin(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_CMA_EVLU_AMT_ICLD_YN: str, in_WCRC_FRCR_DVSN_CD: str, in_FWEX_CTRT_FRCR_DVSN_CD: str):
    """
    주식통합증거금 현황
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : TTTC0869R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 주식통합증거금 현황 API입니다.
      한국투자 HTS(eFriend Plus) &gt; [0867] 통합증거금조회 화면 의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
      ※ 해당 화면은 일반계좌와 통합증거금 신청계좌에 대해서 국내 및 해외 주문가능금액을 간단하게 조회하는 화면입니다.
      ※ 해외 국가별 상세한 증거금현황을 원하시면 [해외주식] 주문/계좌 &gt; 해외증거금 통화별조회 API를 이용하여 주시기 바랍니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). TTTC0869R
      in_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 체계(8-2)의 앞 8자리
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 계좌번호 체계(8-2)의 뒤 2자리
      in_CMA_EVLU_AMT_ICLD_YN (str(1)): CMA평가금액포함여부(필수). N 입력
      in_WCRC_FRCR_DVSN_CD (str(2)): 원화외화구분코드(필수). 01(외화기준),02(원화기준)
      in_FWEX_CTRT_FRCR_DVSN_CD (str(2)): 선도환계약외화구분코드(필수). 01(외화기준),02(원화기준)
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. tr_cont를 이용한 다음조회 불가 API
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output (str): 응답상세
      out_acmga_rt (str(114)): 계좌증거금율
      out_acmga_pct100_aptm_rson (str(100)): 계좌증거금100퍼센트지정사유
      out_stck_cash_objt_amt (str(184)): 주식현금대상금액
      out_stck_sbst_objt_amt (str(184)): 주식대용대상금액
      out_stck_evlu_objt_amt (str(184)): 주식평가대상금액
      out_stck_ruse_psbl_objt_amt (str(184)): 주식재사용가능대상금액
      out_stck_fund_rpch_chgs_objt_amt (str(184)): 주식펀드환매대금대상금액
      out_stck_fncg_rdpt_objt_atm (str(184)): 주식융자상환금대상금액
      out_bond_ruse_psbl_objt_amt (str(184)): 채권재사용가능대상금액
      out_stck_cash_use_amt (str(184)): 주식현금사용금액
      out_stck_sbst_use_amt (str(184)): 주식대용사용금액
      out_stck_evlu_use_amt (str(184)): 주식평가사용금액
      out_stck_ruse_psbl_amt_use_amt (str(184)): 주식재사용가능금사용금액
      out_stck_fund_rpch_chgs_use_amt (str(184)): 주식펀드환매대금사용금액
      out_stck_fncg_rdpt_amt_use_amt (str(184)): 주식융자상환금사용금액
      out_bond_ruse_psbl_amt_use_amt (str(184)): 채권재사용가능금사용금액
      out_stck_cash_ord_psbl_amt (str(184)): 주식현금주문가능금액
      out_stck_sbst_ord_psbl_amt (str(184)): 주식대용주문가능금액
      out_stck_evlu_ord_psbl_amt (str(184)): 주식평가주문가능금액
      out_stck_ruse_psbl_ord_psbl_amt (str(184)): 주식재사용가능주문가능금액
      out_stck_fund_rpch_ord_psbl_amt (str(184)): 주식펀드환매주문가능금액
      out_bond_ruse_psbl_ord_psbl_amt (str(184)): 채권재사용가능주문가능금액
      out_rcvb_amt (str(19)): 미수금액
      out_stck_loan_grta_ruse_psbl_amt (str(184)): 주식대출보증금재사용가능금액
      out_stck_cash20_max_ord_psbl_amt (str(184)): 주식현금20최대주문가능금액
      out_stck_cash30_max_ord_psbl_amt (str(184)): 주식현금30최대주문가능금액
      out_stck_cash40_max_ord_psbl_amt (str(184)): 주식현금40최대주문가능금액
      out_stck_cash50_max_ord_psbl_amt (str(184)): 주식현금50최대주문가능금액
      out_stck_cash60_max_ord_psbl_amt (str(184)): 주식현금60최대주문가능금액
      out_stck_cash100_max_ord_psbl_amt (str(184)): 주식현금100최대주문가능금액
      out_stck_rsip100_max_ord_psbl_amt (str(184)): 주식재사용불가100최대주문가능
      out_bond_max_ord_psbl_amt (str(184)): 채권최대주문가능금액
      out_stck_fncg45_max_ord_psbl_amt (str(182)): 주식융자45최대주문가능금액
      out_stck_fncg50_max_ord_psbl_amt (str(184)): 주식융자50최대주문가능금액
      out_stck_fncg60_max_ord_psbl_amt (str(184)): 주식융자60최대주문가능금액
      out_stck_fncg70_max_ord_psbl_amt (str(182)): 주식융자70최대주문가능금액
      out_stck_stln_max_ord_psbl_amt (str(184)): 주식대주최대주문가능금액
      out_lmt_amt (str(19)): 한도금액
      out_ovrs_stck_itgr_mgna_dvsn_name (str(40)): 해외주식통합증거금구분명
      out_usd_objt_amt (str(182)): 미화대상금액
      out_usd_use_amt (str(182)): 미화사용금액
      out_usd_ord_psbl_amt (str(182)): 미화주문가능금액
      out_hkd_objt_amt (str(182)): 홍콩달러대상금액
      out_hkd_use_amt (str(182)): 홍콩달러사용금액
      out_hkd_ord_psbl_amt (str(182)): 홍콩달러주문가능금액
      out_jpy_objt_amt (str(182)): 엔화대상금액
      out_jpy_use_amt (str(182)): 엔화사용금액
      out_jpy_ord_psbl_amt (str(182)): 엔화주문가능금액
      out_cny_objt_amt (str(182)): 위안화대상금액
      out_cny_use_amt (str(182)): 위안화사용금액
      out_cny_ord_psbl_amt (str(182)): 위안화주문가능금액
      out_usd_ruse_objt_amt (str(182)): 미화재사용대상금액
      out_usd_ruse_amt (str(182)): 미화재사용금액
      out_usd_ruse_ord_psbl_amt (str(182)): 미화재사용주문가능금액
      out_hkd_ruse_objt_amt (str(182)): 홍콩달러재사용대상금액
      out_hkd_ruse_amt (str(182)): 홍콩달러재사용금액
      out_hkd_ruse_ord_psbl_amt (str(172)): 홍콩달러재사용주문가능금액
      out_jpy_ruse_objt_amt (str(182)): 엔화재사용대상금액
      out_jpy_ruse_amt (str(182)): 엔화재사용금액
      out_jpy_ruse_ord_psbl_amt (str(182)): 엔화재사용주문가능금액
      out_cny_ruse_objt_amt (str(182)): 위안화재사용대상금액
      out_cny_ruse_amt (str(182)): 위안화재사용금액
      out_cny_ruse_ord_psbl_amt (str(182)): 위안화재사용주문가능금액
      out_usd_gnrl_ord_psbl_amt (str(182)): 미화일반주문가능금액
      out_usd_itgr_ord_psbl_amt (str(182)): 미화통합주문가능금액
      out_hkd_gnrl_ord_psbl_amt (str(182)): 홍콩달러일반주문가능금액
      out_hkd_itgr_ord_psbl_amt (str(182)): 홍콩달러통합주문가능금액
      out_jpy_gnrl_ord_psbl_amt (str(182)): 엔화일반주문가능금액
      out_jpy_itgr_ord_psbl_amt (str(182)): 엔화통합주문가능금액
      out_cny_gnrl_ord_psbl_amt (str(182)): 위안화일반주문가능금액
      out_cny_itgr_ord_psbl_amt (str(182)): 위안화통합주문가능금액
      out_stck_itgr_cash20_ord_psbl_amt (str(182)): 주식통합현금20주문가능금액
      out_stck_itgr_cash30_ord_psbl_amt (str(182)): 주식통합현금30주문가능금액
      out_stck_itgr_cash40_ord_psbl_amt (str(182)): 주식통합현금40주문가능금액
      out_stck_itgr_cash50_ord_psbl_amt (str(182)): 주식통합현금50주문가능금액
      out_stck_itgr_cash60_ord_psbl_amt (str(182)): 주식통합현금60주문가능금액
      out_stck_itgr_cash100_ord_psbl_amt (str(182)): 주식통합현금100주문가능금액
      out_stck_itgr_100_ord_psbl_amt (str(182)): 주식통합100주문가능금액
      out_stck_itgr_fncg45_ord_psbl_amt (str(182)): 주식통합융자45주문가능금액
      out_stck_itgr_fncg50_ord_psbl_amt (str(182)): 주식통합융자50주문가능금액
      out_stck_itgr_fncg60_ord_psbl_amt (str(182)): 주식통합융자60주문가능금액
      out_stck_itgr_fncg70_ord_psbl_amt (str(182)): 주식통합융자70주문가능금액
      out_stck_itgr_stln_ord_psbl_amt (str(182)): 주식통합대주주문가능금액
      out_bond_itgr_ord_psbl_amt (str(182)): 채권통합주문가능금액
      out_stck_cash_ovrs_use_amt (str(182)): 주식현금해외사용금액
      out_stck_sbst_ovrs_use_amt (str(182)): 주식대용해외사용금액
      out_stck_evlu_ovrs_use_amt (str(182)): 주식평가해외사용금액
      out_stck_re_use_amt_ovrs_use_amt (str(182)): 주식재사용금액해외사용금액
      out_stck_fund_rpch_ovrs_use_amt (str(182)): 주식펀드환매해외사용금액
      out_stck_fncg_rdpt_ovrs_use_amt (str(182)): 주식융자상환해외사용금액
      out_bond_re_use_ovrs_use_amt (str(182)): 채권재사용해외사용금액
      out_usd_oth_mket_use_amt (str(182)): 미화타시장사용금액
      out_jpy_oth_mket_use_amt (str(182)): 엔화타시장사용금액
      out_cny_oth_mket_use_amt (str(182)): 위안화타시장사용금액
      out_hkd_oth_mket_use_amt (str(182)): 홍콩달러타시장사용금액
      out_usd_re_use_oth_mket_use_amt (str(182)): 미화재사용타시장사용금액
      out_jpy_re_use_oth_mket_use_amt (str(182)): 엔화재사용타시장사용금액
      out_cny_re_use_oth_mket_use_amt (str(182)): 위안화재사용타시장사용금액
      out_hkd_re_use_oth_mket_use_amt (str(182)): 홍콩달러재사용타시장사용금액
      out_hgkg_cny_re_use_amt (str(182)): 홍콩위안화재사용금액
      out_usd_frst_bltn_exrt (str(23)): 미국달러최초고시환율
      out_hkd_frst_bltn_exrt (str(23)): 홍콩달러최초고시환율
      out_jpy_frst_bltn_exrt (str(23)): 일본엔화최초고시환율
      out_cny_frst_bltn_exrt (str(23)): 중국위안화최초고시환율
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'CMA_EVLU_AMT_ICLD_YN': in_CMA_EVLU_AMT_ICLD_YN,
      'WCRC_FRCR_DVSN_CD': in_WCRC_FRCR_DVSN_CD,
      'FWEX_CTRT_FRCR_DVSN_CD': in_FWEX_CTRT_FRCR_DVSN_CD,
      'api-id': '국내주식-191',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/intgr-margin'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output'] = out_data['output']
    return_data['out_acmga_rt'] = out_data['acmga_rt']
    return_data['out_acmga_pct100_aptm_rson'] = out_data['acmga_pct100_aptm_rson']
    return_data['out_stck_cash_objt_amt'] = out_data['stck_cash_objt_amt']
    return_data['out_stck_sbst_objt_amt'] = out_data['stck_sbst_objt_amt']
    return_data['out_stck_evlu_objt_amt'] = out_data['stck_evlu_objt_amt']
    return_data['out_stck_ruse_psbl_objt_amt'] = out_data['stck_ruse_psbl_objt_amt']
    return_data['out_stck_fund_rpch_chgs_objt_amt'] = out_data['stck_fund_rpch_chgs_objt_amt']
    return_data['out_stck_fncg_rdpt_objt_atm'] = out_data['stck_fncg_rdpt_objt_atm']
    return_data['out_bond_ruse_psbl_objt_amt'] = out_data['bond_ruse_psbl_objt_amt']
    return_data['out_stck_cash_use_amt'] = out_data['stck_cash_use_amt']
    return_data['out_stck_sbst_use_amt'] = out_data['stck_sbst_use_amt']
    return_data['out_stck_evlu_use_amt'] = out_data['stck_evlu_use_amt']
    return_data['out_stck_ruse_psbl_amt_use_amt'] = out_data['stck_ruse_psbl_amt_use_amt']
    return_data['out_stck_fund_rpch_chgs_use_amt'] = out_data['stck_fund_rpch_chgs_use_amt']
    return_data['out_stck_fncg_rdpt_amt_use_amt'] = out_data['stck_fncg_rdpt_amt_use_amt']
    return_data['out_bond_ruse_psbl_amt_use_amt'] = out_data['bond_ruse_psbl_amt_use_amt']
    return_data['out_stck_cash_ord_psbl_amt'] = out_data['stck_cash_ord_psbl_amt']
    return_data['out_stck_sbst_ord_psbl_amt'] = out_data['stck_sbst_ord_psbl_amt']
    return_data['out_stck_evlu_ord_psbl_amt'] = out_data['stck_evlu_ord_psbl_amt']
    return_data['out_stck_ruse_psbl_ord_psbl_amt'] = out_data['stck_ruse_psbl_ord_psbl_amt']
    return_data['out_stck_fund_rpch_ord_psbl_amt'] = out_data['stck_fund_rpch_ord_psbl_amt']
    return_data['out_bond_ruse_psbl_ord_psbl_amt'] = out_data['bond_ruse_psbl_ord_psbl_amt']
    return_data['out_rcvb_amt'] = out_data['rcvb_amt']
    return_data['out_stck_loan_grta_ruse_psbl_amt'] = out_data['stck_loan_grta_ruse_psbl_amt']
    return_data['out_stck_cash20_max_ord_psbl_amt'] = out_data['stck_cash20_max_ord_psbl_amt']
    return_data['out_stck_cash30_max_ord_psbl_amt'] = out_data['stck_cash30_max_ord_psbl_amt']
    return_data['out_stck_cash40_max_ord_psbl_amt'] = out_data['stck_cash40_max_ord_psbl_amt']
    return_data['out_stck_cash50_max_ord_psbl_amt'] = out_data['stck_cash50_max_ord_psbl_amt']
    return_data['out_stck_cash60_max_ord_psbl_amt'] = out_data['stck_cash60_max_ord_psbl_amt']
    return_data['out_stck_cash100_max_ord_psbl_amt'] = out_data['stck_cash100_max_ord_psbl_amt']
    return_data['out_stck_rsip100_max_ord_psbl_amt'] = out_data['stck_rsip100_max_ord_psbl_amt']
    return_data['out_bond_max_ord_psbl_amt'] = out_data['bond_max_ord_psbl_amt']
    return_data['out_stck_fncg45_max_ord_psbl_amt'] = out_data['stck_fncg45_max_ord_psbl_amt']
    return_data['out_stck_fncg50_max_ord_psbl_amt'] = out_data['stck_fncg50_max_ord_psbl_amt']
    return_data['out_stck_fncg60_max_ord_psbl_amt'] = out_data['stck_fncg60_max_ord_psbl_amt']
    return_data['out_stck_fncg70_max_ord_psbl_amt'] = out_data['stck_fncg70_max_ord_psbl_amt']
    return_data['out_stck_stln_max_ord_psbl_amt'] = out_data['stck_stln_max_ord_psbl_amt']
    return_data['out_lmt_amt'] = out_data['lmt_amt']
    return_data['out_ovrs_stck_itgr_mgna_dvsn_name'] = out_data['ovrs_stck_itgr_mgna_dvsn_name']
    return_data['out_usd_objt_amt'] = out_data['usd_objt_amt']
    return_data['out_usd_use_amt'] = out_data['usd_use_amt']
    return_data['out_usd_ord_psbl_amt'] = out_data['usd_ord_psbl_amt']
    return_data['out_hkd_objt_amt'] = out_data['hkd_objt_amt']
    return_data['out_hkd_use_amt'] = out_data['hkd_use_amt']
    return_data['out_hkd_ord_psbl_amt'] = out_data['hkd_ord_psbl_amt']
    return_data['out_jpy_objt_amt'] = out_data['jpy_objt_amt']
    return_data['out_jpy_use_amt'] = out_data['jpy_use_amt']
    return_data['out_jpy_ord_psbl_amt'] = out_data['jpy_ord_psbl_amt']
    return_data['out_cny_objt_amt'] = out_data['cny_objt_amt']
    return_data['out_cny_use_amt'] = out_data['cny_use_amt']
    return_data['out_cny_ord_psbl_amt'] = out_data['cny_ord_psbl_amt']
    return_data['out_usd_ruse_objt_amt'] = out_data['usd_ruse_objt_amt']
    return_data['out_usd_ruse_amt'] = out_data['usd_ruse_amt']
    return_data['out_usd_ruse_ord_psbl_amt'] = out_data['usd_ruse_ord_psbl_amt']
    return_data['out_hkd_ruse_objt_amt'] = out_data['hkd_ruse_objt_amt']
    return_data['out_hkd_ruse_amt'] = out_data['hkd_ruse_amt']
    return_data['out_hkd_ruse_ord_psbl_amt'] = out_data['hkd_ruse_ord_psbl_amt']
    return_data['out_jpy_ruse_objt_amt'] = out_data['jpy_ruse_objt_amt']
    return_data['out_jpy_ruse_amt'] = out_data['jpy_ruse_amt']
    return_data['out_jpy_ruse_ord_psbl_amt'] = out_data['jpy_ruse_ord_psbl_amt']
    return_data['out_cny_ruse_objt_amt'] = out_data['cny_ruse_objt_amt']
    return_data['out_cny_ruse_amt'] = out_data['cny_ruse_amt']
    return_data['out_cny_ruse_ord_psbl_amt'] = out_data['cny_ruse_ord_psbl_amt']
    return_data['out_usd_gnrl_ord_psbl_amt'] = out_data['usd_gnrl_ord_psbl_amt']
    return_data['out_usd_itgr_ord_psbl_amt'] = out_data['usd_itgr_ord_psbl_amt']
    return_data['out_hkd_gnrl_ord_psbl_amt'] = out_data['hkd_gnrl_ord_psbl_amt']
    return_data['out_hkd_itgr_ord_psbl_amt'] = out_data['hkd_itgr_ord_psbl_amt']
    return_data['out_jpy_gnrl_ord_psbl_amt'] = out_data['jpy_gnrl_ord_psbl_amt']
    return_data['out_jpy_itgr_ord_psbl_amt'] = out_data['jpy_itgr_ord_psbl_amt']
    return_data['out_cny_gnrl_ord_psbl_amt'] = out_data['cny_gnrl_ord_psbl_amt']
    return_data['out_cny_itgr_ord_psbl_amt'] = out_data['cny_itgr_ord_psbl_amt']
    return_data['out_stck_itgr_cash20_ord_psbl_amt'] = out_data['stck_itgr_cash20_ord_psbl_amt']
    return_data['out_stck_itgr_cash30_ord_psbl_amt'] = out_data['stck_itgr_cash30_ord_psbl_amt']
    return_data['out_stck_itgr_cash40_ord_psbl_amt'] = out_data['stck_itgr_cash40_ord_psbl_amt']
    return_data['out_stck_itgr_cash50_ord_psbl_amt'] = out_data['stck_itgr_cash50_ord_psbl_amt']
    return_data['out_stck_itgr_cash60_ord_psbl_amt'] = out_data['stck_itgr_cash60_ord_psbl_amt']
    return_data['out_stck_itgr_cash100_ord_psbl_amt'] = out_data['stck_itgr_cash100_ord_psbl_amt']
    return_data['out_stck_itgr_100_ord_psbl_amt'] = out_data['stck_itgr_100_ord_psbl_amt']
    return_data['out_stck_itgr_fncg45_ord_psbl_amt'] = out_data['stck_itgr_fncg45_ord_psbl_amt']
    return_data['out_stck_itgr_fncg50_ord_psbl_amt'] = out_data['stck_itgr_fncg50_ord_psbl_amt']
    return_data['out_stck_itgr_fncg60_ord_psbl_amt'] = out_data['stck_itgr_fncg60_ord_psbl_amt']
    return_data['out_stck_itgr_fncg70_ord_psbl_amt'] = out_data['stck_itgr_fncg70_ord_psbl_amt']
    return_data['out_stck_itgr_stln_ord_psbl_amt'] = out_data['stck_itgr_stln_ord_psbl_amt']
    return_data['out_bond_itgr_ord_psbl_amt'] = out_data['bond_itgr_ord_psbl_amt']
    return_data['out_stck_cash_ovrs_use_amt'] = out_data['stck_cash_ovrs_use_amt']
    return_data['out_stck_sbst_ovrs_use_amt'] = out_data['stck_sbst_ovrs_use_amt']
    return_data['out_stck_evlu_ovrs_use_amt'] = out_data['stck_evlu_ovrs_use_amt']
    return_data['out_stck_re_use_amt_ovrs_use_amt'] = out_data['stck_re_use_amt_ovrs_use_amt']
    return_data['out_stck_fund_rpch_ovrs_use_amt'] = out_data['stck_fund_rpch_ovrs_use_amt']
    return_data['out_stck_fncg_rdpt_ovrs_use_amt'] = out_data['stck_fncg_rdpt_ovrs_use_amt']
    return_data['out_bond_re_use_ovrs_use_amt'] = out_data['bond_re_use_ovrs_use_amt']
    return_data['out_usd_oth_mket_use_amt'] = out_data['usd_oth_mket_use_amt']
    return_data['out_jpy_oth_mket_use_amt'] = out_data['jpy_oth_mket_use_amt']
    return_data['out_cny_oth_mket_use_amt'] = out_data['cny_oth_mket_use_amt']
    return_data['out_hkd_oth_mket_use_amt'] = out_data['hkd_oth_mket_use_amt']
    return_data['out_usd_re_use_oth_mket_use_amt'] = out_data['usd_re_use_oth_mket_use_amt']
    return_data['out_jpy_re_use_oth_mket_use_amt'] = out_data['jpy_re_use_oth_mket_use_amt']
    return_data['out_cny_re_use_oth_mket_use_amt'] = out_data['cny_re_use_oth_mket_use_amt']
    return_data['out_hkd_re_use_oth_mket_use_amt'] = out_data['hkd_re_use_oth_mket_use_amt']
    return_data['out_hgkg_cny_re_use_amt'] = out_data['hgkg_cny_re_use_amt']
    return_data['out_usd_frst_bltn_exrt'] = out_data['usd_frst_bltn_exrt']
    return_data['out_hkd_frst_bltn_exrt'] = out_data['hkd_frst_bltn_exrt']
    return_data['out_jpy_frst_bltn_exrt'] = out_data['jpy_frst_bltn_exrt']
    return_data['out_cny_frst_bltn_exrt'] = out_data['cny_frst_bltn_exrt']
    
    return return_data

  def get_trading_period_rights(self, in_tr_id: str, in_tr_cont: str, in_custtype: str, in_seq_no: str, in_mac_address: str, in_phone_number: str, in_ip_addr: str, in_gt_uid: str, in_INQR_DVSN: str, in_CUST_RNCNO25: str, in_HMID: str, in_CANO: str, in_ACNT_PRDT_CD: str, in_INQR_STRT_DT: str, in_INQR_END_DT: str, in_RGHT_TYPE_CD: str, in_PDNO: str, in_PRDT_TYPE_CD: str, in_CTX_AREA_NK100: str, in_CTX_AREA_FK100: str):
    """
    기간별계좌권리현황조회
    메뉴 위치 : [국내주식] 주문/계좌
    - 실전 TR_ID : CTRGA011R
    - 모의 TR_ID : 모의투자 미지원
    
    개요 : 기간별계좌권리현황조회 API입니다.
      한국투자 HTS(eFriend Plus) &gt; [7344] 권리유형별 현황조회 화면을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.
    
    Args:
      in_tr_id (str(13)): 거래ID(필수). CTRGA011R
      in_tr_cont (str(1)): 연속 거래 여부. 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우)
      in_custtype (str(1)): 고객 타입(필수). B : 법인  P : 개인
      in_seq_no (str(2)): 일련번호. [법인 필수] 001
      in_mac_address (str(12)): 맥주소. 법인고객 혹은 개인고객의 Mac address 값
      in_phone_number (str(12)): 핸드폰번호. [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거)
      in_ip_addr (str(12)): 접속 단말 공인 IP. [법인 필수] 사용자(회원)의 IP Address
      in_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      in_INQR_DVSN (str(2)): 조회구분(필수). 03 입력
      in_CUST_RNCNO25 (str(25)): 고객실명확인번호25(필수). 공란
      in_HMID (str(8)): 홈넷ID(필수). 공란
      in_CANO (str(8)): 종합계좌번호(필수). 계좌번호 8자리 입력 (ex.12345678)
      in_ACNT_PRDT_CD (str(2)): 계좌상품코드(필수). 상품계좌번호 2자리 입력(ex. 01 or 22)
      in_INQR_STRT_DT (str(8)): 조회시작일자(필수). 조회시작일자(YYYYMMDD)
      in_INQR_END_DT (str(8)): 조회종료일자(필수). 조회종료일자(YYYYMMDD)
      in_RGHT_TYPE_CD (str(2)): 권리유형코드(필수). 공란
      in_PDNO (str(12)): 상품번호(필수). 공란
      in_PRDT_TYPE_CD (str(3)): 상품유형코드(필수). 공란
      in_CTX_AREA_NK100 (str(100)): 연속조회키100(필수). 다음조회시 입력
      in_CTX_AREA_FK100 (str(100)): 연속조회검색조건100(필수). 다음조회시 입력
    
    Returns:
      out_tr_id (str(13)): 거래ID. 요청한 tr_id
      out_tr_cont (str(1)): 연속 거래 여부. F or M : 다음 데이터 있음 D or E : 마지막 데이터
      out_gt_uid (str(32)): Global UID. [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함
      out_rt_cd (str(1)): 성공 실패 여부
      out_msg_cd (str(8)): 응답코드
      out_msg1 (str(80)): 응답메세지
      out_output1 (str): 응답상세. array
      out_acno10 (str(10)): 계좌번호10
      out_rght_type_cd (str(2)): 권리유형코드. 1	유상 2	무상 3	배당 4	매수청구 5	공개매수 6	주주총회 7	신주인수권증서 8	반대의사 9	신주인수권증권 11	합병 12	회사분할 13	주식교환 14	액면분할 15	액면병합 16	종목변경 17	감자 18	신구주합병 21	후합병 22	후회사분할 23	후주식교환 24	후액면분할 25	후액면병합 26	후종목변경 27	후감자 28	후신구주합병 31	뮤츄얼펀드 32	ETF 33	선박투자회사 34	투융자회사 35	해외자원 36	부동산신탁(Ritz) 37	상장수익증권 41	ELW만기 42	ELS분배 43	DLS분배 44	하일드펀드 45	ETN 51	전환청구 52	교환청구 53	BW청구 54	WRT청구 55	채권풋옵션청구 56	전환우선주청구 57	전환조건부청구 58	전자증권일괄입고 59	클라우드펀딩일괄입고 61	원리금상환 62	스트립채권 71	WRT소멸 72	WRT증권 73	DR전환 74	배당옵션 75	특별배당 76	ISINCODE변경 77	실권주청약 81	해외분배금(청산) 82	해외분배금(조기상환) 83	해외분배금(상장폐지) 84	DR FEE 85	SECTION 871M 86	종목전환 87	재매수 88	종목교환 89	기타이벤트 91	공모주 92	청약 93	환매 99	기타권리사유
      out_bass_dt (str(8)): 기준일자
      out_rght_cblc_type_cd (str(2)): 권리잔고유형코드. 1	입고 2	출고 3	출고입고 4	출고입금 5	출고출금 10	현금입금 11	단수주대금입금 12	교부금입금 13	유상감자대금입금 14	지연이자입금 15	이자지급 16	대주권리금출금 17	분할상환 18	만기상환 19	조기상환 20	출금 21	입고&입금 22	입고&입금&단수주대금입금 25	유상환불금입금 26	중도상환 27	분할합병세금출금
      out_rptt_pdno (str(12)): 대표상품번호
      out_pdno (str(12)): 상품번호
      out_prdt_type_cd (str(3)): 상품유형코드
      out_shtn_pdno (str(12)): 단축상품번호
      out_prdt_name (str(60)): 상품명
      out_cblc_qty (str(19)): 잔고수량
      out_last_alct_qty (str(19)): 최종배정수량
      out_excs_alct_qty (str(19)): 초과배정수량
      out_tot_alct_qty (str(19)): 총배정수량
      out_last_ftsk_qty (str(191)): 최종단수주수량
      out_last_alct_amt (str(19)): 최종배정금액
      out_last_ftsk_chgs (str(19)): 최종단수주대금
      out_rdpt_prca (str(19)): 상환원금
      out_dlay_int_amt (str(19)): 지연이자금액
      out_lstg_dt (str(8)): 상장일자
      out_sbsc_end_dt (str(8)): 청약종료일자
      out_cash_dfrm_dt (str(8)): 현금지급일자
      out_rqst_qty (str(19)): 신청수량
      out_rqst_amt (str(19)): 신청금액
      out_rqst_dt (str(8)): 신청일자
      out_rfnd_dt (str(8)): 환불일자
      out_rfnd_amt (str(19)): 환불금액
      out_lstg_stqt (str(19)): 상장주수
      out_tax_amt (str(19)): 세금금액
      out_sbsc_unpr (str(224)): 청약단가
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    token = self.token_data['access_token']
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'authorization': f'Bearer {token}',
      'appkey': self.app_key,
      'appsecret': self.app_secret,
      'tr_id': in_tr_id,
      'tr_cont': in_tr_cont,
      'custtype': in_custtype,
      'seq_no': in_seq_no,
      'mac_address': in_mac_address,
      'phone_number': in_phone_number,
      'ip_addr': in_ip_addr,
      'gt_uid': in_gt_uid,
      'INQR_DVSN': in_INQR_DVSN,
      'CUST_RNCNO25': in_CUST_RNCNO25,
      'HMID': in_HMID,
      'CANO': in_CANO,
      'ACNT_PRDT_CD': in_ACNT_PRDT_CD,
      'INQR_STRT_DT': in_INQR_STRT_DT,
      'INQR_END_DT': in_INQR_END_DT,
      'RGHT_TYPE_CD': in_RGHT_TYPE_CD,
      'PDNO': in_PDNO,
      'PRDT_TYPE_CD': in_PRDT_TYPE_CD,
      'CTX_AREA_NK100': in_CTX_AREA_NK100,
      'CTX_AREA_FK100': in_CTX_AREA_FK100,
      'api-id': '국내주식-211',
    }
    params = {}
    url = '/uapi/domestic-stock/v1/trading/period-rights'
    
    header_data, out_data = self._send_request(url, 'GET', params, headers)
    
    if not out_data or out_data['rt_cd'] != 'Y':
      msg = out_data['msg1'] if out_data and out_data['msg1'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_tr_id'] = header_data['tr_id']
      return_data['out_tr_cont'] = header_data['tr_cont']
      return_data['out_gt_uid'] = header_data['gt_uid']
    
    return_data['out_rt_cd'] = out_data['rt_cd']
    return_data['out_msg_cd'] = out_data['msg_cd']
    return_data['out_msg1'] = out_data['msg1']
    return_data['out_output1'] = out_data['output1']
    return_data['out_acno10'] = out_data['acno10']
    return_data['out_rght_type_cd'] = out_data['rght_type_cd']
    return_data['out_bass_dt'] = out_data['bass_dt']
    return_data['out_rght_cblc_type_cd'] = out_data['rght_cblc_type_cd']
    return_data['out_rptt_pdno'] = out_data['rptt_pdno']
    return_data['out_pdno'] = out_data['pdno']
    return_data['out_prdt_type_cd'] = out_data['prdt_type_cd']
    return_data['out_shtn_pdno'] = out_data['shtn_pdno']
    return_data['out_prdt_name'] = out_data['prdt_name']
    return_data['out_cblc_qty'] = out_data['cblc_qty']
    return_data['out_last_alct_qty'] = out_data['last_alct_qty']
    return_data['out_excs_alct_qty'] = out_data['excs_alct_qty']
    return_data['out_tot_alct_qty'] = out_data['tot_alct_qty']
    return_data['out_last_ftsk_qty'] = out_data['last_ftsk_qty']
    return_data['out_last_alct_amt'] = out_data['last_alct_amt']
    return_data['out_last_ftsk_chgs'] = out_data['last_ftsk_chgs']
    return_data['out_rdpt_prca'] = out_data['rdpt_prca']
    return_data['out_dlay_int_amt'] = out_data['dlay_int_amt']
    return_data['out_lstg_dt'] = out_data['lstg_dt']
    return_data['out_sbsc_end_dt'] = out_data['sbsc_end_dt']
    return_data['out_cash_dfrm_dt'] = out_data['cash_dfrm_dt']
    return_data['out_rqst_qty'] = out_data['rqst_qty']
    return_data['out_rqst_amt'] = out_data['rqst_amt']
    return_data['out_rqst_dt'] = out_data['rqst_dt']
    return_data['out_rfnd_dt'] = out_data['rfnd_dt']
    return_data['out_rfnd_amt'] = out_data['rfnd_amt']
    return_data['out_lstg_stqt'] = out_data['lstg_stqt']
    return_data['out_tax_amt'] = out_data['tax_amt']
    return_data['out_sbsc_unpr'] = out_data['sbsc_unpr']
    
    return return_data