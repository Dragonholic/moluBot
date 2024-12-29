import os
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Any

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

def get_user_messages(room: str, user_id: str = None) -> List[Dict[str, Any]]:
    """특정 방의 (특정 사용자의) 메시지 기록을 가져옴"""
    chat_dir = "chat_logs"
    messages = []
    
    try:
        # 채팅방 로그 파일 경로
        room_file = os.path.join(chat_dir, f"{sanitize_filename(room)}.json")
        
        if not os.path.exists(room_file):
            return messages
            
        with open(room_file, 'r', encoding='utf-8') as f:
            chat_logs = json.load(f)
            
        if user_id:
            # 특정 사용자의 메시지만 필터링
            messages = [msg for msg in chat_logs if msg.get('user_id') == user_id]
        else:
            messages = chat_logs
            
    except Exception as e:
        print(f"Error reading messages: {e}")
        
    return messages

def analyze_personality(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """사용자의 채팅 패턴을 분석"""
    if not messages:
        return {"error": "메시지가 없습니다."}
        
    analysis = {
        "total_messages": len(messages),
        "avg_length": sum(len(m.get('message', '')) for m in messages) / len(messages),
        "active_hours": defaultdict(int),
        "common_words": defaultdict(int)
    }
    
    for msg in messages:
        # 시간대별 활동량 분석
        timestamp = datetime.fromisoformat(msg.get('timestamp', '')).astimezone(KST)
        hour = timestamp.hour
        analysis['active_hours'][hour] += 1
        
        # 자주 사용하는 단어 분석
        words = msg.get('message', '').split()
        for word in words:
            analysis['common_words'][word] += 1
    
    # 가장 자주 사용하는 단어 상위 10개
    analysis['common_words'] = dict(sorted(analysis['common_words'].items(), 
                                         key=lambda x: x[1], 
                                         reverse=True)[:10])
    
    return analysis

def is_valid_message(message: str) -> bool:
    """메시지가 유효한지 검사"""
    if not message or not isinstance(message, str):
        return False
    if len(message.strip()) == 0:
        return False
    return True

def sanitize_filename(filename: str) -> str:
    """파일 이름에서 사용할 수 없는 문자 제거"""
    import re
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    return sanitized
