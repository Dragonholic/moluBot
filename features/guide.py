import json
import os
import aiohttp
from typing import Dict, Optional, List
import re
from datetime import datetime
from molu import call_claude_api

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
    """저장된 공략 URL 조회 또는 AI 검색"""
    try:
        # 저장된 공략 확인
        with open(GUIDES_FILE, 'r', encoding='utf-8') as f:
            guides = json.load(f)
            
        if keyword in guides:
            return {
                "status": "success",
                "found": True,
                "url": guides[keyword]["url"]
            }
        else:
            # Claude API를 사용하여 검색
            search_prompt = f"""
            블루 아카이브 게임의 '{keyword}' 관련 공략이나 정보를 찾아주세요.
            공식 위키나 유명 공략 사이트의 URL을 포함해서 답변해주세요.
            없다면 '해당 공략을 찾을 수 없습니다'라고 답변해주세요.
            """
            
            messages = [{"role": "user", "content": search_prompt}]
            search_result = await call_claude_api(messages, "guide_search", "detailed")
            
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

# 초기 관리자 설정 함수 추가
async def init_default_admin():
    try:
        default_admins = ["용럭/AYVKWWBZ", "용럭"]  # 기본 관리자 목록
        
        # admins.json 파일이 없으면 생성
        if not os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"admins": default_admins}, f, ensure_ascii=False, indent=2)
        else:
            # 파일이 있으면 기존 데이터에 추가
            with open(ADMINS_FILE, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                updated = False
                for admin in default_admins:
                    if admin not in data["admins"]:
                        data["admins"].append(admin)
                        updated = True
                
                if updated:
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.truncate()
        
        return {"status": "success", "message": "기본 관리자가 추가되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)} 

async def remove_admin(admin_id: str, requester_id: str) -> Dict:
    """관리자 삭제 함수"""
    try:
        if not await is_admin(requester_id):
            return {"status": "error", "message": "관리자만 다른 관리자를 삭제할 수 있습니다."}
            
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if admin_id not in data["admins"]:
            return {"status": "error", "message": "해당 사용자는 관리자가 아닙니다."}
            
        data["admins"].remove(admin_id)
        
        with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return {"status": "success", "message": f"{admin_id} 관리자가 삭제되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)} 