# sjhong76/utils/order_manager.py

class OrderManager:
    def __init__(self):
        # 테스트용 가상 주문 데이터 (미체결 상태)
        self.mock_orders = [
            {"id": "ORD-001", "item": "삼성전자", "code": "005930", "amount": 10, "price": 75000, "type": "매수", "status": "미체결"},
            {"id": "ORD-002", "item": "SK하이닉스", "code": "000660", "amount": 5, "price": 180000, "type": "매수", "status": "부분체결(2주)"}
        ]

    async def get_pending_orders(self):
        """정정/취소가 가능한 미체결 주문 목록을 반환합니다."""
        return [o for o in self.mock_orders if "체결" in o['status'] or "미체결" in o['status']]

    async def get_order_by_id(self, order_id):
        return next((o for o in self.mock_orders if o['id'] == order_id), None)