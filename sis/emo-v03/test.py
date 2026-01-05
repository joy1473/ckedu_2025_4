import sys
import os

# ==========================================
# 환경 정보 확인 함수
# ==========================================
# 설명 : 현재 실행 중인 파이썬 경로와 가상 환경 여부를 확인합니다.
# 입력 : 없음
# 출력 : out_env_info (환경 정보 딕셔너리)
# 소스 : System_Environment_Check
def get_env_info():
    v_python_path = sys.executable
    v_is_venv = (sys.prefix != sys.base_prefix)
    
    print("-" * 40)
    print(f"📍 실행 경로: {v_python_path}")
    print(f"📍 가상 환경 여부: {'예(YES)' if v_is_venv else '아니오(NO)'}")
    print("-" * 40)
    
    out_env_info = {
        "path": v_python_path,
        "is_venv": v_is_venv
    }
    return out_env_info

if __name__ == "__main__":
    get_env_info()