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

logger = logging.getLogger(__name__)
ADMIN_ROOM = "프로젝트 아로나"

HELP_MESSAGE = """🤖 아로나 봇 도움말
📌 기본 명령어
*도움말 - 이 도움말을 표시합니다
*공략 [키워드] - 게임 공략을 검색합니다
*관리자확인 - 현재 등록된 관리자 목록을 확인합니다
*통계 [사용자ID] - 채팅방 통계를 확인합니다 (사용자ID 생략 가능)
*토큰 - 토큰 사용량을 확인합니다
*사이트저장 [키워드] [URL] - 사이트 주소를 저장합니다
*사이트목록 - 저장된 사이트 목록을 확인합니다
*[키워드] - 저장된 사이트 주소를 빠르게 확인합니다 (예: *미래시)
💡 예시
- *공략 호시노
- *사이트저장 미래시 [사이트 주소]
- *사이트목록
"""

async def handle_commands(command: str, message, room: str):
    """채팅 명령어를 처리합니다."""
    try:
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "도움말":
            base_help = HELP_MESSAGE
            
            if room == ADMIN_ROOM:
                admin_help = """\n[프롬프트 관리]
*프롬프트 목록 - 저장된 프롬프트 목록
*프롬프트 보기 - 현재 프롬프트 내용
*프롬프트 추가 [이름] [내용] - 새 프롬프트 추가
*프롬프트 사용 [이름] - 프롬프트 변경
*프롬프트 수정 [이름] [내용] - 프롬프트 수정
*temperature - 현재 temperature 확인
*temperature [값] - temperature 변경 (0.0-1.0)
📌 기본 명령어
*도움말 - 이 도움말을 표시합니다
*공략 [키워드] - 게임 공략을 검색합니다
*관리자확인 - 현재 등록된 관리자 목록을 확인합니다
*통계 [사용자ID] - 채팅방 통계를 확인합니다 (사용자ID 생략 가능)
*토큰 - 토큰 사용량을 확인합니다
*사이트저장 [키워드] [URL] - 사이트 주소를 저장합니다
*사이트목록 - 저장된 사이트 목록을 확인합니다
*[키워드] - 저장된 사이트 주소를 빠르게 확인합니다 (예: *미래시)
💡 예시
- *공략 호시노
- *사이트저장 미래시 [사이트 주소]
- *사이트목록"""
                return {"response": base_help + admin_help}
            return {"response": base_help}

        elif cmd == "프롬프트":
            if room != ADMIN_ROOM:
                return {"response": "프롬프트 관리는 관리자 방에서만 가능합니다."}
            
            if len(parts) < 2:
                return {"response": "사용법: *프롬프트 [목록/보기/추가/사용/수정]"}
            
            subcmd = parts[1]
            
            if subcmd == "목록":
                prompts = "\n".join([
                    f"{'* ' if name == config.current_prompt else '  '}{name}"
                    for name in config.prompts
                ])
                return {"response": f"=== 프롬프트 목록 ===\n{prompts}"}
            
            elif subcmd == "보기":
                current = config.current_prompt
                content = config.prompts[current]
                return {"response": f"=== 현재 프롬프트 ({current}) ===\n{content}"}
            
            elif subcmd == "추가" and len(parts) >= 4:
                name = parts[2]
                content = " ".join(parts[3:])
                if name in config.prompts:
                    return {"response": "이미 존재하는 프롬프트 이름입니다."}
                config.prompts[name] = content
                return {"response": f"프롬프트 '{name}' 추가됨"}
            
            elif subcmd == "사용" and len(parts) >= 3:
                name = parts[2]
                if name not in config.prompts:
                    return {"response": "존재하지 않는 프롬프트입니다."}
                config.current_prompt = name
                return {"response": f"프롬프트를 '{name}'으로 변경했습니다."}
            
            elif subcmd == "수정" and len(parts) >= 4:
                name = parts[2]
                content = " ".join(parts[3:])
                if name not in config.prompts:
                    return {"response": "존재하지 않는 프롬프트입니다."}
                config.prompts[name] = content
                return {"response": f"프롬프트 '{name}' 수정됨"}

        elif cmd == "생일":
            # 생일 알림 처리
            response = await check_character_birthday([room])
            # 상점 초기화 알림 추가
            shop_notice = await check_shop_reset()
            if shop_notice:
                response = f"{response}\n\n{shop_notice}" if response else shop_notice
            return {"response": response}
            
        elif cmd == "쓰담":
            # 쓰다듬기 알림 처리
            response = await check_stroking_time([room])
            # 상점 초기화 알림 추가
            shop_notice = await check_shop_reset()
            if shop_notice:
                response = f"{response}\n\n{shop_notice}" if response else shop_notice
            return {"response": response}
            
        # 관리자 명령어
        elif cmd.startswith("관리자"):
            return await handle_admin_commands(command, message.user_id)
        
        # 공략 관련 명령어
        elif cmd.startswith("공략"):
            return await handle_guide_commands(command, message.user_id)
        
        # 토큰 사용량 확인
        elif cmd == "토큰":
            usage = await get_monthly_usage()
            prediction = await predict_monthly_usage()
            return {"response": f"이번 달 토큰 사용량: {usage}\n예상 사용량: {prediction}"}
        
        # 핑
        elif cmd == "ping":
            return {"response": "pong!"}
        
        elif cmd == "temperature":
            if room != ADMIN_ROOM:
                return {"response": "temperature 관리는 관리자 방에서만 가능합니다."}
            
            if len(parts) == 1:
                return {"response": f"현재 temperature: {config.temperature}\n사용법: *temperature [0.0-1.0]"}
            
            try:
                new_temp = float(parts[1])
                if 0.0 <= new_temp <= 1.0:
                    config.temperature = new_temp
                    return {"response": f"temperature가 {new_temp}로 변경되었습니다."}
                else:
                    return {"response": "temperature는 0.0에서 1.0 사이의 값이어야 합니다."}
            except ValueError:
                return {"response": "올바른 숫자를 입력해주세요."}
        
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