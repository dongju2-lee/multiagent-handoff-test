from mcp.server.fastmcp import FastMCP
import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import uuid
from datetime import datetime, timedelta
import random

# 환경 변수 로드
load_dotenv()

SCHEDULE_MCP_NAME = "schedule_manager"
SCHEDULE_MCP_HOST = "0.0.0.0"
SCHEDULE_MCP_PORT = 10002
SCHEDULE_MCP_INSTRUCTIONS = "일정관리 개인비서입니다. 스케줄, 약속, 캘린더 관리에 특화된 서비스를 제공합니다."

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("schedule_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    SCHEDULE_MCP_NAME,
    instructions=SCHEDULE_MCP_INSTRUCTIONS,
    host=SCHEDULE_MCP_HOST,
    port=SCHEDULE_MCP_PORT,
)

# 가짜 일정 데이터 저장소
SCHEDULES = {}

# 초기 가짜 데이터
INITIAL_SCHEDULES = [
    {
        "id": str(uuid.uuid4()),
        "title": "팀 회의",
        "start_time": "2024-01-15T10:00:00",
        "end_time": "2024-01-15T11:00:00",
        "location": "회의실 A",
        "description": "주간 팀 회의",
        "attendees": ["김철수", "이영희"],
        "reminder": {"enabled": True, "minutes_before": 10},
        "created_at": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "title": "점심 약속",
        "start_time": "2024-01-15T12:00:00",
        "end_time": "2024-01-15T13:00:00",
        "location": "강남역 맛집",
        "description": "친구와 점심 약속",
        "attendees": ["박민수"],
        "reminder": {"enabled": True, "minutes_before": 30},
        "created_at": datetime.now().isoformat()
    }
]

# 초기 데이터 로드
for schedule in INITIAL_SCHEDULES:
    SCHEDULES[schedule["id"]] = schedule

@mcp.tool()
async def create_schedule(
    title: str,
    start_time: str,
    end_time: str,
    location: str = "",
    description: str = "",
    attendees: List[str] = None,
    reminder_minutes: int = 15
) -> Dict[str, Any]:
    """
    새로운 일정을 생성합니다.
    
    Args:
        title (str): 일정 제목
        start_time (str): 시작 시간 (ISO 형식: YYYY-MM-DDTHH:MM:SS)
        end_time (str): 종료 시간 (ISO 형식: YYYY-MM-DDTHH:MM:SS)
        location (str, optional): 장소
        description (str, optional): 설명
        attendees (List[str], optional): 참석자 목록
        reminder_minutes (int, optional): 알림 시간 (분 단위, 기본값: 15분)
        
    Returns:
        Dict[str, Any]: 생성된 일정 정보
    """
    logger.info(f"일정 생성 요청: {title}, {start_time} - {end_time}")
    
    try:
        # 시간 유효성 검사
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        
        if start_dt >= end_dt:
            return {"error": "시작 시간이 종료 시간보다 늦을 수 없습니다."}
        
        schedule_id = str(uuid.uuid4())
        new_schedule = {
            "id": schedule_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "description": description,
            "attendees": attendees or [],
            "reminder": {
                "enabled": True,
                "minutes_before": reminder_minutes
            },
            "created_at": datetime.now().isoformat()
        }
        
        SCHEDULES[schedule_id] = new_schedule
        
        return {
            "success": True,
            "schedule": new_schedule,
            "message": f"'{title}' 일정이 성공적으로 생성되었습니다."
        }
        
    except ValueError as e:
        return {"error": f"잘못된 시간 형식입니다: {str(e)}"}
    except Exception as e:
        return {"error": f"일정 생성 중 오류가 발생했습니다: {str(e)}"}

@mcp.tool()
async def get_schedule(schedule_id: str) -> Dict[str, Any]:
    """
    특정 일정의 상세 정보를 조회합니다.
    
    Args:
        schedule_id (str): 일정 ID
        
    Returns:
        Dict[str, Any]: 일정 상세 정보
    """
    logger.info(f"일정 조회 요청: {schedule_id}")
    
    if schedule_id not in SCHEDULES:
        return {"error": f"ID {schedule_id}에 해당하는 일정을 찾을 수 없습니다."}
    
    return {
        "success": True,
        "schedule": SCHEDULES[schedule_id]
    }

