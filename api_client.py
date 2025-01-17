from anthropic import AsyncAnthropic
import os
import logging
from datetime import datetime
from features.token_monitor import log_token_usage
from dotenv import load_dotenv
from config import config

# .env 파일 로드
load_dotenv()

logger = logging.getLogger(__name__)

# Claude API 설정
API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not API_KEY:
    raise ValueError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")

client = AsyncAnthropic(api_key=API_KEY)

async def call_claude_api(messages, room: str, task: str = "chat"):
    """
    Claude API를 호출하여 응답을 받아옵니다.
    
    Args:
        messages (list): 대화 메시지 목록
        room (str): 채팅방 이름
        task (str): 작업 유형 (기본값: "chat")
    
    Returns:
        str: Claude API의 응답 텍스트
    """
    try:
        # 현재 설정된 프롬프트 사용
        system_prompt = config.prompts[config.current_prompt]
        
        # 시스템 프롬프트와 사용자 메시지 결합
        combined_prompt = f"{system_prompt}\n\n"
        for msg in messages:
            combined_prompt += f"{msg['user_id']}: {msg['content']}\n"

        # 토큰 제한 추가
        max_tokens = 250  # 응답 토큰 수 제한
        
        # API 호출
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            temperature=config.temperature,
            messages=[{
                "role": "user",
                "content": combined_prompt
            }]
        )

        # 토큰 사용량 기록
        await log_token_usage(
            room=room,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            timestamp=datetime.now(),
            task=task
        )

        return response.content[0].text

    except Exception as e:
        logger.error(f"Claude API 호출 중 오류 발생: {str(e)}")
        raise