# 몰루봇 서버 구동파일 


from fastapi import FastAPI, HTTPException 
from pydantic import BaseModel
import os
import aiohttp
import ssl
import certifi
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from features.news import daily_news_summary, read_news_summary, get_random_news
from features.personality import analyze_personality, is_valid_message, sanitize_filename, get_user_messages
from features.attend import process_attendance, get_monthly_rankings, init_daily_attendance, init_monthly_rankings
import json
import aiofiles
from datetime import datetime, timezone, timedelta
from collections import deque
import re
import random
import urllib.parse
import logging
from logging.handlers import RotatingFileHandler
from typing import List, Dict
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from features.notifications import check_stroking_time, check_galaxy_coupon, check_character_birthday
from features.guide import save_guide, get_guide, add_admin, is_admin



# FastAPI 앱 초기화
app = FastAPI()

# 데이터 모델 정의
class QuestionModel(BaseModel):
    question: str  # 질문을 받을 데이터 모델

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))
CHAT_DIR = "chat_logs"  # 채팅 로그 저장 디렉터리
os.makedirs(CHAT_DIR, exist_ok=True)

# GPT API 키 및 URL 설정 부분을 Claude API 설정으로 변경
API_KEY = ''  # Anthropic API 키
API_URL = 'https://api.anthropic.com/v1/messages'  # Claude API 엔드포인트

# 시스템 프롬프트 정의 TODO
SYSTEM_PROMPT = (
    
)



# 로그 파일 설정
log_filename = "error_logs.log"
log_handler = RotatingFileHandler(log_filename, maxBytes=5 * 1024 * 1024, backupCount=5)  # 최대 5MB, 백업 5개
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
log_handler.setLevel(logging.ERROR)

# 로거 설정
logger = logging.getLogger("ErrorLogger")
logger.setLevel(logging.ERROR)
logger.addHandler(log_handler)

def process_message(message):
    try:
        # 메시지 처리 로직 (예시)
        if not message:
            raise ValueError("메시지가 비어 있습니다.")
        # 처리 성공 로직
        return "처리 완료"
    except Exception as e:
        # 에러를 파일에 기록
        logger.error(f"Message processing failed: {str(e)}")
        return f"에러 발생: {str(e)}"




# SSL 인증서 경로 설정
os.environ['SSL_CERT_FILE'] = certifi.where()

class Message(BaseModel):
    user_id: str  # 사용자 ID
    room: str    # 채팅방 ID
    message: str  # 메시지 내용



# 채팅방 별 문맥 저장
room_contexts = {}

def sanitize_filename(filename: str) -> str:
    """
    파일 이름에 사용할 수 없는 문자 제거
    """
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized_filename = re.sub(invalid_chars, '_', filename)
    if len(sanitized_filename) > 255:
        sanitized_filename = sanitized_filename[:255]
    return sanitized_filename





