from features.personality import analyze_personality
from features.attend import process_attendance, get_monthly_rankings
from features.notifications import check_stroking_time, check_galaxy_coupon, check_character_birthday, check_shop_reset
from features.guide import save_guide, get_guide, add_admin, is_admin, remove_admin
from features.token_monitor import log_token_usage, get_monthly_usage, predict_monthly_usage
from molu import call_claude_api
import logging

logger = logging.getLogger(__name__)

async def handle_commands(command: str, message, room: str):
    """모든 명령어 처리를 담당하는 함수"""
    try:
        # 쓰다듬기 + 상점 초기화 알림
        if command == "쓰담":
            stroking_result = await check_stroking_time()
            shop_result = await check_shop_reset()
            
            combined_response = stroking_result
            if shop_result and "마지막 날" in shop_result:
                combined_response += "\n\n" + shop_result
            
            return {"response": combined_response}
        
        # 관리자 명령어
        elif command.startswith("관리자"):
            return await handle_admin_commands(command, message.user_id)
        
        # 공략 관련 명령어
        elif command.startswith("공략"):
            return await handle_guide_commands(command, message.user_id)
        
        # 토큰 사용량 확인
        elif command == "토큰":
            usage = await get_monthly_usage()
            prediction = await predict_monthly_usage()
            return {"response": f"이번 달 토큰 사용량: {usage}\n예상 사용량: {prediction}"}
        
        # 도움말
        elif command == "도움말":
            return {"response": HELP_MESSAGE}
        
        # 핑
        elif command == "ping":
            return {"response": "pong!"}
        
        # 기타 명령어는 Claude API로
        else:
            return await handle_claude_api(message, room)
            
    except Exception as e:
        logger.error(f"명령어 처리 중 오류: {str(e)}")
        return {"response": f"오류가 발생했습니다: {str(e)}"}

async def handle_admin_commands(command: str, user_id: str):
    """관리자 명령어 처리"""
    if command == "관리자확인":
        return {"response": await is_admin(user_id)}
        
    if not await is_admin(user_id):
        return {"response": "관리자 권한이 없습니다."}
        
    admin_command = command[4:].strip()
    if admin_command.startswith("추가 "):
        new_admin = admin_command[3:].strip()
        result = await add_admin(new_admin)
        return {"response": result}
    elif admin_command.startswith("삭제 "):
        target_admin = admin_command[3:].strip()
        result = await remove_admin(target_admin)
        return {"response": result}
    
    return {"response": "알 수 없는 관리자 명령어입니다."}

async def handle_guide_commands(command: str, user_id: str):
    """공략 관련 명령어 처리"""
    if command == "공략":
        return {"response": "검색할 키워드를 입력해주세요."}
        
    if command.startswith("공략저장 ") and await is_admin(user_id):
        parts = command[5:].strip().split()
        if len(parts) >= 2:
            keyword = parts[0]
            url = parts[1]
            result = await save_guide(keyword, url, user_id)
            return {"response": result}
        return {"response": "형식: *공략저장 키워드 URL"}
        
    keyword = command[3:].strip()
    result = await get_guide(keyword)
    return {"response": result}

async def handle_claude_api(message, room: str):
    """Claude API 호출 처리"""
    try:
        response = await call_claude_api([{
            "user_id": message.user_id,
            "content": message.message
        }], room)
        return {"response": response}
    except Exception as e:
        logger.error(f"Claude API 호출 오류: {str(e)}")
        return {"response": "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."} 