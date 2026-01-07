# 관리자

## 소스 폴더 구조
```
adm/
├─ logs/                      # 로그 디렉토리
├─ static/
│  ├─ index.js                # JS
│  └─ styles.css              # CSS
├─ templates/                 
│  └─ index.html              # FastAPI 템플릿 HTML
├─ admin_app.py               # 관리자 백엔드 서버
├─ auth.py                    # 관리자 인증 처리(JWT)
├─ db.py                      # DB 연결에 데이터를 처리
└─ requirements.txt           # 필요한 파이썬 패키지 목록
```

## 사용 방법
1. admin_app.py 파일 실행
```bash
cd adm
python admin_app.py
```
2. http://localhost:8000 접속


### 관리자 JWT 인증 추가
