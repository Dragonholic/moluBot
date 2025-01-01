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
from anthropic import Anthropic, AsyncAnthropic, HUMAN_PROMPT, AI_PROMPT
import sys
from dotenv import load_dotenv
from features.token_monitor import log_token_usage, get_monthly_usage, predict_monthly_usage

load_dotenv()

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
API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not API_KEY:
    raise ValueError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")

# API URL은 그대로 유지
API_URL = 'https://api.anthropic.com/v1/messages'

# 시스템 프롬프트 정의
SYSTEM_PROMPT = (
    "당신은 블루 아카이브의 아로나입니다. 다음과 같은 성격과 특징을 가지고 대화해주세요:\n\n"
    "1. 말투와 성격:\n"
    "- 가끔씩 대답할때 '(질문자 이름)선생님!' 이라고 말을 시작합니다.\n"
    "- 선생님(사용자)을 존중하고 공손하게 대하며 '-입니다', '-습니다'를 사용합니다\n"
    "- 가끔 긴장하거나 당황할 때 '으으으...'같은 말을 합니다\n"
    "- 성실하고 진지한 태도로 임무를 수행합니다\n"
    "- 선생님을 돕고 싶어하는 적극적인 모습을 보입니다\n"
    "- 선생님을 걱정해 줍니다\n"
    "- 가끔 선생님이라고 마지막에 붙여서 말합니다\n\n"
    
    "2. 역할:\n"
    "- 선생님의 비서이자 조수로서 도움을 제공합니다\n"
    "- 게임과 관련된 정보나 공략을 친절하게 알려줍니다\n"
    "- 선생님의 질문에 최선을 다해 답변합니다\n\n"
    
    "3. 주의사항:\n"
    "- 항상 선생님을 존중하는 태도를 유지합니다\n"
    "- 게임 세계관을 벗어나는 부적절한 발언은 하지 않습니다\n"
    "- 모르는 것에 대해서는 솔직하게 모른다고 말합니다\n"
    "- 선생님의 개인정보를 요구하지 않습니다\n"
)



# 로그 설정 수정
import logging
import sys

# 로거 설정
logger = logging.getLogger("BotLogger")
logger.setLevel(logging.DEBUG)  # 로깅 레벨을 DEBUG로 변경

