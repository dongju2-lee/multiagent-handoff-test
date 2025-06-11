from mcp.server.fastmcp import FastMCP
import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import uuid
from datetime import datetime
import hashlib

# 환경 변수 로드
load_dotenv()

NOTE_STORAGE_MCP_NAME = "note_storage"
NOTE_STORAGE_MCP_HOST = "0.0.0.0"
NOTE_STORAGE_MCP_PORT = 10006
NOTE_STORAGE_MCP_INSTRUCTIONS = "노트 저장소입니다. 메모관리를 보조하여 파일 저장, 백업, 동기화, 버전 관리 등을 제공합니다."

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("note_storage_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    NOTE_STORAGE_MCP_NAME,
    instructions=NOTE_STORAGE_MCP_INSTRUCTIONS,
    host=NOTE_STORAGE_MCP_HOST,
    port=NOTE_STORAGE_MCP_PORT,
)

# 가짜 저장소 데이터
STORED_FILES = {}
FILE_VERSIONS = {}
BACKUP_HISTORY = {}

@mcp.tool()
async def save_note_file(
    filename: str,
    content: str,
    content_type: str = "text/plain",
    tags: List[str] = None
) -> Dict[str, Any]:
    """
    노트 파일을 저장합니다.
    
    Args:
        filename (str): 파일명
        content (str): 파일 내용
        content_type (str, optional): 컨텐츠 타입 (기본값: "text/plain")
        tags (List[str], optional): 태그 목록
        
    Returns:
        Dict[str, Any]: 저장된 파일 정보
    """
    logger.info(f"노트 파일 저장: {filename}")
    
    file_id = str(uuid.uuid4())
    
    # 파일 해시 생성
    content_hash = hashlib.md5(content.encode()).hexdigest()
    
    file_info = {
        "id": file_id,
        "filename": filename,
        "content": content,
        "content_type": content_type,
        "content_hash": content_hash,
        "size_bytes": len(content.encode()),
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "version": 1
    }
    
    STORED_FILES[file_id] = file_info
    
    # 버전 히스토리 시작
    FILE_VERSIONS[file_id] = [file_info.copy()]
    
    return {
        "success": True,
        "file": file_info,
        "message": f"'{filename}' 파일이 성공적으로 저장되었습니다."
    }

@mcp.tool()
async def get_file(file_id: str) -> Dict[str, Any]:
    """
    저장된 파일을 조회합니다.
    
    Args:
        file_id (str): 파일 ID
        
    Returns:
        Dict[str, Any]: 파일 정보
    """
    logger.info(f"파일 조회: {file_id}")
    
    if file_id not in STORED_FILES:
        return {"error": f"ID {file_id}에 해당하는 파일을 찾을 수 없습니다."}
    
    return {
        "success": True,
        "file": STORED_FILES[file_id]
    }

@mcp.tool()
async def update_file(
    file_id: str,
    content: str = None,
    filename: str = None,
    tags: List[str] = None
) -> Dict[str, Any]:
    """
    저장된 파일을 업데이트합니다.
    
    Args:
        file_id (str): 파일 ID
        content (str, optional): 새로운 내용
        filename (str, optional): 새로운 파일명
        tags (List[str], optional): 새로운 태그 목록
        
    Returns:
        Dict[str, Any]: 업데이트된 파일 정보
    """
    logger.info(f"파일 업데이트: {file_id}")
    
    if file_id not in STORED_FILES:
        return {"error": f"ID {file_id}에 해당하는 파일을 찾을 수 없습니다."}
    
    file_info = STORED_FILES[file_id].copy()
    
    # 이전 버전 백업
    if file_id not in FILE_VERSIONS:
        FILE_VERSIONS[file_id] = []
    FILE_VERSIONS[file_id].append(file_info.copy())
    
    # 업데이트 적용
    if content is not None:
        file_info["content"] = content
        file_info["content_hash"] = hashlib.md5(content.encode()).hexdigest()
        file_info["size_bytes"] = len(content.encode())
    
    if filename is not None:
        file_info["filename"] = filename
    
    if tags is not None:
        file_info["tags"] = tags
    
    file_info["updated_at"] = datetime.now().isoformat()
    file_info["version"] += 1
    
    STORED_FILES[file_id] = file_info
    
    return {
        "success": True,
        "file": file_info,
        "message": "파일이 성공적으로 업데이트되었습니다."
    }

