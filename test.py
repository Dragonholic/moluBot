from fastapi import FastAPI, Request
import uvicorn
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/ping")
async def ping():
    logger.info("ping 요청 받음")
    return {"response": "pong"}

@app.post("/message")
async def handle_message(message: dict):
    logger.info(f"카톡 메시지 받음: {message}")
    return {"response": f"메시지 수신 완료: {message.get('message', '')}"}

if __name__ == "__main__":
    print("\n=== 테스트 서버 시작 ===")
    print("외부 접속 주소: ")
    print("테스트 방법:")
    print("1. 브라우저: ")
    print("2. curl: curl ")
    uvicorn.run(app, host="0.0.0.0", port=20001) 