from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

class TestMessage(BaseModel):
    message: str
    room: Optional[str] = "테스트방"
    user_id: Optional[str] = "테스트유저"

@router.get("/ping")
async def ping():
    """서버 연결 테스트용 엔드포인트"""
    logger.info("ping 요청 받음")
    return {"response": "pong"}

@router.get("/test")
async def test():
    """서버 상태 테스트용 엔드포인트"""
    return {"status": "success", "message": "서버가 정상적으로 동작 중입니다!"}

@router.post("/test_echo")
async def test_echo(message: TestMessage):
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

@router.post("/test_notification/{type}")
async def test_notification(type: str):
    """알림 기능 테스트용 엔드포인트"""
    if type == "stroking":
        from features.notifications import check_stroking_time
        await check_stroking_time()
        return {"message": "쓰다듬기 알림 테스트 완료"}
    elif type == "galaxy":
        from features.notifications import check_galaxy_coupon
        await check_galaxy_coupon()
        return {"message": "겔럭시 쿠폰 알림 테스트 완료"}
    elif type == "birthday":
        from features.notifications import check_character_birthday
        await check_character_birthday()
        return {"message": "생일 알림 테스트 완료"}
    elif type == "shop":
        from features.notifications import check_shop_reset
        await check_shop_reset()
        return {"message": "상점 초기화 알림 테스트 완료"}
    else:
        raise HTTPException(status_code=400, detail="잘못된 알림 유형")

@router.get("/test_chat/{message}")
async def test_chat(message: str):
    """채팅 기능 테스트용 엔드포인트"""
    from molu import Message, handle_message
    test_message = Message(
        user_id="test_user",
        room="프로젝트 아로나",
        message=f"*{message}"
    )
    result = await handle_message(test_message)
    return result 