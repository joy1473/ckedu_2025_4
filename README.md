# CK Edu 2025 4기 프로젝트

2025년 4기 창의코딩교육(CK Edu) 과정에서 진행하는 프로젝트 저장소입니다.

## 프로젝트 개요
- **교육 과정**: 창의코딩교육 2025년 4기
- **목표**: Python, 웹 개발, AI 등을 활용한 실전 프로젝트 제작
- **주요 기술**: Python, Flask/FastAPI, HTML/CSS/JavaScript, Git & GitHub 등

## 폴더 구조
```
ckedu_2025_4/
└── app/                # 메인 애플리케이션 코드
   ├── adm/     # 어드민
   ├── aut/     # 인증 및 API 관련
   ├── emo/     # 감정 분석 관련
   ├── esc/     # 모의주식 관련
   ├── ctg/     # 카테고리 / 추천 관련
   └── bye/     # 해지 / 탈퇴 / 청산 관련
├── static/             # CSS, JS, 이미지 파일
├── templates/          # HTML 템플릿
├── data/               # 데이터 파일 (CSV, JSON 등)
├── doc/
├── requirements.txt    # 필요한 파이썬 패키지 목록
├── README.md           # 이 설명 파일
└── .gitignore          # 업로드 제외 파일 설정
```

## 실행 방법

### 1. 저장소 복제
```bash
git clone https://github.com/joy1473/ckedu_2025_4.git
cd ckedu_2025_4
```

### 2. 가상환경 설정 및 패키지 설치
```bash
python -m venv venv
# Mac : source venv/bin/activate
# Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 애플리케이션 실행
```bash
python main.py
```

브라우저에서 `http://127.0.0.1:5000` 접속

## 참여 방법 (팀원용)
1. GitHub 계정으로 로그인
2. 자신의 이름으로 브랜치 생성:
   ```bash
   git checkout -b feature/본인이름-기능명
   ```
3. 작업 후 커밋 & 푸시:
   ```bash
   git add .
   git commit -m "기능 설명"
   git push origin feature/본인이름-기능명
   ```
4. GitHub에서 Pull Request 생성 → 리뷰 후 병합

## 기여자
- joy1473 (리더 / 메인 개발자)
- (팀원 이름 추가 예정)

## 라이선스
교육 목적 프로젝트입니다. 상업적 사용 금지.

---

문의: GitHub Issues 또는 joy1473에게 DM 주세요!

## 모듈별 상세 설명

### /app/aut - 인증 및 API 관련
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

### /app/ctg - 카테고리 / 추천 관련
# CK Edu 2025 4기 프로젝트

2025년 4기 창의코딩교육(CK Edu) 과정에서 진행하는 프로젝트 저장소입니다.

## 프로젝트 개요
- **교육 과정**: 창의코딩교육 2025년 4기
- **목표**: Python, 웹 개발, AI 등을 활용한 실전 프로젝트 제작
- **주요 기술**: Python, Flask/FastAPI, HTML/CSS/JavaScript, Git & GitHub 등

## 폴더 구조
```
ckedu_2025_4/
├── app/                # 메인 애플리케이션 코드 (예: Flask 또는 FastAPI)
├── static/             # CSS, JS, 이미지 파일
├── templates/          # HTML 템플릿 (Flask 사용 시)
├── data/               # 데이터 파일 (CSV, JSON 등)
├── notebooks/          # Jupyter 노트북 실습 파일
├── requirements.txt    # 필요한 파이썬 패키지 목록
├── README.md           # 이 설명 파일
└── .gitignore          # 업로드 제외 파일 설정
```

## 실행 방법

### 1. 저장소 복제
```bash
git clone https://github.com/joy1473/ckedu_2025_4.git
cd ckedu_2025_4
```

### 2. 가상환경 설정 및 패키지 설치
```bash
python -m venv venv
# Mac : source venv/bin/activate
# Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 애플리케이션 실행
```bash
python app/main.py
```

브라우저에서 `http://127.0.0.1:5000` 접속

## 참여 방법 (팀원용)
1. GitHub 계정으로 로그인
2. 자신의 이름으로 브랜치 생성:
   ```bash
   git checkout -b feature/본인이름-기능명
   ```
3. 작업 후 커밋 & 푸시:
   ```bash
   git add .
   git commit -m "기능 설명"
   git push origin feature/본인이름-기능명
   ```
4. GitHub에서 Pull Request 생성 → 리뷰 후 병합

## 기여자
- joy1473 (리더 / 메인 개발자)
- (팀원 이름 추가 예정)

## 라이선스
교육 목적 프로젝트입니다. 상업적 사용 금지.

---

문의: GitHub Issues 또는 joy1473에게 DM 주세요!

### /app/bye - 해지 / 탈퇴 / 청산 관련
# XXX 프로젝트 - 함수 규칙 및 예시 코드

맞춤 초이스, 도매 가격! 함수 규칙, 똑똑 비용!  
도매로 사서, 시공비만 내자! 재료는 네 맘, 코드 구조는 최소야!  
친환경 함수, 도매 링크 클릭! 비용 쭉↓↓, 생산성 쭉↑↑!  
철거도 도매, 함수도 도매! 복잡한 과정 쏙, 코드 업그레이드!  
너가 고르고, 도매로 사고, 우리는 구현해! 투명 규칙, 완벽 소스!  
뭉뚱그려? NO! 맞춤+도매+함수규칙, 스마트 개발 GO!

