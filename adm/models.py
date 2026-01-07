from pydantic import BaseModel

# Pydantic 모델 정의 (파라미터 수신용)
class SignupRequest(BaseModel):
  email: str
  password: str
  name: str

class LoginRequest(BaseModel):
  email: str
  password: str

class PasswordChangeRequest(BaseModel):
  current_password: str
  new_password: str
  confirm_password: str

class PersonaDataRequest(BaseModel):
  id: str

class PersonaRegisterRequest(BaseModel):
  id: str
  persona_data: dict # 혹은 적절한 타입