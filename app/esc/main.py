# 기존 import에 추가
from elasticsearch import Elasticsearch
import plotly.graph_objects as go
from fastapi.responses import HTMLResponse

# 기존 es 연결 재사용 (이미 코드에 있음)

# 새 엔드포인트: trade_esc_history 모든 데이터 기반 차트
@APP_ESC.get("/api/chart/trade_history", response_class=HTMLResponse)
def get_trade_history_chart():
    # OpenSearch 쿼리: 모든 데이터 가져오기 (size=1000 제한, 대량이면 aggregation 사용)
    body = {
        "query": {"match_all": {}},
        "size": 1000,  # 모든 데이터지만 안전하게 제한
        "sort": [{"timestamp": {"order": "asc"}}]  # timestamp 필드 가정
    }
    res = es.search(index="trade_esc_history", body=body)
    hits = res['hits']['hits']
    
    if not hits:
        return HTMLResponse("<div>데이터가 없습니다.</div>")
    
    # 데이터 추출 (필드 가정: timestamp, rate, ticker 등)
    dates = [hit['_source'].get('timestamp') for hit in hits]
    rates = [hit['_source'].get('rate', 0) for hit in hits]  # 수익률 예시
    tickers = [hit['_source'].get('ticker') for hit in hits]
    
    # Plotly 차트 생성 (라인 차트 예시)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=rates, mode='lines+markers',
        text=tickers,  # 호버 시 ticker 표시
        name='수익률 추이'
    ))
    fig.update_layout(
        title="Trade History: 전체 수익률 추이",
        xaxis_title="날짜",
        yaxis_title="수익률 (%)",
        height=500,
        template="plotly_white"
    )
    
    # HTML로 리턴 (클라이언트에서 embed 가능)
    return HTMLResponse(fig.to_html(full_html=False, include_plotlyjs='cdn'))

# 비슷하게 trade_summary 차트 (예: 요약 바 차트)
@APP_ESC.get("/api/chart/trade_summary", response_class=HTMLResponse)
def get_trade_summary_chart():
    body = {"query": {"match_all": {}}, "size": 1000}
    res = es.search(index="trade_summary", body=body)
    hits = res['hits']['hits']
    
    users = [hit['_source'].get('user_id') for hit in hits]
    total_profits = [hit['_source'].get('total_profit', 0) for hit in hits]  # 필드 가정
    
    fig = go.Figure(data=go.Bar(x=users, y=total_profits))
    fig.update_layout(title="Trade Summary: 사용자별 총 수익")
    
    return HTMLResponse(fig.to_html(full_html=False, include_plotlyjs='cdn'))

# stock_master 차트 (예: 주식 마스터 가격 분포)
@APP_ESC.get("/api/chart/stock_master", response_class=HTMLResponse)
def get_stock_master_chart():
    body = {
        "query": {"match_all": {}},
        "aggs": {
            "price_buckets": {
                "histogram": {"field": "price", "interval": 10000}  # 가격 히스토그램 (필드 가정)
            }
        }
    }
    res = es.search(index="stock_master", body=body)
    
    buckets = res['aggregations']['price_buckets']['buckets']
    keys = [b['key'] for b in buckets]
    counts = [b['doc_count'] for b in buckets]
    
    fig = go.Figure(data=go.Bar(x=keys, y=counts))
    fig.update_layout(title="Stock Master: 가격 분포 히스토그램")
    
    return HTMLResponse(fig.to_html(full_html=False, include_plotlyjs='cdn'))