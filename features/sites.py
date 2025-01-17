import json
import os
from typing import Dict
import aiofiles
from datetime import datetime

SITES_FILE = "data/sites.json"

# 디렉토리 생성
os.makedirs("data", exist_ok=True)

# 기본 파일 생성
if not os.path.exists(SITES_FILE):
    with open(SITES_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

async def save_site(keyword: str, url: str, user_id: str) -> Dict:
    """사이트 URL 저장/수정"""
    try:
        async with aiofiles.open(SITES_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            sites = json.loads(content) if content else {}
        
        is_update = keyword in sites
        sites[keyword] = {
            'url': url,
            'user_id': user_id,
            'updated_at': datetime.now().isoformat()
        }
        
        async with aiofiles.open(SITES_FILE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(sites, ensure_ascii=False, indent=2))
            
        action = "수정" if is_update else "저장"
        return {"status": "success", "message": f"'{keyword}' 사이트가 {action}되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def delete_site(keyword: str) -> Dict:
    """사이트 삭제"""
    try:
        async with aiofiles.open(SITES_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            sites = json.loads(content) if content else {}
        
        if keyword not in sites:
            return {"status": "error", "message": f"'{keyword}' 사이트를 찾을 수 없습니다."}
            
        del sites[keyword]
        
        async with aiofiles.open(SITES_FILE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(sites, ensure_ascii=False, indent=2))
            
        return {"status": "success", "message": f"'{keyword}' 사이트가 삭제되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_site(keyword: str) -> Dict:
    """사이트 URL 조회"""
    try:
        async with aiofiles.open(SITES_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            sites = json.loads(content) if content else {}
            
        if keyword in sites:
            return {"status": "success", "found": True, "url": sites[keyword]}
        else:
            return {"status": "success", "found": False, "message": f"'{keyword}' 사이트를 찾을 수 없습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_site_list() -> Dict:
    """저장된 사이트 목록 조회"""
    try:
        async with aiofiles.open(SITES_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            sites = json.loads(content) if content else {}
            
        if sites:
            site_list = "\n".join([f"- {key}: {url}" for key, url in sites.items()])
            return {"status": "success", "message": f"=== 저장된 사이트 목록 ===\n{site_list}"}
        else:
            return {"status": "success", "message": "저장된 사이트가 없습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)} 