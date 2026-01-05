import requests
import json
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
      response_data = json.loads(response.text)
      logger.debug("response data :", response_data)
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
      token_data = json.loads(response.text)
      logger.debug("token_data :", token_data)
      if token_data and token_data['token']:
        self.token_data = token_data
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

  def get_ka10002(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    주식거래원요청
    메뉴 위치 : 국내주식 > 종목정보 > 주식거래원요청(ka10002)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_cd (str(20)): 종목코드
      out_stk_nm (str(40)): 종목명
      out_cur_prc (str(20)): 현재가
      out_flu_smbol (str(20)): 등락부호
      out_base_pric (str(20)): 기준가
      out_pred_pre (str(20)): 전일대비
      out_flu_rt (str(20)): 등락율
      out_sel_trde_ori_nm_1 (str(20)): 매도거래원명1
      out_sel_trde_ori_1 (str(20)): 매도거래원1
      out_sel_trde_qty_1 (str(20)): 매도거래량1
      out_buy_trde_ori_nm_1 (str(20)): 매수거래원명1
      out_buy_trde_ori_1 (str(20)): 매수거래원1
      out_buy_trde_qty_1 (str(20)): 매수거래량1
      out_sel_trde_ori_nm_2 (str(20)): 매도거래원명2
      out_sel_trde_ori_2 (str(20)): 매도거래원2
      out_sel_trde_qty_2 (str(20)): 매도거래량2
      out_buy_trde_ori_nm_2 (str(20)): 매수거래원명2
      out_buy_trde_ori_2 (str(20)): 매수거래원2
      out_buy_trde_qty_2 (str(20)): 매수거래량2
      out_sel_trde_ori_nm_3 (str(20)): 매도거래원명3
      out_sel_trde_ori_3 (str(20)): 매도거래원3
      out_sel_trde_qty_3 (str(20)): 매도거래량3
      out_buy_trde_ori_nm_3 (str(20)): 매수거래원명3
      out_buy_trde_ori_3 (str(20)): 매수거래원3
      out_buy_trde_qty_3 (str(20)): 매수거래량3
      out_sel_trde_ori_nm_4 (str(20)): 매도거래원명4
      out_sel_trde_ori_4 (str(20)): 매도거래원4
      out_sel_trde_qty_4 (str(20)): 매도거래량4
      out_buy_trde_ori_nm_4 (str(20)): 매수거래원명4
      out_buy_trde_ori_4 (str(20)): 매수거래원4
      out_buy_trde_qty_4 (str(20)): 매수거래량4
      out_sel_trde_ori_nm_5 (str(20)): 매도거래원명5
      out_sel_trde_ori_5 (str(20)): 매도거래원5
      out_sel_trde_qty_5 (str(20)): 매도거래량5
      out_buy_trde_ori_nm_5 (str(20)): 매수거래원명5
      out_buy_trde_ori_5 (str(20)): 매수거래원5
      out_buy_trde_qty_5 (str(20)): 매수거래량5
    
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
      'api-id': 'ka10002',
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
    return_data['out_cur_prc'] = out_data['cur_prc']
    return_data['out_flu_smbol'] = out_data['flu_smbol']
    return_data['out_base_pric'] = out_data['base_pric']
    return_data['out_pred_pre'] = out_data['pred_pre']
    return_data['out_flu_rt'] = out_data['flu_rt']
    return_data['out_sel_trde_ori_nm_1'] = out_data['sel_trde_ori_nm_1']
    return_data['out_sel_trde_ori_1'] = out_data['sel_trde_ori_1']
    return_data['out_sel_trde_qty_1'] = out_data['sel_trde_qty_1']
    return_data['out_buy_trde_ori_nm_1'] = out_data['buy_trde_ori_nm_1']
    return_data['out_buy_trde_ori_1'] = out_data['buy_trde_ori_1']
    return_data['out_buy_trde_qty_1'] = out_data['buy_trde_qty_1']
    return_data['out_sel_trde_ori_nm_2'] = out_data['sel_trde_ori_nm_2']
    return_data['out_sel_trde_ori_2'] = out_data['sel_trde_ori_2']
    return_data['out_sel_trde_qty_2'] = out_data['sel_trde_qty_2']
    return_data['out_buy_trde_ori_nm_2'] = out_data['buy_trde_ori_nm_2']
    return_data['out_buy_trde_ori_2'] = out_data['buy_trde_ori_2']
    return_data['out_buy_trde_qty_2'] = out_data['buy_trde_qty_2']
    return_data['out_sel_trde_ori_nm_3'] = out_data['sel_trde_ori_nm_3']
    return_data['out_sel_trde_ori_3'] = out_data['sel_trde_ori_3']
    return_data['out_sel_trde_qty_3'] = out_data['sel_trde_qty_3']
    return_data['out_buy_trde_ori_nm_3'] = out_data['buy_trde_ori_nm_3']
    return_data['out_buy_trde_ori_3'] = out_data['buy_trde_ori_3']
    return_data['out_buy_trde_qty_3'] = out_data['buy_trde_qty_3']
    return_data['out_sel_trde_ori_nm_4'] = out_data['sel_trde_ori_nm_4']
    return_data['out_sel_trde_ori_4'] = out_data['sel_trde_ori_4']
    return_data['out_sel_trde_qty_4'] = out_data['sel_trde_qty_4']
    return_data['out_buy_trde_ori_nm_4'] = out_data['buy_trde_ori_nm_4']
    return_data['out_buy_trde_ori_4'] = out_data['buy_trde_ori_4']
    return_data['out_buy_trde_qty_4'] = out_data['buy_trde_qty_4']
    return_data['out_sel_trde_ori_nm_5'] = out_data['sel_trde_ori_nm_5']
    return_data['out_sel_trde_ori_5'] = out_data['sel_trde_ori_5']
    return_data['out_sel_trde_qty_5'] = out_data['sel_trde_qty_5']
    return_data['out_buy_trde_ori_nm_5'] = out_data['buy_trde_ori_nm_5']
    return_data['out_buy_trde_ori_5'] = out_data['buy_trde_ori_5']
    return_data['out_buy_trde_qty_5'] = out_data['buy_trde_qty_5']
    
    return return_data

  def get_ka10003(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    체결정보요청
    메뉴 위치 : 국내주식 > 종목정보 > 체결정보요청(ka10003)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_cntr_infr (list): 체결정보
        - tm (str(20)): 시간
        - cur_prc (str(20)): 현재가
        - pred_pre (str(20)): 전일대비
        - pre_rt (str(20)): 대비율
        - pri_sel_bid_unit (str(20)): 우선매도호가단위
        - pri_buy_bid_unit (str(20)): 우선매수호가단위
        - cntr_trde_qty (str(20)): 체결거래량
        - sign (str(20)): sign
        - acc_trde_qty (str(20)): 누적거래량
        - acc_trde_prica (str(20)): 누적거래대금
        - cntr_str (str(20)): 체결강도
        - stex_tp (str(20)): 거래소구분. KRX , NXT , 통합
    
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
      'api-id': 'ka10003',
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
    
    return_data['out_cntr_infr'] = out_data['cntr_infr']
    
    return return_data

  def get_ka10013(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_dt: str, in_qry_tp: str):
    """
    신용매매동향요청
    메뉴 위치 : 국내주식 > 종목정보 > 신용매매동향요청(ka10013)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_dt (str(8)): 일자(필수) YYYYMMDD
      in_qry_tp (str(1)): 조회구분(필수) 1:융자, 2:대주
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_crd_trde_trend (list): 신용매매동향
        - dt (str(20)): 일자
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - trde_qty (str(20)): 거래량
        - new (str(20)): 신규
        - rpya (str(20)): 상환
        - remn (str(20)): 잔고
        - amt (str(20)): 금액
        - pre (str(20)): 대비
        - shr_rt (str(20)): 공여율
        - remn_rt (str(20)): 잔고율
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10013',
    }
    params = {
      'stk_cd': in_stk_cd,
      'dt': in_dt,
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
    
    return_data['out_crd_trde_trend'] = out_data['crd_trde_trend']
    
    return return_data

  def get_ka10015(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_strt_dt: str):
    """
    일별거래상세요청
    메뉴 위치 : 국내주식 > 종목정보 > 일별거래상세요청(ka10015)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_daly_trde_dtl (list): 일별거래상세
        - dt (str(20)): 일자
        - close_pric (str(20)): 종가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - trde_prica (str(20)): 거래대금
        - bf_mkrt_trde_qty (str(20)): 장전거래량
        - bf_mkrt_trde_wght (str(20)): 장전거래비중
        - opmr_trde_qty (str(20)): 장중거래량
        - opmr_trde_wght (str(20)): 장중거래비중
        - af_mkrt_trde_qty (str(20)): 장후거래량
        - af_mkrt_trde_wght (str(20)): 장후거래비중
        - tot_3 (str(20)): 합계3
        - prid_trde_qty (str(20)): 기간중거래량
        - cntr_str (str(20)): 체결강도
        - for_poss (str(20)): 외인보유
        - for_wght (str(20)): 외인비중
        - for_netprps (str(20)): 외인순매수
        - orgn_netprps (str(20)): 기관순매수
        - ind_netprps (str(20)): 개인순매수
        - frgn (str(20)): 외국계
        - crd_remn_rt (str(20)): 신용잔고율
        - prm (str(20)): 프로그램
        - bf_mkrt_trde_prica (str(20)): 장전거래대금
        - bf_mkrt_trde_prica_wght (str(20)): 장전거래대금비중
        - opmr_trde_prica (str(20)): 장중거래대금
        - opmr_trde_prica_wght (str(20)): 장중거래대금비중
        - af_mkrt_trde_prica (str(20)): 장후거래대금
        - af_mkrt_trde_prica_wght (str(20)): 장후거래대금비중
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10015',
    }
    params = {
      'stk_cd': in_stk_cd,
      'strt_dt': in_strt_dt,
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
    
    return_data['out_daly_trde_dtl'] = out_data['daly_trde_dtl']
    
    return return_data

  def get_ka10016(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_ntl_tp: str, in_high_low_close_tp: str, in_stk_cnd: str, in_trde_qty_tp: str, in_crd_cnd: str, in_updown_incls: str, in_dt: str, in_stex_tp: str):
    """
    신고저가요청
    메뉴 위치 : 국내주식 > 종목정보 > 신고저가요청(ka10016)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_ntl_tp (str(1)): 신고저구분(필수) 1:신고가,2:신저가
      in_high_low_close_tp (str(1)): 고저종구분(필수) 1:고저기준, 2:종가기준
      in_stk_cnd (str(1)): 종목조건(필수) 0:전체조회,1:관리종목제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기
      in_trde_qty_tp (str(5)): 거래량구분(필수) 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상
      in_crd_cnd (str(1)): 신용조건(필수) 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체
      in_updown_incls (str(1)): 상하한포함(필수) 0:미포함, 1:포함
      in_dt (str(3)): 기간(필수) 5:5일, 10:10일, 20:20일, 60:60일, 250:250일, 250일까지 입력가능
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ntl_pric (list): 신고저가
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - trde_qty (str(20)): 거래량
        - pred_trde_qty_pre_rt (str(20)): 전일거래량대비율
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10016',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'ntl_tp': in_ntl_tp,
      'high_low_close_tp': in_high_low_close_tp,
      'stk_cnd': in_stk_cnd,
      'trde_qty_tp': in_trde_qty_tp,
      'crd_cnd': in_crd_cnd,
      'updown_incls': in_updown_incls,
      'dt': in_dt,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_ntl_pric'] = out_data['ntl_pric']
    
    return return_data

  def get_ka10017(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_updown_tp: str, in_sort_tp: str, in_stk_cnd: str, in_trde_qty_tp: str, in_crd_cnd: str, in_trde_gold_tp: str, in_stex_tp: str):
    """
    상하한가요청
    메뉴 위치 : 국내주식 > 종목정보 > 상하한가요청(ka10017)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_updown_tp (str(1)): 상하한구분(필수) 1:상한, 2:상승, 3:보합, 4: 하한, 5:하락, 6:전일상한, 7:전일하한
      in_sort_tp (str(1)): 정렬구분(필수) 1:종목코드순, 2:연속횟수순(상위100개), 3:등락률순
      in_stk_cnd (str(1)): 종목조건(필수) 0:전체조회,1:관리종목제외, 3:우선주제외, 4:우선주+관리종목제외, 5:증100제외, 6:증100만 보기, 7:증40만 보기, 8:증30만 보기, 9:증20만 보기, 10:우선주+관리종목+환기종목제외
      in_trde_qty_tp (str(5)): 거래량구분(필수) 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상
      in_crd_cnd (str(1)): 신용조건(필수) 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체
      in_trde_gold_tp (str(1)): 매매금구분(필수) 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~3천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_updown_pric (list): 상하한가
        - stk_cd (str(20)): 종목코드
        - stk_infr (str(20)): 종목정보
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - trde_qty (str(20)): 거래량
        - pred_trde_qty (str(20)): 전일거래량
        - sel_req (str(20)): 매도잔량
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
        - buy_req (str(20)): 매수잔량
        - cnt (str(20)): 횟수
    
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
      'api-id': 'ka10017',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'updown_tp': in_updown_tp,
      'sort_tp': in_sort_tp,
      'stk_cnd': in_stk_cnd,
      'trde_qty_tp': in_trde_qty_tp,
      'crd_cnd': in_crd_cnd,
      'trde_gold_tp': in_trde_gold_tp,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_updown_pric'] = out_data['updown_pric']
    
    return return_data

  def get_ka10018(self, in_cont_yn: str, in_next_key: str, in_high_low_tp: str, in_alacc_rt: str, in_mrkt_tp: str, in_trde_qty_tp: str, in_stk_cnd: str, in_crd_cnd: str, in_stex_tp: str):
    """
    고저가근접요청
    메뉴 위치 : 국내주식 > 종목정보 > 고저가근접요청(ka10018)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_high_low_tp (str(1)): 고저구분(필수) 1:고가, 2:저가
      in_alacc_rt (str(2)): 근접율(필수) 05:0.5 10:1.0, 15:1.5, 20:2.0. 25:2.5, 30:3.0
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_trde_qty_tp (str(5)): 거래량구분(필수) 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상
      in_stk_cnd (str(1)): 종목조건(필수) 0:전체조회,1:관리종목제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기
      in_crd_cnd (str(1)): 신용조건(필수) 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_high_low_pric_alacc (list): 고저가근접
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - trde_qty (str(20)): 거래량
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
        - tdy_high_pric (str(20)): 당일고가
        - tdy_low_pric (str(20)): 당일저가
    
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
      'api-id': 'ka10018',
    }
    params = {
      'high_low_tp': in_high_low_tp,
      'alacc_rt': in_alacc_rt,
      'mrkt_tp': in_mrkt_tp,
      'trde_qty_tp': in_trde_qty_tp,
      'stk_cnd': in_stk_cnd,
      'crd_cnd': in_crd_cnd,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_high_low_pric_alacc'] = out_data['high_low_pric_alacc']
    
    return return_data

  def get_ka10019(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_flu_tp: str, in_tm_tp: str, in_tm: str, in_trde_qty_tp: str, in_stk_cnd: str, in_crd_cnd: str, in_pric_cnd: str, in_updown_incls: str, in_stex_tp: str):
    """
    가격급등락요청
    메뉴 위치 : 국내주식 > 종목정보 > 가격급등락요청(ka10019)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥, 201:코스피200
      in_flu_tp (str(1)): 등락구분(필수) 1:급등, 2:급락
      in_tm_tp (str(1)): 시간구분(필수) 1:분전, 2:일전
      in_tm (str(2)): 시간(필수) 분 혹은 일입력
      in_trde_qty_tp (str(4)): 거래량구분(필수) 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상
      in_stk_cnd (str(1)): 종목조건(필수) 0:전체조회,1:관리종목제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기
      in_crd_cnd (str(1)): 신용조건(필수) 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체
      in_pric_cnd (str(1)): 가격조건(필수) 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~3천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상
      in_updown_incls (str(1)): 상하한포함(필수) 0:미포함, 1:포함
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_pric_jmpflu (list): 가격급등락
        - stk_cd (str(20)): 종목코드
        - stk_cls (str(20)): 종목분류
        - stk_nm (str(40)): 종목명
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - base_pric (str(20)): 기준가
        - cur_prc (str(20)): 현재가
        - base_pre (str(20)): 기준대비
        - trde_qty (str(20)): 거래량
        - jmp_rt (str(20)): 급등률
    
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
      'api-id': 'ka10019',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'flu_tp': in_flu_tp,
      'tm_tp': in_tm_tp,
      'tm': in_tm,
      'trde_qty_tp': in_trde_qty_tp,
      'stk_cnd': in_stk_cnd,
      'crd_cnd': in_crd_cnd,
      'pric_cnd': in_pric_cnd,
      'updown_incls': in_updown_incls,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_pric_jmpflu'] = out_data['pric_jmpflu']
    
    return return_data

  def get_ka10024(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_cycle_tp: str, in_trde_qty_tp: str, in_stex_tp: str):
    """
    거래량갱신요청
    메뉴 위치 : 국내주식 > 종목정보 > 거래량갱신요청(ka10024)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_cycle_tp (str(1)): 주기구분(필수) 5:5일, 10:10일, 20:20일, 60:60일, 250:250일
      in_trde_qty_tp (str(1)): 거래량구분(필수) 5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_trde_qty_updt (list): 거래량갱신
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - prev_trde_qty (str(20)): 이전거래량
        - now_trde_qty (str(20)): 현재거래량
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
    
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
      'api-id': 'ka10024',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'cycle_tp': in_cycle_tp,
      'trde_qty_tp': in_trde_qty_tp,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_trde_qty_updt'] = out_data['trde_qty_updt']
    
    return return_data

  def get_ka10025(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_prps_cnctr_rt: str, in_cur_prc_entry: str, in_prpscnt: str, in_cycle_tp: str, in_stex_tp: str):
    """
    매물대집중요청
    메뉴 위치 : 국내주식 > 종목정보 > 매물대집중요청(ka10025)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_prps_cnctr_rt (str(3)): 매물집중비율(필수) 0~100 입력
      in_cur_prc_entry (str(1)): 현재가진입(필수) 0:현재가 매물대 진입 포함안함, 1:현재가 매물대 진입포함
      in_prpscnt (str(2)): 매물대수(필수) 숫자입력
      in_cycle_tp (str(2)): 주기구분(필수) 50:50일, 100:100일, 150:150일, 200:200일, 250:250일, 300:300일
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_prps_cnctr (list): 매물대집중
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - now_trde_qty (str(20)): 현재거래량
        - pric_strt (str(20)): 가격대시작
        - pric_end (str(20)): 가격대끝
        - prps_qty (str(20)): 매물량
        - prps_rt (str(20)): 매물비
    
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
      'api-id': 'ka10025',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'prps_cnctr_rt': in_prps_cnctr_rt,
      'cur_prc_entry': in_cur_prc_entry,
      'prpscnt': in_prpscnt,
      'cycle_tp': in_cycle_tp,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_prps_cnctr'] = out_data['prps_cnctr']
    
    return return_data

  def get_ka10026(self, in_cont_yn: str, in_next_key: str, in_pertp: str, in_stex_tp: str):
    """
    고저PER요청
    메뉴 위치 : 국내주식 > 종목정보 > 고저PER요청(ka10026)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_pertp (str(1)): PER구분(필수) 1:저PBR, 2:고PBR, 3:저PER, 4:고PER, 5:저ROE, 6:고ROE
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_high_low_per (list): 고저PER
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - per (str(20)): PER
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - now_trde_qty (str(20)): 현재거래량
        - sel_bid (str(20)): 매도호가
    
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
      'api-id': 'ka10026',
    }
    params = {
      'pertp': in_pertp,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_high_low_per'] = out_data['high_low_per']
    
    return return_data

  def get_ka10028(self, in_cont_yn: str, in_next_key: str, in_sort_tp: str, in_trde_qty_cnd: str, in_mrkt_tp: str, in_updown_incls: str, in_stk_cnd: str, in_crd_cnd: str, in_trde_prica_cnd: str, in_flu_cnd: str, in_stex_tp: str):
    """
    시가대비등락률요청
    메뉴 위치 : 국내주식 > 종목정보 > 시가대비등락률요청(ka10028)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_sort_tp (str(1)): 정렬구분(필수) 1:시가, 2:고가, 3:저가, 4:기준가
      in_trde_qty_cnd (str(4)): 거래량조건(필수) 0000:전체조회, 0010:만주이상, 0050:5만주이상, 0100:10만주이상, 0500:50만주이상, 1000:백만주이상
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_updown_incls (str(1)): 상하한포함(필수) 0:불 포함, 1:포함
      in_stk_cnd (str(2)): 종목조건(필수) 0:전체조회, 1:관리종목제외, 4:우선주+관리주제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기
      in_crd_cnd (str(1)): 신용조건(필수) 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체
      in_trde_prica_cnd (str(4)): 거래대금조건(필수) 0:전체조회, 3:3천만원이상, 5:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상
      in_flu_cnd (str(1)): 등락조건(필수) 1:상위, 2:하위
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_open_pric_pre_flu_rt (list): 시가대비등락률
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - open_pric_pre (str(20)): 시가대비
        - now_trde_qty (str(20)): 현재거래량
        - cntr_str (str(20)): 체결강도
    
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
      'api-id': 'ka10028',
    }
    params = {
      'sort_tp': in_sort_tp,
      'trde_qty_cnd': in_trde_qty_cnd,
      'mrkt_tp': in_mrkt_tp,
      'updown_incls': in_updown_incls,
      'stk_cnd': in_stk_cnd,
      'crd_cnd': in_crd_cnd,
      'trde_prica_cnd': in_trde_prica_cnd,
      'flu_cnd': in_flu_cnd,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_open_pric_pre_flu_rt'] = out_data['open_pric_pre_flu_rt']
    
    return return_data

  def get_ka10043(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_strt_dt: str, in_end_dt: str, in_qry_dt_tp: str, in_pot_tp: str, in_dt: str, in_sort_base: str, in_mmcm_cd: str, in_stex_tp: str):
    """
    거래원매물대분석요청
    메뉴 위치 : 국내주식 > 종목정보 > 거래원매물대분석요청(ka10043)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD
      in_end_dt (str(8)): 종료일자(필수) YYYYMMDD
      in_qry_dt_tp (str(1)): 조회기간구분(필수) 0:기간으로 조회, 1:시작일자, 종료일자로 조회
      in_pot_tp (str(1)): 시점구분(필수) 0:당일, 1:전일
      in_dt (str(4)): 기간(필수) 5:5일, 10:10일, 20:20일, 40:40일, 60:60일, 120:120일
      in_sort_base (str(1)): 정렬기준(필수) 1:종가순, 2:날짜순
      in_mmcm_cd (str(3)): 회원사코드(필수) 회원사 코드는 ka10102 조회
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_trde_ori_prps_anly (list): 거래원매물대분석
        - dt (str(20)): 일자
        - close_pric (str(20)): 종가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - sel_qty (str(20)): 매도량
        - buy_qty (str(20)): 매수량
        - netprps_qty (str(20)): 순매수수량
        - trde_qty_sum (str(20)): 거래량합
        - trde_wght (str(20)): 거래비중
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10043',
    }
    params = {
      'stk_cd': in_stk_cd,
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'qry_dt_tp': in_qry_dt_tp,
      'pot_tp': in_pot_tp,
      'dt': in_dt,
      'sort_base': in_sort_base,
      'mmcm_cd': in_mmcm_cd,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_trde_ori_prps_anly'] = out_data['trde_ori_prps_anly']
    
    return return_data

  def get_ka10052(self, in_cont_yn: str, in_next_key: str, in_mmcm_cd: str, in_stk_cd: str, in_mrkt_tp: str, in_qty_tp: str, in_pric_tp: str, in_stex_tp: str):
    """
    거래원순간거래량요청
    메뉴 위치 : 국내주식 > 종목정보 > 거래원순간거래량요청(ka10052)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mmcm_cd (str(3)): 회원사코드(필수) 회원사 코드는 ka10102 조회
      in_stk_cd (str(20)): 종목코드 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_mrkt_tp (str(1)): 시장구분(필수) 0:전체, 1:코스피, 2:코스닥, 3:종목
      in_qty_tp (str(3)): 수량구분(필수) 0:전체, 1:1000주, 2:2000주, 3:, 5:, 10:10000주, 30: 30000주, 50: 50000주, 100: 100000주
      in_pric_tp (str(1)): 가격구분(필수) 0:전체, 1:1천원 미만, 8:1천원 이상, 2:1천원 ~ 2천원, 3:2천원 ~ 5천원, 4:5천원 ~ 1만원, 5:1만원 이상
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_trde_ori_mont_trde_qty (list): 거래원순간거래량
        - tm (str(20)): 시간
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(20)): 종목명
        - trde_ori_nm (str(20)): 거래원명
        - tp (str(20)): 구분
        - mont_trde_qty (str(20)): 순간거래량
        - acc_netprps (str(20)): 누적순매수
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
    
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
      'api-id': 'ka10052',
    }
    params = {
      'mmcm_cd': in_mmcm_cd,
      'stk_cd': in_stk_cd,
      'mrkt_tp': in_mrkt_tp,
      'qty_tp': in_qty_tp,
      'pric_tp': in_pric_tp,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_trde_ori_mont_trde_qty'] = out_data['trde_ori_mont_trde_qty']
    
    return return_data

  def get_ka10054(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_bf_mkrt_tp: str, in_stk_cd: str, in_motn_tp: str, in_skip_stk: str, in_trde_qty_tp: str, in_min_trde_qty: str, in_max_trde_qty: str, in_trde_prica_tp: str, in_min_trde_prica: str, in_max_trde_prica: str, in_motn_drc: str, in_stex_tp: str):
    """
    변동성완화장치발동종목요청
    메뉴 위치 : 국내주식 > 종목정보 > 변동성완화장치발동종목요청(ka10054)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001: 코스피, 101:코스닥
      in_bf_mkrt_tp (str(1)): 장전구분(필수) 0:전체, 1:정규시장,2:시간외단일가
      in_stk_cd (str(20)): 종목코드 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)  공백입력시 시장구분으로 설정한 전체종목조회
      in_motn_tp (str(1)): 발동구분(필수) 0:전체, 1:정적VI, 2:동적VI, 3:동적VI + 정적VI
      in_skip_stk (str(9)): 제외종목(필수) 전종목포함 조회시 9개 0으로 설정(000000000),전종목제외 조회시 9개 1으로 설정(111111111),9개 종목조회여부를 조회포함(0), 조회제외(1)로 설정하며 종목순서는 우선주,관리종목,투자경고/위험,투자주의,환기종목,단기과열종목,증거금100%,ETF,ETN가 됨.우선주만 조회시"011111111"", 관리종목만 조회시 ""101111111"" 설정"
      in_trde_qty_tp (str(1)): 거래량구분(필수) 0:사용안함, 1:사용
      in_min_trde_qty (str(12)): 최소거래량(필수) 0 주 이상, 거래량구분이 1일때만 입력(공백허용)
      in_max_trde_qty (str(12)): 최대거래량(필수) 100000000 주 이하, 거래량구분이 1일때만 입력(공백허용)
      in_trde_prica_tp (str(1)): 거래대금구분(필수) 0:사용안함, 1:사용
      in_min_trde_prica (str(10)): 최소거래대금(필수) 0 백만원 이상, 거래대금구분 1일때만 입력(공백허용)
      in_max_trde_prica (str(10)): 최대거래대금(필수) 100000000 백만원 이하, 거래대금구분 1일때만 입력(공백허용)
      in_motn_drc (str(1)): 발동방향(필수) 0:전체, 1:상승, 2:하락
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_motn_stk (list): 발동종목
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - acc_trde_qty (str(20)): 누적거래량
        - motn_pric (str(20)): 발동가격
        - dynm_dispty_rt (str(20)): 동적괴리율
        - trde_cntr_proc_time (str(20)): 매매체결처리시각
        - virelis_time (str(20)): VI해제시각
        - viaplc_tp (str(20)): VI적용구분
        - dynm_stdpc (str(20)): 동적기준가격
        - static_stdpc (str(20)): 정적기준가격
        - static_dispty_rt (str(20)): 정적괴리율
        - open_pric_pre_flu_rt (str(20)): 시가대비등락률
        - vimotn_cnt (str(20)): VI발동횟수
        - stex_tp (str(20)): 거래소구분
    
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
      'api-id': 'ka10054',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'bf_mkrt_tp': in_bf_mkrt_tp,
      'stk_cd': in_stk_cd,
      'motn_tp': in_motn_tp,
      'skip_stk': in_skip_stk,
      'trde_qty_tp': in_trde_qty_tp,
      'min_trde_qty': in_min_trde_qty,
      'max_trde_qty': in_max_trde_qty,
      'trde_prica_tp': in_trde_prica_tp,
      'min_trde_prica': in_min_trde_prica,
      'max_trde_prica': in_max_trde_prica,
      'motn_drc': in_motn_drc,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_motn_stk'] = out_data['motn_stk']
    
    return return_data

  def get_ka10055(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_tdy_pred: str):
    """
    당일전일체결량요청
    메뉴 위치 : 국내주식 > 종목정보 > 당일전일체결량요청(ka10055)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_tdy_pred (str(1)): 당일전일(필수) 1:당일, 2:전일
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tdy_pred_cntr_qty (list): 당일전일체결량
        - cntr_tm (str(20)): 체결시간
        - cntr_pric (str(20)): 체결가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - cntr_qty (str(20)): 체결량
        - acc_trde_qty (str(20)): 누적거래량
        - acc_trde_prica (str(20)): 누적거래대금
    
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
      'api-id': 'ka10055',
    }
    params = {
      'stk_cd': in_stk_cd,
      'tdy_pred': in_tdy_pred,
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
    
    return_data['out_tdy_pred_cntr_qty'] = out_data['tdy_pred_cntr_qty']
    
    return return_data

  def get_ka10058(self, in_cont_yn: str, in_next_key: str, in_strt_dt: str, in_end_dt: str, in_trde_tp: str, in_mrkt_tp: str, in_invsr_tp: str, in_stex_tp: str):
    """
    투자자별일별매매종목요청
    메뉴 위치 : 국내주식 > 종목정보 > 투자자별일별매매종목요청(ka10058)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD
      in_end_dt (str(8)): 종료일자(필수) YYYYMMDD
      in_trde_tp (str(1)): 매매구분(필수) 순매도:1, 순매수:2
      in_mrkt_tp (str(3)): 시장구분(필수) 001:코스피, 101:코스닥
      in_invsr_tp (str(4)): 투자자구분(필수) 8000:개인, 9000:외국인, 1000:금융투자, 3000:투신, 5000:기타금융, 4000:은행, 2000:보험, 6000:연기금, 7000:국가, 7100:기타법인, 9999:기관계
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_invsr_daly_trde_stk (list): 투자자별일별매매종목
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - netslmt_qty (str(20)): 순매도수량
        - netslmt_amt (str(20)): 순매도금액
        - prsm_avg_pric (str(20)): 추정평균가
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - avg_pric_pre (str(20)): 평균가대비
        - pre_rt (str(20)): 대비율
        - dt_trde_qty (str(20)): 기간거래량
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10058',
    }
    params = {
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'trde_tp': in_trde_tp,
      'mrkt_tp': in_mrkt_tp,
      'invsr_tp': in_invsr_tp,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_invsr_daly_trde_stk'] = out_data['invsr_daly_trde_stk']
    
    return return_data

  def get_ka10059(self, in_cont_yn: str, in_next_key: str, in_dt: str, in_stk_cd: str, in_amt_qty_tp: str, in_trde_tp: str, in_unit_tp: str):
    """
    종목별투자자기관별요청
    메뉴 위치 : 국내주식 > 종목정보 > 종목별투자자기관별요청(ka10059)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dt (str(8)): 일자(필수) YYYYMMDD
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1:금액, 2:수량
      in_trde_tp (str(1)): 매매구분(필수) 0:순매수, 1:매수, 2:매도
      in_unit_tp (str(4)): 단위구분(필수) 1000:천주, 1:단주
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_invsr_orgn (list): 종목별투자자기관별
        - dt (str(20)): 일자
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율. 우측 2자리 소수점자리수
        - acc_trde_qty (str(20)): 누적거래량
        - acc_trde_prica (str(20)): 누적거래대금
        - ind_invsr (str(20)): 개인투자자
        - frgnr_invsr (str(20)): 외국인투자자
        - orgn (str(20)): 기관계
        - fnnc_invt (str(20)): 금융투자
        - insrnc (str(20)): 보험
        - invtrt (str(20)): 투신
        - etc_fnnc (str(20)): 기타금융
        - bank (str(20)): 은행
        - penfnd_etc (str(20)): 연기금등
        - samo_fund (str(20)): 사모펀드
        - natn (str(20)): 국가
        - etc_corp (str(20)): 기타법인
        - natfor (str(20)): 내외국인
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10059',
    }
    params = {
      'dt': in_dt,
      'stk_cd': in_stk_cd,
      'amt_qty_tp': in_amt_qty_tp,
      'trde_tp': in_trde_tp,
      'unit_tp': in_unit_tp,
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
    
    return_data['out_stk_invsr_orgn'] = out_data['stk_invsr_orgn']
    
    return return_data

  def get_ka10061(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_strt_dt: str, in_end_dt: str, in_amt_qty_tp: str, in_trde_tp: str, in_unit_tp: str):
    """
    종목별투자자기관별합계요청
    메뉴 위치 : 국내주식 > 종목정보 > 종목별투자자기관별합계요청(ka10061)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD
      in_end_dt (str(8)): 종료일자(필수) YYYYMMDD
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1:금액, 2:수량
      in_trde_tp (str(1)): 매매구분(필수) 0:순매수
      in_unit_tp (str(4)): 단위구분(필수) 1000:천주, 1:단주
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_invsr_orgn_tot (list): 종목별투자자기관별합계
        - ind_invsr (str(20)): 개인투자자
        - frgnr_invsr (str(20)): 외국인투자자
        - orgn (str(20)): 기관계
        - fnnc_invt (str(20)): 금융투자
        - insrnc (str(20)): 보험
        - invtrt (str(20)): 투신
        - etc_fnnc (str(20)): 기타금융
        - bank (str(20)): 은행
        - penfnd_etc (str(20)): 연기금등
        - samo_fund (str(20)): 사모펀드
        - natn (str(20)): 국가
        - etc_corp (str(20)): 기타법인
        - natfor (str(20)): 내외국인
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10061',
    }
    params = {
      'stk_cd': in_stk_cd,
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'amt_qty_tp': in_amt_qty_tp,
      'trde_tp': in_trde_tp,
      'unit_tp': in_unit_tp,
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
    
    return_data['out_stk_invsr_orgn_tot'] = out_data['stk_invsr_orgn_tot']
    
    return return_data

  def get_ka10084(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_tdy_pred: str, in_tic_min: str, in_tm: str):
    """
    당일전일체결요청
    메뉴 위치 : 국내주식 > 종목정보 > 당일전일체결요청(ka10084)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_tdy_pred (str(1)): 당일전일(필수) 당일 : 1, 전일 : 2
      in_tic_min (str(1)): 틱분(필수) 0:틱, 1:분
      in_tm (str(4)): 시간 조회시간 4자리, 오전 9시일 경우 0900, 오후 2시 30분일 경우 1430
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tdy_pred_cntr (list): 당일전일체결
        - tm (str(20)): 시간
        - cur_prc (str(20)): 현재가
        - pred_pre (str(20)): 전일대비
        - pre_rt (str(20)): 대비율
        - pri_sel_bid_unit (str(20)): 우선매도호가단위
        - pri_buy_bid_unit (str(20)): 우선매수호가단위
        - cntr_trde_qty (str(20)): 체결거래량
        - sign (str(20)): 전일대비기호
        - acc_trde_qty (str(20)): 누적거래량
        - acc_trde_prica (str(20)): 누적거래대금
        - cntr_str (str(20)): 체결강도
        - stex_tp (str(20)): 거래소구분. KRX , NXT , 통합
    
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
      'api-id': 'ka10084',
    }
    params = {
      'stk_cd': in_stk_cd,
      'tdy_pred': in_tdy_pred,
      'tic_min': in_tic_min,
      'tm': in_tm,
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
    
    return_data['out_tdy_pred_cntr'] = out_data['tdy_pred_cntr']
    
    return return_data

  def get_ka10095(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    관심종목정보요청
    메뉴 위치 : 국내주식 > 종목정보 > 관심종목정보요청(ka10095)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL) 여러개의 종목코드 입력시 | 로 구분
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_atn_stk_infr (list): 관심종목정보
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - base_pric (str(20)): 기준가
        - pred_pre (str(20)): 전일대비
        - pred_pre_sig (str(20)): 전일대비기호
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - trde_prica (str(20)): 거래대금
        - cntr_qty (str(20)): 체결량
        - cntr_str (str(20)): 체결강도
        - pred_trde_qty_pre (str(20)): 전일거래량대비
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
        - sel_1th_bid (str(20)): 매도1차호가
        - sel_2th_bid (str(20)): 매도2차호가
        - sel_3th_bid (str(20)): 매도3차호가
        - sel_4th_bid (str(20)): 매도4차호가
        - sel_5th_bid (str(20)): 매도5차호가
        - buy_1th_bid (str(20)): 매수1차호가
        - buy_2th_bid (str(20)): 매수2차호가
        - buy_3th_bid (str(20)): 매수3차호가
        - buy_4th_bid (str(20)): 매수4차호가
        - buy_5th_bid (str(20)): 매수5차호가
        - upl_pric (str(20)): 상한가
        - lst_pric (str(20)): 하한가
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - close_pric (str(20)): 종가
        - cntr_tm (str(20)): 체결시간
        - exp_cntr_pric (str(20)): 예상체결가
        - exp_cntr_qty (str(20)): 예상체결량
        - cap (str(20)): 자본금
        - fav (str(20)): 액면가
        - mac (str(20)): 시가총액
        - stkcnt (str(20)): 주식수
        - bid_tm (str(20)): 호가시간
        - dt (str(20)): 일자
        - pri_sel_req (str(20)): 우선매도잔량
        - pri_buy_req (str(20)): 우선매수잔량
        - pri_sel_cnt (str(20)): 우선매도건수
        - pri_buy_cnt (str(20)): 우선매수건수
        - tot_sel_req (str(20)): 총매도잔량
        - tot_buy_req (str(20)): 총매수잔량
        - tot_sel_cnt (str(20)): 총매도건수
        - tot_buy_cnt (str(20)): 총매수건수
        - prty (str(20)): 패리티
        - gear (str(20)): 기어링
        - pl_qutr (str(20)): 손익분기
        - cap_support (str(20)): 자본지지
        - elwexec_pric (str(20)): ELW행사가
        - cnvt_rt (str(20)): 전환비율
        - elwexpr_dt (str(20)): ELW만기일
        - cntr_engg (str(20)): 미결제약정
        - cntr_pred_pre (str(20)): 미결제전일대비
        - theory_pric (str(20)): 이론가
        - innr_vltl (str(20)): 내재변동성
        - delta (str(20)): 델타
        - gam (str(20)): 감마
        - theta (str(20)): 쎄타
        - vega (str(20)): 베가
        - law (str(20)): 로
    
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
      'api-id': 'ka10095',
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
    
    return_data['out_atn_stk_infr'] = out_data['atn_stk_infr']
    
    return return_data

  def get_ka10099(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str):
    """
    종목정보 리스트
    메뉴 위치 : 국내주식 > 종목정보 > 종목정보 리스트(ka10099)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(2)): 시장구분(필수) 0:코스피,10:코스닥,3:ELW,8:ETF,30:K-OTC,50:코넥스,5:신주인수권,4:뮤추얼펀드,6:리츠,9:하이일드
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_list (list): 종목리스트
        - code (str(20)): 종목코드. 단축코드
        - name (str(40)): 종목명
        - listCount (str(20)): 상장주식수
        - auditInfo (str(20)): 감리구분
        - regDay (str(20)): 상장일
        - lastPrice (str(20)): 전일종가
        - state (str(20)): 종목상태
        - marketCode (str(20)): 시장구분코드
        - marketName (str(20)): 시장명
        - upName (str(20)): 업종명
        - upSizeName (str(20)): 회사크기분류
        - companyClassName (str(20)): 회사분류. 코스닥만 존재함
        - orderWarning (str(20)): 투자유의종목여부. 0: 해당없음, 2: 정리매매, 3: 단기과열, 4: 투자위험, 5: 투자경과, 1: ETF투자주의요망(ETF인 경우만 전달
        - nxtEnable (str(20)): NXT가능여부. Y: 가능
    
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
      'api-id': 'ka10099',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
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
    
    return_data['out_list'] = out_data['list']
    
    return return_data

  def get_ka10100(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    종목정보 조회
    메뉴 위치 : 국내주식 > 종목정보 > 종목정보 조회(ka10100)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_code (str): 종목코드. 단축코드
      out_name (str(40)): 종목명
      out_listCount (str): 상장주식수
      out_auditInfo (str): 감리구분
      out_regDay (str): 상장일
      out_lastPrice (str): 전일종가
      out_state (str): 종목상태
      out_marketCode (str): 시장구분코드
      out_marketName (str): 시장명
      out_upName (str): 업종명
      out_upSizeName (str): 회사크기분류
      out_companyClassName (str): 회사분류. 코스닥만 존재함
      out_orderWarning (str): 투자유의종목여부. 0: 해당없음, 2: 정리매매, 3: 단기과열, 4: 투자위험, 5: 투자경과, 1: ETF투자주의요망(ETF인 경우만 전달
      out_nxtEnable (str): NXT가능여부. Y: 가능
    
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
      'api-id': 'ka10100',
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
    
    return_data['out_code'] = out_data['code']
    return_data['out_name'] = out_data['name']
    return_data['out_listCount'] = out_data['listCount']
    return_data['out_auditInfo'] = out_data['auditInfo']
    return_data['out_regDay'] = out_data['regDay']
    return_data['out_lastPrice'] = out_data['lastPrice']
    return_data['out_state'] = out_data['state']
    return_data['out_marketCode'] = out_data['marketCode']
    return_data['out_marketName'] = out_data['marketName']
    return_data['out_upName'] = out_data['upName']
    return_data['out_upSizeName'] = out_data['upSizeName']
    return_data['out_companyClassName'] = out_data['companyClassName']
    return_data['out_orderWarning'] = out_data['orderWarning']
    return_data['out_nxtEnable'] = out_data['nxtEnable']
    
    return return_data

  def get_ka10101(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str):
    """
    업종코드 리스트
    메뉴 위치 : 국내주식 > 종목정보 > 업종코드 리스트(ka10101)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(1)): 시장구분(필수) 0:코스피(거래소),1:코스닥,2:KOSPI200,4:KOSPI100,7:KRX100(통합지수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_list (list): 업종코드리스트
        - marketCode (list): 시장구분코드
        - code (str): 코드
        - name (str): 업종명
        - group (str): 그룹
    
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
      'api-id': 'ka10101',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
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
    
    return_data['out_list'] = out_data['list']
    
    return return_data

  def get_ka10102(self, in_cont_yn: str, in_next_key: str):
    """
    회원사 리스트
    메뉴 위치 : 국내주식 > 종목정보 > 회원사 리스트(ka10102)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_list (list): 회원사코드리스트
        - code (str): 코드
        - name (str): 업종명
        - gb (str): 구분
    
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
      'api-id': 'ka10102',
    }
    params = {
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
    
    return_data['out_list'] = out_data['list']
    
    return return_data

  def get_ka90003(self, in_cont_yn: str, in_next_key: str, in_trde_upper_tp: str, in_amt_qty_tp: str, in_mrkt_tp: str, in_stex_tp: str):
    """
    프로그램순매수상위50요청
    메뉴 위치 : 국내주식 > 종목정보 > 프로그램순매수상위50요청(ka90003)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_trde_upper_tp (str(1)): 매매상위구분(필수) 1:순매도상위, 2:순매수상위
      in_amt_qty_tp (str(2)): 금액수량구분(필수) 1:금액, 2:수량
      in_mrkt_tp (str(10)): 시장구분(필수) P00101:코스피, P10102:코스닥
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_prm_netprps_upper_50 (list): 프로그램순매수상위50
        - rank (str(20)): 순위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - flu_sig (str(20)): 등락기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - acc_trde_qty (str(20)): 누적거래량
        - prm_sell_amt (str(20)): 프로그램매도금액
        - prm_buy_amt (str(20)): 프로그램매수금액
        - prm_netprps_amt (str(20)): 프로그램순매수금액
    
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
      'api-id': 'ka90003',
    }
    params = {
      'trde_upper_tp': in_trde_upper_tp,
      'amt_qty_tp': in_amt_qty_tp,
      'mrkt_tp': in_mrkt_tp,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_prm_netprps_upper_50'] = out_data['prm_netprps_upper_50']
    
    return return_data

  def get_ka90004(self, in_cont_yn: str, in_next_key: str, in_dt: str, in_mrkt_tp: str, in_stex_tp: str):
    """
    종목별프로그램매매현황요청
    메뉴 위치 : 국내주식 > 종목정보 > 종목별프로그램매매현황요청(ka90004)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dt (str(8)): 일자(필수) YYYYMMDD
      in_mrkt_tp (str(10)): 시장구분(필수) P00101:코스피, P10102:코스닥
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tot_1 (str(20)): 매수체결수량합계
      out_tot_2 (str(20)): 매수체결금액합계
      out_tot_3 (str(20)): 매도체결수량합계
      out_tot_4 (str(20)): 매도체결금액합계
      out_tot_5 (str(20)): 순매수대금합계
      out_tot_6 (str(20)): 합계6
      out_stk_prm_trde_prst (list): 종목별프로그램매매현황
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - flu_sig (str(20)): 등락기호
        - pred_pre (str(20)): 전일대비
        - buy_cntr_qty (str(20)): 매수체결수량
        - buy_cntr_amt (str(20)): 매수체결금액
        - sel_cntr_qty (str(20)): 매도체결수량
        - sel_cntr_amt (str(20)): 매도체결금액
        - netprps_prica (str(20)): 순매수대금
        - all_trde_rt (str(20)): 전체거래비율
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka90004',
    }
    params = {
      'dt': in_dt,
      'mrkt_tp': in_mrkt_tp,
      'stex_tp': in_stex_tp,
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
    
    return_data['out_tot_1'] = out_data['tot_1']
    return_data['out_tot_2'] = out_data['tot_2']
    return_data['out_tot_3'] = out_data['tot_3']
    return_data['out_tot_4'] = out_data['tot_4']
    return_data['out_tot_5'] = out_data['tot_5']
    return_data['out_tot_6'] = out_data['tot_6']
    return_data['out_stk_prm_trde_prst'] = out_data['stk_prm_trde_prst']
    
    return return_data

  def get_kt20016(self, in_cont_yn: str, in_next_key: str, in_crd_stk_grde_tp: str, in_mrkt_deal_tp: str, in_stk_cd: str):
    """
    신용융자 가능종목요청
    메뉴 위치 : 국내주식 > 종목정보 > 신용융자 가능종목요청(kt20016)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_crd_stk_grde_tp (str(1)): 신용종목등급구분 %:전체, A:A군, B:B군, C:C군, D:D군, E:E군
      in_mrkt_deal_tp (str(1)): 시장거래구분(필수) %:전체, 1:코스피, 0:코스닥
      in_stk_cd (str(12)): 종목코드
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_crd_loan_able (str(40)): 신용융자가능여부
      out_crd_loan_pos_stk (list): 신용융자가능종목
        - stk_cd (str(12)): 종목코드
        - stk_nm (str(40)): 종목명
        - crd_assr_rt (str(4)): 신용보증금율
        - repl_pric (str(12)): 대용가
        - pred_close_pric (str(12)): 전일종가
        - crd_limit_over_yn (str(1)): 신용한도초과여부
        - crd_limit_over_txt (str(40)): 신용한도초과. N:공란,Y:회사한도 초과
    
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
      'api-id': 'kt20016',
    }
    params = {
      'crd_stk_grde_tp': in_crd_stk_grde_tp,
      'mrkt_deal_tp': in_mrkt_deal_tp,
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
    
    return_data['out_crd_loan_able'] = out_data['crd_loan_able']
    return_data['out_crd_loan_pos_stk'] = out_data['crd_loan_pos_stk']
    
    return return_data

  def get_kt20017(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    신용융자 가능문의
    메뉴 위치 : 국내주식 > 종목정보 > 신용융자 가능문의(kt20017)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(12)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_crd_alow_yn (str(40)): 신용가능여부
    
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
      'api-id': 'kt20017',
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
    
    return_data['out_crd_alow_yn'] = out_data['crd_alow_yn']
    
    return return_data

  def get_ka01690(self, in_cont_yn: str, in_next_key: str, in_qry_dt: str):
    """
    일별잔고수익률
    메뉴 위치 : 국내주식 > 계좌 > 일별잔고수익률(ka01690)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_qry_dt (str(8)): 조회일자(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_dt (str(20)): 일자
      out_tot_buy_amt (str(20)): 총 매입가
      out_tot_evlt_amt (str(20)): 총 평가금액
      out_tot_evltv_prft (str(20)): 총 평가손익
      out_tot_prft_rt (str(20)): 수익률
      out_dbst_bal (str(20)): 예수금
      out_day_stk_asst (str(20)): 추정자산
      out_buy_wght (str(20)): 현금비중
      out_day_bal_rt (list): 일별잔고수익률
        - cur_prc (str(20)): 현재가
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(20)): 종목명
        - rmnd_qty (str(20)): 보유 수량
        - buy_uv (str(20)): 매입 단가
        - buy_wght (str(20)): 매수비중
        - evltv_prft (str(20)): 평가손익
        - prft_rt (str(20)): 수익률
        - evlt_amt (str(20)): 평가금액
        - evlt_wght (str(20)): 평가비중
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_qry_dt or in_qry_dt == '':
      in_qry_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka01690',
    }
    params = {
      'qry_dt': in_qry_dt,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_dt'] = out_data['dt']
    return_data['out_tot_buy_amt'] = out_data['tot_buy_amt']
    return_data['out_tot_evlt_amt'] = out_data['tot_evlt_amt']
    return_data['out_tot_evltv_prft'] = out_data['tot_evltv_prft']
    return_data['out_tot_prft_rt'] = out_data['tot_prft_rt']
    return_data['out_dbst_bal'] = out_data['dbst_bal']
    return_data['out_day_stk_asst'] = out_data['day_stk_asst']
    return_data['out_buy_wght'] = out_data['buy_wght']
    return_data['out_day_bal_rt'] = out_data['day_bal_rt']
    
    return return_data

  def get_ka10072(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_strt_dt: str):
    """
    일자별종목별실현손익요청_일자
    메뉴 위치 : 국내주식 > 계좌 > 일자별종목별실현손익요청_일자(ka10072)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_dt_stk_div_rlzt_pl (list): 일자별종목별실현손익
        - stk_nm (str(40)): 종목명
        - cntr_qty (str(20)): 체결량
        - buy_uv (str(20)): 매입단가
        - cntr_pric (str(20)): 체결가
        - tdy_sel_pl (str(20)): 당일매도손익
        - pl_rt (str(20)): 손익율
        - stk_cd (str(20)): 종목코드
        - tdy_trde_cmsn (str(20)): 당일매매수수료
        - tdy_trde_tax (str(20)): 당일매매세금
        - wthd_alowa (str(20)): 인출가능금액
        - loan_dt (str(20)): 대출일
        - crd_tp (str(20)): 신용구분
        - stk_cd_1 (str(20)): 종목코드1
        - tdy_sel_pl_1 (str(20)): 당일매도손익1
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10072',
    }
    params = {
      'stk_cd': in_stk_cd,
      'strt_dt': in_strt_dt,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_dt_stk_div_rlzt_pl'] = out_data['dt_stk_div_rlzt_pl']
    
    return return_data

  def get_ka10073(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_strt_dt: str, in_end_dt: str):
    """
    일자별종목별실현손익요청_기간
    메뉴 위치 : 국내주식 > 계좌 > 일자별종목별실현손익요청_기간(ka10073)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD
      in_end_dt (str(8)): 종료일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_dt_stk_rlzt_pl (list): 일자별종목별실현손익
        - dt (str(20)): 일자
        - tdy_htssel_cmsn (str(20)): 당일hts매도수수료
        - stk_nm (str(40)): 종목명
        - cntr_qty (str(20)): 체결량
        - buy_uv (str(20)): 매입단가
        - cntr_pric (str(20)): 체결가
        - tdy_sel_pl (str(20)): 당일매도손익
        - pl_rt (str(20)): 손익율
        - stk_cd (str(20)): 종목코드
        - tdy_trde_cmsn (str(20)): 당일매매수수료
        - tdy_trde_tax (str(20)): 당일매매세금
        - wthd_alowa (str(20)): 인출가능금액
        - loan_dt (str(20)): 대출일
        - crd_tp (str(20)): 신용구분
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10073',
    }
    params = {
      'stk_cd': in_stk_cd,
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_dt_stk_rlzt_pl'] = out_data['dt_stk_rlzt_pl']
    
    return return_data

  def get_ka10074(self, in_cont_yn: str, in_next_key: str, in_strt_dt: str, in_end_dt: str):
    """
    일자별실현손익요청
    메뉴 위치 : 국내주식 > 계좌 > 일자별실현손익요청(ka10074)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_strt_dt (str(8)): 시작일자(필수)
      in_end_dt (str(8)): 종료일자(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tot_buy_amt (str): 총매수금액
      out_tot_sell_amt (str): 총매도금액
      out_rlzt_pl (str): 실현손익
      out_trde_cmsn (str): 매매수수료
      out_trde_tax (str): 매매세금
      out_dt_rlzt_pl (list): 일자별실현손익
        - dt (str(20)): 일자
        - buy_amt (str(20)): 매수금액
        - sell_amt (str(20)): 매도금액
        - tdy_sel_pl (str(20)): 당일매도손익
        - tdy_trde_cmsn (str(20)): 당일매매수수료
        - tdy_trde_tax (str(20)): 당일매매세금
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10074',
    }
    params = {
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_tot_buy_amt'] = out_data['tot_buy_amt']
    return_data['out_tot_sell_amt'] = out_data['tot_sell_amt']
    return_data['out_rlzt_pl'] = out_data['rlzt_pl']
    return_data['out_trde_cmsn'] = out_data['trde_cmsn']
    return_data['out_trde_tax'] = out_data['trde_tax']
    return_data['out_dt_rlzt_pl'] = out_data['dt_rlzt_pl']
    
    return return_data

  def get_ka10075(self, in_cont_yn: str, in_next_key: str, in_all_stk_tp: str, in_trde_tp: str, in_stk_cd: str, in_stex_tp: str):
    """
    미체결요청
    메뉴 위치 : 국내주식 > 계좌 > 미체결요청(ka10075)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_all_stk_tp (str(1)): 전체종목구분(필수) 0:전체, 1:종목
      in_trde_tp (str(1)): 매매구분(필수) 0:전체, 1:매도, 2:매수
      in_stk_cd (str(6)): 종목코드
      in_stex_tp (str(1)): 거래소구분(필수) 0 : 통합, 1 : KRX, 2 : NXT
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_oso (list): 미체결
        - acnt_no (str(20)): 계좌번호
        - ord_no (str(20)): 주문번호
        - mang_empno (str(20)): 관리사번
        - stk_cd (str(20)): 종목코드
        - tsk_tp (str(20)): 업무구분
        - ord_stt (str(20)): 주문상태
        - stk_nm (str(40)): 종목명
        - ord_qty (str(20)): 주문수량
        - ord_pric (str(20)): 주문가격
        - oso_qty (str(20)): 미체결수량
        - cntr_tot_amt (str(20)): 체결누계금액
        - orig_ord_no (str(20)): 원주문번호
        - io_tp_nm (str(20)): 주문구분
        - trde_tp (str(20)): 매매구분
        - tm (str(20)): 시간
        - cntr_no (str(20)): 체결번호
        - cntr_pric (str(20)): 체결가
        - cntr_qty (str(20)): 체결량
        - cur_prc (str(20)): 현재가
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
        - unit_cntr_pric (str(20)): 단위체결가
        - unit_cntr_qty (str(20)): 단위체결량
        - tdy_trde_cmsn (str(20)): 당일매매수수료
        - tdy_trde_tax (str(20)): 당일매매세금
        - ind_invsr (str(20)): 개인투자자
        - stex_tp (str(20)): 거래소구분. 0 : 통합, 1 : KRX, 2 : NXT
        - stex_tp_txt (str(20)): 거래소구분텍스트. 통합,KRX,NXT
        - sor_yn (str(20)): SOR 여부값. Y,N
        - stop_pric (str(20)): 스톱가. 스톱지정가주문 스톱가
    
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
      'api-id': 'ka10075',
    }
    params = {
      'all_stk_tp': in_all_stk_tp,
      'trde_tp': in_trde_tp,
      'stk_cd': in_stk_cd,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_oso'] = out_data['oso']
    
    return return_data

  def get_ka10076(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_qry_tp: str, in_sell_tp: str, in_ord_no: str, in_stex_tp: str):
    """
    체결요청
    메뉴 위치 : 국내주식 > 계좌 > 체결요청(ka10076)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드
      in_qry_tp (str(1)): 조회구분(필수) 0:전체, 1:종목
      in_sell_tp (str(1)): 매도수구분(필수) 0:전체, 1:매도, 2:매수
      in_ord_no (str(10)): 주문번호 검색 기준 값으로 입력한 주문번호 보다 과거에 체결된 내역이 조회됩니다.
      in_stex_tp (str(1)): 거래소구분(필수) 0 : 통합, 1 : KRX, 2 : NXT
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_cntr (list): 체결
        - ord_no (str(20)): 주문번호
        - stk_nm (str(40)): 종목명
        - io_tp_nm (str(20)): 주문구분
        - ord_pric (str(20)): 주문가격
        - ord_qty (str(20)): 주문수량
        - cntr_pric (str(20)): 체결가
        - cntr_qty (str(20)): 체결량
        - oso_qty (str(20)): 미체결수량
        - tdy_trde_cmsn (str(20)): 당일매매수수료
        - tdy_trde_tax (str(20)): 당일매매세금
        - ord_stt (str(20)): 주문상태
        - trde_tp (str(20)): 매매구분
        - orig_ord_no (str(20)): 원주문번호
        - ord_tm (str(20)): 주문시간
        - stk_cd (str(20)): 종목코드
        - stex_tp (str(20)): 거래소구분. 0 : 통합, 1 : KRX, 2 : NXT
        - stex_tp_txt (str(20)): 거래소구분텍스트. 통합,KRX,NXT
        - sor_yn (str(20)): SOR 여부값. Y,N
        - stop_pric (str(20)): 스톱가. 스톱지정가주문 스톱가
    
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
      'api-id': 'ka10076',
    }
    params = {
      'stk_cd': in_stk_cd,
      'qry_tp': in_qry_tp,
      'sell_tp': in_sell_tp,
      'ord_no': in_ord_no,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_cntr'] = out_data['cntr']
    
    return return_data

  def get_ka10077(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    당일실현손익상세요청
    메뉴 위치 : 국내주식 > 계좌 > 당일실현손익상세요청(ka10077)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tdy_rlzt_pl (str): 당일실현손익
      out_tdy_rlzt_pl_dtl (list): 당일실현손익상세
        - stk_nm (str(40)): 종목명
        - cntr_qty (str(20)): 체결량
        - buy_uv (str(20)): 매입단가
        - cntr_pric (str(20)): 체결가
        - tdy_sel_pl (str(20)): 당일매도손익
        - pl_rt (str(20)): 손익율
        - tdy_trde_cmsn (str(20)): 당일매매수수료
        - tdy_trde_tax (str(20)): 당일매매세금
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
      'api-id': 'ka10077',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_tdy_rlzt_pl'] = out_data['tdy_rlzt_pl']
    return_data['out_tdy_rlzt_pl_dtl'] = out_data['tdy_rlzt_pl_dtl']
    
    return return_data

  def get_ka10085(self, in_cont_yn: str, in_next_key: str, in_stex_tp: str):
    """
    계좌수익률요청
    메뉴 위치 : 국내주식 > 계좌 > 계좌수익률요청(ka10085)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stex_tp (str(1)): 거래소구분(필수) 0 : 통합, 1 : KRX, 2 : NXT
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_acnt_prft_rt (list): 계좌수익률
        - dt (str(20)): 일자
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pur_pric (str(20)): 매입가
        - pur_amt (str(20)): 매입금액
        - rmnd_qty (str(20)): 보유수량
        - tdy_sel_pl (str(20)): 당일매도손익
        - tdy_trde_cmsn (str(20)): 당일매매수수료
        - tdy_trde_tax (str(20)): 당일매매세금
        - crd_tp (str(20)): 신용구분
        - loan_dt (str(20)): 대출일
        - setl_remn (str(20)): 결제잔고
        - clrn_alow_qty (str(20)): 청산가능수량
        - crd_amt (str(20)): 신용금액
        - crd_int (str(20)): 신용이자
        - expr_dt (str(20)): 만기일
    
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
      'api-id': 'ka10085',
    }
    params = {
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_acnt_prft_rt'] = out_data['acnt_prft_rt']
    
    return return_data

  def get_ka10088(self, in_cont_yn: str, in_next_key: str, in_ord_no: str):
    """
    미체결 분할주문 상세
    메뉴 위치 : 국내주식 > 계좌 > 미체결 분할주문 상세(ka10088)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_ord_no (str(20)): 주문번호(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_osop (list): 미체결분할주문리스트
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - ord_no (str(20)): 주문번호
        - ord_qty (str(20)): 주문수량
        - ord_pric (str(20)): 주문가격
        - osop_qty (str(20)): 미체결수량
        - io_tp_nm (str(20)): 주문구분
        - trde_tp (str(20)): 매매구분
        - sell_tp (str(20)): 매도/수 구분
        - cntr_qty (str(20)): 체결량
        - ord_stt (str(20)): 주문상태
        - cur_prc (str(20)): 현재가
        - stex_tp (str(20)): 거래소구분. 0 : 통합, 1 : KRX, 2 : NXT
        - stex_tp_txt (str(20)): 거래소구분텍스트. 통합,KRX,NXT
    
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
      'api-id': 'ka10088',
    }
    params = {
      'ord_no': in_ord_no,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_osop'] = out_data['osop']
    
    return return_data

  def get_ka10170(self, in_cont_yn: str, in_next_key: str, in_base_dt: str, in_ottks_tp: str, in_ch_crd_tp: str):
    """
    당일매매일지요청
    메뉴 위치 : 국내주식 > 계좌 > 당일매매일지요청(ka10170)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_base_dt (str(8)): 기준일자 YYYYMMDD(공백입력시 금일데이터,최근 2개월까지 제공)
      in_ottks_tp (str(1)): 단주구분(필수) 1:당일매수에 대한 당일매도,2:당일매도 전체
      in_ch_crd_tp (str(1)): 현금신용구분(필수) 0:전체, 1:현금매매만, 2:신용매매만
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tot_sell_amt (str): 총매도금액
      out_tot_buy_amt (str): 총매수금액
      out_tot_cmsn_tax (str): 총수수료_세금
      out_tot_exct_amt (str): 총정산금액
      out_tot_pl_amt (str): 총손익금액
      out_tot_prft_rt (str): 총수익률
      out_tdy_trde_diary (list): 당일매매일지
        - stk_nm (str(40)): 종목명
        - buy_avg_pric (str): 매수평균가
        - buy_qty (str): 매수수량
        - sel_avg_pric (str): 매도평균가
        - sell_qty (str): 매도수량
        - cmsn_alm_tax (str): 수수료_제세금
        - pl_amt (str): 손익금액
        - sell_amt (str): 매도금액
        - buy_amt (str): 매수금액
        - prft_rt (str): 수익률
        - stk_cd (str(6)): 종목코드
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10170',
    }
    params = {
      'base_dt': in_base_dt,
      'ottks_tp': in_ottks_tp,
      'ch_crd_tp': in_ch_crd_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_tot_sell_amt'] = out_data['tot_sell_amt']
    return_data['out_tot_buy_amt'] = out_data['tot_buy_amt']
    return_data['out_tot_cmsn_tax'] = out_data['tot_cmsn_tax']
    return_data['out_tot_exct_amt'] = out_data['tot_exct_amt']
    return_data['out_tot_pl_amt'] = out_data['tot_pl_amt']
    return_data['out_tot_prft_rt'] = out_data['tot_prft_rt']
    return_data['out_tdy_trde_diary'] = out_data['tdy_trde_diary']
    
    return return_data

  def get_kt00001(self, in_cont_yn: str, in_next_key: str, in_qry_tp: str):
    """
    예수금상세현황요청
    메뉴 위치 : 국내주식 > 계좌 > 예수금상세현황요청(kt00001)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_qry_tp (str(1)): 조회구분(필수) 3:추정조회, 2:일반조회
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_entr (str(15)): 예수금
      out_profa_ch (str(15)): 주식증거금현금
      out_bncr_profa_ch (str(15)): 수익증권증거금현금
      out_nxdy_bncr_sell_exct (str(15)): 익일수익증권매도정산대금
      out_fc_stk_krw_repl_set_amt (str(15)): 해외주식원화대용설정금
      out_crd_grnta_ch (str(15)): 신용보증금현금
      out_crd_grnt_ch (str(15)): 신용담보금현금
      out_add_grnt_ch (str(15)): 추가담보금현금
      out_etc_profa (str(15)): 기타증거금
      out_uncl_stk_amt (str(15)): 미수확보금
      out_shrts_prica (str(15)): 공매도대금
      out_crd_set_grnta (str(15)): 신용설정평가금
      out_chck_ina_amt (str(15)): 수표입금액
      out_etc_chck_ina_amt (str(15)): 기타수표입금액
      out_crd_grnt_ruse (str(15)): 신용담보재사용
      out_knx_asset_evltv (str(15)): 코넥스기본예탁금
      out_elwdpst_evlta (str(15)): ELW예탁평가금
      out_crd_ls_rght_frcs_amt (str(15)): 신용대주권리예정금액
      out_lvlh_join_amt (str(15)): 생계형가입금액
      out_lvlh_trns_alowa (str(15)): 생계형입금가능금액
      out_repl_amt (str(15)): 대용금평가금액(합계)
      out_remn_repl_evlta (str(15)): 잔고대용평가금액
      out_trst_remn_repl_evlta (str(15)): 위탁대용잔고평가금액
      out_bncr_remn_repl_evlta (str(15)): 수익증권대용평가금액
      out_profa_repl (str(15)): 위탁증거금대용
      out_crd_grnta_repl (str(15)): 신용보증금대용
      out_crd_grnt_repl (str(15)): 신용담보금대용
      out_add_grnt_repl (str(15)): 추가담보금대용
      out_rght_repl_amt (str(15)): 권리대용금
      out_pymn_alow_amt (str(15)): 출금가능금액
      out_wrap_pymn_alow_amt (str(15)): 랩출금가능금액
      out_ord_alow_amt (str(15)): 주문가능금액
      out_bncr_buy_alowa (str(15)): 수익증권매수가능금액
      out_20stk_ord_alow_amt (str(15)): 20%종목주문가능금액
      out_30stk_ord_alow_amt (str(15)): 30%종목주문가능금액
      out_40stk_ord_alow_amt (str(15)): 40%종목주문가능금액
      out_100stk_ord_alow_amt (str(15)): 100%종목주문가능금액
      out_ch_uncla (str(15)): 현금미수금
      out_ch_uncla_dlfe (str(15)): 현금미수연체료
      out_ch_uncla_tot (str(15)): 현금미수금합계
      out_crd_int_npay (str(15)): 신용이자미납
      out_int_npay_amt_dlfe (str(15)): 신용이자미납연체료
      out_int_npay_amt_tot (str(15)): 신용이자미납합계
      out_etc_loana (str(15)): 기타대여금
      out_etc_loana_dlfe (str(15)): 기타대여금연체료
      out_etc_loan_tot (str(15)): 기타대여금합계
      out_nrpy_loan (str(15)): 미상환융자금
      out_loan_sum (str(15)): 융자금합계
      out_ls_sum (str(15)): 대주금합계
      out_crd_grnt_rt (str(15)): 신용담보비율
      out_mdstrm_usfe (str(15)): 중도이용료
      out_min_ord_alow_yn (str(15)): 최소주문가능금액
      out_loan_remn_evlt_amt (str(15)): 대출총평가금액
      out_dpst_grntl_remn (str(15)): 예탁담보대출잔고
      out_sell_grntl_remn (str(15)): 매도담보대출잔고
      out_d1_entra (str(15)): d+1추정예수금
      out_d1_slby_exct_amt (str(15)): d+1매도매수정산금
      out_d1_buy_exct_amt (str(15)): d+1매수정산금
      out_d1_out_rep_mor (str(15)): d+1미수변제소요금
      out_d1_sel_exct_amt (str(15)): d+1매도정산금
      out_d1_pymn_alow_amt (str(15)): d+1출금가능금액
      out_d2_entra (str(15)): d+2추정예수금
      out_d2_slby_exct_amt (str(15)): d+2매도매수정산금
      out_d2_buy_exct_amt (str(15)): d+2매수정산금
      out_d2_out_rep_mor (str(15)): d+2미수변제소요금
      out_d2_sel_exct_amt (str(15)): d+2매도정산금
      out_d2_pymn_alow_amt (str(15)): d+2출금가능금액
      out_50stk_ord_alow_amt (str(15)): 50%종목주문가능금액
      out_60stk_ord_alow_amt (str(15)): 60%종목주문가능금액
      out_stk_entr_prst (list): 종목별예수금
        - crnc_cd (str(3)): 통화코드
        - fx_entr (str(15)): 외화예수금
        - fc_krw_repl_evlta (str(15)): 원화대용평가금
        - fc_trst_profa (str(15)): 해외주식증거금
        - pymn_alow_amt (str(15)): 출금가능금액
        - pymn_alow_amt_entr (str(15)): 출금가능금액(예수금)
        - ord_alow_amt_entr (str(15)): 주문가능금액(예수금)
        - fc_uncla (str(15)): 외화미수(합계)
        - fc_ch_uncla (str(15)): 외화현금미수금
        - dly_amt (str(15)): 연체료
        - d1_fx_entr (str(15)): d+1외화예수금
        - d2_fx_entr (str(15)): d+2외화예수금
        - d3_fx_entr (str(15)): d+3외화예수금
        - d4_fx_entr (str(15)): d+4외화예수금
    
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
      'api-id': 'kt00001',
    }
    params = {
      'qry_tp': in_qry_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_entr'] = out_data['entr']
    return_data['out_profa_ch'] = out_data['profa_ch']
    return_data['out_bncr_profa_ch'] = out_data['bncr_profa_ch']
    return_data['out_nxdy_bncr_sell_exct'] = out_data['nxdy_bncr_sell_exct']
    return_data['out_fc_stk_krw_repl_set_amt'] = out_data['fc_stk_krw_repl_set_amt']
    return_data['out_crd_grnta_ch'] = out_data['crd_grnta_ch']
    return_data['out_crd_grnt_ch'] = out_data['crd_grnt_ch']
    return_data['out_add_grnt_ch'] = out_data['add_grnt_ch']
    return_data['out_etc_profa'] = out_data['etc_profa']
    return_data['out_uncl_stk_amt'] = out_data['uncl_stk_amt']
    return_data['out_shrts_prica'] = out_data['shrts_prica']
    return_data['out_crd_set_grnta'] = out_data['crd_set_grnta']
    return_data['out_chck_ina_amt'] = out_data['chck_ina_amt']
    return_data['out_etc_chck_ina_amt'] = out_data['etc_chck_ina_amt']
    return_data['out_crd_grnt_ruse'] = out_data['crd_grnt_ruse']
    return_data['out_knx_asset_evltv'] = out_data['knx_asset_evltv']
    return_data['out_elwdpst_evlta'] = out_data['elwdpst_evlta']
    return_data['out_crd_ls_rght_frcs_amt'] = out_data['crd_ls_rght_frcs_amt']
    return_data['out_lvlh_join_amt'] = out_data['lvlh_join_amt']
    return_data['out_lvlh_trns_alowa'] = out_data['lvlh_trns_alowa']
    return_data['out_repl_amt'] = out_data['repl_amt']
    return_data['out_remn_repl_evlta'] = out_data['remn_repl_evlta']
    return_data['out_trst_remn_repl_evlta'] = out_data['trst_remn_repl_evlta']
    return_data['out_bncr_remn_repl_evlta'] = out_data['bncr_remn_repl_evlta']
    return_data['out_profa_repl'] = out_data['profa_repl']
    return_data['out_crd_grnta_repl'] = out_data['crd_grnta_repl']
    return_data['out_crd_grnt_repl'] = out_data['crd_grnt_repl']
    return_data['out_add_grnt_repl'] = out_data['add_grnt_repl']
    return_data['out_rght_repl_amt'] = out_data['rght_repl_amt']
    return_data['out_pymn_alow_amt'] = out_data['pymn_alow_amt']
    return_data['out_wrap_pymn_alow_amt'] = out_data['wrap_pymn_alow_amt']
    return_data['out_ord_alow_amt'] = out_data['ord_alow_amt']
    return_data['out_bncr_buy_alowa'] = out_data['bncr_buy_alowa']
    return_data['out_20stk_ord_alow_amt'] = out_data['20stk_ord_alow_amt']
    return_data['out_30stk_ord_alow_amt'] = out_data['30stk_ord_alow_amt']
    return_data['out_40stk_ord_alow_amt'] = out_data['40stk_ord_alow_amt']
    return_data['out_100stk_ord_alow_amt'] = out_data['100stk_ord_alow_amt']
    return_data['out_ch_uncla'] = out_data['ch_uncla']
    return_data['out_ch_uncla_dlfe'] = out_data['ch_uncla_dlfe']
    return_data['out_ch_uncla_tot'] = out_data['ch_uncla_tot']
    return_data['out_crd_int_npay'] = out_data['crd_int_npay']
    return_data['out_int_npay_amt_dlfe'] = out_data['int_npay_amt_dlfe']
    return_data['out_int_npay_amt_tot'] = out_data['int_npay_amt_tot']
    return_data['out_etc_loana'] = out_data['etc_loana']
    return_data['out_etc_loana_dlfe'] = out_data['etc_loana_dlfe']
    return_data['out_etc_loan_tot'] = out_data['etc_loan_tot']
    return_data['out_nrpy_loan'] = out_data['nrpy_loan']
    return_data['out_loan_sum'] = out_data['loan_sum']
    return_data['out_ls_sum'] = out_data['ls_sum']
    return_data['out_crd_grnt_rt'] = out_data['crd_grnt_rt']
    return_data['out_mdstrm_usfe'] = out_data['mdstrm_usfe']
    return_data['out_min_ord_alow_yn'] = out_data['min_ord_alow_yn']
    return_data['out_loan_remn_evlt_amt'] = out_data['loan_remn_evlt_amt']
    return_data['out_dpst_grntl_remn'] = out_data['dpst_grntl_remn']
    return_data['out_sell_grntl_remn'] = out_data['sell_grntl_remn']
    return_data['out_d1_entra'] = out_data['d1_entra']
    return_data['out_d1_slby_exct_amt'] = out_data['d1_slby_exct_amt']
    return_data['out_d1_buy_exct_amt'] = out_data['d1_buy_exct_amt']
    return_data['out_d1_out_rep_mor'] = out_data['d1_out_rep_mor']
    return_data['out_d1_sel_exct_amt'] = out_data['d1_sel_exct_amt']
    return_data['out_d1_pymn_alow_amt'] = out_data['d1_pymn_alow_amt']
    return_data['out_d2_entra'] = out_data['d2_entra']
    return_data['out_d2_slby_exct_amt'] = out_data['d2_slby_exct_amt']
    return_data['out_d2_buy_exct_amt'] = out_data['d2_buy_exct_amt']
    return_data['out_d2_out_rep_mor'] = out_data['d2_out_rep_mor']
    return_data['out_d2_sel_exct_amt'] = out_data['d2_sel_exct_amt']
    return_data['out_d2_pymn_alow_amt'] = out_data['d2_pymn_alow_amt']
    return_data['out_50stk_ord_alow_amt'] = out_data['50stk_ord_alow_amt']
    return_data['out_60stk_ord_alow_amt'] = out_data['60stk_ord_alow_amt']
    return_data['out_stk_entr_prst'] = out_data['stk_entr_prst']
    
    return return_data

  def get_kt00002(self, in_cont_yn: str, in_next_key: str, in_start_dt: str, in_end_dt: str):
    """
    일별추정예탁자산현황요청
    메뉴 위치 : 국내주식 > 계좌 > 일별추정예탁자산현황요청(kt00002)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_start_dt (str(8)): 시작조회기간(필수) YYYYMMDD
      in_end_dt (str(8)): 종료조회기간(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_daly_prsm_dpst_aset_amt_prst (list): 일별추정예탁자산현황
        - dt (str(8)): 일자
        - entr (str(12)): 예수금
        - grnt_use_amt (str(12)): 담보대출금
        - crd_loan (str(12)): 신용융자금
        - ls_grnt (str(12)): 대주담보금
        - repl_amt (str(12)): 대용금
        - prsm_dpst_aset_amt (str(12)): 추정예탁자산
        - prsm_dpst_aset_amt_bncr_skip (str(12)): 추정예탁자산수익증권제외
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_start_dt or in_start_dt == '':
      in_start_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'kt00002',
    }
    params = {
      'start_dt': in_start_dt,
      'end_dt': in_end_dt,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_daly_prsm_dpst_aset_amt_prst'] = out_data['daly_prsm_dpst_aset_amt_prst']
    
    return return_data

  def get_kt00003(self, in_cont_yn: str, in_next_key: str, in_qry_tp: str):
    """
    추정자산조회요청
    메뉴 위치 : 국내주식 > 계좌 > 추정자산조회요청(kt00003)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_qry_tp (str(1)): 상장폐지조회구분(필수) 0:전체, 1:상장폐지종목제외
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_prsm_dpst_aset_amt (str(12)): 추정예탁자산
    
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
      'api-id': 'kt00003',
    }
    params = {
      'qry_tp': in_qry_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_prsm_dpst_aset_amt'] = out_data['prsm_dpst_aset_amt']
    
    return return_data

  def get_kt00004(self, in_cont_yn: str, in_next_key: str, in_qry_tp: str, in_dmst_stex_tp: str):
    """
    계좌평가현황요청
    메뉴 위치 : 국내주식 > 계좌 > 계좌평가현황요청(kt00004)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_qry_tp (str(1)): 상장폐지조회구분(필수) 0:전체, 1:상장폐지종목제외
      in_dmst_stex_tp (str(6)): 국내거래소구분(필수) KRX:한국거래소,NXT:넥스트트레이드
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_acnt_nm (str(30)): 계좌명
      out_brch_nm (str(30)): 지점명
      out_entr (str(12)): 예수금
      out_d2_entra (str(12)): D+2추정예수금
      out_tot_est_amt (str(12)): 유가잔고평가액
      out_aset_evlt_amt (str(12)): 예탁자산평가액
      out_tot_pur_amt (str(12)): 총매입금액
      out_prsm_dpst_aset_amt (str(12)): 추정예탁자산
      out_tot_grnt_sella (str(12)): 매도담보대출금
      out_tdy_lspft_amt (str(12)): 당일투자원금
      out_invt_bsamt (str(12)): 당월투자원금
      out_lspft_amt (str(12)): 누적투자원금
      out_tdy_lspft (str(12)): 당일투자손익
      out_lspft2 (str(12)): 당월투자손익
      out_lspft (str(12)): 누적투자손익
      out_tdy_lspft_rt (str(12)): 당일손익율
      out_lspft_ratio (str(12)): 당월손익율
      out_lspft_rt (str(12)): 누적손익율
      out_stk_acnt_evlt_prst (list): 종목별계좌평가현황
        - stk_cd (str(12)): 종목코드
        - stk_nm (str(30)): 종목명
        - rmnd_qty (str(12)): 보유수량
        - avg_prc (str(12)): 평균단가
        - cur_prc (str(12)): 현재가
        - evlt_amt (str(12)): 평가금액
        - pl_amt (str(12)): 손익금액
        - pl_rt (str(12)): 손익율
        - loan_dt (str(10)): 대출일
        - pur_amt (str(12)): 매입금액
        - setl_remn (str(12)): 결제잔고
        - pred_buyq (str(12)): 전일매수수량
        - pred_sellq (str(12)): 전일매도수량
        - tdy_buyq (str(12)): 금일매수수량
        - tdy_sellq (str(12)): 금일매도수량
    
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
      'api-id': 'kt00004',
    }
    params = {
      'qry_tp': in_qry_tp,
      'dmst_stex_tp': in_dmst_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_acnt_nm'] = out_data['acnt_nm']
    return_data['out_brch_nm'] = out_data['brch_nm']
    return_data['out_entr'] = out_data['entr']
    return_data['out_d2_entra'] = out_data['d2_entra']
    return_data['out_tot_est_amt'] = out_data['tot_est_amt']
    return_data['out_aset_evlt_amt'] = out_data['aset_evlt_amt']
    return_data['out_tot_pur_amt'] = out_data['tot_pur_amt']
    return_data['out_prsm_dpst_aset_amt'] = out_data['prsm_dpst_aset_amt']
    return_data['out_tot_grnt_sella'] = out_data['tot_grnt_sella']
    return_data['out_tdy_lspft_amt'] = out_data['tdy_lspft_amt']
    return_data['out_invt_bsamt'] = out_data['invt_bsamt']
    return_data['out_lspft_amt'] = out_data['lspft_amt']
    return_data['out_tdy_lspft'] = out_data['tdy_lspft']
    return_data['out_lspft2'] = out_data['lspft2']
    return_data['out_lspft'] = out_data['lspft']
    return_data['out_tdy_lspft_rt'] = out_data['tdy_lspft_rt']
    return_data['out_lspft_ratio'] = out_data['lspft_ratio']
    return_data['out_lspft_rt'] = out_data['lspft_rt']
    return_data['out_stk_acnt_evlt_prst'] = out_data['stk_acnt_evlt_prst']
    
    return return_data

  def get_kt00005(self, in_cont_yn: str, in_next_key: str, in_dmst_stex_tp: str):
    """
    체결잔고요청
    메뉴 위치 : 국내주식 > 계좌 > 체결잔고요청(kt00005)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dmst_stex_tp (str(6)): 국내거래소구분(필수) KRX:한국거래소,NXT:넥스트트레이드
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_entr (str(12)): 예수금
      out_entr_d1 (str(12)): 예수금D+1
      out_entr_d2 (str(12)): 예수금D+2
      out_pymn_alow_amt (str(12)): 출금가능금액
      out_uncl_stk_amt (str(12)): 미수확보금
      out_repl_amt (str(12)): 대용금
      out_rght_repl_amt (str(12)): 권리대용금
      out_ord_alowa (str(12)): 주문가능현금
      out_ch_uncla (str(12)): 현금미수금
      out_crd_int_npay_gold (str(12)): 신용이자미납금
      out_etc_loana (str(12)): 기타대여금
      out_nrpy_loan (str(12)): 미상환융자금
      out_profa_ch (str(12)): 증거금현금
      out_repl_profa (str(12)): 증거금대용
      out_stk_buy_tot_amt (str(12)): 주식매수총액
      out_evlt_amt_tot (str(12)): 평가금액합계
      out_tot_pl_tot (str(12)): 총손익합계
      out_tot_pl_rt (str(12)): 총손익률
      out_tot_re_buy_alowa (str(12)): 총재매수가능금액
      out_20ord_alow_amt (str(12)): 20%주문가능금액
      out_30ord_alow_amt (str(12)): 30%주문가능금액
      out_40ord_alow_amt (str(12)): 40%주문가능금액
      out_50ord_alow_amt (str(12)): 50%주문가능금액
      out_60ord_alow_amt (str(12)): 60%주문가능금액
      out_100ord_alow_amt (str(12)): 100%주문가능금액
      out_crd_loan_tot (str(12)): 신용융자합계
      out_crd_loan_ls_tot (str(12)): 신용융자대주합계
      out_crd_grnt_rt (str(12)): 신용담보비율
      out_dpst_grnt_use_amt_amt (str(12)): 예탁담보대출금액
      out_grnt_loan_amt (str(12)): 매도담보대출금액
      out_stk_cntr_remn (list): 종목별체결잔고
        - crd_tp (str(2)): 신용구분
        - loan_dt (str(8)): 대출일
        - expr_dt (str(8)): 만기일
        - stk_cd (str(12)): 종목번호
        - stk_nm (str(30)): 종목명
        - setl_remn (str(12)): 결제잔고
        - cur_qty (str(12)): 현재잔고
        - cur_prc (str(12)): 현재가
        - buy_uv (str(12)): 매입단가
        - pur_amt (str(12)): 매입금액
        - evlt_amt (str(12)): 평가금액
        - evltv_prft (str(12)): 평가손익
        - pl_rt (str(12)): 손익률
    
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
      'api-id': 'kt00005',
    }
    params = {
      'dmst_stex_tp': in_dmst_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_entr'] = out_data['entr']
    return_data['out_entr_d1'] = out_data['entr_d1']
    return_data['out_entr_d2'] = out_data['entr_d2']
    return_data['out_pymn_alow_amt'] = out_data['pymn_alow_amt']
    return_data['out_uncl_stk_amt'] = out_data['uncl_stk_amt']
    return_data['out_repl_amt'] = out_data['repl_amt']
    return_data['out_rght_repl_amt'] = out_data['rght_repl_amt']
    return_data['out_ord_alowa'] = out_data['ord_alowa']
    return_data['out_ch_uncla'] = out_data['ch_uncla']
    return_data['out_crd_int_npay_gold'] = out_data['crd_int_npay_gold']
    return_data['out_etc_loana'] = out_data['etc_loana']
    return_data['out_nrpy_loan'] = out_data['nrpy_loan']
    return_data['out_profa_ch'] = out_data['profa_ch']
    return_data['out_repl_profa'] = out_data['repl_profa']
    return_data['out_stk_buy_tot_amt'] = out_data['stk_buy_tot_amt']
    return_data['out_evlt_amt_tot'] = out_data['evlt_amt_tot']
    return_data['out_tot_pl_tot'] = out_data['tot_pl_tot']
    return_data['out_tot_pl_rt'] = out_data['tot_pl_rt']
    return_data['out_tot_re_buy_alowa'] = out_data['tot_re_buy_alowa']
    return_data['out_20ord_alow_amt'] = out_data['20ord_alow_amt']
    return_data['out_30ord_alow_amt'] = out_data['30ord_alow_amt']
    return_data['out_40ord_alow_amt'] = out_data['40ord_alow_amt']
    return_data['out_50ord_alow_amt'] = out_data['50ord_alow_amt']
    return_data['out_60ord_alow_amt'] = out_data['60ord_alow_amt']
    return_data['out_100ord_alow_amt'] = out_data['100ord_alow_amt']
    return_data['out_crd_loan_tot'] = out_data['crd_loan_tot']
    return_data['out_crd_loan_ls_tot'] = out_data['crd_loan_ls_tot']
    return_data['out_crd_grnt_rt'] = out_data['crd_grnt_rt']
    return_data['out_dpst_grnt_use_amt_amt'] = out_data['dpst_grnt_use_amt_amt']
    return_data['out_grnt_loan_amt'] = out_data['grnt_loan_amt']
    return_data['out_stk_cntr_remn'] = out_data['stk_cntr_remn']
    
    return return_data

  def get_kt00007(self, in_cont_yn: str, in_next_key: str, in_ord_dt: str, in_qry_tp: str, in_stk_bond_tp: str, in_sell_tp: str, in_stk_cd: str, in_fr_ord_no: str, in_dmst_stex_tp: str):
    """
    계좌별주문체결내역상세요청
    메뉴 위치 : 국내주식 > 계좌 > 계좌별주문체결내역상세요청(kt00007)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_ord_dt (str(8)): 주문일자 YYYYMMDD
      in_qry_tp (str(1)): 조회구분(필수) 1:주문순, 2:역순, 3:미체결, 4:체결내역만
      in_stk_bond_tp (str(1)): 주식채권구분(필수) 0:전체, 1:주식, 2:채권
      in_sell_tp (str(1)): 매도수구분(필수) 0:전체, 1:매도, 2:매수
      in_stk_cd (str(12)): 종목코드 공백허용 (공백일때 전체종목)
      in_fr_ord_no (str(7)): 시작주문번호 공백허용 (공백일때 전체주문)
      in_dmst_stex_tp (str(6)): 국내거래소구분(필수) %:(전체),KRX:한국거래소,NXT:넥스트트레이드,SOR:최선주문집행
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_acnt_ord_cntr_prps_dtl (list): 계좌별주문체결내역상세
        - ord_no (str(7)): 주문번호
        - stk_cd (str(12)): 종목번호
        - trde_tp (str(20)): 매매구분
        - crd_tp (str(20)): 신용구분
        - ord_qty (str(10)): 주문수량
        - ord_uv (str(10)): 주문단가
        - cnfm_qty (str(10)): 확인수량
        - acpt_tp (str(20)): 접수구분
        - rsrv_tp (str(20)): 반대여부
        - ord_tm (str(8)): 주문시간
        - ori_ord (str(7)): 원주문
        - stk_nm (str(40)): 종목명
        - io_tp_nm (str(20)): 주문구분
        - loan_dt (str(8)): 대출일
        - cntr_qty (str(10)): 체결수량
        - cntr_uv (str(10)): 체결단가
        - ord_remnq (str(10)): 주문잔량
        - comm_ord_tp (str(20)): 통신구분
        - mdfy_cncl (str(20)): 정정취소
        - cnfm_tm (str(8)): 확인시간
        - dmst_stex_tp (str(8)): 국내거래소구분
        - cond_uv (str(10)): 스톱가
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_ord_dt or in_ord_dt == '':
      in_ord_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'kt00007',
    }
    params = {
      'ord_dt': in_ord_dt,
      'qry_tp': in_qry_tp,
      'stk_bond_tp': in_stk_bond_tp,
      'sell_tp': in_sell_tp,
      'stk_cd': in_stk_cd,
      'fr_ord_no': in_fr_ord_no,
      'dmst_stex_tp': in_dmst_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_acnt_ord_cntr_prps_dtl'] = out_data['acnt_ord_cntr_prps_dtl']
    
    return return_data

  def get_kt00008(self, in_cont_yn: str, in_next_key: str, in_strt_dcd_seq: str):
    """
    계좌별익일결제예정내역요청
    메뉴 위치 : 국내주식 > 계좌 > 계좌별익일결제예정내역요청(kt00008)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_strt_dcd_seq (str(7)): 시작결제번호
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_trde_dt (str(8)): 매매일자
      out_setl_dt (str(8)): 결제일자
      out_sell_amt_sum (str(12)): 매도정산합
      out_buy_amt_sum (str(12)): 매수정산합
      out_acnt_nxdy_setl_frcs_prps_array (list): 계좌별익일결제예정내역배열
        - seq (str(7)): 일련번호
        - stk_cd (str(12)): 종목번호
        - loan_dt (str(8)): 대출일
        - qty (str(12)): 수량
        - engg_amt (str(12)): 약정금액
        - cmsn (str(12)): 수수료
        - incm_tax (str(12)): 소득세
        - rstx (str(12)): 농특세
        - stk_nm (str(40)): 종목명
        - sell_tp (str(10)): 매도수구분
        - unp (str(12)): 단가
        - exct_amt (str(12)): 정산금액
        - trde_tax (str(12)): 거래세
        - resi_tax (str(12)): 주민세
        - crd_tp (str(20)): 신용구분
    
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
      'api-id': 'kt00008',
    }
    params = {
      'strt_dcd_seq': in_strt_dcd_seq,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_trde_dt'] = out_data['trde_dt']
    return_data['out_setl_dt'] = out_data['setl_dt']
    return_data['out_sell_amt_sum'] = out_data['sell_amt_sum']
    return_data['out_buy_amt_sum'] = out_data['buy_amt_sum']
    return_data['out_acnt_nxdy_setl_frcs_prps_array'] = out_data['acnt_nxdy_setl_frcs_prps_array']
    
    return return_data

  def get_kt00009(self, in_cont_yn: str, in_next_key: str, in_ord_dt: str, in_stk_bond_tp: str, in_mrkt_tp: str, in_sell_tp: str, in_qry_tp: str, in_stk_cd: str, in_fr_ord_no: str, in_dmst_stex_tp: str):
    """
    계좌별주문체결현황요청
    메뉴 위치 : 국내주식 > 계좌 > 계좌별주문체결현황요청(kt00009)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_ord_dt (str(8)): 주문일자 YYYYMMDD
      in_stk_bond_tp (str(1)): 주식채권구분(필수) 0:전체, 1:주식, 2:채권
      in_mrkt_tp (str(1)): 시장구분(필수) 0:전체, 1:코스피, 2:코스닥, 3:OTCBB, 4:ECN
      in_sell_tp (str(1)): 매도수구분(필수) 0:전체, 1:매도, 2:매수
      in_qry_tp (str(1)): 조회구분(필수) 0:전체, 1:체결
      in_stk_cd (str(12)): 종목코드 전문 조회할 종목코드
      in_fr_ord_no (str(7)): 시작주문번호
      in_dmst_stex_tp (str(6)): 국내거래소구분(필수) %:(전체),KRX:한국거래소,NXT:넥스트트레이드,SOR:최선주문집행
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_sell_grntl_engg_amt (str(12)): 매도약정금액
      out_buy_engg_amt (str(12)): 매수약정금액
      out_engg_amt (str(12)): 약정금액
      out_acnt_ord_cntr_prst_array (list): 계좌별주문체결현황배열
        - stk_bond_tp (str(1)): 주식채권구분
        - ord_no (str(7)): 주문번호
        - stk_cd (str(12)): 종목번호
        - trde_tp (str(15)): 매매구분
        - io_tp_nm (str(20)): 주문유형구분
        - ord_qty (str(10)): 주문수량
        - ord_uv (str(10)): 주문단가
        - cnfm_qty (str(10)): 확인수량
        - rsrv_oppo (str(4)): 예약/반대
        - cntr_no (str(7)): 체결번호
        - acpt_tp (str(8)): 접수구분
        - orig_ord_no (str(7)): 원주문번호
        - stk_nm (str(20)): 종목명
        - setl_tp (str(8)): 결제구분
        - crd_deal_tp (str(20)): 신용거래구분
        - cntr_qty (str(10)): 체결수량
        - cntr_uv (str(10)): 체결단가
        - comm_ord_tp (str(8)): 통신구분
        - mdfy_cncl_tp (str(12)): 정정/취소구분
        - cntr_tm (str(8)): 체결시간
        - dmst_stex_tp (str(6)): 국내거래소구분
        - cond_uv (str(10)): 스톱가
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_ord_dt or in_ord_dt == '':
      in_ord_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'kt00009',
    }
    params = {
      'ord_dt': in_ord_dt,
      'stk_bond_tp': in_stk_bond_tp,
      'mrkt_tp': in_mrkt_tp,
      'sell_tp': in_sell_tp,
      'qry_tp': in_qry_tp,
      'stk_cd': in_stk_cd,
      'fr_ord_no': in_fr_ord_no,
      'dmst_stex_tp': in_dmst_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_sell_grntl_engg_amt'] = out_data['sell_grntl_engg_amt']
    return_data['out_buy_engg_amt'] = out_data['buy_engg_amt']
    return_data['out_engg_amt'] = out_data['engg_amt']
    return_data['out_acnt_ord_cntr_prst_array'] = out_data['acnt_ord_cntr_prst_array']
    
    return return_data

  def get_kt00010(self, in_cont_yn: str, in_next_key: str, in_io_amt: str, in_stk_cd: str, in_trde_tp: str, in_trde_qty: str, in_uv: str, in_exp_buy_unp: str):
    """
    주문인출가능금액요청
    메뉴 위치 : 국내주식 > 계좌 > 주문인출가능금액요청(kt00010)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_io_amt (str(12)): 입출금액
      in_stk_cd (str(12)): 종목번호(필수)
      in_trde_tp (str(1)): 매매구분(필수) 1:매도, 2:매수
      in_trde_qty (str(10)): 매매수량
      in_uv (str(10)): 매수가격(필수)
      in_exp_buy_unp (str(10)): 예상매수단가
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_profa_20ord_alow_amt (str(12)): 증거금20%주문가능금액
      out_profa_20ord_alowq (str(10)): 증거금20%주문가능수량
      out_profa_30ord_alow_amt (str(12)): 증거금30%주문가능금액
      out_profa_30ord_alowq (str(10)): 증거금30%주문가능수량
      out_profa_40ord_alow_amt (str(12)): 증거금40%주문가능금액
      out_profa_40ord_alowq (str(10)): 증거금40%주문가능수량
      out_profa_50ord_alow_amt (str(12)): 증거금50%주문가능금액
      out_profa_50ord_alowq (str(10)): 증거금50%주문가능수량
      out_profa_60ord_alow_amt (str(12)): 증거금60%주문가능금액
      out_profa_60ord_alowq (str(10)): 증거금60%주문가능수량
      out_profa_rdex_60ord_alow_amt (str(12)): 증거금감면60%주문가능금
      out_profa_rdex_60ord_alowq (str(10)): 증거금감면60%주문가능수
      out_profa_100ord_alow_amt (str(12)): 증거금100%주문가능금액
      out_profa_100ord_alowq (str(10)): 증거금100%주문가능수량
      out_pred_reu_alowa (str(12)): 전일재사용가능금액
      out_tdy_reu_alowa (str(12)): 금일재사용가능금액
      out_entr (str(12)): 예수금
      out_repl_amt (str(12)): 대용금
      out_uncla (str(12)): 미수금
      out_ord_pos_repl (str(12)): 주문가능대용
      out_ord_alowa (str(12)): 주문가능현금
      out_wthd_alowa (str(12)): 인출가능금액
      out_nxdy_wthd_alowa (str(12)): 익일인출가능금액
      out_pur_amt (str(12)): 매입금액
      out_cmsn (str(12)): 수수료
      out_pur_exct_amt (str(12)): 매입정산금
      out_d2entra (str(12)): D2추정예수금
      out_profa_rdex_aplc_tp (str(1)): 증거금감면적용구분. 0:일반,1:60%감면
    
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
      'api-id': 'kt00010',
    }
    params = {
      'io_amt': in_io_amt,
      'stk_cd': in_stk_cd,
      'trde_tp': in_trde_tp,
      'trde_qty': in_trde_qty,
      'uv': in_uv,
      'exp_buy_unp': in_exp_buy_unp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_profa_20ord_alow_amt'] = out_data['profa_20ord_alow_amt']
    return_data['out_profa_20ord_alowq'] = out_data['profa_20ord_alowq']
    return_data['out_profa_30ord_alow_amt'] = out_data['profa_30ord_alow_amt']
    return_data['out_profa_30ord_alowq'] = out_data['profa_30ord_alowq']
    return_data['out_profa_40ord_alow_amt'] = out_data['profa_40ord_alow_amt']
    return_data['out_profa_40ord_alowq'] = out_data['profa_40ord_alowq']
    return_data['out_profa_50ord_alow_amt'] = out_data['profa_50ord_alow_amt']
    return_data['out_profa_50ord_alowq'] = out_data['profa_50ord_alowq']
    return_data['out_profa_60ord_alow_amt'] = out_data['profa_60ord_alow_amt']
    return_data['out_profa_60ord_alowq'] = out_data['profa_60ord_alowq']
    return_data['out_profa_rdex_60ord_alow_amt'] = out_data['profa_rdex_60ord_alow_amt']
    return_data['out_profa_rdex_60ord_alowq'] = out_data['profa_rdex_60ord_alowq']
    return_data['out_profa_100ord_alow_amt'] = out_data['profa_100ord_alow_amt']
    return_data['out_profa_100ord_alowq'] = out_data['profa_100ord_alowq']
    return_data['out_pred_reu_alowa'] = out_data['pred_reu_alowa']
    return_data['out_tdy_reu_alowa'] = out_data['tdy_reu_alowa']
    return_data['out_entr'] = out_data['entr']
    return_data['out_repl_amt'] = out_data['repl_amt']
    return_data['out_uncla'] = out_data['uncla']
    return_data['out_ord_pos_repl'] = out_data['ord_pos_repl']
    return_data['out_ord_alowa'] = out_data['ord_alowa']
    return_data['out_wthd_alowa'] = out_data['wthd_alowa']
    return_data['out_nxdy_wthd_alowa'] = out_data['nxdy_wthd_alowa']
    return_data['out_pur_amt'] = out_data['pur_amt']
    return_data['out_cmsn'] = out_data['cmsn']
    return_data['out_pur_exct_amt'] = out_data['pur_exct_amt']
    return_data['out_d2entra'] = out_data['d2entra']
    return_data['out_profa_rdex_aplc_tp'] = out_data['profa_rdex_aplc_tp']
    
    return return_data

  def get_kt00011(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_uv: str):
    """
    증거금율별주문가능수량조회요청
    메뉴 위치 : 국내주식 > 계좌 > 증거금율별주문가능수량조회요청(kt00011)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(12)): 종목번호(필수)
      in_uv (str(10)): 매수가격
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_profa_rt (str(15)): 종목증거금율
      out_profa_rt (str(15)): 계좌증거금율
      out_aplc_rt (str(15)): 적용증거금율
      out_profa_20ord_alow_amt (str(12)): 증거금20%주문가능금액
      out_profa_20ord_alowq (str(12)): 증거금20%주문가능수량
      out_profa_20pred_reu_amt (str(12)): 증거금20%전일재사용금액
      out_profa_20tdy_reu_amt (str(12)): 증거금20%금일재사용금액
      out_profa_30ord_alow_amt (str(12)): 증거금30%주문가능금액
      out_profa_30ord_alowq (str(12)): 증거금30%주문가능수량
      out_profa_30pred_reu_amt (str(12)): 증거금30%전일재사용금액
      out_profa_30tdy_reu_amt (str(12)): 증거금30%금일재사용금액
      out_profa_40ord_alow_amt (str(12)): 증거금40%주문가능금액
      out_profa_40ord_alowq (str(12)): 증거금40%주문가능수량
      out_profa_40pred_reu_amt (str(12)): 증거금40전일재사용금액
      out_profa_40tdy_reu_amt (str(12)): 증거금40%금일재사용금액
      out_profa_50ord_alow_amt (str(12)): 증거금50%주문가능금액
      out_profa_50ord_alowq (str(12)): 증거금50%주문가능수량
      out_profa_50pred_reu_amt (str(12)): 증거금50%전일재사용금액
      out_profa_50tdy_reu_amt (str(12)): 증거금50%금일재사용금액
      out_profa_60ord_alow_amt (str(12)): 증거금60%주문가능금액
      out_profa_60ord_alowq (str(12)): 증거금60%주문가능수량
      out_profa_60pred_reu_amt (str(12)): 증거금60%전일재사용금액
      out_profa_60tdy_reu_amt (str(12)): 증거금60%금일재사용금액
      out_profa_100ord_alow_amt (str(12)): 증거금100%주문가능금액
      out_profa_100ord_alowq (str(12)): 증거금100%주문가능수량
      out_profa_100pred_reu_amt (str(12)): 증거금100%전일재사용금액
      out_profa_100tdy_reu_amt (str(12)): 증거금100%금일재사용금액
      out_min_ord_alow_amt (str(12)): 미수불가주문가능금액
      out_min_ord_alowq (str(12)): 미수불가주문가능수량
      out_min_pred_reu_amt (str(12)): 미수불가전일재사용금액
      out_min_tdy_reu_amt (str(12)): 미수불가금일재사용금액
      out_entr (str(12)): 예수금
      out_repl_amt (str(12)): 대용금
      out_uncla (str(12)): 미수금
      out_ord_pos_repl (str(12)): 주문가능대용
      out_ord_alowa (str(12)): 주문가능현금
    
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
      'api-id': 'kt00011',
    }
    params = {
      'stk_cd': in_stk_cd,
      'uv': in_uv,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_profa_rt'] = out_data['stk_profa_rt']
    return_data['out_profa_rt'] = out_data['profa_rt']
    return_data['out_aplc_rt'] = out_data['aplc_rt']
    return_data['out_profa_20ord_alow_amt'] = out_data['profa_20ord_alow_amt']
    return_data['out_profa_20ord_alowq'] = out_data['profa_20ord_alowq']
    return_data['out_profa_20pred_reu_amt'] = out_data['profa_20pred_reu_amt']
    return_data['out_profa_20tdy_reu_amt'] = out_data['profa_20tdy_reu_amt']
    return_data['out_profa_30ord_alow_amt'] = out_data['profa_30ord_alow_amt']
    return_data['out_profa_30ord_alowq'] = out_data['profa_30ord_alowq']
    return_data['out_profa_30pred_reu_amt'] = out_data['profa_30pred_reu_amt']
    return_data['out_profa_30tdy_reu_amt'] = out_data['profa_30tdy_reu_amt']
    return_data['out_profa_40ord_alow_amt'] = out_data['profa_40ord_alow_amt']
    return_data['out_profa_40ord_alowq'] = out_data['profa_40ord_alowq']
    return_data['out_profa_40pred_reu_amt'] = out_data['profa_40pred_reu_amt']
    return_data['out_profa_40tdy_reu_amt'] = out_data['profa_40tdy_reu_amt']
    return_data['out_profa_50ord_alow_amt'] = out_data['profa_50ord_alow_amt']
    return_data['out_profa_50ord_alowq'] = out_data['profa_50ord_alowq']
    return_data['out_profa_50pred_reu_amt'] = out_data['profa_50pred_reu_amt']
    return_data['out_profa_50tdy_reu_amt'] = out_data['profa_50tdy_reu_amt']
    return_data['out_profa_60ord_alow_amt'] = out_data['profa_60ord_alow_amt']
    return_data['out_profa_60ord_alowq'] = out_data['profa_60ord_alowq']
    return_data['out_profa_60pred_reu_amt'] = out_data['profa_60pred_reu_amt']
    return_data['out_profa_60tdy_reu_amt'] = out_data['profa_60tdy_reu_amt']
    return_data['out_profa_100ord_alow_amt'] = out_data['profa_100ord_alow_amt']
    return_data['out_profa_100ord_alowq'] = out_data['profa_100ord_alowq']
    return_data['out_profa_100pred_reu_amt'] = out_data['profa_100pred_reu_amt']
    return_data['out_profa_100tdy_reu_amt'] = out_data['profa_100tdy_reu_amt']
    return_data['out_min_ord_alow_amt'] = out_data['min_ord_alow_amt']
    return_data['out_min_ord_alowq'] = out_data['min_ord_alowq']
    return_data['out_min_pred_reu_amt'] = out_data['min_pred_reu_amt']
    return_data['out_min_tdy_reu_amt'] = out_data['min_tdy_reu_amt']
    return_data['out_entr'] = out_data['entr']
    return_data['out_repl_amt'] = out_data['repl_amt']
    return_data['out_uncla'] = out_data['uncla']
    return_data['out_ord_pos_repl'] = out_data['ord_pos_repl']
    return_data['out_ord_alowa'] = out_data['ord_alowa']
    
    return return_data

  def get_kt00012(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_uv: str):
    """
    신용보증금율별주문가능수량조회요청
    메뉴 위치 : 국내주식 > 계좌 > 신용보증금율별주문가능수량조회요청(kt00012)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(12)): 종목번호(필수)
      in_uv (str(10)): 매수가격
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_assr_rt (str(1)): 종목보증금율
      out_stk_assr_rt_nm (str(4)): 종목보증금율명
      out_assr_30ord_alow_amt (str(12)): 보증금30%주문가능금액
      out_assr_30ord_alowq (str(12)): 보증금30%주문가능수량
      out_assr_30pred_reu_amt (str(12)): 보증금30%전일재사용금액
      out_assr_30tdy_reu_amt (str(12)): 보증금30%금일재사용금액
      out_assr_40ord_alow_amt (str(12)): 보증금40%주문가능금액
      out_assr_40ord_alowq (str(12)): 보증금40%주문가능수량
      out_assr_40pred_reu_amt (str(12)): 보증금40%전일재사용금액
      out_assr_40tdy_reu_amt (str(12)): 보증금40%금일재사용금액
      out_assr_50ord_alow_amt (str(12)): 보증금50%주문가능금액
      out_assr_50ord_alowq (str(12)): 보증금50%주문가능수량
      out_assr_50pred_reu_amt (str(12)): 보증금50%전일재사용금액
      out_assr_50tdy_reu_amt (str(12)): 보증금50%금일재사용금액
      out_assr_60ord_alow_amt (str(12)): 보증금60%주문가능금액
      out_assr_60ord_alowq (str(12)): 보증금60%주문가능수량
      out_assr_60pred_reu_amt (str(12)): 보증금60%전일재사용금액
      out_assr_60tdy_reu_amt (str(12)): 보증금60%금일재사용금액
      out_entr (str(12)): 예수금
      out_repl_amt (str(12)): 대용금
      out_uncla (str(12)): 미수금
      out_ord_pos_repl (str(12)): 주문가능대용
      out_ord_alowa (str(12)): 주문가능현금
      out_out_alowa (str(12)): 미수가능금액
      out_out_pos_qty (str(12)): 미수가능수량
      out_min_amt (str(12)): 미수불가금액
      out_min_qty (str(12)): 미수불가수량
    
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
      'api-id': 'kt00012',
    }
    params = {
      'stk_cd': in_stk_cd,
      'uv': in_uv,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_assr_rt'] = out_data['stk_assr_rt']
    return_data['out_stk_assr_rt_nm'] = out_data['stk_assr_rt_nm']
    return_data['out_assr_30ord_alow_amt'] = out_data['assr_30ord_alow_amt']
    return_data['out_assr_30ord_alowq'] = out_data['assr_30ord_alowq']
    return_data['out_assr_30pred_reu_amt'] = out_data['assr_30pred_reu_amt']
    return_data['out_assr_30tdy_reu_amt'] = out_data['assr_30tdy_reu_amt']
    return_data['out_assr_40ord_alow_amt'] = out_data['assr_40ord_alow_amt']
    return_data['out_assr_40ord_alowq'] = out_data['assr_40ord_alowq']
    return_data['out_assr_40pred_reu_amt'] = out_data['assr_40pred_reu_amt']
    return_data['out_assr_40tdy_reu_amt'] = out_data['assr_40tdy_reu_amt']
    return_data['out_assr_50ord_alow_amt'] = out_data['assr_50ord_alow_amt']
    return_data['out_assr_50ord_alowq'] = out_data['assr_50ord_alowq']
    return_data['out_assr_50pred_reu_amt'] = out_data['assr_50pred_reu_amt']
    return_data['out_assr_50tdy_reu_amt'] = out_data['assr_50tdy_reu_amt']
    return_data['out_assr_60ord_alow_amt'] = out_data['assr_60ord_alow_amt']
    return_data['out_assr_60ord_alowq'] = out_data['assr_60ord_alowq']
    return_data['out_assr_60pred_reu_amt'] = out_data['assr_60pred_reu_amt']
    return_data['out_assr_60tdy_reu_amt'] = out_data['assr_60tdy_reu_amt']
    return_data['out_entr'] = out_data['entr']
    return_data['out_repl_amt'] = out_data['repl_amt']
    return_data['out_uncla'] = out_data['uncla']
    return_data['out_ord_pos_repl'] = out_data['ord_pos_repl']
    return_data['out_ord_alowa'] = out_data['ord_alowa']
    return_data['out_out_alowa'] = out_data['out_alowa']
    return_data['out_out_pos_qty'] = out_data['out_pos_qty']
    return_data['out_min_amt'] = out_data['min_amt']
    return_data['out_min_qty'] = out_data['min_qty']
    
    return return_data

  def get_kt00013(self, in_cont_yn: str, in_next_key: str):
    """
    증거금세부내역조회요청
    메뉴 위치 : 국내주식 > 계좌 > 증거금세부내역조회요청(kt00013)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tdy_reu_objt_amt (str(15)): 금일재사용대상금액
      out_tdy_reu_use_amt (str(15)): 금일재사용사용금액
      out_tdy_reu_alowa (str(15)): 금일재사용가능금액
      out_tdy_reu_lmtt_amt (str(15)): 금일재사용제한금액
      out_tdy_reu_alowa_fin (str(15)): 금일재사용가능금액최종
      out_pred_reu_objt_amt (str(15)): 전일재사용대상금액
      out_pred_reu_use_amt (str(15)): 전일재사용사용금액
      out_pred_reu_alowa (str(15)): 전일재사용가능금액
      out_pred_reu_lmtt_amt (str(15)): 전일재사용제한금액
      out_pred_reu_alowa_fin (str(15)): 전일재사용가능금액최종
      out_ch_amt (str(15)): 현금금액
      out_ch_profa (str(15)): 현금증거금
      out_use_pos_ch (str(15)): 사용가능현금
      out_ch_use_lmtt_amt (str(15)): 현금사용제한금액
      out_use_pos_ch_fin (str(15)): 사용가능현금최종
      out_repl_amt_amt (str(15)): 대용금액
      out_repl_profa (str(15)): 대용증거금
      out_use_pos_repl (str(15)): 사용가능대용
      out_repl_use_lmtt_amt (str(15)): 대용사용제한금액
      out_use_pos_repl_fin (str(15)): 사용가능대용최종
      out_crd_grnta_ch (str(15)): 신용보증금현금
      out_crd_grnta_repl (str(15)): 신용보증금대용
      out_crd_grnt_ch (str(15)): 신용담보금현금
      out_crd_grnt_repl (str(15)): 신용담보금대용
      out_uncla (str(12)): 미수금
      out_ls_grnt_reu_gold (str(15)): 대주담보금재사용금
      out_20ord_alow_amt (str(15)): 20%주문가능금액
      out_30ord_alow_amt (str(15)): 30%주문가능금액
      out_40ord_alow_amt (str(15)): 40%주문가능금액
      out_50ord_alow_amt (str(15)): 50%주문가능금액
      out_60ord_alow_amt (str(15)): 60%주문가능금액
      out_100ord_alow_amt (str(15)): 100%주문가능금액
      out_tdy_crd_rpya_loss_amt (str(15)): 금일신용상환손실금액
      out_pred_crd_rpya_loss_amt (str(15)): 전일신용상환손실금액
      out_tdy_ls_rpya_loss_repl_profa (str(15)): 금일대주상환손실대용증거금
      out_pred_ls_rpya_loss_repl_profa (str(15)): 전일대주상환손실대용증거금
      out_evlt_repl_amt_spg_use_skip (str(15)): 평가대용금(현물사용제외)
      out_evlt_repl_rt (str(15)): 평가대용비율
      out_crd_repl_profa (str(15)): 신용대용증거금
      out_ch_ord_repl_profa (str(15)): 현금주문대용증거금
      out_crd_ord_repl_profa (str(15)): 신용주문대용증거금
      out_crd_repl_conv_gold (str(15)): 신용대용환산금
      out_repl_alowa (str(15)): 대용가능금액(현금제한)
      out_repl_alowa_2 (str(15)): 대용가능금액2(신용제한)
      out_ch_repl_lck_gold (str(15)): 현금대용부족금
      out_crd_repl_lck_gold (str(15)): 신용대용부족금
      out_ch_ord_alow_repla (str(15)): 현금주문가능대용금
      out_crd_ord_alow_repla (str(15)): 신용주문가능대용금
      out_d2vexct_entr (str(15)): D2가정산예수금
      out_d2ch_ord_alow_amt (str(15)): D2현금주문가능금액
    
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
      'api-id': 'kt00013',
    }
    params = {
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_tdy_reu_objt_amt'] = out_data['tdy_reu_objt_amt']
    return_data['out_tdy_reu_use_amt'] = out_data['tdy_reu_use_amt']
    return_data['out_tdy_reu_alowa'] = out_data['tdy_reu_alowa']
    return_data['out_tdy_reu_lmtt_amt'] = out_data['tdy_reu_lmtt_amt']
    return_data['out_tdy_reu_alowa_fin'] = out_data['tdy_reu_alowa_fin']
    return_data['out_pred_reu_objt_amt'] = out_data['pred_reu_objt_amt']
    return_data['out_pred_reu_use_amt'] = out_data['pred_reu_use_amt']
    return_data['out_pred_reu_alowa'] = out_data['pred_reu_alowa']
    return_data['out_pred_reu_lmtt_amt'] = out_data['pred_reu_lmtt_amt']
    return_data['out_pred_reu_alowa_fin'] = out_data['pred_reu_alowa_fin']
    return_data['out_ch_amt'] = out_data['ch_amt']
    return_data['out_ch_profa'] = out_data['ch_profa']
    return_data['out_use_pos_ch'] = out_data['use_pos_ch']
    return_data['out_ch_use_lmtt_amt'] = out_data['ch_use_lmtt_amt']
    return_data['out_use_pos_ch_fin'] = out_data['use_pos_ch_fin']
    return_data['out_repl_amt_amt'] = out_data['repl_amt_amt']
    return_data['out_repl_profa'] = out_data['repl_profa']
    return_data['out_use_pos_repl'] = out_data['use_pos_repl']
    return_data['out_repl_use_lmtt_amt'] = out_data['repl_use_lmtt_amt']
    return_data['out_use_pos_repl_fin'] = out_data['use_pos_repl_fin']
    return_data['out_crd_grnta_ch'] = out_data['crd_grnta_ch']
    return_data['out_crd_grnta_repl'] = out_data['crd_grnta_repl']
    return_data['out_crd_grnt_ch'] = out_data['crd_grnt_ch']
    return_data['out_crd_grnt_repl'] = out_data['crd_grnt_repl']
    return_data['out_uncla'] = out_data['uncla']
    return_data['out_ls_grnt_reu_gold'] = out_data['ls_grnt_reu_gold']
    return_data['out_20ord_alow_amt'] = out_data['20ord_alow_amt']
    return_data['out_30ord_alow_amt'] = out_data['30ord_alow_amt']
    return_data['out_40ord_alow_amt'] = out_data['40ord_alow_amt']
    return_data['out_50ord_alow_amt'] = out_data['50ord_alow_amt']
    return_data['out_60ord_alow_amt'] = out_data['60ord_alow_amt']
    return_data['out_100ord_alow_amt'] = out_data['100ord_alow_amt']
    return_data['out_tdy_crd_rpya_loss_amt'] = out_data['tdy_crd_rpya_loss_amt']
    return_data['out_pred_crd_rpya_loss_amt'] = out_data['pred_crd_rpya_loss_amt']
    return_data['out_tdy_ls_rpya_loss_repl_profa'] = out_data['tdy_ls_rpya_loss_repl_profa']
    return_data['out_pred_ls_rpya_loss_repl_profa'] = out_data['pred_ls_rpya_loss_repl_profa']
    return_data['out_evlt_repl_amt_spg_use_skip'] = out_data['evlt_repl_amt_spg_use_skip']
    return_data['out_evlt_repl_rt'] = out_data['evlt_repl_rt']
    return_data['out_crd_repl_profa'] = out_data['crd_repl_profa']
    return_data['out_ch_ord_repl_profa'] = out_data['ch_ord_repl_profa']
    return_data['out_crd_ord_repl_profa'] = out_data['crd_ord_repl_profa']
    return_data['out_crd_repl_conv_gold'] = out_data['crd_repl_conv_gold']
    return_data['out_repl_alowa'] = out_data['repl_alowa']
    return_data['out_repl_alowa_2'] = out_data['repl_alowa_2']
    return_data['out_ch_repl_lck_gold'] = out_data['ch_repl_lck_gold']
    return_data['out_crd_repl_lck_gold'] = out_data['crd_repl_lck_gold']
    return_data['out_ch_ord_alow_repla'] = out_data['ch_ord_alow_repla']
    return_data['out_crd_ord_alow_repla'] = out_data['crd_ord_alow_repla']
    return_data['out_d2vexct_entr'] = out_data['d2vexct_entr']
    return_data['out_d2ch_ord_alow_amt'] = out_data['d2ch_ord_alow_amt']
    
    return return_data

  def get_kt00015(self, in_cont_yn: str, in_next_key: str, in_strt_dt: str, in_end_dt: str, in_tp: str, in_stk_cd: str, in_crnc_cd: str, in_gds_tp: str, in_frgn_stex_code: str, in_dmst_stex_tp: str):
    """
    위탁종합거래내역요청
    메뉴 위치 : 국내주식 > 계좌 > 위탁종합거래내역요청(kt00015)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_strt_dt (str(8)): 시작일자(필수)
      in_end_dt (str(8)): 종료일자(필수)
      in_tp (str(1)): 구분(필수) 0:전체,1:입출금,2:입출고,3:매매,4:매수,5:매도,6:입금,7:출금,A:예탁담보대출입금,B:매도담보대출입금,C:현금상환(융자,담보상환),F:환전,M:입출금+환전,G:외화매수,H:외화매도,I:환전정산입금,J:환전정산출금
      in_stk_cd (str(12)): 종목코드
      in_crnc_cd (str(3)): 통화코드
      in_gds_tp (str(1)): 상품구분(필수) 0:전체, 1:국내주식, 2:수익증권, 3:해외주식, 4:금융상품
      in_frgn_stex_code (str(10)): 해외거래소코드
      in_dmst_stex_tp (str(6)): 국내거래소구분(필수) %:(전체),KRX:한국거래소,NXT:넥스트트레이드
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_trst_ovrl_trde_prps_array (list): 위탁종합거래내역배열
        - trde_dt (str(8)): 거래일자
        - trde_no (str(9)): 거래번호
        - rmrk_nm (str(60)): 적요명
        - crd_deal_tp_nm (str(20)): 신용거래구분명
        - exct_amt (str(15)): 정산금액
        - loan_amt_rpya (str(15)): 대출금상환
        - fc_trde_amt (str(15)): 거래금액(외)
        - fc_exct_amt (str(15)): 정산금액(외)
        - entra_remn (str(15)): 예수금잔고
        - crnc_cd (str(3)): 통화코드
        - trde_ocr_tp (str(2)): 거래종류구분. 1:입출금, 2:펀드, 3:ELS, 4:채권, 5:해외채권, 6:외화RP, 7:외화발행어음
        - trde_kind_nm (str(20)): 거래종류명
        - stk_nm (str(40)): 종목명
        - trde_amt (str(15)): 거래금액
        - trde_agri_tax (str(15)): 거래및농특세
        - rpy_diffa (str(15)): 상환차금
        - fc_trde_tax (str(15)): 거래세(외)
        - dly_sum (str(15)): 연체합
        - fc_entra (str(15)): 외화예수금잔고
        - mdia_tp_nm (str(20)): 매체구분명
        - io_tp (str(1)): 입출구분
        - io_tp_nm (str(10)): 입출구분명
        - orig_deal_no (str(9)): 원거래번호
        - stk_cd (str(12)): 종목코드
        - trde_qty_jwa_cnt (str(30)): 거래수량/좌수
        - cmsn (str(15)): 수수료
        - int_ls_usfe (str(15)): 이자/대주이용
        - fc_cmsn (str(15)): 수수료(외)
        - fc_dly_sum (str(15)): 연체합(외)
        - vlbl_nowrm (str(30)): 유가금잔
        - proc_tm (str(111)): 처리시간
        - isin_cd (str(12)): ISIN코드
        - stex_cd (str(10)): 거래소코드
        - stex_nm (str(20)): 거래소명
        - trde_unit (str(20)): 거래단가/환율
        - incm_resi_tax (str(15)): 소득/주민세
        - loan_dt (str(8)): 대출일
        - uncl_ocr (str(30)): 미수(원/주)
        - rpym_sum (str(30)): 변제합
        - cntr_dt (str(8)): 체결일
        - rcpy_no (str(20)): 출납번호
        - prcsr (str(20)): 처리자
        - proc_brch (str(20)): 처리점
        - trde_stle (str(40)): 매매형태
        - txon_base_pric (str(15)): 과세기준가
        - tax_sum_cmsn (str(15)): 세금수수료합
        - frgn_pay_txam (str(15)): 외국납부세액(외)
        - fc_uncl_ocr (str(15)): 미수(외)
        - rpym_sum_fr (str(30)): 변제합(외)
        - rcpmnyer (str(20)): 입금자
        - trde_prtc_tp (str(2)): 거래내역구분
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'kt00015',
    }
    params = {
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'tp': in_tp,
      'stk_cd': in_stk_cd,
      'crnc_cd': in_crnc_cd,
      'gds_tp': in_gds_tp,
      'frgn_stex_code': in_frgn_stex_code,
      'dmst_stex_tp': in_dmst_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_trst_ovrl_trde_prps_array'] = out_data['trst_ovrl_trde_prps_array']
    
    return return_data

  def get_kt00016(self, in_cont_yn: str, in_next_key: str, in_fr_dt: str, in_to_dt: str):
    """
    일별계좌수익률상세현황요청
    메뉴 위치 : 국내주식 > 계좌 > 일별계좌수익률상세현황요청(kt00016)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_fr_dt (str(8)): 평가시작일(필수)
      in_to_dt (str(8)): 평가종료일(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_mang_empno (str(8)): 관리사원번호
      out_mngr_nm (str(8)): 관리자명
      out_dept_nm (str(30)): 관리자지점
      out_entr_fr (str(30)): 예수금_초
      out_entr_to (str(12)): 예수금_말
      out_scrt_evlt_amt_fr (str(12)): 유가증권평가금액_초
      out_scrt_evlt_amt_to (str(12)): 유가증권평가금액_말
      out_ls_grnt_fr (str(12)): 대주담보금_초
      out_ls_grnt_to (str(12)): 대주담보금_말
      out_crd_loan_fr (str(12)): 신용융자금_초
      out_crd_loan_to (str(12)): 신용융자금_말
      out_ch_uncla_fr (str(12)): 현금미수금_초
      out_ch_uncla_to (str(12)): 현금미수금_말
      out_krw_asgna_fr (str(12)): 원화대용금_초
      out_krw_asgna_to (str(12)): 원화대용금_말
      out_ls_evlta_fr (str(12)): 대주평가금_초
      out_ls_evlta_to (str(12)): 대주평가금_말
      out_rght_evlta_fr (str(12)): 권리평가금_초
      out_rght_evlta_to (str(12)): 권리평가금_말
      out_loan_amt_fr (str(12)): 대출금_초
      out_loan_amt_to (str(12)): 대출금_말
      out_etc_loana_fr (str(12)): 기타대여금_초
      out_etc_loana_to (str(12)): 기타대여금_말
      out_crd_int_npay_gold_fr (str(12)): 신용이자미납금_초
      out_crd_int_npay_gold_to (str(12)): 신용이자미납금_말
      out_crd_int_fr (str(12)): 신용이자_초
      out_crd_int_to (str(12)): 신용이자_말
      out_tot_amt_fr (str(12)): 순자산액계_초
      out_tot_amt_to (str(12)): 순자산액계_말
      out_invt_bsamt (str(12)): 투자원금평잔
      out_evltv_prft (str(12)): 평가손익
      out_prft_rt (str(12)): 수익률
      out_tern_rt (str(12)): 회전율
      out_termin_tot_trns (str(12)): 기간내총입금
      out_termin_tot_pymn (str(12)): 기간내총출금
      out_termin_tot_inq (str(12)): 기간내총입고
      out_termin_tot_outq (str(12)): 기간내총출고
      out_futr_repl_sella (str(12)): 선물대용매도금액
      out_trst_repl_sella (str(12)): 위탁대용매도금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_fr_dt or in_fr_dt == '':
      in_fr_dt = format_datetime('%Y%m%d')
    
    if not in_to_dt or in_to_dt == '':
      in_to_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'kt00016',
    }
    params = {
      'fr_dt': in_fr_dt,
      'to_dt': in_to_dt,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_mang_empno'] = out_data['mang_empno']
    return_data['out_mngr_nm'] = out_data['mngr_nm']
    return_data['out_dept_nm'] = out_data['dept_nm']
    return_data['out_entr_fr'] = out_data['entr_fr']
    return_data['out_entr_to'] = out_data['entr_to']
    return_data['out_scrt_evlt_amt_fr'] = out_data['scrt_evlt_amt_fr']
    return_data['out_scrt_evlt_amt_to'] = out_data['scrt_evlt_amt_to']
    return_data['out_ls_grnt_fr'] = out_data['ls_grnt_fr']
    return_data['out_ls_grnt_to'] = out_data['ls_grnt_to']
    return_data['out_crd_loan_fr'] = out_data['crd_loan_fr']
    return_data['out_crd_loan_to'] = out_data['crd_loan_to']
    return_data['out_ch_uncla_fr'] = out_data['ch_uncla_fr']
    return_data['out_ch_uncla_to'] = out_data['ch_uncla_to']
    return_data['out_krw_asgna_fr'] = out_data['krw_asgna_fr']
    return_data['out_krw_asgna_to'] = out_data['krw_asgna_to']
    return_data['out_ls_evlta_fr'] = out_data['ls_evlta_fr']
    return_data['out_ls_evlta_to'] = out_data['ls_evlta_to']
    return_data['out_rght_evlta_fr'] = out_data['rght_evlta_fr']
    return_data['out_rght_evlta_to'] = out_data['rght_evlta_to']
    return_data['out_loan_amt_fr'] = out_data['loan_amt_fr']
    return_data['out_loan_amt_to'] = out_data['loan_amt_to']
    return_data['out_etc_loana_fr'] = out_data['etc_loana_fr']
    return_data['out_etc_loana_to'] = out_data['etc_loana_to']
    return_data['out_crd_int_npay_gold_fr'] = out_data['crd_int_npay_gold_fr']
    return_data['out_crd_int_npay_gold_to'] = out_data['crd_int_npay_gold_to']
    return_data['out_crd_int_fr'] = out_data['crd_int_fr']
    return_data['out_crd_int_to'] = out_data['crd_int_to']
    return_data['out_tot_amt_fr'] = out_data['tot_amt_fr']
    return_data['out_tot_amt_to'] = out_data['tot_amt_to']
    return_data['out_invt_bsamt'] = out_data['invt_bsamt']
    return_data['out_evltv_prft'] = out_data['evltv_prft']
    return_data['out_prft_rt'] = out_data['prft_rt']
    return_data['out_tern_rt'] = out_data['tern_rt']
    return_data['out_termin_tot_trns'] = out_data['termin_tot_trns']
    return_data['out_termin_tot_pymn'] = out_data['termin_tot_pymn']
    return_data['out_termin_tot_inq'] = out_data['termin_tot_inq']
    return_data['out_termin_tot_outq'] = out_data['termin_tot_outq']
    return_data['out_futr_repl_sella'] = out_data['futr_repl_sella']
    return_data['out_trst_repl_sella'] = out_data['trst_repl_sella']
    
    return return_data

  def get_kt00017(self, in_cont_yn: str, in_next_key: str):
    """
    계좌별당일현황요청
    메뉴 위치 : 국내주식 > 계좌 > 계좌별당일현황요청(kt00017)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_d2_entra (str(12)): D+2추정예수금
      out_crd_int_npay_gold (str(12)): 신용이자미납금
      out_etc_loana (str(12)): 기타대여금
      out_gnrl_stk_evlt_amt_d2 (str(12)): 일반주식평가금액D+2
      out_dpst_grnt_use_amt_d2 (str(12)): 예탁담보대출금D+2
      out_crd_stk_evlt_amt_d2 (str(12)): 예탁담보주식평가금액D+2
      out_crd_loan_d2 (str(12)): 신용융자금D+2
      out_crd_loan_evlta_d2 (str(12)): 신용융자평가금D+2
      out_crd_ls_grnt_d2 (str(12)): 신용대주담보금D+2
      out_crd_ls_evlta_d2 (str(12)): 신용대주평가금D+2
      out_ina_amt (str(12)): 입금금액
      out_outa (str(12)): 출금금액
      out_inq_amt (str(12)): 입고금액
      out_outq_amt (str(12)): 출고금액
      out_sell_amt (str(12)): 매도금액
      out_buy_amt (str(12)): 매수금액
      out_cmsn (str(12)): 수수료
      out_tax (str(12)): 세금
      out_stk_pur_cptal_loan_amt (str(12)): 주식매입자금대출금
      out_rp_evlt_amt (str(12)): RP평가금액
      out_bd_evlt_amt (str(12)): 채권평가금액
      out_elsevlt_amt (str(12)): ELS평가금액
      out_crd_int_amt (str(12)): 신용이자금액
      out_sel_prica_grnt_loan_int_amt_amt (str(12)): 매도대금담보대출이자금액
      out_dvida_amt (str(12)): 배당금액
    
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
      'api-id': 'kt00017',
    }
    params = {
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_d2_entra'] = out_data['d2_entra']
    return_data['out_crd_int_npay_gold'] = out_data['crd_int_npay_gold']
    return_data['out_etc_loana'] = out_data['etc_loana']
    return_data['out_gnrl_stk_evlt_amt_d2'] = out_data['gnrl_stk_evlt_amt_d2']
    return_data['out_dpst_grnt_use_amt_d2'] = out_data['dpst_grnt_use_amt_d2']
    return_data['out_crd_stk_evlt_amt_d2'] = out_data['crd_stk_evlt_amt_d2']
    return_data['out_crd_loan_d2'] = out_data['crd_loan_d2']
    return_data['out_crd_loan_evlta_d2'] = out_data['crd_loan_evlta_d2']
    return_data['out_crd_ls_grnt_d2'] = out_data['crd_ls_grnt_d2']
    return_data['out_crd_ls_evlta_d2'] = out_data['crd_ls_evlta_d2']
    return_data['out_ina_amt'] = out_data['ina_amt']
    return_data['out_outa'] = out_data['outa']
    return_data['out_inq_amt'] = out_data['inq_amt']
    return_data['out_outq_amt'] = out_data['outq_amt']
    return_data['out_sell_amt'] = out_data['sell_amt']
    return_data['out_buy_amt'] = out_data['buy_amt']
    return_data['out_cmsn'] = out_data['cmsn']
    return_data['out_tax'] = out_data['tax']
    return_data['out_stk_pur_cptal_loan_amt'] = out_data['stk_pur_cptal_loan_amt']
    return_data['out_rp_evlt_amt'] = out_data['rp_evlt_amt']
    return_data['out_bd_evlt_amt'] = out_data['bd_evlt_amt']
    return_data['out_elsevlt_amt'] = out_data['elsevlt_amt']
    return_data['out_crd_int_amt'] = out_data['crd_int_amt']
    return_data['out_sel_prica_grnt_loan_int_amt_amt'] = out_data['sel_prica_grnt_loan_int_amt_amt']
    return_data['out_dvida_amt'] = out_data['dvida_amt']
    
    return return_data

  def get_kt00018(self, in_cont_yn: str, in_next_key: str, in_qry_tp: str, in_dmst_stex_tp: str):
    """
    계좌평가잔고내역요청
    메뉴 위치 : 국내주식 > 계좌 > 계좌평가잔고내역요청(kt00018)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_qry_tp (str(1)): 조회구분(필수) 1:합산, 2:개별
      in_dmst_stex_tp (str(6)): 국내거래소구분(필수) KRX:한국거래소,NXT:넥스트트레이드
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tot_pur_amt (str(15)): 총매입금액
      out_tot_evlt_amt (str(15)): 총평가금액
      out_tot_evlt_pl (str(15)): 총평가손익금액
      out_tot_prft_rt (str(12)): 총수익률(%)
      out_prsm_dpst_aset_amt (str(15)): 추정예탁자산
      out_tot_loan_amt (str(15)): 총대출금
      out_tot_crd_loan_amt (str(15)): 총융자금액
      out_tot_crd_ls_amt (str(15)): 총대주금액
      out_acnt_evlt_remn_indv_tot (list): 계좌평가잔고개별합산
        - stk_cd (str(12)): 종목번호
        - stk_nm (str(40)): 종목명
        - evltv_prft (str(15)): 평가손익
        - prft_rt (str(12)): 수익률(%)
        - pur_pric (str(15)): 매입가
        - pred_close_pric (str(12)): 전일종가
        - rmnd_qty (str(15)): 보유수량
        - trde_able_qty (str(15)): 매매가능수량
        - cur_prc (str(12)): 현재가
        - pred_buyq (str(15)): 전일매수수량
        - pred_sellq (str(15)): 전일매도수량
        - tdy_buyq (str(15)): 금일매수수량
        - tdy_sellq (str(15)): 금일매도수량
        - pur_amt (str(15)): 매입금액
        - pur_cmsn (str(15)): 매입수수료
        - evlt_amt (str(15)): 평가금액
        - sell_cmsn (str(15)): 평가수수료
        - tax (str(15)): 세금
        - sum_cmsn (str(15)): 수수료합. 매입수수료 + 평가수수료
        - poss_rt (str(12)): 보유비중(%)
        - crd_tp (str(2)): 신용구분
        - crd_tp_nm (str(4)): 신용구분명
        - crd_loan_dt (str(8)): 대출일
    
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
      'api-id': 'kt00018',
    }
    params = {
      'qry_tp': in_qry_tp,
      'dmst_stex_tp': in_dmst_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_tot_pur_amt'] = out_data['tot_pur_amt']
    return_data['out_tot_evlt_amt'] = out_data['tot_evlt_amt']
    return_data['out_tot_evlt_pl'] = out_data['tot_evlt_pl']
    return_data['out_tot_prft_rt'] = out_data['tot_prft_rt']
    return_data['out_prsm_dpst_aset_amt'] = out_data['prsm_dpst_aset_amt']
    return_data['out_tot_loan_amt'] = out_data['tot_loan_amt']
    return_data['out_tot_crd_loan_amt'] = out_data['tot_crd_loan_amt']
    return_data['out_tot_crd_ls_amt'] = out_data['tot_crd_ls_amt']
    return_data['out_acnt_evlt_remn_indv_tot'] = out_data['acnt_evlt_remn_indv_tot']
    
    return return_data

  def get_kt50020(self, in_cont_yn: str, in_next_key: str):
    """
    금현물 잔고확인
    메뉴 위치 : 국내주식 > 계좌 > 금현물 잔고확인(kt50020)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tot_entr (str(12)): 예수금
      out_net_entr (str(12)): 추정예수금
      out_tot_est_amt (str(12)): 잔고평가액
      out_net_amt (str(12)): 예탁자산평가액
      out_tot_book_amt2 (str(12)): 총매입금액
      out_tot_dep_amt (str(12)): 추정예탁자산
      out_paym_alowa (str(12)): 출금가능금액
      out_pl_amt (str(12)): 실현손익
      out_gold_acnt_evlt_prst (list): 금현물계좌평가현황
        - stk_cd (str(30)): 종목코드
        - stk_nm (str(12)): 종목명
        - real_qty (str(12)): 보유수량
        - avg_prc (str(12)): 평균단가
        - cur_prc (str(12)): 현재가
        - est_amt (str(12)): 평가금액
        - est_lspft (str(12)): 손익금액
        - est_ratio (str(12)): 손익율
        - cmsn (str(12)): 수수료
        - vlad_tax (str(12)): 부가가치세
        - book_amt2 (str(12)): 매입금액
        - pl_prch_prc (str(12)): 손익분기매입가
        - qty (str(12)): 결제잔고
        - buy_qty (str(12)): 매수수량
        - sell_qty (str(12)): 매도수량
        - able_qty (str(12)): 가능수량
    
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
      'api-id': 'kt50020',
    }
    params = {
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_tot_entr'] = out_data['tot_entr']
    return_data['out_net_entr'] = out_data['net_entr']
    return_data['out_tot_est_amt'] = out_data['tot_est_amt']
    return_data['out_net_amt'] = out_data['net_amt']
    return_data['out_tot_book_amt2'] = out_data['tot_book_amt2']
    return_data['out_tot_dep_amt'] = out_data['tot_dep_amt']
    return_data['out_paym_alowa'] = out_data['paym_alowa']
    return_data['out_pl_amt'] = out_data['pl_amt']
    return_data['out_gold_acnt_evlt_prst'] = out_data['gold_acnt_evlt_prst']
    
    return return_data

  def get_kt50021(self, in_cont_yn: str, in_next_key: str):
    """
    금현물 예수금
    메뉴 위치 : 국내주식 > 계좌 > 금현물 예수금(kt50021)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_entra (str(15)): 예수금
      out_profa_ch (str(15)): 증거금현금
      out_chck_ina_amt (str(15)): 수표입금액
      out_etc_loan (str(15)): 기타대여금
      out_etc_loan_dlfe (str(15)): 기타대여금연체료
      out_etc_loan_tot (str(15)): 기타대여금합계
      out_prsm_entra (str(15)): 추정예수금
      out_buy_exct_amt (str(15)): 매수정산금
      out_sell_exct_amt (str(15)): 매도정산금
      out_sell_buy_exct_amt (str(15)): 매도매수정산금
      out_dly_amt (str(15)): 미수변제소요금
      out_prsm_pymn_alow_amt (str(15)): 추정출금가능금액
      out_pymn_alow_amt (str(15)): 출금가능금액
      out_ord_alow_amt (str(15)): 주문가능금액
    
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
      'api-id': 'kt50021',
    }
    params = {
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_entra'] = out_data['entra']
    return_data['out_profa_ch'] = out_data['profa_ch']
    return_data['out_chck_ina_amt'] = out_data['chck_ina_amt']
    return_data['out_etc_loan'] = out_data['etc_loan']
    return_data['out_etc_loan_dlfe'] = out_data['etc_loan_dlfe']
    return_data['out_etc_loan_tot'] = out_data['etc_loan_tot']
    return_data['out_prsm_entra'] = out_data['prsm_entra']
    return_data['out_buy_exct_amt'] = out_data['buy_exct_amt']
    return_data['out_sell_exct_amt'] = out_data['sell_exct_amt']
    return_data['out_sell_buy_exct_amt'] = out_data['sell_buy_exct_amt']
    return_data['out_dly_amt'] = out_data['dly_amt']
    return_data['out_prsm_pymn_alow_amt'] = out_data['prsm_pymn_alow_amt']
    return_data['out_pymn_alow_amt'] = out_data['pymn_alow_amt']
    return_data['out_ord_alow_amt'] = out_data['ord_alow_amt']
    
    return return_data

  def get_kt50030(self, in_cont_yn: str, in_next_key: str, in_ord_dt: str, in_qry_tp: str, in_mrkt_deal_tp: str, in_stk_bond_tp: str, in_slby_tp: str, in_stk_cd: str, in_fr_ord_no: str, in_dmst_stex_tp: str):
    """
    금현물 주문체결전체조회
    메뉴 위치 : 국내주식 > 계좌 > 금현물 주문체결전체조회(kt50030)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_ord_dt (str(8)): 주문일자(필수)
      in_qry_tp (str(1)): 조회구분 1: 주문순, 2: 역순
      in_mrkt_deal_tp (str(1)): 시장구분(필수)
      in_stk_bond_tp (str(1)): 주식채권구분(필수) 0:전체, 1:주식, 2:채권
      in_slby_tp (str(1)): 매도수구분(필수) 0:전체, 1:매도, 2:매수
      in_stk_cd (str(12)): 종목코드
      in_fr_ord_no (str(7)): 시작주문번호
      in_dmst_stex_tp (str(6)): 국내거래소구분 %:(전체), KRX, NXT, SOR
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_acnt_ord_cntr_prst (list): 계좌별주문체결현황
        - stk_bond_tp (str(1)): 주식채권구분
        - ord_no (str(7)): 주문번호
        - stk_cd (str(12)): 상품코드
        - trde_tp (str(12)): 매매구분
        - io_tp_nm (str(20)): 주문유형구분
        - ord_qty (str(10)): 주문수량
        - ord_uv (str(10)): 주문단가
        - cnfm_qty (str(10)): 확인수량
        - data_send_end_tp (str(12)): 접수구분
        - mrkt_deal_tp (str(1)): 시장구분
        - rsrv_tp (str(4)): 예약/반대여부
        - orig_ord_no (str(7)): 원주문번호
        - stk_nm (str(40)): 종목명
        - dcd_tp_nm (str(4)): 결제구분
        - crd_deal_tp (str(20)): 신용거래구분
        - cntr_qty (str(10)): 체결수량
        - cntr_uv (str(10)): 체결단가
        - ord_remnq (str(10)): 미체결수량
        - comm_ord_tp (str(10)): 통신구분
        - mdfy_cncl_tp (str(20)): 정정취소구분
        - dmst_stex_tp (str(6)): 국내거래소구분
        - cond_uv (str(10)): 스톱가
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_ord_dt or in_ord_dt == '':
      in_ord_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'kt50030',
    }
    params = {
      'ord_dt': in_ord_dt,
      'qry_tp': in_qry_tp,
      'mrkt_deal_tp': in_mrkt_deal_tp,
      'stk_bond_tp': in_stk_bond_tp,
      'slby_tp': in_slby_tp,
      'stk_cd': in_stk_cd,
      'fr_ord_no': in_fr_ord_no,
      'dmst_stex_tp': in_dmst_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_acnt_ord_cntr_prst'] = out_data['acnt_ord_cntr_prst']
    
    return return_data

  def get_kt50031(self, in_cont_yn: str, in_next_key: str, in_ord_dt: str, in_qry_tp: str, in_stk_bond_tp: str, in_sell_tp: str, in_stk_cd: str, in_fr_ord_no: str, in_dmst_stex_tp: str):
    """
    금현물 주문체결조회
    메뉴 위치 : 국내주식 > 계좌 > 금현물 주문체결조회(kt50031)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_ord_dt (str(8)): 주문일자 YYYYMMDD
      in_qry_tp (str(1)): 조회구분(필수) 1:주문순, 2:역순, 3:미체결, 4:체결내역만
      in_stk_bond_tp (str(1)): 주식채권구분(필수) 0:전체, 1:주식, 2:채권
      in_sell_tp (str(1)): 매도수구분(필수) 0:전체, 1:매도, 2:매수
      in_stk_cd (str(12)): 종목코드 공백허용 (공백일때 전체종목)
      in_fr_ord_no (str(7)): 시작주문번호 공백허용 (공백일때 전체주문)
      in_dmst_stex_tp (str(6)): 국내거래소구분(필수) %:(전체),KRX:한국거래소,NXT:넥스트트레이드,SOR:최선주문집행
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_acnt_ord_cntr_prps_dtl (list): 계좌별주문체결내역상세
        - ord_no (str(7)): 주문번호
        - stk_cd (str(12)): 종목번호
        - trde_tp (str(20)): 매매구분
        - crd_tp (str(20)): 신용구분
        - ord_qty (str(10)): 주문수량
        - ord_uv (str(10)): 주문단가
        - cnfm_qty (str(10)): 확인수량
        - acpt_tp (str(20)): 접수구분
        - rsrv_tp (str(20)): 반대여부
        - ord_tm (str(8)): 주문시간
        - ori_ord (str(7)): 원주문
        - stk_nm (str(40)): 종목명
        - io_tp_nm (str(20)): 주문구분
        - loan_dt (str(8)): 대출일
        - cntr_qty (str(10)): 체결수량
        - cntr_uv (str(10)): 체결단가
        - ord_remnq (str(10)): 주문잔량
        - comm_ord_tp (str(20)): 통신구분
        - mdfy_cncl (str(20)): 정정취소
        - cnfm_tm (str(8)): 확인시간
        - dmst_stex_tp (str(8)): 국내거래소구분
        - cond_uv (str(10)): 스톱가
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_ord_dt or in_ord_dt == '':
      in_ord_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'kt50031',
    }
    params = {
      'ord_dt': in_ord_dt,
      'qry_tp': in_qry_tp,
      'stk_bond_tp': in_stk_bond_tp,
      'sell_tp': in_sell_tp,
      'stk_cd': in_stk_cd,
      'fr_ord_no': in_fr_ord_no,
      'dmst_stex_tp': in_dmst_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_acnt_ord_cntr_prps_dtl'] = out_data['acnt_ord_cntr_prps_dtl']
    
    return return_data

  def get_kt50032(self, in_cont_yn: str, in_next_key: str, in_strt_dt: str, in_end_dt: str, in_tp: str, in_stk_cd: str):
    """
    금현물 거래내역조회
    메뉴 위치 : 국내주식 > 계좌 > 금현물 거래내역조회(kt50032)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_strt_dt (str(8)): 시작일자
      in_end_dt (str(8)): 종료일자
      in_tp (str(1)): 구분 0:전체, 1:입출금, 2:출고, 3:매매, 4:매수, 5:매도, 6:입금, 7:출금
      in_stk_cd (str(12)): 종목코드
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_acnt_print (str(62)): 계좌번호. 계좌번호 출력용
      out_gold_trde_hist (list): 금현물거래내역
        - deal_dt (str): 거래일자
        - deal_no (str): 거래번호
        - rmrk_nm (str): 적요명
        - deal_qty (str): 거래수량
        - gold_spot_vat (str): 금현물부가가치세
        - exct_amt (str): 정산금액
        - dly_sum (str): 연체합
        - entra_remn (str): 예수금잔고
        - mdia_nm (str): 메체구분명
        - orig_deal_no (str): 원거래번호
        - stk_nm (str): 종목명
        - uv_exrt (str): 거래단가
        - cmsn (str): 수수료
        - uncl_ocr (str): 미수(원/g)
        - rpym_sum (str): 변제합
        - spot_remn (str): 현물잔고
        - proc_time (str): 처리시간
        - rcpy_no (str): 출납번호
        - stk_cd (str): 종목코드
        - deal_amt (str): 거래금액
        - tax_tot_amt (str): 소득/주민세
        - cntr_dt (str): 체결일
        - proc_brch_nm (str): 처리점
        - prcsr (str): 처리자
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'kt50032',
    }
    params = {
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'tp': in_tp,
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_acnt_print'] = out_data['acnt_print']
    return_data['out_gold_trde_hist'] = out_data['gold_trde_hist']
    
    return return_data

  def get_kt50075(self, in_cont_yn: str, in_next_key: str, in_ord_dt: str, in_qry_tp: str, in_mrkt_deal_tp: str, in_stk_bond_tp: str, in_sell_tp: str, in_stk_cd: str, in_fr_ord_no: str, in_dmst_stex_tp: str):
    """
    금현물 미체결조회
    메뉴 위치 : 국내주식 > 계좌 > 금현물 미체결조회(kt50075)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_ord_dt (str(8)): 주문일자(필수)
      in_qry_tp (str(1)): 조회구분 1: 주문순, 2: 역순
      in_mrkt_deal_tp (str(1)): 시장구분(필수)
      in_stk_bond_tp (str(1)): 주식채권구분(필수) 0:전체, 1:주식, 2:채권
      in_sell_tp (str(1)): 매도수구분(필수) 0:전체, 1:매도, 2:매수
      in_stk_cd (str(12)): 종목코드
      in_fr_ord_no (str(7)): 시작주문번호
      in_dmst_stex_tp (str(6)): 국내거래소구분 %:(전체), KRX, NXT, SOR
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_acnt_ord_oso_prst (list): 계좌별주문미체결현황
        - stk_bond_tp (str(1)): 주식채권구분
        - ord_no (str(7)): 주문번호
        - stk_cd (str(12)): 상품코드
        - trde_tp (str(12)): 매매구분
        - io_tp_nm (str(20)): 주문유형구분
        - ord_qty (str(10)): 주문수량
        - ord_uv (str(10)): 주문단가
        - cnfm_qty (str(10)): 확인수량
        - data_send_end_tp (str(12)): 접수구분
        - mrkt_deal_tp (str(1)): 시장구분
        - rsrv_tp (str(4)): 예약/반대여부
        - orig_ord_no (str(7)): 원주문번호
        - stk_nm (str(40)): 종목명
        - dcd_tp_nm (str(4)): 결제구분
        - crd_deal_tp (str(20)): 신용거래구분
        - cntr_qty (str(10)): 체결수량
        - cntr_uv (str(10)): 체결단가
        - ord_remnq (str(10)): 미체결수량
        - comm_ord_tp (str(10)): 통신구분
        - mdfy_cncl_tp (str(20)): 정정취소구분
        - dmst_stex_tp (str(6)): 국내거래소구분
        - cond_uv (str(10)): 스톱가
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_ord_dt or in_ord_dt == '':
      in_ord_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'kt50075',
    }
    params = {
      'ord_dt': in_ord_dt,
      'qry_tp': in_qry_tp,
      'mrkt_deal_tp': in_mrkt_deal_tp,
      'stk_bond_tp': in_stk_bond_tp,
      'sell_tp': in_sell_tp,
      'stk_cd': in_stk_cd,
      'fr_ord_no': in_fr_ord_no,
      'dmst_stex_tp': in_dmst_stex_tp,
    }
    url = '/api/dostk/acnt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_acnt_ord_oso_prst'] = out_data['acnt_ord_oso_prst']
    
    return return_data

  def get_ka10004(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    주식호가요청
    메뉴 위치 : 국내주식 > 시세 > 주식호가요청(ka10004)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_bid_req_base_tm (str(20)): 호가잔량기준시간. 호가시간
      out_sel_10th_pre_req_pre (str(20)): 매도10차선잔량대비. 매도호가직전대비10
      out_sel_10th_pre_req (str(20)): 매도10차선잔량. 매도호가수량10
      out_sel_10th_pre_bid (str(20)): 매도10차선호가. 매도호가10
      out_sel_9th_pre_req_pre (str(20)): 매도9차선잔량대비. 매도호가직전대비9
      out_sel_9th_pre_req (str(20)): 매도9차선잔량. 매도호가수량9
      out_sel_9th_pre_bid (str(20)): 매도9차선호가. 매도호가9
      out_sel_8th_pre_req_pre (str(20)): 매도8차선잔량대비. 매도호가직전대비8
      out_sel_8th_pre_req (str(20)): 매도8차선잔량. 매도호가수량8
      out_sel_8th_pre_bid (str(20)): 매도8차선호가. 매도호가8
      out_sel_7th_pre_req_pre (str(20)): 매도7차선잔량대비. 매도호가직전대비7
      out_sel_7th_pre_req (str(20)): 매도7차선잔량. 매도호가수량7
      out_sel_7th_pre_bid (str(20)): 매도7차선호가. 매도호가7
      out_sel_6th_pre_req_pre (str(20)): 매도6차선잔량대비. 매도호가직전대비6
      out_sel_6th_pre_req (str(20)): 매도6차선잔량. 매도호가수량6
      out_sel_6th_pre_bid (str(20)): 매도6차선호가. 매도호가6
      out_sel_5th_pre_req_pre (str(20)): 매도5차선잔량대비. 매도호가직전대비5
      out_sel_5th_pre_req (str(20)): 매도5차선잔량. 매도호가수량5
      out_sel_5th_pre_bid (str(20)): 매도5차선호가. 매도호가5
      out_sel_4th_pre_req_pre (str(20)): 매도4차선잔량대비. 매도호가직전대비4
      out_sel_4th_pre_req (str(20)): 매도4차선잔량. 매도호가수량4
      out_sel_4th_pre_bid (str(20)): 매도4차선호가. 매도호가4
      out_sel_3th_pre_req_pre (str(20)): 매도3차선잔량대비. 매도호가직전대비3
      out_sel_3th_pre_req (str(20)): 매도3차선잔량. 매도호가수량3
      out_sel_3th_pre_bid (str(20)): 매도3차선호가. 매도호가3
      out_sel_2th_pre_req_pre (str(20)): 매도2차선잔량대비. 매도호가직전대비2
      out_sel_2th_pre_req (str(20)): 매도2차선잔량. 매도호가수량2
      out_sel_2th_pre_bid (str(20)): 매도2차선호가. 매도호가2
      out_sel_1th_pre_req_pre (str(20)): 매도1차선잔량대비. 매도호가직전대비1
      out_sel_fpr_req (str(20)): 매도최우선잔량. 매도호가수량1
      out_sel_fpr_bid (str(20)): 매도최우선호가. 매도호가1
      out_buy_fpr_bid (str(20)): 매수최우선호가. 매수호가1
      out_buy_fpr_req (str(20)): 매수최우선잔량. 매수호가수량1
      out_buy_1th_pre_req_pre (str(20)): 매수1차선잔량대비. 매수호가직전대비1
      out_buy_2th_pre_bid (str(20)): 매수2차선호가. 매수호가2
      out_buy_2th_pre_req (str(20)): 매수2차선잔량. 매수호가수량2
      out_buy_2th_pre_req_pre (str(20)): 매수2차선잔량대비. 매수호가직전대비2
      out_buy_3th_pre_bid (str(20)): 매수3차선호가. 매수호가3
      out_buy_3th_pre_req (str(20)): 매수3차선잔량. 매수호가수량3
      out_buy_3th_pre_req_pre (str(20)): 매수3차선잔량대비. 매수호가직전대비3
      out_buy_4th_pre_bid (str(20)): 매수4차선호가. 매수호가4
      out_buy_4th_pre_req (str(20)): 매수4차선잔량. 매수호가수량4
      out_buy_4th_pre_req_pre (str(20)): 매수4차선잔량대비. 매수호가직전대비4
      out_buy_5th_pre_bid (str(20)): 매수5차선호가. 매수호가5
      out_buy_5th_pre_req (str(20)): 매수5차선잔량. 매수호가수량5
      out_buy_5th_pre_req_pre (str(20)): 매수5차선잔량대비. 매수호가직전대비5
      out_buy_6th_pre_bid (str(20)): 매수6차선호가. 매수호가6
      out_buy_6th_pre_req (str(20)): 매수6차선잔량. 매수호가수량6
      out_buy_6th_pre_req_pre (str(20)): 매수6차선잔량대비. 매수호가직전대비6
      out_buy_7th_pre_bid (str(20)): 매수7차선호가. 매수호가7
      out_buy_7th_pre_req (str(20)): 매수7차선잔량. 매수호가수량7
      out_buy_7th_pre_req_pre (str(20)): 매수7차선잔량대비. 매수호가직전대비7
      out_buy_8th_pre_bid (str(20)): 매수8차선호가. 매수호가8
      out_buy_8th_pre_req (str(20)): 매수8차선잔량. 매수호가수량8
      out_buy_8th_pre_req_pre (str(20)): 매수8차선잔량대비. 매수호가직전대비8
      out_buy_9th_pre_bid (str(20)): 매수9차선호가. 매수호가9
      out_buy_9th_pre_req (str(20)): 매수9차선잔량. 매수호가수량9
      out_buy_9th_pre_req_pre (str(20)): 매수9차선잔량대비. 매수호가직전대비9
      out_buy_10th_pre_bid (str(20)): 매수10차선호가. 매수호가10
      out_buy_10th_pre_req (str(20)): 매수10차선잔량. 매수호가수량10
      out_buy_10th_pre_req_pre (str(20)): 매수10차선잔량대비. 매수호가직전대비10
      out_tot_sel_req_jub_pre (str(20)): 총매도잔량직전대비. 매도호가총잔량직전대비
      out_tot_sel_req (str(20)): 총매도잔량. 매도호가총잔량
      out_tot_buy_req (str(20)): 총매수잔량. 매수호가총잔량
      out_tot_buy_req_jub_pre (str(20)): 총매수잔량직전대비. 매수호가총잔량직전대비
      out_ovt_sel_req_pre (str(20)): 시간외매도잔량대비. 시간외 매도호가 총잔량 직전대비
      out_ovt_sel_req (str(20)): 시간외매도잔량. 시간외 매도호가 총잔량
      out_ovt_buy_req (str(20)): 시간외매수잔량. 시간외 매수호가 총잔량
      out_ovt_buy_req_pre (str(20)): 시간외매수잔량대비. 시간외 매수호가 총잔량 직전대비
    
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
      'api-id': 'ka10004',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_bid_req_base_tm'] = out_data['bid_req_base_tm']
    return_data['out_sel_10th_pre_req_pre'] = out_data['sel_10th_pre_req_pre']
    return_data['out_sel_10th_pre_req'] = out_data['sel_10th_pre_req']
    return_data['out_sel_10th_pre_bid'] = out_data['sel_10th_pre_bid']
    return_data['out_sel_9th_pre_req_pre'] = out_data['sel_9th_pre_req_pre']
    return_data['out_sel_9th_pre_req'] = out_data['sel_9th_pre_req']
    return_data['out_sel_9th_pre_bid'] = out_data['sel_9th_pre_bid']
    return_data['out_sel_8th_pre_req_pre'] = out_data['sel_8th_pre_req_pre']
    return_data['out_sel_8th_pre_req'] = out_data['sel_8th_pre_req']
    return_data['out_sel_8th_pre_bid'] = out_data['sel_8th_pre_bid']
    return_data['out_sel_7th_pre_req_pre'] = out_data['sel_7th_pre_req_pre']
    return_data['out_sel_7th_pre_req'] = out_data['sel_7th_pre_req']
    return_data['out_sel_7th_pre_bid'] = out_data['sel_7th_pre_bid']
    return_data['out_sel_6th_pre_req_pre'] = out_data['sel_6th_pre_req_pre']
    return_data['out_sel_6th_pre_req'] = out_data['sel_6th_pre_req']
    return_data['out_sel_6th_pre_bid'] = out_data['sel_6th_pre_bid']
    return_data['out_sel_5th_pre_req_pre'] = out_data['sel_5th_pre_req_pre']
    return_data['out_sel_5th_pre_req'] = out_data['sel_5th_pre_req']
    return_data['out_sel_5th_pre_bid'] = out_data['sel_5th_pre_bid']
    return_data['out_sel_4th_pre_req_pre'] = out_data['sel_4th_pre_req_pre']
    return_data['out_sel_4th_pre_req'] = out_data['sel_4th_pre_req']
    return_data['out_sel_4th_pre_bid'] = out_data['sel_4th_pre_bid']
    return_data['out_sel_3th_pre_req_pre'] = out_data['sel_3th_pre_req_pre']
    return_data['out_sel_3th_pre_req'] = out_data['sel_3th_pre_req']
    return_data['out_sel_3th_pre_bid'] = out_data['sel_3th_pre_bid']
    return_data['out_sel_2th_pre_req_pre'] = out_data['sel_2th_pre_req_pre']
    return_data['out_sel_2th_pre_req'] = out_data['sel_2th_pre_req']
    return_data['out_sel_2th_pre_bid'] = out_data['sel_2th_pre_bid']
    return_data['out_sel_1th_pre_req_pre'] = out_data['sel_1th_pre_req_pre']
    return_data['out_sel_fpr_req'] = out_data['sel_fpr_req']
    return_data['out_sel_fpr_bid'] = out_data['sel_fpr_bid']
    return_data['out_buy_fpr_bid'] = out_data['buy_fpr_bid']
    return_data['out_buy_fpr_req'] = out_data['buy_fpr_req']
    return_data['out_buy_1th_pre_req_pre'] = out_data['buy_1th_pre_req_pre']
    return_data['out_buy_2th_pre_bid'] = out_data['buy_2th_pre_bid']
    return_data['out_buy_2th_pre_req'] = out_data['buy_2th_pre_req']
    return_data['out_buy_2th_pre_req_pre'] = out_data['buy_2th_pre_req_pre']
    return_data['out_buy_3th_pre_bid'] = out_data['buy_3th_pre_bid']
    return_data['out_buy_3th_pre_req'] = out_data['buy_3th_pre_req']
    return_data['out_buy_3th_pre_req_pre'] = out_data['buy_3th_pre_req_pre']
    return_data['out_buy_4th_pre_bid'] = out_data['buy_4th_pre_bid']
    return_data['out_buy_4th_pre_req'] = out_data['buy_4th_pre_req']
    return_data['out_buy_4th_pre_req_pre'] = out_data['buy_4th_pre_req_pre']
    return_data['out_buy_5th_pre_bid'] = out_data['buy_5th_pre_bid']
    return_data['out_buy_5th_pre_req'] = out_data['buy_5th_pre_req']
    return_data['out_buy_5th_pre_req_pre'] = out_data['buy_5th_pre_req_pre']
    return_data['out_buy_6th_pre_bid'] = out_data['buy_6th_pre_bid']
    return_data['out_buy_6th_pre_req'] = out_data['buy_6th_pre_req']
    return_data['out_buy_6th_pre_req_pre'] = out_data['buy_6th_pre_req_pre']
    return_data['out_buy_7th_pre_bid'] = out_data['buy_7th_pre_bid']
    return_data['out_buy_7th_pre_req'] = out_data['buy_7th_pre_req']
    return_data['out_buy_7th_pre_req_pre'] = out_data['buy_7th_pre_req_pre']
    return_data['out_buy_8th_pre_bid'] = out_data['buy_8th_pre_bid']
    return_data['out_buy_8th_pre_req'] = out_data['buy_8th_pre_req']
    return_data['out_buy_8th_pre_req_pre'] = out_data['buy_8th_pre_req_pre']
    return_data['out_buy_9th_pre_bid'] = out_data['buy_9th_pre_bid']
    return_data['out_buy_9th_pre_req'] = out_data['buy_9th_pre_req']
    return_data['out_buy_9th_pre_req_pre'] = out_data['buy_9th_pre_req_pre']
    return_data['out_buy_10th_pre_bid'] = out_data['buy_10th_pre_bid']
    return_data['out_buy_10th_pre_req'] = out_data['buy_10th_pre_req']
    return_data['out_buy_10th_pre_req_pre'] = out_data['buy_10th_pre_req_pre']
    return_data['out_tot_sel_req_jub_pre'] = out_data['tot_sel_req_jub_pre']
    return_data['out_tot_sel_req'] = out_data['tot_sel_req']
    return_data['out_tot_buy_req'] = out_data['tot_buy_req']
    return_data['out_tot_buy_req_jub_pre'] = out_data['tot_buy_req_jub_pre']
    return_data['out_ovt_sel_req_pre'] = out_data['ovt_sel_req_pre']
    return_data['out_ovt_sel_req'] = out_data['ovt_sel_req']
    return_data['out_ovt_buy_req'] = out_data['ovt_buy_req']
    return_data['out_ovt_buy_req_pre'] = out_data['ovt_buy_req_pre']
    
    return return_data

  def get_ka10005(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    주식일주월시분요청
    메뉴 위치 : 국내주식 > 시세 > 주식일주월시분요청(ka10005)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_ddwkmm (list): 주식일주월시분
        - date (str(20)): 날짜
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - close_pric (str(20)): 종가
        - pre (str(20)): 대비
        - flu_rt (str(20)): 등락률
        - trde_qty (str(20)): 거래량
        - trde_prica (str(20)): 거래대금
        - for_poss (str(20)): 외인보유
        - for_wght (str(20)): 외인비중
        - for_netprps (str(20)): 외인순매수
        - orgn_netprps (str(20)): 기관순매수
        - ind_netprps (str(20)): 개인순매수
        - frgn (str(20)): 외국계
        - crd_remn_rt (str(20)): 신용잔고율
        - prm (str(20)): 프로그램
    
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
      'api-id': 'ka10005',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_ddwkmm'] = out_data['stk_ddwkmm']
    
    return return_data

  def get_ka10006(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    주식시분요청
    메뉴 위치 : 국내주식 > 시세 > 주식시분요청(ka10006)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_date (str(20)): 날짜
      out_open_pric (str(20)): 시가
      out_high_pric (str(20)): 고가
      out_low_pric (str(20)): 저가
      out_close_pric (str(20)): 종가
      out_pre (str(20)): 대비
      out_flu_rt (str(20)): 등락률
      out_trde_qty (str(20)): 거래량
      out_trde_prica (str(20)): 거래대금
      out_cntr_str (str(20)): 체결강도
    
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
      'api-id': 'ka10006',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_date'] = out_data['date']
    return_data['out_open_pric'] = out_data['open_pric']
    return_data['out_high_pric'] = out_data['high_pric']
    return_data['out_low_pric'] = out_data['low_pric']
    return_data['out_close_pric'] = out_data['close_pric']
    return_data['out_pre'] = out_data['pre']
    return_data['out_flu_rt'] = out_data['flu_rt']
    return_data['out_trde_qty'] = out_data['trde_qty']
    return_data['out_trde_prica'] = out_data['trde_prica']
    return_data['out_cntr_str'] = out_data['cntr_str']
    
    return return_data

  def get_ka10007(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    시세표성정보요청
    메뉴 위치 : 국내주식 > 시세 > 시세표성정보요청(ka10007)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_nm (str(40)): 종목명
      out_stk_cd (str(6)): 종목코드
      out_date (str(20)): 날짜
      out_tm (str(20)): 시간
      out_pred_close_pric (str(20)): 전일종가
      out_pred_trde_qty (str(20)): 전일거래량
      out_upl_pric (str(20)): 상한가
      out_lst_pric (str(20)): 하한가
      out_pred_trde_prica (str(20)): 전일거래대금
      out_flo_stkcnt (str(20)): 상장주식수
      out_cur_prc (str(20)): 현재가
      out_smbol (str(20)): 부호
      out_flu_rt (str(20)): 등락률
      out_pred_rt (str(20)): 전일비
      out_open_pric (str(20)): 시가
      out_high_pric (str(20)): 고가
      out_low_pric (str(20)): 저가
      out_cntr_qty (str(20)): 체결량
      out_trde_qty (str(20)): 거래량
      out_trde_prica (str(20)): 거래대금
      out_exp_cntr_pric (str(20)): 예상체결가
      out_exp_cntr_qty (str(20)): 예상체결량
      out_exp_sel_pri_bid (str(20)): 예상매도우선호가
      out_exp_buy_pri_bid (str(20)): 예상매수우선호가
      out_trde_strt_dt (str(20)): 거래시작일
      out_exec_pric (str(20)): 행사가격
      out_hgst_pric (str(20)): 최고가
      out_lwst_pric (str(20)): 최저가
      out_hgst_pric_dt (str(20)): 최고가일
      out_lwst_pric_dt (str(20)): 최저가일
      out_sel_1bid (str(20)): 매도1호가
      out_sel_2bid (str(20)): 매도2호가
      out_sel_3bid (str(20)): 매도3호가
      out_sel_4bid (str(20)): 매도4호가
      out_sel_5bid (str(20)): 매도5호가
      out_sel_6bid (str(20)): 매도6호가
      out_sel_7bid (str(20)): 매도7호가
      out_sel_8bid (str(20)): 매도8호가
      out_sel_9bid (str(20)): 매도9호가
      out_sel_10bid (str(20)): 매도10호가
      out_buy_1bid (str(20)): 매수1호가
      out_buy_2bid (str(20)): 매수2호가
      out_buy_3bid (str(20)): 매수3호가
      out_buy_4bid (str(20)): 매수4호가
      out_buy_5bid (str(20)): 매수5호가
      out_buy_6bid (str(20)): 매수6호가
      out_buy_7bid (str(20)): 매수7호가
      out_buy_8bid (str(20)): 매수8호가
      out_buy_9bid (str(20)): 매수9호가
      out_buy_10bid (str(20)): 매수10호가
      out_sel_1bid_req (str(20)): 매도1호가잔량
      out_sel_2bid_req (str(20)): 매도2호가잔량
      out_sel_3bid_req (str(20)): 매도3호가잔량
      out_sel_4bid_req (str(20)): 매도4호가잔량
      out_sel_5bid_req (str(20)): 매도5호가잔량
      out_sel_6bid_req (str(20)): 매도6호가잔량
      out_sel_7bid_req (str(20)): 매도7호가잔량
      out_sel_8bid_req (str(20)): 매도8호가잔량
      out_sel_9bid_req (str(20)): 매도9호가잔량
      out_sel_10bid_req (str(20)): 매도10호가잔량
      out_buy_1bid_req (str(20)): 매수1호가잔량
      out_buy_2bid_req (str(20)): 매수2호가잔량
      out_buy_3bid_req (str(20)): 매수3호가잔량
      out_buy_4bid_req (str(20)): 매수4호가잔량
      out_buy_5bid_req (str(20)): 매수5호가잔량
      out_buy_6bid_req (str(20)): 매수6호가잔량
      out_buy_7bid_req (str(20)): 매수7호가잔량
      out_buy_8bid_req (str(20)): 매수8호가잔량
      out_buy_9bid_req (str(20)): 매수9호가잔량
      out_buy_10bid_req (str(20)): 매수10호가잔량
      out_sel_1bid_jub_pre (str(20)): 매도1호가직전대비
      out_sel_2bid_jub_pre (str(20)): 매도2호가직전대비
      out_sel_3bid_jub_pre (str(20)): 매도3호가직전대비
      out_sel_4bid_jub_pre (str(20)): 매도4호가직전대비
      out_sel_5bid_jub_pre (str(20)): 매도5호가직전대비
      out_sel_6bid_jub_pre (str(20)): 매도6호가직전대비
      out_sel_7bid_jub_pre (str(20)): 매도7호가직전대비
      out_sel_8bid_jub_pre (str(20)): 매도8호가직전대비
      out_sel_9bid_jub_pre (str(20)): 매도9호가직전대비
      out_sel_10bid_jub_pre (str(20)): 매도10호가직전대비
      out_buy_1bid_jub_pre (str(20)): 매수1호가직전대비
      out_buy_2bid_jub_pre (str(20)): 매수2호가직전대비
      out_buy_3bid_jub_pre (str(20)): 매수3호가직전대비
      out_buy_4bid_jub_pre (str(20)): 매수4호가직전대비
      out_buy_5bid_jub_pre (str(20)): 매수5호가직전대비
      out_buy_6bid_jub_pre (str(20)): 매수6호가직전대비
      out_buy_7bid_jub_pre (str(20)): 매수7호가직전대비
      out_buy_8bid_jub_pre (str(20)): 매수8호가직전대비
      out_buy_9bid_jub_pre (str(20)): 매수9호가직전대비
      out_buy_10bid_jub_pre (str(20)): 매수10호가직전대비
      out_sel_1bid_cnt (str(20)): 매도1호가건수
      out_sel_2bid_cnt (str(20)): 매도2호가건수
      out_sel_3bid_cnt (str(20)): 매도3호가건수
      out_sel_4bid_cnt (str(20)): 매도4호가건수
      out_sel_5bid_cnt (str(20)): 매도5호가건수
      out_buy_1bid_cnt (str(20)): 매수1호가건수
      out_buy_2bid_cnt (str(20)): 매수2호가건수
      out_buy_3bid_cnt (str(20)): 매수3호가건수
      out_buy_4bid_cnt (str(20)): 매수4호가건수
      out_buy_5bid_cnt (str(20)): 매수5호가건수
      out_lpsel_1bid_req (str(20)): LP매도1호가잔량
      out_lpsel_2bid_req (str(20)): LP매도2호가잔량
      out_lpsel_3bid_req (str(20)): LP매도3호가잔량
      out_lpsel_4bid_req (str(20)): LP매도4호가잔량
      out_lpsel_5bid_req (str(20)): LP매도5호가잔량
      out_lpsel_6bid_req (str(20)): LP매도6호가잔량
      out_lpsel_7bid_req (str(20)): LP매도7호가잔량
      out_lpsel_8bid_req (str(20)): LP매도8호가잔량
      out_lpsel_9bid_req (str(20)): LP매도9호가잔량
      out_lpsel_10bid_req (str(20)): LP매도10호가잔량
      out_lpbuy_1bid_req (str(20)): LP매수1호가잔량
      out_lpbuy_2bid_req (str(20)): LP매수2호가잔량
      out_lpbuy_3bid_req (str(20)): LP매수3호가잔량
      out_lpbuy_4bid_req (str(20)): LP매수4호가잔량
      out_lpbuy_5bid_req (str(20)): LP매수5호가잔량
      out_lpbuy_6bid_req (str(20)): LP매수6호가잔량
      out_lpbuy_7bid_req (str(20)): LP매수7호가잔량
      out_lpbuy_8bid_req (str(20)): LP매수8호가잔량
      out_lpbuy_9bid_req (str(20)): LP매수9호가잔량
      out_lpbuy_10bid_req (str(20)): LP매수10호가잔량
      out_tot_buy_req (str(20)): 총매수잔량
      out_tot_sel_req (str(20)): 총매도잔량
      out_tot_buy_cnt (str(20)): 총매수건수
      out_tot_sel_cnt (str(20)): 총매도건수
    
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
      'api-id': 'ka10007',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_nm'] = out_data['stk_nm']
    return_data['out_stk_cd'] = out_data['stk_cd']
    return_data['out_date'] = out_data['date']
    return_data['out_tm'] = out_data['tm']
    return_data['out_pred_close_pric'] = out_data['pred_close_pric']
    return_data['out_pred_trde_qty'] = out_data['pred_trde_qty']
    return_data['out_upl_pric'] = out_data['upl_pric']
    return_data['out_lst_pric'] = out_data['lst_pric']
    return_data['out_pred_trde_prica'] = out_data['pred_trde_prica']
    return_data['out_flo_stkcnt'] = out_data['flo_stkcnt']
    return_data['out_cur_prc'] = out_data['cur_prc']
    return_data['out_smbol'] = out_data['smbol']
    return_data['out_flu_rt'] = out_data['flu_rt']
    return_data['out_pred_rt'] = out_data['pred_rt']
    return_data['out_open_pric'] = out_data['open_pric']
    return_data['out_high_pric'] = out_data['high_pric']
    return_data['out_low_pric'] = out_data['low_pric']
    return_data['out_cntr_qty'] = out_data['cntr_qty']
    return_data['out_trde_qty'] = out_data['trde_qty']
    return_data['out_trde_prica'] = out_data['trde_prica']
    return_data['out_exp_cntr_pric'] = out_data['exp_cntr_pric']
    return_data['out_exp_cntr_qty'] = out_data['exp_cntr_qty']
    return_data['out_exp_sel_pri_bid'] = out_data['exp_sel_pri_bid']
    return_data['out_exp_buy_pri_bid'] = out_data['exp_buy_pri_bid']
    return_data['out_trde_strt_dt'] = out_data['trde_strt_dt']
    return_data['out_exec_pric'] = out_data['exec_pric']
    return_data['out_hgst_pric'] = out_data['hgst_pric']
    return_data['out_lwst_pric'] = out_data['lwst_pric']
    return_data['out_hgst_pric_dt'] = out_data['hgst_pric_dt']
    return_data['out_lwst_pric_dt'] = out_data['lwst_pric_dt']
    return_data['out_sel_1bid'] = out_data['sel_1bid']
    return_data['out_sel_2bid'] = out_data['sel_2bid']
    return_data['out_sel_3bid'] = out_data['sel_3bid']
    return_data['out_sel_4bid'] = out_data['sel_4bid']
    return_data['out_sel_5bid'] = out_data['sel_5bid']
    return_data['out_sel_6bid'] = out_data['sel_6bid']
    return_data['out_sel_7bid'] = out_data['sel_7bid']
    return_data['out_sel_8bid'] = out_data['sel_8bid']
    return_data['out_sel_9bid'] = out_data['sel_9bid']
    return_data['out_sel_10bid'] = out_data['sel_10bid']
    return_data['out_buy_1bid'] = out_data['buy_1bid']
    return_data['out_buy_2bid'] = out_data['buy_2bid']
    return_data['out_buy_3bid'] = out_data['buy_3bid']
    return_data['out_buy_4bid'] = out_data['buy_4bid']
    return_data['out_buy_5bid'] = out_data['buy_5bid']
    return_data['out_buy_6bid'] = out_data['buy_6bid']
    return_data['out_buy_7bid'] = out_data['buy_7bid']
    return_data['out_buy_8bid'] = out_data['buy_8bid']
    return_data['out_buy_9bid'] = out_data['buy_9bid']
    return_data['out_buy_10bid'] = out_data['buy_10bid']
    return_data['out_sel_1bid_req'] = out_data['sel_1bid_req']
    return_data['out_sel_2bid_req'] = out_data['sel_2bid_req']
    return_data['out_sel_3bid_req'] = out_data['sel_3bid_req']
    return_data['out_sel_4bid_req'] = out_data['sel_4bid_req']
    return_data['out_sel_5bid_req'] = out_data['sel_5bid_req']
    return_data['out_sel_6bid_req'] = out_data['sel_6bid_req']
    return_data['out_sel_7bid_req'] = out_data['sel_7bid_req']
    return_data['out_sel_8bid_req'] = out_data['sel_8bid_req']
    return_data['out_sel_9bid_req'] = out_data['sel_9bid_req']
    return_data['out_sel_10bid_req'] = out_data['sel_10bid_req']
    return_data['out_buy_1bid_req'] = out_data['buy_1bid_req']
    return_data['out_buy_2bid_req'] = out_data['buy_2bid_req']
    return_data['out_buy_3bid_req'] = out_data['buy_3bid_req']
    return_data['out_buy_4bid_req'] = out_data['buy_4bid_req']
    return_data['out_buy_5bid_req'] = out_data['buy_5bid_req']
    return_data['out_buy_6bid_req'] = out_data['buy_6bid_req']
    return_data['out_buy_7bid_req'] = out_data['buy_7bid_req']
    return_data['out_buy_8bid_req'] = out_data['buy_8bid_req']
    return_data['out_buy_9bid_req'] = out_data['buy_9bid_req']
    return_data['out_buy_10bid_req'] = out_data['buy_10bid_req']
    return_data['out_sel_1bid_jub_pre'] = out_data['sel_1bid_jub_pre']
    return_data['out_sel_2bid_jub_pre'] = out_data['sel_2bid_jub_pre']
    return_data['out_sel_3bid_jub_pre'] = out_data['sel_3bid_jub_pre']
    return_data['out_sel_4bid_jub_pre'] = out_data['sel_4bid_jub_pre']
    return_data['out_sel_5bid_jub_pre'] = out_data['sel_5bid_jub_pre']
    return_data['out_sel_6bid_jub_pre'] = out_data['sel_6bid_jub_pre']
    return_data['out_sel_7bid_jub_pre'] = out_data['sel_7bid_jub_pre']
    return_data['out_sel_8bid_jub_pre'] = out_data['sel_8bid_jub_pre']
    return_data['out_sel_9bid_jub_pre'] = out_data['sel_9bid_jub_pre']
    return_data['out_sel_10bid_jub_pre'] = out_data['sel_10bid_jub_pre']
    return_data['out_buy_1bid_jub_pre'] = out_data['buy_1bid_jub_pre']
    return_data['out_buy_2bid_jub_pre'] = out_data['buy_2bid_jub_pre']
    return_data['out_buy_3bid_jub_pre'] = out_data['buy_3bid_jub_pre']
    return_data['out_buy_4bid_jub_pre'] = out_data['buy_4bid_jub_pre']
    return_data['out_buy_5bid_jub_pre'] = out_data['buy_5bid_jub_pre']
    return_data['out_buy_6bid_jub_pre'] = out_data['buy_6bid_jub_pre']
    return_data['out_buy_7bid_jub_pre'] = out_data['buy_7bid_jub_pre']
    return_data['out_buy_8bid_jub_pre'] = out_data['buy_8bid_jub_pre']
    return_data['out_buy_9bid_jub_pre'] = out_data['buy_9bid_jub_pre']
    return_data['out_buy_10bid_jub_pre'] = out_data['buy_10bid_jub_pre']
    return_data['out_sel_1bid_cnt'] = out_data['sel_1bid_cnt']
    return_data['out_sel_2bid_cnt'] = out_data['sel_2bid_cnt']
    return_data['out_sel_3bid_cnt'] = out_data['sel_3bid_cnt']
    return_data['out_sel_4bid_cnt'] = out_data['sel_4bid_cnt']
    return_data['out_sel_5bid_cnt'] = out_data['sel_5bid_cnt']
    return_data['out_buy_1bid_cnt'] = out_data['buy_1bid_cnt']
    return_data['out_buy_2bid_cnt'] = out_data['buy_2bid_cnt']
    return_data['out_buy_3bid_cnt'] = out_data['buy_3bid_cnt']
    return_data['out_buy_4bid_cnt'] = out_data['buy_4bid_cnt']
    return_data['out_buy_5bid_cnt'] = out_data['buy_5bid_cnt']
    return_data['out_lpsel_1bid_req'] = out_data['lpsel_1bid_req']
    return_data['out_lpsel_2bid_req'] = out_data['lpsel_2bid_req']
    return_data['out_lpsel_3bid_req'] = out_data['lpsel_3bid_req']
    return_data['out_lpsel_4bid_req'] = out_data['lpsel_4bid_req']
    return_data['out_lpsel_5bid_req'] = out_data['lpsel_5bid_req']
    return_data['out_lpsel_6bid_req'] = out_data['lpsel_6bid_req']
    return_data['out_lpsel_7bid_req'] = out_data['lpsel_7bid_req']
    return_data['out_lpsel_8bid_req'] = out_data['lpsel_8bid_req']
    return_data['out_lpsel_9bid_req'] = out_data['lpsel_9bid_req']
    return_data['out_lpsel_10bid_req'] = out_data['lpsel_10bid_req']
    return_data['out_lpbuy_1bid_req'] = out_data['lpbuy_1bid_req']
    return_data['out_lpbuy_2bid_req'] = out_data['lpbuy_2bid_req']
    return_data['out_lpbuy_3bid_req'] = out_data['lpbuy_3bid_req']
    return_data['out_lpbuy_4bid_req'] = out_data['lpbuy_4bid_req']
    return_data['out_lpbuy_5bid_req'] = out_data['lpbuy_5bid_req']
    return_data['out_lpbuy_6bid_req'] = out_data['lpbuy_6bid_req']
    return_data['out_lpbuy_7bid_req'] = out_data['lpbuy_7bid_req']
    return_data['out_lpbuy_8bid_req'] = out_data['lpbuy_8bid_req']
    return_data['out_lpbuy_9bid_req'] = out_data['lpbuy_9bid_req']
    return_data['out_lpbuy_10bid_req'] = out_data['lpbuy_10bid_req']
    return_data['out_tot_buy_req'] = out_data['tot_buy_req']
    return_data['out_tot_sel_req'] = out_data['tot_sel_req']
    return_data['out_tot_buy_cnt'] = out_data['tot_buy_cnt']
    return_data['out_tot_sel_cnt'] = out_data['tot_sel_cnt']
    
    return return_data

  def get_ka10011(self, in_cont_yn: str, in_next_key: str, in_newstk_recvrht_tp: str):
    """
    신주인수권전체시세요청
    메뉴 위치 : 국내주식 > 시세 > 신주인수권전체시세요청(ka10011)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_newstk_recvrht_tp (str(2)): 신주인수권구분(필수) 00:전체, 05:신주인수권증권, 07:신주인수권증서
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_newstk_recvrht_mrpr (list): 신주인수권시세
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - fpr_sel_bid (str(20)): 최우선매도호가
        - fpr_buy_bid (str(20)): 최우선매수호가
        - acc_trde_qty (str(20)): 누적거래량
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
    
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
      'api-id': 'ka10011',
    }
    params = {
      'newstk_recvrht_tp': in_newstk_recvrht_tp,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_newstk_recvrht_mrpr'] = out_data['newstk_recvrht_mrpr']
    
    return return_data

  def get_ka10044(self, in_cont_yn: str, in_next_key: str, in_strt_dt: str, in_end_dt: str, in_trde_tp: str, in_mrkt_tp: str, in_stex_tp: str):
    """
    일별기관매매종목요청
    메뉴 위치 : 국내주식 > 시세 > 일별기관매매종목요청(ka10044)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD
      in_end_dt (str(8)): 종료일자(필수) YYYYMMDD
      in_trde_tp (str(1)): 매매구분(필수) 1:순매도, 2:순매수
      in_mrkt_tp (str(3)): 시장구분(필수) 001:코스피, 101:코스닥
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_daly_orgn_trde_stk (list): 일별기관매매종목
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - netprps_qty (str(20)): 순매수수량
        - netprps_amt (str(20)): 순매수금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10044',
    }
    params = {
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'trde_tp': in_trde_tp,
      'mrkt_tp': in_mrkt_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_daly_orgn_trde_stk'] = out_data['daly_orgn_trde_stk']
    
    return return_data

  def get_ka10045(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_strt_dt: str, in_end_dt: str, in_orgn_prsm_unp_tp: str, in_for_prsm_unp_tp: str):
    """
    종목별기관매매추이요청
    메뉴 위치 : 국내주식 > 시세 > 종목별기관매매추이요청(ka10045)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD
      in_end_dt (str(8)): 종료일자(필수) YYYYMMDD
      in_orgn_prsm_unp_tp (str(1)): 기관추정단가구분(필수) 1:매수단가, 2:매도단가
      in_for_prsm_unp_tp (str(1)): 외인추정단가구분(필수) 1:매수단가, 2:매도단가
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_orgn_prsm_avg_pric (str): 기관추정평균가
      out_for_prsm_avg_pric (str): 외인추정평균가
      out_stk_orgn_trde_trnsn (list): 종목별기관매매추이
        - dt (str(20)): 일자
        - close_pric (str(20)): 종가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - orgn_dt_acc (str(20)): 기관기간누적
        - orgn_daly_nettrde_qty (str(20)): 기관일별순매매수량
        - for_dt_acc (str(20)): 외인기간누적
        - for_daly_nettrde_qty (str(20)): 외인일별순매매수량
        - limit_exh_rt (str(20)): 한도소진율
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10045',
    }
    params = {
      'stk_cd': in_stk_cd,
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'orgn_prsm_unp_tp': in_orgn_prsm_unp_tp,
      'for_prsm_unp_tp': in_for_prsm_unp_tp,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_orgn_prsm_avg_pric'] = out_data['orgn_prsm_avg_pric']
    return_data['out_for_prsm_avg_pric'] = out_data['for_prsm_avg_pric']
    return_data['out_stk_orgn_trde_trnsn'] = out_data['stk_orgn_trde_trnsn']
    
    return return_data

  def get_ka10046(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    체결강도추이시간별요청
    메뉴 위치 : 국내주식 > 시세 > 체결강도추이시간별요청(ka10046)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_cntr_str_tm (list): 체결강도시간별
        - cntr_tm (str(20)): 체결시간
        - cur_prc (str(20)): 현재가
        - pred_pre (str(20)): 전일대비
        - pred_pre_sig (str(20)): 전일대비기호
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - acc_trde_prica (str(20)): 누적거래대금
        - acc_trde_qty (str(20)): 누적거래량
        - cntr_str (str(20)): 체결강도
        - cntr_str_5min (str(20)): 체결강도5분
        - cntr_str_20min (str(20)): 체결강도20분
        - cntr_str_60min (str(20)): 체결강도60분
        - stex_tp (str(20)): 거래소구분
    
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
      'api-id': 'ka10046',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_cntr_str_tm'] = out_data['cntr_str_tm']
    
    return return_data

  def get_ka10047(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    체결강도추이일별요청
    메뉴 위치 : 국내주식 > 시세 > 체결강도추이일별요청(ka10047)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_cntr_str_daly (list): 체결강도일별
        - dt (str(20)): 일자
        - cur_prc (str(20)): 현재가
        - pred_pre (str(20)): 전일대비
        - pred_pre_sig (str(20)): 전일대비기호
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - acc_trde_prica (str(20)): 누적거래대금
        - acc_trde_qty (str(20)): 누적거래량
        - cntr_str (str(20)): 체결강도
        - cntr_str_5min (str(20)): 체결강도5일
        - cntr_str_20min (str(20)): 체결강도20일
        - cntr_str_60min (str(20)): 체결강도60일
    
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
      'api-id': 'ka10047',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_cntr_str_daly'] = out_data['cntr_str_daly']
    
    return return_data

  def get_ka10063(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_amt_qty_tp: str, in_invsr: str, in_frgn_all: str, in_smtm_netprps_tp: str, in_stex_tp: str):
    """
    장중투자자별매매요청
    메뉴 위치 : 국내주식 > 시세 > 장중투자자별매매요청(ka10063)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1: 금액&수량
      in_invsr (str(1)): 투자자별(필수) 6:외국인, 7:기관계, 1:투신, 0:보험, 2:은행, 3:연기금, 4:국가, 5:기타법인
      in_frgn_all (str(1)): 외국계전체(필수) 1:체크, 0:미체크
      in_smtm_netprps_tp (str(1)): 동시순매수구분(필수) 1:체크, 0:미체크
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_opmr_invsr_trde (list): 장중투자자별매매
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - acc_trde_qty (str(20)): 누적거래량
        - netprps_amt (str(20)): 순매수금액
        - prev_netprps_amt (str(20)): 이전순매수금액
        - buy_amt (str(20)): 매수금액
        - netprps_amt_irds (str(20)): 순매수금액증감
        - buy_amt_irds (str(20)): 매수금액증감
        - sell_amt (str(20)): 매도금액
        - sell_amt_irds (str(20)): 매도금액증감
        - netprps_qty (str(20)): 순매수수량
        - prev_pot_netprps_qty (str(20)): 이전시점순매수수량
        - netprps_irds (str(20)): 순매수증감
        - buy_qty (str(20)): 매수수량
        - buy_qty_irds (str(20)): 매수수량증감
        - sell_qty (str(20)): 매도수량
        - sell_qty_irds (str(20)): 매도수량증감
    
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
      'api-id': 'ka10063',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'amt_qty_tp': in_amt_qty_tp,
      'invsr': in_invsr,
      'frgn_all': in_frgn_all,
      'smtm_netprps_tp': in_smtm_netprps_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_opmr_invsr_trde'] = out_data['opmr_invsr_trde']
    
    return return_data

  def get_ka10066(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_amt_qty_tp: str, in_trde_tp: str, in_stex_tp: str):
    """
    장마감후투자자별매매요청
    메뉴 위치 : 국내주식 > 시세 > 장마감후투자자별매매요청(ka10066)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1:금액, 2:수량
      in_trde_tp (str(1)): 매매구분(필수) 0:순매수, 1:매수, 2:매도
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_opaf_invsr_trde (list): 장중투자자별매매차트
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - trde_qty (str(20)): 거래량
        - ind_invsr (str(20)): 개인투자자
        - frgnr_invsr (str(20)): 외국인투자자
        - orgn (str(20)): 기관계
        - fnnc_invt (str(20)): 금융투자
        - insrnc (str(20)): 보험
        - invtrt (str(20)): 투신
        - etc_fnnc (str(20)): 기타금융
        - bank (str(20)): 은행
        - penfnd_etc (str(20)): 연기금등
        - samo_fund (str(20)): 사모펀드
        - natn (str(20)): 국가
        - etc_corp (str(20)): 기타법인
    
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
      'api-id': 'ka10066',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'amt_qty_tp': in_amt_qty_tp,
      'trde_tp': in_trde_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_opaf_invsr_trde'] = out_data['opaf_invsr_trde']
    
    return return_data

  def get_ka10078(self, in_cont_yn: str, in_next_key: str, in_mmcm_cd: str, in_stk_cd: str, in_strt_dt: str, in_end_dt: str):
    """
    증권사별종목매매동향요청
    메뉴 위치 : 국내주식 > 시세 > 증권사별종목매매동향요청(ka10078)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mmcm_cd (str(3)): 회원사코드(필수) 회원사 코드는 ka10102 조회
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD
      in_end_dt (str(8)): 종료일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_sec_stk_trde_trend (list): 증권사별종목매매동향
        - dt (str(20)): 일자
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - acc_trde_qty (str(20)): 누적거래량
        - netprps_qty (str(20)): 순매수수량
        - buy_qty (str(20)): 매수수량
        - sell_qty (str(20)): 매도수량
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10078',
    }
    params = {
      'mmcm_cd': in_mmcm_cd,
      'stk_cd': in_stk_cd,
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_sec_stk_trde_trend'] = out_data['sec_stk_trde_trend']
    
    return return_data

  def get_ka10086(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_qry_dt: str, in_indc_tp: str):
    """
    일별주가요청
    메뉴 위치 : 국내주식 > 시세 > 일별주가요청(ka10086)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_qry_dt (str(8)): 조회일자(필수) YYYYMMDD
      in_indc_tp (str(1)): 표시구분(필수) 0:수량, 1:금액(백만원)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_daly_stkpc (list): 일별주가
        - date (str(20)): 날짜
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - close_pric (str(20)): 종가
        - pred_rt (str(20)): 전일비
        - flu_rt (str(20)): 등락률
        - trde_qty (str(20)): 거래량
        - amt_mn (str(20)): 금액(백만)
        - crd_rt (str(20)): 신용비
        - ind (str(20)): 개인
        - orgn (str(20)): 기관
        - for_qty (str(20)): 외인수량
        - frgn (str(20)): 외국계
        - prm (str(20)): 프로그램
        - for_rt (str(20)): 외인비
        - for_poss (str(20)): 외인보유
        - for_wght (str(20)): 외인비중
        - for_netprps (str(20)): 외인순매수
        - orgn_netprps (str(20)): 기관순매수
        - ind_netprps (str(20)): 개인순매수
        - crd_remn_rt (str(20)): 신용잔고율
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_qry_dt or in_qry_dt == '':
      in_qry_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10086',
    }
    params = {
      'stk_cd': in_stk_cd,
      'qry_dt': in_qry_dt,
      'indc_tp': in_indc_tp,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_daly_stkpc'] = out_data['daly_stkpc']
    
    return return_data

  def get_ka10087(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    시간외단일가요청
    메뉴 위치 : 국내주식 > 시세 > 시간외단일가요청(ka10087)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_bid_req_base_tm (str): 호가잔량기준시간
      out_ovt_sigpric_sel_bid_jub_pre_5 (str): 시간외단일가_매도호가직전대비5
      out_ovt_sigpric_sel_bid_jub_pre_4 (str): 시간외단일가_매도호가직전대비4
      out_ovt_sigpric_sel_bid_jub_pre_3 (str): 시간외단일가_매도호가직전대비3
      out_ovt_sigpric_sel_bid_jub_pre_2 (str): 시간외단일가_매도호가직전대비2
      out_ovt_sigpric_sel_bid_jub_pre_1 (str): 시간외단일가_매도호가직전대비1
      out_ovt_sigpric_sel_bid_qty_5 (str): 시간외단일가_매도호가수량5
      out_ovt_sigpric_sel_bid_qty_4 (str): 시간외단일가_매도호가수량4
      out_ovt_sigpric_sel_bid_qty_3 (str): 시간외단일가_매도호가수량3
      out_ovt_sigpric_sel_bid_qty_2 (str): 시간외단일가_매도호가수량2
      out_ovt_sigpric_sel_bid_qty_1 (str): 시간외단일가_매도호가수량1
      out_ovt_sigpric_sel_bid_5 (str): 시간외단일가_매도호가5
      out_ovt_sigpric_sel_bid_4 (str): 시간외단일가_매도호가4
      out_ovt_sigpric_sel_bid_3 (str): 시간외단일가_매도호가3
      out_ovt_sigpric_sel_bid_2 (str): 시간외단일가_매도호가2
      out_ovt_sigpric_sel_bid_1 (str): 시간외단일가_매도호가1
      out_ovt_sigpric_buy_bid_1 (str): 시간외단일가_매수호가1
      out_ovt_sigpric_buy_bid_2 (str): 시간외단일가_매수호가2
      out_ovt_sigpric_buy_bid_3 (str): 시간외단일가_매수호가3
      out_ovt_sigpric_buy_bid_4 (str): 시간외단일가_매수호가4
      out_ovt_sigpric_buy_bid_5 (str): 시간외단일가_매수호가5
      out_ovt_sigpric_buy_bid_qty_1 (str): 시간외단일가_매수호가수량1
      out_ovt_sigpric_buy_bid_qty_2 (str): 시간외단일가_매수호가수량2
      out_ovt_sigpric_buy_bid_qty_3 (str): 시간외단일가_매수호가수량3
      out_ovt_sigpric_buy_bid_qty_4 (str): 시간외단일가_매수호가수량4
      out_ovt_sigpric_buy_bid_qty_5 (str): 시간외단일가_매수호가수량5
      out_ovt_sigpric_buy_bid_jub_pre_1 (str): 시간외단일가_매수호가직전대비1
      out_ovt_sigpric_buy_bid_jub_pre_2 (str): 시간외단일가_매수호가직전대비2
      out_ovt_sigpric_buy_bid_jub_pre_3 (str): 시간외단일가_매수호가직전대비3
      out_ovt_sigpric_buy_bid_jub_pre_4 (str): 시간외단일가_매수호가직전대비4
      out_ovt_sigpric_buy_bid_jub_pre_5 (str): 시간외단일가_매수호가직전대비5
      out_ovt_sigpric_sel_bid_tot_req (str): 시간외단일가_매도호가총잔량
      out_ovt_sigpric_buy_bid_tot_req (str): 시간외단일가_매수호가총잔량
      out_sel_bid_tot_req_jub_pre (str): 매도호가총잔량직전대비
      out_sel_bid_tot_req (str): 매도호가총잔량
      out_buy_bid_tot_req (str): 매수호가총잔량
      out_buy_bid_tot_req_jub_pre (str): 매수호가총잔량직전대비
      out_ovt_sel_bid_tot_req_jub_pre (str): 시간외매도호가총잔량직전대비
      out_ovt_sel_bid_tot_req (str): 시간외매도호가총잔량
      out_ovt_buy_bid_tot_req (str): 시간외매수호가총잔량
      out_ovt_buy_bid_tot_req_jub_pre (str): 시간외매수호가총잔량직전대비
      out_ovt_sigpric_cur_prc (str): 시간외단일가_현재가
      out_ovt_sigpric_pred_pre_sig (str): 시간외단일가_전일대비기호
      out_ovt_sigpric_pred_pre (str): 시간외단일가_전일대비
      out_ovt_sigpric_flu_rt (str): 시간외단일가_등락률
      out_ovt_sigpric_acc_trde_qty (str): 시간외단일가_누적거래량
    
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
      'api-id': 'ka10087',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_bid_req_base_tm'] = out_data['bid_req_base_tm']
    return_data['out_ovt_sigpric_sel_bid_jub_pre_5'] = out_data['ovt_sigpric_sel_bid_jub_pre_5']
    return_data['out_ovt_sigpric_sel_bid_jub_pre_4'] = out_data['ovt_sigpric_sel_bid_jub_pre_4']
    return_data['out_ovt_sigpric_sel_bid_jub_pre_3'] = out_data['ovt_sigpric_sel_bid_jub_pre_3']
    return_data['out_ovt_sigpric_sel_bid_jub_pre_2'] = out_data['ovt_sigpric_sel_bid_jub_pre_2']
    return_data['out_ovt_sigpric_sel_bid_jub_pre_1'] = out_data['ovt_sigpric_sel_bid_jub_pre_1']
    return_data['out_ovt_sigpric_sel_bid_qty_5'] = out_data['ovt_sigpric_sel_bid_qty_5']
    return_data['out_ovt_sigpric_sel_bid_qty_4'] = out_data['ovt_sigpric_sel_bid_qty_4']
    return_data['out_ovt_sigpric_sel_bid_qty_3'] = out_data['ovt_sigpric_sel_bid_qty_3']
    return_data['out_ovt_sigpric_sel_bid_qty_2'] = out_data['ovt_sigpric_sel_bid_qty_2']
    return_data['out_ovt_sigpric_sel_bid_qty_1'] = out_data['ovt_sigpric_sel_bid_qty_1']
    return_data['out_ovt_sigpric_sel_bid_5'] = out_data['ovt_sigpric_sel_bid_5']
    return_data['out_ovt_sigpric_sel_bid_4'] = out_data['ovt_sigpric_sel_bid_4']
    return_data['out_ovt_sigpric_sel_bid_3'] = out_data['ovt_sigpric_sel_bid_3']
    return_data['out_ovt_sigpric_sel_bid_2'] = out_data['ovt_sigpric_sel_bid_2']
    return_data['out_ovt_sigpric_sel_bid_1'] = out_data['ovt_sigpric_sel_bid_1']
    return_data['out_ovt_sigpric_buy_bid_1'] = out_data['ovt_sigpric_buy_bid_1']
    return_data['out_ovt_sigpric_buy_bid_2'] = out_data['ovt_sigpric_buy_bid_2']
    return_data['out_ovt_sigpric_buy_bid_3'] = out_data['ovt_sigpric_buy_bid_3']
    return_data['out_ovt_sigpric_buy_bid_4'] = out_data['ovt_sigpric_buy_bid_4']
    return_data['out_ovt_sigpric_buy_bid_5'] = out_data['ovt_sigpric_buy_bid_5']
    return_data['out_ovt_sigpric_buy_bid_qty_1'] = out_data['ovt_sigpric_buy_bid_qty_1']
    return_data['out_ovt_sigpric_buy_bid_qty_2'] = out_data['ovt_sigpric_buy_bid_qty_2']
    return_data['out_ovt_sigpric_buy_bid_qty_3'] = out_data['ovt_sigpric_buy_bid_qty_3']
    return_data['out_ovt_sigpric_buy_bid_qty_4'] = out_data['ovt_sigpric_buy_bid_qty_4']
    return_data['out_ovt_sigpric_buy_bid_qty_5'] = out_data['ovt_sigpric_buy_bid_qty_5']
    return_data['out_ovt_sigpric_buy_bid_jub_pre_1'] = out_data['ovt_sigpric_buy_bid_jub_pre_1']
    return_data['out_ovt_sigpric_buy_bid_jub_pre_2'] = out_data['ovt_sigpric_buy_bid_jub_pre_2']
    return_data['out_ovt_sigpric_buy_bid_jub_pre_3'] = out_data['ovt_sigpric_buy_bid_jub_pre_3']
    return_data['out_ovt_sigpric_buy_bid_jub_pre_4'] = out_data['ovt_sigpric_buy_bid_jub_pre_4']
    return_data['out_ovt_sigpric_buy_bid_jub_pre_5'] = out_data['ovt_sigpric_buy_bid_jub_pre_5']
    return_data['out_ovt_sigpric_sel_bid_tot_req'] = out_data['ovt_sigpric_sel_bid_tot_req']
    return_data['out_ovt_sigpric_buy_bid_tot_req'] = out_data['ovt_sigpric_buy_bid_tot_req']
    return_data['out_sel_bid_tot_req_jub_pre'] = out_data['sel_bid_tot_req_jub_pre']
    return_data['out_sel_bid_tot_req'] = out_data['sel_bid_tot_req']
    return_data['out_buy_bid_tot_req'] = out_data['buy_bid_tot_req']
    return_data['out_buy_bid_tot_req_jub_pre'] = out_data['buy_bid_tot_req_jub_pre']
    return_data['out_ovt_sel_bid_tot_req_jub_pre'] = out_data['ovt_sel_bid_tot_req_jub_pre']
    return_data['out_ovt_sel_bid_tot_req'] = out_data['ovt_sel_bid_tot_req']
    return_data['out_ovt_buy_bid_tot_req'] = out_data['ovt_buy_bid_tot_req']
    return_data['out_ovt_buy_bid_tot_req_jub_pre'] = out_data['ovt_buy_bid_tot_req_jub_pre']
    return_data['out_ovt_sigpric_cur_prc'] = out_data['ovt_sigpric_cur_prc']
    return_data['out_ovt_sigpric_pred_pre_sig'] = out_data['ovt_sigpric_pred_pre_sig']
    return_data['out_ovt_sigpric_pred_pre'] = out_data['ovt_sigpric_pred_pre']
    return_data['out_ovt_sigpric_flu_rt'] = out_data['ovt_sigpric_flu_rt']
    return_data['out_ovt_sigpric_acc_trde_qty'] = out_data['ovt_sigpric_acc_trde_qty']
    
    return return_data

  def get_ka50010(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    금현물체결추이
    메뉴 위치 : 국내주식 > 시세 > 금현물체결추이(ka50010)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gold_cntr (list): 금현물체결추이
        - cntr_pric (str(20)): 체결가
        - pred_pre (str(20)): 전일 대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 누적 거래량
        - acc_trde_prica (str(20)): 누적 거래대금
        - cntr_trde_qty (str(20)): 거래량(체결량)
        - tm (str(20)): 체결시간
        - pre_sig (str(20)): 전일대비기호
        - pri_sel_bid_unit (str(20)): 매도호가
        - pri_buy_bid_unit (str(20)): 매수호가
        - trde_pre (str(20)): 전일 거래량 대비 비율
        - trde_tern_rt (str(20)): 전일 거래량 대비 순간 거래량 비율
        - cntr_str (str(20)): 체결강도
    
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
      'api-id': 'ka50010',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gold_cntr'] = out_data['gold_cntr']
    
    return return_data

  def get_ka50012(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_base_dt: str):
    """
    금현물일별추이
    메뉴 위치 : 국내주식 > 시세 > 금현물일별추이(ka50012)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gold_daly_trnsn (list): 금현물일별추이
        - cur_prc (str(20)): 종가
        - pred_pre (str(20)): 전일 대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 누적 거래량
        - acc_trde_prica (str(20)): 누적 거래대금(백만)
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - dt (str(20)): 일자
        - pre_sig (str(20)): 전일대비기호
        - orgn_netprps (str(20)): 기관 순매수 수량
        - for_netprps (str(20)): 외국인 순매수 수량
        - ind_netprps (str(20)): 순매매량(개인)
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka50012',
    }
    params = {
      'stk_cd': in_stk_cd,
      'base_dt': in_base_dt,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gold_daly_trnsn'] = out_data['gold_daly_trnsn']
    
    return return_data

  def get_ka50087(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    금현물예상체결
    메뉴 위치 : 국내주식 > 시세 > 금현물예상체결(ka50087)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gold_expt_exec (list): 금현물예상체결
        - exp_cntr_pric (str(20)): 예상 체결가
        - exp_pred_pre (str(20)): 예상 체결가 전일대비
        - exp_flu_rt (str(20)): 예상 체결가 등락율
        - exp_acc_trde_qty (str(20)): 예상 체결 수량(누적)
        - exp_cntr_trde_qty (str(20)): 예상 체결 수량
        - exp_tm (str(20)): 예상 체결 시간
        - exp_pre_sig (str(20)): 예상 체결가 전일대비기호
        - stex_tp (str): 거래소 구분
    
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
      'api-id': 'ka50087',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gold_expt_exec'] = out_data['gold_expt_exec']
    
    return return_data

  def get_ka50100(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    금현물 시세정보
    메뉴 위치 : 국내주식 > 시세 > 금현물 시세정보(ka50100)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_pred_pre_sig (str(20)): 전일대비기호
      out_pred_pre (str(20)): 전일대비
      out_flu_rt (str(20)): 등락율
      out_trde_qty (str(20)): 거래량
      out_open_pric (str(20)): 시가
      out_high_pric (str(20)): 고가
      out_low_pric (str(20)): 저가
      out_pred_rt (str(20)): 전일비
      out_upl_pric (str(20)): 상한가
      out_lst_pric (str(20)): 하한가
      out_pred_close_pric (str(20)): 전일종가
    
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
      'api-id': 'ka50100',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_pred_pre_sig'] = out_data['pred_pre_sig']
    return_data['out_pred_pre'] = out_data['pred_pre']
    return_data['out_flu_rt'] = out_data['flu_rt']
    return_data['out_trde_qty'] = out_data['trde_qty']
    return_data['out_open_pric'] = out_data['open_pric']
    return_data['out_high_pric'] = out_data['high_pric']
    return_data['out_low_pric'] = out_data['low_pric']
    return_data['out_pred_rt'] = out_data['pred_rt']
    return_data['out_upl_pric'] = out_data['upl_pric']
    return_data['out_lst_pric'] = out_data['lst_pric']
    return_data['out_pred_close_pric'] = out_data['pred_close_pric']
    
    return return_data

  def get_ka50101(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_tic_scope: str):
    """
    금현물 호가
    메뉴 위치 : 국내주식 > 시세 > 금현물 호가(ka50101)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_tic_scope (str(2)): 틱범위(필수) 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gold_bid (list): 금현물호가
        - cntr_pric (str(20)): 체결가
        - pred_pre (str(20)): 전일 대비(원)
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 누적 거래량
        - acc_trde_prica (str(20)): 누적 거래대금
        - cntr_trde_qty (str(20)): 거래량(체결량)
        - tm (str(20)): 체결시간
        - pre_sig (str(20)): 전일대비기호
        - pri_sel_bid_unit (str(20)): 매도호가
        - pri_buy_bid_unit (str(20)): 매수호가
        - trde_pre (str(20)): 전일 거래량 대비 비율
        - trde_tern_rt (str): 전일 거래량 대비 순간 거래량 비율
        - cntr_str (str(20)): 체결강도
        - lpmmcm_nm_1 (str(20)): K.O 접근도
        - stex_tp (str(20)): 거래소구분
    
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
      'api-id': 'ka50101',
    }
    params = {
      'stk_cd': in_stk_cd,
      'tic_scope': in_tic_scope,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gold_bid'] = out_data['gold_bid']
    
    return return_data

  def get_ka90005(self, in_cont_yn: str, in_next_key: str, in_date: str, in_amt_qty_tp: str, in_mrkt_tp: str, in_min_tic_tp: str, in_stex_tp: str):
    """
    프로그램매매추이요청 시간대별
    메뉴 위치 : 국내주식 > 시세 > 프로그램매매추이요청 시간대별(ka90005)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_date (str(8)): 날짜(필수) YYYYMMDD
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1:금액(백만원), 2:수량(천주)
      in_mrkt_tp (str(10)): 시장구분(필수) 코스피- 거래소구분값 1일경우:P00101, 2일경우:P001_NX01, 3일경우:P001_AL01 코스닥- 거래소구분값 1일경우:P10102, 2일경우:P101_NX02, 3일경우:P101_AL02
      in_min_tic_tp (str(1)): 분틱구분(필수) 0:틱, 1:분
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_prm_trde_trnsn (list): 프로그램매매추이
        - cntr_tm (str(20)): 체결시간
        - dfrt_trde_sel (str(20)): 차익거래매도
        - dfrt_trde_buy (str(20)): 차익거래매수
        - dfrt_trde_netprps (str(20)): 차익거래순매수
        - ndiffpro_trde_sel (str(20)): 비차익거래매도
        - ndiffpro_trde_buy (str(20)): 비차익거래매수
        - ndiffpro_trde_netprps (str(20)): 비차익거래순매수
        - dfrt_trde_sell_qty (str(20)): 차익거래매도수량
        - dfrt_trde_buy_qty (str(20)): 차익거래매수수량
        - dfrt_trde_netprps_qty (str(20)): 차익거래순매수수량
        - ndiffpro_trde_sell_qty (str(20)): 비차익거래매도수량
        - ndiffpro_trde_buy_qty (str(20)): 비차익거래매수수량
        - ndiffpro_trde_netprps_qty (str(20)): 비차익거래순매수수량
        - all_sel (str(20)): 전체매도
        - all_buy (str(20)): 전체매수
        - all_netprps (str(20)): 전체순매수
        - kospi200 (str(20)): KOSPI200
        - basis (str(20)): BASIS
    
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
      'api-id': 'ka90005',
    }
    params = {
      'date': in_date,
      'amt_qty_tp': in_amt_qty_tp,
      'mrkt_tp': in_mrkt_tp,
      'min_tic_tp': in_min_tic_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_prm_trde_trnsn'] = out_data['prm_trde_trnsn']
    
    return return_data

  def get_ka90006(self, in_cont_yn: str, in_next_key: str, in_date: str, in_stex_tp: str):
    """
    프로그램매매차익잔고추이요청
    메뉴 위치 : 국내주식 > 시세 > 프로그램매매차익잔고추이요청(ka90006)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_date (str(8)): 날짜(필수) YYYYMMDD
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_prm_trde_dfrt_remn_trnsn (list): 프로그램매매차익잔고추이
        - dt (str(20)): 일자
        - buy_dfrt_trde_qty (str(20)): 매수차익거래수량
        - buy_dfrt_trde_amt (str(20)): 매수차익거래금액
        - buy_dfrt_trde_irds_amt (str(20)): 매수차익거래증감액
        - sel_dfrt_trde_qty (str(20)): 매도차익거래수량
        - sel_dfrt_trde_amt (str(20)): 매도차익거래금액
        - sel_dfrt_trde_irds_amt (str(20)): 매도차익거래증감액
    
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
      'api-id': 'ka90006',
    }
    params = {
      'date': in_date,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_prm_trde_dfrt_remn_trnsn'] = out_data['prm_trde_dfrt_remn_trnsn']
    
    return return_data

  def get_ka90007(self, in_cont_yn: str, in_next_key: str, in_date: str, in_amt_qty_tp: str, in_mrkt_tp: str, in_stex_tp: str):
    """
    프로그램매매누적추이요청
    메뉴 위치 : 국내주식 > 시세 > 프로그램매매누적추이요청(ka90007)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_date (str(8)): 날짜(필수) YYYYMMDD (종료일기준 1년간 데이터만 조회가능)
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1:금액, 2:수량
      in_mrkt_tp (str(5)): 시장구분(필수) 0:코스피 , 1:코스닥
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT, 3:통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_prm_trde_acc_trnsn (list): 프로그램매매누적추이
        - dt (str(20)): 일자
        - kospi200 (str(20)): KOSPI200
        - basis (str(20)): BASIS
        - dfrt_trde_tdy (str(20)): 차익거래당일
        - dfrt_trde_acc (str(20)): 차익거래누적
        - ndiffpro_trde_tdy (str(20)): 비차익거래당일
        - ndiffpro_trde_acc (str(20)): 비차익거래누적
        - all_tdy (str(20)): 전체당일
        - all_acc (str(20)): 전체누적
    
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
      'api-id': 'ka90007',
    }
    params = {
      'date': in_date,
      'amt_qty_tp': in_amt_qty_tp,
      'mrkt_tp': in_mrkt_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_prm_trde_acc_trnsn'] = out_data['prm_trde_acc_trnsn']
    
    return return_data

  def get_ka90008(self, in_cont_yn: str, in_next_key: str, in_amt_qty_tp: str, in_stk_cd: str, in_date: str):
    """
    종목시간별프로그램매매추이요청
    메뉴 위치 : 국내주식 > 시세 > 종목시간별프로그램매매추이요청(ka90008)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1:금액, 2:수량
      in_stk_cd (str(6)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_date (str(8)): 날짜(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_tm_prm_trde_trnsn (list): 종목시간별프로그램매매추이
        - tm (str(20)): 시간
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - prm_sell_amt (str(20)): 프로그램매도금액
        - prm_buy_amt (str(20)): 프로그램매수금액
        - prm_netprps_amt (str(20)): 프로그램순매수금액
        - prm_netprps_amt_irds (str(20)): 프로그램순매수금액증감
        - prm_sell_qty (str(20)): 프로그램매도수량
        - prm_buy_qty (str(20)): 프로그램매수수량
        - prm_netprps_qty (str(20)): 프로그램순매수수량
        - prm_netprps_qty_irds (str(20)): 프로그램순매수수량증감
        - base_pric_tm (str(20)): 기준가시간
        - dbrt_trde_rpy_sum (str(20)): 대차거래상환주수합
        - remn_rcvord_sum (str(20)): 잔고수주합
        - stex_tp (str(20)): 거래소구분. KRX , NXT , 통합
    
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
      'api-id': 'ka90008',
    }
    params = {
      'amt_qty_tp': in_amt_qty_tp,
      'stk_cd': in_stk_cd,
      'date': in_date,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_tm_prm_trde_trnsn'] = out_data['stk_tm_prm_trde_trnsn']
    
    return return_data

  def get_ka90010(self, in_cont_yn: str, in_next_key: str, in_date: str, in_amt_qty_tp: str, in_mrkt_tp: str, in_min_tic_tp: str, in_stex_tp: str):
    """
    프로그램매매추이요청 일자별
    메뉴 위치 : 국내주식 > 시세 > 프로그램매매추이요청 일자별(ka90010)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_date (str(8)): 날짜(필수) YYYYMMDD
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1:금액(백만원), 2:수량(천주)
      in_mrkt_tp (str(10)): 시장구분(필수) 코스피- 거래소구분값 1일경우:P00101, 2일경우:P001_NX01, 3일경우:P001_AL01 코스닥- 거래소구분값 1일경우:P10102, 2일경우:P101_NX02, 3일경우:P001_AL02
      in_min_tic_tp (str(1)): 분틱구분(필수) 0:틱, 1:분
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_prm_trde_trnsn (list): 프로그램매매추이
        - cntr_tm (str(20)): 체결시간
        - dfrt_trde_sel (str(20)): 차익거래매도
        - dfrt_trde_buy (str(20)): 차익거래매수
        - dfrt_trde_netprps (str(20)): 차익거래순매수
        - ndiffpro_trde_sel (str(20)): 비차익거래매도
        - ndiffpro_trde_buy (str(20)): 비차익거래매수
        - ndiffpro_trde_netprps (str(20)): 비차익거래순매수
        - dfrt_trde_sell_qty (str(20)): 차익거래매도수량
        - dfrt_trde_buy_qty (str(20)): 차익거래매수수량
        - dfrt_trde_netprps_qty (str(20)): 차익거래순매수수량
        - ndiffpro_trde_sell_qty (str(20)): 비차익거래매도수량
        - ndiffpro_trde_buy_qty (str(20)): 비차익거래매수수량
        - ndiffpro_trde_netprps_qty (str(20)): 비차익거래순매수수량
        - all_sel (str(20)): 전체매도
        - all_buy (str(20)): 전체매수
        - all_netprps (str(20)): 전체순매수
        - kospi200 (str(20)): KOSPI200
        - basis (str(20)): BASIS
    
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
      'api-id': 'ka90010',
    }
    params = {
      'date': in_date,
      'amt_qty_tp': in_amt_qty_tp,
      'mrkt_tp': in_mrkt_tp,
      'min_tic_tp': in_min_tic_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_prm_trde_trnsn'] = out_data['prm_trde_trnsn']
    
    return return_data

  def get_ka90013(self, in_cont_yn: str, in_next_key: str, in_amt_qty_tp: str, in_stk_cd: str, in_date: str):
    """
    종목일별프로그램매매추이요청
    메뉴 위치 : 국내주식 > 시세 > 종목일별프로그램매매추이요청(ka90013)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_amt_qty_tp (str(1)): 금액수량구분 1:금액, 2:수량
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_date (str(8)): 날짜 YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_daly_prm_trde_trnsn (list): 종목일별프로그램매매추이
        - dt (str(20)): 일자
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - prm_sell_amt (str(20)): 프로그램매도금액
        - prm_buy_amt (str(20)): 프로그램매수금액
        - prm_netprps_amt (str(20)): 프로그램순매수금액
        - prm_netprps_amt_irds (str(20)): 프로그램순매수금액증감
        - prm_sell_qty (str(20)): 프로그램매도수량
        - prm_buy_qty (str(20)): 프로그램매수수량
        - prm_netprps_qty (str(20)): 프로그램순매수수량
        - prm_netprps_qty_irds (str(20)): 프로그램순매수수량증감
        - base_pric_tm (str(20)): 기준가시간
        - dbrt_trde_rpy_sum (str(20)): 대차거래상환주수합
        - remn_rcvord_sum (str(20)): 잔고수주합
        - stex_tp (str(20)): 거래소구분. KRX , NXT , 통합
    
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
      'api-id': 'ka90013',
    }
    params = {
      'amt_qty_tp': in_amt_qty_tp,
      'stk_cd': in_stk_cd,
      'date': in_date,
    }
    url = '/api/dostk/mrkcond'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_daly_prm_trde_trnsn'] = out_data['stk_daly_prm_trde_trnsn']
    
    return return_data

  def get_ka10008(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    주식외국인종목별매매동향
    메뉴 위치 : 국내주식 > 기관/외국인 > 주식외국인종목별매매동향(ka10008)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_frgnr (list): 주식외국인
        - dt (str(20)): 일자
        - close_pric (str(20)): 종가
        - pred_pre (str(20)): 전일대비
        - trde_qty (str(20)): 거래량
        - chg_qty (str(20)): 변동수량
        - poss_stkcnt (str(20)): 보유주식수
        - wght (str(20)): 비중
        - gain_pos_stkcnt (str(20)): 취득가능주식수
        - frgnr_limit (str(20)): 외국인한도
        - frgnr_limit_irds (str(20)): 외국인한도증감
        - limit_exh_rt (str(20)): 한도소진률
    
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
      'api-id': 'ka10008',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/frgnistt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_frgnr'] = out_data['stk_frgnr']
    
    return return_data

  def get_ka10009(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    주식기관요청
    메뉴 위치 : 국내주식 > 기관/외국인 > 주식기관요청(ka10009)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_date (str(20)): 날짜
      out_close_pric (str(20)): 종가
      out_pre (str(20)): 대비
      out_orgn_dt_acc (str(20)): 기관기간누적
      out_orgn_daly_nettrde (str(20)): 기관일별순매매
      out_frgnr_daly_nettrde (str(20)): 외국인일별순매매
      out_frgnr_qota_rt (str(20)): 외국인지분율
    
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
      'api-id': 'ka10009',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/frgnistt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_date'] = out_data['date']
    return_data['out_close_pric'] = out_data['close_pric']
    return_data['out_pre'] = out_data['pre']
    return_data['out_orgn_dt_acc'] = out_data['orgn_dt_acc']
    return_data['out_orgn_daly_nettrde'] = out_data['orgn_daly_nettrde']
    return_data['out_frgnr_daly_nettrde'] = out_data['frgnr_daly_nettrde']
    return_data['out_frgnr_qota_rt'] = out_data['frgnr_qota_rt']
    
    return return_data

  def get_ka10131(self, in_cont_yn: str, in_next_key: str, in_dt: str, in_strt_dt: str, in_end_dt: str, in_mrkt_tp: str, in_netslmt_tp: str, in_stk_inds_tp: str, in_amt_qty_tp: str, in_stex_tp: str):
    """
    기관외국인연속매매현황요청
    메뉴 위치 : 국내주식 > 기관/외국인 > 기관외국인연속매매현황요청(ka10131)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dt (str(3)): 기간(필수) 1:최근일, 3:3일, 5:5일, 10:10일, 20:20일, 120:120일, 0:시작일자/종료일자로 조회
      in_strt_dt (str(8)): 시작일자 YYYYMMDD
      in_end_dt (str(8)): 종료일자 YYYYMMDD
      in_mrkt_tp (str(3)): 장구분(필수) 001:코스피, 101:코스닥
      in_netslmt_tp (str(1)): 순매도수구분(필수) 2:순매수(고정값)
      in_stk_inds_tp (str(1)): 종목업종구분(필수) 0:종목(주식),1:업종
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 0:금액, 1:수량
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT, 3:통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_orgn_frgnr_cont_trde_prst (list): 기관외국인연속매매현황
        - rank (str): 순위
        - stk_cd (str(6)): 종목코드
        - stk_nm (str(40)): 종목명
        - prid_stkpc_flu_rt (str): 기간중주가등락률
        - orgn_nettrde_amt (str): 기관순매매금액
        - orgn_nettrde_qty (str): 기관순매매량
        - orgn_cont_netprps_dys (str): 기관계연속순매수일수
        - orgn_cont_netprps_qty (str): 기관계연속순매수량
        - orgn_cont_netprps_amt (str): 기관계연속순매수금액
        - frgnr_nettrde_qty (str): 외국인순매매량
        - frgnr_nettrde_amt (str): 외국인순매매액
        - frgnr_cont_netprps_dys (str): 외국인연속순매수일수
        - frgnr_cont_netprps_qty (str): 외국인연속순매수량
        - frgnr_cont_netprps_amt (str): 외국인연속순매수금액
        - nettrde_qty (str): 순매매량
        - nettrde_amt (str): 순매매액
        - tot_cont_netprps_dys (str): 합계연속순매수일수
        - tot_cont_nettrde_qty (str): 합계연속순매매수량
        - tot_cont_netprps_amt (str): 합계연속순매수금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10131',
    }
    params = {
      'dt': in_dt,
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'mrkt_tp': in_mrkt_tp,
      'netslmt_tp': in_netslmt_tp,
      'stk_inds_tp': in_stk_inds_tp,
      'amt_qty_tp': in_amt_qty_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/frgnistt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_orgn_frgnr_cont_trde_prst'] = out_data['orgn_frgnr_cont_trde_prst']
    
    return return_data

  def get_ka52301(self, in_cont_yn: str, in_next_key: str):
    """
    금현물투자자현황
    메뉴 위치 : 국내주식 > 기관/외국인 > 금현물투자자현황(ka52301)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_inve_trad_stat (list): 금현물투자자현황
        - all_dfrt_trst_sell_qty (str(20)): 투자자별 매도 수량(천)
        - sell_qty_irds (str(20)): 투자자별 매도 수량 증감(천)
        - all_dfrt_trst_sell_amt (str(20)): 투자자별 매도 금액(억)
        - sell_amt_irds (str(20)): 투자자별 매도 금액 증감(억)
        - all_dfrt_trst_buy_qty (str(20)): 투자자별 매수 수량(천)
        - buy_qty_irds (str(20)): 투자자별 매수 수량 증감(천)
        - all_dfrt_trst_buy_amt (str(20)): 투자자별 매수 금액(억)
        - buy_amt_irds (str(20)): 투자자별 매수 금액 증감(억)
        - all_dfrt_trst_netprps_qty (str(20)): 투자자별 순매수 수량(천)
        - netprps_qty_irds (str(20)): 투자자별 순매수 수량 증감(천)
        - all_dfrt_trst_netprps_amt (str(20)): 투자자별 순매수 금액(억)
        - netprps_amt_irds (str(20)): 투자자별 순매수 금액 증감(억)
        - sell_uv (str(20)): 투자자별 매도 단가
        - buy_uv (str(20)): 투자자별 매수 단가
        - stk_nm (str(20)): 투자자 구분명
        - acc_netprps_amt (str(20)): 누적 순매수 금액(억)
        - acc_netprps_qty (str(20)): 누적 순매수 수량(천)
        - stk_cd (str(20)): 투자자 코드
    
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
      'api-id': 'ka52301',
    }
    params = {
    }
    url = '/api/dostk/frgnistt'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_inve_trad_stat'] = out_data['inve_trad_stat']
    
    return return_data

  def get_ka10010(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    업종프로그램요청
    메뉴 위치 : 국내주식 > 업종 > 업종프로그램요청(ka10010)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_dfrt_trst_sell_qty (str(20)): 차익위탁매도수량
      out_dfrt_trst_sell_amt (str(20)): 차익위탁매도금액
      out_dfrt_trst_buy_qty (str(20)): 차익위탁매수수량
      out_dfrt_trst_buy_amt (str(20)): 차익위탁매수금액
      out_dfrt_trst_netprps_qty (str(20)): 차익위탁순매수수량
      out_dfrt_trst_netprps_amt (str(20)): 차익위탁순매수금액
      out_ndiffpro_trst_sell_qty (str(20)): 비차익위탁매도수량
      out_ndiffpro_trst_sell_amt (str(20)): 비차익위탁매도금액
      out_ndiffpro_trst_buy_qty (str(20)): 비차익위탁매수수량
      out_ndiffpro_trst_buy_amt (str(20)): 비차익위탁매수금액
      out_ndiffpro_trst_netprps_qty (str(20)): 비차익위탁순매수수량
      out_ndiffpro_trst_netprps_amt (str(20)): 비차익위탁순매수금액
      out_all_dfrt_trst_sell_qty (str(20)): 전체차익위탁매도수량
      out_all_dfrt_trst_sell_amt (str(20)): 전체차익위탁매도금액
      out_all_dfrt_trst_buy_qty (str(20)): 전체차익위탁매수수량
      out_all_dfrt_trst_buy_amt (str(20)): 전체차익위탁매수금액
      out_all_dfrt_trst_netprps_qty (str(20)): 전체차익위탁순매수수량
      out_all_dfrt_trst_netprps_amt (str(20)): 전체차익위탁순매수금액
    
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
      'api-id': 'ka10010',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/sect'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_dfrt_trst_sell_qty'] = out_data['dfrt_trst_sell_qty']
    return_data['out_dfrt_trst_sell_amt'] = out_data['dfrt_trst_sell_amt']
    return_data['out_dfrt_trst_buy_qty'] = out_data['dfrt_trst_buy_qty']
    return_data['out_dfrt_trst_buy_amt'] = out_data['dfrt_trst_buy_amt']
    return_data['out_dfrt_trst_netprps_qty'] = out_data['dfrt_trst_netprps_qty']
    return_data['out_dfrt_trst_netprps_amt'] = out_data['dfrt_trst_netprps_amt']
    return_data['out_ndiffpro_trst_sell_qty'] = out_data['ndiffpro_trst_sell_qty']
    return_data['out_ndiffpro_trst_sell_amt'] = out_data['ndiffpro_trst_sell_amt']
    return_data['out_ndiffpro_trst_buy_qty'] = out_data['ndiffpro_trst_buy_qty']
    return_data['out_ndiffpro_trst_buy_amt'] = out_data['ndiffpro_trst_buy_amt']
    return_data['out_ndiffpro_trst_netprps_qty'] = out_data['ndiffpro_trst_netprps_qty']
    return_data['out_ndiffpro_trst_netprps_amt'] = out_data['ndiffpro_trst_netprps_amt']
    return_data['out_all_dfrt_trst_sell_qty'] = out_data['all_dfrt_trst_sell_qty']
    return_data['out_all_dfrt_trst_sell_amt'] = out_data['all_dfrt_trst_sell_amt']
    return_data['out_all_dfrt_trst_buy_qty'] = out_data['all_dfrt_trst_buy_qty']
    return_data['out_all_dfrt_trst_buy_amt'] = out_data['all_dfrt_trst_buy_amt']
    return_data['out_all_dfrt_trst_netprps_qty'] = out_data['all_dfrt_trst_netprps_qty']
    return_data['out_all_dfrt_trst_netprps_amt'] = out_data['all_dfrt_trst_netprps_amt']
    
    return return_data

  def get_ka10051(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_amt_qty_tp: str, in_base_dt: str, in_stex_tp: str):
    """
    업종별투자자순매수요청
    메뉴 위치 : 국내주식 > 업종 > 업종별투자자순매수요청(ka10051)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(1)): 시장구분(필수) 코스피:0, 코스닥:1
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 금액:0, 수량:1
      in_base_dt (str(8)): 기준일자 YYYYMMDD
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT, 3:통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_inds_netprps (list): 업종별순매수
        - inds_cd (str(20)): 업종코드
        - inds_nm (str(20)): 업종명
        - cur_prc (str(20)): 현재가
        - pre_smbol (str(20)): 대비부호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - sc_netprps (str(20)): 증권순매수
        - insrnc_netprps (str(20)): 보험순매수
        - invtrt_netprps (str(20)): 투신순매수
        - bank_netprps (str(20)): 은행순매수
        - jnsinkm_netprps (str(20)): 종신금순매수
        - endw_netprps (str(20)): 기금순매수
        - etc_corp_netprps (str(20)): 기타법인순매수
        - ind_netprps (str(20)): 개인순매수
        - frgnr_netprps (str(20)): 외국인순매수
        - native_trmt_frgnr_netprps (str(20)): 내국인대우외국인순매수
        - natn_netprps (str(20)): 국가순매수
        - samo_fund_netprps (str(20)): 사모펀드순매수
        - orgn_netprps (str(20)): 기관계순매수
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10051',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'amt_qty_tp': in_amt_qty_tp,
      'base_dt': in_base_dt,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/sect'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_inds_netprps'] = out_data['inds_netprps']
    
    return return_data

  def get_ka20001(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_inds_cd: str):
    """
    업종현재가요청
    메뉴 위치 : 국내주식 > 업종 > 업종현재가요청(ka20001)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(1)): 시장구분(필수) 0:코스피, 1:코스닥, 2:코스피200
      in_inds_cd (str(3)): 업종코드(필수) 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_cur_prc (str(20)): 현재가
      out_pred_pre_sig (str(20)): 전일대비기호
      out_pred_pre (str(20)): 전일대비
      out_flu_rt (str(20)): 등락률
      out_trde_qty (str(20)): 거래량
      out_trde_prica (str(20)): 거래대금
      out_trde_frmatn_stk_num (str(20)): 거래형성종목수
      out_trde_frmatn_rt (str(20)): 거래형성비율
      out_open_pric (str(20)): 시가
      out_high_pric (str(20)): 고가
      out_low_pric (str(20)): 저가
      out_upl (str(20)): 상한
      out_rising (str(20)): 상승
      out_stdns (str(20)): 보합
      out_fall (str(20)): 하락
      out_lst (str(20)): 하한
      out_52wk_hgst_pric (str(20)): 52주최고가
      out_52wk_hgst_pric_dt (str(20)): 52주최고가일
      out_52wk_hgst_pric_pre_rt (str(20)): 52주최고가대비율
      out_52wk_lwst_pric (str(20)): 52주최저가
      out_52wk_lwst_pric_dt (str(20)): 52주최저가일
      out_52wk_lwst_pric_pre_rt (str(20)): 52주최저가대비율
      out_inds_cur_prc_tm (list): 업종현재가_시간별
        - tm_n (str(20)): 시간n
        - cur_prc_n (str(20)): 현재가n
        - pred_pre_sig_n (str(20)): 전일대비기호n
        - pred_pre_n (str(20)): 전일대비n
        - flu_rt_n (str(20)): 등락률n
        - trde_qty_n (str(20)): 거래량n
        - acc_trde_qty_n (str(20)): 누적거래량n
    
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
      'api-id': 'ka20001',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'inds_cd': in_inds_cd,
    }
    url = '/api/dostk/sect'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_cur_prc'] = out_data['cur_prc']
    return_data['out_pred_pre_sig'] = out_data['pred_pre_sig']
    return_data['out_pred_pre'] = out_data['pred_pre']
    return_data['out_flu_rt'] = out_data['flu_rt']
    return_data['out_trde_qty'] = out_data['trde_qty']
    return_data['out_trde_prica'] = out_data['trde_prica']
    return_data['out_trde_frmatn_stk_num'] = out_data['trde_frmatn_stk_num']
    return_data['out_trde_frmatn_rt'] = out_data['trde_frmatn_rt']
    return_data['out_open_pric'] = out_data['open_pric']
    return_data['out_high_pric'] = out_data['high_pric']
    return_data['out_low_pric'] = out_data['low_pric']
    return_data['out_upl'] = out_data['upl']
    return_data['out_rising'] = out_data['rising']
    return_data['out_stdns'] = out_data['stdns']
    return_data['out_fall'] = out_data['fall']
    return_data['out_lst'] = out_data['lst']
    return_data['out_52wk_hgst_pric'] = out_data['52wk_hgst_pric']
    return_data['out_52wk_hgst_pric_dt'] = out_data['52wk_hgst_pric_dt']
    return_data['out_52wk_hgst_pric_pre_rt'] = out_data['52wk_hgst_pric_pre_rt']
    return_data['out_52wk_lwst_pric'] = out_data['52wk_lwst_pric']
    return_data['out_52wk_lwst_pric_dt'] = out_data['52wk_lwst_pric_dt']
    return_data['out_52wk_lwst_pric_pre_rt'] = out_data['52wk_lwst_pric_pre_rt']
    return_data['out_inds_cur_prc_tm'] = out_data['inds_cur_prc_tm']
    
    return return_data

  def get_ka20002(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_inds_cd: str, in_stex_tp: str):
    """
    업종별주가요청
    메뉴 위치 : 국내주식 > 업종 > 업종별주가요청(ka20002)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(1)): 시장구분(필수) 0:코스피, 1:코스닥, 2:코스피200
      in_inds_cd (str(3)): 업종코드(필수) 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT, 3:통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_inds_stkpc (list): 업종별주가
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - now_trde_qty (str(20)): 현재거래량
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
    
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
      'api-id': 'ka20002',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'inds_cd': in_inds_cd,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/sect'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_inds_stkpc'] = out_data['inds_stkpc']
    
    return return_data

  def get_ka20003(self, in_cont_yn: str, in_next_key: str, in_inds_cd: str):
    """
    전업종지수요청
    메뉴 위치 : 국내주식 > 업종 > 전업종지수요청(ka20003)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_inds_cd (str(3)): 업종코드(필수) 001:종합(KOSPI), 101:종합(KOSDAQ)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_all_inds_idex (list): 전업종지수
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - trde_qty (str(20)): 거래량
        - wght (str(20)): 비중
        - trde_prica (str(20)): 거래대금
        - upl (str(20)): 상한
        - rising (str(20)): 상승
        - stdns (str(20)): 보합
        - fall (str(20)): 하락
        - lst (str(20)): 하한
        - flo_stk_num (str(20)): 상장종목수
    
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
      'api-id': 'ka20003',
    }
    params = {
      'inds_cd': in_inds_cd,
    }
    url = '/api/dostk/sect'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_all_inds_idex'] = out_data['all_inds_idex']
    
    return return_data

  def get_ka20009(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_inds_cd: str):
    """
    업종현재가일별요청
    메뉴 위치 : 국내주식 > 업종 > 업종현재가일별요청(ka20009)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(1)): 시장구분(필수) 0:코스피, 1:코스닥, 2:코스피200
      in_inds_cd (str(3)): 업종코드(필수) 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_cur_prc (str(20)): 현재가
      out_pred_pre_sig (str(20)): 전일대비기호
      out_pred_pre (str(20)): 전일대비
      out_flu_rt (str(20)): 등락률
      out_trde_qty (str(20)): 거래량
      out_trde_prica (str(20)): 거래대금
      out_trde_frmatn_stk_num (str(20)): 거래형성종목수
      out_trde_frmatn_rt (str(20)): 거래형성비율
      out_open_pric (str(20)): 시가
      out_high_pric (str(20)): 고가
      out_low_pric (str(20)): 저가
      out_upl (str(20)): 상한
      out_rising (str(20)): 상승
      out_stdns (str(20)): 보합
      out_fall (str(20)): 하락
      out_lst (str(20)): 하한
      out_52wk_hgst_pric (str(20)): 52주최고가
      out_52wk_hgst_pric_dt (str(20)): 52주최고가일
      out_52wk_hgst_pric_pre_rt (str(20)): 52주최고가대비율
      out_52wk_lwst_pric (str(20)): 52주최저가
      out_52wk_lwst_pric_dt (str(20)): 52주최저가일
      out_52wk_lwst_pric_pre_rt (str(20)): 52주최저가대비율
      out_inds_cur_prc_daly_rept (list): 업종현재가_일별반복
        - dt_n (str(20)): 일자n
        - cur_prc_n (str(20)): 현재가n
        - pred_pre_sig_n (str(20)): 전일대비기호n
        - pred_pre_n (str(20)): 전일대비n
        - flu_rt_n (str(20)): 등락률n
        - acc_trde_qty_n (str(20)): 누적거래량n
    
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
      'api-id': 'ka20009',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'inds_cd': in_inds_cd,
    }
    url = '/api/dostk/sect'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_cur_prc'] = out_data['cur_prc']
    return_data['out_pred_pre_sig'] = out_data['pred_pre_sig']
    return_data['out_pred_pre'] = out_data['pred_pre']
    return_data['out_flu_rt'] = out_data['flu_rt']
    return_data['out_trde_qty'] = out_data['trde_qty']
    return_data['out_trde_prica'] = out_data['trde_prica']
    return_data['out_trde_frmatn_stk_num'] = out_data['trde_frmatn_stk_num']
    return_data['out_trde_frmatn_rt'] = out_data['trde_frmatn_rt']
    return_data['out_open_pric'] = out_data['open_pric']
    return_data['out_high_pric'] = out_data['high_pric']
    return_data['out_low_pric'] = out_data['low_pric']
    return_data['out_upl'] = out_data['upl']
    return_data['out_rising'] = out_data['rising']
    return_data['out_stdns'] = out_data['stdns']
    return_data['out_fall'] = out_data['fall']
    return_data['out_lst'] = out_data['lst']
    return_data['out_52wk_hgst_pric'] = out_data['52wk_hgst_pric']
    return_data['out_52wk_hgst_pric_dt'] = out_data['52wk_hgst_pric_dt']
    return_data['out_52wk_hgst_pric_pre_rt'] = out_data['52wk_hgst_pric_pre_rt']
    return_data['out_52wk_lwst_pric'] = out_data['52wk_lwst_pric']
    return_data['out_52wk_lwst_pric_dt'] = out_data['52wk_lwst_pric_dt']
    return_data['out_52wk_lwst_pric_pre_rt'] = out_data['52wk_lwst_pric_pre_rt']
    return_data['out_inds_cur_prc_daly_rept'] = out_data['inds_cur_prc_daly_rept']
    
    return return_data

  def get_ka10014(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_tm_tp: str, in_strt_dt: str, in_end_dt: str):
    """
    공매도추이요청
    메뉴 위치 : 국내주식 > 공매도 > 공매도추이요청(ka10014)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_tm_tp (str(1)): 시간구분 0:시작일, 1:기간
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD
      in_end_dt (str(8)): 종료일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_shrts_trnsn (list): 공매도추이
        - dt (str(20)): 일자
        - close_pric (str(20)): 종가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - shrts_qty (str(20)): 공매도량
        - ovr_shrts_qty (str(20)): 누적공매도량. 설정 기간의 공매도량 합산데이터
        - trde_wght (str(20)): 매매비중
        - shrts_trde_prica (str(20)): 공매도거래대금
        - shrts_avg_pric (str(20)): 공매도평균가
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10014',
    }
    params = {
      'stk_cd': in_stk_cd,
      'tm_tp': in_tm_tp,
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
    }
    url = '/api/dostk/shsa'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_shrts_trnsn'] = out_data['shrts_trnsn']
    
    return return_data

  def get_ka10020(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_sort_tp: str, in_trde_qty_tp: str, in_stk_cnd: str, in_crd_cnd: str, in_stex_tp: str):
    """
    호가잔량상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 호가잔량상위요청(ka10020)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 001:코스피, 101:코스닥
      in_sort_tp (str(1)): 정렬구분(필수) 1:순매수잔량순, 2:순매도잔량순, 3:매수비율순, 4:매도비율순
      in_trde_qty_tp (str(4)): 거래량구분(필수) 0000:장시작전(0주이상), 0010:만주이상, 0050:5만주이상, 00100:10만주이상
      in_stk_cnd (str(1)): 종목조건(필수) 0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기
      in_crd_cnd (str(1)): 신용조건(필수) 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_bid_req_upper (list): 호가잔량상위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - trde_qty (str(20)): 거래량
        - tot_sel_req (str(20)): 총매도잔량
        - tot_buy_req (str(20)): 총매수잔량
        - netprps_req (str(20)): 순매수잔량
        - buy_rt (str(20)): 매수비율
    
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
      'api-id': 'ka10020',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'sort_tp': in_sort_tp,
      'trde_qty_tp': in_trde_qty_tp,
      'stk_cnd': in_stk_cnd,
      'crd_cnd': in_crd_cnd,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_bid_req_upper'] = out_data['bid_req_upper']
    
    return return_data

  def get_ka10021(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_trde_tp: str, in_sort_tp: str, in_tm_tp: str, in_trde_qty_tp: str, in_stk_cnd: str, in_stex_tp: str):
    """
    호가잔량급증요청
    메뉴 위치 : 국내주식 > 순위정보 > 호가잔량급증요청(ka10021)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 001:코스피, 101:코스닥
      in_trde_tp (str(1)): 매매구분(필수) 1:매수잔량, 2:매도잔량
      in_sort_tp (str(1)): 정렬구분(필수) 1:급증량, 2:급증률
      in_tm_tp (str(2)): 시간구분(필수) 분 입력
      in_trde_qty_tp (str(4)): 거래량구분(필수) 1:천주이상, 5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상
      in_stk_cnd (str(1)): 종목조건(필수) 0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_bid_req_sdnin (list): 호가잔량급증
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - int (str(20)): 기준률
        - now (str(20)): 현재
        - sdnin_qty (str(20)): 급증수량
        - sdnin_rt (str(20)): 급증률
        - tot_buy_qty (str(20)): 총매수량
    
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
      'api-id': 'ka10021',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'trde_tp': in_trde_tp,
      'sort_tp': in_sort_tp,
      'tm_tp': in_tm_tp,
      'trde_qty_tp': in_trde_qty_tp,
      'stk_cnd': in_stk_cnd,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_bid_req_sdnin'] = out_data['bid_req_sdnin']
    
    return return_data

  def get_ka10022(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_rt_tp: str, in_tm_tp: str, in_trde_qty_tp: str, in_stk_cnd: str, in_stex_tp: str):
    """
    잔량율급증요청
    메뉴 위치 : 국내주식 > 순위정보 > 잔량율급증요청(ka10022)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 001:코스피, 101:코스닥
      in_rt_tp (str(1)): 비율구분(필수) 1:매수/매도비율, 2:매도/매수비율
      in_tm_tp (str(2)): 시간구분(필수) 분 입력
      in_trde_qty_tp (str(1)): 거래량구분(필수) 5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상
      in_stk_cnd (str(1)): 종목조건(필수) 0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_req_rt_sdnin (list): 잔량율급증
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - int (str(20)): 기준률
        - now_rt (str(20)): 현재비율
        - sdnin_rt (str(20)): 급증률
        - tot_sel_req (str(20)): 총매도잔량
        - tot_buy_req (str(20)): 총매수잔량
    
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
      'api-id': 'ka10022',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'rt_tp': in_rt_tp,
      'tm_tp': in_tm_tp,
      'trde_qty_tp': in_trde_qty_tp,
      'stk_cnd': in_stk_cnd,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_req_rt_sdnin'] = out_data['req_rt_sdnin']
    
    return return_data

  def get_ka10023(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_sort_tp: str, in_tm_tp: str, in_trde_qty_tp: str, in_tm: str, in_stk_cnd: str, in_pric_tp: str, in_stex_tp: str):
    """
    거래량급증요청
    메뉴 위치 : 국내주식 > 순위정보 > 거래량급증요청(ka10023)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_sort_tp (str(1)): 정렬구분(필수) 1:급증량, 2:급증률, 3:급감량, 4:급감률
      in_tm_tp (str(1)): 시간구분(필수) 1:분, 2:전일
      in_trde_qty_tp (str(1)): 거래량구분(필수) 5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상
      in_tm (str(2)): 시간 분 입력
      in_stk_cnd (str(1)): 종목조건(필수) 0:전체조회, 1:관리종목제외, 3:우선주제외, 11:정리매매종목제외, 4:관리종목,우선주제외, 5:증100제외, 6:증100만보기, 13:증60만보기, 12:증50만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 17:ETN제외, 14:ETF제외, 18:ETF+ETN제외, 15:스팩제외, 20:ETF+ETN+스팩제외
      in_pric_tp (str(1)): 가격구분(필수) 0:전체조회, 2:5만원이상, 5:1만원이상, 6:5천원이상, 8:1천원이상, 9:10만원이상
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_trde_qty_sdnin (list): 거래량급증
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - prev_trde_qty (str(20)): 이전거래량
        - now_trde_qty (str(20)): 현재거래량
        - sdnin_qty (str(20)): 급증량
        - sdnin_rt (str(20)): 급증률
    
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
      'api-id': 'ka10023',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'sort_tp': in_sort_tp,
      'tm_tp': in_tm_tp,
      'trde_qty_tp': in_trde_qty_tp,
      'tm': in_tm,
      'stk_cnd': in_stk_cnd,
      'pric_tp': in_pric_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_trde_qty_sdnin'] = out_data['trde_qty_sdnin']
    
    return return_data

  def get_ka10027(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_sort_tp: str, in_trde_qty_cnd: str, in_stk_cnd: str, in_crd_cnd: str, in_updown_incls: str, in_pric_cnd: str, in_trde_prica_cnd: str, in_stex_tp: str):
    """
    전일대비등락률상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 전일대비등락률상위요청(ka10027)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_sort_tp (str(1)): 정렬구분(필수) 1:상승률, 2:상승폭, 3:하락률, 4:하락폭, 5:보합
      in_trde_qty_cnd (str(5)): 거래량조건(필수) 0000:전체조회, 0010:만주이상, 0050:5만주이상, 0100:10만주이상, 0150:15만주이상, 0200:20만주이상, 0300:30만주이상, 0500:50만주이상, 1000:백만주이상
      in_stk_cnd (str(2)): 종목조건(필수) 0:전체조회, 1:관리종목제외, 4:우선주+관리주제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 11:정리매매종목제외, 12:증50만보기, 13:증60만보기, 14:ETF제외, 15:스펙제외, 16:ETF+ETN제외
      in_crd_cnd (str(1)): 신용조건(필수) 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체
      in_updown_incls (str(2)): 상하한포함(필수) 0:불 포함, 1:포함
      in_pric_cnd (str(2)): 가격조건(필수) 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~5천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상, 10: 1만원미만
      in_trde_prica_cnd (str(4)): 거래대금조건(필수) 0:전체조회, 3:3천만원이상, 5:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_pred_pre_flu_rt_upper (list): 전일대비등락률상위
        - stk_cls (str(20)): 종목분류
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - sel_req (str(20)): 매도잔량
        - buy_req (str(20)): 매수잔량
        - now_trde_qty (str(20)): 현재거래량
        - cntr_str (str(20)): 체결강도
        - cnt (str(20)): 횟수
    
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
      'api-id': 'ka10027',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'sort_tp': in_sort_tp,
      'trde_qty_cnd': in_trde_qty_cnd,
      'stk_cnd': in_stk_cnd,
      'crd_cnd': in_crd_cnd,
      'updown_incls': in_updown_incls,
      'pric_cnd': in_pric_cnd,
      'trde_prica_cnd': in_trde_prica_cnd,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_pred_pre_flu_rt_upper'] = out_data['pred_pre_flu_rt_upper']
    
    return return_data

  def get_ka10029(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_sort_tp: str, in_trde_qty_cnd: str, in_stk_cnd: str, in_crd_cnd: str, in_pric_cnd: str, in_stex_tp: str):
    """
    예상체결등락률상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 예상체결등락률상위요청(ka10029)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_sort_tp (str(1)): 정렬구분(필수) 1:상승률, 2:상승폭, 3:보합, 4:하락률, 5:하락폭, 6:체결량, 7:상한, 8:하한
      in_trde_qty_cnd (str(5)): 거래량조건(필수) 0:전체조회, 1;천주이상, 3:3천주, 5:5천주, 10:만주이상, 50:5만주이상, 100:10만주이상
      in_stk_cnd (str(2)): 종목조건(필수) 0:전체조회, 1:관리종목제외, 3:우선주제외, 4:관리종목,우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 11:정리매매종목제외, 12:증50만보기, 13:증60만보기, 14:ETF제외, 15:스팩제외, 16:ETF+ETN제외
      in_crd_cnd (str(1)): 신용조건(필수) 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 5:신용한도초과제외, 7:신용융자E군, 8:신용대주, 9:신용융자전체
      in_pric_cnd (str(2)): 가격조건(필수) 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~5천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상, 10:1만원미만
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_exp_cntr_flu_rt_upper (list): 예상체결등락률상위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - exp_cntr_pric (str(20)): 예상체결가
        - base_pric (str(20)): 기준가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - exp_cntr_qty (str(20)): 예상체결량
        - sel_req (str(20)): 매도잔량
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
        - buy_req (str(20)): 매수잔량
    
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
      'api-id': 'ka10029',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'sort_tp': in_sort_tp,
      'trde_qty_cnd': in_trde_qty_cnd,
      'stk_cnd': in_stk_cnd,
      'crd_cnd': in_crd_cnd,
      'pric_cnd': in_pric_cnd,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_exp_cntr_flu_rt_upper'] = out_data['exp_cntr_flu_rt_upper']
    
    return return_data

  def get_ka10030(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_sort_tp: str, in_mang_stk_incls: str, in_crd_tp: str, in_trde_qty_tp: str, in_pric_tp: str, in_trde_prica_tp: str, in_mrkt_open_tp: str, in_stex_tp: str):
    """
    당일거래량상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 당일거래량상위요청(ka10030)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_sort_tp (str(1)): 정렬구분(필수) 1:거래량, 2:거래회전율, 3:거래대금
      in_mang_stk_incls (str(1)): 관리종목포함(필수) 0:관리종목 포함, 1:관리종목 미포함, 3:우선주제외, 11:정리매매종목제외, 4:관리종목, 우선주제외, 5:증100제외, 6:증100마나보기, 13:증60만보기, 12:증50만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 14:ETF제외, 15:스팩제외, 16:ETF+ETN제외
      in_crd_tp (str(1)): 신용구분(필수) 0:전체조회, 9:신용융자전체, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 8:신용대주
      in_trde_qty_tp (str(1)): 거래량구분(필수) 0:전체조회, 5:5천주이상, 10:1만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:500만주이상, 1000:백만주이상
      in_pric_tp (str(1)): 가격구분(필수) 0:전체조회, 1:1천원미만, 2:1천원이상, 3:1천원~2천원, 4:2천원~5천원, 5:5천원이상, 6:5천원~1만원, 10:1만원미만, 7:1만원이상, 8:5만원이상, 9:10만원이상
      in_trde_prica_tp (str(1)): 거래대금구분(필수) 0:전체조회, 1:1천만원이상, 3:3천만원이상, 4:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상
      in_mrkt_open_tp (str(1)): 장운영구분(필수) 0:전체조회, 1:장중, 2:장전시간외, 3:장후시간외
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tdy_trde_qty_upper (list): 당일거래량상위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - trde_qty (str(20)): 거래량
        - pred_rt (str(20)): 전일비
        - trde_tern_rt (str(20)): 거래회전율
        - trde_amt (str(20)): 거래금액
        - opmr_trde_qty (str(20)): 장중거래량
        - opmr_pred_rt (str(20)): 장중전일비
        - opmr_trde_rt (str(20)): 장중거래회전율
        - opmr_trde_amt (str(20)): 장중거래금액
        - af_mkrt_trde_qty (str(20)): 장후거래량
        - af_mkrt_pred_rt (str(20)): 장후전일비
        - af_mkrt_trde_rt (str(20)): 장후거래회전율
        - af_mkrt_trde_amt (str(20)): 장후거래금액
        - bf_mkrt_trde_qty (str(20)): 장전거래량
        - bf_mkrt_pred_rt (str(20)): 장전전일비
        - bf_mkrt_trde_rt (str(20)): 장전거래회전율
        - bf_mkrt_trde_amt (str(20)): 장전거래금액
    
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
      'api-id': 'ka10030',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'sort_tp': in_sort_tp,
      'mang_stk_incls': in_mang_stk_incls,
      'crd_tp': in_crd_tp,
      'trde_qty_tp': in_trde_qty_tp,
      'pric_tp': in_pric_tp,
      'trde_prica_tp': in_trde_prica_tp,
      'mrkt_open_tp': in_mrkt_open_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_tdy_trde_qty_upper'] = out_data['tdy_trde_qty_upper']
    
    return return_data

  def get_ka10031(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_qry_tp: str, in_rank_strt: str, in_rank_end: str, in_stex_tp: str):
    """
    전일거래량상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 전일거래량상위요청(ka10031)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_qry_tp (str(1)): 조회구분(필수) 1:전일거래량 상위100종목, 2:전일거래대금 상위100종목
      in_rank_strt (str(3)): 순위시작(필수) 0 ~ 100 값 중에  조회를 원하는 순위 시작값
      in_rank_end (str(3)): 순위끝(필수) 0 ~ 100 값 중에  조회를 원하는 순위 끝값
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_pred_trde_qty_upper (list): 전일거래량상위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - trde_qty (str(20)): 거래량
    
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
      'api-id': 'ka10031',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'qry_tp': in_qry_tp,
      'rank_strt': in_rank_strt,
      'rank_end': in_rank_end,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_pred_trde_qty_upper'] = out_data['pred_trde_qty_upper']
    
    return return_data

  def get_ka10032(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_mang_stk_incls: str, in_stex_tp: str):
    """
    거래대금상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 거래대금상위요청(ka10032)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_mang_stk_incls (str(1)): 관리종목포함(필수) 0:관리종목 미포함, 1:관리종목 포함
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_trde_prica_upper (list): 거래대금상위
        - stk_cd (str(20)): 종목코드
        - now_rank (str(20)): 현재순위
        - pred_rank (str(20)): 전일순위
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
        - now_trde_qty (str(20)): 현재거래량
        - pred_trde_qty (str(20)): 전일거래량
        - trde_prica (str(20)): 거래대금
    
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
      'api-id': 'ka10032',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'mang_stk_incls': in_mang_stk_incls,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_trde_prica_upper'] = out_data['trde_prica_upper']
    
    return return_data

  def get_ka10033(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_trde_qty_tp: str, in_stk_cnd: str, in_updown_incls: str, in_crd_cnd: str, in_stex_tp: str):
    """
    신용비율상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 신용비율상위요청(ka10033)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_trde_qty_tp (str(3)): 거래량구분(필수) 0:전체조회, 10:만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상
      in_stk_cnd (str(1)): 종목조건(필수) 0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기
      in_updown_incls (str(1)): 상하한포함(필수) 0:상하한 미포함, 1:상하한포함
      in_crd_cnd (str(1)): 신용조건(필수) 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_crd_rt_upper (list): 신용비율상위
        - stk_infr (str(20)): 종목정보
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - crd_rt (str(20)): 신용비율
        - sel_req (str(20)): 매도잔량
        - buy_req (str(20)): 매수잔량
        - now_trde_qty (str(20)): 현재거래량
    
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
      'api-id': 'ka10033',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'trde_qty_tp': in_trde_qty_tp,
      'stk_cnd': in_stk_cnd,
      'updown_incls': in_updown_incls,
      'crd_cnd': in_crd_cnd,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_crd_rt_upper'] = out_data['crd_rt_upper']
    
    return return_data

  def get_ka10034(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_trde_tp: str, in_dt: str, in_stex_tp: str):
    """
    외인기간별매매상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 외인기간별매매상위요청(ka10034)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_trde_tp (str(1)): 매매구분(필수) 1:순매도, 2:순매수, 3:순매매
      in_dt (str(2)): 기간(필수) 0:당일, 1:전일, 5:5일, 10;10일, 20:20일, 60:60일
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT, 3:통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_for_dt_trde_upper (list): 외인기간별매매상위
        - rank (str(20)): 순위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
        - trde_qty (str(20)): 거래량
        - netprps_qty (str(20)): 순매수량
        - gain_pos_stkcnt (str(20)): 취득가능주식수
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10034',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'trde_tp': in_trde_tp,
      'dt': in_dt,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_for_dt_trde_upper'] = out_data['for_dt_trde_upper']
    
    return return_data

  def get_ka10035(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_trde_tp: str, in_base_dt_tp: str, in_stex_tp: str):
    """
    외인연속순매매상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 외인연속순매매상위요청(ka10035)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_trde_tp (str(1)): 매매구분(필수) 1:연속순매도, 2:연속순매수
      in_base_dt_tp (str(1)): 기준일구분(필수) 0:당일기준, 1:전일기준
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT, 3:통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_for_cont_nettrde_upper (list): 외인연속순매매상위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - dm1 (str(20)): D-1
        - dm2 (str(20)): D-2
        - dm3 (str(20)): D-3
        - tot (str(20)): 합계
        - limit_exh_rt (str(20)): 한도소진율
        - pred_pre_1 (str(20)): 전일대비1
        - pred_pre_2 (str(20)): 전일대비2
        - pred_pre_3 (str(20)): 전일대비3
    
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
      'api-id': 'ka10035',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'trde_tp': in_trde_tp,
      'base_dt_tp': in_base_dt_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_for_cont_nettrde_upper'] = out_data['for_cont_nettrde_upper']
    
    return return_data

  def get_ka10036(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_dt: str, in_stex_tp: str):
    """
    외인한도소진율증가상위
    메뉴 위치 : 국내주식 > 순위정보 > 외인한도소진율증가상위(ka10036)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_dt (str(2)): 기간(필수) 0:당일, 1:전일, 5:5일, 10;10일, 20:20일, 60:60일
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT, 3:통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_for_limit_exh_rt_incrs_upper (list): 외인한도소진율증가상위
        - rank (str(20)): 순위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - trde_qty (str(20)): 거래량
        - poss_stkcnt (str(20)): 보유주식수
        - gain_pos_stkcnt (str(20)): 취득가능주식수
        - base_limit_exh_rt (str(20)): 기준한도소진율
        - limit_exh_rt (str(20)): 한도소진율
        - exh_rt_incrs (str(20)): 소진율증가
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10036',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'dt': in_dt,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_for_limit_exh_rt_incrs_upper'] = out_data['for_limit_exh_rt_incrs_upper']
    
    return return_data

  def get_ka10037(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_dt: str, in_trde_tp: str, in_sort_tp: str, in_stex_tp: str):
    """
    외국계창구매매상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 외국계창구매매상위요청(ka10037)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_dt (str(2)): 기간(필수) 0:당일, 1:전일, 5:5일, 10;10일, 20:20일, 60:60일
      in_trde_tp (str(1)): 매매구분(필수) 1:순매수, 2:순매도, 3:매수, 4:매도
      in_sort_tp (str(1)): 정렬구분(필수) 1:금액, 2:수량
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT, 3:통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_frgn_wicket_trde_upper (list): 외국계창구매매상위
        - rank (str(20)): 순위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - sel_trde_qty (str(20)): 매도거래량
        - buy_trde_qty (str(20)): 매수거래량
        - netprps_trde_qty (str(20)): 순매수거래량
        - netprps_prica (str(20)): 순매수대금
        - trde_qty (str(20)): 거래량
        - trde_prica (str(20)): 거래대금
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10037',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'dt': in_dt,
      'trde_tp': in_trde_tp,
      'sort_tp': in_sort_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_frgn_wicket_trde_upper'] = out_data['frgn_wicket_trde_upper']
    
    return return_data

  def get_ka10038(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_strt_dt: str, in_end_dt: str, in_qry_tp: str, in_dt: str):
    """
    종목별증권사순위요청
    메뉴 위치 : 국내주식 > 순위정보 > 종목별증권사순위요청(ka10038)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD (연도4자리, 월 2자리, 일 2자리 형식)
      in_end_dt (str(8)): 종료일자(필수) YYYYMMDD (연도4자리, 월 2자리, 일 2자리 형식)
      in_qry_tp (str(1)): 조회구분(필수) 1:순매도순위정렬, 2:순매수순위정렬
      in_dt (str(2)): 기간(필수) 1:전일, 4:5일, 9:10일, 19:20일, 39:40일, 59:60일, 119:120일
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_rank_1 (str(20)): 순위1
      out_rank_2 (str(20)): 순위2
      out_rank_3 (str(20)): 순위3
      out_prid_trde_qty (str(20)): 기간중거래량
      out_stk_sec_rank (list): 종목별증권사순위
        - rank (str(20)): 순위
        - mmcm_nm (str(20)): 회원사명
        - buy_qty (str(20)): 매수수량
        - sell_qty (str(20)): 매도수량
        - acc_netprps_qty (str(20)): 누적순매수수량
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10038',
    }
    params = {
      'stk_cd': in_stk_cd,
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'qry_tp': in_qry_tp,
      'dt': in_dt,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_rank_1'] = out_data['rank_1']
    return_data['out_rank_2'] = out_data['rank_2']
    return_data['out_rank_3'] = out_data['rank_3']
    return_data['out_prid_trde_qty'] = out_data['prid_trde_qty']
    return_data['out_stk_sec_rank'] = out_data['stk_sec_rank']
    
    return return_data

  def get_ka10039(self, in_cont_yn: str, in_next_key: str, in_mmcm_cd: str, in_trde_qty_tp: str, in_trde_tp: str, in_dt: str, in_stex_tp: str):
    """
    증권사별매매상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 증권사별매매상위요청(ka10039)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mmcm_cd (str(3)): 회원사코드(필수) 회원사 코드는 ka10102 조회
      in_trde_qty_tp (str(4)): 거래량구분(필수) 0:전체, 5:5000주, 10:1만주, 50:5만주, 100:10만주, 500:50만주, 1000: 100만주
      in_trde_tp (str(2)): 매매구분(필수) 1:순매수, 2:순매도
      in_dt (str(2)): 기간(필수) 1:전일, 5:5일, 10:10일, 60:60일
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_sec_trde_upper (list): 증권사별매매상위
        - rank (str(20)): 순위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - prid_stkpc_flu (str(20)): 기간중주가등락
        - flu_rt (str(20)): 등락율
        - prid_trde_qty (str(20)): 기간중거래량
        - netprps (str(20)): 순매수
        - buy_trde_qty (str(20)): 매수거래량
        - sel_trde_qty (str(20)): 매도거래량
        - netprps_amt (str(20)): 순매수금액
        - buy_amt (str(20)): 매수금액
        - sell_amt (str(20)): 매도금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10039',
    }
    params = {
      'mmcm_cd': in_mmcm_cd,
      'trde_qty_tp': in_trde_qty_tp,
      'trde_tp': in_trde_tp,
      'dt': in_dt,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_sec_trde_upper'] = out_data['sec_trde_upper']
    
    return return_data

  def get_ka10040(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    당일주요거래원요청
    메뉴 위치 : 국내주식 > 순위정보 > 당일주요거래원요청(ka10040)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_sel_trde_ori_irds_1 (str): 매도거래원별증감1
      out_sel_trde_ori_qty_1 (str): 매도거래원수량1
      out_sel_trde_ori_1 (str): 매도거래원1
      out_sel_trde_ori_cd_1 (str): 매도거래원코드1
      out_buy_trde_ori_1 (str): 매수거래원1
      out_buy_trde_ori_cd_1 (str): 매수거래원코드1
      out_buy_trde_ori_qty_1 (str): 매수거래원수량1
      out_buy_trde_ori_irds_1 (str): 매수거래원별증감1
      out_sel_trde_ori_irds_2 (str): 매도거래원별증감2
      out_sel_trde_ori_qty_2 (str): 매도거래원수량2
      out_sel_trde_ori_2 (str): 매도거래원2
      out_sel_trde_ori_cd_2 (str): 매도거래원코드2
      out_buy_trde_ori_2 (str): 매수거래원2
      out_buy_trde_ori_cd_2 (str): 매수거래원코드2
      out_buy_trde_ori_qty_2 (str): 매수거래원수량2
      out_buy_trde_ori_irds_2 (str): 매수거래원별증감2
      out_sel_trde_ori_irds_3 (str): 매도거래원별증감3
      out_sel_trde_ori_qty_3 (str): 매도거래원수량3
      out_sel_trde_ori_3 (str): 매도거래원3
      out_sel_trde_ori_cd_3 (str): 매도거래원코드3
      out_buy_trde_ori_3 (str): 매수거래원3
      out_buy_trde_ori_cd_3 (str): 매수거래원코드3
      out_buy_trde_ori_qty_3 (str): 매수거래원수량3
      out_buy_trde_ori_irds_3 (str): 매수거래원별증감3
      out_sel_trde_ori_irds_4 (str): 매도거래원별증감4
      out_sel_trde_ori_qty_4 (str): 매도거래원수량4
      out_sel_trde_ori_4 (str): 매도거래원4
      out_sel_trde_ori_cd_4 (str): 매도거래원코드4
      out_buy_trde_ori_4 (str): 매수거래원4
      out_buy_trde_ori_cd_4 (str): 매수거래원코드4
      out_buy_trde_ori_qty_4 (str): 매수거래원수량4
      out_buy_trde_ori_irds_4 (str): 매수거래원별증감4
      out_sel_trde_ori_irds_5 (str): 매도거래원별증감5
      out_sel_trde_ori_qty_5 (str): 매도거래원수량5
      out_sel_trde_ori_5 (str): 매도거래원5
      out_sel_trde_ori_cd_5 (str): 매도거래원코드5
      out_buy_trde_ori_5 (str): 매수거래원5
      out_buy_trde_ori_cd_5 (str): 매수거래원코드5
      out_buy_trde_ori_qty_5 (str): 매수거래원수량5
      out_buy_trde_ori_irds_5 (str): 매수거래원별증감5
      out_frgn_sel_prsm_sum_chang (str): 외국계매도추정합변동
      out_frgn_sel_prsm_sum (str): 외국계매도추정합
      out_frgn_buy_prsm_sum (str): 외국계매수추정합
      out_frgn_buy_prsm_sum_chang (str): 외국계매수추정합변동
      out_tdy_main_trde_ori (list): 당일주요거래원
        - sel_scesn_tm (str(20)): 매도이탈시간
        - sell_qty (str(20)): 매도수량
        - sel_upper_scesn_ori (str(20)): 매도상위이탈원
        - buy_scesn_tm (str(20)): 매수이탈시간
        - buy_qty (str(20)): 매수수량
        - buy_upper_scesn_ori (str(20)): 매수상위이탈원
        - qry_dt (str(20)): 조회일자
        - qry_tm (str(20)): 조회시간
    
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
      'api-id': 'ka10040',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_sel_trde_ori_irds_1'] = out_data['sel_trde_ori_irds_1']
    return_data['out_sel_trde_ori_qty_1'] = out_data['sel_trde_ori_qty_1']
    return_data['out_sel_trde_ori_1'] = out_data['sel_trde_ori_1']
    return_data['out_sel_trde_ori_cd_1'] = out_data['sel_trde_ori_cd_1']
    return_data['out_buy_trde_ori_1'] = out_data['buy_trde_ori_1']
    return_data['out_buy_trde_ori_cd_1'] = out_data['buy_trde_ori_cd_1']
    return_data['out_buy_trde_ori_qty_1'] = out_data['buy_trde_ori_qty_1']
    return_data['out_buy_trde_ori_irds_1'] = out_data['buy_trde_ori_irds_1']
    return_data['out_sel_trde_ori_irds_2'] = out_data['sel_trde_ori_irds_2']
    return_data['out_sel_trde_ori_qty_2'] = out_data['sel_trde_ori_qty_2']
    return_data['out_sel_trde_ori_2'] = out_data['sel_trde_ori_2']
    return_data['out_sel_trde_ori_cd_2'] = out_data['sel_trde_ori_cd_2']
    return_data['out_buy_trde_ori_2'] = out_data['buy_trde_ori_2']
    return_data['out_buy_trde_ori_cd_2'] = out_data['buy_trde_ori_cd_2']
    return_data['out_buy_trde_ori_qty_2'] = out_data['buy_trde_ori_qty_2']
    return_data['out_buy_trde_ori_irds_2'] = out_data['buy_trde_ori_irds_2']
    return_data['out_sel_trde_ori_irds_3'] = out_data['sel_trde_ori_irds_3']
    return_data['out_sel_trde_ori_qty_3'] = out_data['sel_trde_ori_qty_3']
    return_data['out_sel_trde_ori_3'] = out_data['sel_trde_ori_3']
    return_data['out_sel_trde_ori_cd_3'] = out_data['sel_trde_ori_cd_3']
    return_data['out_buy_trde_ori_3'] = out_data['buy_trde_ori_3']
    return_data['out_buy_trde_ori_cd_3'] = out_data['buy_trde_ori_cd_3']
    return_data['out_buy_trde_ori_qty_3'] = out_data['buy_trde_ori_qty_3']
    return_data['out_buy_trde_ori_irds_3'] = out_data['buy_trde_ori_irds_3']
    return_data['out_sel_trde_ori_irds_4'] = out_data['sel_trde_ori_irds_4']
    return_data['out_sel_trde_ori_qty_4'] = out_data['sel_trde_ori_qty_4']
    return_data['out_sel_trde_ori_4'] = out_data['sel_trde_ori_4']
    return_data['out_sel_trde_ori_cd_4'] = out_data['sel_trde_ori_cd_4']
    return_data['out_buy_trde_ori_4'] = out_data['buy_trde_ori_4']
    return_data['out_buy_trde_ori_cd_4'] = out_data['buy_trde_ori_cd_4']
    return_data['out_buy_trde_ori_qty_4'] = out_data['buy_trde_ori_qty_4']
    return_data['out_buy_trde_ori_irds_4'] = out_data['buy_trde_ori_irds_4']
    return_data['out_sel_trde_ori_irds_5'] = out_data['sel_trde_ori_irds_5']
    return_data['out_sel_trde_ori_qty_5'] = out_data['sel_trde_ori_qty_5']
    return_data['out_sel_trde_ori_5'] = out_data['sel_trde_ori_5']
    return_data['out_sel_trde_ori_cd_5'] = out_data['sel_trde_ori_cd_5']
    return_data['out_buy_trde_ori_5'] = out_data['buy_trde_ori_5']
    return_data['out_buy_trde_ori_cd_5'] = out_data['buy_trde_ori_cd_5']
    return_data['out_buy_trde_ori_qty_5'] = out_data['buy_trde_ori_qty_5']
    return_data['out_buy_trde_ori_irds_5'] = out_data['buy_trde_ori_irds_5']
    return_data['out_frgn_sel_prsm_sum_chang'] = out_data['frgn_sel_prsm_sum_chang']
    return_data['out_frgn_sel_prsm_sum'] = out_data['frgn_sel_prsm_sum']
    return_data['out_frgn_buy_prsm_sum'] = out_data['frgn_buy_prsm_sum']
    return_data['out_frgn_buy_prsm_sum_chang'] = out_data['frgn_buy_prsm_sum_chang']
    return_data['out_tdy_main_trde_ori'] = out_data['tdy_main_trde_ori']
    
    return return_data

  def get_ka10042(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_strt_dt: str, in_end_dt: str, in_qry_dt_tp: str, in_pot_tp: str, in_dt: str, in_sort_base: str):
    """
    순매수거래원순위요청
    메뉴 위치 : 국내주식 > 순위정보 > 순매수거래원순위요청(ka10042)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_strt_dt (str(8)): 시작일자 YYYYMMDD (연도4자리, 월 2자리, 일 2자리 형식)
      in_end_dt (str(8)): 종료일자 YYYYMMDD (연도4자리, 월 2자리, 일 2자리 형식)
      in_qry_dt_tp (str(1)): 조회기간구분(필수) 0:기간으로 조회, 1:시작일자, 종료일자로 조회
      in_pot_tp (str(1)): 시점구분(필수) 0:당일, 1:전일
      in_dt (str(4)): 기간 5:5일, 10:10일, 20:20일, 40:40일, 60:60일, 120:120일
      in_sort_base (str(1)): 정렬기준(필수) 1:종가순, 2:날짜순
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_netprps_trde_ori_rank (list): 순매수거래원순위
        - rank (str(20)): 순위
        - mmcm_cd (str(20)): 회원사코드
        - mmcm_nm (str(20)): 회원사명
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10042',
    }
    params = {
      'stk_cd': in_stk_cd,
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'qry_dt_tp': in_qry_dt_tp,
      'pot_tp': in_pot_tp,
      'dt': in_dt,
      'sort_base': in_sort_base,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_netprps_trde_ori_rank'] = out_data['netprps_trde_ori_rank']
    
    return return_data

  def get_ka10053(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    당일상위이탈원요청
    메뉴 위치 : 국내주식 > 순위정보 > 당일상위이탈원요청(ka10053)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_tdy_upper_scesn_ori (list): 당일상위이탈원
        - sel_scesn_tm (str(20)): 매도이탈시간
        - sell_qty (str(20)): 매도수량
        - sel_upper_scesn_ori (str(20)): 매도상위이탈원
        - buy_scesn_tm (str(20)): 매수이탈시간
        - buy_qty (str(20)): 매수수량
        - buy_upper_scesn_ori (str(20)): 매수상위이탈원
        - qry_dt (str(20)): 조회일자
        - qry_tm (str(20)): 조회시간
    
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
      'api-id': 'ka10053',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_tdy_upper_scesn_ori'] = out_data['tdy_upper_scesn_ori']
    
    return return_data

  def get_ka10062(self, in_cont_yn: str, in_next_key: str, in_strt_dt: str, in_end_dt: str, in_mrkt_tp: str, in_trde_tp: str, in_sort_cnd: str, in_unit_tp: str, in_stex_tp: str):
    """
    동일순매매순위요청
    메뉴 위치 : 국내주식 > 순위정보 > 동일순매매순위요청(ka10062)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD (연도4자리, 월 2자리, 일 2자리 형식)
      in_end_dt (str(8)): 종료일자 YYYYMMDD (연도4자리, 월 2자리, 일 2자리 형식)
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001: 코스피, 101:코스닥
      in_trde_tp (str(1)): 매매구분(필수) 1:순매수, 2:순매도
      in_sort_cnd (str(1)): 정렬조건(필수) 1:수량, 2:금액
      in_unit_tp (str(1)): 단위구분(필수) 1:단주, 1000:천주
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_eql_nettrde_rank (list): 동일순매매순위
        - stk_cd (str(20)): 종목코드
        - rank (str(20)): 순위
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - acc_trde_qty (str(20)): 누적거래량
        - orgn_nettrde_qty (str(20)): 기관순매매수량
        - orgn_nettrde_amt (str(20)): 기관순매매금액
        - orgn_nettrde_avg_pric (str(20)): 기관순매매평균가
        - for_nettrde_qty (str(20)): 외인순매매수량
        - for_nettrde_amt (str(20)): 외인순매매금액
        - for_nettrde_avg_pric (str(20)): 외인순매매평균가
        - nettrde_qty (str(20)): 순매매수량
        - nettrde_amt (str(20)): 순매매금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10062',
    }
    params = {
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'mrkt_tp': in_mrkt_tp,
      'trde_tp': in_trde_tp,
      'sort_cnd': in_sort_cnd,
      'unit_tp': in_unit_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_eql_nettrde_rank'] = out_data['eql_nettrde_rank']
    
    return return_data

  def get_ka10065(self, in_cont_yn: str, in_next_key: str, in_trde_tp: str, in_mrkt_tp: str, in_orgn_tp: str):
    """
    장중투자자별매매상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 장중투자자별매매상위요청(ka10065)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_trde_tp (str(1)): 매매구분(필수) 1:순매수, 2:순매도
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_orgn_tp (str(4)): 기관구분(필수) 9000:외국인, 9100:외국계, 1000:금융투자, 3000:투신, 5000:기타금융, 4000:은행, 2000:보험, 6000:연기금, 7000:국가, 7100:기타법인, 9999:기관계
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_opmr_invsr_trde_upper (list): 장중투자자별매매상위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - sel_qty (str(20)): 매도량
        - buy_qty (str(20)): 매수량
        - netslmt (str(20)): 순매도
    
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
      'api-id': 'ka10065',
    }
    params = {
      'trde_tp': in_trde_tp,
      'mrkt_tp': in_mrkt_tp,
      'orgn_tp': in_orgn_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_opmr_invsr_trde_upper'] = out_data['opmr_invsr_trde_upper']
    
    return return_data

  def get_ka10098(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_sort_base: str, in_stk_cnd: str, in_trde_qty_cnd: str, in_crd_cnd: str, in_trde_prica: str):
    """
    시간외단일가등락율순위요청
    메뉴 위치 : 국내주식 > 순위정보 > 시간외단일가등락율순위요청(ka10098)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체,001:코스피,101:코스닥
      in_sort_base (str(1)): 정렬기준(필수) 1:상승률, 2:상승폭, 3:하락률, 4:하락폭, 5:보합
      in_stk_cnd (str(2)): 종목조건(필수) 0:전체조회,1:관리종목제외,2:정리매매종목제외,3:우선주제외,4:관리종목우선주제외,5:증100제외,6:증100만보기,7:증40만보기,8:증30만보기,9:증20만보기,12:증50만보기,13:증60만보기,14:ETF제외,15:스팩제외,16:ETF+ETN제외,17:ETN제외
      in_trde_qty_cnd (str(5)): 거래량조건(필수) 0:전체조회, 10:백주이상,50:5백주이상,100;천주이상, 500:5천주이상, 1000:만주이상, 5000:5만주이상, 10000:10만주이상
      in_crd_cnd (str(1)): 신용조건(필수) 0:전체조회, 9:신용융자전체, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 8:신용대주, 5:신용한도초과제외
      in_trde_prica (str(5)): 거래대금(필수) 0:전체조회, 5:5백만원이상,10:1천만원이상, 30:3천만원이상, 50:5천만원이상, 100:1억원이상, 300:3억원이상, 500:5억원이상, 1000:10억원이상, 3000:30억원이상, 5000:50억원이상, 10000:100억원이상
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ovt_sigpric_flu_rt_rank (list): 시간외단일가등락율순위
        - rank (str(20)): 순위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pred_pre_sig (str(20)): 전일대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - sel_tot_req (str(20)): 매도총잔량
        - buy_tot_req (str(20)): 매수총잔량
        - acc_trde_qty (str(20)): 누적거래량
        - acc_trde_prica (str(20)): 누적거래대금
        - tdy_close_pric (str(20)): 당일종가
        - tdy_close_pric_flu_rt (str(20)): 당일종가등락률
    
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
      'api-id': 'ka10098',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'sort_base': in_sort_base,
      'stk_cnd': in_stk_cnd,
      'trde_qty_cnd': in_trde_qty_cnd,
      'crd_cnd': in_crd_cnd,
      'trde_prica': in_trde_prica,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ovt_sigpric_flu_rt_rank'] = out_data['ovt_sigpric_flu_rt_rank']
    
    return return_data

  def get_ka90009(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_amt_qty_tp: str, in_qry_dt_tp: str, in_date: str, in_stex_tp: str):
    """
    외국인기관매매상위요청
    메뉴 위치 : 국내주식 > 순위정보 > 외국인기관매매상위요청(ka90009)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1:금액(천만), 2:수량(천)
      in_qry_dt_tp (str(1)): 조회일자구분(필수) 0:조회일자 미포함, 1:조회일자 포함
      in_date (str(8)): 날짜 YYYYMMDD (연도4자리, 월 2자리, 일 2자리 형식)
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT, 3:통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_frgnr_orgn_trde_upper (list): 외국인기관매매상위
        - for_netslmt_stk_cd (str(20)): 외인순매도종목코드
        - for_netslmt_stk_nm (str(20)): 외인순매도종목명
        - for_netslmt_amt (str(20)): 외인순매도금액
        - for_netslmt_qty (str(20)): 외인순매도수량
        - for_netprps_stk_cd (str(20)): 외인순매수종목코드
        - for_netprps_stk_nm (str(20)): 외인순매수종목명
        - for_netprps_amt (str(20)): 외인순매수금액
        - for_netprps_qty (str(20)): 외인순매수수량
        - orgn_netslmt_stk_cd (str(20)): 기관순매도종목코드
        - orgn_netslmt_stk_nm (str(20)): 기관순매도종목명
        - orgn_netslmt_amt (str(20)): 기관순매도금액
        - orgn_netslmt_qty (str(20)): 기관순매도수량
        - orgn_netprps_stk_cd (str(20)): 기관순매수종목코드
        - orgn_netprps_stk_nm (str(20)): 기관순매수종목명
        - orgn_netprps_amt (str(20)): 기관순매수금액
        - orgn_netprps_qty (str(20)): 기관순매수수량
    
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
      'api-id': 'ka90009',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'amt_qty_tp': in_amt_qty_tp,
      'qry_dt_tp': in_qry_dt_tp,
      'date': in_date,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/rkinfo'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_frgnr_orgn_trde_upper'] = out_data['frgnr_orgn_trde_upper']
    
    return return_data

  def get_ka10048(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ELW일별민감도지표요청
    메뉴 위치 : 국내주식 > ELW > ELW일별민감도지표요청(ka10048)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_elwdaly_snst_ix (list): ELW일별민감도지표
        - dt (str(20)): 일자
        - iv (str(20)): IV
        - delta (str(20)): 델타
        - gam (str(20)): 감마
        - theta (str(20)): 쎄타
        - vega (str(20)): 베가
        - law (str(20)): 로
        - lp (str(20)): LP
    
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
      'api-id': 'ka10048',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_elwdaly_snst_ix'] = out_data['elwdaly_snst_ix']
    
    return return_data

  def get_ka10050(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ELW민감도지표요청
    메뉴 위치 : 국내주식 > ELW > ELW민감도지표요청(ka10050)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_elwsnst_ix_array (list): ELW민감도지표배열
        - cntr_tm (str(20)): 체결시간
        - cur_prc (str(20)): 현재가
        - elwtheory_pric (str(20)): ELW이론가
        - iv (str(20)): IV
        - delta (str(20)): 델타
        - gam (str(20)): 감마
        - theta (str(20)): 쎄타
        - vega (str(20)): 베가
        - law (str(20)): 로
        - lp (str(20)): LP
    
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
      'api-id': 'ka10050',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_elwsnst_ix_array'] = out_data['elwsnst_ix_array']
    
    return return_data

  def get_ka30001(self, in_cont_yn: str, in_next_key: str, in_flu_tp: str, in_tm_tp: str, in_tm: str, in_trde_qty_tp: str, in_isscomp_cd: str, in_bsis_aset_cd: str, in_rght_tp: str, in_lpcd: str, in_trde_end_elwskip: str):
    """
    ELW가격급등락요청
    메뉴 위치 : 국내주식 > ELW > ELW가격급등락요청(ka30001)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_flu_tp (str(1)): 등락구분(필수) 1:급등, 2:급락
      in_tm_tp (str(1)): 시간구분(필수) 1:분전, 2:일전
      in_tm (str(2)): 시간(필수) 분 혹은 일입력 (예 1, 3, 5)
      in_trde_qty_tp (str(4)): 거래량구분(필수) 0:전체, 10:만주이상, 50:5만주이상, 100:10만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상
      in_isscomp_cd (str(12)): 발행사코드(필수) 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17
      in_bsis_aset_cd (str(12)): 기초자산코드(필수) 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200..
      in_rght_tp (str(3)): 권리구분(필수) 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 005:EX, 006:조기종료콜, 007:조기종료풋
      in_lpcd (str(12)): LP코드(필수) 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17
      in_trde_end_elwskip (str(1)): 거래종료ELW제외(필수) 0:포함, 1:제외
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_base_pric_tm (str(20)): 기준가시간
      out_elwpric_jmpflu (list): ELW가격급등락
        - stk_cd (str(20)): 종목코드
        - rank (str(20)): 순위
        - stk_nm (str(40)): 종목명
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - trde_end_elwbase_pric (str(20)): 거래종료ELW기준가
        - cur_prc (str(20)): 현재가
        - base_pre (str(20)): 기준대비
        - trde_qty (str(20)): 거래량
        - jmp_rt (str(20)): 급등율
    
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
      'api-id': 'ka30001',
    }
    params = {
      'flu_tp': in_flu_tp,
      'tm_tp': in_tm_tp,
      'tm': in_tm,
      'trde_qty_tp': in_trde_qty_tp,
      'isscomp_cd': in_isscomp_cd,
      'bsis_aset_cd': in_bsis_aset_cd,
      'rght_tp': in_rght_tp,
      'lpcd': in_lpcd,
      'trde_end_elwskip': in_trde_end_elwskip,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_base_pric_tm'] = out_data['base_pric_tm']
    return_data['out_elwpric_jmpflu'] = out_data['elwpric_jmpflu']
    
    return return_data

  def get_ka30002(self, in_cont_yn: str, in_next_key: str, in_isscomp_cd: str, in_trde_qty_tp: str, in_trde_tp: str, in_dt: str, in_trde_end_elwskip: str):
    """
    거래원별ELW순매매상위요청
    메뉴 위치 : 국내주식 > ELW > 거래원별ELW순매매상위요청(ka30002)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_isscomp_cd (str(3)): 발행사코드(필수) 3자리, 영웅문4 0273화면참조 (교보:001, 신한금융투자:002, 한국투자증권:003, 대신:004, 미래대우:005, ,,,)
      in_trde_qty_tp (str(4)): 거래량구분(필수) 0:전체, 5:5천주, 10:만주, 50:5만주, 100:10만주, 500:50만주, 1000:백만주
      in_trde_tp (str(1)): 매매구분(필수) 1:순매수, 2:순매도
      in_dt (str(2)): 기간(필수) 1:전일, 5:5일, 10:10일, 40:40일, 60:60일
      in_trde_end_elwskip (str(1)): 거래종료ELW제외(필수) 0:포함, 1:제외
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_trde_ori_elwnettrde_upper (list): 거래원별ELW순매매상위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - stkpc_flu (str(20)): 주가등락
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - netprps (str(20)): 순매수
        - buy_trde_qty (str(20)): 매수거래량
        - sel_trde_qty (str(20)): 매도거래량
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka30002',
    }
    params = {
      'isscomp_cd': in_isscomp_cd,
      'trde_qty_tp': in_trde_qty_tp,
      'trde_tp': in_trde_tp,
      'dt': in_dt,
      'trde_end_elwskip': in_trde_end_elwskip,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_trde_ori_elwnettrde_upper'] = out_data['trde_ori_elwnettrde_upper']
    
    return return_data

  def get_ka30003(self, in_cont_yn: str, in_next_key: str, in_bsis_aset_cd: str, in_base_dt: str):
    """
    ELWLP보유일별추이요청
    메뉴 위치 : 국내주식 > ELW > ELWLP보유일별추이요청(ka30003)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_bsis_aset_cd (str(12)): 기초자산코드(필수)
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_elwlpposs_daly_trnsn (list): ELWLP보유일별추이
        - dt (str(20)): 일자
        - cur_prc (str(20)): 현재가
        - pre_tp (str(20)): 대비구분
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - trde_prica (str(20)): 거래대금
        - chg_qty (str(20)): 변동수량
        - lprmnd_qty (str(20)): LP보유수량
        - wght (str(20)): 비중
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka30003',
    }
    params = {
      'bsis_aset_cd': in_bsis_aset_cd,
      'base_dt': in_base_dt,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_elwlpposs_daly_trnsn'] = out_data['elwlpposs_daly_trnsn']
    
    return return_data

  def get_ka30004(self, in_cont_yn: str, in_next_key: str, in_isscomp_cd: str, in_bsis_aset_cd: str, in_rght_tp: str, in_lpcd: str, in_trde_end_elwskip: str):
    """
    ELW괴리율요청
    메뉴 위치 : 국내주식 > ELW > ELW괴리율요청(ka30004)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_isscomp_cd (str(12)): 발행사코드(필수) 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17
      in_bsis_aset_cd (str(12)): 기초자산코드(필수) 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200..
      in_rght_tp (str(3)): 권리구분(필수) 000: 전체, 001: 콜, 002: 풋, 003: DC, 004: DP, 005: EX, 006: 조기종료콜, 007: 조기종료풋
      in_lpcd (str(12)): LP코드(필수) 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17
      in_trde_end_elwskip (str(1)): 거래종료ELW제외(필수) 1:거래종료ELW제외, 0:거래종료ELW포함
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_elwdispty_rt (list): ELW괴리율
        - stk_cd (str(20)): 종목코드
        - isscomp_nm (str(20)): 발행사명
        - sqnc (str(20)): 회차
        - base_aset_nm (str(20)): 기초자산명
        - rght_tp (str(20)): 권리구분
        - dispty_rt (str(20)): 괴리율
        - basis (str(20)): 베이시스
        - srvive_dys (str(20)): 잔존일수
        - theory_pric (str(20)): 이론가
        - cur_prc (str(20)): 현재가
        - pre_tp (str(20)): 대비구분
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - stk_nm (str(40)): 종목명
    
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
      'api-id': 'ka30004',
    }
    params = {
      'isscomp_cd': in_isscomp_cd,
      'bsis_aset_cd': in_bsis_aset_cd,
      'rght_tp': in_rght_tp,
      'lpcd': in_lpcd,
      'trde_end_elwskip': in_trde_end_elwskip,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_elwdispty_rt'] = out_data['elwdispty_rt']
    
    return return_data

  def get_ka30005(self, in_cont_yn: str, in_next_key: str, in_isscomp_cd: str, in_bsis_aset_cd: str, in_rght_tp: str, in_lpcd: str, in_sort_tp: str):
    """
    ELW조건검색요청
    메뉴 위치 : 국내주식 > ELW > ELW조건검색요청(ka30005)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_isscomp_cd (str(12)): 발행사코드(필수) 12자리입력(전체:000000000000, 한국투자증권:000,,,3, 미래대우:000,,,5, 신영:000,,,6, NK투자증권:000,,,12, KB증권:000,,,17)
      in_bsis_aset_cd (str(12)): 기초자산코드(필수) 전체일때만 12자리입력(전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼정전자:005930, KT:030200,,)
      in_rght_tp (str(1)): 권리구분(필수) 0:전체, 1:콜, 2:풋, 3:DC, 4:DP, 5:EX, 6:조기종료콜, 7:조기종료풋
      in_lpcd (str(12)): LP코드(필수) 전체일때만 12자리입력(전체:000000000000, 한국투자증권:003, 미래대우:005, 신영:006, NK투자증권:012, KB증권:017)
      in_sort_tp (str(1)): 정렬구분(필수) 0:정렬없음, 1:상승율순, 2:상승폭순, 3:하락율순, 4:하락폭순, 5:거래량순, 6:거래대금순, 7:잔존일순
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_elwcnd_qry (list): ELW조건검색
        - stk_cd (str(20)): 종목코드
        - isscomp_nm (str(20)): 발행사명
        - sqnc (str(20)): 회차
        - base_aset_nm (str(20)): 기초자산명
        - rght_tp (str(20)): 권리구분
        - expr_dt (str(20)): 만기일
        - cur_prc (str(20)): 현재가
        - pre_tp (str(20)): 대비구분
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - trde_qty_pre (str(20)): 거래량대비
        - trde_prica (str(20)): 거래대금
        - pred_trde_qty (str(20)): 전일거래량
        - sel_bid (str(20)): 매도호가
        - buy_bid (str(20)): 매수호가
        - prty (str(20)): 패리티
        - gear_rt (str(20)): 기어링비율
        - pl_qutr_rt (str(20)): 손익분기율
        - cfp (str(20)): 자본지지점
        - theory_pric (str(20)): 이론가
        - innr_vltl (str(20)): 내재변동성
        - delta (str(20)): 델타
        - lvrg (str(20)): 레버리지
        - exec_pric (str(20)): 행사가격
        - cnvt_rt (str(20)): 전환비율
        - lpposs_rt (str(20)): LP보유비율
        - pl_qutr_pt (str(20)): 손익분기점
        - fin_trde_dt (str(20)): 최종거래일
        - flo_dt (str(20)): 상장일
        - lpinitlast_suply_dt (str(20)): LP초종공급일
        - stk_nm (str(40)): 종목명
        - srvive_dys (str(20)): 잔존일수
        - dispty_rt (str(20)): 괴리율
        - lpmmcm_nm (str(20)): LP회원사명
        - lpmmcm_nm_1 (str(20)): LP회원사명1
        - lpmmcm_nm_2 (str(20)): LP회원사명2
        - xraymont_cntr_qty_arng_trde_tp (str(20)): Xray순간체결량정리매매구분
        - xraymont_cntr_qty_profa_100tp (str(20)): Xray순간체결량증거금100구분
    
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
      'api-id': 'ka30005',
    }
    params = {
      'isscomp_cd': in_isscomp_cd,
      'bsis_aset_cd': in_bsis_aset_cd,
      'rght_tp': in_rght_tp,
      'lpcd': in_lpcd,
      'sort_tp': in_sort_tp,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_elwcnd_qry'] = out_data['elwcnd_qry']
    
    return return_data

  def get_ka30009(self, in_cont_yn: str, in_next_key: str, in_sort_tp: str, in_rght_tp: str, in_trde_end_skip: str):
    """
    ELW등락율순위요청
    메뉴 위치 : 국내주식 > ELW > ELW등락율순위요청(ka30009)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_sort_tp (str(1)): 정렬구분(필수) 1:상승률, 2:상승폭, 3:하락률, 4:하락폭
      in_rght_tp (str(3)): 권리구분(필수) 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 006:조기종료콜, 007:조기종료풋
      in_trde_end_skip (str(1)): 거래종료제외(필수) 1:거래종료제외, 0:거래종료포함
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_elwflu_rt_rank (list): ELW등락율순위
        - rank (str(20)): 순위
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - sel_req (str(20)): 매도잔량
        - buy_req (str(20)): 매수잔량
        - trde_qty (str(20)): 거래량
        - trde_prica (str(20)): 거래대금
    
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
      'api-id': 'ka30009',
    }
    params = {
      'sort_tp': in_sort_tp,
      'rght_tp': in_rght_tp,
      'trde_end_skip': in_trde_end_skip,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_elwflu_rt_rank'] = out_data['elwflu_rt_rank']
    
    return return_data

  def get_ka30010(self, in_cont_yn: str, in_next_key: str, in_sort_tp: str, in_rght_tp: str, in_trde_end_skip: str):
    """
    ELW잔량순위요청
    메뉴 위치 : 국내주식 > ELW > ELW잔량순위요청(ka30010)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_sort_tp (str(1)): 정렬구분(필수) 1:순매수잔량상위, 2: 순매도 잔량상위
      in_rght_tp (str(3)): 권리구분(필수) 000: 전체, 001: 콜, 002: 풋, 003: DC, 004: DP, 006: 조기종료콜, 007: 조기종료풋
      in_trde_end_skip (str(1)): 거래종료제외(필수) 1:거래종료제외, 0:거래종료포함
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_elwreq_rank (list): ELW잔량순위
        - stk_cd (str(20)): 종목코드
        - rank (str(20)): 순위
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락률
        - trde_qty (str(20)): 거래량
        - sel_req (str(20)): 매도잔량
        - buy_req (str(20)): 매수잔량
        - netprps_req (str(20)): 순매수잔량
        - trde_prica (str(20)): 거래대금
    
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
      'api-id': 'ka30010',
    }
    params = {
      'sort_tp': in_sort_tp,
      'rght_tp': in_rght_tp,
      'trde_end_skip': in_trde_end_skip,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_elwreq_rank'] = out_data['elwreq_rank']
    
    return return_data

  def get_ka30011(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ELW근접율요청
    메뉴 위치 : 국내주식 > ELW > ELW근접율요청(ka30011)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_elwalacc_rt (list): ELW근접율
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - acc_trde_qty (str(20)): 누적거래량
        - alacc_rt (str(20)): 근접율
    
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
      'api-id': 'ka30011',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_elwalacc_rt'] = out_data['elwalacc_rt']
    
    return return_data

  def get_ka30012(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ELW종목상세정보요청
    메뉴 위치 : 국내주식 > ELW > ELW종목상세정보요청(ka30012)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_aset_cd (str(20)): 자산코드
      out_cur_prc (str(20)): 현재가
      out_pred_pre_sig (str(20)): 전일대비기호
      out_pred_pre (str(20)): 전일대비
      out_flu_rt (str(20)): 등락율
      out_lpmmcm_nm (str(20)): LP회원사명
      out_lpmmcm_nm_1 (str(20)): LP회원사명1
      out_lpmmcm_nm_2 (str(20)): LP회원사명2
      out_elwrght_cntn (str(20)): ELW권리내용
      out_elwexpr_evlt_pric (str(20)): ELW만기평가가격
      out_elwtheory_pric (str(20)): ELW이론가
      out_dispty_rt (str(20)): 괴리율
      out_elwinnr_vltl (str(20)): ELW내재변동성
      out_exp_rght_pric (str(20)): 예상권리가
      out_elwpl_qutr_rt (str(20)): ELW손익분기율
      out_elwexec_pric (str(20)): ELW행사가
      out_elwcnvt_rt (str(20)): ELW전환비율
      out_elwcmpn_rt (str(20)): ELW보상율
      out_elwpric_rising_part_rt (str(20)): ELW가격상승참여율
      out_elwrght_type (str(20)): ELW권리유형
      out_elwsrvive_dys (str(20)): ELW잔존일수
      out_stkcnt (str(20)): 주식수
      out_elwlpord_pos (str(20)): ELWLP주문가능
      out_lpposs_rt (str(20)): LP보유비율
      out_lprmnd_qty (str(20)): LP보유수량
      out_elwspread (str(20)): ELW스프레드
      out_elwprty (str(20)): ELW패리티
      out_elwgear (str(20)): ELW기어링
      out_elwflo_dt (str(20)): ELW상장일
      out_elwfin_trde_dt (str(20)): ELW최종거래일
      out_expr_dt (str(20)): 만기일
      out_exec_dt (str(20)): 행사일
      out_lpsuply_end_dt (str(20)): LP공급종료일
      out_elwpay_dt (str(20)): ELW지급일
      out_elwinvt_ix_comput (str): ELW투자지표산출
      out_elwpay_agnt (str): ELW지급대리인
      out_elwappr_way (str): ELW결재방법
      out_elwrght_exec_way (str): ELW권리행사방식
      out_elwpblicte_orgn (str): ELW발행기관
      out_dcsn_pay_amt (str): 확정지급액
      out_kobarr (str): KO베리어
      out_iv (str): IV
      out_clsprd_end_elwocr (str): 종기종료ELW발생
      out_bsis_aset_1 (str): 기초자산1
      out_bsis_aset_comp_rt_1 (str): 기초자산구성비율1
      out_bsis_aset_2 (str): 기초자산2
      out_bsis_aset_comp_rt_2 (str): 기초자산구성비율2
      out_bsis_aset_3 (str): 기초자산3
      out_bsis_aset_comp_rt_3 (str): 기초자산구성비율3
      out_bsis_aset_4 (str): 기초자산4
      out_bsis_aset_comp_rt_4 (str): 기초자산구성비율4
      out_bsis_aset_5 (str): 기초자산5
      out_bsis_aset_comp_rt_5 (str): 기초자산구성비율5
      out_fr_dt (str): 평가시작일자
      out_to_dt (str): 평가종료일자
      out_fr_tm (str): 평가시작시간
      out_evlt_end_tm (str): 평가종료시간
      out_evlt_pric (str): 평가가격
      out_evlt_fnsh_yn (str): 평가완료여부
      out_all_hgst_pric (str): 전체최고가
      out_all_lwst_pric (str): 전체최저가
      out_imaf_hgst_pric (str): 직후최고가
      out_imaf_lwst_pric (str): 직후최저가
      out_sndhalf_mrkt_hgst_pric (str): 후반장최고가
      out_sndhalf_mrkt_lwst_pric (str): 후반장최저가
    
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
      'api-id': 'ka30012',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/elw'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_aset_cd'] = out_data['aset_cd']
    return_data['out_cur_prc'] = out_data['cur_prc']
    return_data['out_pred_pre_sig'] = out_data['pred_pre_sig']
    return_data['out_pred_pre'] = out_data['pred_pre']
    return_data['out_flu_rt'] = out_data['flu_rt']
    return_data['out_lpmmcm_nm'] = out_data['lpmmcm_nm']
    return_data['out_lpmmcm_nm_1'] = out_data['lpmmcm_nm_1']
    return_data['out_lpmmcm_nm_2'] = out_data['lpmmcm_nm_2']
    return_data['out_elwrght_cntn'] = out_data['elwrght_cntn']
    return_data['out_elwexpr_evlt_pric'] = out_data['elwexpr_evlt_pric']
    return_data['out_elwtheory_pric'] = out_data['elwtheory_pric']
    return_data['out_dispty_rt'] = out_data['dispty_rt']
    return_data['out_elwinnr_vltl'] = out_data['elwinnr_vltl']
    return_data['out_exp_rght_pric'] = out_data['exp_rght_pric']
    return_data['out_elwpl_qutr_rt'] = out_data['elwpl_qutr_rt']
    return_data['out_elwexec_pric'] = out_data['elwexec_pric']
    return_data['out_elwcnvt_rt'] = out_data['elwcnvt_rt']
    return_data['out_elwcmpn_rt'] = out_data['elwcmpn_rt']
    return_data['out_elwpric_rising_part_rt'] = out_data['elwpric_rising_part_rt']
    return_data['out_elwrght_type'] = out_data['elwrght_type']
    return_data['out_elwsrvive_dys'] = out_data['elwsrvive_dys']
    return_data['out_stkcnt'] = out_data['stkcnt']
    return_data['out_elwlpord_pos'] = out_data['elwlpord_pos']
    return_data['out_lpposs_rt'] = out_data['lpposs_rt']
    return_data['out_lprmnd_qty'] = out_data['lprmnd_qty']
    return_data['out_elwspread'] = out_data['elwspread']
    return_data['out_elwprty'] = out_data['elwprty']
    return_data['out_elwgear'] = out_data['elwgear']
    return_data['out_elwflo_dt'] = out_data['elwflo_dt']
    return_data['out_elwfin_trde_dt'] = out_data['elwfin_trde_dt']
    return_data['out_expr_dt'] = out_data['expr_dt']
    return_data['out_exec_dt'] = out_data['exec_dt']
    return_data['out_lpsuply_end_dt'] = out_data['lpsuply_end_dt']
    return_data['out_elwpay_dt'] = out_data['elwpay_dt']
    return_data['out_elwinvt_ix_comput'] = out_data['elwinvt_ix_comput']
    return_data['out_elwpay_agnt'] = out_data['elwpay_agnt']
    return_data['out_elwappr_way'] = out_data['elwappr_way']
    return_data['out_elwrght_exec_way'] = out_data['elwrght_exec_way']
    return_data['out_elwpblicte_orgn'] = out_data['elwpblicte_orgn']
    return_data['out_dcsn_pay_amt'] = out_data['dcsn_pay_amt']
    return_data['out_kobarr'] = out_data['kobarr']
    return_data['out_iv'] = out_data['iv']
    return_data['out_clsprd_end_elwocr'] = out_data['clsprd_end_elwocr']
    return_data['out_bsis_aset_1'] = out_data['bsis_aset_1']
    return_data['out_bsis_aset_comp_rt_1'] = out_data['bsis_aset_comp_rt_1']
    return_data['out_bsis_aset_2'] = out_data['bsis_aset_2']
    return_data['out_bsis_aset_comp_rt_2'] = out_data['bsis_aset_comp_rt_2']
    return_data['out_bsis_aset_3'] = out_data['bsis_aset_3']
    return_data['out_bsis_aset_comp_rt_3'] = out_data['bsis_aset_comp_rt_3']
    return_data['out_bsis_aset_4'] = out_data['bsis_aset_4']
    return_data['out_bsis_aset_comp_rt_4'] = out_data['bsis_aset_comp_rt_4']
    return_data['out_bsis_aset_5'] = out_data['bsis_aset_5']
    return_data['out_bsis_aset_comp_rt_5'] = out_data['bsis_aset_comp_rt_5']
    return_data['out_fr_dt'] = out_data['fr_dt']
    return_data['out_to_dt'] = out_data['to_dt']
    return_data['out_fr_tm'] = out_data['fr_tm']
    return_data['out_evlt_end_tm'] = out_data['evlt_end_tm']
    return_data['out_evlt_pric'] = out_data['evlt_pric']
    return_data['out_evlt_fnsh_yn'] = out_data['evlt_fnsh_yn']
    return_data['out_all_hgst_pric'] = out_data['all_hgst_pric']
    return_data['out_all_lwst_pric'] = out_data['all_lwst_pric']
    return_data['out_imaf_hgst_pric'] = out_data['imaf_hgst_pric']
    return_data['out_imaf_lwst_pric'] = out_data['imaf_lwst_pric']
    return_data['out_sndhalf_mrkt_hgst_pric'] = out_data['sndhalf_mrkt_hgst_pric']
    return_data['out_sndhalf_mrkt_lwst_pric'] = out_data['sndhalf_mrkt_lwst_pric']
    
    return return_data

  def get_ka10060(self, in_cont_yn: str, in_next_key: str, in_dt: str, in_stk_cd: str, in_amt_qty_tp: str, in_trde_tp: str, in_unit_tp: str):
    """
    종목별투자자기관별차트요청
    메뉴 위치 : 국내주식 > 차트 > 종목별투자자기관별차트요청(ka10060)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dt (str(8)): 일자(필수) YYYYMMDD
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1:금액, 2:수량
      in_trde_tp (str(1)): 매매구분(필수) 0:순매수, 1:매수, 2:매도
      in_unit_tp (str(4)): 단위구분(필수) 1000:천주, 1:단주
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_invsr_orgn_chart (list): 종목별투자자기관별차트
        - dt (str(20)): 일자
        - cur_prc (str(20)): 현재가
        - pred_pre (str(20)): 전일대비
        - acc_trde_prica (str(20)): 누적거래대금
        - ind_invsr (str(20)): 개인투자자
        - frgnr_invsr (str(20)): 외국인투자자
        - orgn (str(20)): 기관계
        - fnnc_invt (str(20)): 금융투자
        - insrnc (str(20)): 보험
        - invtrt (str(20)): 투신
        - etc_fnnc (str(20)): 기타금융
        - bank (str(20)): 은행
        - penfnd_etc (str(20)): 연기금등
        - samo_fund (str(20)): 사모펀드
        - natn (str(20)): 국가
        - etc_corp (str(20)): 기타법인
        - natfor (str(20)): 내외국인
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10060',
    }
    params = {
      'dt': in_dt,
      'stk_cd': in_stk_cd,
      'amt_qty_tp': in_amt_qty_tp,
      'trde_tp': in_trde_tp,
      'unit_tp': in_unit_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_invsr_orgn_chart'] = out_data['stk_invsr_orgn_chart']
    
    return return_data

  def get_ka10064(self, in_cont_yn: str, in_next_key: str, in_mrkt_tp: str, in_amt_qty_tp: str, in_trde_tp: str, in_stk_cd: str):
    """
    장중투자자별매매차트요청
    메뉴 위치 : 국내주식 > 차트 > 장중투자자별매매차트요청(ka10064)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_mrkt_tp (str(3)): 시장구분(필수) 000:전체, 001:코스피, 101:코스닥
      in_amt_qty_tp (str(1)): 금액수량구분(필수) 1:금액, 2:수량
      in_trde_tp (str(1)): 매매구분(필수) 0:순매수, 1:매수, 2:매도
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_opmr_invsr_trde_chart (list): 장중투자자별매매차트
        - tm (str(20)): 시간
        - frgnr_invsr (str(20)): 외국인투자자
        - orgn (str(20)): 기관계
        - invtrt (str(20)): 투신
        - insrnc (str(20)): 보험
        - bank (str(20)): 은행
        - penfnd_etc (str(20)): 연기금등
        - etc_corp (str(20)): 기타법인
        - natn (str(20)): 국가
    
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
      'api-id': 'ka10064',
    }
    params = {
      'mrkt_tp': in_mrkt_tp,
      'amt_qty_tp': in_amt_qty_tp,
      'trde_tp': in_trde_tp,
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_opmr_invsr_trde_chart'] = out_data['opmr_invsr_trde_chart']
    
    return return_data

  def get_ka10079(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_tic_scope: str, in_upd_stkpc_tp: str):
    """
    주식틱차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 주식틱차트조회요청(ka10079)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_tic_scope (str(2)): 틱범위(필수) 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱
      in_upd_stkpc_tp (str(1)): 수정주가구분(필수) 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_cd (str(6)): 종목코드
      out_last_tic_cnt (str): 마지막틱갯수
      out_stk_tic_chart_qry (list): 주식틱차트조회
        - cur_prc (str(20)): 현재가
        - trde_qty (str(20)): 거래량
        - cntr_tm (str(20)): 체결시간
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - pred_pre (str(20)): 전일대비. 현재가 - 전일종가
        - pred_pre_sig (str(20)): 전일대비 기호. 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락
    
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
      'api-id': 'ka10079',
    }
    params = {
      'stk_cd': in_stk_cd,
      'tic_scope': in_tic_scope,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_cd'] = out_data['stk_cd']
    return_data['out_last_tic_cnt'] = out_data['last_tic_cnt']
    return_data['out_stk_tic_chart_qry'] = out_data['stk_tic_chart_qry']
    
    return return_data

  def get_ka10080(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_tic_scope: str, in_upd_stkpc_tp: str):
    """
    주식분봉차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 주식분봉차트조회요청(ka10080)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_tic_scope (str(2)): 틱범위(필수) 1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분
      in_upd_stkpc_tp (str(1)): 수정주가구분(필수) 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_cd (str(6)): 종목코드
      out_stk_min_pole_chart_qry (list): 주식분봉차트조회
        - cur_prc (str(20)): 현재가. 종가
        - trde_qty (str(20)): 거래량
        - cntr_tm (str(20)): 체결시간
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - pred_pre (str(20)): 전일대비. 현재가 - 전일종가
        - pred_pre_sig (str(20)): 전일대비 기호. 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락
    
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
      'api-id': 'ka10080',
    }
    params = {
      'stk_cd': in_stk_cd,
      'tic_scope': in_tic_scope,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_cd'] = out_data['stk_cd']
    return_data['out_stk_min_pole_chart_qry'] = out_data['stk_min_pole_chart_qry']
    
    return return_data

  def get_ka10081(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_base_dt: str, in_upd_stkpc_tp: str):
    """
    주식일봉차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 주식일봉차트조회요청(ka10081)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
      in_upd_stkpc_tp (str(1)): 수정주가구분(필수) 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_cd (str(6)): 종목코드
      out_stk_dt_pole_chart_qry (list): 주식일봉차트조회
        - cur_prc (str(20)): 현재가
        - trde_qty (str(20)): 거래량
        - trde_prica (str(20)): 거래대금
        - dt (str(20)): 일자
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - pred_pre (str(20)): 전일대비. 현재가 - 전일종가
        - pred_pre_sig (str(20)): 전일대비기호. 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락
        - trde_tern_rt (str(20)): 거래회전율
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10081',
    }
    params = {
      'stk_cd': in_stk_cd,
      'base_dt': in_base_dt,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_cd'] = out_data['stk_cd']
    return_data['out_stk_dt_pole_chart_qry'] = out_data['stk_dt_pole_chart_qry']
    
    return return_data

  def get_ka10082(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_base_dt: str, in_upd_stkpc_tp: str):
    """
    주식주봉차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 주식주봉차트조회요청(ka10082)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
      in_upd_stkpc_tp (str(1)): 수정주가구분(필수) 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_cd (str(6)): 종목코드
      out_stk_stk_pole_chart_qry (list): 주식주봉차트조회
        - cur_prc (str(20)): 현재가
        - trde_qty (str(20)): 거래량
        - trde_prica (str(20)): 거래대금
        - dt (str(20)): 일자
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - pred_pre (str(20)): 전일대비. 현재가 - 전일종가
        - pred_pre_sig (str(20)): 전일대비기호. 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락
        - trde_tern_rt (str(20)): 거래회전율
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10082',
    }
    params = {
      'stk_cd': in_stk_cd,
      'base_dt': in_base_dt,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_cd'] = out_data['stk_cd']
    return_data['out_stk_stk_pole_chart_qry'] = out_data['stk_stk_pole_chart_qry']
    
    return return_data

  def get_ka10083(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_base_dt: str, in_upd_stkpc_tp: str):
    """
    주식월봉차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 주식월봉차트조회요청(ka10083)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
      in_upd_stkpc_tp (str(1)): 수정주가구분(필수) 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_cd (str(6)): 종목코드
      out_stk_mth_pole_chart_qry (list): 주식월봉차트조회
        - cur_prc (str(20)): 현재가
        - trde_qty (str(20)): 거래량
        - trde_prica (str(20)): 거래대금
        - dt (str(20)): 일자
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - pred_pre (str(20)): 전일대비. 현재가 - 전일종가
        - pred_pre_sig (str(20)): 전일대비기호. 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락
        - trde_tern_rt (str(20)): 거래회전율
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10083',
    }
    params = {
      'stk_cd': in_stk_cd,
      'base_dt': in_base_dt,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_cd'] = out_data['stk_cd']
    return_data['out_stk_mth_pole_chart_qry'] = out_data['stk_mth_pole_chart_qry']
    
    return return_data

  def get_ka10094(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_base_dt: str, in_upd_stkpc_tp: str):
    """
    주식년봉차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 주식년봉차트조회요청(ka10094)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
      in_upd_stkpc_tp (str(1)): 수정주가구분(필수) 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_cd (str(6)): 종목코드
      out_stk_yr_pole_chart_qry (list): 주식년봉차트조회
        - cur_prc (str(20)): 현재가
        - trde_qty (str(20)): 거래량
        - trde_prica (str(20)): 거래대금
        - dt (str(20)): 일자
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10094',
    }
    params = {
      'stk_cd': in_stk_cd,
      'base_dt': in_base_dt,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_cd'] = out_data['stk_cd']
    return_data['out_stk_yr_pole_chart_qry'] = out_data['stk_yr_pole_chart_qry']
    
    return return_data

  def get_ka20004(self, in_cont_yn: str, in_next_key: str, in_inds_cd: str, in_tic_scope: str):
    """
    업종틱차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 업종틱차트조회요청(ka20004)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_inds_cd (str(3)): 업종코드(필수) 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
      in_tic_scope (str(2)): 틱범위(필수) 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_inds_cd (str(20)): 업종코드
      out_inds_tic_chart_qry (list): 업종틱차트조회
        - cur_prc (str(20)): 현재가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - trde_qty (str(20)): 거래량
        - cntr_tm (str(20)): 체결시간
        - open_pric (str(20)): 시가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - high_pric (str(20)): 고가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - low_pric (str(20)): 저가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - pred_pre (str(20)): 전일대비. 현재가 - 전일종가
        - pred_pre_sig (str(20)): 전일대비 기호. 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락
    
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
      'api-id': 'ka20004',
    }
    params = {
      'inds_cd': in_inds_cd,
      'tic_scope': in_tic_scope,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_inds_cd'] = out_data['inds_cd']
    return_data['out_inds_tic_chart_qry'] = out_data['inds_tic_chart_qry']
    
    return return_data

  def get_ka20005(self, in_cont_yn: str, in_next_key: str, in_inds_cd: str, in_tic_scope: str):
    """
    업종분봉조회요청
    메뉴 위치 : 국내주식 > 차트 > 업종분봉조회요청(ka20005)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_inds_cd (str(3)): 업종코드(필수) 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
      in_tic_scope (str(2)): 틱범위(필수) 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_inds_cd (str(20)): 업종코드
      out_inds_min_pole_qry (list): 업종분봉조회
        - cur_prc (str(20)): 현재가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - trde_qty (str(20)): 거래량
        - cntr_tm (str(20)): 체결시간
        - open_pric (str(20)): 시가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - high_pric (str(20)): 고가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - low_pric (str(20)): 저가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - acc_trde_qty (str(20)): 누적거래량
        - pred_pre (str(20)): 전일대비. 현재가 - 전일종가
        - pred_pre_sig (str(20)): 전일대비 기호. 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락
    
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
      'api-id': 'ka20005',
    }
    params = {
      'inds_cd': in_inds_cd,
      'tic_scope': in_tic_scope,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_inds_cd'] = out_data['inds_cd']
    return_data['out_inds_min_pole_qry'] = out_data['inds_min_pole_qry']
    
    return return_data

  def get_ka20006(self, in_cont_yn: str, in_next_key: str, in_inds_cd: str, in_base_dt: str):
    """
    업종일봉조회요청
    메뉴 위치 : 국내주식 > 차트 > 업종일봉조회요청(ka20006)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_inds_cd (str(3)): 업종코드(필수) 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_inds_cd (str(20)): 업종코드
      out_inds_dt_pole_qry (list): 업종일봉조회
        - cur_prc (str(20)): 현재가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - trde_qty (str(20)): 거래량
        - dt (str(20)): 일자
        - open_pric (str(20)): 시가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - high_pric (str(20)): 고가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - low_pric (str(20)): 저가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - trde_prica (str(20)): 거래대금
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka20006',
    }
    params = {
      'inds_cd': in_inds_cd,
      'base_dt': in_base_dt,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_inds_cd'] = out_data['inds_cd']
    return_data['out_inds_dt_pole_qry'] = out_data['inds_dt_pole_qry']
    
    return return_data

  def get_ka20007(self, in_cont_yn: str, in_next_key: str, in_inds_cd: str, in_base_dt: str):
    """
    업종주봉조회요청
    메뉴 위치 : 국내주식 > 차트 > 업종주봉조회요청(ka20007)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_inds_cd (str(8)): 업종코드(필수) 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
      in_base_dt (str(3)): 기준일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_inds_cd (str(20)): 업종코드
      out_inds_stk_pole_qry (list): 업종주봉조회
        - cur_prc (str(20)): 현재가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - trde_qty (str(20)): 거래량
        - dt (str(20)): 일자
        - open_pric (str(20)): 시가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - high_pric (str(20)): 고가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - low_pric (str(20)): 저가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - trde_prica (str(20)): 거래대금
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka20007',
    }
    params = {
      'inds_cd': in_inds_cd,
      'base_dt': in_base_dt,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_inds_cd'] = out_data['inds_cd']
    return_data['out_inds_stk_pole_qry'] = out_data['inds_stk_pole_qry']
    
    return return_data

  def get_ka20008(self, in_cont_yn: str, in_next_key: str, in_inds_cd: str, in_base_dt: str):
    """
    업종월봉조회요청
    메뉴 위치 : 국내주식 > 차트 > 업종월봉조회요청(ka20008)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_inds_cd (str(3)): 업종코드(필수) 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_inds_cd (str(20)): 업종코드
      out_inds_mth_pole_qry (list): 업종월봉조회
        - cur_prc (str(20)): 현재가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - trde_qty (str(20)): 거래량
        - dt (str(20)): 일자
        - open_pric (str(20)): 시가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - high_pric (str(20)): 고가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - low_pric (str(20)): 저가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - trde_prica (str(20)): 거래대금
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka20008',
    }
    params = {
      'inds_cd': in_inds_cd,
      'base_dt': in_base_dt,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_inds_cd'] = out_data['inds_cd']
    return_data['out_inds_mth_pole_qry'] = out_data['inds_mth_pole_qry']
    
    return return_data

  def get_ka20019(self, in_cont_yn: str, in_next_key: str, in_inds_cd: str, in_base_dt: str):
    """
    업종년봉조회요청
    메뉴 위치 : 국내주식 > 차트 > 업종년봉조회요청(ka20019)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_inds_cd (str(3)): 업종코드(필수) 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_inds_cd (str(20)): 업종코드
      out_inds_yr_pole_qry (list): 업종년봉조회
        - cur_prc (str(20)): 현재가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - trde_qty (str(20)): 거래량
        - dt (str(20)): 일자
        - open_pric (str(20)): 시가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - high_pric (str(20)): 고가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - low_pric (str(20)): 저가. 지수 값은 소수점 제거 후 100배 값으로 반환
        - trde_prica (str(20)): 거래대금
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka20019',
    }
    params = {
      'inds_cd': in_inds_cd,
      'base_dt': in_base_dt,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_inds_cd'] = out_data['inds_cd']
    return_data['out_inds_yr_pole_qry'] = out_data['inds_yr_pole_qry']
    
    return return_data

  def get_ka50079(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_tic_scope: str, in_upd_stkpc_tp: str):
    """
    금현물틱차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 금현물틱차트조회요청(ka50079)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_tic_scope (str(2)): 틱범위(필수) 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱
      in_upd_stkpc_tp (str(1)): 수정주가구분(필수) 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gds_tic_chart_qry (list): 금현물틱차트조회
        - cur_prc (str(20)): 현재가
        - pred_pre (str(20)): 전일대비
        - trde_qty (str(20)): 거래량
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str): 저가
        - cntr_tm (str(20)): 체결시간
        - dt (str(20)): 일자
        - pred_pre_sig (str(20)): 전일대비기호
    
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
      'api-id': 'ka50079',
    }
    params = {
      'stk_cd': in_stk_cd,
      'tic_scope': in_tic_scope,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gds_tic_chart_qry'] = out_data['gds_tic_chart_qry']
    
    return return_data

  def get_ka50080(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_tic_scope: str, in_upd_stkpc_tp: str):
    """
    금현물분봉차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 금현물분봉차트조회요청(ka50080)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_tic_scope (str(3)): 틱범위(필수) 1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분
      in_upd_stkpc_tp (str(1)): 수정주가구분 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gds_min_chart_qry (list): 금현물분봉차트조회
        - cur_prc (str(20)): 현재가
        - pred_pre (str(20)): 전일대비
        - acc_trde_qty (str(20)): 누적거래량
        - trde_qty (str(20)): 거래량
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - cntr_tm (str(20)): 체결시간
        - dt (str(20)): 일자
        - pred_pre_sig (str(20)): 전일대비기호
    
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
      'api-id': 'ka50080',
    }
    params = {
      'stk_cd': in_stk_cd,
      'tic_scope': in_tic_scope,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gds_min_chart_qry'] = out_data['gds_min_chart_qry']
    
    return return_data

  def get_ka50081(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_base_dt: str, in_upd_stkpc_tp: str):
    """
    금현물일봉차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 금현물일봉차트조회요청(ka50081)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
      in_upd_stkpc_tp (str(1)): 수정주가구분(필수) 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gds_day_chart_qry (list): 금현물일봉차트조회
        - cur_prc (str(20)): 현재가
        - acc_trde_qty (str(20)): 누적 거래량
        - acc_trde_prica (str(20)): 누적 거래대금
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - dt (str(20)): 일자
        - pred_pre_sig (str(20)): 전일대비기호
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka50081',
    }
    params = {
      'stk_cd': in_stk_cd,
      'base_dt': in_base_dt,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gds_day_chart_qry'] = out_data['gds_day_chart_qry']
    
    return return_data

  def get_ka50082(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_base_dt: str, in_upd_stkpc_tp: str):
    """
    금현물주봉차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 금현물주봉차트조회요청(ka50082)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
      in_upd_stkpc_tp (str(1)): 수정주가구분(필수) 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gds_week_chart_qry (list): 금현물일봉차트조회
        - cur_prc (str(20)): 현재가
        - acc_trde_qty (str(20)): 누적 거래량
        - acc_trde_prica (str(20)): 누적 거래대금
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - dt (str(20)): 일자
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka50082',
    }
    params = {
      'stk_cd': in_stk_cd,
      'base_dt': in_base_dt,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gds_week_chart_qry'] = out_data['gds_week_chart_qry']
    
    return return_data

  def get_ka50083(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_base_dt: str, in_upd_stkpc_tp: str):
    """
    금현물월봉차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 금현물월봉차트조회요청(ka50083)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_base_dt (str(8)): 기준일자(필수) YYYYMMDD
      in_upd_stkpc_tp (str(1)): 수정주가구분(필수) 0 or 1
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gds_month_chart_qry (list): 금현물일봉차트조회
        - cur_prc (str(20)): 현재가
        - acc_trde_qty (str(20)): 누적 거래량
        - acc_trde_prica (str(20)): 누적 거래대금
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - dt (str(20)): 일자
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_base_dt or in_base_dt == '':
      in_base_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka50083',
    }
    params = {
      'stk_cd': in_stk_cd,
      'base_dt': in_base_dt,
      'upd_stkpc_tp': in_upd_stkpc_tp,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gds_month_chart_qry'] = out_data['gds_month_chart_qry']
    
    return return_data

  def get_ka50091(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_tic_scope: str):
    """
    금현물당일틱차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 금현물당일틱차트조회요청(ka50091)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_tic_scope (str(2)): 틱범위(필수) 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gds_tic_chart_qry (list): 금현물일봉차트조회
        - cntr_pric (str(20)): 체결가
        - pred_pre (str(20)): 전일 대비(원)
        - trde_qty (str(20)): 거래량(체결량)
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - cntr_tm (str(20)): 체결시간
        - dt (str(20)): 일자
        - pred_pre_sig (str(20)): 전일대비기호
    
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
      'api-id': 'ka50091',
    }
    params = {
      'stk_cd': in_stk_cd,
      'tic_scope': in_tic_scope,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gds_tic_chart_qry'] = out_data['gds_tic_chart_qry']
    
    return return_data

  def get_ka50092(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_tic_scope: str):
    """
    금현물당일분봉차트조회요청
    메뉴 위치 : 국내주식 > 차트 > 금현물당일분봉차트조회요청(ka50092)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(20)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_tic_scope (str(2)): 틱범위(필수) 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_gds_min_chart_qry (list): 금현물일봉차트조회
        - cntr_pric (str(20)): 체결가
        - pred_pre (str(20)): 전일 대비(원)
        - acc_trde_qty (str(20)): 누적 거래량
        - acc_trde_prica (str(20)): 누적 거래대금
        - trde_qty (str(20)): 거래량(체결량)
        - open_pric (str(20)): 시가
        - high_pric (str(20)): 고가
        - low_pric (str(20)): 저가
        - cntr_tm (str(20)): 체결시간
        - dt (str(20)): 일자
        - pred_pre_sig (str(20)): 전일대비기호
    
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
      'api-id': 'ka50092',
    }
    params = {
      'stk_cd': in_stk_cd,
      'tic_scope': in_tic_scope,
    }
    url = '/api/dostk/chart'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_gds_min_chart_qry'] = out_data['gds_min_chart_qry']
    
    return return_data

  def get_ka10068(self, in_cont_yn: str, in_next_key: str, in_strt_dt: str, in_end_dt: str, in_all_tp: str):
    """
    대차거래추이요청
    메뉴 위치 : 국내주식 > 대차거래 > 대차거래추이요청(ka10068)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_strt_dt (str(8)): 시작일자 YYYYMMDD
      in_end_dt (str(8)): 종료일자 YYYYMMDD
      in_all_tp (str(6)): 전체구분(필수) 1: 전체표시
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_dbrt_trde_trnsn (list): 대차거래추이
        - dt (str(8)): 일자
        - dbrt_trde_cntrcnt (str(12)): 대차거래체결주수
        - dbrt_trde_rpy (str(18)): 대차거래상환주수
        - rmnd (str(18)): 잔고주수
        - dbrt_trde_irds (str(60)): 대차거래증감
        - remn_amt (str(18)): 잔고금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10068',
    }
    params = {
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'all_tp': in_all_tp,
    }
    url = '/api/dostk/slb'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_dbrt_trde_trnsn'] = out_data['dbrt_trde_trnsn']
    
    return return_data

  def get_ka10069(self, in_cont_yn: str, in_next_key: str, in_strt_dt: str, in_end_dt: str, in_mrkt_tp: str):
    """
    대차거래상위10종목요청
    메뉴 위치 : 국내주식 > 대차거래 > 대차거래상위10종목요청(ka10069)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_strt_dt (str(8)): 시작일자(필수) YYYYMMDD (연도4자리, 월 2자리, 일 2자리 형식)
      in_end_dt (str(8)): 종료일자 YYYYMMDD (연도4자리, 월 2자리, 일 2자리 형식)
      in_mrkt_tp (str(3)): 시장구분(필수) 001:코스피, 101:코스닥
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_dbrt_trde_cntrcnt_sum (str): 대차거래체결주수합
      out_dbrt_trde_rpy_sum (str): 대차거래상환주수합
      out_rmnd_sum (str): 잔고주수합
      out_remn_amt_sum (str): 잔고금액합
      out_dbrt_trde_cntrcnt_rt (str): 대차거래체결주수비율
      out_dbrt_trde_rpy_rt (str): 대차거래상환주수비율
      out_rmnd_rt (str): 잔고주수비율
      out_remn_amt_rt (str): 잔고금액비율
      out_dbrt_trde_upper_10stk (list): 대차거래상위10종목
        - stk_nm (str(40)): 종목명
        - stk_cd (str(20)): 종목코드
        - dbrt_trde_cntrcnt (str(20)): 대차거래체결주수
        - dbrt_trde_rpy (str(20)): 대차거래상환주수
        - rmnd (str(20)): 잔고주수
        - remn_amt (str(20)): 잔고금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka10069',
    }
    params = {
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'mrkt_tp': in_mrkt_tp,
    }
    url = '/api/dostk/slb'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_dbrt_trde_cntrcnt_sum'] = out_data['dbrt_trde_cntrcnt_sum']
    return_data['out_dbrt_trde_rpy_sum'] = out_data['dbrt_trde_rpy_sum']
    return_data['out_rmnd_sum'] = out_data['rmnd_sum']
    return_data['out_remn_amt_sum'] = out_data['remn_amt_sum']
    return_data['out_dbrt_trde_cntrcnt_rt'] = out_data['dbrt_trde_cntrcnt_rt']
    return_data['out_dbrt_trde_rpy_rt'] = out_data['dbrt_trde_rpy_rt']
    return_data['out_rmnd_rt'] = out_data['rmnd_rt']
    return_data['out_remn_amt_rt'] = out_data['remn_amt_rt']
    return_data['out_dbrt_trde_upper_10stk'] = out_data['dbrt_trde_upper_10stk']
    
    return return_data

  def get_ka20068(self, in_cont_yn: str, in_next_key: str, in_strt_dt: str, in_end_dt: str, in_all_tp: str, in_stk_cd: str):
    """
    대차거래추이요청
    메뉴 위치 : 국내주식 > 대차거래 > 대차거래추이요청(종목별)(ka20068)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_strt_dt (str(8)): 시작일자 YYYYMMDD
      in_end_dt (str(8)): 종료일자 YYYYMMDD
      in_all_tp (str(1)): 전체구분 0:종목코드 입력종목만 표시
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_dbrt_trde_trnsn (list): 대차거래추이
        - dt (str(20)): 일자
        - dbrt_trde_cntrcnt (str(20)): 대차거래체결주수
        - dbrt_trde_rpy (str(20)): 대차거래상환주수
        - dbrt_trde_irds (str(20)): 대차거래증감
        - rmnd (str(20)): 잔고주수
        - remn_amt (str(20)): 잔고금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_strt_dt or in_strt_dt == '':
      in_strt_dt = format_datetime('%Y%m%d')
    
    if not in_end_dt or in_end_dt == '':
      in_end_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka20068',
    }
    params = {
      'strt_dt': in_strt_dt,
      'end_dt': in_end_dt,
      'all_tp': in_all_tp,
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/slb'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_dbrt_trde_trnsn'] = out_data['dbrt_trde_trnsn']
    
    return return_data

  def get_ka90012(self, in_cont_yn: str, in_next_key: str, in_dt: str, in_mrkt_tp: str):
    """
    대차거래내역요청
    메뉴 위치 : 국내주식 > 대차거래 > 대차거래내역요청(ka90012)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dt (str(8)): 일자(필수) YYYYMMDD
      in_mrkt_tp (str(3)): 시장구분(필수) 001:코스피, 101:코스닥
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_dbrt_trde_prps (list): 대차거래내역
        - stk_nm (str(40)): 종목명
        - stk_cd (str(20)): 종목코드
        - dbrt_trde_cntrcnt (str(20)): 대차거래체결주수
        - dbrt_trde_rpy (str(20)): 대차거래상환주수
        - rmnd (str(20)): 잔고주수
        - remn_amt (str(20)): 잔고금액
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka90012',
    }
    params = {
      'dt': in_dt,
      'mrkt_tp': in_mrkt_tp,
    }
    url = '/api/dostk/slb'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_dbrt_trde_prps'] = out_data['dbrt_trde_prps']
    
    return return_data

  def get_ka40001(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_etfobjt_idex_cd: str, in_dt: str):
    """
    ETF수익율요청
    메뉴 위치 : 국내주식 > ETF > ETF수익율요청(ka40001)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
      in_etfobjt_idex_cd (str(3)): ETF대상지수코드(필수)
      in_dt (str(1)): 기간(필수) 0:1주, 1:1달, 2:6개월, 3:1년
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_etfprft_rt_lst (list): ETF수익율
        - etfprft_rt (str(20)): ETF수익률
        - cntr_prft_rt (str(20)): 체결수익률
        - for_netprps_qty (str(20)): 외인순매수수량
        - orgn_netprps_qty (str(20)): 기관순매수수량
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_dt or in_dt == '':
      in_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'ka40001',
    }
    params = {
      'stk_cd': in_stk_cd,
      'etfobjt_idex_cd': in_etfobjt_idex_cd,
      'dt': in_dt,
    }
    url = '/api/dostk/etf'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_etfprft_rt_lst'] = out_data['etfprft_rt_lst']
    
    return return_data

  def get_ka40002(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ETF종목정보요청
    메뉴 위치 : 국내주식 > ETF > ETF종목정보요청(ka40002)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_nm (str(40)): 종목명
      out_etfobjt_idex_nm (str(20)): ETF대상지수명
      out_wonju_pric (str(20)): 원주가격
      out_etftxon_type (str(20)): ETF과세유형
      out_etntxon_type (str(20)): ETN과세유형
    
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
      'api-id': 'ka40002',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/etf'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_nm'] = out_data['stk_nm']
    return_data['out_etfobjt_idex_nm'] = out_data['etfobjt_idex_nm']
    return_data['out_wonju_pric'] = out_data['wonju_pric']
    return_data['out_etftxon_type'] = out_data['etftxon_type']
    return_data['out_etntxon_type'] = out_data['etntxon_type']
    
    return return_data

  def get_ka40003(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ETF일별추이요청
    메뉴 위치 : 국내주식 > ETF > ETF일별추이요청(ka40003)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_etfdaly_trnsn (list): ETF일별추이
        - cntr_dt (str(20)): 체결일자
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - pre_rt (str(20)): 대비율
        - trde_qty (str(20)): 거래량
        - nav (str(20)): NAV
        - acc_trde_prica (str(20)): 누적거래대금
        - navidex_dispty_rt (str(20)): NAV/지수괴리율
        - navetfdispty_rt (str(20)): NAV/ETF괴리율
        - trace_eor_rt (str(20)): 추적오차율
        - trace_cur_prc (str(20)): 추적현재가
        - trace_pred_pre (str(20)): 추적전일대비
        - trace_pre_sig (str(20)): 추적대비기호
    
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
      'api-id': 'ka40003',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/etf'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_etfdaly_trnsn'] = out_data['etfdaly_trnsn']
    
    return return_data

  def get_ka40004(self, in_cont_yn: str, in_next_key: str, in_txon_type: str, in_navpre: str, in_mngmcomp: str, in_txon_yn: str, in_trace_idex: str, in_stex_tp: str):
    """
    ETF전체시세요청
    메뉴 위치 : 국내주식 > ETF > ETF전체시세요청(ka40004)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_txon_type (str(1)): 과세유형(필수) 0:전체, 1:비과세, 2:보유기간과세, 3:회사형, 4:외국, 5:비과세해외(보유기간관세)
      in_navpre (str(1)): NAV대비(필수) 0:전체, 1:NAV > 전일종가, 2:NAV < 전일종가
      in_mngmcomp (str(4)): 운용사(필수) 0000:전체, 3020:KODEX(삼성), 3027:KOSEF(키움), 3191:TIGER(미래에셋), 3228:KINDEX(한국투자), 3023:KStar(KB), 3022:아리랑(한화), 9999:기타운용사
      in_txon_yn (str(1)): 과세여부(필수) 0:전체, 1:과세, 2:비과세
      in_trace_idex (str(1)): 추적지수(필수) 0:전체
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT, 3:통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_etfall_mrpr (list): ETF전체시세
        - stk_cd (str(20)): 종목코드
        - stk_cls (str(20)): 종목분류
        - stk_nm (str(40)): 종목명
        - close_pric (str(20)): 종가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - pre_rt (str(20)): 대비율
        - trde_qty (str(20)): 거래량
        - nav (str(20)): NAV
        - trace_eor_rt (str(20)): 추적오차율
        - txbs (str(20)): 과표기준
        - dvid_bf_base (str(20)): 배당전기준
        - pred_dvida (str(20)): 전일배당금
        - trace_idex_nm (str(20)): 추적지수명
        - drng (str(20)): 배수
        - trace_idex_cd (str(20)): 추적지수코드
        - trace_idex (str(20)): 추적지수
        - trace_flu_rt (str(20)): 추적등락율
    
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
      'api-id': 'ka40004',
    }
    params = {
      'txon_type': in_txon_type,
      'navpre': in_navpre,
      'mngmcomp': in_mngmcomp,
      'txon_yn': in_txon_yn,
      'trace_idex': in_trace_idex,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/etf'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_etfall_mrpr'] = out_data['etfall_mrpr']
    
    return return_data

  def get_ka40006(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ETF시간대별추이요청
    메뉴 위치 : 국내주식 > ETF > ETF시간대별추이요청(ka40006)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_nm (str(40)): 종목명
      out_etfobjt_idex_nm (str(20)): ETF대상지수명
      out_wonju_pric (str(20)): 원주가격
      out_etftxon_type (str(20)): ETF과세유형
      out_etntxon_type (str(20)): ETN과세유형
      out_etftisl_trnsn (list): ETF시간대별추이
        - tm (str(20)): 시간
        - close_pric (str(20)): 종가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - trde_qty (str(20)): 거래량
        - nav (str(20)): NAV
        - trde_prica (str(20)): 거래대금
        - navidex (str(20)): NAV지수
        - navetf (str(20)): NAVETF
        - trace (str(20)): 추적
        - trace_idex (str(20)): 추적지수
        - trace_idex_pred_pre (str(20)): 추적지수전일대비
        - trace_idex_pred_pre_sig (str(20)): 추적지수전일대비기호
    
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
      'api-id': 'ka40006',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/etf'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_nm'] = out_data['stk_nm']
    return_data['out_etfobjt_idex_nm'] = out_data['etfobjt_idex_nm']
    return_data['out_wonju_pric'] = out_data['wonju_pric']
    return_data['out_etftxon_type'] = out_data['etftxon_type']
    return_data['out_etntxon_type'] = out_data['etntxon_type']
    return_data['out_etftisl_trnsn'] = out_data['etftisl_trnsn']
    
    return return_data

  def get_ka40007(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ETF시간대별체결요청
    메뉴 위치 : 국내주식 > ETF > ETF시간대별체결요청(ka40007)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_stk_cls (str(20)): 종목분류
      out_stk_nm (str(40)): 종목명
      out_etfobjt_idex_nm (str(20)): ETF대상지수명
      out_etfobjt_idex_cd (str(20)): ETF대상지수코드
      out_objt_idex_pre_rt (str(20)): 대상지수대비율
      out_wonju_pric (str(20)): 원주가격
      out_etftisl_cntr_array (list): ETF시간대별체결배열
        - cntr_tm (str(20)): 체결시간
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - trde_qty (str(20)): 거래량
        - stex_tp (str(20)): 거래소구분. KRX , NXT , 통합
    
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
      'api-id': 'ka40007',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/etf'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_stk_cls'] = out_data['stk_cls']
    return_data['out_stk_nm'] = out_data['stk_nm']
    return_data['out_etfobjt_idex_nm'] = out_data['etfobjt_idex_nm']
    return_data['out_etfobjt_idex_cd'] = out_data['etfobjt_idex_cd']
    return_data['out_objt_idex_pre_rt'] = out_data['objt_idex_pre_rt']
    return_data['out_wonju_pric'] = out_data['wonju_pric']
    return_data['out_etftisl_cntr_array'] = out_data['etftisl_cntr_array']
    
    return return_data

  def get_ka40008(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ETF일자별체결요청
    메뉴 위치 : 국내주식 > ETF > ETF일자별체결요청(ka40008)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_cntr_tm (str(20)): 체결시간
      out_cur_prc (str(20)): 현재가
      out_pre_sig (str(20)): 대비기호
      out_pred_pre (str(20)): 전일대비
      out_trde_qty (str(20)): 거래량
      out_etfnetprps_qty_array (list): ETF순매수수량배열
        - dt (str(20)): 일자
        - cur_prc_n (str(20)): 현재가n
        - pre_sig_n (str(20)): 대비기호n
        - pred_pre_n (str(20)): 전일대비n
        - acc_trde_qty (str(20)): 누적거래량
        - for_netprps_qty (str(20)): 외인순매수수량
        - orgn_netprps_qty (str(20)): 기관순매수수량
    
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
      'api-id': 'ka40008',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/etf'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_cntr_tm'] = out_data['cntr_tm']
    return_data['out_cur_prc'] = out_data['cur_prc']
    return_data['out_pre_sig'] = out_data['pre_sig']
    return_data['out_pred_pre'] = out_data['pred_pre']
    return_data['out_trde_qty'] = out_data['trde_qty']
    return_data['out_etfnetprps_qty_array'] = out_data['etfnetprps_qty_array']
    
    return return_data

  def get_ka40009(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ETF시간대별체결요청
    메뉴 위치 : 국내주식 > ETF > ETF시간대별체결요청(ka40009)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_etfnavarray (list): ETFNAV배열
        - nav (str(20)): NAV
        - navpred_pre (str(20)): NAV전일대비
        - navflu_rt (str(20)): NAV등락율
        - trace_eor_rt (str(20)): 추적오차율
        - dispty_rt (str(20)): 괴리율
        - stkcnt (str(20)): 주식수
        - base_pric (str(20)): 기준가
        - for_rmnd_qty (str(20)): 외인보유수량
        - repl_pric (str(20)): 대용가
        - conv_pric (str(20)): 환산가격
        - drstk (str(20)): DR/주
        - wonju_pric (str(20)): 원주가격
    
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
      'api-id': 'ka40009',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/etf'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_etfnavarray'] = out_data['etfnavarray']
    
    return return_data

  def get_ka40010(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str):
    """
    ETF시간대별추이요청
    메뉴 위치 : 국내주식 > ETF > ETF시간대별추이요청(ka40010)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(6)): 종목코드(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_etftisl_trnsn (list): ETF시간대별추이
        - cur_prc (str(20)): 현재가
        - pre_sig (str(20)): 대비기호
        - pred_pre (str(20)): 전일대비
        - trde_qty (str(20)): 거래량
        - for_netprps (str(20)): 외인순매수
    
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
      'api-id': 'ka40010',
    }
    params = {
      'stk_cd': in_stk_cd,
    }
    url = '/api/dostk/etf'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_etftisl_trnsn'] = out_data['etftisl_trnsn']
    
    return return_data

  def get_ka90001(self, in_cont_yn: str, in_next_key: str, in_qry_tp: str, in_stk_cd: str, in_date_tp: str, in_thema_nm: str, in_flu_pl_amt_tp: str, in_stex_tp: str):
    """
    테마그룹별요청
    메뉴 위치 : 국내주식 > 테마 > 테마그룹별요청(ka90001)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_qry_tp (str(1)): 검색구분(필수) 0:전체검색, 1:테마검색, 2:종목검색
      in_stk_cd (str(6)): 종목코드 검색하려는 종목코드
      in_date_tp (str(2)): 날짜구분(필수) n일전 (1일 ~ 99일 날짜입력)
      in_thema_nm (str(50)): 테마명 검색하려는 테마명
      in_flu_pl_amt_tp (str(1)): 등락수익구분(필수) 1:상위기간수익률, 2:하위기간수익률, 3:상위등락률, 4:하위등락률
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_thema_grp (list): 테마그룹별
        - thema_grp_cd (str(20)): 테마그룹코드
        - thema_nm (str(20)): 테마명
        - stk_num (str(20)): 종목수
        - flu_sig (str(20)): 등락기호
        - flu_rt (str(20)): 등락율
        - rising_stk_num (str(20)): 상승종목수
        - fall_stk_num (str(20)): 하락종목수
        - dt_prft_rt (str(20)): 기간수익률
        - main_stk (str(20)): 주요종목
    
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
      'api-id': 'ka90001',
    }
    params = {
      'qry_tp': in_qry_tp,
      'stk_cd': in_stk_cd,
      'date_tp': in_date_tp,
      'thema_nm': in_thema_nm,
      'flu_pl_amt_tp': in_flu_pl_amt_tp,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/thme'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_thema_grp'] = out_data['thema_grp']
    
    return return_data

  def get_ka90002(self, in_cont_yn: str, in_next_key: str, in_date_tp: str, in_thema_grp_cd: str, in_stex_tp: str):
    """
    테마구성종목요청
    메뉴 위치 : 국내주식 > 테마 > 테마구성종목요청(ka90002)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_date_tp (str(1)): 날짜구분 1일 ~ 99일 날짜입력
      in_thema_grp_cd (str(6)): 테마그룹코드(필수) 테마그룹코드 번호
      in_stex_tp (str(1)): 거래소구분(필수) 1:KRX, 2:NXT 3.통합
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_flu_rt (str(20)): 등락률
      out_dt_prft_rt (str(20)): 기간수익률
      out_thema_comp_stk (list): 테마구성종목
        - stk_cd (str(20)): 종목코드
        - stk_nm (str(40)): 종목명
        - cur_prc (str(20)): 현재가
        - flu_sig (str(20)): 등락기호. 1: 상한가, 2:상승, 3:보합, 4:하한가, 5:하락
        - pred_pre (str(20)): 전일대비
        - flu_rt (str(20)): 등락율
        - acc_trde_qty (str(20)): 누적거래량
        - sel_bid (str(20)): 매도호가
        - sel_req (str(20)): 매도잔량
        - buy_bid (str(20)): 매수호가
        - buy_req (str(20)): 매수잔량
        - dt_prft_rt_n (str(20)): 기간수익률n
    
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
      'api-id': 'ka90002',
    }
    params = {
      'date_tp': in_date_tp,
      'thema_grp_cd': in_thema_grp_cd,
      'stex_tp': in_stex_tp,
    }
    url = '/api/dostk/thme'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_flu_rt'] = out_data['flu_rt']
    return_data['out_dt_prft_rt'] = out_data['dt_prft_rt']
    return_data['out_thema_comp_stk'] = out_data['thema_comp_stk']
    
    return return_data

  def get_kt10000(self, in_cont_yn: str, in_next_key: str, in_dmst_stex_tp: str, in_stk_cd: str, in_ord_qty: str, in_ord_uv: str, in_trde_tp: str, in_cond_uv: str):
    """
    주식 매수주문
    메뉴 위치 : 국내주식 > 주문 > 주식 매수주문(kt10000)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dmst_stex_tp (str(3)): 국내거래소구분(필수) KRX,NXT,SOR
      in_stk_cd (str(12)): 종목코드(필수)
      in_ord_qty (str(12)): 주문수량(필수)
      in_ord_uv (str(12)): 주문단가
      in_trde_tp (str(2)): 매매구분(필수) 0:보통 , 3:시장가 , 5:조건부지정가 , 81:장마감후시간외 , 61:장시작전시간외, 62:시간외단일가 , 6:최유리지정가 , 7:최우선지정가 , 10:보통(IOC) , 13:시장가(IOC) , 16:최유리(IOC) , 20:보통(FOK) , 23:시장가(FOK) , 26:최유리(FOK) , 28:스톱지정가,29:중간가,30:중간가(IOC),31:중간가(FOK)
      in_cond_uv (str(12)): 조건단가
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
      out_dmst_stex_tp (str(6)): 국내거래소구분
    
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
      'api-id': 'kt10000',
    }
    params = {
      'dmst_stex_tp': in_dmst_stex_tp,
      'stk_cd': in_stk_cd,
      'ord_qty': in_ord_qty,
      'ord_uv': in_ord_uv,
      'trde_tp': in_trde_tp,
      'cond_uv': in_cond_uv,
    }
    url = '/api/dostk/ordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    return_data['out_dmst_stex_tp'] = out_data['dmst_stex_tp']
    
    return return_data

  def get_kt10001(self, in_cont_yn: str, in_next_key: str, in_dmst_stex_tp: str, in_stk_cd: str, in_ord_qty: str, in_ord_uv: str, in_trde_tp: str, in_cond_uv: str):
    """
    주식 매도주문
    메뉴 위치 : 국내주식 > 주문 > 주식 매도주문(kt10001)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dmst_stex_tp (str(3)): 국내거래소구분(필수) KRX,NXT,SOR
      in_stk_cd (str(12)): 종목코드(필수)
      in_ord_qty (str(12)): 주문수량(필수)
      in_ord_uv (str(12)): 주문단가
      in_trde_tp (str(2)): 매매구분(필수) 0:보통 , 3:시장가 , 5:조건부지정가 , 81:장마감후시간외 , 61:장시작전시간외, 62:시간외단일가 , 6:최유리지정가 , 7:최우선지정가 , 10:보통(IOC) , 13:시장가(IOC) , 16:최유리(IOC) , 20:보통(FOK) , 23:시장가(FOK) , 26:최유리(FOK) , 28:스톱지정가,29:중간가,30:중간가(IOC),31:중간가(FOK)
      in_cond_uv (str(12)): 조건단가
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
      out_dmst_stex_tp (str(6)): 국내거래소구분
    
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
      'api-id': 'kt10001',
    }
    params = {
      'dmst_stex_tp': in_dmst_stex_tp,
      'stk_cd': in_stk_cd,
      'ord_qty': in_ord_qty,
      'ord_uv': in_ord_uv,
      'trde_tp': in_trde_tp,
      'cond_uv': in_cond_uv,
    }
    url = '/api/dostk/ordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    return_data['out_dmst_stex_tp'] = out_data['dmst_stex_tp']
    
    return return_data

  def get_kt10002(self, in_cont_yn: str, in_next_key: str, in_dmst_stex_tp: str, in_orig_ord_no: str, in_stk_cd: str, in_mdfy_qty: str, in_mdfy_uv: str, in_mdfy_cond_uv: str):
    """
    주식 정정주문
    메뉴 위치 : 국내주식 > 주문 > 주식 정정주문(kt10002)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dmst_stex_tp (str(3)): 국내거래소구분(필수) KRX,NXT,SOR
      in_orig_ord_no (str(7)): 원주문번호(필수)
      in_stk_cd (str(12)): 종목코드(필수)
      in_mdfy_qty (str(12)): 정정수량(필수)
      in_mdfy_uv (str(12)): 정정단가(필수)
      in_mdfy_cond_uv (str(12)): 정정조건단가
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
      out_base_orig_ord_no (str(7)): 모주문번호
      out_mdfy_qty (str(12)): 정정수량
      out_dmst_stex_tp (str(6)): 국내거래소구분
    
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
      'api-id': 'kt10002',
    }
    params = {
      'dmst_stex_tp': in_dmst_stex_tp,
      'orig_ord_no': in_orig_ord_no,
      'stk_cd': in_stk_cd,
      'mdfy_qty': in_mdfy_qty,
      'mdfy_uv': in_mdfy_uv,
      'mdfy_cond_uv': in_mdfy_cond_uv,
    }
    url = '/api/dostk/ordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    return_data['out_base_orig_ord_no'] = out_data['base_orig_ord_no']
    return_data['out_mdfy_qty'] = out_data['mdfy_qty']
    return_data['out_dmst_stex_tp'] = out_data['dmst_stex_tp']
    
    return return_data

  def get_kt10003(self, in_cont_yn: str, in_next_key: str, in_dmst_stex_tp: str, in_orig_ord_no: str, in_stk_cd: str, in_cncl_qty: str):
    """
    주식 취소주문
    메뉴 위치 : 국내주식 > 주문 > 주식 취소주문(kt10003)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dmst_stex_tp (str(3)): 국내거래소구분(필수) KRX,NXT,SOR
      in_orig_ord_no (str(7)): 원주문번호(필수)
      in_stk_cd (str(12)): 종목코드(필수)
      in_cncl_qty (str(12)): 취소수량(필수) '0' 입력시 잔량 전부 취소
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
      out_base_orig_ord_no (str(7)): 모주문번호
      out_cncl_qty (str(12)): 취소수량
    
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
      'api-id': 'kt10003',
    }
    params = {
      'dmst_stex_tp': in_dmst_stex_tp,
      'orig_ord_no': in_orig_ord_no,
      'stk_cd': in_stk_cd,
      'cncl_qty': in_cncl_qty,
    }
    url = '/api/dostk/ordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    return_data['out_base_orig_ord_no'] = out_data['base_orig_ord_no']
    return_data['out_cncl_qty'] = out_data['cncl_qty']
    
    return return_data

  def get_kt50000(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_ord_qty: str, in_ord_uv: str, in_trde_tp: str):
    """
    금현물 매수주문
    메뉴 위치 : 국내주식 > 주문 > 금현물 매수주문(kt50000)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(12)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_ord_qty (str(12)): 주문수량(필수)
      in_ord_uv (str(12)): 주문단가
      in_trde_tp (str(2)): 매매구분(필수) 00:보통, 10:보통(IOC), 20:보통(FOK)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
    
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
      'api-id': 'kt50000',
    }
    params = {
      'stk_cd': in_stk_cd,
      'ord_qty': in_ord_qty,
      'ord_uv': in_ord_uv,
      'trde_tp': in_trde_tp,
    }
    url = '/api/dostk/ordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    
    return return_data

  def get_kt50001(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_ord_qty: str, in_ord_uv: str, in_trde_tp: str):
    """
    금현물 매도주문
    메뉴 위치 : 국내주식 > 주문 > 금현물 매도주문(kt50001)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(12)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_ord_qty (str(12)): 주문수량(필수)
      in_ord_uv (str(12)): 주문단가
      in_trde_tp (str(2)): 매매구분(필수) 00:보통, 10:보통(IOC), 20:보통(FOK)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
    
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
      'api-id': 'kt50001',
    }
    params = {
      'stk_cd': in_stk_cd,
      'ord_qty': in_ord_qty,
      'ord_uv': in_ord_uv,
      'trde_tp': in_trde_tp,
    }
    url = '/api/dostk/ordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    
    return return_data

  def get_kt50002(self, in_cont_yn: str, in_next_key: str, in_stk_cd: str, in_orig_ord_no: str, in_mdfy_qty: str, in_mdfy_uv: str):
    """
    금현물 정정주문
    메뉴 위치 : 국내주식 > 주문 > 금현물 정정주문(kt50002)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_stk_cd (str(12)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_orig_ord_no (str(7)): 원주문번호(필수)
      in_mdfy_qty (str(12)): 정정수량(필수)
      in_mdfy_uv (str(12)): 정정단가(필수)
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
      out_base_orig_ord_no (str(7)): 모주문번호
      out_mdfy_qty (str(12)): 정정수량
    
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
      'api-id': 'kt50002',
    }
    params = {
      'stk_cd': in_stk_cd,
      'orig_ord_no': in_orig_ord_no,
      'mdfy_qty': in_mdfy_qty,
      'mdfy_uv': in_mdfy_uv,
    }
    url = '/api/dostk/ordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    return_data['out_base_orig_ord_no'] = out_data['base_orig_ord_no']
    return_data['out_mdfy_qty'] = out_data['mdfy_qty']
    
    return return_data

  def get_kt50003(self, in_cont_yn: str, in_next_key: str, in_orig_ord_no: str, in_stk_cd: str, in_cncl_qty: str):
    """
    금현물 취소주문
    메뉴 위치 : 국내주식 > 주문 > 금현물 취소주문(kt50003)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_orig_ord_no (str(7)): 원주문번호(필수)
      in_stk_cd (str(12)): 종목코드(필수) M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
      in_cncl_qty (str(12)): 취소수량(필수) '0' 입력시 잔량 전부 취소
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
      out_base_orig_ord_no (str(7)): 모주문번호
      out_cncl_qty (str(12)): 취소수량
    
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
      'api-id': 'kt50003',
    }
    params = {
      'orig_ord_no': in_orig_ord_no,
      'stk_cd': in_stk_cd,
      'cncl_qty': in_cncl_qty,
    }
    url = '/api/dostk/ordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    return_data['out_base_orig_ord_no'] = out_data['base_orig_ord_no']
    return_data['out_cncl_qty'] = out_data['cncl_qty']
    
    return return_data

  def get_kt10006(self, in_cont_yn: str, in_next_key: str, in_dmst_stex_tp: str, in_stk_cd: str, in_ord_qty: str, in_ord_uv: str, in_trde_tp: str, in_cond_uv: str):
    """
    신용 매수주문
    메뉴 위치 : 국내주식 > 신용주문 > 신용 매수주문(kt10006)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dmst_stex_tp (str(3)): 국내거래소구분(필수) KRX,NXT,SOR
      in_stk_cd (str(12)): 종목코드(필수)
      in_ord_qty (str(12)): 주문수량(필수)
      in_ord_uv (str(12)): 주문단가
      in_trde_tp (str(2)): 매매구분(필수) 0:보통 , 3:시장가 , 5:조건부지정가 , 81:장마감후시간외 , 61:장시작전시간외, 62:시간외단일가 , 6:최유리지정가 , 7:최우선지정가 , 10:보통(IOC) , 13:시장가(IOC) , 16:최유리(IOC) , 20:보통(FOK) , 23:시장가(FOK) , 26:최유리(FOK) , 28:스톱지정가,29:중간가,30:중간가(IOC),31:중간가(FOK)
      in_cond_uv (str(12)): 조건단가
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
      out_dmst_stex_tp (str(6)): 국내거래소구분
    
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
      'api-id': 'kt10006',
    }
    params = {
      'dmst_stex_tp': in_dmst_stex_tp,
      'stk_cd': in_stk_cd,
      'ord_qty': in_ord_qty,
      'ord_uv': in_ord_uv,
      'trde_tp': in_trde_tp,
      'cond_uv': in_cond_uv,
    }
    url = '/api/dostk/crdordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    return_data['out_dmst_stex_tp'] = out_data['dmst_stex_tp']
    
    return return_data

  def get_kt10007(self, in_cont_yn: str, in_next_key: str, in_dmst_stex_tp: str, in_stk_cd: str, in_ord_qty: str, in_ord_uv: str, in_trde_tp: str, in_crd_deal_tp: str, in_crd_loan_dt: str, in_cond_uv: str):
    """
    신용 매도주문
    메뉴 위치 : 국내주식 > 신용주문 > 신용 매도주문(kt10007)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dmst_stex_tp (str(3)): 국내거래소구분(필수) KRX,NXT,SOR
      in_stk_cd (str(12)): 종목코드(필수)
      in_ord_qty (str(12)): 주문수량(필수)
      in_ord_uv (str(12)): 주문단가
      in_trde_tp (str(2)): 매매구분(필수) 0:보통 , 3:시장가 , 5:조건부지정가 , 81:장마감후시간외 , 61:장시작전시간외, 62:시간외단일가 , 6:최유리지정가 , 7:최우선지정가 , 10:보통(IOC) , 13:시장가(IOC) , 16:최유리(IOC) , 20:보통(FOK) , 23:시장가(FOK) , 26:최유리(FOK) , 28:스톱지정가,29:중간가,30:중간가(IOC),31:중간가(FOK)
      in_crd_deal_tp (str(2)): 신용거래구분(필수) 33:융자 , 99:융자합
      in_crd_loan_dt (str(8)): 대출일 YYYYMMDD(융자일경우필수)
      in_cond_uv (str(12)): 조건단가
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
      out_dmst_stex_tp (str(6)): 국내거래소구분
    
    Raises:
      Exception: 에러
    """
    
    if not self.token_data:
      self.connect()
    
    if not in_crd_loan_dt or in_crd_loan_dt == '':
      in_crd_loan_dt = format_datetime('%Y%m%d')
    
    token = self.token_data['token']
    headers = {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {token}',
      'cont-yn': in_cont_yn,
      'next-key': in_next_key,
      'api-id': 'kt10007',
    }
    params = {
      'dmst_stex_tp': in_dmst_stex_tp,
      'stk_cd': in_stk_cd,
      'ord_qty': in_ord_qty,
      'ord_uv': in_ord_uv,
      'trde_tp': in_trde_tp,
      'crd_deal_tp': in_crd_deal_tp,
      'crd_loan_dt': in_crd_loan_dt,
      'cond_uv': in_cond_uv,
    }
    url = '/api/dostk/crdordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    return_data['out_dmst_stex_tp'] = out_data['dmst_stex_tp']
    
    return return_data

  def get_kt10008(self, in_cont_yn: str, in_next_key: str, in_dmst_stex_tp: str, in_orig_ord_no: str, in_stk_cd: str, in_mdfy_qty: str, in_mdfy_uv: str, in_mdfy_cond_uv: str):
    """
    신용 정정주문
    메뉴 위치 : 국내주식 > 신용주문 > 신용 정정주문(kt10008)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dmst_stex_tp (str(3)): 국내거래소구분(필수) KRX,NXT,SOR
      in_orig_ord_no (str(7)): 원주문번호(필수)
      in_stk_cd (str(12)): 종목코드(필수)
      in_mdfy_qty (str(12)): 정정수량(필수)
      in_mdfy_uv (str(12)): 정정단가(필수)
      in_mdfy_cond_uv (str(12)): 정정조건단가
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
      out_base_orig_ord_no (str(7)): 모주문번호
      out_mdfy_qty (str(12)): 정정수량
      out_dmst_stex_tp (str(6)): 국내거래소구분
    
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
      'api-id': 'kt10008',
    }
    params = {
      'dmst_stex_tp': in_dmst_stex_tp,
      'orig_ord_no': in_orig_ord_no,
      'stk_cd': in_stk_cd,
      'mdfy_qty': in_mdfy_qty,
      'mdfy_uv': in_mdfy_uv,
      'mdfy_cond_uv': in_mdfy_cond_uv,
    }
    url = '/api/dostk/crdordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    return_data['out_base_orig_ord_no'] = out_data['base_orig_ord_no']
    return_data['out_mdfy_qty'] = out_data['mdfy_qty']
    return_data['out_dmst_stex_tp'] = out_data['dmst_stex_tp']
    
    return return_data

  def get_kt10009(self, in_cont_yn: str, in_next_key: str, in_dmst_stex_tp: str, in_orig_ord_no: str, in_stk_cd: str, in_cncl_qty: str):
    """
    신용 취소주문
    메뉴 위치 : 국내주식 > 신용주문 > 신용 취소주문(kt10009)
    
    Args:
      in_cont_yn (str(1)): 연속조회여부 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅
      in_next_key (str(50)): 연속조회키 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅
      in_dmst_stex_tp (str(3)): 국내거래소구분(필수) KRX,NXT,SOR
      in_orig_ord_no (str(7)): 원주문번호(필수)
      in_stk_cd (str(12)): 종목코드(필수)
      in_cncl_qty (str(12)): 취소수량(필수) '0' 입력시 잔량 전부 취소
    
    Returns:
      out_cont_yn (str(1)): 연속조회여부. 다음 데이터가 있을시 Y값 전달
      out_next_key (str(50)): 연속조회키. 다음 데이터가 있을시 다음 키값 전달
      out_ord_no (str(7)): 주문번호
      out_base_orig_ord_no (str(7)): 모주문번호
      out_cncl_qty (str(12)): 취소수량
    
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
      'api-id': 'kt10009',
    }
    params = {
      'dmst_stex_tp': in_dmst_stex_tp,
      'orig_ord_no': in_orig_ord_no,
      'stk_cd': in_stk_cd,
      'cncl_qty': in_cncl_qty,
    }
    url = '/api/dostk/crdordr'
    
    header_data, out_data = self._send_request(url, params, headers)
    
    if not out_data or out_data['return_code'] != 0:
      msg = out_data['return_msg'] if out_data and out_data['return_msg'] else 'Error'
      raise Exception(msg)
    
    return_data = {}
    
    if header_data:
      return_data['out_cont_yn'] = header_data['cont-yn']
      return_data['out_next_key'] = header_data['next-key']
    
    return_data['out_ord_no'] = out_data['ord_no']
    return_data['out_base_orig_ord_no'] = out_data['base_orig_ord_no']
    return_data['out_cncl_qty'] = out_data['cncl_qty']
    
    return return_data
