import json
import os
import aiohttp
from typing import Dict, Optional, List
import re
from datetime import datetime

# 가이드 데이터를 저장할 파일
GUIDES_FILE = "data/guides.json"
ADMINS_FILE = "data/admins.json"

# 디렉토리 생성
os.makedirs("data", exist_ok=True)

# 파일이 없으면 생성
if not os.path.exists(GUIDES_FILE):
    with open(GUIDES_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"admins": []}, f)

async def search_guide(query: str) -> str:
    """인터넷에서 블루아카이브 공략 검색"""
    search_query = f"블루아카이브 {query} 공략"
    
    async with aiohttp.ClientSession() as session:
        # 여기에 실제 검색 API 호출 구현
        # 예: Google Custom Search API 사용
        pass
    
    # 임시 응답
    return f"죄송합니다. '{query}'에 대한 공략을 찾지 못했습니다."

async def save_guide(keyword: str, url: str, admin_id: str) -> Dict:
    """공략 URL 저장"""
    if not await is_admin(admin_id):
        return {"status": "error", "message": "관리자만 공략을 저장할 수 있습니다."}
    
    try:
        with open(GUIDES_FILE, 'r', encoding='utf-8') as f:
            guides = json.load(f)
        
        guides[keyword] = {
            "url": url,
            "added_by": admin_id,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(GUIDES_FILE, 'w', encoding='utf-8') as f:
            json.dump(guides, f, ensure_ascii=False, indent=2)
            
        return {"status": "success", "message": f"'{keyword}' 공략이 저장되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_guide(keyword: str) -> Dict:
    """저장된 공략 URL 조회"""
    try:
        with open(GUIDES_FILE, 'r', encoding='utf-8') as f:
            guides = json.load(f)
            
        if keyword in guides:
            return {
                "status": "success",
                "found": True,
                "url": guides[keyword]["url"]
            }
        else:
            # 저장된 공략이 없으면 검색 시도
            search_result = await search_guide(keyword)
            return {
                "status": "success",
                "found": False,
                "search_result": search_result
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def add_admin(admin_id: str) -> Dict:
    """관리자 추가"""
    try:
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if admin_id not in data["admins"]:
            data["admins"].append(admin_id)
            
            with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        return {"status": "success", "message": "관리자가 추가되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def is_admin(user_id: str) -> bool:
    """관리자 여부 확인"""
    try:
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return user_id in data["admins"]
    except Exception:
        return False 