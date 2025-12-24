# sjhong76/utils/exception_handler.py

class LUAExceptionHandler:
    def __init__(self):
        # STEP 6: 대표 템플릿 12종 정의
        self.templates = {
            "OUT_OF_HOURS": {
                "msg": "주인님, 지금은 장이 열려있지 않아요. (휴장 또는 시간 외)",
                "buttons": ["예약 주문하기", "시장 요약 보기", "도움말"]
            },
            "SESSION_EXPIRED": {
                "msg": "거래 연결 세션이 만료되었습니다. 다시 연결이 필요해요.",
                "buttons": ["거래 연결하기", "나중에"]
            },
            "NETWORK_DELAY": {
                "msg": "증권사 응답이 조금 늦어지고 있네요. 잠시 후 다시 시도할까요?",
                "buttons": ["다시 시도", "중단"]
            },
            "AMBIGUOUS_ITEM": {
                "msg": "앗, 어떤 종목인지 제가 확실히 알기 어려워요. 아래 후보 중에 있나요?",
                "buttons": ["종목 다시 입력", "인기 종목 보기"]
            },
            "INSUFFICIENT_FUNDS": {
                "msg": "계좌에 주문 가능한 금액이 부족합니다.",
                "buttons": ["입금하기", "수량 변경", "취소"]
            },
            "INSUFFICIENT_HOLDINGS": {
                "msg": "팔 수 있는 주식이 부족합니다.",
                "buttons": ["보유 수량 확인", "수량 변경", "취소"]
            },
            "TICK_SIZE_ERROR": {
                "msg": "입력하신 가격이 호가 단위(틱)와 맞지 않습니다.",
                "buttons": ["가격 변경", "시장가로 변경"]
            },
            "MISSING_PARAMS": {
                "msg": "주문에 필요한 정보(수량/가격 등)가 일부 빠져있어요.",
                "buttons": ["조건 완성하기", "처음부터 다시"]
            },
            "CANT_MODIFY": {
                "msg": "지금은 이 주문을 정정하거나 취소할 수 없는 상태입니다.",
                "buttons": ["체결 내역 확인", "도움말"]
            },
            "ORDER_REJECTED": {
                "msg": "증권사에서 주문을 거부했습니다. (사유: 계좌 상태 확인 필요)",
                "buttons": ["상세 사유 보기", "고객센터 연결"]
            },
            "SYSTEM_CHECK": {
                "msg": "증권사 시스템 점검 시간입니다. (예정 종료: 04:00)",
                "buttons": ["공지 보기", "닫기"]
            },
            "UNKNOWN_ERROR": {
                "msg": "알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                "buttons": ["다시 시도", "문의하기"]
            }
        }

    def get_error_view(self, error_code):
        """에러 코드에 따른 메시지와 버튼 구성을 반환합니다."""
        error_info = self.templates.get(error_code, self.templates["UNKNOWN_ERROR"])
        return error_info["msg"], error_info["buttons"]