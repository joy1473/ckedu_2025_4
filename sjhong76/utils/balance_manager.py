# sjhong76/utils/balance_manager.py

class BalanceManager:
    def __init__(self):
        pass

    async def get_total_balance(self, user_id: str):
        """총자산 요약 데이터를 반환합니다."""
        return {
            "total_asset": 15450000,
            "cash": 2450000,
            "stock_eval": 13000000,
            "total_profit_loss": -1250000,
            "total_return_rate": -7.48
        }

    async def get_top_holdings(self, user_id: str):
        """보유 종목 TOP 5 리스트를 반환합니다."""
        return [
            {"name": "삼성전자", "code": "005930", "amount": 50, "return_rate": -12.5, "current_price": 74500},
            {"name": "SK하이닉스", "code": "000660", "amount": 10, "return_rate": 8.2, "current_price": 185000},
            {"name": "현대차", "code": "005380", "amount": 5, "return_rate": 2.1, "current_price": 245000},
            {"name": "NAVER", "code": "035420", "amount": 20, "return_rate": -5.3, "current_price": 175000},
            {"name": "카카오", "code": "035720", "amount": 30, "return_rate": -15.8, "current_price": 45000}
        ]