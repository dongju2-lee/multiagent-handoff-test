from mcp.server.fastmcp import FastMCP
import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime, timedelta
import calendar

# 환경 변수 로드
load_dotenv()

CALENDAR_MCP_NAME = "calendar_helper"
CALENDAR_MCP_HOST = "0.0.0.0"
CALENDAR_MCP_PORT = 10003
CALENDAR_MCP_INSTRUCTIONS = "캘린더 도우미입니다. 일정관리를 보조하여 캘린더 보기, 날짜 계산, 반복 일정 처리 등을 제공합니다."

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("calendar_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    CALENDAR_MCP_NAME,
    instructions=CALENDAR_MCP_INSTRUCTIONS,
    host=CALENDAR_MCP_HOST,
    port=CALENDAR_MCP_PORT,
)

@mcp.tool()
async def get_monthly_calendar(year: int, month: int) -> Dict[str, Any]:
    """
    월별 캘린더를 생성합니다.
    
    Args:
        year (int): 연도
        month (int): 월 (1-12)
        
    Returns:
        Dict[str, Any]: 월별 캘린더 정보
    """
    logger.info(f"월별 캘린더 조회: {year}년 {month}월")
    
    try:
        # 월별 캘린더 생성
        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]
        
        # 주별로 정리
        weeks = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({"day": None, "date": None})
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    week_data.append({
                        "day": day,
                        "date": date_str,
                        "weekday": calendar.weekday(year, month, day)
                    })
            weeks.append(week_data)
        
        return {
            "year": year,
            "month": month,
            "month_name": month_name,
            "total_days": calendar.monthrange(year, month)[1],
            "first_weekday": calendar.monthrange(year, month)[0],
            "weeks": weeks,
            "weekday_names": list(calendar.day_name)
        }
        
    except Exception as e:
        return {"error": f"캘린더 생성 오류: {str(e)}"}

