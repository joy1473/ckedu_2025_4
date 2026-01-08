import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta 
from elasticsearch import Elasticsearch
from jinja2 import Template
import requests
import sys
from fastapi.templating import Jinja2Templates

# 1. 현재 파일(appEsc.py)의 위치를 기준으로 프로젝트 루트 경로를 계산
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))

# 2. 프로젝트 루트를 파이썬 경로에 추가합니다.
if project_root not in sys.path:
    sys.path.append(project_root)

templates = Jinja2Templates(directory="templates")

# 1. FastAPI 앱 및 경로 설정
APP_ESC = FastAPI()
BASE_PATH = Path(__file__).resolve().parent
DATA_FILE_PATH = BASE_PATH / "trd_04chart_data.json"
MASTER_FILE_PATH = BASE_PATH / "stock_master.json"
OPENBANK_CLIENT_ID = os.getenv("OPENBANK_CLIENT_ID")
OPENBANK_CLIENT_SECRET = os.getenv("OPENBANK_CLIENT_SECRET")
OPEN_BANKING_URL = "https://openapi.openbanking.or.kr"
# 테스트 API
# OPEN_BANKING_URL = "https://testapi.openbanking.or.kr"
OPENBANK_REDIRECT_URI = "http://localhost:5050/auth/callback/"
ACCESS_TOKEN = f"{OPEN_BANKING_URL}/oauth/2.0/token"

# 엘라스틱서치 연결 설정
try:
    es = Elasticsearch(
        ["http://172.26.117.88:9200"],
        headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=7"},
        verify_certs=False,
        request_timeout=3 # 연결 시도 시간 제한 (무한 대기 방지)
    )
    # 실제 연결이 유효한지 핑(ping)으로 확인
    if not es.ping():
        print("⚠️ ES 서버에 응답이 없습니다. 관련 기능을 비활성화합니다.")
        es = None
except Exception as e:
    print(f"❌ ES 연결 중 예외 발생: {e}")
    es = None

# --- [추가] 오픈뱅킹 API 호출 함수 ---
async def fetch_openbank_transactions(user_id: str, start_date: str, end_date: str):
    """
    # 설명 : fetch_openbank_transactions - 오픈뱅킹 API를 통해 투자상품 거래내역을 가져와 DataFrame으로 변환
    # 입력 : user_id - 사용자ID
    #       start_date - 조회 시작일자
    #       end_date - 조회 종료일자
    # 출력 : df - 거래내역 데이터프레임
    # 소스 : 오픈뱅킹 API
    """
    from app.aut.app_auth import get_user_info, get_transaction_list

    # 1. 사용자 정보(토큰 및 핀테크이용번호) 확보
    user_info = get_user_info(user_id)
    access_token = user_info.get("out_org_access_token")
    fintech_use_num = user_info.get("out_fintech_use_num")

    if not access_token:
        print(f"❌ 오류: {user_id}의 Access Token이 없습니다.")
        return pd.DataFrame()

    # 2. 거래를 식별하기 위한 고유한 bank_tran_id 생성 (필수!)
    # 기관코드(예: M202300081) + U + 고유번호 9자리
    bank_tran_id = f"M202300081U{datetime.now().strftime('%H%M%S%f')[:9]}"

    try:
        # 3. 비동기 호출 (await 정상 작동)
        response_data = await get_transaction_list(
            in_user_id=user_id,
            in_bank_tran_id=bank_tran_id,
            in_fintech_use_num=fintech_use_num,
            in_inquiry_type="A",
            in_inquiry_base="D",
            in_from_date=start_date.replace("-", ""),
            in_to_date=end_date.replace("-", "")
        )

        # 이후 데이터 처리 로직... (중략)
        res_list = response_data.get("res_list", [])
        if not res_list: return pd.DataFrame()
        
        df = pd.DataFrame(res_list)
        # 차트와 연동을 위한 컬럼명 통일
        df['date'] = pd.to_datetime(df['tran_date'])
        df['profit'] = pd.to_numeric(df['tran_amt'])
        df['currentPrice'] = pd.to_numeric(df['after_balance_amt'])
        df['name'] = df['print_content']
        df['code'] = "OPENBANK"
        
        return df

    except Exception as e:
        print(f"❌ 오픈뱅킹 호출 중 예외 발생: {e}")
        return pd.DataFrame()
    
