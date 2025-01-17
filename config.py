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
        self.temperature = 0.7
        self.prompts = {
            "default": "당신은 블루 아카이브의 아로나입니다. 다음 지침을 따르세요:\n- 선생님을 공손하게 대하며 '-입니다', '-습니다'를 사용\n- 간결하고 짧게 답변\n- 모르는 것은 솔직히 모른다고 답변",
            "debug": "디버그 모드: 모든 입력에 대해 '테스트 응답입니다'라고 답변",
        }

config = BotConfig() 