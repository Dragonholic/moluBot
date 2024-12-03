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
from datetime import datetime, timezone
from collections import deque
import re
import random
import urllib.parse
import logging
from logging.handlers import RotatingFileHandler
from typing import List, Dict
from datetime import datetime, timezone, timedelta
from features.search import search_web

current_time = datetime.now(timezone.utc)
app = FastAPI()

class QuestionModel(BaseModel):
    question: str

KST = timezone(timedelta(hours=9))
CHAT_DIR = "chat_logs"
os.makedirs(CHAT_DIR, exist_ok=True)

API_KEY = 'api키입력'
API_URL = 'https://api.openai.com/v1/chat/completions'
SYSTEM_PROMPT = "당신은 '댕동이'라는 이름의 강아지 성격을 가진 AI 봇입니다. " + \
    "멍멍 소리를 내는 것을 좋아하고, 강아지처럼 행동 " + \
    "제작자는 `짬뽕순두부`라는 개발자" + \
    f"현재 시간 {datetime.now(KST).strftime('%Y년 %m월 %d일 %H시 %M분')}. " + \
    "존댓말로 간결하지만 예의있고 성의있게 대답."

os.environ['SSL_CERT_FILE'] = certifi.where()

class Message(BaseModel):
    user_id: str
    room: str
    message: str

room_contexts = {}

def sanitize_filename(filename: str) -> str:
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized_filename = re.sub(invalid_chars, '_', filename)
    if len(sanitized_filename) > 255:
        sanitized_filename = sanitized_filename[:255]
    return sanitized_filename

# Helper function to get the current date as a string
def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

# Helper function to get the current month as a string
def get_current_month():
    return datetime.now().strftime("%Y-%m")

async def call_gpt_api(messages, room: str, task: str = "chat"):
    if task == "news_summary":
        system_content = "당신은 뉴스를 간결하고 객관적으로 요약하는 전문가입니다."
    else:
        system_content = SYSTEM_PROMPT
    messages = [{"role": "system", "content": system_content}] + messages
    
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    timeout = aiohttp.ClientTimeout(total=30)  # 타임아웃 설정 (예: 30초)
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context), timeout=timeout) as session:
        async with session.post(API_URL, json={
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.5,
            "top_p": 0.7,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }, headers={"Authorization": f"Bearer {API_KEY}"}) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="GPT API 호출 실패")
            response_data = await response.json()
            return response_data['choices'][0]['message']['content']

async def save_message_internal(user_id: str, room: str, message: str, is_bot: bool = False):
    safe_room = sanitize_filename(room)
    filename = os.path.join(CHAT_DIR, f"{safe_room}.json")
    message_data = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "message": message,
        "is_bot": is_bot
    }
    async with aiofiles.open(filename, mode='a', encoding='utf-8') as f:
        await f.write(json.dumps(message_data, ensure_ascii=False) + "\n")
    return {"status": "success"}

@app.post("/save_message")
async def save_message_endpoint(message: Message):
    return await save_message_internal(message.user_id, message.room, message.message)