@mcp.tool()
async def list_schedules(
    start_date: str = None,
    end_date: str = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    일정 목록을 조회합니다.
    
    Args:
        start_date (str, optional): 조회 시작 날짜 (YYYY-MM-DD)
        end_date (str, optional): 조회 종료 날짜 (YYYY-MM-DD)
        limit (int, optional): 최대 조회 개수 (기본값: 10)
        
    Returns:
        Dict[str, Any]: 일정 목록
    """
    logger.info(f"일정 목록 조회: {start_date} ~ {end_date}, 제한: {limit}")
    
    try:
        schedules = list(SCHEDULES.values())
        
        # 날짜 필터링
        if start_date:
            start_dt = datetime.fromisoformat(start_date + "T00:00:00")
            schedules = [s for s in schedules if datetime.fromisoformat(s["start_time"]) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date + "T23:59:59")
            schedules = [s for s in schedules if datetime.fromisoformat(s["start_time"]) <= end_dt]
        
        # 시작 시간 순으로 정렬
        schedules.sort(key=lambda x: x["start_time"])
        
        # 제한 개수 적용
        schedules = schedules[:limit]
        
        return {
            "success": True,
            "total_count": len(schedules),
            "schedules": schedules,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit
            }
        }
        
    except Exception as e:
        return {"error": f"일정 목록 조회 중 오류가 발생했습니다: {str(e)}"}

@mcp.tool()
async def update_schedule(
    schedule_id: str,
    title: str = None,
    start_time: str = None,
    end_time: str = None,
    location: str = None,
    description: str = None,
    attendees: List[str] = None,
    reminder_minutes: int = None
) -> Dict[str, Any]:
    """
    기존 일정을 수정합니다.
    
    Args:
        schedule_id (str): 수정할 일정 ID
        title (str, optional): 새로운 제목
        start_time (str, optional): 새로운 시작 시간
        end_time (str, optional): 새로운 종료 시간
        location (str, optional): 새로운 장소
        description (str, optional): 새로운 설명
        attendees (List[str], optional): 새로운 참석자 목록
        reminder_minutes (int, optional): 새로운 알림 시간
        
    Returns:
        Dict[str, Any]: 수정된 일정 정보
    """
    logger.info(f"일정 수정 요청: {schedule_id}")
    
    if schedule_id not in SCHEDULES:
        return {"error": f"ID {schedule_id}에 해당하는 일정을 찾을 수 없습니다."}
    
    try:
        schedule = SCHEDULES[schedule_id].copy()
        
        # 수정할 필드들 업데이트
        if title is not None:
            schedule["title"] = title
        if start_time is not None:
            schedule["start_time"] = start_time
        if end_time is not None:
            schedule["end_time"] = end_time
        if location is not None:
            schedule["location"] = location
        if description is not None:
            schedule["description"] = description
        if attendees is not None:
            schedule["attendees"] = attendees
        if reminder_minutes is not None:
            schedule["reminder"]["minutes_before"] = reminder_minutes
        
        # 시간 유효성 검사
        if start_time or end_time:
            start_dt = datetime.fromisoformat(schedule["start_time"])
            end_dt = datetime.fromisoformat(schedule["end_time"])
            
            if start_dt >= end_dt:
                return {"error": "시작 시간이 종료 시간보다 늦을 수 없습니다."}
        
        schedule["updated_at"] = datetime.now().isoformat()
        SCHEDULES[schedule_id] = schedule
        
        return {
            "success": True,
            "schedule": schedule,
            "message": f"일정이 성공적으로 수정되었습니다."
        }
        
    except Exception as e:
        return {"error": f"일정 수정 중 오류가 발생했습니다: {str(e)}"}

@mcp.tool()
async def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    """
    일정을 삭제합니다.
    
    Args:
        schedule_id (str): 삭제할 일정 ID
        
    Returns:
        Dict[str, Any]: 삭제 결과
    """
    logger.info(f"일정 삭제 요청: {schedule_id}")
    
    if schedule_id not in SCHEDULES:
        return {"error": f"ID {schedule_id}에 해당하는 일정을 찾을 수 없습니다."}
    
    deleted_schedule = SCHEDULES.pop(schedule_id)
    
    return {
        "success": True,
        "deleted_schedule": deleted_schedule,
        "message": f"'{deleted_schedule['title']}' 일정이 성공적으로 삭제되었습니다."
    }

@mcp.tool()
async def check_conflicts(start_time: str, end_time: str, exclude_id: str = None) -> Dict[str, Any]:
    """
    시간 충돌을 확인합니다.
    
    Args:
        start_time (str): 확인할 시작 시간 (ISO 형식)
        end_time (str): 확인할 종료 시간 (ISO 형식)
        exclude_id (str, optional): 충돌 확인에서 제외할 일정 ID
        
    Returns:
        Dict[str, Any]: 충돌 정보
    """
    logger.info(f"시간 충돌 확인: {start_time} - {end_time}")
    
    try:
        check_start = datetime.fromisoformat(start_time)
        check_end = datetime.fromisoformat(end_time)
        
        conflicts = []
        
        for schedule_id, schedule in SCHEDULES.items():
            if exclude_id and schedule_id == exclude_id:
                continue
                
            schedule_start = datetime.fromisoformat(schedule["start_time"])
            schedule_end = datetime.fromisoformat(schedule["end_time"])
            
            # 시간 겹침 확인
            if (check_start < schedule_end and check_end > schedule_start):
                conflicts.append({
                    "id": schedule_id,
                    "title": schedule["title"],
                    "start_time": schedule["start_time"],
                    "end_time": schedule["end_time"]
                })
        
        return {
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "checked_period": {
                "start_time": start_time,
                "end_time": end_time
            }
        }
        
    except Exception as e:
        return {"error": f"충돌 확인 중 오류가 발생했습니다: {str(e)}"}

@mcp.tool()
async def get_available_slots(
    date: str,
    duration_minutes: int = 60,
    start_hour: int = 9,
    end_hour: int = 18
) -> Dict[str, Any]:
    """
    지정된 날짜의 가능한 시간 슬롯을 찾습니다.
    
    Args:
        date (str): 날짜 (YYYY-MM-DD)
        duration_minutes (int, optional): 필요한 시간 (분 단위, 기본값: 60분)
        start_hour (int, optional): 검색 시작 시간 (기본값: 9시)
        end_hour (int, optional): 검색 종료 시간 (기본값: 18시)
        
    Returns:
        Dict[str, Any]: 가능한 시간 슬롯 목록
    """
    logger.info(f"가능한 시간 슬롯 검색: {date}, {duration_minutes}분, {start_hour}-{end_hour}시")
    
    try:
        target_date = datetime.fromisoformat(date + "T00:00:00")
        
        # 해당 날짜의 일정들 필터링
        day_schedules = []
        for schedule in SCHEDULES.values():
            schedule_start = datetime.fromisoformat(schedule["start_time"])
            if schedule_start.date() == target_date.date():
                day_schedules.append({
                    "start": schedule_start,
                    "end": datetime.fromisoformat(schedule["end_time"])
                })
        
        # 시간 순으로 정렬
        day_schedules.sort(key=lambda x: x["start"])
        
        # 가능한 슬롯 찾기
        available_slots = []
        current_time = target_date.replace(hour=start_hour, minute=0, second=0)
        end_time = target_date.replace(hour=end_hour, minute=0, second=0)
        
        for schedule in day_schedules:
            if current_time + timedelta(minutes=duration_minutes) <= schedule["start"]:
                available_slots.append({
                    "start_time": current_time.isoformat(),
                    "end_time": (current_time + timedelta(minutes=duration_minutes)).isoformat(),
                    "duration_minutes": duration_minutes
                })
            current_time = max(current_time, schedule["end"])
        
        # 마지막 슬롯 확인
        if current_time + timedelta(minutes=duration_minutes) <= end_time:
            available_slots.append({
                "start_time": current_time.isoformat(),
                "end_time": (current_time + timedelta(minutes=duration_minutes)).isoformat(),
                "duration_minutes": duration_minutes
            })
        
        return {
            "date": date,
            "duration_minutes": duration_minutes,
            "search_period": f"{start_hour}:00 - {end_hour}:00",
            "available_slots": available_slots,
            "total_slots": len(available_slots)
        }
        
    except Exception as e:
        return {"error": f"가능한 시간 슬롯 검색 중 오류가 발생했습니다: {str(e)}"}

if __name__ == "__main__":
    print("일정관리 MCP 서버가 실행 중입니다...")
    print(f"포트: {SCHEDULE_MCP_PORT}")
    mcp.run(transport="sse") 