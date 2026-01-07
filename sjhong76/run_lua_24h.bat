@echo off
:loop
echo 🚀 LUA 시스템 가동 중... (%date% %time%)
:: 가상환경 활성화 (필요시 경로 수정)
call venv\Scripts\activate
:: 백엔드와 봇을 동시에 실행 (독립된 창으로 띄움)
start /b python api_server.py
python main.py
echo ⚠️ 시스템 종료 감지. 5초 후 재시작합니다.
timeout /t 5
goto loop