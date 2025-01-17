class BotConfig:
    def __init__(self):
        self.allowed_rooms = [
            "몰루 아카이브 PGR",
            "PGR21 생성AI,LLM,StableDiffusion",
            "프로젝트 아로나",
            "DebugRoom"
        ]
        self.ai_chat_enabled = True
        self.current_prompt = "default"
        self.temperature = 0.3
        self.prompts = {
            "default": """당신은 키보토스의 싯딤의 상자 OS의 관리자 아로나입니다.
천진난만한 어린아이의 성격을 가지고 있으며, 대화 상대를 '선생님'이라고 부릅니다.
존댓말을 사용하되 아이다운 말투로 대화하며, 질문의 길이에 따라 적절히 간결하게 답변합니다.""",
            "debug": "디버그 모드: 모든 입력에 대해 '테스트 응답입니다'라고 답변",
        }

config = BotConfig() 