[최종본] 업데이트된 README.md (통 코드)
Markdown

# 🚀 LUA Onboarding & Prompt Management Contract

본 문서는 **LUA 서비스**의 온보딩 상태 머신, 입력 검증 규칙, 그리고 `lua_config.py`를 통한 폴더 기반 프롬프트 관리 체계를 정의합니다.

---

## 1. 온보딩 상태 머신 (Frontend State Machine)

### 🔄 상태 전이도 (States & Transitions)
* **INTRO** → **NAME** → **BIRTHDATE** → **GENDER** → **CONSENT** → **SUITABILITY(Q1~Q4)** → **READY**
* **특이사항:** “이전” 입력 시 1-step back 지원, 새로고침 시 세션 복원(Persistence).

---

## 2. 입력 검증 규칙 (Validation Rules)
* **NAME:** 2~20자 실명 권장 (닉네임/테스트 계정 필터링)
* **BIRTHDATE:** `YYYYMMDD` 형식 (만 19세 기준 `is_minor` 판정)
* **GENDER:** M/F 정규화 저장
* **CONSENT:** 실전 투자 위험 고지 동의 여부 (`true`/`false`)

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
##4. Case/Policy 핵심 규칙
Case Override: is_minor == true 시 무조건 case_id = case_05 (또는 전용 케이스) 강제.

Consent Rule: 미동의 시 READY 진입은 가능하나 실전 거래 기능 차단.

Persona Match: case_id에 따라 lua_config.py에서 시스템 프롬프트 자동 매칭.

##5. 프롬프트 관리 시스템 (Prompt Management)
주인님(기획자)이 파이썬 코드를 수정하지 않고도 AI의 말투를 바꿀 수 있도록 폴더 기반 관리 체계를 사용합니다.

📁 폴더 구조
/intro: 환영 메시지 및 단계별 안내 (welcome.txt 등)

/persona: 케이스별 AI 인격 정의 (mz_aggressive.txt, retiree_safe.txt 등)

/suitability: 투자 성향 결과 문구 (result.txt)

/consent: 동의/거부 관련 안내 문구 (consent_decline.txt)

⚙️ 로직 로더 (lua_config.py)
역할: 위 폴더의 .txt 파일들을 읽어 user_state에 맞는 최적의 시스템 프롬프트를 조립합니다.

함수: get_lua_policy(user_state) 호출 시 {프롬프트, 추천메뉴, UI모드} 반환.

##6. lua_core 연동 계약 (Chat API)
READY 상태 이후의 모든 채팅 요청은 아래 메타 데이터를 포함해야 합니다.

📨 Request Payload
JSON

{
  "user_id": "sjhong76",
  "message": "현재 시장 상황 어때?",
  "user_state": { "case_id": "case_01", "is_minor": false, "risk_level": 1 }
}
##7. R&R (역할 분담)
📱 Frontend 책임
상태 머신 진행 및 UI/UX 렌더링, 입력값 1차 검증.

⚙️ Backend/Orchestrator 책임
lua_config.py를 임포트하여 get_lua_policy() 실행.

산출된 시스템 프롬프트를 LLM(OpenAI 등)에 주입하여 답변 생성.

✍️ Prompt Engineering (홍상진 주인님)
lua_core_prompt 내 각 폴더의 .txt 파일 내용 수정 및 관리.

lua_config.py 내의 페르소나 매칭 로직 관리.


---

### 주인님, 업데이트 방법은 다음과 같습니다:

1.  **파일 수정:** VS Code에서 `D:\AIclass02\lua_core_prompt\README.md` 파일을 열고 위 내용을 전체 붙여넣기 후 저장하세요.
2.  **명령어 실행:** 터미널에서 아래 명령어를 순서대로 입력하여 GitHub에 반영하세요.

```powershell
# 1. 변경된 내용을 저장소 폴더로 복사
robocopy ..\lua_core_prompt .\sjhong76 /mir /xd venv .git

# 2. GitHub 업로드
git add sjhong76
git commit -m "docs: 프롬프트 관리 시스템(lua_config) 내용 README에 추가"
git push origin main
