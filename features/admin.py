import json
import os
import aiofiles
from typing import Dict

ADMINS_FILE = "data/admins.json"

# 디렉토리 생성
os.makedirs("data", exist_ok=True)

# 기본 파일 생성
if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"admins": []}, f)

async def is_admin(user_id: str) -> bool:
    """관리자 여부 확인"""
    try:
        async with aiofiles.open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
            return user_id in data.get("admins", [])
    except Exception:
        return False

async def add_admin(admin_id: str) -> Dict:
    """관리자 추가"""
    try:
        async with aiofiles.open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
            
        if admin_id in data["admins"]:
            return {"status": "error", "message": "이미 관리자로 등록된 사용자입니다."}
            
        data["admins"].append(admin_id)
        
        async with aiofiles.open(ADMINS_FILE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            
        return {"status": "success", "message": f"{admin_id}가 관리자로 추가되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def remove_admin(admin_id: str) -> Dict:
    """관리자 삭제"""
    try:
        async with aiofiles.open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
            
        if admin_id not in data["admins"]:
            return {"status": "error", "message": "해당 사용자는 관리자가 아닙니다."}
            
        data["admins"].remove(admin_id)
        
        async with aiofiles.open(ADMINS_FILE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            
        return {"status": "success", "message": f"{admin_id} 관리자가 삭제되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)} 