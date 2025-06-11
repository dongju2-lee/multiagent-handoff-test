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

FITNESS_MCP_NAME = "fitness_tracker"
FITNESS_MCP_HOST = "0.0.0.0"
FITNESS_MCP_PORT = 10009
FITNESS_MCP_INSTRUCTIONS = "피트니스 트래커입니다. 건강관리를 보조하여 운동 계획, 운동 기록, 칼로리 계산, 피트니스 분석 등을 제공합니다."

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fitness_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    FITNESS_MCP_NAME,
    instructions=FITNESS_MCP_INSTRUCTIONS,
    host=FITNESS_MCP_HOST,
    port=FITNESS_MCP_PORT,
)

# 가짜 데이터 저장소
WORKOUTS = {}
WORKOUT_PLANS = {}
EXERCISE_LIBRARY = {}

# 운동 라이브러리 초기 데이터
INITIAL_EXERCISES = [
    {"id": "push_up", "name": "팔굽혀펴기", "category": "상체", "calories_per_minute": 8, "difficulty": "초급"},
    {"id": "pull_up", "name": "턱걸이", "category": "상체", "calories_per_minute": 10, "difficulty": "중급"},
    {"id": "squat", "name": "스쿼트", "category": "하체", "calories_per_minute": 6, "difficulty": "초급"},
    {"id": "lunges", "name": "런지", "category": "하체", "calories_per_minute": 7, "difficulty": "초급"},
    {"id": "plank", "name": "플랭크", "category": "코어", "calories_per_minute": 5, "difficulty": "초급"},
    {"id": "running", "name": "달리기", "category": "유산소", "calories_per_minute": 12, "difficulty": "중급"},
    {"id": "walking", "name": "걷기", "category": "유산소", "calories_per_minute": 4, "difficulty": "초급"},
    {"id": "burpee", "name": "버피", "category": "전신", "calories_per_minute": 15, "difficulty": "고급"},
]

# 초기 운동 라이브러리 로드
for exercise in INITIAL_EXERCISES:
    EXERCISE_LIBRARY[exercise["id"]] = exercise

@mcp.tool()
async def log_workout(
    date: str,
    exercises: List[Dict[str, Any]],
    notes: str = ""
) -> Dict[str, Any]:
    """
    운동 기록을 추가합니다.
    
    Args:
        date (str): 운동 날짜 (YYYY-MM-DD)
        exercises (List[Dict[str, Any]]): 운동 목록 [{"exercise_id": "push_up", "duration_minutes": 10, "sets": 3, "reps": 15}]
        notes (str, optional): 운동 메모
        
    Returns:
        Dict[str, Any]: 기록된 운동 정보
    """
    logger.info(f"운동 기록 추가: {date}")
    
    workout_id = str(uuid.uuid4())
    
    # 총 칼로리 계산
    total_calories = 0
    processed_exercises = []
    
    for exercise in exercises:
        exercise_id = exercise.get("exercise_id")
        if exercise_id not in EXERCISE_LIBRARY:
            continue
            
        exercise_info = EXERCISE_LIBRARY[exercise_id]
        duration = exercise.get("duration_minutes", 0)
        calories_burned = exercise_info["calories_per_minute"] * duration
        total_calories += calories_burned
        
        processed_exercises.append({
            "exercise_id": exercise_id,
            "name": exercise_info["name"],
            "category": exercise_info["category"],
            "duration_minutes": duration,
            "sets": exercise.get("sets", 0),
            "reps": exercise.get("reps", 0),
            "calories_burned": calories_burned
        })
    
    workout_record = {
        "id": workout_id,
        "date": date,
        "exercises": processed_exercises,
        "total_duration_minutes": sum(e["duration_minutes"] for e in processed_exercises),
        "total_calories_burned": total_calories,
        "notes": notes,
        "created_at": datetime.now().isoformat()
    }
    
    WORKOUTS[workout_id] = workout_record
    
    return {
        "success": True,
        "workout": workout_record,
        "message": f"{date} 운동 기록이 성공적으로 추가되었습니다."
    }

