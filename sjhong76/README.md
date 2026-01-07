# CK Edu 2025 4기 프로젝트

2025년 4기 창의코딩교육(CK Edu) 과정에서 진행하는 프로젝트 저장소입니다.

## 프로젝트 개요
- **교육 과정**: 창의코딩교육 2025년 4기
- **목표**: Python, 웹 개발, AI 등을 활용한 실전 프로젝트 제작
- **주요 기술**: Python, Flask/FastAPI, HTML/CSS/JavaScript, Git & GitHub 등

## 폴더 구조
```
ckedu_2025_4/
├── app/                # 메인 애플리케이션 코드 (예: Flask 또는 FastAPI)
├── static/             # CSS, JS, 이미지 파일
├── templates/          # HTML 템플릿 (Flask 사용 시)
├── data/               # 데이터 파일 (CSV, JSON 등)
├── notebooks/          # Jupyter 노트북 실습 파일
├── requirements.txt    # 필요한 파이썬 패키지 목록
├── README.md           # 이 설명 파일
└── .gitignore          # 업로드 제외 파일 설정
```

## 실행 방법

### 1. 저장소 복제
```bash
git clone https://github.com/joy1473/ckedu_2025_4.git
cd ckedu_2025_4
```

### 2. 가상환경 설정 및 패키지 설치
```bash
python -m venv venv
# Mac : source venv/bin/activate
# Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 애플리케이션 실행
```bash
python app/main.py
```

브라우저에서 `http://127.0.0.1:5000` 접속

## 참여 방법 (팀원용)
1. GitHub 계정으로 로그인
2. 자신의 이름으로 브랜치 생성:
   ```bash
   git checkout -b feature/본인이름-기능명
   ```
3. 작업 후 커밋 & 푸시:
   ```bash
   git add .
   git commit -m "기능 설명"
   git push origin feature/본인이름-기능명
   ```
4. GitHub에서 Pull Request 생성 → 리뷰 후 병합

## 기여자
- joy1473 (리더 / 메인 개발자)
- (팀원 이름 추가 예정)

## 라이선스
교육 목적 프로젝트입니다. 상업적 사용 금지.

---

문의: GitHub Issues 또는 joy1473에게 DM 주세요!
```
