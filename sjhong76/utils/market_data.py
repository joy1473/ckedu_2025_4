# sjhong76/utils/market_data.py

class MarketDataManager:
    def __init__(self):
        pass

    async def get_global_indices(self):
        """지수 및 환율 데이터 반환"""
        return {
            "KOSPI": {"value": 2580.45, "change": "+0.52%"},
            "KOSDAQ": {"value": 850.12, "change": "-0.10%"},
            "USD_KRW": {"value": 1320.50, "change": "+2.50"}
        }

    async def get_top_news(self):
        """주요 뉴스 3개 반환"""
        return [
            {"id": 1, "title": "반도체 업황 회복세, 수출 지표 역대 최고", "source": "LUA 뉴스"},
            {"id": 2, "title": "금리 동결 전망 우세... 관망세 짙은 시장", "source": "LUA 경제"},
            {"id": 3, "title": "AI 테마주 순환매 지속, 다음 타자는?", "source": "LUA 인사이트"}
        ]