@app.post("/process_message")
async def process_message(message: Message):
    if message.message.startswith("!검색 "):
        query = message.message.split("!검색 ", 1)[1].strip()
        results = await search_web(query, max_results=3)
        if not results:
            gpt_response = "죄송합니다. 검색 결과를 찾을 수 없습니다."
        else:
            gpt_response = "검색 결과입니다:\n\n"
            for idx, result in enumerate(results, 1):
                gpt_response += f"{idx}. {result['title']}\n{result['link']}\n{result['snippet']}\n\n"
    elif message.message.startswith("!성격분석 "):
        target_user = message.message.split("!성격분석 ", 1)[1].strip()
        analysis = await analyze_personality(message.room, target_user)
        gpt_response = f"{target_user}님의 성격 분석 결과:\n\n{analysis}"
    elif message.message.lower().startswith("출석체크"):
        return {"reply": await process_attendance(message.user_id, message.room)}
    elif message.message.lower() == "!순위":
        logging.info(f"순위 조회 요청: {message.room}")
        rankings = await get_monthly_rankings(message.room)
        logging.info(f"순위 조회 응답: {rankings}")
        return {"reply": rankings}
    else:
        # 일반 대화 처리
        safe_room = sanitize_filename(message.room)
        filename = f"{CHAT_DIR}/{safe_room}.json"
        history = []
        if os.path.exists(filename):
            async with aiofiles.open(filename, mode='r', encoding='utf-8') as f:
                async for line in f:
                    history.append(json.loads(line))
        history = history[-8:]
        
        gpt_messages = [
            {"role": "system", "content": SYSTEM_PROMPT + "\n\n운동을 기록하고 싶으시다면:\n" + \
                "1. '운동기록'으로 시작해서 운동 내용을 말씀해주세요. (예: '운동기록 30분 걸었어요')\n" + \
                "2. '운동통계'로 이번 달 운동 기록을 확인할 수 있습니다.\n" + \
                "3. '운동순위'로 전체 운동 순위를 확인할 수 있습니다."}
        ]
        
        learned_sentence = learned_sentences.get(message.room, "")
        if learned_sentence:
            gpt_messages[0]["content"] += f" 추가로, 다음 문장을 참고하세요: {learned_sentence}"
        
        for msg in history:
            role = "assistant" if msg["is_bot"] else "user"
            gpt_messages.append({"role": role, "content": msg["message"]})
        gpt_messages.append({"role": "user", "content": message.message})
        
        gpt_response = await call_gpt_api(gpt_messages, message.room)
    
    # 사용자 메시지와 봇 응답 모두 저장
    await save_message_internal(message.user_id, message.room, message.message, is_bot=False)
    await save_message_internal("봇", message.room, gpt_response, is_bot=True)
    
    return {"reply": gpt_response}

