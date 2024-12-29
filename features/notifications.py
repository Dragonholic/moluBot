from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

# 캐릭터 생일 데이터 (월, 일, 이름)
CHARACTER_BIRTHDAYS = [
    (1, 1, "스즈미 마리나"),
    (1, 15, "시로코"),
    (2, 1, "호시노"),
    (2, 14, "아루"),
    # ... 다른 캐릭터들의 생일 정보 추가
    #TODO: 캐릭터 생일 정보 추가
]

async def send_notification(message: str, room: str) -> Dict[str, Any]:
    """
    지정된 방에 알림 메시지를 보내는 함수
    실제 구현에서는 봇 API를 통해 메시지를 전송해야 함
    """
    try:
        # 여기에 실제 메시지 전송 로직 구현
        # 예: 카카오톡 봇 API 호출 등
        return {
            "status": "success",
            "message": message,
            "room": room,
            "timestamp": datetime.now(KST).isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

async def check_stroking_time():
    """
    매일 16시에 쓰다듬기 알림
    """
    message = "🐱 냥이 쓰다듬기 시간이에요! 게임에 접속해서 냥이를 쓰다듬어주세요~ 😊"
    # 여기에 알림을 보낼 방 목록을 설정하거나 DB에서 가져옴
    rooms = ["방1", "방2"]  # 예시
    
    for room in rooms:
        await send_notification(message, room)

async def check_galaxy_coupon():
    """
    매주 월/금 10:58에 겔럭시 쿠폰 확인 알림
    """
    message = "🎮 겔럭시 쿠폰 확인하세요! 새로운 쿠폰이 나왔을지도...? 💎"
    rooms = ["방1", "방2"]  # 예시
    
    for room in rooms:
        await send_notification(message, room)

async def check_character_birthday():
    """
    오늘이 생일인 캐릭터 확인 및 알림
    """
    now = datetime.now(KST)
    today_month = now.month
    today_day = now.day
    
    birthday_characters = [
        name for month, day, name in CHARACTER_BIRTHDAYS
        if month == today_month and day == today_day
    ]
    
    if birthday_characters:
        characters = ", ".join(birthday_characters)
        message = f"🎂 오늘은 {characters} 선생님의 생일입니다! 축하해주세요~ 🎉"
        rooms = ["방1", "방2"]  # 알림을 보낼 방 목록
        
        for room in rooms:
            await send_notification(message, room) 