# lua_config.py (홍상진 주인님 관리 파일)
import os

# 1. 파일 로드 공통 함수
def load_prompt_file(folder, filename):
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, folder, filename)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

# 2. 유저 메시지 의도 판별 로직
def detect_task_intent(message):
    """
    유저의 메시지를 분석하여 주식(stock)인지 뱅킹(banking)인지 판별합니다.
    """
    stock_triggers = ["주식", "매수", "매도", "사줘", "팔아", "코스피", "나스닥", "시세"]
    banking_triggers = ["이체", "송금", "보내줘", "잔액", "계좌", "입금", "출금"]
    
    if any(trigger in message for trigger in stock_triggers):
        return "stock"
    if any(trigger in message for trigger in banking_triggers):
        return "banking"
    return "general"

# 3. 통합 정책 결정 엔진
def get_lua_policy(user_state: dict, user_message: str):
    """
    페르소나 + 업무 지침 + 성향 데이터를 조합하여 최종 시스템 프롬프트를 생성합니다.
    """
    case_id = user_state.get("case_id", "case_unknown")
    is_minor = user_state.get("is_minor", False)
    consent = user_state.get("consent_investment_risk", False)
    risk_label = user_state.get("risk_label", "미지정")

    policy = {
        "system_prompt": "",
        "recommended_menu": ["메인으로"],
        "ui_mode": "standard",
        "is_allowed": True
    }

    # [1단계] 페르소나(말투) 결정
    if is_minor:
        policy["system_prompt"] = load_prompt_file("persona", "kid_learner.txt")
    else:
        persona_map = {
            "case_01": "mz_aggressive.txt",
            "case_02": "office_worker.txt",
            "case_03": "retiree_safe.txt",
            "case_04": "young_worker.txt",
            "case_05": "young_worker.txt"
        }
        policy["system_prompt"] = load_prompt_file("persona", persona_map.get(case_id, "young_worker.txt"))

    # [2단계] 업무 지침(Task) 결합
    intent = detect_task_intent(user_message)
    if intent == "stock":
        task_content = load_prompt_file("task", "stock.txt")
        # 프롬프트 내 변수({risk_label}) 치환
        task_content = task_content.replace("{risk_label}", risk_label)
        policy["system_prompt"] += f"\n\n### [현재 업무 지침: 주식]\n{task_content}"
        policy["recommended_menu"] = ["인기 종목 조회", "나의 자산 보기"]
    
    elif intent == "banking":
        task_content = load_prompt_file("task", "banking.txt")
        policy["system_prompt"] += f"\n\n### [현재 업무 지침: 뱅킹]\n{task_content}"
        policy["recommended_menu"] = ["계좌 이체", "최근 내역"]

    # [3단계] 권한 및 성향 정보 추가
    if consent:
        suitability_res = load_prompt_file("suitability", "result.txt")
        policy["system_prompt"] += f"\n\n[사용자 투자 정보]\n{suitability_res}"
    else:
        consent_decline = load_prompt_file("consent", "consent_decline.txt")
        policy["system_prompt"] += f"\n\n[권한 알림]\n{consent_decline}"
        policy["is_allowed"] = False

    return policy