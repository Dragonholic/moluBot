import json
import os
from typing import Dict

SHORTCUTS_DIR = "data/shortcuts"

# 디렉토리 생성
os.makedirs(SHORTCUTS_DIR, exist_ok=True)

def get_room_file(room: str) -> str:
    """방별 파일 경로 반환"""
    return os.path.join(SHORTCUTS_DIR, f"{room}.json")

async def init_room_shortcuts(room: str):
    """방별 사이트 주소 파일 초기화"""
    file_path = get_room_file(room)
    if not os.path.exists(file_path):
        default_shortcuts = {
            "미래시": "https://gall.dcinside.com/mgallery/board/lists?id=projectmx",
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_shortcuts, f, ensure_ascii=False, indent=2)

async def add_shortcut(keyword: str, url: str, admin_id: str, room: str) -> Dict:
    """방별 사이트 주소 추가/수정"""
    try:
        await init_room_shortcuts(room)
        file_path = get_room_file(room)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            shortcuts = json.load(f)
        
        shortcuts[keyword] = url
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(shortcuts, f, ensure_ascii=False, indent=2)
            
        action = "수정되었습니다" if keyword in shortcuts else "추가되었습니다"
        return {"status": "success", "message": f"'{keyword}' 사이트 주소가 {action}."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_shortcut(keyword: str, room: str) -> Dict:
    """방별 사이트 주소 조회"""
    try:
        await init_room_shortcuts(room)
        file_path = get_room_file(room)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            shortcuts = json.load(f)
            
        if keyword in shortcuts:
            return {"status": "success", "url": shortcuts[keyword]}
        else:
            return {"status": "error", "message": "등록되지 않은 사이트 주소입니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def list_shortcuts(room: str) -> Dict:
    """방별 저장된 사이트 목록 조회"""
    try:
        await init_room_shortcuts(room)
        file_path = get_room_file(room)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            shortcuts = json.load(f)
            
        if shortcuts:
            site_list = sorted(shortcuts.keys())
            return {
                "status": "success",
                "message": f"📌 {room} 방의 저장된 사이트 목록:\n" + "\n".join(f"- {key}" for key in site_list)
            }
        else:
            return {
                "status": "success",
                "message": f"{room} 방에 저장된 사이트가 없습니다."
            }
    except Exception as e:
        return {"status": "error", "message": str(e)} 