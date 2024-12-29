import json
import os
from datetime import datetime, timezone, timedelta

async def process_attendance(user_id: str, room: str):
    """출석 처리"""
    now = datetime.now(timezone(timedelta(hours=9)))
    attendance_data = {
        "user_id": user_id,
        "timestamp": now.isoformat(),
        "room": room
    }
    
    # 출석 데이터 저장
    return {"status": "success", "message": "출석이 처리되었습니다."}

async def get_monthly_rankings(room: str):
    """월간 랭킹 조회"""
    try:
        with open(f'rankings/{room}_rankings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"rankings": []}

async def init_daily_attendance():
    """일일 출석 초기화"""
    # 매일 자정에 실행될 초기화 로직
    pass

async def init_monthly_rankings():
    """월간 랭킹 초기화"""
    # 매월 1일에 실행될 초기화 로직
    pass 