import requests
import json
from datetime import datetime
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
log_file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), f'logs/kiwoom_api_{format_datetime('%Y%m%d')}.log'))
file_handler = logging.FileHandler(filename=log_file_name)
logger.addHandler(file_handler)

user_token_data = {}

class KiwoomAPI():
  """
  키움증권 REST API 서버와 직접 요청과 응답을 주고받는 클래스
  API 신청 계좌만 조회 가능
  """
  def __init__(self, is_real: bool, in_app_key: str, in_app_secret: str):
    """
    키움증권 REST API init

    Args:
      is_real (boon): 실전 여부
      in_app_key (str): 키움증권 API 신청 계좌의 앱키
      in_app_secret (str): 키움증권 API 신청 계좌의 시크릿키
    """
    # 키움증권 API 신청 키
    self.app_key = in_app_key
    self.app_secret = in_app_secret
    if is_real:
      ## 실전
      self.base_url = "https://api.kiwoom.com"
    else:
      ## 모의
      self.base_url = "https://mockapi.kiwoom.com"
    # 토큰 정보
    self.token_data = None
    self.json_file_name = f'kiwoom_token_{format_datetime('%Y%m%d')}.json'
    if os.path.exists(self.json_file_name):
      with open(self.json_file_name, 'r', encoding='utf-8') as f:
        txt = f.read()
        f.close()
        print(txt.strip())
        if txt and txt.strip().startswith('{'):
          user_token_data = json.loads(txt)
          if self.app_key in user_token_data:
            expires_dt = user_token_data[self.app_key]['expires_dt']
            format = '%Y%m%d%H%M%S'
            current_time = datetime.now()
            end_time = datetime.strptime(expires_dt, format)
            time_difference = end_time - current_time
            print(f'expires_dt : {time_difference.total_seconds()} seconds after...')
            if time_difference.total_seconds() > 0:
              self.token_data = user_token_data[self.app_key]
              print(self.token_data)

  def _send_request(self, url: str, params: dict, headers: dict):
    """
    내부 공통 요청 처리 함수
    """
    #headers["Accept"] = "text/plain"
    #headers["charset"] = "UTF-8"
    full_url = f"{self.base_url}{url}"
    logger.debug(headers)
    logger.debug(params)
    logger.debug(full_url)
    response = requests.post(full_url, data=json.dumps(params), headers=headers)
    response.raise_for_status()
    logger.debug(f"status_code : {response.status_code}")
    if response.status_code == 200:
      #logger.debug("response headers :", json.dumps(response.headers()))
      #logger.debug("response text :", response.text)
      #response_data = json.loads(response.text)
      response_data = response.json()
      logger.debug("response data :", response.text)
      logger.debug("response data keys :", response_data.keys())
      response_headers = {}
      for x in response.headers.keys():
        if x.islower():
          response_headers[x] = response.headers.get(x)
      logger.debug("response headers :", response_headers)
      return response_headers, response_data
    else:
      return None, None

  def connect(self):
    """
    키움증권 REST API 토큰을 발급받습니다.
    본인 계좌에 필요한 인증 절차로, 인증을 통해 접근 토큰을 부여받아 오픈API 활용이 가능합니다.

    Raises:
      RuntimeError: 토큰을 발급받지 못한 경우
    """

    if not self.token_data:
      headers = {
        "Content-Type": "application/json"
      }
      params = {
        "grant_type": "client_credentials",
        "appkey": self.app_key,
        "secretkey": self.app_secret,
      }
      url = '/oauth2/token'

      full_url = f"{self.base_url}{url}"
      logger.debug(headers)
      logger.debug(params)
      logger.debug(full_url)
      response = requests.post(full_url, data=json.dumps(params), headers=headers)
      response.raise_for_status()
      logger.debug(f"status_code : {response.status_code}")
      if response.status_code == 200:
        token_data = response.json()
        logger.debug("token_data :", token_data)
        if token_data and token_data['token']:
          self.token_data = token_data
          user_token_data[self.app_key] = token_data
          with open(self.json_file_name, 'w', encoding='utf-8') as f:
            f.write(json.dumps(user_token_data, indent=4))
            f.close()
        else:
          self.token_data = None
          raise RuntimeError("Not connected: token is not available.")
      else:
        self.token_data = None
        raise RuntimeError("Not connected: token is not available.")

  def close(self):
    """
    리소스를 정리합니다.
    """
    self.token_data = None

  def get_ka00198(self, in_cont_yn: str, in_next_key: str, in_qry_tp: str):
    """
    실시간종목조회순위
    메뉴 위치 : 국내주식 > 종목정보 > 실시간종목조회순위(ka00198)

    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_qry_tp (str(1)): 구분(필수) 1:1분, 2:10분, 3:1시간, 4:당일 누적, 5:30초

    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_item_inq_rank (list): 실시간종목조회순위
        - stk_nm (str(40)): 종목명
        - bigd_rank (str(20)): 빅데이터 순위
        - rank_chg (str(20)): 순위 등락
        - rank_chg_sign (str(20)): 순위 등락 부호
        - past_curr_prc (str(20)): 과거 현재가
        - base_comp_sign (str(20)): 기준가 대비 부호
        - base_comp_chgr (str(20)): 기준가 대비 등락율
        - prev_base_sign (str(20)): 직전 기준 대비 부호
        - prev_base_chgr (str(20)): 직전 기준 대비 등락율
        - dt (str(20)): 일자
        - tm (str(20)): 시간
        - stk_cd (str(20)): 종목코드

    Raises:
      Exception: 에러
    """

    if not self.token_data:
      self.connect()

    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka00198',
    }
    params = {
      'qry_tp': in_qry_tp,
    }
    url = '/api/dostk/stkinfo'

    header_data, out_data = self._send_request(url, params, headers)

    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)

    return_data = {}

    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']

    return_data['out_item_inq_rank'] = out_data['item_inq_rank']

    return return_data

  def get_ka10001(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    주식기본정보요청
    메뉴 위치 : 국내주식 > 종목정보 > 주식기본정보요청(ka10001)

    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)

    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_cd (str(20)): 종목코드
      out_stk_nm (str(40)): 종목명
      out_setl_mm (str(20)): 결산월
      out_fav (str(20)): 액면가
      out_cap (str(20)): 자본금
      out_flo_stk (str(20)): 상장주식
      out_crd_rt (str(20)): 신용비율
      out_oyr_hgst (str(20)): 연중최고
      out_oyr_lwst (str(20)): 연중최저
      out_mac (str(20)): 시가총액
      out_mac_wght (str(20)): 시가총액비중
      out_for_exh_rt (str(20)): 외인소진률
      out_repl_pric (str(20)): 대용가
      out_per (str(20)): PER. [ 주의 ] PER, ROE 값들은 외부벤더사에서 제공되는 데이터이며 일주일에 한번 또는 실적발표 시즌에 업데이트 됨
      out_eps (str(20)): EPS
      out_roe (str(20)): ROE. [ 주의 ]  PER, ROE 값들은 외부벤더사에서 제공되는 데이터이며 일주일에 한번 또는 실적발표 시즌에 업데이트 됨
      out_pbr (str(20)): PBR
      out_ev (str(20)): EV
      out_bps (str(20)): BPS
      out_sale_amt (str(20)): 매출액
      out_bus_pro (str(20)): 영업이익
      out_cup_nga (str(20)): 당기순이익
      out_250hgst (str(20)): 250최고
      out_250lwst (str(20)): 250최저
      out_open_pric (str(20)): 시가
      out_high_pric (str(20)): 고가
      out_low_pric (str(20)): 저가
      out_upl_pric (str(20)): 상한가
      out_lst_pric (str(20)): 하한가
      out_base_pric (str(20)): 기준가
      out_exp_cntr_pric (str(20)): 예상체결가
      out_exp_cntr_qty (str(20)): 예상체결수량
      out_250hgst_pric_dt (str(20)): 250최고가일
      out_250hgst_pric_pre_rt (str(20)): 250최고가대비율
      out_250lwst_pric_dt (str(20)): 250최저가일
      out_250lwst_pric_pre_rt (str(20)): 250최저가대비율
      out_cur_prc (str(20)): 현재가
      out_pre_sig (str(20)): 대비기호
      out_pred_pre (str(20)): 전일대비
      out_flu_rt (str(20)): 등락율
      out_trde_qty (str(20)): 거래량
      out_trde_pre (str(20)): 거래대비
      out_fav_unit (str(20)): 액면가단위
      out_dstr_stk (str(20)): 유통주식
      out_dstr_rt (str(20)): 유통비율

    Raises:
      Exception: 에러
    """

    if not self.token_data:
      self.connect()

    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10001',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/stkinfo'

    header_data, out_data = self._send_request(url, params, headers)

    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)

    return_data = {}

    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']

    return_data['out_stk_cd'] = out_data['stk_cd']
    return_data['out_stk_nm'] = out_data['stk_nm']
    return_data['out_setl_mm'] = out_data['setl_mm']
    return_data['out_fav'] = out_data['fav']
    return_data['out_cap'] = out_data['cap']
    return_data['out_flo_stk'] = out_data['flo_stk']
    return_data['out_crd_rt'] = out_data['crd_rt']
    return_data['out_oyr_hgst'] = out_data['oyr_hgst']
    return_data['out_oyr_lwst'] = out_data['oyr_lwst']
    return_data['out_mac'] = out_data['mac']
    return_data['out_mac_wght'] = out_data['mac_wght']
    return_data['out_for_exh_rt'] = out_data['for_exh_rt']
    return_data['out_repl_pric'] = out_data['repl_pric']
    return_data['out_per'] = out_data['per']
    return_data['out_eps'] = out_data['eps']
    return_data['out_roe'] = out_data['roe']
    return_data['out_pbr'] = out_data['pbr']
    return_data['out_ev'] = out_data['ev']
    return_data['out_bps'] = out_data['bps']
    return_data['out_sale_amt'] = out_data['sale_amt']
    return_data['out_bus_pro'] = out_data['bus_pro']
    return_data['out_cup_nga'] = out_data['cup_nga']
    return_data['out_250hgst'] = out_data['250hgst']
    return_data['out_250lwst'] = out_data['250lwst']
    return_data['out_open_pric'] = out_data['open_pric']
    return_data['out_high_pric'] = out_data['high_pric']
    return_data['out_low_pric'] = out_data['low_pric']
    return_data['out_upl_pric'] = out_data['upl_pric']
    return_data['out_lst_pric'] = out_data['lst_pric']
    return_data['out_base_pric'] = out_data['base_pric']
    return_data['out_exp_cntr_pric'] = out_data['exp_cntr_pric']
    return_data['out_exp_cntr_qty'] = out_data['exp_cntr_qty']
    return_data['out_250hgst_pric_dt'] = out_data['250hgst_pric_dt']
    return_data['out_250hgst_pric_pre_rt'] = out_data['250hgst_pric_pre_rt']
    return_data['out_250lwst_pric_dt'] = out_data['250lwst_pric_dt']
    return_data['out_250lwst_pric_pre_rt'] = out_data['250lwst_pric_pre_rt']
    return_data['out_cur_prc'] = out_data['cur_prc']
    return_data['out_pre_sig'] = out_data['pre_sig']
    return_data['out_pred_pre'] = out_data['pred_pre']
    return_data['out_flu_rt'] = out_data['flu_rt']
    return_data['out_trde_qty'] = out_data['trde_qty']
    return_data['out_trde_pre'] = out_data['trde_pre']
    return_data['out_fav_unit'] = out_data['fav_unit']
    return_data['out_dstr_stk'] = out_data['dstr_stk']
    return_data['out_dstr_rt'] = out_data['dstr_rt']

    return return_data