@mcp.tool()
async def list_files(
    search_query: str = None,
    content_type: str = None,
    tags: List[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    저장된 파일 목록을 조회합니다.
    
    Args:
        search_query (str, optional): 파일명 검색 쿼리
        content_type (str, optional): 컨텐츠 타입 필터
        tags (List[str], optional): 태그 필터
        limit (int, optional): 최대 조회 개수 (기본값: 10)
        
    Returns:
        Dict[str, Any]: 파일 목록
    """
    logger.info(f"파일 목록 조회: 쿼리={search_query}, 타입={content_type}")
    
    results = []
    
    for file_info in STORED_FILES.values():
        # 검색 쿼리 필터
        if search_query:
            if search_query.lower() not in file_info["filename"].lower():
                continue
        
        # 컨텐츠 타입 필터
        if content_type and file_info["content_type"] != content_type:
            continue
        
        # 태그 필터
        if tags:
            if not any(tag in file_info["tags"] for tag in tags):
                continue
        
        # 민감한 정보 제외한 요약 정보
        file_summary = {
            "id": file_info["id"],
            "filename": file_info["filename"],
            "content_type": file_info["content_type"],
            "size_bytes": file_info["size_bytes"],
            "tags": file_info["tags"],
            "created_at": file_info["created_at"],
            "updated_at": file_info["updated_at"],
            "version": file_info["version"]
        }
        results.append(file_summary)
    
    # 최신순으로 정렬
    results.sort(key=lambda x: x["updated_at"], reverse=True)
    
    # 제한 개수 적용
    results = results[:limit]
    
    return {
        "success": True,
        "total_count": len(results),
        "files": results,
        "filters": {
            "search_query": search_query,
            "content_type": content_type,
            "tags": tags,
            "limit": limit
        }
    }

@mcp.tool()
async def get_file_versions(file_id: str) -> Dict[str, Any]:
    """
    파일의 버전 히스토리를 조회합니다.
    
    Args:
        file_id (str): 파일 ID
        
    Returns:
        Dict[str, Any]: 버전 히스토리
    """
    logger.info(f"파일 버전 히스토리 조회: {file_id}")
    
    if file_id not in STORED_FILES:
        return {"error": f"ID {file_id}에 해당하는 파일을 찾을 수 없습니다."}
    
    if file_id not in FILE_VERSIONS:
        return {"error": "버전 히스토리가 없습니다."}
    
    versions = []
    for i, version in enumerate(FILE_VERSIONS[file_id]):
        version_summary = {
            "version": i + 1,
            "filename": version["filename"],
            "content_hash": version["content_hash"],
            "size_bytes": version["size_bytes"],
            "updated_at": version["updated_at"]
        }
        versions.append(version_summary)
    
    return {
        "file_id": file_id,
        "total_versions": len(versions),
        "versions": versions
    }

@mcp.tool()
async def restore_file_version(file_id: str, version: int) -> Dict[str, Any]:
    """
    파일을 특정 버전으로 복원합니다.
    
    Args:
        file_id (str): 파일 ID
        version (int): 복원할 버전 번호
        
    Returns:
        Dict[str, Any]: 복원된 파일 정보
    """
    logger.info(f"파일 버전 복원: {file_id}, 버전 {version}")
    
    if file_id not in STORED_FILES:
        return {"error": f"ID {file_id}에 해당하는 파일을 찾을 수 없습니다."}
    
    if file_id not in FILE_VERSIONS or len(FILE_VERSIONS[file_id]) < version:
        return {"error": f"버전 {version}을 찾을 수 없습니다."}
    
    # 현재 버전을 히스토리에 추가
    current_file = STORED_FILES[file_id].copy()
    FILE_VERSIONS[file_id].append(current_file)
    
    # 지정된 버전으로 복원
    target_version = FILE_VERSIONS[file_id][version - 1].copy()
    target_version["updated_at"] = datetime.now().isoformat()
    target_version["version"] = current_file["version"] + 1
    
    STORED_FILES[file_id] = target_version
    
    return {
        "success": True,
        "file": target_version,
        "message": f"파일이 버전 {version}으로 복원되었습니다."
    }

@mcp.tool()
async def create_backup(backup_name: str, file_ids: List[str] = None) -> Dict[str, Any]:
    """
    파일들의 백업을 생성합니다.
    
    Args:
        backup_name (str): 백업 이름
        file_ids (List[str], optional): 백업할 파일 ID 목록 (None이면 전체 백업)
        
    Returns:
        Dict[str, Any]: 백업 정보
    """
    logger.info(f"백업 생성: {backup_name}")
    
    backup_id = str(uuid.uuid4())
    
    # 백업할 파일들 선택
    if file_ids is None:
        files_to_backup = dict(STORED_FILES)
    else:
        files_to_backup = {fid: STORED_FILES[fid] for fid in file_ids if fid in STORED_FILES}
    
    backup_info = {
        "id": backup_id,
        "name": backup_name,
        "file_count": len(files_to_backup),
        "files": files_to_backup,
        "created_at": datetime.now().isoformat(),
        "size_bytes": sum(f["size_bytes"] for f in files_to_backup.values())
    }
    
    BACKUP_HISTORY[backup_id] = backup_info
    
    return {
        "success": True,
        "backup": {
            "id": backup_id,
            "name": backup_name,
            "file_count": backup_info["file_count"],
            "size_bytes": backup_info["size_bytes"],
            "created_at": backup_info["created_at"]
        },
        "message": f"'{backup_name}' 백업이 성공적으로 생성되었습니다."
    }

@mcp.tool()
async def list_backups() -> Dict[str, Any]:
    """
    백업 목록을 조회합니다.
    
    Returns:
        Dict[str, Any]: 백업 목록
    """
    logger.info("백업 목록 조회")
    
    backup_summaries = []
    for backup in BACKUP_HISTORY.values():
        summary = {
            "id": backup["id"],
            "name": backup["name"],
            "file_count": backup["file_count"],
            "size_bytes": backup["size_bytes"],
            "created_at": backup["created_at"]
        }
        backup_summaries.append(summary)
    
    # 최신순으로 정렬
    backup_summaries.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "total_backups": len(backup_summaries),
        "backups": backup_summaries
    }

@mcp.tool()
async def restore_from_backup(backup_id: str, file_ids: List[str] = None) -> Dict[str, Any]:
    """
    백업에서 파일들을 복원합니다.
    
    Args:
        backup_id (str): 백업 ID
        file_ids (List[str], optional): 복원할 파일 ID 목록 (None이면 전체 복원)
        
    Returns:
        Dict[str, Any]: 복원 결과
    """
    logger.info(f"백업에서 복원: {backup_id}")
    
    if backup_id not in BACKUP_HISTORY:
        return {"error": f"ID {backup_id}에 해당하는 백업을 찾을 수 없습니다."}
    
    backup = BACKUP_HISTORY[backup_id]
    
    # 복원할 파일들 선택
    if file_ids is None:
        files_to_restore = backup["files"]
    else:
        files_to_restore = {fid: backup["files"][fid] for fid in file_ids if fid in backup["files"]}
    
    restored_count = 0
    for file_id, file_info in files_to_restore.items():
        # 기존 파일이 있으면 버전 히스토리에 추가
        if file_id in STORED_FILES:
            if file_id not in FILE_VERSIONS:
                FILE_VERSIONS[file_id] = []
            FILE_VERSIONS[file_id].append(STORED_FILES[file_id].copy())
        
        # 파일 복원
        restored_file = file_info.copy()
        restored_file["updated_at"] = datetime.now().isoformat()
        restored_file["version"] = restored_file.get("version", 1) + 1
        
        STORED_FILES[file_id] = restored_file
        restored_count += 1
    
    return {
        "success": True,
        "restored_count": restored_count,
        "backup_name": backup["name"],
        "message": f"{restored_count}개의 파일이 복원되었습니다."
    }

@mcp.tool()
async def get_storage_stats() -> Dict[str, Any]:
    """
    저장소 통계 정보를 제공합니다.
    
    Returns:
        Dict[str, Any]: 저장소 통계
    """
    logger.info("저장소 통계 조회")
    
    # 파일 통계
    total_files = len(STORED_FILES)
    total_size = sum(f["size_bytes"] for f in STORED_FILES.values())
    
    # 컨텐츠 타입별 통계
    content_types = {}
    for file_info in STORED_FILES.values():
        ct = file_info["content_type"]
        content_types[ct] = content_types.get(ct, 0) + 1
    
    # 태그 통계
    tag_counts = {}
    for file_info in STORED_FILES.values():
        for tag in file_info["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # 최근 활동
    recent_files = sorted(STORED_FILES.values(), key=lambda x: x["updated_at"], reverse=True)[:5]
    recent_activity = [
        {
            "filename": f["filename"],
            "updated_at": f["updated_at"],
            "version": f["version"]
        }
        for f in recent_files
    ]
    
    return {
        "file_statistics": {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "content_types": content_types,
            "popular_tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        },
        "backup_statistics": {
            "total_backups": len(BACKUP_HISTORY),
            "total_backup_size": sum(b["size_bytes"] for b in BACKUP_HISTORY.values())
        },
        "recent_activity": recent_activity,
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("노트 저장소 MCP 서버가 실행 중입니다...")
    print(f"포트: {NOTE_STORAGE_MCP_PORT}")
    mcp.run(transport="sse") 