# 오픈뱅킹 기반 조회: 은행/증권 계좌 연동으로 간편 가입. 거래내역 통합 조회

## 백엔드 소스 폴더 구조
```
01/
├── logs/               # 로그 디렉토리
├── .env                # 오픈뱅킹 계좌통합조회 api 거래고유번호, 계좌통합조회 리스트번호 정보
├── app_1.py            # 오픈뱅킹 함수 파일
├── openbankcallback.py # choeuna/choeuna1/openbankcallback.py 파일을 테스트를 위해 수정
└── requirements.txt    # 필요한 파이썬 패키지 목록
```

### 사용 방법
from app_1 import get_user_info, get_account_list

