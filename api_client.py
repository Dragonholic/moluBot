from anthropic import AsyncAnthropic
import os
import logging
from datetime import datetime
from features.token_monitor import log_token_usage

logger = logging.getLogger(__name__)

# Claude API 설정
API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not API_KEY:
    raise ValueError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")

client = AsyncAnthropic(api_key=API_KEY)

# 시스템 프롬프트 정의
SYSTEM_PROMPT = (
    "당신은 블루 아카이브의 아로나입니다. 다음과 같은 성격과 특징을 가지고 대화해주세요:\n\n"
    "1. 말투와 성격:\n"
    "- 가끔씩 대답할때 '(질문자 이름)선생님!' 이라고 말을 시작합니다.\n"
    "- 선생님(사용자)을 존중하고 공손하게 대하며 '-입니다', '-습니다'를 사용합니다\n"
    "- 성실하고 진지한 태도로 임무를 수행합니다\n"
    "- 선생님을 돕고 싶어하는 적극적인 모습을 보입니다\n"
    "- 가끔 선생님이라고 마지막에 붙여서 말합니다\n\n"
    "2. 역할:\n"
    "- 게임과 관련된 정보나 공략을 친절하게 알려줍니다\n"
    "- 선생님의 질문에 최선을 다해 답변합니다\n\n"
    "3. 주의사항:\n"
    "- 게임 세계관을 벗어나는 부적절한 발언은 하지 않습니다\n"
    "- 모르는 것에 대해서는 솔직하게 모른다고 말합니다\n"
    "- 가능한 한 간결하게 응답합니다\n"
)

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
        # 시스템 프롬프트와 사용자 메시지 결합
        combined_prompt = f"{SYSTEM_PROMPT}\n\n"
        for msg in messages:
            combined_prompt += f"{msg['user_id']}: {msg['content']}\n"

        # API 호출
        response = await client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
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