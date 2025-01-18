from config import config
import logging
from datetime import datetime
from api_client import call_claude_api
from features.token_monitor import get_monthly_usage, predict_monthly_usage
from features.notifications import (
    check_character_birthday,
    check_shop_reset,
    check_stroking_time
)
from features.admin import is_admin, add_admin, remove_admin
from features.guide import save_guide, get_guide
from features.sites import save_site, get_site, get_site_list, delete_site
from features.chat_stats import get_user_stats, log_chat

logger = logging.getLogger(__name__)
ADMIN_ROOM = "프로젝트 아로나"

# 일반 채팅방용 도움말
HELP_MESSAGE = """🤖 아로나 봇 도움말
📌 기본 명령어
*도움말 - 이 도움말을 표시합니다
*관리자확인 - 현재 등록된 관리자 목록을 확인합니다
*토큰 - 토큰 사용량을 확인합니다
*생일 - 오늘의 생일 캐릭터를 확인합니다
*쓰담 - 쓰다듬기 알림을 확인합니다
*ping - 봇 상태를 확인합니다

[채팅 통계]
*통계 - 채팅방 전체 통계를 확인합니다
*통계 [사용자ID] - 특정 사용자의 통계를 확인합니다

[사이트/공략 관리]
*저장 [키워드] [URL] - 사이트/공략 주소를 저장합니다
*삭제 [키워드] - 저장된 사이트/공략을 삭제합니다
*목록 - 저장된 사이트/공략 목록을 확인합니다
*[키워드] - 저장된 사이트/공략을 검색합니다

💡 예시
- *통계
- *통계 user123
- *저장 미래시 https://example.com
- *목록
- *사이트 미래시
- *삭제 미래시
"""

# 관리자 채팅방용 추가 도움말
ADMIN_HELP = """
📌 관리자 전용 명령어
[프롬프트 관리]
*프롬프트 목록 - 저장된 프롬프트 목록
*프롬프트 보기 - 현재 프롬프트 내용
*프롬프트 추가 [이름] [내용] - 새 프롬프트 추가
*프롬프트 사용 [이름] - 프롬프트 변경
*프롬프트 수정 [이름] [내용] - 프롬프트 수정

[Temperature 관리]
*temperature - 현재 temperature 확인
*temperature [값] - temperature 변경 (0.0-1.0)

[관리자 관리]
*관리자추가 [사용자ID] - 관리자 추가
*관리자삭제 [사용자ID] - 관리자 삭제

💡 관리자 명령어 예시
- *프롬프트 목록
- *temperature 0.3
- *관리자추가 user123
"""

async def handle_commands(command: str, message, room: str):
    """채팅 명령어를 처리합니다."""
    try:
        # 채팅 로그 기록
        await log_chat(message.user_id, room, message.message)
        
        # '*'로 시작하지 않는 메시지는 무시
        if not message.message.startswith("*"):
            return {"response": None}
            
        # '*' 제거
        command = message.message[1:]
        parts = command.split()
        cmd = parts[0].lower()

        # 명령어 처리
        if cmd == "도움말":
            if room == ADMIN_ROOM:
                return {"response": HELP_MESSAGE + ADMIN_HELP}
            return {"response": HELP_MESSAGE}
            
        elif cmd == "통계":
            user_id = parts[1] if len(parts) > 1 else None
            result = await get_user_stats(room, user_id)
            return {"response": result["message"]}
            
        elif cmd == "목록":
            result = await get_site_list()
            if not result:  # 빈 리스트인 경우
                return {"response": "저장된 사이트가 없습니다."}
                
            try:
                sites_text = "\n".join([
                    f"• {site['keyword']}: {site['url']}"
                    for site in result  # result 자체가 리스트이므로 직접 사용
                ])
                return {"response": f"📚 저장된 사이트 목록\n{sites_text}\n\n💡 검색방법: *사이트 [키워드]"}
            except Exception as e:
                logger.error(f"사이트 목록 처리 중 오류: {str(e)}")
                return {"response": "사이트 목록을 불러오는 중 오류가 발생했습니다."}
            
        elif cmd == "저장":
            if len(parts) < 3:
                return {"response": "사용법: *저장 [키워드] [URL]"}
            
            keyword = parts[1]
            url = parts[2]
            result = await save_site(keyword, url, message.user_id)
            return {"response": result["message"]}
            
        elif cmd == "사이트":
            if len(parts) < 2:
                return {"response": "검색할 키워드를 입력해주세요.\n사용법: *사이트 [키워드]"}
            
            keyword = parts[1]
            result = await get_site(keyword)
            if result["found"]:
                site_info = result["url"]
                return {"response": f"URL: {site_info['url']}\n"
                                  f"등록자: {site_info['user_id']}\n"
                                  f"최종수정: {datetime.fromisoformat(site_info['updated_at']).strftime('%Y-%m-%d %H:%M')}"}
            return {"response": result["message"]}
            
        # 명령어가 아닌 경우 Claude API로 전달
        message.message = command  # '*'가 제거된 메시지 사용
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