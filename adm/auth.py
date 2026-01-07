from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

class Auth:
  def __init__(self):
    # .env 파일에서 정보를 로드합니다.
    load_dotenv()
    self.SECRET_KEY = os.getenv("ADM_SECRET_KEY")
    self.ALGORITHM = "HS256"
    # 토큰 만료시간을 지정합니다.
    self.ACCESS_TOKEN_EXPIRE_MINUTES = 12 * 60
    self.ACCESS_TOKEN_EXPIRE_MINUTES = 1
    self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

  def hash_password(self, password: str):
    return self.pwd_context.hash(password)

  def verify_password(self, password, hashed):
    return self.pwd_context.verify(password, hashed)

  def create_token(self, email: str):
    to_encode = {"sub": email}
    expire = datetime.now() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

  def decode_token(self, token: str):
    try:
      payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
      return {"email": payload["sub"]}
    except JWTError:
      raise Exception("Invalid token")