import socket

# 서버 설정 (main-step10-discord.py와 동일하게 설정)
HOST = '127.0.0.1'  # 로컬 테스트이므로 localhost
PORT = 5000         # 서버에서 설정한 포트

def start_client():
    """
    LUA 클라이언트 흉내를 내는 테스트용 Python 클라이언트입니다.
    소켓을 통해 서버에 접속하고 메시지를 전송합니다.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"[Client] Connecting to server at {HOST}:{PORT}...")
        client_socket.connect((HOST, PORT))
        print("[Client] Connected! (Type 'quit' to exit)")

        while True:
            # 사용자 입력 받기
            user_input = input("You (LUA): ")
            if user_input.lower() in ['quit', 'exit']:
                break
            
            if not user_input:
                continue

            # 서버로 데이터 전송 (UTF-8 인코딩)
            client_socket.sendall(user_input.encode('utf-8'))

            # 서버로부터 응답 수신
            data = client_socket.recv(1024)
            print(f"Server (Bot): {data.decode('utf-8').strip()}")

    except ConnectionRefusedError:
        print("[Error] 서버에 연결할 수 없습니다. 'main-step10-discord.py'가 실행 중인지 확인해주세요.")
    except Exception as e:
        print(f"[Error] {e}")
    finally:
        client_socket.close()
        print("[Client] Connection closed.")

if __name__ == "__main__":
    start_client()