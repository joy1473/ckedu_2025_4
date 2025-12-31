# 오픈뱅킹 기반 조회: 은행/증권 계좌 연동으로 간편 가입. 거래내역 통합 조회

## 백엔드 소스 폴더 구조
```
01/
├── logs/                 # 로그 디렉토리
├── templates/            # Flask 템플릿 HTML
├── .env                  # 오픈뱅킹 계좌통합조회 api 거래고유번호, 계좌통합조회 리스트번호 정보
├── app_1.py              # 오픈뱅킹 함수 파일
├── openbank_user_app.py  # 오픈뱅킹 사용자 인증 테스트 파일
├── openbankcallback.py   # choeuna/choeuna1/openbankcallback.py 파일을 테스트를 위해 수정
└── requirements.txt      # 필요한 파이썬 패키지 목록
```

### 사용 방법
from app_1 import get_user_info, get_account_list

### 오픈뱅킹 사용자 인증 후 계좌 등록
1. openbank_user_app.py 파일 실행
```bash
cd letzrock/01
python openbank_user_app.py
```
2. http://localhost:5050 접속
3. 오픈뱅킹 사용자 인증 시작
4. 새 창에서 휴대폰 인증 후 계좌 정보 등록
5. 등록 결과 확인
**인증**
--> **토큰 각각 발행** : 사용자_토큰_정보.json / 자체인증_이용기관_토큰_정보.json 파일로 저장
--> **사용자정보조회 API 로 등록 정보 확인** : 사용자_정보.json 파일로 저장 (인증을 여러번 실행시 등록한 계좌 모두 조회됨. 최근 1건만 저장)
