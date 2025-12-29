import os
from dotenv import load_dotenv
from pymongo import MongoClient
import requests
import time
from datetime import datetime

# .env 로드
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_LINK = os.getenv('TELEGRAM_BOT_LINK')

if not all([MONGO_URI, TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_LINK]):
    print("❌ .env에 MONGO_URI, TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_LINK를 설정하세요!")
    exit()

# Telegram API 기본 URL
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# 알려진 CHAT_ID 저장 (처음엔 빈 set)
known_chat_ids = set()

# 마지막 처리한 업데이트 ID
last_update_id = 0

def get_updates():
    """새로운 메시지 받기 (Long Polling)"""
    global last_update_id
    url = f"{BASE_URL}/getUpdates"
    params = {
        "offset": last_update_id + 1,
        "timeout": 30  # 30초 대기
    }
    try:
        response = requests.get(url, params=params, timeout=35)
        if response.status_code == 200:
            data = response.json()
            if data["ok"]:
                return data["result"]
    except Exception as e:
        print(f"업데이트 수신 오류: {e}")
    return []

def send_alarm_to_all(message):
    """모든 알려진 사용자에게 알람 보내기"""
    if not known_chat_ids:
        print("⚠️ 아직 메시지를 보낸 사용자가 없어요. 봇에 먼저 말 걸어주세요!")
        return

    full_message = (
        f"{message}\n\n"
        f"🔗 봇 바로가기: {TELEGRAM_BOT_LINK}\n"
        f"더 많은 알람 받으려면 클릭!"
    )

    for chat_id in known_chat_ids:
        try:
            requests.post(
                f"{BASE_URL}/sendMessage",
                data={
                    "chat_id": chat_id,
                    "text": full_message,
                    "disable_web_page_preview": True
                }
            )
            print(f"✅ 알람 전송 성공 → {chat_id}")
        except Exception as e:
            print(f"❌ 전송 실패 ({chat_id}): {e}")

def monitor_mongo_changes():
    client = MongoClient(MONGO_URI)
    db = client['mock_trading_db']
    collection = db['trades']

    print("🚀 MongoDB 변화 감지 + Telegram 자동 알람 시작!")
    print(f"봇 링크: {TELEGRAM_BOT_LINK}")
    print("사용자가 봇에 메시지 보내면 자동으로 알람 대상 추가됩니다!\n")

    with collection.watch(full_document='updateLookup') as stream:
        while True:
            # 1. MongoDB 변화 확인
            if stream.alive and stream.try_next():
                change = stream.next()
                op_type = change['operationType']
                doc = change.get('fullDocument') or change.get('documentKey', '정보 없음')

                alarm_message = (
                    f"🔔 새로운 DB 변화!\n"
                    f"이벤트: {op_type.upper()}\n"
                    f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"데이터:\n{doc}"
                )

                print(alarm_message)
                send_alarm_to_all(alarm_message)

            # 2. Telegram 새로운 메시지 확인 (CHAT_ID 수집)
            updates = get_updates()
            for update in updates:
                global last_update_id
                last_update_id = update["update_id"]

                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    username = update["message"]["from"].get("username", "익명")
                    text = update["message"].get("text", "")

                    if chat_id not in known_chat_ids:
                        known_chat_ids.add(chat_id)
                        welcome = f"👋 환영합니다 @{username}!\n이제 DB 변화 알람을 받습니다!"
                        requests.post(f"{BASE_URL}/sendMessage", data={
                            "chat_id": chat_id,
                            "text": welcome
                        })
                        print(f"✅ 새 사용자 추가: {chat_id} (@{username})")
                    else:
                        print(f"메시지 수신: {chat_id} → {text}")

            time.sleep(1)  # CPU 부하 줄이기

# 실행
if __name__ == "__main__":
    client = MongoClient(MONGO_URI)
    collection = client['mock_trading_db']['trades']

    # 테스트 데이터 삽입 (알람 트리거)
    collection.insert_one({
        "test": "자동 알람 시스템 시작!",
        "timestamp": datetime.now()
    })
    print("테스트 데이터 삽입 → 알람 발송 예정\n")

    monitor_mongo_changes()