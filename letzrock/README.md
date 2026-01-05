# 오픈뱅킹 기반 조회: 은행/증권 계좌 연동으로 간편 가입. 거래내역 통합 조회

## 백엔드 소스 폴더 구조
```
01/
├── logs/                 # 로그 디렉토리
├── templates/            # Flask 템플릿 HTML
├── .env                  # 오픈뱅킹 계좌통합조회 api 거래고유번호, 계좌통합조회 리스트번호 정보
├── api_test.py           # 유틸 함수 파일
├── app_1.py              # 오픈뱅킹 함수 파일
├── kiwoom_api.py         # 키움증권 API 파일
├── korea_investment_api  # 한국투자증권 API 파일
├── openbank_user_app.py  # 오픈뱅킹 사용자 인증 테스트 파일
├── openbankcallback.py   # choeuna/choeuna1/openbankcallback.py 파일을 테스트를 위해 수정
└── requirements.txt      # 필요한 파이썬 패키지 목록
```

## 오픈뱅킹 API 사용 방법
from app_1 import get_user_info, get_account_list

### 오픈뱅킹 사용자 인증 후 계좌 등록
1. openbank_user_app.py 파일 실행
```bash
cd letzrock/01
python openbank_user_app.py
```
2. http://localhost:5050 접속
3. 오픈뱅킹 사용자 인증 시작
4. 새 창에서 휴대폰 인증 후 계좌 정보 등록
5. 등록 결과 확인

**인증**
-> **토큰 각각 발행** : 사용자_토큰_정보.json / 자체인증_이용기관_토큰_정보.json 파일로 저장
-> **사용자정보조회 API 로 등록 정보 확인** : 사용자_정보.json 파일로 저장 (인증을 여러번 실행시 등록한 계좌 모두 조회됨. 최근 1건만 저장)


## 키움증권 API 사용 방법
1. 키움증권 계좌 개설
https://www.kiwoom.com/

2. 키움증권 API 사용 신청
https://openapi.kiwoom.com/

3. 
```bash
from kiwoom_api import KiwoomAPI

# user1 계좌의 앱키
app_key = "PSg5dctL9dKPo727J13Ur405OSXXXXXXXXXX"
# user1 계좌의 시크릿키
app_secret = "yo2t8zS68zpdjGuWvFyM9VikjXE0OIXXXXXXXXXX"
# user1 계좌의 API 객체
user1_kiwoom_api = KiwoomAPI(True, app_key, app_secret)
# 접근토큰 발급 요청
user1_kiwoom_api.connect()

# 일별거래상세요청
in_cont_yn = ''
in_next_key = ''
in_stk_cd = '039490'
in_strt_dt = '20260106'
result_data = user1_kiwoom_api.get_ka10015(in_cont_yn, in_next_key, in_stk_cd, in_strt_dt)
print(result_data)
```

## 한국투자증권 API 사용 방법
1. 한국투자증권 계좌 개설
https://securities.koreainvestment.com/

2. 한국투자증권 API 사용 신청
https://apiportal.koreainvestment.com/

3. 
```bash
from korea_investment_api import KoreaInvestmentAPI

# user1 계좌의 앱키
app_key = "PSg5dctL9dKPo727J13Ur405OSXXXXXXXXXX"
# user1 계좌의 시크릿키
app_secret = "yo2t8zS68zpdjGuWvFyM9VikjXE0i0CbgPEamnqPA00G0bIfrdfQb2RUD1xP7SqatQXr1cD1fGUNsb78MMXoq6o4lAYt9YTtHAjbMoFy+c72kbq5owQY1Pvp39/x6ejpJlXCj7gE3yVOB/h25Hvl+URmYeBTfrQeOqIAOYc/OIXXXXXXXXXX"
# user1 계좌의 API 객체
user1_ki_api = KoreaInvestmentAPI(True, app_key, app_secret)
# 접근토큰 발급 요청
user1_ki_api.connect()

# 매도가능수량조회
in_tr_id = 'TTTC8408R'
in_tr_cont = ''
in_custtype = 'P'
in_seq_no = ''
in_mac_address = ''
in_phone_number = ''
in_ip_addr = ''
in_gt_uid = ''
in_CANO = '12345678'
in_ACNT_PRDT_CD = '01'
in_PDNO = '000660'
result_data = user1_ki_api.get_trading_inquire_psbl_sell(in_tr_id, in_tr_cont, in_custtype, in_seq_no, in_mac_address, in_phone_number, in_ip_addr, in_gt_uid, in_CANO, in_ACNT_PRDT_CD, in_PDNO)
print(result_data)
```
