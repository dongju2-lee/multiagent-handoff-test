from mcp.server.fastmcp import FastMCP
import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import uuid
from datetime import datetime
import random

# 환경 변수 로드
load_dotenv()

MEMO_MCP_NAME = "memo_manager"
MEMO_MCP_HOST = "0.0.0.0"
MEMO_MCP_PORT = 10005
MEMO_MCP_INSTRUCTIONS = "메모관리 개인비서입니다. 메모 작성, 할일 관리, 정보 저장과 검색에 특화된 서비스를 제공합니다."

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("memo_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    MEMO_MCP_NAME,
    instructions=MEMO_MCP_INSTRUCTIONS,
    host=MEMO_MCP_HOST,
    port=MEMO_MCP_PORT,
)

# 가짜 데이터 저장소
MEMOS = {}
TODOS = {}

# 초기 가짜 메모 데이터
INITIAL_MEMOS = [
    {
        "id": str(uuid.uuid4()),
        "title": "프로젝트 아이디어",
        "content": "새로운 개인비서 앱 개발 아이디어\n- AI 기반 스케줄 관리\n- 음성 인식 기능\n- 스마트 알림",
        "category": "아이디어",
        "tags": ["프로젝트", "AI", "앱개발"],
        "priority": "medium",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "title": "회의 노트",
        "content": "팀 회의 주요 내용\n1. Q1 목표 설정\n2. 새로운 기능 개발 계획\n3. 마케팅 전략 논의",
        "category": "업무",
        "tags": ["회의", "팀", "계획"],
        "priority": "high",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

# 초기 가짜 할일 데이터
INITIAL_TODOS = [
    {
        "id": str(uuid.uuid4()),
        "title": "프로젝트 문서 작성",
        "description": "새로운 프로젝트 기획서 작성 완료하기",
        "priority": "high",
        "status": "pending",
        "due_date": "2024-01-20T17:00:00",
        "category": "업무",
        "tags": ["문서", "기획"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "title": "운동하기",
        "description": "주 3회 이상 운동하기",
        "priority": "medium",
        "status": "in_progress",
        "due_date": "2024-01-25T20:00:00",
        "category": "건강",
        "tags": ["운동", "건강"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

# 초기 데이터 로드
for memo in INITIAL_MEMOS:
    MEMOS[memo["id"]] = memo

for todo in INITIAL_TODOS:
    TODOS[todo["id"]] = todo

@mcp.tool()
async def create_memo(
    title: str,
    content: str,
    category: str = "일반",
    tags: List[str] = None,
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    새로운 메모를 생성합니다.
    
    Args:
        title (str): 메모 제목
        content (str): 메모 내용
        category (str, optional): 카테고리 (기본값: "일반")
        tags (List[str], optional): 태그 목록
        priority (str, optional): 우선순위 ("low", "medium", "high", 기본값: "medium")
        
    Returns:
        Dict[str, Any]: 생성된 메모 정보
    """
    logger.info(f"메모 생성 요청: {title}")
    
    memo_id = str(uuid.uuid4())
    new_memo = {
        "id": memo_id,
        "title": title,
        "content": content,
        "category": category,
        "tags": tags or [],
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    MEMOS[memo_id] = new_memo
    
    return {
        "success": True,
        "memo": new_memo,
        "message": f"'{title}' 메모가 성공적으로 생성되었습니다."
    }

@mcp.tool()
async def get_memo(memo_id: str) -> Dict[str, Any]:
    """
    특정 메모의 상세 정보를 조회합니다.
    
    Args:
        memo_id (str): 메모 ID
        
    Returns:
        Dict[str, Any]: 메모 상세 정보
    """
    logger.info(f"메모 조회 요청: {memo_id}")
    
    if memo_id not in MEMOS:
        return {"error": f"ID {memo_id}에 해당하는 메모를 찾을 수 없습니다."}
    
    return {
        "success": True,
        "memo": MEMOS[memo_id]
    }

@mcp.tool()
async def search_memos(
    keyword: str = None,
    category: str = None,
    tags: List[str] = None,
    priority: str = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    메모를 검색합니다.
    
    Args:
        keyword (str, optional): 제목이나 내용에서 검색할 키워드
        category (str, optional): 카테고리 필터
        tags (List[str], optional): 포함해야 할 태그들
        priority (str, optional): 우선순위 필터
        limit (int, optional): 최대 결과 개수 (기본값: 10)
        
    Returns:
        Dict[str, Any]: 검색된 메모 목록
    """
    logger.info(f"메모 검색: 키워드={keyword}, 카테고리={category}, 태그={tags}")
    
    results = []
    
    for memo in MEMOS.values():
        # 키워드 검색
        if keyword:
            if keyword.lower() not in memo["title"].lower() and keyword.lower() not in memo["content"].lower():
                continue
        
        # 카테고리 필터
        if category and memo["category"] != category:
            continue
        
        # 태그 필터
        if tags:
            if not any(tag in memo["tags"] for tag in tags):
                continue
        
        # 우선순위 필터
        if priority and memo["priority"] != priority:
            continue
        
        results.append(memo)
    
    # 최신순으로 정렬
    results.sort(key=lambda x: x["updated_at"], reverse=True)
    
    # 제한 개수 적용
    results = results[:limit]
    
    return {
        "success": True,
        "total_count": len(results),
        "memos": results,
        "search_criteria": {
            "keyword": keyword,
            "category": category,
            "tags": tags,
            "priority": priority,
            "limit": limit
        }
    }

@mcp.tool()
async def update_memo(
    memo_id: str,
    title: str = None,
    content: str = None,
    category: str = None,
    tags: List[str] = None,
    priority: str = None
) -> Dict[str, Any]:
    """
    기존 메모를 수정합니다.
    
    Args:
        memo_id (str): 수정할 메모 ID
        title (str, optional): 새로운 제목
        content (str, optional): 새로운 내용
        category (str, optional): 새로운 카테고리
        tags (List[str], optional): 새로운 태그 목록
        priority (str, optional): 새로운 우선순위
        
    Returns:
        Dict[str, Any]: 수정된 메모 정보
    """
    logger.info(f"메모 수정 요청: {memo_id}")
    
    if memo_id not in MEMOS:
        return {"error": f"ID {memo_id}에 해당하는 메모를 찾을 수 없습니다."}
    
    memo = MEMOS[memo_id].copy()
    
    # 수정할 필드들 업데이트
    if title is not None:
        memo["title"] = title
    if content is not None:
        memo["content"] = content
    if category is not None:
        memo["category"] = category
    if tags is not None:
        memo["tags"] = tags
    if priority is not None:
        memo["priority"] = priority
    
    memo["updated_at"] = datetime.now().isoformat()
    MEMOS[memo_id] = memo
    
    return {
        "success": True,
        "memo": memo,
        "message": "메모가 성공적으로 수정되었습니다."
    }

@mcp.tool()
async def delete_memo(memo_id: str) -> Dict[str, Any]:
    """
    메모를 삭제합니다.
    
    Args:
        memo_id (str): 삭제할 메모 ID
        
    Returns:
        Dict[str, Any]: 삭제 결과
    """
    logger.info(f"메모 삭제 요청: {memo_id}")
    
    if memo_id not in MEMOS:
        return {"error": f"ID {memo_id}에 해당하는 메모를 찾을 수 없습니다."}
    
    deleted_memo = MEMOS.pop(memo_id)
    
    return {
        "success": True,
        "deleted_memo": deleted_memo,
        "message": f"'{deleted_memo['title']}' 메모가 성공적으로 삭제되었습니다."
    }

@mcp.tool()
async def create_todo(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: str = None,
    category: str = "일반",
    tags: List[str] = None
) -> Dict[str, Any]:
    """
    새로운 할일을 생성합니다.
    
    Args:
        title (str): 할일 제목
        description (str, optional): 할일 설명
        priority (str, optional): 우선순위 ("low", "medium", "high", 기본값: "medium")
        due_date (str, optional): 마감일 (ISO 형식: YYYY-MM-DDTHH:MM:SS)
        category (str, optional): 카테고리 (기본값: "일반")
        tags (List[str], optional): 태그 목록
        
    Returns:
        Dict[str, Any]: 생성된 할일 정보
    """
    logger.info(f"할일 생성 요청: {title}")
    
    todo_id = str(uuid.uuid4())
    new_todo = {
        "id": todo_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending",
        "due_date": due_date,
        "category": category,
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    TODOS[todo_id] = new_todo
    
    return {
        "success": True,
        "todo": new_todo,
        "message": f"'{title}' 할일이 성공적으로 생성되었습니다."
    }

@mcp.tool()
async def list_todos(
    status: str = None,
    priority: str = None,
    category: str = None,
    overdue_only: bool = False,
    limit: int = 10
) -> Dict[str, Any]:
    """
    할일 목록을 조회합니다.
    
    Args:
        status (str, optional): 상태 필터 ("pending", "in_progress", "completed", "cancelled")
        priority (str, optional): 우선순위 필터 ("low", "medium", "high")
        category (str, optional): 카테고리 필터
        overdue_only (bool, optional): 지연된 할일만 조회 (기본값: False)
        limit (int, optional): 최대 조회 개수 (기본값: 10)
        
    Returns:
        Dict[str, Any]: 할일 목록
    """
    logger.info(f"할일 목록 조회: 상태={status}, 우선순위={priority}")
    
    results = []
    current_time = datetime.now()
    
    for todo in TODOS.values():
        # 상태 필터
        if status and todo["status"] != status:
            continue
        
        # 우선순위 필터
        if priority and todo["priority"] != priority:
            continue
        
        # 카테고리 필터
        if category and todo["category"] != category:
            continue
        
        # 지연된 할일만 조회
        if overdue_only:
            if not todo["due_date"]:
                continue
            due_dt = datetime.fromisoformat(todo["due_date"])
            if due_dt >= current_time or todo["status"] == "completed":
                continue
        
        results.append(todo)
    
    # 우선순위와 마감일 순으로 정렬
    priority_order = {"high": 3, "medium": 2, "low": 1}
    results.sort(key=lambda x: (
        priority_order.get(x["priority"], 0),
        x["due_date"] or "9999-12-31T23:59:59"
    ), reverse=True)
    
    # 제한 개수 적용
    results = results[:limit]
    
    return {
        "success": True,
        "total_count": len(results),
        "todos": results,
        "filters": {
            "status": status,
            "priority": priority,
            "category": category,
            "overdue_only": overdue_only,
            "limit": limit
        }
    }

@mcp.tool()
async def update_todo_status(todo_id: str, status: str) -> Dict[str, Any]:
    """
    할일의 상태를 업데이트합니다.
    
    Args:
        todo_id (str): 할일 ID
        status (str): 새로운 상태 ("pending", "in_progress", "completed", "cancelled")
        
    Returns:
        Dict[str, Any]: 업데이트된 할일 정보
    """
    logger.info(f"할일 상태 업데이트: {todo_id} -> {status}")
    
    if todo_id not in TODOS:
        return {"error": f"ID {todo_id}에 해당하는 할일을 찾을 수 없습니다."}
    
    valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
    if status not in valid_statuses:
        return {"error": f"유효하지 않은 상태입니다. 가능한 상태: {valid_statuses}"}
    
    todo = TODOS[todo_id].copy()
    todo["status"] = status
    todo["updated_at"] = datetime.now().isoformat()
    
    if status == "completed":
        todo["completed_at"] = datetime.now().isoformat()
    
    TODOS[todo_id] = todo
    
    return {
        "success": True,
        "todo": todo,
        "message": f"할일 상태가 '{status}'로 변경되었습니다."
    }

@mcp.tool()
async def get_memo_statistics() -> Dict[str, Any]:
    """
    메모와 할일의 통계 정보를 제공합니다.
    
    Returns:
        Dict[str, Any]: 통계 정보
    """
    logger.info("메모/할일 통계 조회")
    
    # 메모 통계
    memo_categories = {}
    memo_priorities = {"low": 0, "medium": 0, "high": 0}
    
    for memo in MEMOS.values():
        category = memo["category"]
        memo_categories[category] = memo_categories.get(category, 0) + 1
        memo_priorities[memo["priority"]] += 1
    
    # 할일 통계
    todo_statuses = {"pending": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
    todo_priorities = {"low": 0, "medium": 0, "high": 0}
    overdue_count = 0
    
    current_time = datetime.now()
    
    for todo in TODOS.values():
        todo_statuses[todo["status"]] += 1
        todo_priorities[todo["priority"]] += 1
        
        # 지연된 할일 계산
        if todo["due_date"] and todo["status"] not in ["completed", "cancelled"]:
            due_dt = datetime.fromisoformat(todo["due_date"])
            if due_dt < current_time:
                overdue_count += 1
    
    return {
        "memo_statistics": {
            "total_memos": len(MEMOS),
            "categories": memo_categories,
            "priorities": memo_priorities
        },
        "todo_statistics": {
            "total_todos": len(TODOS),
            "statuses": todo_statuses,
            "priorities": todo_priorities,
            "overdue_count": overdue_count
        },
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("메모관리 MCP 서버가 실행 중입니다...")
    print(f"포트: {MEMO_MCP_PORT}")
    mcp.run(transport="sse") 