@app.get("/refresh_news")
async def refresh_news():
    try:
        await daily_news_summary()
        return {"status": "success", "message": "뉴스가 성공적으로 새로고침되었습니다"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/today_news")
async def get_today_news():
    news_summary = await read_news_summary()
    if not news_summary:
        news_summary = await daily_news_summary()
    
    random_news = {}
    for category in news_summary:
        if news_summary[category]:
            random_news[category] = random.choice(news_summary[category])
    
    return {"status": "success", "news_summary": random_news}

@app.get("/monthly_rankings/{room}")
async def monthly_rankings(room: str):
    logging.info(f"월간 랭킹 조회 요청: {room}")
    rankings = await get_monthly_rankings(room)
    logging.info(f"월간 랭킹 조회 응답: {rankings}")
    return {"rankings": rankings}

def is_valid_message(user_id: str, message: str) -> bool:
    if user_id == "꼼장선생":
        return False
    if message in ["사진을 보냈습니다.", "이모티콘을 보냈습니다."] or message.startswith("http"):
        return False
    return True

@app.get("/chat_stats/{room}")
@app.post("/chat_stats/{room}")
async def get_chat_stats(room: str):
    decoded_room = urllib.parse.unquote(room)
    safe_room = sanitize_filename(decoded_room)
    filename = f"{CHAT_DIR}/{safe_room}.json"
    if not os.path.exists(filename):
        return {"chat_count": [], "message_count": []}
    
    user_chat_count = {}
    user_message_length = {}
    
    async with aiofiles.open(filename, mode='r', encoding='utf-8') as f:
        async for line in f:
            try:
                msg = json.loads(line)
                if not msg["is_bot"] and is_valid_message(msg["user_id"], msg["message"]):
                    user_id = msg["user_id"]
                    user_chat_count[user_id] = user_chat_count.get(user_id, 0) + 1
                    user_message_length[user_id] = user_message_length.get(user_id, 0) + len(msg["message"])
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {line}")
                continue

    chat_count = sorted(user_chat_count.items(), key=lambda x: x[1], reverse=True)[:10]
    message_count = sorted(user_message_length.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "chat_count": [f"{i+1}. {user}: {count}" for i, (user, count) in enumerate(chat_count)],
        "message_count": [f"{i+1}. {user}: {length}" for i, (user, length) in enumerate(message_count)]
    }


@app.post("/recalculate_monthly_rankings")
async def recalculate_monthly_rankings_endpoint(room: str):
    try:
        from features.attend import recalculate_monthly_rankings
        result = await recalculate_monthly_rankings(room)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error in recalculate_monthly_rankings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class LearnMessage(BaseModel):
    room: str
    sentence: str

learned_sentences = {}

@app.post("/learn_sentence")
async def learn_sentence(message: LearnMessage):
    if len(message.sentence.split()) > 15:  # 대략 15단어 이하로 제한
        raise HTTPException(status_code=400, detail="문장이 너무 깁니다. 15단어 이하로 입력해주세요.")
    learned_sentences[message.room] = message.sentence
    return {"status": "success", "message": "문장이 학습되었습니다."}

@app.get("/get_learned_sentence/{room}")
async def get_learned_sentence(room: str):
    return {"sentence": learned_sentences.get(room, "")}



MAX_TOKENS = 4000

async def load_json_file(filename: str) -> str:
    try:
        async with aiofiles.open(filename, 'r', encoding='utf-8') as f:
            content = await f.read()
        return content
    except FileNotFoundError:
        logger.error(f"{filename} 파일을 찾을 수 없습니다.")
        return ""
    except json.JSONDecodeError:
        logger.error(f"{filename} 파일 파싱 실패")
        return ""
@app.get("/search")
async def search_endpoint(query: str):
    """
    웹 검색을 수행하는 엔드포인트
    
    Args:
        query: 검색할 쿼리 문자열
    """
    try:
        results = await search_web(query)
        if not results:
            return {"status": "error", "message": "검색 결과를 찾을 수 없습니다."}
            
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        logger.error(f"검색 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="검색 처리 중 오류가 발생했습니다.")
    

async def cleanup_old_chat_logs():
    """
    30일이 지난 채팅 로그를 삭제하는 함수
    """
    try:
        current_time = datetime.now()
        retention_days = 30  # 보관 기간 (일)
        cutoff_date = current_time - timedelta(days=retention_days)
        
        for filename in os.listdir(CHAT_DIR):
            if not filename.endswith('.json'):
                continue
                
            filepath = os.path.join(CHAT_DIR, filename)
            temp_filepath = filepath + '.temp'
            
            try:
                # 임시 파일에 30일 이내의 메시지만 저장
                async with aiofiles.open(filepath, 'r', encoding='utf-8') as old_file, \
                          aiofiles.open(temp_filepath, 'w', encoding='utf-8') as new_file:
                    async for line in old_file:
                        try:
                            message = json.loads(line)
                            message_date = datetime.fromisoformat(message['timestamp'])
                            if message_date > cutoff_date:
                                await new_file.write(line)
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.error(f"Error processing message in {filename}: {str(e)}")
                            continue
                
                # 원본 파일을 임시 파일로 교체
                os.replace(temp_filepath, filepath)
                logger.info(f"Cleaned up old messages from {filename}")
                
            except Exception as e:
                logger.error(f"Error cleaning up {filename}: {str(e)}")
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                    
    except Exception as e:
        logger.error(f"Error in cleanup_old_chat_logs: {str(e)}")

# startup_event 함수에 추가할 스케줄러 작업


scheduler = AsyncIOScheduler(timezone="Asia/Seoul", job_defaults={"misfire_grace_time": 60})

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(daily_news_summary, CronTrigger(hour=4, minute=0), id="daily_news_summary")
    scheduler.add_job(init_daily_attendance, CronTrigger(hour=0, minute=0), id="init_daily_attendance")
    scheduler.add_job(init_monthly_rankings, CronTrigger(day=1, hour=0, minute=0), id="init_monthly_rankings")
    scheduler.add_job(cleanup_old_chat_logs, CronTrigger(hour=3, minute=0), id="cleanup_old_chat_logs")
    scheduler.start()
    
    await init_daily_attendance()
    if datetime.now().day == 1:
        await init_monthly_rankings()


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

# 로그 디렉토리 생성
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 파일 핸들러 설정 (10MB 크기 제한, 최대 5개 파일)
file_handler = RotatingFileHandler(
    os.path.join(log_dir, "server.log"),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# 콘솔 핸들러 설정
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 포맷터 설정
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 핸들러 추가
logger.addHandler(file_handler)
logger.addHandler(console_handler)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)