## 함수 작성 규칙 (모든 함수 100% 준수)

### 패키지 구조
```
/app/
├── aut/     # 인증 및 API 관련
├── emo/     # 감정 분석 관련
├── esc/     # 모의주식 관련
├── ctg/     # 카테고리 / 추천 관련
└── bye/     # 해지 / 탈퇴 / 청산 관련
```

### 함수명 규칙
- 시작은 `set_` 또는 `get_`

### 입력 파라미터
- `in_xxx` 형식으로 명명

### 출력
- `out_xxx` 키를 가진 딕셔너리 반환

### 함수 주석 (반드시 맨 위에!)
```python
"""
# 설명 : 함수 목적 설명
# 입력 : in_파라미터1 (타입) - 설명
# 출력 : out_키1 (타입) - 설명
# 소스 : 테이블명, 기관명 또는 출처
"""
```

## 예시 함수들

### /app/aut/auth.py
```python
def set_user_auth(in_user_id: str, in_access_token: str):
    """
    # 설명 : 사용자 인증 토큰 저장 (오픈뱅킹 인증 후)
    # 입력 : in_user_id (str) - 사용자 ID
            in_access_token (str) - 오픈뱅킹 토큰
    # 출력 : out_success (bool) - 성공 여부
            out_message (str) - 처리 결과 메시지
    # 소스 : users 테이블, 오픈뱅킹
    """
    try:
        collection = db["users"]
        collection.update_one(
            {"user_id": in_user_id},
            {"$set": {"access_token": in_access_token, "updated_at": datetime.now()}},
            upsert=True
        )
        out_success = True
        out_message = "인증 토큰 저장 성공"
    except Exception as e:
        out_success = False
        out_message = f"인증 저장 실패: {str(e)}"
    
    return {"out_success": out_success, "out_message": out_message}
```

### /app/emo/sentiment.py
```python
def get_sentiment_score(in_text: str):
    """
    # 설명 : 입력 텍스트의 감정 점수 분석
    # 입력 : in_text (str) - 사용자 입력 문장
    # 출력 : out_label (str) - POSITIVE/NEUTRAL/NEGATIVE
            out_score (float) - 감정 점수 (0~100)
    # 소스 : sentiment 모델, Grok/Claude API
    """
    try:
        result = sentiment_model(in_text)
        out_label = result["label"].upper()
        out_score = round(result["score"] * 100, 2)
    except:
        out_label = "NEUTRAL"
        out_score = 50.0
    
    return {"out_label": out_label, "out_score": out_score}
```

### /app/esc/mock.py
```python
def set_mock_trade(in_user_id: str, in_stock: str, in_quantity: int, in_price: float):
    """
    # 설명 : 모의주식 거래 기록 저장
    # 입력 : in_user_id (str) - 사용자 ID
            in_stock (str) - 종목 코드
            in_quantity (int) - 수량
            in_price (float) - 가격
    # 출력 : out_trade_id (str) - 거래 ID
            out_success (bool) - 성공 여부
    # 소스 : mock_trades 테이블, 키움 모의 API
    """
    trade_doc = {
        "user_id": in_user_id,
        "stock": in_stock,
        "quantity": in_quantity,
        "price": in_price,
        "timestamp": datetime.now(),
        "type": "mock"
    }
    result = collection_mock.insert_one(trade_doc)
    
    return {
        "out_trade_id": str(result.inserted_id),
        "out_success": True
    }
```

### /app/ctg/recommend.py
```python
def get_recommend_stocks(in_user_id: str, in_risk_level: str):
    """
    # 설명 : 사용자 위험 성향에 맞는 추천 종목 반환
    # 입력 : in_user_id (str) - 사용자 ID
            in_risk_level (str) - low/medium/high
    # 출력 : out_stocks (list) - 추천 종목 리스트
            out_reason (str) - 추천 이유
    # 소스 : recommend 테이블, RAG 기반 AI
    """
    recommended = ["삼성전자", "카카오", "현대차"] if in_risk_level == "medium" else ["국고채", "예금"]
    
    return {
        "out_stocks": recommended,
        "out_reason": f"{in_risk_level} 위험 수준 추천"
    }
```

### /app/bye/withdraw.py
```python
def set_auto_withdraw(in_user_id: str):
    """
    # 설명 : 탈퇴 자동 청산 프로세스 실행
    # 입력 : in_user_id (str) - 사용자 ID
    # 출력 : out_success (bool) - 성공 여부
            out_message (str) - 처리 결과 메시지
            out_steps (list) - 진행 단계 리스트
    # 소스 : trades/portfolio 테이블, 키움 API + 오픈뱅킹
    """
    steps = []
    try:
        steps.append("보유 주식 시장가 매도 완료")
        steps.append("잔고 은행 계좌로 이체 완료")
        steps.append("앱 내 데이터 완전 삭제")
        out_success = True
        out_message = "자동 청산 완료! 증권계좌는 직접 해지하세요."
    except:
        out_success = False
        out_message = "청산 중 오류 발생"
        steps = ["오류 발생"]
    
    return {
        "out_success": out_success,
        "out_message": out_message,
        "out_steps": steps
    }
```
```
