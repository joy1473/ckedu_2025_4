from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import requests
import os
import json
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import threading

# 1. 환경 설정 로드
load_dotenv()
RAW_SERVICE_KEY = os.getenv('PUBLIC_DATA_SERVICE_KEY')
# 서비스키 중복 인코딩 방지를 위해 디코딩 수행
SERVICE_KEY = urllib.parse.unquote(RAW_SERVICE_KEY) if RAW_SERVICE_KEY else ""
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# [핵심] 학습 완료된 커스텀 모델 ID를 우선적으로 가져옵니다.
MODEL_ID = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

client = OpenAI(api_key=OPENAI_API_KEY)

# 공공데이터 API 주소
BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"

app = FastAPI(title="LUA Stable Stock Backend")

# 페르소나 설정 [cite: 2025-12-06]
PERSONA_MATRIX = {
    "CASE_01": {"name": "공격적인 MZ", "style": "짧고 강렬한 트렌디 톤"},
    "CASE_02": {"name": "꼼꼼한 직장인", "style": "데이터 중심 전문 톤"},
    "CASE_03": {"name": "안전제일 은퇴자", "style": "안정성 강조 쉬운 용어"},
    "CASE_04": {"name": "사회초년생 입문자", "style": "교육적 가이드 중심"},
    "CASE_05": {"name": "꿈나무 투자자", "style": "미성년 보호 교육 모드"}
}

def load_lua_prompt():
    if not os.path.exists('prompt.xml'): return "당신은 금융 조력자 LUA입니다."
    with open('prompt.xml', 'r', encoding='utf-8') as f: return f.read()

# [✅ 트리플 로그 시스템] 기능 유지: 학습용(jsonl)과 모니터링용(dashboard)와 통합 로그 API 분리 저장
def save_dual_logs(user_msg, ai_res, case_id, stock_info):
    persona = PERSONA_MATRIX.get(case_id, {})
    lua_rules = load_lua_prompt()

    # 1. OpenAI 추가 학습용 (규격 준수)
    train_entry = {
        "messages": [
            {"role": "system", "content": f"{lua_rules}\n페르소나: {persona.get('name')}"},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": ai_res}
        ]
    }
    with open("pure_train_data.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(train_entry, ensure_ascii=False) + "\n")

    # 2. 대시보드 모니터링용 (웹 화면 출력용)
    monitor_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "case_name": persona.get("name"),
        "stock_name": stock_info.get('itmsNm', 'Unknown'),
        "user_msg": user_msg,
        "ai_res": ai_res
    }
    with open("dashboard_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(monitor_entry, ensure_ascii=False) + "\n")

    # 3. 통합 로그 API (새로 추가)
    def send_to_log_api():
        try:
            log_data = {
                "event": "stock_consultation",
                "user_id": None,
                "note": f"Stock consultation for {stock_info.get('itmsNm', 'Unknown')} with persona {persona.get('name')}",
                "extra": {
                    "timestamp": datetime.now().isoformat(),
                    "stock_name": stock_info.get('itmsNm', 'Unknown'),
                    "stock_price": stock_info.get('clpr', '0'),
                    "stock_change": stock_info.get('vs', '0'),
                    "stock_rate": stock_info.get('fltRt', '0'),
                    "case_id": case_id,
                    "persona_name": persona.get("name"),
                    "user_msg": user_msg,
                    "ai_response": ai_res,
                    "model_used": MODEL_ID
                }
            }
            requests.post("http://localhost:8000/config/log", json=log_data, timeout=5)
        except Exception as e:
            print(f"Log API failed: {e}")

    # 비동기로 로그 API 호출 (응답 지연 방지)
    thread = threading.Thread(target=send_to_log_api)
    thread.daemon = True
    thread.start()

@app.get("/lua/stock")
async def get_stock_persona_info(itmsNm: str, case_id: str = "CASE_02", user_msg: str = ""):
    # API 요청 파라미터 (종목명으로 검색)
    params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": 1,
        "pageNo": 1,
        "resultType": "json",
        "itmsNm": itmsNm
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        raw_data = response.json()
        
        # 데이터 존재 여부 정밀 체크
        body = raw_data.get("response", {}).get("body", {})
        items_list = body.get("items", {}).get("item", [])
        
        if not items_list:
            return {"status": "fail", "message": f"'{itmsNm}'의 현재 시세 정보를 찾을 수 없습니다."}
        
        stock = items_list[0]
        # 필수 시세 정보 추출
        stock_data = {
            "name": stock.get("itmsNm"),
            "price": stock.get("clpr", "0"),    # 종가
            "change": stock.get("vs", "0"),      # 전일대비 대비
            "rate": stock.get("fltRt", "0")    # 등락률
        }
        
        persona = PERSONA_MATRIX.get(case_id, PERSONA_MATRIX["CASE_02"])
        lua_rules = load_lua_prompt()
        
        # [변경 핵심] 커스텀 학습 모델(MODEL_ID)을 사용하여 주인님이 학습시킨 말투로 답변 생성
        completion = client.chat.completions.create(
            model=MODEL_ID, # ft:xxx 모델 적용
            messages=[
                {"role": "system", "content": f"{lua_rules}\n페르소나: {persona['name']}\n지침: {persona['style']}"},
                {"role": "system", "content": f"실시간 데이터: {stock_data['name']} 현재가 {stock_data['price']}원, 등락 {stock_data['rate']}%"},
                {"role": "user", "content": user_msg if user_msg else f"{itmsNm} 주가 알려줘."}
            ],
            temperature=0.7
        )
        final_answer = completion.choices[0].message.content
        
        # 듀얼 로그 저장 (기능 복구)
        save_dual_logs(user_msg, final_answer, case_id, stock)

        return {
            "status": "success",
            "stock_info": stock_data,
            "ai_answer": final_answer,
            "persona_name": persona["name"],
            "used_model": MODEL_ID
        }
        
    except Exception as e:
        print(f"❌ 백엔드 에러: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/monitor", response_class=HTMLResponse)
async def view_monitor():
    logs = []
    if os.path.exists("dashboard_log.jsonl"):
        with open("dashboard_log.jsonl", "r", encoding="utf-8") as f:
            for line in f: 
                try: logs.append(json.loads(line))
                except: continue
    
    # 기능 복구: DataTable을 포함한 화려한 모니터링 대시보드
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LUA 실시간 모니터링</title>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>body {{ font-family: 'Malgun Gothic', sans-serif; }}</style>
    </head>
    <body class="container mt-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>📈 LUA 시세 연동 및 학습 데이터 현황</h2>
            <span class="badge bg-primary">현재 모델: {MODEL_ID}</span>
        </div>
        <table id="logTable" class="table table-striped table-hover">
            <thead class="table-dark">
                <tr><th>일시</th><th>종목</th><th>페르소나</th><th>사용자 질문</th><th>AI 응답</th></tr>
            </thead>
            <tbody>
                {"".join([f"<tr><td>{l['timestamp']}</td><td>{l.get('stock_name', 'Unknown')}</td><td>{l['case_name']}</td><td>{l['user_msg']}</td><td>{l['ai_res']}</td></tr>" for l in logs])}
            </tbody>
        </table>
        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
        <script>$('#logTable').DataTable({{order:[[0,'desc']], pageLength: 10}});</script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    # 외부(Discord 봇)에서 접근 가능하도록 0.0.0.0으로 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)