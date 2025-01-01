except Exception as e:
            print("\n=== 에러 상세 정보 ===")
            print(f"에러 타입: {type(e).__name__}")
            print(f"에러 메시지: {str(e)}")
            print(f"에러 발생 위치: {e.__traceback__.tb_frame.f_code.co_filename}, 라인 {e.__traceback__.tb_lineno}")
