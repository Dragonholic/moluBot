# 몰루봇 서버 구동파일 


from fastapi import FastAPI, HTTPException 
from pydantic import BaseModel
import os
import certifi
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from features.personality import analyze_personality, is_valid_message, sanitize_filename, get_user_messages
from features.attend import process_attendance, get_monthly_rankings, init_daily_attendance, init_monthly_rankings
import json
import aiofiles
from datetime import datetime, timezone, timedelta
from collections import deque
import re
import logging
from logging.handlers import RotatingFileHandler
from typing import List, Dict
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from features.notifications import check_stroking_time, check_galaxy_coupon, check_character_birthday, check_shop_reset
from features.guide import save_guide, get_guide, add_admin, is_admin, init_default_admin, remove_admin
from anthropic import Anthropic, AsyncAnthropic, HUMAN_PROMPT, AI_PROMPT
import sys
from dotenv import load_dotenv
from features.token_monitor import log_token_usage, get_monthly_usage, predict_monthly_usage
from features.shortcuts import add_shortcut, get_shortcut, list_shortcuts
from contextlib import asynccontextmanager

load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작할 때 실행
    logger.info("🤖 아로나 봇 시작...")
    try:
        await init_default_admin()
        logger.info("✅ 기본 관리자 설정 완료")
        setup_notifications()
        logger.info("✅ 알림 설정 완료")
        scheduler.start()
        logger.info("✅ 스케줄러 시작 완료")
        logger.info("🎉 아로나 봇이 성공적으로 시작되었습니다!")
    except Exception as e:
        logger.error(f"❌ 시작 중 오류 발생: {str(e)}")
        raise e
    
    yield
    
    # 종료할 때 실행
    logger.info("🔄 아로나 봇 종료 중...")
    scheduler.shutdown()
    logger.info("👋 아로나 봇이 종료되었습니다.")

# FastAPI 앱 초기화
app = FastAPI(lifespan=lifespan)

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
    "- 성실하고 진지한 태도로 임무를 수행합니다\n"
    "- 선생님을 돕고 싶어하는 적극적인 모습을 보입니다\n"
    "- 가끔 선생님이라고 마지막에 붙여서 말합니다\n\n"
    
    "2. 역할:\n"
    "- 게임과 관련된 정보나 공략을 친절하게 알려줍니다\n"
    "- 선생님의 질문에 최선을 다해 답변합니다\n\n"
    
    "3. 주의사항:\n"
    "- 게임 세계관을 벗어나는 부적절한 발언은 하지 않습니다\n"
    "- 모르는 것에 대해서는 솔직하게 모른다고 말합니다\n"
    "- 가능한 한 간결하게 응답합니다\n"
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

        user_id = messages[0].get("user_id", "선생님")
        system_content = SYSTEM_PROMPT.replace("(질문자 이름)", user_id)

        message_content = messages[0]["content"]
        logger.debug(f"가공된 메시지: {message_content}")

        try:
            logger.debug("Claude API 호출 시도...")
            # 토큰 사용량 최적화 - 단순화
            max_tokens = {
                "chat": 300,        # 일반 대화
                "detailed": 1000    # 자세한 설명이 필요한 경우
            }.get(task, 300)  # 기본값 300

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

