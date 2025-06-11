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

HEALTH_MCP_NAME = "health_manager"
HEALTH_MCP_HOST = "0.0.0.0"
HEALTH_MCP_PORT = 10008
HEALTH_MCP_INSTRUCTIONS = "건강관리 개인비서입니다. 건강 데이터 추적, 목표 설정, 건강 조언과 의료 정보 관리에 특화된 서비스를 제공합니다."

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("health_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    HEALTH_MCP_NAME,
    instructions=HEALTH_MCP_INSTRUCTIONS,
    host=HEALTH_MCP_HOST,
    port=HEALTH_MCP_PORT,
)

# 가짜 데이터 저장소
HEALTH_RECORDS = {}
HEALTH_GOALS = {}
MEDICATIONS = {}

# 초기 가짜 건강 기록 데이터
INITIAL_HEALTH_RECORDS = [
    {
        "id": str(uuid.uuid4()),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": "vital_signs",
        "data": {
            "blood_pressure": {"systolic": 120, "diastolic": 80},
            "heart_rate": 72,
            "temperature": 36.5,
            "weight": 70.5
        },
        "notes": "정상 범위",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "type": "sleep",
        "data": {
            "sleep_hours": 7.5,
            "sleep_quality": "good",
            "bedtime": "23:30",
            "wake_time": "07:00"
        },
        "notes": "숙면함",
        "created_at": (datetime.now() - timedelta(days=1)).isoformat()
    }
]

# 초기 건강 목표 데이터
INITIAL_HEALTH_GOALS = [
    {
        "id": str(uuid.uuid4()),
        "title": "체중 감량",
        "target_value": 65.0,
        "current_value": 70.5,
        "unit": "kg",
        "target_date": "2024-06-01",
        "status": "active",
        "category": "weight",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "title": "일일 걸음 수",
        "target_value": 10000,
        "current_value": 7500,
        "unit": "steps",
        "target_date": "2024-12-31",
        "status": "active",
        "category": "exercise",
        "created_at": datetime.now().isoformat()
    }
]

