import json
import os
from typing import Dict
import aiofiles

GUIDES_FILE = "data/guides.json"
ADMINS_FILE = "data/admins.json"

# 디렉토리 생성
os.makedirs("data", exist_ok=True)

# 기본 파일 생성
if not os.path.exists(GUIDES_FILE):
    with open(GUIDES_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"admins": []}, f)

async def save_guide(keyword: str, url: str, admin_id: str) -> Dict:
    """공략 URL 저장"""
    try:
        if not await is_admin(admin_id):
            return {"status": "error", "message": "관리자만 공략을 저장할 수 있습니다."}
            
        async with aiofiles.open(GUIDES_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            guides = json.loads(content) if content else {}
        
        guides[keyword] = url
        
        async with aiofiles.open(GUIDES_FILE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(guides, ensure_ascii=False, indent=2))
            
        return {"status": "success", "message": f"'{keyword}' 공략이 저장되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_guide(keyword: str) -> Dict:
    """공략 URL 조회"""
    try:
        async with aiofiles.open(GUIDES_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            guides = json.loads(content) if content else {}
            
        if keyword in guides:
            return {"status": "success", "found": True, "url": guides[keyword]}
        else:
            return {"status": "success", "found": False, "search_result": f"'{keyword}' 공략을 찾을 수 없습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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

async def remove_admin(admin_id: str, requester_id: str) -> Dict:
    """관리자 삭제"""
    try:
        if not await is_admin(requester_id):
            return {"status": "error", "message": "관리자만 다른 관리자를 삭제할 수 있습니다."}
            
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

async def init_default_admin() -> Dict:
    """기본 관리자 초기화"""
    try:
        default_admins = ["용럭/AYVKWWBZ", "용럭"]
        
        async with aiofiles.open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content) if content else {"admins": []}
            
        updated = False
        for admin in default_admins:
            if admin not in data["admins"]:
                data["admins"].append(admin)
                updated = True
                
        if updated:
            async with aiofiles.open(ADMINS_FILE, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
                
        return {"status": "success", "message": "기본 관리자가 추가되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)} 