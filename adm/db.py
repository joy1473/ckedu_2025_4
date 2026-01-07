from pymongo import MongoClient, errors
from pymongo.monitoring import ServerHeartbeatListener
import os
from dotenv import load_dotenv
from bson import ObjectId
import logging
from datetime import datetime

from auth import Auth

# Logger 설정
logging.basicConfig(
  format='%(asctime)s %(levelname)s:%(message)s',
  level=logging.DEBUG,
  datefmt='%m/%d/%Y %I:%M:%S %p',
)
logger = logging.getLogger()
#stream_handler = logging.StreamHandler()
#logger.addHandler(stream_handler)
log_file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), f'logs/admin_db_{datetime.now().strftime(format='%Y%m%d')}.log'))
file_handler = logging.FileHandler(filename=log_file_name)
logger.addHandler(file_handler)
logging.getLogger("pymongo.server_monitoring").setLevel(logging.WARNING)

class DbUtils:
  """
  DB 연결 후 관리자 정보 관리, 사용자 성향 관리 등의 업무를 처리하는 클래스
  """
  def __init__(self):
    """
    초기화
    """
    # .env 파일에서 정보를 로드합니다.
    load_dotenv()
    MONGO_URL = os.getenv("ADM_MONGO_URL")
    self.is_connected = False
    try:
      # DB 접속 클라이언트 생성
      self.client = MongoClient(
        MONGO_URL,
        serverSelectionTimeoutMS=3000
      )
      db = self.client["mock_trading_db"]
      # 사용자 정보
      #self.user_collection = db["users"]
      # 사용자 성향 정보
      self.user_persona_collection = db["auth_states"]
      # 관리자 정보
      self.adm_user_collection = db["adm_users"]
      # 인증 유틸 객체
      self.auth = Auth()
      self.is_connected = True
    except errors.ServerSelectionTimeoutError as e:
      logger.debug("MongoDB 연결 실패:", e)
    except Exception as e:
      logger.debug(e)
  
  def disconnect(self):
    try:
      if self.client:
        self.client.close()
      self.is_connected = False
    except Exception as e:
      logger.debug(e)

  def get_adm_user_data(self, in_email: str):
    """
    관리자 정보 조회

    Args:
      in_email (str): 이메일
      
    Returns:
      (dict): 관리자 정보
        - email (str): 이메일
        - name (str): 이름

    Raises:
      Exception
    """
    if not self.is_connected:
      raise Exception("DB 접속 필요")
    
    db_user = self.adm_user_collection.find_one({"email": in_email})
    if not db_user:
      raise Exception("해당 이메일의 관리자 정보가 없습니다.")

    return {"email": db_user['email'], "name": db_user['name']}

  def set_adm_user_data(self, in_email: str, in_password: str, in_name: str):
    """
    관리자 정보 저장
      in_email (str): 이메일
      in_password (str): 암호
      in_name (str): 이름

    Args:

    Returns:
      (dict): 토큰 정보
        - token (str): 토큰
        - token_type (str): 토큰 타입

    Raises:
      Exception
    """
    if not self.is_connected:
      raise Exception("DB 접속 필요")
    
    db_user = self.adm_user_collection.find_one({"email": in_email})
    if db_user:
      raise Exception("해당 이메일의 관리자 정보가 이미 등록되어 있습니다.")

    user_data = {
      "email": in_email,
      "password": self.auth.hash_password(in_password),
      "name": in_name
    }
    res = self.adm_user_collection.insert_one(user_data)
    if res.inserted_id:
      token = self.auth.create_token(in_email)
      logger.debug(f'token : {token}')
      if token:
        return {"token": token, "token_type": "bearer"}
      else:
        logger.debug('토큰 생성 중 오류 : rollback')
        self.adm_user_collection.delete_one({"email": in_email})
    else:
      raise Exception("관리자 등록에 실패헸습니다.")

  def get_adm_user_login(self, in_email: str, in_password: str):
    """
    관리자 로그인

    Args:
      in_email (str): 이메일
      in_password (str): 암호

    Returns:
      (dict): 토큰 정보
        - token (str): 토큰
        - token_type (str): 토큰 타입

    Raises:
      Exception
    """
    if not self.is_connected:
      raise Exception("DB 접속 필요")
    
    #print(f"++++++++++++++++++ email:{in_email} ++++++++++++++++++")
    logger.debug(f'email : "{in_email}"')
    logger.debug(f'password : "{in_password}"')
    logger.debug('.......... 해당 이메일의 데이터가 있는지 확인 ..........')
    db_user = self.adm_user_collection.find_one({"email": in_email})
    logger.debug(db_user)
    if not db_user:
      raise Exception("해당 이메일의 관리자 정보가 없습니다.")
    if not self.auth.verify_password(in_password, db_user["password"]):
      raise Exception("암호가 다릅니다.")

    token = self.auth.create_token(in_email)
    return {"token": token, "token_type": "bearer"}

  def set_adm_user_password(self, in_email: str, in_current_password: str, in_new_password: str):
    """
    관리자 암호 변경
      in_email (str): 이메일
      in_current_password (str): 현재 암호
      in_new_password (str): 새 암호

    Args:

    Returns:
      (bool): 암호 변경 여부

    Raises:
      Exception
    """
    if not self.is_connected:
      raise Exception("DB 접속 필요")
    
    logger.debug(f'current_password : "{in_current_password}"')
    logger.debug(f'new_password : "{in_new_password}"')
    logger.debug('.......... 해당 이메일의 데이터가 있는지 확인 ..........')
    db_user = self.adm_user_collection.find_one({"email": in_email})
    logger.debug(db_user)
    if not db_user:
      raise Exception("해당 이메일의 관리자 정보가 없습니다.")
    if not self.auth.verify_password(in_current_password, db_user["password"]):
      raise Exception("현재 암호가 다릅니다.")

    user_data = {
      "password": self.auth.hash_password(in_new_password)
    }
    res = self.adm_user_collection.update_one(
      {"_id": db_user["_id"]},
      {
        "$set": user_data,
        #"$currentDate": {"updated_at": True}
      }
    )
    return res.matched_count == 1

  def get_user_persona_list(self):
    """
    사용자 성향 목록 조회

    Returns:
      (list): 사용자 성향 목록

    Raises:
      Exception
    """
    cursor = self.user_persona_collection.find()
    items = cursor.to_list(length=None)
    
    for item in items:
      item["_id"] = str(item["_id"])
    return items

  def get_user_persona_data(self, in_id: str):
    """
    사용자 성향 정보 조회

    Args:
      in_id (str): ObjectId 값

    Returns:
      (dict): 사용자 성향 정보

    Raises:
      Exception
    """
    _id = ObjectId(in_id)
    item = self.user_persona_collection.find_one({"_id": _id})
    if not item:
      raise Exception("Invalid ID")
    
    item["_id"] = str(item["_id"])
    return item

  def set_user_persona_data(self, in_id: str, in_persona_data: dict):
    """
    사용자 성향 정보 저장

    Args:
      in_id (str): ObjectId 값
      in_persona_data (dict): 성향 정보
        - investment_grade (str)
        - risk_tolerance (str)
        - investment_style (str)
        - preferred_sectors (str)
        - holding_period (str)
        - typical_behavior (str)
        - favorite_patterns (str)
        - specific_stocks (str)
        - analysis_tendency (str)
        - special_note (str)
        - lua_branch (str)

    Returns:
      (bool): 저장 결과

    Raises:
      Exception
    """
    if not self.is_connected:
      raise Exception("DB 접속 필요")
    
    _id = ObjectId(in_id)
    filter_data = {"_id": _id}
    item = self.user_persona_collection.find_one(filter_data)
    logger.debug('.......... 해당 ID의 데이터가 있는지 확인 ..........')
    logger.debug(item)
    if not item:
      raise Exception("Invalid ID")


    logger.debug(f'preferred_sectors : {in_persona_data['preferred_sectors']}')
    logger.debug(f'favorite_patterns : {in_persona_data['favorite_patterns']}')
    logger.debug(f'specific_stocks : {in_persona_data['specific_stocks']}')
    
    preferred_sectors = []
    if in_persona_data['preferred_sectors'] and in_persona_data['preferred_sectors'].count(',') > 0:
      preferred_sectors = in_persona_data['preferred_sectors'].split(',')
    elif in_persona_data['preferred_sectors']:
      preferred_sectors.append(in_persona_data['preferred_sectors'])
    
    favorite_patterns = []
    if in_persona_data['favorite_patterns'] and in_persona_data['favorite_patterns'].count(',') > 0:
      favorite_patterns = in_persona_data['favorite_patterns'].split(',')
    elif in_persona_data['favorite_patterns']:
      favorite_patterns.append(in_persona_data['favorite_patterns'])

    specific_stocks = []
    if in_persona_data['specific_stocks'] and in_persona_data['specific_stocks'].count(',') > 0:
      specific_stocks = in_persona_data['specific_stocks'].split(',')
    elif in_persona_data['specific_stocks']:
      specific_stocks.append(in_persona_data['specific_stocks'])
    
    persona_data = {
      "investment_grade": in_persona_data['investment_grade'],
      "risk_tolerance": in_persona_data['risk_tolerance'],
      "investment_style": in_persona_data['investment_style'],
      "preferred_sectors": preferred_sectors,
      "holding_period": in_persona_data['holding_period'],
      "typical_behavior": in_persona_data['typical_behavior'],
      "favorite_patterns": favorite_patterns,
      "specific_stocks": specific_stocks,
      "analysis_tendency": in_persona_data['analysis_tendency'],
      "special_note": in_persona_data['special_note'],
      "lua_branch": in_persona_data['lua_branch']
    }
    res = self.user_persona_collection.update_one(
        filter_data,
        {
            "$set": persona_data,
            #"$currentDate": {"updated_at": True}
        }
    )
    return res.matched_count == 1
