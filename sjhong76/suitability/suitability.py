# suitability.py

def classify_risk(ans: dict) -> tuple[int, str]:
    """
    ans: {"q1":1, "q2":3, "q3":2, "q4":1}  (각 문항의 선택지 번호)
    returns: (risk_level, label)
      risk_level: 1(매우 공격) ~ 5(매우 안정)
    """
    score_map = {
        "q1": {1: 3, 2: 2, 3: 1},
        "q2": {1: 1, 2: 2, 3: 3, 4: 4},
        "q3": {1: 1, 2: 2, 3: 3, 4: 4},
        "q4": {1: 1, 2: 2, 3: 3, 4: 4},
    }
    total = sum(score_map[k][ans[k]] for k in ["q1", "q2", "q3", "q4"])

    if total <= 6:
        return 5, "매우 안정형"
    if total <= 9:
        return 4, "안정형"
    if total <= 12:
        return 3, "중립형"
    if total <= 15:
        return 2, "공격형"
    return 1, "매우 공격형"