# 초기 복용 약물 데이터
INITIAL_MEDICATIONS = [
    {
        "id": str(uuid.uuid4()),
        "name": "종합비타민",
        "dosage": "1정",
        "frequency": "1일 1회",
        "schedule": ["09:00"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "notes": "식후 복용",
        "active": True,
        "created_at": datetime.now().isoformat()
    }
]

# 초기 데이터 로드
for record in INITIAL_HEALTH_RECORDS:
    HEALTH_RECORDS[record["id"]] = record

for goal in INITIAL_HEALTH_GOALS:
    HEALTH_GOALS[goal["id"]] = goal

for medication in INITIAL_MEDICATIONS:
    MEDICATIONS[medication["id"]] = medication

@mcp.tool()
async def add_health_record(
    date: str,
    record_type: str,
    data: Dict[str, Any],
    notes: str = ""
) -> Dict[str, Any]:
    """
    새로운 건강 기록을 추가합니다.
    
    Args:
        date (str): 기록 날짜 (YYYY-MM-DD)
        record_type (str): 기록 유형 ("vital_signs", "sleep", "nutrition", "symptoms", "exercise")
        data (Dict[str, Any]): 건강 데이터
        notes (str, optional): 추가 메모
        
    Returns:
        Dict[str, Any]: 생성된 건강 기록 정보
    """
    logger.info(f"건강 기록 추가: {record_type}, {date}")
    
    valid_types = ["vital_signs", "sleep", "nutrition", "symptoms", "exercise"]
    if record_type not in valid_types:
        return {"error": f"유효하지 않은 기록 유형입니다. 가능한 유형: {valid_types}"}
    
    record_id = str(uuid.uuid4())
    new_record = {
        "id": record_id,
        "date": date,
        "type": record_type,
        "data": data,
        "notes": notes,
        "created_at": datetime.now().isoformat()
    }
    
    HEALTH_RECORDS[record_id] = new_record
    
    return {
        "success": True,
        "record": new_record,
        "message": f"{record_type} 기록이 성공적으로 추가되었습니다."
    }

@mcp.tool()
async def get_health_records(
    start_date: str = None,
    end_date: str = None,
    record_type: str = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    건강 기록을 조회합니다.
    
    Args:
        start_date (str, optional): 조회 시작 날짜 (YYYY-MM-DD)
        end_date (str, optional): 조회 종료 날짜 (YYYY-MM-DD)
        record_type (str, optional): 기록 유형 필터
        limit (int, optional): 최대 조회 개수 (기본값: 10)
        
    Returns:
        Dict[str, Any]: 건강 기록 목록
    """
    logger.info(f"건강 기록 조회: {start_date} ~ {end_date}, 유형: {record_type}")
    
    results = []
    
    for record in HEALTH_RECORDS.values():
        # 날짜 필터
        if start_date and record["date"] < start_date:
            continue
        if end_date and record["date"] > end_date:
            continue
        
        # 유형 필터
        if record_type and record["type"] != record_type:
            continue
        
        results.append(record)
    
    # 날짜 순으로 정렬 (최신순)
    results.sort(key=lambda x: x["date"], reverse=True)
    
    # 제한 개수 적용
    results = results[:limit]
    
    return {
        "success": True,
        "total_count": len(results),
        "records": results,
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "record_type": record_type,
            "limit": limit
        }
    }

@mcp.tool()
async def create_health_goal(
    title: str,
    target_value: float,
    unit: str,
    target_date: str,
    category: str,
    current_value: float = 0.0
) -> Dict[str, Any]:
    """
    새로운 건강 목표를 생성합니다.
    
    Args:
        title (str): 목표 제목
        target_value (float): 목표 수치
        unit (str): 단위 (kg, steps, hours, etc.)
        target_date (str): 목표 날짜 (YYYY-MM-DD)
        category (str): 카테고리 ("weight", "exercise", "sleep", "nutrition")
        current_value (float, optional): 현재 수치 (기본값: 0.0)
        
    Returns:
        Dict[str, Any]: 생성된 건강 목표 정보
    """
    logger.info(f"건강 목표 생성: {title}")
    
    goal_id = str(uuid.uuid4())
    new_goal = {
        "id": goal_id,
        "title": title,
        "target_value": target_value,
        "current_value": current_value,
        "unit": unit,
        "target_date": target_date,
        "status": "active",
        "category": category,
        "created_at": datetime.now().isoformat()
    }
    
    HEALTH_GOALS[goal_id] = new_goal
    
    return {
        "success": True,
        "goal": new_goal,
        "message": f"'{title}' 목표가 성공적으로 생성되었습니다."
    }

@mcp.tool()
async def update_goal_progress(goal_id: str, current_value: float) -> Dict[str, Any]:
    """
    건강 목표의 진행 상황을 업데이트합니다.
    
    Args:
        goal_id (str): 목표 ID
        current_value (float): 현재 수치
        
    Returns:
        Dict[str, Any]: 업데이트된 목표 정보
    """
    logger.info(f"목표 진행 상황 업데이트: {goal_id}")
    
    if goal_id not in HEALTH_GOALS:
        return {"error": f"ID {goal_id}에 해당하는 목표를 찾을 수 없습니다."}
    
    goal = HEALTH_GOALS[goal_id].copy()
    goal["current_value"] = current_value
    goal["updated_at"] = datetime.now().isoformat()
    
    # 달성도 계산
    if goal["target_value"] != 0:
        progress_percentage = (current_value / goal["target_value"]) * 100
        goal["progress_percentage"] = min(progress_percentage, 100)
        
        if progress_percentage >= 100:
            goal["status"] = "completed"
    
    HEALTH_GOALS[goal_id] = goal
    
    return {
        "success": True,
        "goal": goal,
        "message": "목표 진행 상황이 업데이트되었습니다."
    }

@mcp.tool()
async def add_medication(
    name: str,
    dosage: str,
    frequency: str,
    schedule: List[str],
    start_date: str,
    end_date: str = None,
    notes: str = ""
) -> Dict[str, Any]:
    """
    새로운 복용 약물을 추가합니다.
    
    Args:
        name (str): 약물명
        dosage (str): 복용량 (예: "1정", "5ml")
        frequency (str): 복용 빈도 (예: "1일 3회", "필요시")
        schedule (List[str]): 복용 시간 (예: ["08:00", "12:00", "18:00"])
        start_date (str): 복용 시작일 (YYYY-MM-DD)
        end_date (str, optional): 복용 종료일 (YYYY-MM-DD)
        notes (str, optional): 추가 메모
        
    Returns:
        Dict[str, Any]: 추가된 약물 정보
    """
    logger.info(f"약물 추가: {name}")
    
    medication_id = str(uuid.uuid4())
    new_medication = {
        "id": medication_id,
        "name": name,
        "dosage": dosage,
        "frequency": frequency,
        "schedule": schedule,
        "start_date": start_date,
        "end_date": end_date,
        "notes": notes,
        "active": True,
        "created_at": datetime.now().isoformat()
    }
    
    MEDICATIONS[medication_id] = new_medication
    
    return {
        "success": True,
        "medication": new_medication,
        "message": f"'{name}' 약물이 성공적으로 추가되었습니다."
    }

@mcp.tool()
async def get_medication_schedule(date: str = None) -> Dict[str, Any]:
    """
    약물 복용 일정을 조회합니다.
    
    Args:
        date (str, optional): 조회할 날짜 (YYYY-MM-DD), 기본값은 오늘
        
    Returns:
        Dict[str, Any]: 약물 복용 일정
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"약물 일정 조회: {date}")
    
    schedule = []
    target_date = datetime.strptime(date, "%Y-%m-%d")
    
    for medication in MEDICATIONS.values():
        if not medication["active"]:
            continue
        
        start_date = datetime.strptime(medication["start_date"], "%Y-%m-%d")
        end_date = None
        if medication["end_date"]:
            end_date = datetime.strptime(medication["end_date"], "%Y-%m-%d")
        
        # 복용 기간 확인
        if target_date < start_date:
            continue
        if end_date and target_date > end_date:
            continue
        
        # 복용 시간별로 일정 생성
        for time in medication["schedule"]:
            schedule.append({
                "medication_id": medication["id"],
                "name": medication["name"],
                "dosage": medication["dosage"],
                "time": time,
                "notes": medication["notes"]
            })
    
    # 시간 순으로 정렬
    schedule.sort(key=lambda x: x["time"])
    
    return {
        "date": date,
        "total_medications": len(schedule),
        "schedule": schedule
    }

@mcp.tool()
async def get_health_insights() -> Dict[str, Any]:
    """
    건강 데이터 기반 인사이트를 제공합니다.
    
    Returns:
        Dict[str, Any]: 건강 인사이트
    """
    logger.info("건강 인사이트 생성")
    
    insights = []
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 최근 7일간의 데이터 분석
    recent_records = []
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    for record in HEALTH_RECORDS.values():
        if record["date"] >= cutoff_date:
            recent_records.append(record)
    
    # 수면 패턴 분석
    sleep_records = [r for r in recent_records if r["type"] == "sleep"]
    if sleep_records:
        avg_sleep = sum(r["data"].get("sleep_hours", 0) for r in sleep_records) / len(sleep_records)
        if avg_sleep < 7:
            insights.append({
                "type": "sleep",
                "level": "warning",
                "message": f"최근 평균 수면시간이 {avg_sleep:.1f}시간으로 권장 수면시간(7-9시간)보다 부족합니다.",
                "recommendation": "규칙적인 수면 패턴을 만들고 취침 전 스마트폰 사용을 줄여보세요."
            })
        else:
            insights.append({
                "type": "sleep",
                "level": "good",
                "message": f"최근 평균 수면시간이 {avg_sleep:.1f}시간으로 양호합니다.",
                "recommendation": "현재의 수면 패턴을 유지하세요."
            })
    
    # 목표 달성도 분석
    active_goals = [g for g in HEALTH_GOALS.values() if g["status"] == "active"]
    for goal in active_goals:
        if goal["target_value"] > 0:
            progress = (goal["current_value"] / goal["target_value"]) * 100
            if progress >= 80:
                insights.append({
                    "type": "goal",
                    "level": "good",
                    "message": f"'{goal['title']}' 목표 달성도가 {progress:.1f}%로 우수합니다.",
                    "recommendation": "목표 달성까지 조금 더 화이팅하세요!"
                })
            elif progress < 50:
                insights.append({
                    "type": "goal",
                    "level": "warning",
                    "message": f"'{goal['title']}' 목표 달성도가 {progress:.1f}%로 저조합니다.",
                    "recommendation": "목표 달성을 위한 구체적인 계획을 세워보세요."
                })
    
    # 일반적인 건강 조언
    general_tips = [
        "하루 8잔 이상의 물을 마시세요.",
        "규칙적인 운동으로 건강을 유지하세요.",
        "스트레스 관리를 위해 명상이나 요가를 시도해보세요.",
        "균형 잡힌 식단으로 영양소를 골고루 섭취하세요."
    ]
    
    insights.append({
        "type": "general",
        "level": "info",
        "message": "건강한 생활습관 팁",
        "recommendation": random.choice(general_tips)
    })
    
    return {
        "date": current_date,
        "total_insights": len(insights),
        "insights": insights,
        "data_period": f"{cutoff_date} ~ {current_date}"
    }

@mcp.tool()
async def get_health_summary() -> Dict[str, Any]:
    """
    전체적인 건강 상태 요약을 제공합니다.
    
    Returns:
        Dict[str, Any]: 건강 상태 요약
    """
    logger.info("건강 상태 요약 생성")
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 최근 기록
    recent_record = None
    latest_date = None
    for record in HEALTH_RECORDS.values():
        if not latest_date or record["date"] > latest_date:
            latest_date = record["date"]
            recent_record = record
    
    # 활성 목표 수
    active_goals = len([g for g in HEALTH_GOALS.values() if g["status"] == "active"])
    completed_goals = len([g for g in HEALTH_GOALS.values() if g["status"] == "completed"])
    
    # 활성 약물 수
    active_medications = len([m for m in MEDICATIONS.values() if m["active"]])
    
    # 이번 주 기록 수
    week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    this_week_records = len([r for r in HEALTH_RECORDS.values() if r["date"] >= week_start])
    
    return {
        "summary_date": current_date,
        "recent_record": {
            "date": latest_date,
            "type": recent_record["type"] if recent_record else None,
            "available": recent_record is not None
        },
        "goals": {
            "active": active_goals,
            "completed": completed_goals,
            "total": len(HEALTH_GOALS)
        },
        "medications": {
            "active": active_medications,
            "total": len(MEDICATIONS)
        },
        "activity": {
            "records_this_week": this_week_records,
            "total_records": len(HEALTH_RECORDS)
        }
    }

if __name__ == "__main__":
    print("건강관리 MCP 서버가 실행 중입니다...")
    print(f"포트: {HEALTH_MCP_PORT}")
    mcp.run(transport="sse") 