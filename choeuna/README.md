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