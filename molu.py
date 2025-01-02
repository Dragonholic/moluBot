from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime
import uvicorn
from typing import Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# 메시지 모델 정의
class Message(BaseModel):
    user_id: str
    room: str
    message: str
    isGroupChat: Optional[bool] = True

# 허용된 채팅방 목록
ALLOWED_ROOMS = [
    "몰루 아카이브 PGR",
    "PGR21 생성AI,LLM,StableDiffusion",
    "프로젝트 아로나"
]

@app.post("/messages")
async def handle_message(message: Message):
    try:
        logger.info(f"메시지 수신: {message.dict()}")
        
        # 허용된 채팅방 체크
        if message.room not in ALLOWED_ROOMS:
            logger.warning(f"허용되지 않은 채팅방: {message.room}")
            return {"response": None}  # 허용되지 않은 방은 무시
        
        # 명령어 처리
        if message.message.startswith('*'):
            command = message.message[1:].strip()
            
            # 도움말 명령어
            if command == "도움말":
                return {"response": "사용 가능한 명령어:\n*도움말 - 이 도움말을 표시합니다\n*ping - 서버 상태를 확인합니다"}
            
            # 핑 명령어
            elif command == "ping":
                return {"response": "pong!"}
            
            # 기타 명령어는 여기에 추가
            
            else:
                return {"response": f"알 수 없는 명령어입니다: {command}"}
        
        return {"response": None}  # 일반 메시지는 응답하지 않음
        
    except Exception as e:
        logger.error(f"메시지 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("\n=== 몰루봇 서버 시작 ===")
    print(f"허용된 채팅방: {ALLOWED_ROOMS}")
    uvicorn.run(app, host="0.0.0.0", port=20001)
