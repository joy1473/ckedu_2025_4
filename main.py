import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from emo.app_emotion import app as emo_app
from cmm.config import app as config_app
#from adm.app_admin import app as admin_app
from aut.app_auth import APP_AUTH
from bye.app_telegram import APP_TELEGRAM
from ctg.app_qa import APP_QA
from esc.app_stock import APP_STOCK

# 메인 FastAPI 앱 생성
app = FastAPI(title="CK Edu 2025 Main API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서브 앱 마운트
app.mount("/emo", emo_app)  # 감정 분석 (초기 페이지)
app.mount("/config", config_app)  # 설정 및 로깅
#app.mount("/admin", admin_app)  # 관리자
app.mount("/auth", APP_AUTH)  # 인증
app.mount("/telegram", APP_TELEGRAM)  # Telegram
app.mount("/qa", APP_QA)  # QA
app.mount("/stock", APP_STOCK)  # 주식

# 루트 리다이렉트: emo의 초기 페이지로
from fastapi.responses import RedirectResponse
@app.get("/")
async def root():
    return RedirectResponse(url="/emo/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)