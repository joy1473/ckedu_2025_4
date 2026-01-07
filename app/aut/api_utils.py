from datetime import datetime
import secrets
import string

def format_datetime(format: str = None):
  """
  현재 날짜를 형식에 맞춰 문자로 반환

  Args:
    format (str): 날짜 형식

  Returns:
    strftime (str): 날짜
  """
  if not format:
    format = '%Y%m%d%H%M%S'
  now = datetime.now()
  return now.strftime(format=format)

def generate_secure_key(length=12):
  """
  안전한 랜덤 키 생성 함수 (문자 포함)

  Args:
    length (nt): 문자 길이

  Returns:
    random_key (str): 랜덤 키
  """
  # 랜덤 문자열 생성 (문자, 숫자, 특수문자 포함)
  alphabet = string.ascii_letters + string.digits
  random_key = ''.join(secrets.choice(alphabet) for i in range(length))
  return random_key