def get_stock_name_map():
    """
    # 설명 : get_stock_name_map - 엘라스틱서치의 stock_master 인덱스에서 종목명 맵을 생성
    # 입력 : 없음
    # 출력 : name_map - 종목코드:종목명 딕셔너리
    # 소스 : 엘라스틱서치 stock_master
    """
    """ ES 연결이 없어도 에러 없이 빈 딕셔너리 반환 """
    if es is None:
        print("⚠️ ES 미연결 상태: 종목명 매핑을 건너뜁니다.")
        return {}
    try:
        if not es.indices.exists(index="stock_master"):
            return {}
        res = es.search(index="stock_master", query={"match_all": {}}, size=5000)
        return {hit['_source']['code']: hit['_source']['name'] for hit in res['hits']['hits']}
    except Exception as e:
        print(f"ES stock_master 조회 중 오류: {e}")
        return {}

def get_merged_df_from_json(user_ids, stock_codes, start_date, end_date):
    """
    # 설명 : get_merged_df_from_json - JSON 데이터 로드 및 ES 마스터 정보 병합
    # 입력 : user_ids - 사용자ID리스트
    #       stock_codes - 종목코드리스트
    #       start_date - 시작일자
    #       end_date - 종료일자
    # 출력 : df - 필터링 및 병합된 데이터프레임
    # 소스 : 로컬 JSON 파일 및 엘라스틱서치
    """
    if not os.path.exists(DATA_FILE_PATH):
        return pd.DataFrame()
        
    with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        ledger_data = json.load(f)
    
    df = pd.DataFrame(ledger_data)
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    filtered_user_ids = [uid for uid in user_ids if uid and uid.strip()] if user_ids else []
    if filtered_user_ids:
        df = df[df['user_id'].isin(filtered_user_ids)]
        
    if stock_codes:
        df = df[df['code'].isin(stock_codes)]
    
    if df.empty: return pd.DataFrame()

    name_map = get_stock_name_map()
    df['name'] = df['code'].map(name_map).fillna(df['code'])
    return df.sort_values(["date", "name"])

