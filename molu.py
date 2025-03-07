import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import uvicorn
import asyncio
import threading
from commands import handle_commands
from test_endpoints import router as test_router
from datetime import datetime
from fastapi.responses import FileResponse
from config import config
from features.chat_stats import log_chat

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
app = FastAPI()

# 채팅 메시지 모델 정의
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
            print("prompt - 현재 프롬프트 설정 표시")
            print("status - 현재 설정 상태 표시")
            print("update - 코드 업데이트 및 서버 재시작")
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
            
        elif command == "prompt":
            print(f"\n=== 현재 프롬프트 ({config.current_prompt}) ===")
            print(config.prompts[config.current_prompt])
            
        elif command == "status":
            print("\n=== 현재 설정 상태 ===")
            print(f"AI 채팅: {'활성화' if config.ai_chat_enabled else '비활성화'}")
            print(f"현재 프롬프트: {config.current_prompt}")
            print("\n등록된 채팅방:")
            for room in config.allowed_rooms:
                print(f"- {room}")
                
        elif command == "update":
            print("\n코드 업데이트를 시작합니다...")
            try:
                # git pull 실행
                import subprocess
                result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("코드 업데이트 완료!")
                    print("변경사항:")
                    print(result.stdout)
                    
                    print("\n서버를 재시작합니다...")
                    # 현재 프로세스를 새로운 프로세스로 대체
                    import sys
                    os.execv(sys.executable, ['python'] + sys.argv)
                else:
                    print("업데이트 중 오류 발생:")
                    print(result.stderr)
                    
            except Exception as e:
                print(f"업데이트 중 오류 발생: {str(e)}")
                
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
        start_time = datetime.now()
        
        # 실시간 메시지 출력
        current_time = start_time.strftime('%H:%M:%S.%f')[:-3]
        print(f"\n[{current_time}] 메시지 수신 {message.room}")
        print(f"└─ {message.user_id}: {message.message}")
        
        if message.message.startswith('*'):
            command = message.message[1:].strip()
            command_start = datetime.now()
            response = await handle_commands(command, message, message.room)
            command_end = datetime.now()
            
            if response and response.get("response"):
                print(f"└─ 봇 응답: {response['response']}")
                print(f"└─ 명령어 처리 시간: {(command_end - command_start).total_seconds()*1000:.0f}ms")
            
            return response
        
        elif config.ai_chat_enabled:
            from api_client import call_claude_api
            api_start = datetime.now()
            response = await call_claude_api(
                messages=[{"user_id": message.user_id, "content": message.message}],
                room=message.room
            )
            api_end = datetime.now()
            
            print(f"└─ 봇 응답: {response}")
            print(f"└─ API 응답 시간: {(api_end - api_start).total_seconds()*1000:.0f}ms")
            return {"response": response}
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds() * 1000
        print(f"└─ 총 처리 시간: {total_time:.0f}ms")
        
        return {"response": None}
        
    except Exception as e:
        error_msg = f"오류가 발생했습니다: {str(e)}"
        print(f"└─ 오류: {error_msg}")
        return {"response": error_msg}

# 테스트 라우터 추가
app.include_router(test_router, prefix="/test", tags=["test"])

@app.get("/favicon.ico")
async def favicon():
    return {"message": "No favicon"}  # 또는 실제 favicon 파일이 있다면:
    # return FileResponse("static/favicon.ico")

if __name__ == "__main__":
    print("\n=== 몰루봇 서버 시작 ===")
    print("'help'를 입력력하여 사용 가능한 명령어를 확인하세요.")
    
    # 콘솔 입력 스레드 시작
    threading.Thread(target=console_input, daemon=True).start()
    
    # FastAPI 서버 시작
    uvicorn.run(app, host="0.0.0.0", port=20001)
