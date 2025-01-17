import logging

# 로거 설정
logger = logging.getLogger("NotificationLogger")
logger.setLevel(logging.DEBUG)

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

# 알림을 받을 방 목록 설정
NOTIFICATION_ROOMS = {
    "stroking": ["몰루 아카이브 PGR"],
    "galaxy": ["몰루 아카이브 PGR"],
    "birthday": ["몰루 아카이브 PGR"],
    "shop": ["몰루 아카이브 PGR"]
}

# 캐릭터 생일 데이터 (월, 일, 이름)
CHARACTER_BIRTHDAYS = [
    (1, 2, "호시노"),
    (1, 3, "사야"),
    (1, 3, "하나코"),
    (1, 5, "코타마"),
    (1, 6, "세리나"),
    (1, 7, "미야코"),
    (1, 8, "히요리"),
    (1, 13, "미사키"),
    (1, 20, "아츠코"),
    (1, 22, "시구레"),
    (1, 30, "아이리"),
    (2, 2, "카린"),
    (2, 3, "츠바키"),
    (2, 5, "슌"),
    (2, 14, "코유키"),
    (2, 19, "히나"),
    (2, 19, "키사키"),
    (2, 20, "노도카"),
    (2, 22, "미치루"),
    (2, 24, "키라라"),
    (3, 1, "하루나"),
    (3, 3, "레이죠"),
    (3, 5, "루미"),
    (3, 12, "아루"),
    (3, 14, "유우카"),
    (3, 15, "미모리"),
    (3, 17, "카요코"),
    (3, 19, "마코토"),
    (3, 24, "아스나"),
    (3, 25, "아리스"),
    (4, 1, "아카네"),
    (4, 2, "히비키"),
    (4, 3, "와카모"),
    (4, 5, "츠쿠요"),
    (4, 7, "세나"),
    (4, 9, "사키"),
    (4, 10, "사츠키"),
    (4, 13, "노아"),
    (4, 14, "이부키"),
    (4, 16, "코하루"),
    (4, 19, "하레"),
    (4, 23, "우이"),
    (4, 25, "메구"),
    (4, 26, "치히로"),
    (4, 30, "후우카"),
    (5, 1, "에이미"),
    (5, 2, "미사카 미코토"),
    (5, 8, "미카"),
    (5, 11, "이즈미"),
    (5, 12, "하나에"),
    (5, 13, "하루카"),
    (5, 16, "시로코"),
    (5, 16, "시로코*테러"),
    (5, 17, "히나타"),
    (5, 24, "카스미"),
    (5, 31, "레이사"),
    (6, 1, "코코나"),
    (6, 5, "마시로"),
    (6, 16, "유카리"),
    (6, 24, "츠루기"),
    (6, 25, "세리카"),
    (7, 1, "우미카"),
    (7, 4, "나기사"),
    (7, 7, "시즈코"),
    (7, 9, "카에데"),
    (7, 12, "미유"),
    (7, 13, "치세"),
    (7, 14, "미노리"),
    (7, 23, "렌게"),
    (7, 29, "무츠키"),
    (8, 1, "마키"),
    (8, 5, "카즈사"),
    (8, 7, "모미지"),
    (8, 8, "키쿄"),
    (8, 12, "유즈"),
    (8, 16, "토키"),
    (8, 17, "네루"),
    (8, 20, "스미레"),
    (8, 22, "치나츠"),
    (8, 29, "요시미"),
    (8, 31, "스즈미"),
    (8, 31, "하츠네 미쿠"),
    (9, 1, "노노미"),
    (9, 3, "사오리"),
    (9, 7, "칸나"),
    (9, 9, "미나"),
    (9, 12, "마리"),
    (9, 13, "모에"),
    (9, 22, "치아키"),
    (10, 4, "사쿠라코"),
    (10, 9, "카호"),
    (10, 20, "주리"),
    (10, 21, "후부키"),
    (10, 22, "키리노"),
    (10, 27, "체리노"),
    (11, 3, "피나"),
    (11, 4, "마리나"),
    (11, 8, "이오리"),
    (11, 10, "토모에"),
    (11, 11, "이치카"),
    (11, 12, "아야네"),
    (11, 13, "우타하"),
    (11, 16, "이로하"),
    (11, 23, "미네"),
    (11, 27, "히후미"),
    (11, 30, "시미코"),
    (12, 4, "나츠"),
    (12, 8, "미도리"),
    (12, 8, "모모이"),
    (12, 9, "아카리"),
    (12, 10, "히마리"),
    (12, 12, "하스미"),
    (12, 16, "이즈나"),
    (12, 21, "메루"),
    (12, 22, "아코"),
    (12, 26, "아즈사"),
    (12, 27, "준코"),
    (12, 31, "코토리")

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

async def check_stroking_time(rooms: list = None) -> str:
    """쓰다듬기 알림 확인"""
    try:
        now = datetime.now()
        next_time = now.replace(hour=19, minute=0, second=0, microsecond=0)
        
        if now.hour >= 19:
            next_time += timedelta(days=1)
            
        time_left = next_time - now
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        if hours > 0:
            return f"선생님! 다음 쓰다듬기까지 {hours}시간 {minutes}분 남았어요~"
        else:
            return f"선생님! 다음 쓰다듬기까지 {minutes}분 남았어요~"
            
    except Exception as e:
        logger.error(f"쓰다듬기 시간 확인 중 오류: {str(e)}")
        return "죄송해요 선생님... 쓰다듬기 시간을 확인하다가 문제가 생겼어요."

async def check_galaxy_coupon(rooms: List[str]):
    """
    매주 월/금 10:58에 겔럭시 쿠폰 확인 알림
    """
    message = "선생님 겔럭시 쿠폰 확인하세요! "
    for room in rooms:
        await send_notification(message, room)

async def check_character_birthday(rooms: List[str]) -> str:
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
        message = f"선생님! 오늘은 {characters} 의 생일이에요! 축하해주세요~ 🎂"
        # 알림 전송
        for room in rooms:
            await send_notification(message, room)
        return message
    else:
        return "선생님, 오늘은 생일인 학생이 없네요!"

async def check_shop_reset():
    """매월 마지막 날 상점 초기화 알림"""
    try:
        current_time = datetime.now(KST)
        # 다음 날이 다음 달의 1일인지 확인
        next_day = current_time + timedelta(days=1)
        
        if next_day.day == 1:  # 오늘이 이번 달의 마지막 날
            message = (
                "📢 선생님! 오늘은 이번 달의 마지막 날입니다!\n\n"
                "🏪 상점 초기화 전 확인하실 것:\n"
                "- 총력전/대결전 상점\n"
                "- 종합전술시험 상점\n"
                "- 숙련증서 상점\n"
                "상점 초기화 전에 모든 재화를 사용하는 것을 잊지 마세요!"
            )
            
            # 알림 전송
            for room in NOTIFICATION_ROOMS["shop"]:
                await send_notification(room, message)
                
    except Exception as e:
        logger.error(f"상점 초기화 알림 오류: {str(e)}") 