def get_top_user_data():
    """
    # 설명 : get_top_user_data - 실현손익 + 미실현손익 합계가 가장 높은 유저 추출
    # 입력 : 없음
    # 출력 : top_user_id - 1위 사용자ID, df - 해당 유저의 상세 데이터프레임
    # 소스 : 엘라스틱서치 trade_summary
    """
    """ ES 연결 실패 시 None과 빈 DF 반환 """
    if es is None:
        print("⚠️ ES 미연결 상태: TOP 유저 조회가 불가능합니다.")
        return None, pd.DataFrame()
    
    TARGET_INDEX = "trade_summary"
    try:
        if not es.indices.exists(index=TARGET_INDEX):
            print(f"❌ [DEBUG] 인덱스 '{TARGET_INDEX}'가 ES에 없습니다.")
            return None, pd.DataFrame()
        
        es.indices.refresh(index=TARGET_INDEX)

        # 1. 집계 시도 (필드명 후보군을 순회)
        field_candidates = ["user_id.keyword", "user_id"]
        buckets = []
        
        for field in field_candidates:
            agg_query = {
                "size": 0,
                "aggs": {
                    "top_users": {
                        "terms": {
                            "field": field, 
                            "size": 1, 
                            "order": {"total_valuation_profit": "desc"}
                        },
                        "aggs": {
                            "total_valuation_profit": {
                                "sum": {
                                    "script": {
                                        "source": """
                                            double realized = doc['total_sell_amt'].value - doc['total_buy_amt'].value;
                                            double holdings = doc['total_buy_qty'].value - doc['total_sell_qty'].value;
                                            double unrealized = holdings * doc['current_price'].value;
                                            return realized + unrealized;
                                        """
                                    }
                                }
                            }
                        }
                    }
                }
            }
            try:
                res = es.search(index=TARGET_INDEX, body=agg_query)
                buckets = res.get('aggregations', {}).get('top_users', {}).get('buckets', [])
                if buckets: break # 유저를 찾으면 중단
            except Exception:
                continue # 필드 에러 시 다음 후보로 진행

        if not buckets:
            print("❌ [DEBUG] 유저 집계 실패: 데이터가 비어있거나 필드 계산 오류")
            return None, pd.DataFrame()
            
        top_user_id = buckets[0]['key']
        print(f"✅ [DEBUG] 발견된 TOP 유저: {top_user_id}")
        
        # 2. 상세 데이터 검색 (유연한 쿼리 사용)
        detail_query = {
            "query": {
                "multi_match": {
                    "query": top_user_id,
                    "fields": ["user_id", "user_id.keyword"]
                }
            }
        }
        details = es.search(index=TARGET_INDEX, body=detail_query, size=1000)
        raw_hits = details['hits']['hits']
        
        if not raw_hits:
            print(f"❌ [DEBUG] 유저 {top_user_id}의 상세 데이터를 찾지 못함")
            return top_user_id, pd.DataFrame()

        df = pd.DataFrame([hit['_source'] for hit in raw_hits])
        
        # 3. 데이터 가공 (보유주식 가치 포함)
        df['holdings'] = df['total_buy_qty'] - df['total_sell_qty']
        df['profit'] = (df['total_sell_amt'] - df['total_buy_amt']) + (df['holdings'] * df['current_price'])
        df['profit_rate'] = df.apply(lambda x: round((x['profit'] / x['total_buy_amt'] * 100), 2) if x['total_buy_amt'] > 0 else 0, axis=1)
        
        name_map = get_stock_name_map()
        df['name'] = df['code'].map(name_map).fillna(df['code'])
        df = df.sort_values(by='profit', ascending=False)
        
        return top_user_id, df

    except Exception as e:
        print(f"❌ [DEBUG] 최종 에러: {str(e)}")
        return None, pd.DataFrame()

def get_user_report_data(target_user_id):
    """
    # 설명 : get_user_report_data - 특정 유저의 상세 리포트 데이터 조회
    # 입력 : target_user_id - 조회 대상 사용자ID
    # 출력 : df - 가공된 상세 거래 데이터프레임
    # 소스 : 엘라스틱서치 trade_summary
    """
    """ ES 연결 실패 시 None과 빈 DF 반환 """
    if es is None:
        print("⚠️ ES 미연결 상태: TOP 유저 조회가 불가능합니다.")
        return None, pd.DataFrame()
    
    TARGET_INDEX = "trade_summary"
    try:
        # [중요] 만약 target_user_id가 Request 객체인 경우를 대비해 문자열로 강제 변환
        if not isinstance(target_user_id, str):
            target_user_id = str(target_user_id)

        # 특정 유저의 상세 데이터 검색
        detail_query = {
            "query": {
                "multi_match": {
                    "query": target_user_id,
                    "fields": ["user_id", "user_id.keyword"]
                }
            }
        }
        # body=detail_query 대신 query=detail_query["query"] 사용 권장 (ES 버전에 따라)
        details = es.search(index=TARGET_INDEX, query=detail_query["query"], size=1000)
        raw_hits = details['hits']['hits']
        
        if not raw_hits:
            return pd.DataFrame()

        df = pd.DataFrame([hit['_source'] for hit in raw_hits])
        
        # 데이터 가공
        df['holdings'] = df['total_buy_qty'] - df['total_sell_qty']
        df['profit'] = (df['total_sell_amt'] - df['total_buy_amt']) + (df['holdings'] * df['current_price'])
        df['profit_rate'] = df.apply(lambda x: round((x['profit'] / x['total_buy_amt'] * 100), 2) if x['total_buy_amt'] > 0 else 0, axis=1)
        
        name_map = get_stock_name_map()
        df['name'] = df['code'].map(name_map).fillna(df['code'])
        df = df.sort_values(by='profit', ascending=False)
        
        return df
    except Exception as e:
        print(f"❌ ES 조회 에러 발생: {e}")
        return pd.DataFrame()