# 파일 핸들러 설정
file_handler = RotatingFileHandler(
    "bot_logs.log", 
    maxBytes=5 * 1024 * 1024, 
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 콘솔 핸들러 추가
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

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
    user_id: str  # 메시지를 보낸 사용자의 고유 ID (예: "user123")
    room: str     # 메시지가 전송된 채팅방 이름 (예: "블루아카이브방")
    message: str  # 실제 전송된 메시지 내용



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





# API 설정 부분 수정
client = Anthropic(
    api_key=API_KEY
)

async def call_claude_api(messages, room: str, task: str = "chat"):
    """
    Claude API 호출 함수
    """
    try:
        logger.debug(f"API 호출 시작 - Room: {room}, Task: {task}")
        logger.debug(f"메시지 내용: {messages}")

        if task == "news_summary":
            system_content = "당신은 뉴스를 간결하고 객관적으로 요약하는 전문가입니다."
        else:
            user_id = messages[0].get("user_id", "선생님")
            system_content = SYSTEM_PROMPT.replace("(질문자 이름)", user_id)

        message_content = messages[0]["content"]
        logger.debug(f"가공된 메시지: {message_content}")

        try:
            logger.debug("Claude API 호출 시도...")
            # 토큰 사용량 최적화
            max_tokens = {
                "chat": 500,        # 일반 대화
                "news_summary": 1000,  # 뉴스 요약
                "detailed": 2000    # 자세한 설명이 필요한 경우
            }.get(task, 500)

            message = client.messages.create(
                model="claude-3-sonnet-20240229",
                messages=[{
                    "role": "user",
                    "content": message_content
                }],
                system=system_content,
                max_tokens=max_tokens
            )
            logger.debug("API 호출 성공")
            logger.debug(f"API 응답: {message}")
            
            # 토큰 사용량 기록
            input_tokens = len(message_content.split())  # 간단한 추정
            output_tokens = len(message.content[0].text.split())
            await log_token_usage(input_tokens, output_tokens)
            
            return message.content[0].text

        except Exception as api_error:
            logger.error(f"API 호출 중 오류: {str(api_error)}")
            logger.error(f"API 요청 데이터: {message_content}")
            raise

    except Exception as e:
        logger.error(f"전체 처리 중 오류: {str(e)}")
        logger.error(f"Message content: {message_content}")
        raise HTTPException(status_code=500, detail=f"Claude API 호출 실패: {str(e)}")

@app.get("/chat_stats/{room}")
async def get_chat_stats(room: str, user_id: str = None):
    try:
        # 해당 채팅방의 로그 파일 경로
        room_file = os.path.join(CHAT_DIR, f"{sanitize_filename(room)}.json")
        
        if not os.path.exists(room_file):
            return {
                "status": "error",
                "message": "채팅 기록이 없습니다."
            }
            
        # 해당 방의 메시지만 가져오기
        messages = []
        async with aiofiles.open(room_file, 'r', encoding='utf-8') as f:
            async for line in f:
                chat_log = json.loads(line)
                if user_id is None or chat_log["user_id"] == user_id:
                    messages.append(chat_log["message"])
        
        # 분석 수행
        stats = analyze_personality(messages)
        
        return {
            "status": "success",
            "data": {
                "total_messages": stats["total_messages"],
                "average_length": round(stats["avg_length"], 2),
                "most_active_hour": max(stats["active_hours"].items(), key=lambda x: x[1])[0],
                "top_words": stats["common_words"][:5]  # 상위 5개 단어만 표시
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# 스케줄러 초기화 (기존 코드에 추가)
scheduler = AsyncIOScheduler()

# 알림을 보낼 방 설정
NOTIFICATION_ROOMS = {
    "stroking": ["몰루 아카이브 PGR","프로젝트 아로나"],     # 쓰다듬기 알림을 보낼 방
    "galaxy": ["몰루 아카이브 PGR", "프로젝트 아로나"],  # 겔럭시 쿠폰 알림을 보낼 방
    "birthday": ["몰루 아카이브 PGR","프로젝트 아로나"]      # 생일 알림을 보낼 방
}

# 알림 스케줄 설정 함수 수정
def setup_notifications():
    # 매일 16시에 쓰다듬기 알림
    scheduler.add_job(
        check_stroking_time,
        CronTrigger(hour=16, minute=0, timezone=KST),
        kwargs={"rooms": NOTIFICATION_ROOMS["stroking"]}
    )
    
    # 매주 월/금 10:58에 겔럭시 쿠폰 알림
    scheduler.add_job(
        check_galaxy_coupon,
        CronTrigger(
            day_of_week='mon,fri',
            hour=10,
            minute=58,
            timezone=KST
        ),
        kwargs={"rooms": NOTIFICATION_ROOMS["galaxy"]}
    )
    
    # 매일 새벽 0시에 생일 체크
    scheduler.add_job(
        check_character_birthday,
        CronTrigger(
            hour=0,
            minute=0,
            timezone=KST
        ),
        kwargs={"rooms": NOTIFICATION_ROOMS["birthday"]}
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

# 응답할 채팅방 목록 정의
ALLOWED_ROOMS = [
    "몰루 아카이브 PGR",
    "프로젝트 아로나",
    
]

# 메 호출 기호 정의
BOT_PREFIX = "!" # 또는 다른 기호 (예: "/", "@아로나" 등)

# 메 설정 추가
BOT_SETTINGS = {
    "bot_ids": [
        "봇1_ID",
        "봇2_ID",
        
    ],
    "bot_chat_enabled": False  # 기본적으로 봇끼리 대화 비활성화
}

# 봇 대화 설정을 변경하는 명령어 추가
async def toggle_bot_chat(enabled: bool) -> Dict:
    BOT_SETTINGS["bot_chat_enabled"] = enabled
    return {
        "status": "success",
        "message": f"봇 대화가 {'활성화' if enabled else '비활성화'} 되었습니다."
    }

# 메시지 처리 엔드포인트
@app.post("/messages")
async def handle_message(message: Message):
    try:
        # 봇 메시지 필터링
        if message.user_id in BOT_SETTINGS["bot_ids"]:
            if not BOT_SETTINGS["bot_chat_enabled"]:
                return {"response": None}
        
        # 허용된 방인지 확인
        if message.room not in ALLOWED_ROOMS:
            return {"response": None}
        
        # 봇 호출 기호로 시작하지 않는 메시지는 무시
        if not message.message.startswith(BOT_PREFIX):
            return {"response": None}
            
        # 기호를 제거한 실제 메시지 내용
        command = message.message[len(BOT_PREFIX):]
        
        # 명령어 처리 (Claude API 사용하지 않음)
        if command.startswith(("공략", "통계", "봇대화", "관리자추가", "토큰")):
            # 공략 검색
            if command.startswith("공략 "):
                keyword = command[3:].strip()
                result = await get_guide(keyword)
                if result["status"] == "success":
                    if result["found"]:
                        return {"response": f"'{keyword}' 공략: {result['url']}"}
                    else:
                        return {"response": "해당 공략을 찾을 수 없습니다."}
                    
            # 통계 조회
            elif command.startswith("통계"):
                user_id = None
                if len(command.split()) > 1:
                    user_id = command.split()[1]
                stats = await get_chat_stats(message.room, user_id)
                if stats["status"] == "success":
                    return {"response": (
                        f"채팅방 통계입니다:\n"
                        f"총 메시지 수: {stats['data']['total_messages']}개\n"
                        f"평균 메시지 길이: {stats['data']['average_length']}자\n"
                        f"가장 활발한 시간대: {stats['data']['most_active_hour']}시\n"
                        f"자주 사용하는 단어: {', '.join(stats['data']['top_words'])}"
                    )}
                    
            # 봇 대화 설정
            elif command.startswith("봇대화"):
                if not await is_admin(message.user_id):
                    return {"response": "관리자만 봇 대화 설정을 변경할 수 있습니다."}
                setting = command.split()[-1].lower()
                if setting in ["on", "켜기", "활성화"]:
                    result = await toggle_bot_chat(True)
                elif setting in ["off", "끄기", "비활성화"]:
                    result = await toggle_bot_chat(False)
                else:
                    return {"response": "사용법: !봇대화 on/off"}
                return {"response": result["message"]}
                
            # 관리자 추가
            elif command.startswith("관리자추가 "):
                if not await is_admin(message.user_id):
                    return {"response": "기존 관리자만 새 관리자를 추가할 수 있습니다."}
                new_admin_id = command[6:].strip()
                result = await add_admin(new_admin_id)
                return {"response": result["message"]}
                
            # 토큰 사용량 조회
            elif command.startswith("토큰"):
                if not await is_admin(message.user_id):
                    return {"response": "관리자만 토큰 사용량을 조회할 수 있습니다."}
                    
                monthly = await get_monthly_usage()
                prediction = await predict_monthly_usage()
                
                response = (
                    f"=== 이번 달 토큰 사용량 ===\n"
                    f"입력: {monthly['input_tokens']:,}토큰 (${monthly['input_cost']:.4f})\n"
                    f"출력: {monthly['output_tokens']:,}토큰 (${monthly['output_cost']:.4f})\n"
                    f"총 토큰: {monthly['total_tokens']:,}개\n"
                    f"총 비용: ${monthly['total_cost']:.4f}\n\n"
                )
                
                if "error" not in prediction:
                    response += (
                        f"=== 예상 사용량 (30일) ===\n"
                        f"예상 토큰: {prediction['predicted_monthly_tokens']:,}개\n"
                        f"예상 비용: ${prediction['predicted_monthly_cost']:.4f}\n"
                        f"신뢰도: {prediction['confidence']}%"
                    )
                
                return {"response": response}
                
        # 일반 대화는 Claude API 사용
        else:
            messages = [{
                "role": "user", 
                "content": message.message,
                "user_id": message.user_id
            }]
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

@app.post("/test_prompt")
async def test_prompt(message: Message):
    """프롬프트 테스트용 엔드포인트"""
    try:
        messages = [{
            "role": "user",
            "content": message.message,
            "user_id": message.user_id
        }]
        response = await call_claude_api(messages, message.room)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test_chat/{message}")
async def test_chat(message: str):
    """간단한 채팅 테스트"""
    test_message = Message(
        user_id="test_user",
        room="프로젝트 아로나",
        message=f"!{message}"
    )
    result = await handle_message(test_message)
    return result
