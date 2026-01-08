from dotenv import load_dotenv
import os
from huggingface_hub import HfApi

load_dotenv()
token = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")
print("토큰 설정 여부:", bool(token))
api = HfApi()
try:
    who = api.whoami(token=token)
    print("whoami 성공: username=", who.get("name") or who.get("email"))
except Exception as e:
    print("whoami 실패:", e)

repo = "monologg/koelectra-base-finetuned-nsmc"
try:
    info = api.model_info(repo, token=token)
    print("model_info: repo exists, private=", getattr(info, 'private', None))
except Exception as e:
    print("model_info 실패:", e)
    print("유사한 monologg 모델 목록을 가져옵니다...")
    try:
        models = api.list_models(author="monologg")
        names = [m.modelId for m in models]
        print("monologg 소유 모델 수:", len(names))
        print(names[:30])
    except Exception as e2:
        print("list_models 실패:", e2)