@mcp.tool()
async def get_workouts(
    start_date: str = None,
    end_date: str = None,
    category: str = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    운동 기록을 조회합니다.
    
    Args:
        start_date (str, optional): 조회 시작 날짜 (YYYY-MM-DD)
        end_date (str, optional): 조회 종료 날짜 (YYYY-MM-DD)
        category (str, optional): 운동 카테고리 필터
        limit (int, optional): 최대 조회 개수 (기본값: 10)
        
    Returns:
        Dict[str, Any]: 운동 기록 목록
    """
    logger.info(f"운동 기록 조회: {start_date} ~ {end_date}")
    
    results = []
    
    for workout in WORKOUTS.values():
        # 날짜 필터
        if start_date and workout["date"] < start_date:
            continue
        if end_date and workout["date"] > end_date:
            continue
        
        # 카테고리 필터
        if category:
            if not any(e["category"] == category for e in workout["exercises"]):
                continue
        
        results.append(workout)
    
    # 날짜 순으로 정렬 (최신순)
    results.sort(key=lambda x: x["date"], reverse=True)
    
    # 제한 개수 적용
    results = results[:limit]
    
    return {
        "success": True,
        "total_count": len(results),
        "workouts": results,
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "category": category,
            "limit": limit
        }
    }

@mcp.tool()
async def create_workout_plan(
    name: str,
    description: str,
    target_days_per_week: int,
    exercises: List[Dict[str, Any]],
    difficulty_level: str = "중급"
) -> Dict[str, Any]:
    """
    운동 계획을 생성합니다.
    
    Args:
        name (str): 운동 계획 이름
        description (str): 계획 설명
        target_days_per_week (int): 주당 목표 운동 일수
        exercises (List[Dict[str, Any]]): 운동 목록
        difficulty_level (str, optional): 난이도 (초급, 중급, 고급, 기본값: "중급")
        
    Returns:
        Dict[str, Any]: 생성된 운동 계획
    """
    logger.info(f"운동 계획 생성: {name}")
    
    plan_id = str(uuid.uuid4())
    
    # 운동 정보 처리
    processed_exercises = []
    estimated_calories_per_session = 0
    
    for exercise in exercises:
        exercise_id = exercise.get("exercise_id")
        if exercise_id not in EXERCISE_LIBRARY:
            continue
            
        exercise_info = EXERCISE_LIBRARY[exercise_id]
        duration = exercise.get("duration_minutes", 0)
        calories = exercise_info["calories_per_minute"] * duration
        estimated_calories_per_session += calories
        
        processed_exercises.append({
            "exercise_id": exercise_id,
            "name": exercise_info["name"],
            "category": exercise_info["category"],
            "duration_minutes": duration,
            "sets": exercise.get("sets", 0),
            "reps": exercise.get("reps", 0),
            "estimated_calories": calories
        })
    
    workout_plan = {
        "id": plan_id,
        "name": name,
        "description": description,
        "difficulty_level": difficulty_level,
        "target_days_per_week": target_days_per_week,
        "exercises": processed_exercises,
        "estimated_duration_minutes": sum(e["duration_minutes"] for e in processed_exercises),
        "estimated_calories_per_session": estimated_calories_per_session,
        "estimated_weekly_calories": estimated_calories_per_session * target_days_per_week,
        "created_at": datetime.now().isoformat()
    }
    
    WORKOUT_PLANS[plan_id] = workout_plan
    
    return {
        "success": True,
        "plan": workout_plan,
        "message": f"'{name}' 운동 계획이 성공적으로 생성되었습니다."
    }

@mcp.tool()
async def get_workout_plans() -> Dict[str, Any]:
    """
    운동 계획 목록을 조회합니다.
    
    Returns:
        Dict[str, Any]: 운동 계획 목록
    """
    logger.info("운동 계획 목록 조회")
    
    plans = list(WORKOUT_PLANS.values())
    plans.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "total_plans": len(plans),
        "plans": plans
    }

@mcp.tool()
async def suggest_workout(
    available_time_minutes: int,
    preferred_category: str = None,
    difficulty_level: str = "중급",
    target_calories: int = None
) -> Dict[str, Any]:
    """
    조건에 맞는 운동을 추천합니다.
    
    Args:
        available_time_minutes (int): 사용 가능한 시간 (분)
        preferred_category (str, optional): 선호 운동 카테고리
        difficulty_level (str, optional): 선호 난이도 (기본값: "중급")
        target_calories (int, optional): 목표 칼로리 소모량
        
    Returns:
        Dict[str, Any]: 추천 운동
    """
    logger.info(f"운동 추천: {available_time_minutes}분, 카테고리={preferred_category}")
    
    # 조건에 맞는 운동 필터링
    suitable_exercises = []
    
    for exercise in EXERCISE_LIBRARY.values():
        # 카테고리 필터
        if preferred_category and exercise["category"] != preferred_category:
            continue
        
        # 난이도 필터
        if exercise["difficulty"] != difficulty_level:
            continue
        
        suitable_exercises.append(exercise)
    
    if not suitable_exercises:
        return {"error": "조건에 맞는 운동을 찾을 수 없습니다."}
    
    # 추천 운동 구성
    recommended_workout = []
    remaining_time = available_time_minutes
    total_calories = 0
    
    # 랜덤하게 운동 선택하고 시간 분배
    while remaining_time > 10 and suitable_exercises:  # 최소 10분 이상 남았을 때
        exercise = random.choice(suitable_exercises)
        
        # 시간 할당 (남은 시간의 20-50%)
        allocated_time = min(remaining_time, max(10, int(remaining_time * random.uniform(0.2, 0.5))))
        
        calories = exercise["calories_per_minute"] * allocated_time
        total_calories += calories
        
        recommended_workout.append({
            "exercise_id": exercise["id"],
            "name": exercise["name"],
            "category": exercise["category"],
            "duration_minutes": allocated_time,
            "estimated_calories": calories,
            "difficulty": exercise["difficulty"]
        })
        
        remaining_time -= allocated_time
        
        # 목표 칼로리에 도달했으면 종료
        if target_calories and total_calories >= target_calories:
            break
    
    return {
        "recommended_workout": recommended_workout,
        "total_duration_minutes": available_time_minutes - remaining_time,
        "total_estimated_calories": total_calories,
        "criteria": {
            "available_time_minutes": available_time_minutes,
            "preferred_category": preferred_category,
            "difficulty_level": difficulty_level,
            "target_calories": target_calories
        }
    }

@mcp.tool()
async def calculate_calories_burned(
    exercise_name: str,
    duration_minutes: int,
    user_weight_kg: float = 70.0
) -> Dict[str, Any]:
    """
    특정 운동의 칼로리 소모량을 계산합니다.
    
    Args:
        exercise_name (str): 운동 ID
        duration_minutes (int): 운동 시간 (분)
        user_weight_kg (float, optional): 사용자 체중 (kg, 기본값: 70kg)
        
    Returns:
        Dict[str, Any]: 칼로리 계산 결과
    """
    logger.info(f"칼로리 계산: {exercise_name}, {duration_minutes}분")
    
    if exercise_name not in EXERCISE_LIBRARY:
        return {"error": f"운동 ID '{exercise_name}'를 찾을 수 없습니다."}
    
    exercise = EXERCISE_LIBRARY[exercise_name]
    
    # 체중 보정 (기준 체중 70kg)
    weight_factor = user_weight_kg / 70.0
    base_calories = exercise["calories_per_minute"] * duration_minutes
    adjusted_calories = base_calories * weight_factor
    
    return {
        "exercise": exercise,
        "duration_minutes": duration_minutes,
        "user_weight_kg": user_weight_kg,
        "base_calories": base_calories,
        "adjusted_calories": round(adjusted_calories, 1),
        "calories_per_minute": round(adjusted_calories / duration_minutes, 1)
    }

@mcp.tool()
async def get_exercise_library(category: str = None) -> Dict[str, Any]:
    """
    운동 라이브러리를 조회합니다.
    
    Args:
        category (str, optional): 카테고리 필터 ("상체", "하체", "코어", "유산소", "전신")
        
    Returns:
        Dict[str, Any]: 운동 라이브러리
    """
    logger.info(f"운동 라이브러리 조회: 카테고리={category}")
    
    exercises = list(EXERCISE_LIBRARY.values())
    
    if category:
        exercises = [e for e in exercises if e["category"] == category]
    
    # 카테고리별 분류
    categories = {}
    for exercise in exercises:
        cat = exercise["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(exercise)
    
    return {
        "total_exercises": len(exercises),
        "exercises": exercises,
        "categories": categories,
        "available_categories": list(set(e["category"] for e in EXERCISE_LIBRARY.values()))
    }

@mcp.tool()
async def get_fitness_stats(
    start_date: str = None,
    end_date: str = None
) -> Dict[str, Any]:
    """
    피트니스 통계를 제공합니다.
    
    Args:
        start_date (str, optional): 통계 시작 날짜 (YYYY-MM-DD)
        end_date (str, optional): 통계 종료 날짜 (YYYY-MM-DD)
        
    Returns:
        Dict[str, Any]: 피트니스 통계
    """
    logger.info(f"피트니스 통계 조회: {start_date} ~ {end_date}")
    
    # 기간 설정
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 기간 내 운동 필터링
    period_workouts = []
    for workout in WORKOUTS.values():
        if start_date <= workout["date"] <= end_date:
            period_workouts.append(workout)
    
    if not period_workouts:
        return {
            "period": f"{start_date} ~ {end_date}",
            "total_workouts": 0,
            "message": "해당 기간에 운동 기록이 없습니다."
        }
    
    # 통계 계산
    total_workouts = len(period_workouts)
    total_duration = sum(w["total_duration_minutes"] for w in period_workouts)
    total_calories = sum(w["total_calories_burned"] for w in period_workouts)
    
    # 카테고리별 통계
    category_stats = {}
    for workout in period_workouts:
        for exercise in workout["exercises"]:
            category = exercise["category"]
            if category not in category_stats:
                category_stats[category] = {
                    "count": 0,
                    "total_duration": 0,
                    "total_calories": 0
                }
            category_stats[category]["count"] += 1
            category_stats[category]["total_duration"] += exercise["duration_minutes"]
            category_stats[category]["total_calories"] += exercise["calories_burned"]
    
    # 주별 평균
    days_in_period = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days + 1
    weeks_in_period = days_in_period / 7
    
    return {
        "period": f"{start_date} ~ {end_date}",
        "days_in_period": days_in_period,
        "summary": {
            "total_workouts": total_workouts,
            "total_duration_minutes": total_duration,
            "total_calories_burned": total_calories,
            "average_workout_duration": round(total_duration / total_workouts, 1) if total_workouts > 0 else 0,
            "average_calories_per_workout": round(total_calories / total_workouts, 1) if total_workouts > 0 else 0
        },
        "weekly_averages": {
            "workouts_per_week": round(total_workouts / weeks_in_period, 1),
            "duration_per_week": round(total_duration / weeks_in_period, 1),
            "calories_per_week": round(total_calories / weeks_in_period, 1)
        },
        "category_breakdown": category_stats
    }

if __name__ == "__main__":
    print("피트니스 MCP 서버가 실행 중입니다...")
    print(f"포트: {FITNESS_MCP_PORT}")
    mcp.run(transport="sse") 