def render_report_html(user_id, df, title_label):
    """
    # 설명 : render_report_html - TOP1 유저와 내 리포트에서 공통으로 사용할 HTML 렌더링 함수
    # 입력 : user_id - 사용자ID
    #       df - 거래 데이터프레임
    #       title_label - 리포트 제목
    # 출력 : HTML - 렌더링된 HTML 문자열
    # 소스 : Jinja2 Template
    """
    total_buy_amt = df['total_buy_amt'].sum()
    total_profit = df['profit'].sum()
    avg_profit_rate = round((total_profit / total_buy_amt * 100), 2) if total_buy_amt > 0 else 0
    
    # 수익은 빨강, 손실은 파랑 (한국 주식 시장 기준)
    summary_color = "#ff4d4d" if total_profit >= 0 else "#4d94ff"
    
    chart_df = df[df['profit'] > 0].head(5) # 수익 난 종목만 차트에 표시
    chart_data = {
        "labels": chart_df['name'].tolist(),
        "values": chart_df['profit'].tolist()
    }

    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ title_label }}</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { background-color: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 20px; }
            .container { max-width: 1000px; margin: auto; background: #1e293b; padding: 30px; border-radius: 15px; border: 1px solid #334155; }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 15px; margin-bottom: 25px; }
            .title { font-size: 24px; font-weight: bold; color: #f1f5f9; }
            .user-badge { background: #334155; color: #94a3b8; padding: 5px 15px; border-radius: 20px; font-size: 14px; }
            
            .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: #0f172a; padding: 20px; border-radius: 12px; border: 1px solid #334155; text-align: center; }
            .stat-label { font-size: 14px; color: #94a3b8; margin-bottom: 8px; }
            .stat-value { font-size: 22px; font-weight: bold; }
            
            #profitChart { background: transparent; margin-bottom: 30px; }
            
            /* --- 테이블 디자인 수정 (이미지 1번 스타일 적용) --- */
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            
            /* 헤더: 배경색과 글자색, 중앙 정렬 및 하단 선 강조 */
            th { 
                background: #334155; 
                color: #cbd5e1; 
                padding: 14px 12px; 
                text-align: center !important; 
                border-bottom: 2px solid #475569; /* 헤더 아래 선을 더 두껍게 */
                font-size: 14px;
            }
            
            /* 데이터 셀: 가로 선을 더 명확하게 변경 */
            td { 
                padding: 14px 12px; 
                border-bottom: 1px solid #334155; /* 가로 구분선 */
                color: #e2e8f0; 
                font-size: 14px;
            }

            /* 첫 번째 칸(종목명) 왼쪽 정렬 */
            .display-table td:nth-child(1) {
                text-align: left;
                padding-left: 20px;
            }

            /* 숫자 데이터 오른쪽 정렬 및 여백 */
            .display-table td:nth-child(2),
            .display-table td:nth-child(3),
            .display-table td:nth-child(4),
            .display-table td:nth-child(5) {
                text-align: right !important;
                padding-right: 25px; 
                font-variant-numeric: tabular-nums;
            }

            /* 마지막 행은 선을 없애서 깔끔하게 마무리 */
            tr:last-child td {
                border-bottom: none;
            }
            /* -------------------------------------- */

            .pos { color: #ff4d4d; }
            .neg { color: #4d94ff; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="title">{{ title_label }}</div>
                <div class="user-badge">Investor: {{ user_id }}</div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">총 투자금액</div>
                    <div class="stat-value">{{ "{:,}".format(total_buy_amt|int) }}원</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">총 손익 (평가포함)</div>
                    <div class="stat-value" style="color: {{ summary_color }}">{{ "{:+,}".format(total_profit|int) }}원</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">누적 수익률</div>
                    <div class="stat-value" style="color: {{ summary_color }}">{{ avg_profit_rate }}%</div>
                </div>
            </div>

            <div id="profitChart"></div>

            <table class="display-table">
                <thead>
                    <tr>
                        <th>종목명</th>
                        <th>보유수량</th>
                        <th>현재가</th>
                        <th>실현+평가손익</th>
                        <th>수익률</th>
                    </tr>
                </thead>
                <tbody>
                    {% for _, row in df.iterrows() %}
                    <tr>
                        <td>{{ row['name'] }}</td>
                        <td>{{ "{:,}".format(row['holdings']|int) }}</td>
                        <td>{{ "{:,}".format(row['current_price']|int) }}</td>
                        <td class="{{ 'pos' if row['profit'] >= 0 else 'neg' }}">
                            {{ "{:+,}".format(row['profit']|int) }}
                        </td>
                        <td class="{{ 'pos' if row['profit_rate'] >= 0 else 'neg' }}">
                            {{ row['profit_rate'] }}%
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <script>
            var data = [{
                values: {{ chart_data['values'] | tojson }},
                labels: {{ chart_data['labels'] | tojson }},
                type: 'pie',
                hole: .4,
                marker: { colors: ['#ff4d4d', '#ff9f43', '#feca57', '#5f27cd', '#54a0ff'] }
            }];
            var layout = {
                title: { text: '수익 기여 종목 TOP 5', font: {color: '#f8fafc'} },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#94a3b8' },
                showlegend: true
            };
            Plotly.newPlot('profitChart', data, layout);
        </script>
    </body>
    </html>
    """
    return Template(template_str).render(
        user_id=user_id, df=df, title_label=title_label,
        total_buy_amt=total_buy_amt, total_profit=total_profit,
        avg_profit_rate=avg_profit_rate, summary_color=summary_color,
        chart_data=chart_data
    )
  
@APP_ESC.get("/apiEsc/get_chartHtml", response_class=HTMLResponse)
async def get_chart_html(
    in_chartType: str = Query(..., description="차트 타입 (01~04)"),
    in_userIds: Optional[List[str]] = Query(None), 
    in_stockCodes: Optional[List[str]] = Query(None),
    in_startDate: Optional[str] = Query(None),
    in_endDate: Optional[str] = Query(None)
):
    """
    # 설명 : get_chartHtml - 차트 구현
    # 입력 : in_chartType - 차트유형코드 # VOL_CHART, DIST_CHART, COMPLETED_CHART, UNIT_CHART
    #       in_userIds - 사용자ID리스트
    #       in_stockCodes - 종목코드리스트
    #       in_startDate - 시작일자
    #       in_endDate - 종료일자
    # 출력 : user - json 정보
    # 소스 : 몽고DB mock_trading_db.users
    """
    from app.aut.app_auth import get_user_info, get_transaction_list

    # 1. 날짜 설정
    target_end = in_endDate if in_endDate else datetime.now().strftime('%Y-%m-%d')
    target_start = in_startDate if in_startDate else (datetime.now() - relativedelta(months=6)).strftime('%Y-%m-%d')
    
    # 리스트가 비어있을 경우 기본값 설정
    active_user_ids = [uid for uid in in_userIds if uid and uid.strip()] if in_userIds else ["user1"]
    main_user_id = active_user_ids[0]

    # 2. 사용자 정보에서 핀테크이용번호 확인
    user_info = get_user_info(main_user_id)
    fintech_use_num = user_info.get("out_fintech_use_num")
    print('----------fintech_use_num')
    print(fintech_use_num)

    # 2. 데이터 확보 (분기 로직 수정)
    if fintech_use_num:
        # [중요] fetch_openbank_transactions가 async이므로 반드시 await 사용
        # 첫 번째 유저 아이디를 기준으로 호출 (또는 시스템 기본값)
        user_id = active_user_ids[0] if active_user_ids else "user_0007" 
        df = await fetch_openbank_transactions(user_id, target_start, target_end)
        source_label = "오픈뱅킹 실거래"
    else:
        # 모의투자 데이터 (JSON/ES 기반)
        df = get_merged_df_from_json(active_user_ids, in_stockCodes, target_start, target_end)
        source_label = "모의투자"

    # 3. 데이터 유무 확인 (데이터가 비어있으면 조기 리턴)
    if df is None or df.empty:
        return f"""
        <div style='color:white; background:#0f172a; padding:50px; text-align:center; font-family:sans-serif;'>
            <h3>{main_user_id}님의 {source_label} 데이터가 없습니다.</h3>
            <p>조회 기간: {target_start} ~ {target_end}</p>
        </div>
        """

    # 4. 공통 데이터 가공
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['date', 'name'])

    # --- 레이아웃 및 차트 생성 로직 (기존과 동일하지만 가독성 위해 유지) ---
    def apply_layout(fig, title, y_label="값"):
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            template="plotly_dark", paper_bgcolor='#0f172a', plot_bgcolor='#0f172a',
            height=450, margin=dict(t=80, b=40, l=60, r=20),
            legend=dict(title_text="종목명", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        # fig.update_xaxes(title_text="거래일자", tickformat="%Y-%m-%d")
        # Y축 한글 설정
        fig.update_yaxes(title_text=y_label)
    kor_labels = {"date": "거래일자", "name": "종목명", "quantity": "체결수량", "profit": "실현손익", "profit_rate": "수익률(%)", "cum_profit": "누적수익"}
    fig = go.Figure()

    # 차트 타입별 생성
    if in_chartType == "01":
        fig = px.bar(df, x="date", y="quantity", color="name", barmode="group", labels=kor_labels)
        fig.update_xaxes(title_text="거래일자")
        apply_layout(fig, f"📊 [{source_label}] 종목별 체결수량 추이", "체결수량")
    elif in_chartType == "02":
        # 현재가와 매수가가 있을 경우 수익률 계산 (없으면 0 처리)
        if 'buyPrice' in df.columns and 'currentPrice' in df.columns:
            df['profit_rate'] = df.apply(lambda x: round(((x['currentPrice'] - x['buyPrice']) / x['buyPrice'] * 100), 2) if x.get('buyPrice', 0) > 0 else 0, axis=1)
        elif 'profit' in df.columns:
            # 매수가가 없을 경우 실현손익 기반의 가상 수익률 (예시)
            df['profit_rate'] = df['profit'] / 1000  # 비중 확인용
        else:
            df['profit_rate'] = 0

        # 2. 히스토그램 생성 (데이터가 적을 경우를 대비해 nbins 제거 또는 x축 범위 고정)
        fig = px.histogram(df, x="profit_rate", nbins=20, color_discrete_sequence=['#10b981'], labels=kor_labels, range_x=[-10, 10])
        
        fig.update_xaxes(title_text="수익률 (%)", ticksuffix="%")
        # 데이터가 1개일 때 깨짐 방지를 위해 범위 고정 (선택사항)
        if len(df) == 1:
            fig.update_xaxes(range=[df['profit_rate'].iloc[0]-5, df['profit_rate'].iloc[0]+5])

        # 막대 테두리를 추가하여 구분감 제공
        fig.update_traces(marker_line_color='white', marker_line_width=1)
        apply_layout(fig, f"📈 [{source_label}] 수익률 분포도", "종목 수 (건)")
    elif in_chartType == "03":
        df['cum_profit'] = df.groupby('name')['profit'].cumsum()
        fig = px.line(df, x="date", y="cum_profit", color="name", markers=True, labels=kor_labels)
        apply_layout(fig, f"💰 [{source_label}] 종목별 누적 성과 추이", "누적 수익 (원)")
    elif in_chartType == "04":
        # 자산 구성 차트
        df['total_asset'] = df['quantity'] * df.get('currentPrice', 0)
        df['equity'] = (df['total_asset'] * 0.4).round(0)
        df['misu'] = df['total_asset'] - df['equity']
        df['margin_ratio'] = (df['equity'] / df['total_asset'] * 100).fillna(0).round(2)
        # fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.2, subplot_titles=("자산 구성 (자기자본/미수금)", "담보유지비율 (%)"))
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, 
                            subplot_titles=("자산 구성 (자기자본/미수금)", "담보유지비율 (%)"))
        fig.add_trace(go.Scatter(x=df['date'], y=df['equity'], name='자기자본', stackgroup='one', mode='lines+markers'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['misu'], name='미수금', stackgroup='one', mode='lines+markers'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['margin_ratio'], name='담보비율', line=dict(color='#ef4444', width=3), mode='lines+markers'), row=2, col=1)
        
        apply_layout(fig, f"🛡️ [{source_label}] 자산 구성 및 담보비율")

        fig.update_xaxes(title_text="거래일자", row=2, col=1)
        fig.update_yaxes(title_text="자산 가치 (원)", row=1, col=1)
        fig.update_yaxes(title_text="비율 (%)", row=2, col=1)

    chart_div = plot(fig, output_type='div', include_plotlyjs='cdn')
    
    # 5. 하단 테이블 생성
    df_table = df.copy()
    df_table['date_str'] = df_table['date'].dt.strftime('%Y-%m-%d')
    # 필요한 컬럼만 추출 (오픈뱅킹 데이터셋에 맞게 조정 필요할 수 있음)
    cols = ['date_str', 'name', 'quantity', 'profit']
    df_table = df_table[cols]
    df_table.columns = ['거래일자', '종목명', '체결수량', '실현손익']

    def format_cells(row):
        qty = f"{int(row['체결수량']):,}"
        val = int(row['실현손익'])
        color = "#ff4d4d" if val > 0 else "#4d94ff" if val < 0 else "#ffffff"
        profit = f'<span style="color:{color}; font-weight:bold;">{val:+,}</span>'
        return pd.Series([qty, profit])

    df_table[['체결수량', '실현손익']] = df_table.apply(format_cells, axis=1)
    table_html = df_table.to_html(classes="display-table", index=False, escape=False)

    return f"""
    <html>
        <head>
            <style>
                body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 10px; margin: 0; }}
                #chart-area {{ background: #0f172a; padding-bottom: 10px; }}
                #table-wrapper {{ background: #1e293b; border-radius: 8px; border: 1px solid #334155; margin-top: 10px; overflow: hidden; }}
                .display-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
                .display-table th {{ background: #334155; padding: 12px; text-align: center; color: #cbd5e1; border-bottom: 2px solid #475569; }}
                .display-table td {{ padding: 12px; text-align: center; border-bottom: 1px solid #334155; }}
                .display-table td:nth-child(3), .display-table td:nth-child(4) {{ text-align: right; padding-right: 30px; }}
                tr:hover {{ background: #2d3748; }}
            </style>
        </head>
        <body>
            <div id="chart-area">{chart_div}</div>
            <div id="table-wrapper">{table_html}</div>
        </body>
    </html>
    """

@APP_ESC.get("/apiEsc/get_topReport", response_class=HTMLResponse)
async def get_top_report():
    """
    # 설명 : get_top_report - 수익률 TOP 1 투자자의 상세 리포트 조회
    # 입력 : 없음
    # 출력 : HTML - 렌더링된 리포트 페이지
    # 소스 : 엘라스틱서치 trade_summary
    """
    top_user_id, _ = get_top_user_data()
    if not top_user_id:
        return HTMLResponse(content="데이터를 찾을 수 없습니다.", status_code=404)
        
    df = get_user_report_data(top_user_id)
    return render_report_html(top_user_id, df, "수익률 TOP 1 투자자 리포트")

# 2. 새로운 나의 리포트
@APP_ESC.get("/apiEsc/get_myReport", response_class=HTMLResponse)
async def get_my_report(in_userId: Optional[str] = Query("user_0007")): 
    """
    # 설명 : get_my_report - 로그인한 나의 상세 투자 리포트 조회
    # 입력 : in_userId - 사용자ID (기본값: user_0007)
    # 출력 : HTML - 렌더링된 리포트 페이지
    # 소스 : 엘라스틱서치 trade_summary
    """
    # 1. 데이터 가져오기
    df = get_user_report_data(in_userId)
    
    if df.empty:
        # FastAPI에서 에러 메시지는 HTMLResponse 객체로 감싸서 반환해야 함
        return HTMLResponse(
            content=f"<h3>{in_userId}님의 데이터가 없습니다.</h3>", 
            status_code=404
        )
        
    # 2. 공통 렌더링 함수 호출
    return render_report_html(in_userId, df, "📊 나의 모의투자 리포트")