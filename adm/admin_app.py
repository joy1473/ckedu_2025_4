# 관리자 : 사용자 성향 변경 / 학습 버튼
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
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

CHECK_AUTH = 0
auth = Auth()
dbUtils = DbUtils()

@app.route("/", methods=["GET"])
def index():
  return render_template('index.html')

# 회원가입
@app.route("/signup", methods=["POST"])
def signup():
  logger.debug('========= signup =========')
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
      logger.debug(e)
      return jsonify({"error": 'Error'}), 400
    
  except Exception as e:
    logger.debug(e)
    return jsonify({"error": 'Error'}), 500

# 로그인
@app.route("/login", methods=["POST"])
def login():
  logger.debug('========= login =========')
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
      return jsonify({"error": 'Error'}), 400
    
  except Exception as e:
    logger.debug(e)
    return jsonify({"error": 'Error'}), 500

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

# JWT 보호 API
@app.route("/me", methods=["POST"])
def me():
  message, code = verify_token()

  if code == 200:
    return jsonify({"email": message})
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
  logger.debug('========= get_user_persona_data =========')
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
  logger.debug('========= register_user_persona_data =========')
  message, code = verify_token()

  if code == 200:
    params = request.get_json()
    if not params:
      return jsonify({"error": "No JSON data provided"}), 400
    
    id = params.get('id').strip()
    persona_data = params.get('persona_data')
    logger.debug('id : ' + id)
    logger.debug(persona_data)
    #persona_data = json.loads(persona_data_str)
    result = dbUtils.set_user_persona_data(id, persona_data)
    return jsonify({'result': 1 if result else 0})
  else:
    return jsonify({"error": message}), code

#logger.debug(f'__name__ : {__name__}')
if __name__ == '__main__':
  # 서버 실행
  app.run(host="0.0.0.0", port=PORT, debug=True)