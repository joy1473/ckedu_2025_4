# 🚀 LUA Onboarding & Task Management Contract

본 문서는 **LUA 서비스**의 온보딩 프로세스와 실전 업무(주식/뱅킹) 대응을 위한 프롬프트 관리 체계를 정의합니다.

---

## 1. 온보딩 상태 머신 (Frontend State Machine)
* **Flow:** INTRO → NAME → BIRTHDATE → GENDER → CONSENT → SUITABILITY → READY
* **특이사항:** “이전” 입력 시 1-step back 지원, 새로고침 시 세션 복원(Persistence).

---

## 2. 입력 검증 규칙 (Validation Rules)
* **NAME:** 2~20자 실명 (닉네임/테스트 계정 필터링)
* **BIRTHDATE:** `YYYYMMDD` 형식 (만 19세 기준 `is_minor` 판정)
* **GENDER:** M/F 정규화
* **CONSENT:** 실전 투자 위험 고지 동의 (`true`/`false`)

---

## 3. 저장 데이터 모델 (User Profile / Session)
```json
{
  "real_name": "홍길동",
  "is_minor": false,
  "case_id": "case_01",
  "consent_investment_risk": true,
  "risk_level": 1,
  "risk_label": "매우 공격형"
}
```
## 4. Case & Policy 핵심 규칙
Case Override: is_minor == true 시 무조건 case_id = case_05 강제.

Consent Rule: 투자 미동의 시 실전 거래 기능 차단 및 동의 안내 모드 진입.

Intent-Based Task: 유저 메시지에서 '주식' 또는 '뱅킹' 의도 감지 시 전용 지침 결합.

## 5. 프롬프트 관리 시스템 (Prompt Management)
📁 폴더 구조 및 역할
/intro: 온보딩 단계별 안내 문구

/persona: 케이스별 AI 인격 정의 (MZ, 직장인, 은퇴자 등)

/suitability: 투자 성향 진단 및 결과 문구

/consent: 동의/거부 관련 안내 문구

/task (NEW): 실전 업무별 시나리오 및 체크리스트 (stock.txt, banking.txt)

⚙️ 로더 로직 (lua_config.py)
get_lua_policy(user_state, user_message)를 통해 유저 상태와 **의도(Intent)**에 맞는 프롬프트를 조립합니다.

## 6. 실전 업무 시나리오 (Task Scenarios)
📈 주식 업무 (stock.txt)
Slot-Filling: 종목명, 수량, 주문 방식 누락 시 재질문.

Risk Matching: 사용자 성향(risk_level)보다 위험한 종목 주문 시 경고 필수.

Final Confirm: 주문 실행 전 [종목/수량/금액] 최종 확인 절차.

💰 뱅킹 업무 (banking.txt)
3-Way Match: 받는 사람, 계좌번호, 금액의 정확성 확인.

Security: 보이스피싱 의심 상황 등에 대한 방어적 질문 포함.

Limit Check: 이체 한도 및 잔액 부족 상황 대응.

## 7. R&R (역할 분담)
역할: Frontend
담당 주체: 신인숙
주요 책임 범위: 상태 머신 구현, 입력 검증 UI, 태스크별 UI 모드 대응

역할: Backend
담당 주체: 노현정, 조은아 support
주요 책임 범위: lua_config.py 연동, API 엔드포인트 관리, 데이터 영속 저장

역할: Prompt Eng.
담당 주체: 홍상진
주요 책임 범위: 모든 .txt 기반 시나리오 설계, 페르소나 및 태스크 지침 최적화