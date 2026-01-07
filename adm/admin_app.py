# 관리자 : 사용자 성향 변경 / 학습 버튼
from flask import Flask, render_template, request, jsonify, abort
from flask_cors import CORS
import atexit
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

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

app = Flask(__name__)
CORS(app)

CHECK_AUTH = 1
auth = Auth()
dbUtils = DbUtils()

@app.route("/", methods=["GET"])
def index():
  return render_template('index.html')

# 관리자 회원가입
@app.route("/signup", methods=["POST"])
def signup():
  logger.debug('========= 관리자 회원가입 =========')
  params = request.get_json()
  if not params:
    return jsonify({"error": "No JSON data provided"}), 400
  
  try:
    email = params.get('email').strip()
    password = params.get('password').strip()
    name = params.get('name').strip()
    logger.debug(f'email : "{email}"')
    logger.debug(f'password : "{password}"')
    logger.debug(f'name : "{name}"')

    try:
      token_data = dbUtils.set_adm_user_data(email, password, name)
      return token_data
    except Exception as e:
      #print(f'$$$$$$$$$$$$$ {type(e.args[0])} $$$$$$$$$$$$$')
      #print(e.args[0])
      logger.debug(e)
      return jsonify({"error": e.args[0]}), 400
    
  except Exception as e:
    logger.debug(e)
    return jsonify({"error": e.args[0]}), 500

# 관리자 로그인
@app.route("/login", methods=["POST"])
def login():
  logger.debug('========= 관리자 로그인 =========')
  params = request.get_json()
  if not params:
    return jsonify({"error": "No JSON data provided"}), 400
  
  try:
    email = params.get('email').strip()
    password = params.get('password').strip()
    logger.debug(f'email : "{email}"')
    logger.debug(f'password : "{password}"')

    try:
      token_data = dbUtils.get_adm_user_login(email, password)
      return token_data
    except Exception as e:
      logger.debug(e)
      return jsonify({"error": e.args[0]}), 400
    
  except Exception as e:
    logger.debug(e)
    return jsonify({"error": e.args[0]}), 500

def verify_token():
  """
  토큰 검증 후 결과 반환

  Returns:
    message or email
    code
  """
  if CHECK_AUTH == 0:
    return '', 200
  
  try:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
      return 'Token is missing!', 403
    
    token = auth_header.split(" ")[1]
    payload = auth.decode_token(token)
    if payload and payload["email"]:
      return payload["email"], 200
    else:
      return 'Token is invalid!', 403
  except Exception:
    return 'Token is invalid!', 403

# 관리자 인증 정보
@app.route("/me", methods=["POST"])
def me():
  message, code = verify_token()

  if code == 200:
    try:
      admin_user = dbUtils.get_adm_user_data(message)
      return jsonify(admin_user)
    except Exception as e:
      logger.debug(e)
      return jsonify({"error": e.args[0]}), 403
  else:
    return jsonify({"error": message}), code

# 관리자 암호 변경
@app.route("/change-passrod", methods=["POST"])
def change_passrod():
  message, code = verify_token()

  if code == 200:
    logger.debug('========= 관리자 암호 변경 =========')
    params = request.get_json()
    if not params:
      return jsonify({"error": "No JSON data provided"}), 400
    
    try:
      logger.debug(f'*** 현재 관리자 : {message}')
      current_password = params.get('current_password').strip()
      new_password = params.get('new_password').strip()
      confirm_password = params.get('confirm_password').strip()
      logger.debug(f'current_password : "{current_password}"')
      logger.debug(f'new_password : "{new_password}"')
      logger.debug(f'confirm_password : "{confirm_password}"')
      if current_password == '' or new_password == '':
        return jsonify({"error": "No data provided"}), 400
      if new_password != confirm_password:
        return jsonify({"error": "새 암호와 새 암호 확인이 일치하지 않습니다."}), 400

      try:
        result = dbUtils.set_adm_user_password(message, current_password, new_password)
        return jsonify({'result': 1 if result else 0})
      except Exception as e:
        logger.debug(e)
        return jsonify({"error": e.args[0]}), 400
      
    except Exception as e:
      logger.debug(e)
      return jsonify({"error": e.args[0]}), 500
  else:
    return jsonify({"error": message}), code

# 사용자 성향 목록 조회
@app.route("/user/persona/list", methods=["POST"])
def get_user_persona_list():
  message, code = verify_token()

  if code == 200:
    persona_list = dbUtils.get_user_persona_list()
    return jsonify(persona_list)
  else:
    return jsonify({"error": message}), code

# 사용자 성향 정보 조회
@app.route("/user/persona/data", methods=["POST"])
def get_user_persona_data():
  logger.debug('========= 사용자 성향 정보 조회 =========')
  message, code = verify_token()

  if code == 200:
    params = request.get_json()
    if not params:
      return jsonify({"error": "No JSON data provided"}), 400
    
    id = params.get('id').strip()

    persona_data = dbUtils.get_user_persona_data(id)
    return persona_data
  else:
    return jsonify({"error": message}), code

# 사용자 성향 정보 저장
@app.route("/user/persona/register", methods=["POST"])
def register_user_persona_data():
  logger.debug('========= 사용자 성향 정보 저장 =========')
  message, code = verify_token()

  if code == 200:
    params = request.get_json()
    if not params:
      return jsonify({"error": "No JSON data provided"}), 400
    
    logger.debug(f'*** 현재 관리자 : {message}')
    id = params.get('id').strip()
    persona_data = params.get('persona_data')
    logger.debug('id : ' + id)
    logger.debug(persona_data)
    #persona_data = json.loads(persona_data_str)
    result = dbUtils.set_user_persona_data(id, persona_data)
    return jsonify({'result': 1 if result else 0})
  else:
    return jsonify({"error": message}), code

@atexit.register
def shutdown():
  """
  Flask 앱 종료 시
  - DB 접속 해제
  """
  dbUtils.disconnect()
  
#logger.debug(f'__name__ : {__name__}')
if __name__ == '__main__':
  # 서버 실행
  app.run(host="0.0.0.0", port=PORT, debug=True)