async def call_claude_api(messages, room: str, task: str = "chat"):
    """
    Claude API 호출 함수
    """
    if task == "news_summary":
        system_content = "당신은 뉴스를 간결하고 객관적으로 요약하는 전문가입니다."
    else:
        system_content = SYSTEM_PROMPT

    # Claude API 형식에 맞게 메시지 변환
    formatted_messages = []
    for msg in messages:
        if msg["role"] == "user":
            formatted_messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            formatted_messages.append({"role": "assistant", "content": msg["content"]})
    
    # SSL 인증서 및 타임아웃 설정
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=ssl_context), 
        timeout=timeout
    ) as session:
        async with session.post(
            API_URL,
            json={
                "model": "claude-3-sonnet-20240229",  # 또는 다른 Claude 모델
                "messages": formatted_messages,
                "max_tokens": 500,
                "temperature": 0.5,
                "system": system_content
            },
            headers={
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        ) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Claude API 호출 실패")
            
            response_data = await response.json()
            return response_data['content'][0]['text']

@app.get("/chat_stats/{room}")
async def get_chat_stats(room: str, user_id: str = None):
    try:
        # 메시지 가져오기
        messages = get_user_messages(room, user_id)
        
        # 분석 수행
        stats = analyze_personality(messages)
        
        return {
            "status": "success",
            "data": {
                "total_messages": stats["total_messages"],
                "average_length": round(stats["avg_length"], 2),
                "most_active_hour": max(stats["active_hours"].items(), key=lambda x: x[1])[0],
                "top_words": stats["common_words"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 스케줄러 초기화 (기존 코드에 추가)
scheduler = AsyncIOScheduler()

# 알림 스케줄 설정
def setup_notifications():
    # 매일 16시에 쓰다듬기 알림
    scheduler.add_job(
        check_stroking_time,
        CronTrigger(hour=16, minute=0, timezone=KST)
    )
    
    # 매주 월/금 10:58에 겔럭시 쿠폰 알림
    scheduler.add_job(
        check_galaxy_coupon,
        CronTrigger(
            day_of_week='mon,fri',
            hour=10,
            minute=58,
            timezone=KST
        )
    )
    
    # 매일 아침 8시에 생일 체크
    scheduler.add_job(
        check_character_birthday,
        CronTrigger(
            hour=8,
            minute=0,
            timezone=KST
        )
    )

# FastAPI 시작 이벤트에 스케줄러 시작 추가
@app.on_event("startup")
async def startup_event():
    setup_notifications()
    scheduler.start()

# FastAPI 종료 이벤트에 스케줄러 종료 추가
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()


#테스트 알림 코드 
@app.post("/test_notification/{type}")
async def test_notification(type: str):
    if type == "stroking":
        await check_stroking_time()
        return {"message": "쓰다듬기 알림 테스트 완료"}
    elif type == "galaxy":
        await check_galaxy_coupon()
        return {"message": "겔럭시 쿠폰 알림 테스트 완료"}
    elif type == "birthday":  # 생일 알림 테스트 추가
        await check_character_birthday()
        return {"message": "생일 알림 테스트 완료"}
    else:
        raise HTTPException(status_code=400, detail="잘못된 알림 유형")

# 메시지 처리 엔드포인트
@app.post("/messages")
async def handle_message(message: Message):
    try:
        # 메시지 유효성 검사
        if not is_valid_message(message.message):
            raise HTTPException(status_code=400, detail="잘못된 메시지 형식")
        
        # 공략 저장 명령어 처리 (!공략저장 키워드 URL)
        if message.message.startswith("!공략저장 "):
            if not await is_admin(message.user_id):
                return {"response": "관리자만 공략을 저장할 수 있습니다."}
            
            try:
                _, keyword, url = message.message.split(maxsplit=2)
                result = await save_guide(keyword, url, message.user_id)
                return {"response": result["message"]}
            except ValueError:
                return {"response": "사용법: !공략저장 키워드 URL"}
        
        # 공략 검색 명령어 처리 (!공략 키워드)
        elif message.message.startswith("!공략 "):
            keyword = message.message[4:].strip()
            result = await get_guide(keyword)
            
            if result["status"] == "success":
                if result["found"]:
                    return {"response": f"'{keyword}' 공략: {result['url']}"}
                else:
                    return {"response": result["search_result"]}
            else:
                return {"response": "공략 검색 중 오류가 발생했습니다."}
        
        # 관리자 추가 명령어 처리 (!관리자추가 사용자ID)
        elif message.message.startswith("!관리자추가 "):
            if not await is_admin(message.user_id):
                return {"response": "기존 관리자만 새 관리자를 추가할 수 있습니다."}
            
            new_admin_id = message.message[7:].strip()
            result = await add_admin(new_admin_id)
            return {"response": result["message"]}
            
        # 일반 메시지 처리
        else:
            messages = [{"role": "user", "content": message.message}]
            response = await call_claude_api(messages, message.room)
            
            # 채팅 로그 저장
            chat_log = {
                "user_id": message.user_id,
                "room": message.room,
                "message": message.message,
                "response": response,
                "timestamp": datetime.now(KST).isoformat()
            }
            
            room_file = os.path.join(CHAT_DIR, f"{sanitize_filename(message.room)}.json")
            async with aiofiles.open(room_file, 'a', encoding='utf-8') as f:
                await f.write(json.dumps(chat_log, ensure_ascii=False) + '\n')
            
            return {"response": response}
        
    except Exception as e:
        logger.error(f"Message handling error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
