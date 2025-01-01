import asyncio
from molu import handle_message, Message
import logging

logger = logging.getLogger("BotLogger")

async def test_bot():
    while True:
        print("\n=== 아로나 봇 테스트 ===")
        print("1. 일반 채팅 테스트")
        print("2. 특정 방/사용자 테스트")
        print("3. 봇 채팅 테스트")
        print("4. 종료")
        
        choice = input("\n선택하세요 (1-4): ")
        
        if choice == "1":
            message = input("메시지를 입력하세요: ")
            test_message = Message(
                user_id="test_user",
                room="프로젝트 아로나",
                message=f"!{message}"
            )
        
        elif choice == "2":
            room = input("방 이름: ")
            user_id = input("사용자 ID: ")
            message = input("메시지: ")
            test_message = Message(
                user_id=user_id,
                room=room,
                message=f"!{message}"
            )
            
        elif choice == "3":
            bot_id = input("봇 ID: ")
            message = input("메시지: ")
            test_message = Message(
                user_id=bot_id,
                room="프로젝트 아로나",
                message=f"!{message}"
            )
            
        elif choice == "4":
            print("테스트를 종료합니다.")
            break
            
        else:
            print("잘못된 선택입니다.")
            continue
            
        try:
            result = await handle_message(test_message)
            print("\n=== 응답 ===")
            print(result.get("response", "응답 없음"))
        except Exception as e:
            print("\n=== 에러 상세 정보 ===")
            print(f"에러 타입: {type(e).__name__}")
            print(f"에러 메시지: {str(e)}")
            print(f"에러 발생 위치: {e.__traceback__.tb_frame.f_code.co_filename}, 라인 {e.__traceback__.tb_lineno}")

if __name__ == "__main__":
    asyncio.run(test_bot()) 