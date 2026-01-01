# lua_config.py (홍상진 주인님 관리 파일)
import os

# 1. 파일 시스템에서 프롬프트를 읽어오는 공통 함수
def load_prompt_file(folder, filename):
    """
    lua_core_prompt 내의 각 카테고리 폴더에서 .txt 파일을 읽어옵니다.
    """
    # lua_config.py 파일이 있는 현재 위치를 기준으로 경로 설정
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 해당 폴더 내의 파일 경로 생성
    file_path = os.path.join(base_path, folder, filename)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        # 파일이 없을 경우 시스템 중단을 방지하기 위해 경고 문구 반환
        return f"[경고] {filename} 파일이 {folder} 폴더에 없습니다. 내용을 확인해주세요."

# 2. 정책 결정 및 프롬프트 조립 엔진 (lua_policy 핵심 로직)
def get_lua_policy(user_state: dict):
    """
    사용자의 온보딩 데이터(UserState)를 기반으로 
    최종 시스템 프롬프트, UI 모드, 권한 등을 결정하여 반환합니다.
    """
    case_id = user_state.get("case_id", "case_unknown")
    is_minor = user_state.get("is_minor", False)
    consent = user_state.get("consent_investment_risk", False)

    # 기본 설정 (초기값)
    policy = {
        "system_prompt": load_prompt_file("intro", "welcome.txt"),
        "recommended_menu": ["채팅하기"],
        "ui_mode": "standard",
        "is_allowed": True
    }

    # [규칙 1] 미성년자 (최우선순위: persona/kid_learner.txt 활용)
    if is_minor:
        policy["system_prompt"] = load_prompt_file("persona", "kid_learner.txt")
        policy["recommended_menu"] = ["경제 퀴즈", "모의투자 연습"]
        policy["ui_mode"] = "education"
        policy["is_allowed"] = False
        return policy

    # [규칙 2] 케이스별 페르소나 매칭 (persona 폴더 내 txt 파일 활용)
    # 이미지로 주신 폴더 내 파일명과 매칭했습니다.
    persona_files = {
        "case_01": "mz_aggressive.txt",
        "case_02": "office_worker.txt",
        "case_03": "retiree_safe.txt",
        "case_04": "young_worker.txt",
        "case_05": "young_worker.txt" # 필요 시 전용 파일(자산가 등)로 변경 가능
    }

    if case_id in persona_files:
        # 선택된 케이스의 페르소나 파일 내용을 시스템 프롬프트로 로드
        policy["system_prompt"] = load_prompt_file("persona", persona_files[case_id])
    
    # [규칙 3] 투자 성향 결과 및 동의 여부에 따른 문구 결합
    if consent:
        # 투자 성향 진단 결과 문구 추가 (suitability/result.txt)
        policy["system_prompt"] += "\n\n[투자 성향 정보]\n" + load_prompt_file("suitability", "result.txt")
    else:
        # 동의 거부 시 안내 문구 추가 (consent/consent_decline.txt)
        policy["system_prompt"] += "\n\n[알림]\n" + load_prompt_file("consent", "consent_decline.txt")
        policy["is_allowed"] = False

    # [규칙 4] 특정 케이스 UI 모드 변경 (CASE 03: 은퇴자)
    if case_id == "case_03":
        policy["ui_mode"] = "easy_mode"

    return policy