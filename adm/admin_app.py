# 관리자 : 사용자 성향 변경 / 학습 버튼
from fastapi import FastAPI, Request, HTTPException, Depends, Header, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

from models import SignupRequest, LoginRequest, PasswordChangeRequest, PersonaDataRequest, PersonaRegisterRequest
from db import DbUtils
from auth import Auth

# Logger 설정
logging.basicConfig(
  format='%(asctime)s %(levelname)s:%(message)s',
  level=logging.DEBUG,
  datefmt='%m/%d/%Y %I:%M:%S %p',
)
logger = logging.getLogger()
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)
log_file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), f'logs/admin_app_{datetime.now().strftime(format='%Y%m%d')}.log'))
file_handler = logging.FileHandler(filename=log_file_name)
logger.addHandler(file_handler)

# .env 파일에서 정보를 로드합니다.
load_dotenv()
# 서버 포트
PORT = 8000

CHECK_AUTH = 1
auth = Auth()
dbUtils = DbUtils()

# Lifecycle 관리 (Startup/Shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
  """
  Flask 앱 종료 시
  - DB 접속 해제
  """
  # Startup: 필요한 경우 여기에 작성
  yield
  # Shutdown: DB 접속 해제
  if dbUtils:
    logger.debug("Shutting down: Disconnecting DB")
    dbUtils.disconnect()

app = FastAPI(lifespan=lifespan)
# CORS 설정
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
# 'static'이라는 이름의 디렉토리를 /static 경로로 마운트합니다.
# 실제 폴더명(directory)이 'static'이어야 합니다.
app.mount("/static", StaticFiles(directory="static"), name="static")

# 토큰 검증 의존성 함수
def verify_token(authorization: Optional[str] = Header(None)):
  """
  토큰 검증 후 결과 반환

  Returns:
    message or email
    code
  """
  if CHECK_AUTH == 0:
    return ''
  
  if not authorization or not authorization.startswith("Bearer "):
    raise JSONResponse(status_code=403, content={"error": "Token is missing!"})
  
  try:
    token = authorization.split(" ")[1]
    payload = auth.decode_token(token)
    if payload and "email" in payload:
      return payload["email"]
    else:
      raise JSONResponse(status_code=403, content={"error": "Token is invalid!"})
  except Exception:
    raise JSONResponse(status_code=403, content={"error": "Token is invalid!"})

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
  return templates.TemplateResponse(request=request, name='index.html')

# 관리자 회원가입
@app.post("/signup")
async def signup(data: SignupRequest):
  logger.debug('========= 관리자 회원가입 =========')
  try:
    logger.debug(f'email : "{data.email}"')
    logger.debug(f'password : "{data.password}"')
    logger.debug(f'name : "{data.name}"')

    token_data = dbUtils.set_adm_user_data(data.email, data.password, data.name)
    return token_data
    
  except Exception as e:
    logger.debug(e)
    return JSONResponse(status_code=400, content={"error": str(e)})

# 관리자 로그인
@app.post("/login")
async def login(data: LoginRequest):
  logger.debug('========= 관리자 로그인 =========')
  try:
    logger.debug(f'email : "{data.email}"')
    logger.debug(f'password : "{data.password}"')

    token_data = dbUtils.get_adm_user_login(data.email, data.password)
    return token_data
    
  except Exception as e:
    logger.debug(e)
    return JSONResponse(status_code=400, content={"error": str(e)})

# 관리자 인증 정보
@app.post("/me")
async def me(current_user: str = Depends(verify_token)):
  try:
    admin_user = dbUtils.get_adm_user_data(current_user)
    return admin_user
  except Exception as e:
    logger.debug(e)
    raise JSONResponse(status_code=403, content={"error": str(e)})

# 관리자 암호 변경
@app.post("/change-password")
async def change_password(data: PasswordChangeRequest, current_user: str = Depends(verify_token)):
  logger.debug('========= 관리자 암호 변경 =========')
  try:
    logger.debug(f'*** 현재 관리자 : {current_user}')
    logger.debug(f'current_password : "{data.current_password}"')
    logger.debug(f'new_password : "{data.new_password}"')
    logger.debug(f'confirm_password : "{data.confirm_password}"')
    if not data.current_password or not data.new_password:
      raise JSONResponse(status_code=400, content={"error": "No data provided"})
    if data.new_password != data.confirm_password:
      return JSONResponse(status_code=400, content={"error": "새 암호와 새 암호 확인이 일치하지 않습니다."})

    result = dbUtils.set_adm_user_password(current_user, data.current_password, data.new_password)
    return {'result': 1 if result else 0}
  except Exception as e:
    logger.debug(e)
    raise JSONResponse(status_code=400, content={"error": str(e)})

# 사용자 성향 목록 조회
@app.post("/user/persona/list")
async def get_user_persona_list(current_user: str = Depends(verify_token)):
  persona_list = dbUtils.get_user_persona_list()
  return persona_list

# 사용자 성향 정보 조회
@app.post("/user/persona/data")
async def get_user_persona_data(data: PersonaDataRequest, current_user: str = Depends(verify_token)):
  logger.debug('========= 사용자 성향 정보 조회 =========')
  persona_data = dbUtils.get_user_persona_data(data.id)
  return persona_data

# 사용자 성향 정보 저장
@app.post("/user/persona/register")
async def register_user_persona_data(data: PersonaRegisterRequest, current_user: str = Depends(verify_token)):
  logger.debug('========= 사용자 성향 정보 저장 =========')

  logger.debug(f'*** 현재 관리자 : {current_user}')
  logger.debug('id : ' + data.id)
  logger.debug(data.persona_data)
  #persona_data = json.loads(persona_data_str)
  result = dbUtils.set_user_persona_data(data.id, data.persona_data)
  return {'result': 1 if result else 0}
  
#logger.debug(f'__name__ : {__name__}')
if __name__ == '__main__':
  # 서버 실행
  import uvicorn
  uvicorn.run('admin_app:app', host="0.0.0.0", port=PORT, reload=True)