@mcp.tool()
async def calculate_date_difference(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    두 날짜 사이의 차이를 계산합니다.
    
    Args:
        start_date (str): 시작 날짜 (YYYY-MM-DD)
        end_date (str): 종료 날짜 (YYYY-MM-DD)
        
    Returns:
        Dict[str, Any]: 날짜 차이 정보
    """
    logger.info(f"날짜 차이 계산: {start_date} ~ {end_date}")
    
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        difference = end_dt - start_dt
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": difference.days,
            "weeks": difference.days // 7,
            "remaining_days": difference.days % 7,
            "business_days": len([d for d in range(difference.days + 1) 
                                if (start_dt + timedelta(days=d)).weekday() < 5])
        }
        
    except Exception as e:
        return {"error": f"날짜 계산 오류: {str(e)}"}

@mcp.tool()
async def get_date_info(date: str) -> Dict[str, Any]:
    """
    특정 날짜의 상세 정보를 제공합니다.
    
    Args:
        date (str): 날짜 (YYYY-MM-DD)
        
    Returns:
        Dict[str, Any]: 날짜 정보
    """
    logger.info(f"날짜 정보 조회: {date}")
    
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        
        return {
            "date": date,
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "weekday": dt.weekday(),
            "weekday_name": calendar.day_name[dt.weekday()],
            "month_name": calendar.month_name[dt.month],
            "day_of_year": dt.timetuple().tm_yday,
            "week_of_year": dt.isocalendar()[1],
            "is_weekend": dt.weekday() >= 5,
            "is_leap_year": calendar.isleap(dt.year)
        }
        
    except Exception as e:
        return {"error": f"날짜 정보 조회 오류: {str(e)}"}

@mcp.tool()
async def generate_recurring_dates(
    start_date: str,
    recurrence_type: str,
    interval: int = 1,
    count: int = 10,
    end_date: str = None
) -> Dict[str, Any]:
    """
    반복 일정의 날짜들을 생성합니다.
    
    Args:
        start_date (str): 시작 날짜 (YYYY-MM-DD)
        recurrence_type (str): 반복 유형 ("daily", "weekly", "monthly", "yearly")
        interval (int, optional): 간격 (기본값: 1)
        count (int, optional): 생성할 개수 (기본값: 10)
        end_date (str, optional): 종료 날짜 (YYYY-MM-DD)
        
    Returns:
        Dict[str, Any]: 반복 날짜 목록
    """
    logger.info(f"반복 일정 생성: {start_date}, {recurrence_type}, 간격={interval}")
    
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = None
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        dates = []
        current_dt = start_dt
        
        for i in range(count):
            # 종료 날짜 확인
            if end_dt and current_dt > end_dt:
                break
                
            dates.append({
                "date": current_dt.strftime("%Y-%m-%d"),
                "weekday": calendar.day_name[current_dt.weekday()],
                "occurrence": i + 1
            })
            
            # 다음 날짜 계산
            if recurrence_type == "daily":
                current_dt += timedelta(days=interval)
            elif recurrence_type == "weekly":
                current_dt += timedelta(weeks=interval)
            elif recurrence_type == "monthly":
                # 월 단위 계산 (복잡하므로 간단히 30일로 근사)
                current_dt += timedelta(days=30 * interval)
            elif recurrence_type == "yearly":
                # 년 단위 계산 (365일로 근사)
                current_dt += timedelta(days=365 * interval)
            else:
                return {"error": f"지원하지 않는 반복 유형: {recurrence_type}"}
        
        return {
            "start_date": start_date,
            "recurrence_type": recurrence_type,
            "interval": interval,
            "total_dates": len(dates),
            "dates": dates
        }
        
    except Exception as e:
        return {"error": f"반복 일정 생성 오류: {str(e)}"}

@mcp.tool()
async def find_available_time_blocks(
    date: str,
    duration_minutes: int,
    working_hours: Dict[str, str] = None,
    exclude_times: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    특정 날짜에서 사용 가능한 시간 블록을 찾습니다.
    
    Args:
        date (str): 날짜 (YYYY-MM-DD)
        duration_minutes (int): 필요한 시간 (분)
        working_hours (Dict[str, str], optional): 근무 시간 {"start": "09:00", "end": "18:00"}
        exclude_times (List[Dict[str, str]], optional): 제외할 시간대들
        
    Returns:
        Dict[str, Any]: 사용 가능한 시간 블록들
    """
    logger.info(f"시간 블록 검색: {date}, {duration_minutes}분")
    
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
        
        # 기본 근무 시간 설정
        if not working_hours:
            working_hours = {"start": "09:00", "end": "18:00"}
        
        start_time = datetime.strptime(f"{date} {working_hours['start']}", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{date} {working_hours['end']}", "%Y-%m-%d %H:%M")
        
        # 제외할 시간대 처리
        blocked_times = []
        if exclude_times:
            for block in exclude_times:
                blocked_start = datetime.strptime(f"{date} {block['start']}", "%Y-%m-%d %H:%M")
                blocked_end = datetime.strptime(f"{date} {block['end']}", "%Y-%m-%d %H:%M")
                blocked_times.append({"start": blocked_start, "end": blocked_end})
        
        # 사용 가능한 시간 블록 찾기
        available_blocks = []
        current_time = start_time
        
        # 시간 블록들을 정렬
        blocked_times.sort(key=lambda x: x["start"])
        
        for blocked in blocked_times:
            # 현재 시간부터 차단된 시간 전까지 확인
            if current_time + timedelta(minutes=duration_minutes) <= blocked["start"]:
                available_blocks.append({
                    "start_time": current_time.strftime("%H:%M"),
                    "end_time": (current_time + timedelta(minutes=duration_minutes)).strftime("%H:%M"),
                    "duration_minutes": duration_minutes
                })
            current_time = max(current_time, blocked["end"])
        
        # 마지막 블록 이후 시간 확인
        if current_time + timedelta(minutes=duration_minutes) <= end_time:
            available_blocks.append({
                "start_time": current_time.strftime("%H:%M"),
                "end_time": (current_time + timedelta(minutes=duration_minutes)).strftime("%H:%M"),
                "duration_minutes": duration_minutes
            })
        
        return {
            "date": date,
            "duration_minutes": duration_minutes,
            "working_hours": working_hours,
            "total_available_blocks": len(available_blocks),
            "available_blocks": available_blocks
        }
        
    except Exception as e:
        return {"error": f"시간 블록 검색 오류: {str(e)}"}

@mcp.tool()
async def get_holidays_info(year: int, country: str = "KR") -> Dict[str, Any]:
    """
    연도별 공휴일 정보를 제공합니다. (간단한 한국 공휴일)
    
    Args:
        year (int): 연도
        country (str, optional): 국가 코드 (기본값: "KR")
        
    Returns:
        Dict[str, Any]: 공휴일 정보
    """
    logger.info(f"공휴일 조회: {year}년, {country}")
    
    # 간단한 한국 공휴일 (고정 날짜만)
    korean_holidays = [
        {"date": f"{year}-01-01", "name": "신정", "type": "national"},
        {"date": f"{year}-03-01", "name": "삼일절", "type": "national"},
        {"date": f"{year}-05-05", "name": "어린이날", "type": "national"},
        {"date": f"{year}-06-06", "name": "현충일", "type": "national"},
        {"date": f"{year}-08-15", "name": "광복절", "type": "national"},
        {"date": f"{year}-10-03", "name": "개천절", "type": "national"},
        {"date": f"{year}-10-09", "name": "한글날", "type": "national"},
        {"date": f"{year}-12-25", "name": "크리스마스", "type": "national"},
    ]
    
    # 요일 정보 추가
    holidays_with_weekday = []
    for holiday in korean_holidays:
        date_obj = datetime.strptime(holiday["date"], "%Y-%m-%d")
        holiday_info = holiday.copy()
        holiday_info["weekday"] = calendar.day_name[date_obj.weekday()]
        holiday_info["is_weekend"] = date_obj.weekday() >= 5
        holidays_with_weekday.append(holiday_info)
    
    return {
        "year": year,
        "country": country,
        "total_holidays": len(holidays_with_weekday),
        "holidays": holidays_with_weekday
    }

if __name__ == "__main__":
    print("캘린더 MCP 서버가 실행 중입니다...")
    print(f"포트: {CALENDAR_MCP_PORT}")
    mcp.run(transport="sse") 