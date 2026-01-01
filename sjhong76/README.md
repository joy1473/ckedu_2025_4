# 온보딩 상태 머신 정의서
## LUA Onboarding Contract (1-page)

### 1) 상태 머신 (Frontend State Machine)
**States**
* INTRO → NAME → BIRTHDATE → GENDER → CONSENT → SUITABILITY_Q1 → SUITABILITY_Q2 → SUITABILITY_Q3 → SUITABILITY_Q4 → READY

**Transitions**
* INTRO → NAME: 첫 입력 또는 “시작” 버튼
* NAME → BIRTHDATE: 실명 유효
* BIRTHDATE → GENDER: 생년월일(YYYYMMDD) 유효
* GENDER → CONSENT: 성별(M/F) 유효
* CONSENT → SUITABILITY_Q1: 동의(true)
* CONSENT → READY: 비동의(false) (제한 모드로 READY 진입)
* SUITABILITY_Q1 → Q2 → Q3 → Q4 → READY: 각 문항 선택 유효

**Optional**
* “이전” 입력 시 직전 상태로 1-step back (덮어쓰기 허용)
* 새로고침/재접속: 마지막 상태 복원(세션 저장)

---

### 2) 입력 검증 규칙 (Validation Rules)
* **NAME (실명 필수)**
    * trim 후 길이 2~20 권장
    * 닉네임 의심 규칙(예): 숫자/특수문자 포함 과다, 1글자, test/guest/익명 등
    * 의심 시: “실명으로 다시” 재요청 후 상태 유지
* **BIRTHDATE**
    * 정규식: `^\d{8}$` (예: 19900123)
    * 실제 날짜 유효성 검사
    * is_minor 계산 (정책 기준: 만 19세 미만 등 팀에서 상수화)
* **GENDER (필수)**
    * 입력 허용: 남/여, 남자/여자, M/F 등
    * 내부 정규화: M 또는 F
* **CONSENT (필수)**
    * 값: true/false (UI에선 “동의/비동의” 또는 1/2)
* **SUITABILITY_Q1~Q4**
    * 각 문항 선택지 번호만 허용(1~3 또는 1~4)
    * 유효하지 않으면 재질문

---

### 3) 저장 데이터 모델 (User Profile / Session)
온보딩 도중에도 저장(중단 복원용), 완료 시 확정.

```json
{
  "real_name": "홍길동",
  "birthdate": "19900123",
  "gender": "M",
  "is_minor": false,
  "case_id": "case_04",
  "persona_id": "young_worker",
  "consent_investment_risk": true,
  "suitability_answers": {"q1": 1, "q2": 3, "q3": 2, "q4": 1},
  "risk_score": 9,
  "risk_level": 4,
  "risk_label": "안정형"
}
4) Case/Policy 핵심 규칙 (Backend or Orchestrator)
Case Override

is_minor == true → case_id = case_05 강제 (최상위 우선순위)

성인일 때 case 확정이 아직이면 case_unknown 허용 가능

Consent Rule

consent_investment_risk == false: READY 진입은 허용

단, lua_core에서 “실전 투자/주문/행동 유도” 관련 기능 제한

Suitability Rule

Q1~Q4 완료 시 risk_score/risk_level/risk_label 확정 저장

확정 값은 READY 이후 모든 채팅에 주입

5) Risk Classification Contract (Implementation-agnostic)
Inputs: suitability_answers: {q1, q2, q3, q4} (옵션 번호)

Scoring

Q1 목표: ① 3점, ② 2점, ③ 1점

Q2 기간: ① 1점, ② 2점, ③ 3점, ④ 4점

Q3 손실: ① 1점, ② 2점, ③ 3점, ④ 4점

Q4 경험: ① 1점, ② 2점, ③ 3점, ④ 4점

Mapping (Total Score → risk_level)

4 ~ 6 → 5 (매우 안정형)

7 ~ 9 → 4 (안정형)

10 ~ 12 → 3 (중립형)

13 ~ 15 → 2 (공격형)

16+ → 1 (매우 공격형)

Outputs: risk_score, risk_level(1~5), risk_label

6) lua_core 연동 계약 (Chat API → lua_core)
READY 이후, 모든 채팅 요청은 아래 메타를 포함해야 함.

Chat Request Payload (최소)

JSON

{
  "user_id": "string",
  "message": "string",
  "user_state": {
    "case_id": "case_04",
    "persona_id": "young_worker",
    "is_minor": false,
    "consent_investment_risk": true,
    "risk_level": 4,
    "risk_label": "안정형"
  }
}
lua_core Output

항상 JSON Schema 강제 (summary/explanation/risk_warning/next_actions/meta)

정책 위반/차단 상황에서도 JSON 형태 유지

7) Front 역할 vs Backend 역할 (분업 명확화)
Frontend 책임

상태 머신 진행, 입력 수집/검증(형식 1차)

온보딩 진행 상태 저장/복원

READY 이후 chat API 호출 + 응답 렌더링

Backend/Orchestrator 책임

날짜 유효성/미성년 판정(최종)

case override / consent / risk 계산(최종)

user_state 영속 저장

lua_core 호출 및 결과 검증(JSON Schema)