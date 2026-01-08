import os
import asyncio
import random
import socket
import sys
import discord
from dotenv import load_dotenv
from pymongo import MongoClient

# 1. 환경 변수 로드
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# 만약 실행 시 커맨드 라인 인자로 토큰을 입력했다면 우선 사용 (예: python main.py MY_TOKEN)
if len(sys.argv) > 1:
    DISCORD_TOKEN = sys.argv[1]

MONGO_DB_URL = os.getenv("MONGO_DB_URL")
SOCKET_HOST = "0.0.0.0"  # 모든 인터페이스에서 접속 허용
SOCKET_PORT = 5000       # LUA 클라이언트가 접속할 포트 (필요시 변경)

# 2. 전역 변수 및 DB 설정
MEME_DB = []

def load_meme_data():
    """MongoDB에서 유행어 데이터를 메모리로 로드"""
    global MEME_DB
    if not MONGO_DB_URL:
        print("[System] Error: MONGO_DB_URL is not set.")
        return

    try:
        client = MongoClient(MONGO_DB_URL)
        db = client["mock_trading_db"]
        collection = db["emo_db"]
        
        # term 필드만 가져와서 리스트로 저장
        cursor = collection.find({}, {"term": 1, "_id": 0})
        MEME_DB = [doc["term"] for doc in cursor if "term" in doc]
        print(f"[System] Loaded {len(MEME_DB)} items from MongoDB.")
    except Exception as e:
        print(f"[System] Error loading data from MongoDB: {e}")
        MEME_DB = ["가즈아", "존버", "떡상", "알잘딱깔센"] # 기본값

def get_response_logic(user_text: str) -> str:
    """
    OpenAI를 대체하는 내부 로직.
    사용자 입력에 따라 MongoDB 데이터를 기반으로 응답 생성.
    """
    user_text = user_text.strip()
    
    # 1. 기본 명령어 처리
    if user_text in ["!help", "도움", "명령어"]:
        return "명령어: !help, !status, 또는 아무 말이나 해보세요."
    
    # 2. 키워드 매칭 (DB 활용)
    matched = [m for m in MEME_DB if m in user_text]
    if matched:
        pick = random.choice(matched)
        return f"오! '{pick}' 말씀이시군요. 요즘 그게 핫하죠!"
    
    # 3. 랜덤 응답 (매칭 실패 시)
    if MEME_DB:
        recommend = random.choice(MEME_DB)
        return f"음, 잘 모르겠지만 '{recommend}' 같은 건 어때요?"
    
    return "데이터가 없어서 무슨 말을 해야 할지 모르겠어요."

# 3. Discord Bot 설정
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"[Discord] Logged in as {bot.user}")
    load_meme_data() # 봇 시작 시 데이터 로드

@bot.event
async def on_message(message):
    # 디스코드 채널에서 테스트할 때 사용
    if message.author == bot.user:
        return
    
    if message.content.startswith("!chat"):
        user_msg = message.content.replace("!chat", "").strip()
        response = get_response_logic(user_msg)
        await message.channel.send(f"[Bot] {response}")

# 4. Socket Server (LUA 통신용) 설정
async def handle_lua_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"[Socket] New connection from {addr}")

    try:
        while True:
            # LUA에서 데이터 수신 (최대 1024바이트)
            data = await reader.read(1024)
            if not data:
                break
            
            message = data.decode('utf-8').strip()
            print(f"[Socket] Received from LUA: {message}")

            # 로직을 통해 응답 생성
            response = get_response_logic(message)
            
            # LUA로 응답 전송 (줄바꿈 문자 추가)
            writer.write((response + "\n").encode('utf-8'))
            await writer.drain()
            
    except Exception as e:
        print(f"[Socket] Error with client {addr}: {e}")
    finally:
        print(f"[Socket] Closing connection {addr}")
        writer.close()
        await writer.wait_closed()

async def start_socket_server():
    server = await asyncio.start_server(
        handle_lua_client, SOCKET_HOST, SOCKET_PORT
    )
    addr = server.sockets[0].getsockname()
    print(f"[Socket] Serving on {addr}")

    async with server:
        await server.serve_forever()

# 5. 메인 실행부 (Discord Bot + Socket Server 병렬 실행)
async def main():
    # Discord Bot과 소켓 서버를 동시에 실행
    tasks = [start_socket_server()]

    if not DISCORD_TOKEN:
        print("[System] Warning: DISCORD_TOKEN is missing. Running in Socket-only mode.")
    else:
        tasks.append(bot.start(DISCORD_TOKEN))

    # 등록된 태스크들을 동시에 실행 (소켓 서버 + 봇)
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[System] Server stopped.")