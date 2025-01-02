from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import uvicorn
import asyncio
import threading
from commands import handle_commands
from test_endpoints import router as test_router

logger = logging.getLogger(__name__)
app = FastAPI()

# 전역 설정
class BotConfig:
    def __init__(self):
        self.allowed_rooms = [
            "몰루 아카이브 PGR",
            "PGR21 생성AI,LLM,StableDiffusion",
            "프로젝트 아로나",
            "DebugRoom"
        ]
        self.ai_chat_enabled = True

config = BotConfig()

# 메시지 모델 정의
class Message(BaseModel):
    user_id: str
    room: str
    message: str

# 콘솔 명령어 처리
def handle_console_command(command: str):
    try:
        if command == "help":
            print("\n=== 사용 가능한 명령어 ===")
            print("rooms - 채팅방 목록 표시")
            print("add [방이름] - 채팅방 추가")
            print("remove [방이름] - 채팅방 삭제")
            print("ai on - AI 채팅 활성화")
            print("ai off - AI 채팅 비활성화")
            print("status - 현재 설정 상태 표시")
            print("exit - 서버 종료")
            
        elif command == "rooms":
            print("\n=== 등록된 채팅방 ===")
            for room in config.allowed_rooms:
                print(f"- {room}")
                
        elif command.startswith("add "):
            room = command[4:].strip()
            if room not in config.allowed_rooms:
                config.allowed_rooms.append(room)
                print(f"채팅방 추가됨: {room}")
            else:
                print("이미 등록된 채팅방입니다")
                
        elif command.startswith("remove "):
            room = command[7:].strip()
            if room in config.allowed_rooms:
                config.allowed_rooms.remove(room)
                print(f"채팅방 삭제됨: {room}")
            else:
                print("등록되지 않은 채팅방입니다")
                
        elif command == "ai on":
            config.ai_chat_enabled = True
            print("AI 채팅이 활성화되었습니다")
            
        elif command == "ai off":
            config.ai_chat_enabled = False
            print("AI 채팅이 비활성화되었습니다")
            
        elif command == "status":
            print("\n=== 현재 설정 상태 ===")
            print(f"AI 채팅: {'활성화' if config.ai_chat_enabled else '비활성화'}")
            print("\n등록된 채팅방:")
            for room in config.allowed_rooms:
                print(f"- {room}")
                
        elif command == "exit":
            print("서버를 종료합니다...")
            os._exit(0)
            
        else:
            print("알 수 없는 명령어입니다. 'help'를 입력하여 도움말을 확인하세요.")
            
    except Exception as e:
        print(f"명령어 처리 중 오류 발생: {str(e)}")

# 콘솔 입력 처리 스레드
def console_input():
    while True:
        command = input("\n명령어 입력> ").strip().lower()
        handle_console_command(command)

@app.post("/messages")
async def handle_message(message: Message):
    try:
        logger.info(f"카톡 메시지 받음: {message}")
        
        if message.message.startswith('*'):
            command = message.message[1:].strip()
            return await handle_commands(command, message, message.room)
        
        # AI 채팅 처리 (활성화된 경우에만)
        elif config.ai_chat_enabled:
            from api_client import call_claude_api
            response = await call_claude_api(
                messages=[{"user_id": message.user_id, "content": message.message}],
                room=message.room
            )
            return {"response": response}
        
        return {"response": None}
        
    except Exception as e:
        logger.error(f"메시지 처리 중 오류: {str(e)}")
        return {"response": f"오류가 발생했습니다: {str(e)}"}

# 테스트 라우터 추가
app.include_router(test_router, prefix="/test", tags=["test"])

if __name__ == "__main__":
    print("\n=== 몰루봇 서버 시작 ===")
    print("'help'를 입력하여 사용 가능한 명령어를 확인하세요.")
    
    # 콘솔 입력 스레드 시작
    threading.Thread(target=console_input, daemon=True).start()
    
    # FastAPI 서버 시작
    uvicorn.run(app, host="0.0.0.0", port=20001)
