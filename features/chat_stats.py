from collections import defaultdict
from datetime import datetime, timedelta
import json
import os
import aiofiles
from typing import Dict, List
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# 파일 경로 설정
CHAT_LOGS_FILE = "data/chat_logs.json"

# 디렉토리 및 파일 생성
os.makedirs("data", exist_ok=True)
if not os.path.exists(CHAT_LOGS_FILE):
    with open(CHAT_LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

async def log_chat(user_id: str, room: str, message: str):
    """채팅 로그 기록"""
    try:
        async with aiofiles.open(CHAT_LOGS_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            logs = json.loads(content) if content else {}
        
        if room not in logs:
            logs[room] = {}
        if user_id not in logs[room]:
            logs[room][user_id] = []
        
        logs[room][user_id].append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        async with aiofiles.open(CHAT_LOGS_FILE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(logs, ensure_ascii=False, indent=2))
            
    except Exception as e:
        logger.error(f"채팅 로그 기록 중 오류: {str(e)}")

async def get_user_stats(room: str, user_id: str = None) -> Dict[str, str]:
    """채팅 통계를 조회합니다."""
    try:
        async with aiofiles.open(CHAT_LOGS_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            logs = json.loads(content) if content else {}
            
        if room not in logs:
            return {"message": "해당 채팅방의 기록이 없습니다."}
            
        room_logs = logs[room]
        
        if user_id:  # 특정 사용자 통계
            if user_id not in room_logs:
                return {"message": f"해당 사용자({user_id})의 기록이 없습니다."}
                
            user_messages = room_logs[user_id]
            message_count = len(user_messages)
            if message_count == 0:
                return {"message": f"해당 사용자({user_id})의 기록이 없습니다."}
                
            return {
                "message": f"📊 {user_id}님의 채팅 통계\n"
                          f"총 메시지 수: {message_count}개"
            }
            
        else:  # 전체 통계
            total_messages = sum(len(msgs) for msgs in room_logs.values())
            user_count = len(room_logs)
            
            if total_messages == 0:
                return {"message": "아직 채팅 기록이 없습니다."}
                
            # 상위 5명의 사용자 추출
            top_users = sorted(
                [(user, len(msgs)) for user, msgs in room_logs.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            top_users_str = "\n".join(
                f"{i+1}. {user}: {count}개"
                for i, (user, count) in enumerate(top_users)
            )
            
            return {
                "message": f"📊 채팅방 전체 통계\n"
                          f"총 메시지 수: {total_messages}개\n"
                          f"참여자 수: {user_count}명\n\n"
                          f"🏆 가장 많이 채팅한 사용자 TOP 5\n{top_users_str}"
            }
            
    except Exception as e:
        logger.error(f"채팅 통계 조회 중 오류: {str(e)}")
        return {"message": "통계를 조회하는 중에 오류가 발생했습니다."} 