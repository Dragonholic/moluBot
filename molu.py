from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import uvicorn
from commands import handle_commands
from test_endpoints import router as test_router

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI()

# 메시지 모델 정의
class Message(BaseModel):
    user_id: str
    room: str
    message: str

# 응답할 채팅방 목록 정의
ALLOWED_ROOMS = [
    "몰루 아카이브 PGR",
    "PGR21 생성AI,LLM,StableDiffusion",
    "프로젝트 아로나",
    "DebugRoom"
]

@app.get("/ping")
async def ping():
    logger.info("ping 요청 받음")
    return {"response": "pong"}

@app.post("/messages")
async def handle_message(message: Message):
    try:
        logger.info(f"카톡 메시지 받음: {message}")
        
        if message.message.startswith('*'):
            command = message.message[1:].strip()
            return await handle_commands(command, message, message.room)
            
        return {"response": None}
        
    except Exception as e:
        logger.error(f"메시지 처리 중 오류: {str(e)}")
        return {"response": f"오류가 발생했습니다: {str(e)}"}

# 테스트 라우터 추가
app.include_router(test_router, prefix="/test", tags=["test"])

if __name__ == "__main__":
    print("\n=== 몰루봇 서버 시작 ===")
    print(f"허용된 채팅방: {ALLOWED_ROOMS}")
    uvicorn.run(app, host="0.0.0.0", port=20001)
