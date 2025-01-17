from collections import defaultdict
from datetime import datetime, timedelta
import json
import os
import aiofiles
from typing import Dict, List

STATS_FILE = "data/chat_stats.json"

# 디렉토리 및 파일 생성
os.makedirs("data", exist_ok=True)
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

async def log_chat(user_id: str, room: str, message: str):
    """채팅 로그 기록"""
    try:
        async with aiofiles.open(STATS_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            stats = json.loads(content) if content else {}
        
        if room not in stats:
            stats[room] = {}
        if user_id not in stats[room]:
            stats[room][user_id] = {
                "message_count": 0,
                "last_active": "",
                "first_seen": datetime.now().isoformat()
            }
        
        stats[room][user_id]["message_count"] += 1
        stats[room][user_id]["last_active"] = datetime.now().isoformat()
        
        async with aiofiles.open(STATS_FILE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(stats, ensure_ascii=False, indent=2))
            
    except Exception as e:
        print(f"채팅 로그 기록 중 오류: {str(e)}")

async def get_user_stats(room: str, user_id: str = None) -> Dict:
    """사용자 통계 조회"""
    try:
        async with aiofiles.open(STATS_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            stats = json.loads(content) if content else {}
        
        if room not in stats:
            return {"status": "error", "message": "해당 채팅방의 통계가 없습니다."}
            
        if user_id:
            if user_id not in stats[room]:
                return {"status": "error", "message": "해당 사용자의 통계가 없습니다."}
            
            user_stats = stats[room][user_id]
            first_seen = datetime.fromisoformat(user_stats["first_seen"])
            last_active = datetime.fromisoformat(user_stats["last_active"])
            days_active = (last_active - first_seen).days + 1
            
            return {
                "status": "success",
                "message": f"=== {user_id}님의 채팅 통계 ===\n"
                          f"총 메시지: {user_stats['message_count']:,}개\n"
                          f"하루 평균: {user_stats['message_count']/days_active:.1f}개\n"
                          f"첫 활동일: {first_seen.strftime('%Y-%m-%d')}\n"
                          f"마지막 활동: {last_active.strftime('%Y-%m-%d %H:%M')}"
            }
        
        # 전체 통계 수정
        # 메시지 수로 정렬된 사용자 목록 생성
        sorted_users = sorted(
            stats[room].items(),
            key=lambda x: x[1]["message_count"],
            reverse=True
        )
        
        total_messages = sum(u[1]["message_count"] for u in sorted_users)
        active_users = len(sorted_users)
        
        # 상위 10명의 통계 생성
        top_users = "\n".join(
            f"{i+1}위: {user[0]} ({user[1]['message_count']:,}개)"
            for i, user in enumerate(sorted_users[:10])
        )
        
        return {
            "status": "success",
            "message": f"=== 채팅방 전체 통계 ===\n"
                      f"총 메시지: {total_messages:,}개\n"
                      f"활성 사용자: {active_users}명\n\n"
                      f"📊 채팅 순위 (상위 10명)\n"
                      f"{top_users}"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"통계 조회 중 오류: {str(e)}"} 