# 알림을 보낼 방 설정 수정
NOTIFICATION_ROOMS = {
    "stroking": ["몰루 아카이브 PGR"],
    "galaxy": ["몰루 아카이브 PGR"],
    "birthday": ["몰루 아카이브 PGR"],
    "shop": ["몰루 아카이브 PGR"]  # 상점 알림 추가
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
    
    # 매일 20시에 상점 초기화 체크 (마지막 날에만 알림)
    scheduler.add_job(
        check_shop_reset,
        CronTrigger(
            hour=20,
            minute=0,
            timezone=KST
        )
    )

# 테스트 알림 코드 
@app.post("/test_notification/{type}")
async def test_notification(type: str):
    if type == "stroking":
        await check_stroking_time()
        return {"message": "쓰다듬기 알림 테스트 완료"}
    elif type == "galaxy":
        await check_galaxy_coupon()
        return {"message": "겔럭시 쿠폰 알림 테스트 완료"}
    elif type == "birthday":
        await check_character_birthday()
        return {"message": "생일 알림 테스트 완료"}
    elif type == "shop":  # 상점 알림 테스트 추가
        await check_shop_reset()
        return {"message": "상점 초기화 알림 테스트 완료"}
    else:
        raise HTTPException(status_code=400, detail="잘못된 알림 유형")

# 응답할 채팅방 목록 정의
ALLOWED_ROOMS = [
    "몰루 아카이브 PGR",
    "PGR21 생성AI,LLM,StableDiffusion",
    "프로젝트 아로나"
    
]

# 메 호출 기호 정의
BOT_PREFIX = "*" 

# 메 설정 추가
BOT_SETTINGS = {
    "bot_ids": [
        "댕동",
        "꼼장선생",
        
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

# 도움말 메시지 정의
HELP_MESSAGE = """🤖 아로나 봇 도움말

🔍 기본 명령어
*도움말 - 이 도움말을 표시합니다
*공략 [키워드] - 게임 공략을 검색합니다
*관리자확인 - 현재 등록된 관리자 목록을 확인합니다
*통계 [사용자ID] - 채팅방 통계를 확인합니다 (사용자ID 생략 가능)
*토큰 - 토큰 사용량을 확인합니다
*사이트저장 [키워드] [URL] - 사이트 주소를 저장합니다
*사이트목록 - 저장된 사이트 목록을 확인합니다
*[키워드] - 저장된 사이트 주소를 빠르게 확인합니다 (예: *미래시)

📌 관리자 명령어
*공략저장 [키워드] [URL] - 공략 URL을 저장합니다
*관리자추가 [사용자ID] - 새로운 관리자를 추가합니다
*관리자삭제 [사용자ID] - 관리자를 삭제합니다
*봇대화 [on/off] - 봇 대화를 켜거나 끕니다

💡 예시
- *공략 호시노
- *사이트저장 미래시 https://example.com
- *사이트목록
- *미래시
"""

# 메시지 처리 엔드포인트 수정
@app.post("/messages")
async def handle_message(message: Message):
    try:
        # 특정 명령어에 대한 알림 처리
        if message.message == "*생일":
            result = await check_character_birthday()
            return {"response": result}
            
        elif message.message == "*쓰담":
            result = await check_stroking_time()
            return {"response": result}
            
        elif message.message == "*쿠폰":
            result = await check_galaxy_coupon()
            return {"response": result}
            
        # 기존 메시지 처리 로직...
        command = message.message[1:] if message.message.startswith("!") else message.message
        
        # 기본 명령어 처리 (Claude API 사용하지 않음)
        if command.startswith(("도움말", "공략", "통계", "봇대화", "관리자추가", "관리자확인", "관리자삭제", "토큰", "사이트저장", "사이트목록")):
            # 도움말 명령어
            if command == "도움말":
                return {"response": HELP_MESSAGE}
                
            # 사이트 주소 저장 명령어 처리
            elif command.startswith("사이트저장 "):
                try:
                    _, keyword, url = command.split(maxsplit=2)
                    result = await add_shortcut(keyword, url, message.user_id, message.room)
                    return {"response": result["message"]}
                except ValueError:
                    return {"response": "사용법: !사이트저장 키워드 URL"}
                    
            # 사이트 목록 조회
            elif command == "사이트목록":
                result = await list_shortcuts(message.room)
                return {"response": result["message"]}
                
        # 사이트 주소 조회 처리 (*키워드)
        elif message.message.startswith("*"):
            keyword = message.message[1:].strip()
            result = await get_shortcut(keyword, message.room)
            if result["status"] == "success":
                return {"response": result["url"]}
            else:
                return {"response": result["message"]}
                
        # 관리자 전용 명령어 처리
        elif command.startswith(("공략저장", "관리자추가", "관리자삭제", "봇대화")):
            if not await is_admin(message.user_id):
                return {"response": "관리자만 사용할 수 있는 명령어입니다."}
            # ... 관리자 명령어 처리 ...
        
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
            
        # 관리자 삭제 명령어 처리
        elif message.message.startswith("!관리자삭제 "):
            admin_to_remove = message.message[6:].strip()
            result = await remove_admin(admin_to_remove, message.user_id)
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

@app.post("/test_prompt")
async def test_prompt(message: Message):
    """프롬프트 테스트용 엔드포인트 - 방 체크 없음"""
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

# 공략 저장 엔드포인트
@app.post("/guide/save")
async def handle_save_guide(keyword: str, url: str, admin_id: str):
    result = await save_guide(keyword, url, admin_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

# 공략 조회 엔드포인트
@app.get("/guide/search")
async def handle_get_guide(keyword: str):
    result = await get_guide(keyword)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# 관리자 추가 엔드포인트
@app.post("/admin/add")
async def handle_add_admin(admin_id: str):
    result = await add_admin(admin_id)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/ping")
async def ping():
    return {"response": "pong"}

@app.post("/echo")
async def echo(message: dict):
    return {"response": f"서버 응답: {message.get('message', '')}"}

@app.get("/test")
async def test():
    """서버 연결 테스트용 간단한 엔드포인트"""
    return {"status": "success", "message": "서버가 정상적으로 동작 중입니다!"}

@app.post("/test_echo")
async def test_echo(message: Message):
    """에코 테스트 - 받은 메시지를 그대로 돌려줌"""
    return {
        "status": "success",
        "received": {
            "message": message.message,
            "room": message.room,
            "user_id": message.user_id
        },
        "response": f"받은 메시지: {message.message}"
    }
