from mcp.server.fastmcp import FastMCP
import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import random
from datetime import datetime

# 환경 변수 로드
load_dotenv()

GENERAL_MCP_NAME = "general_consulting"
GENERAL_MCP_HOST = "0.0.0.0"
GENERAL_MCP_PORT = 10001
GENERAL_MCP_INSTRUCTIONS = "일반상담 개인비서입니다. 일상적인 질문과 다양한 도움 요청에 친절하고 전문적으로 응답합니다."

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("general_consulting_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    GENERAL_MCP_NAME,
    instructions=GENERAL_MCP_INSTRUCTIONS,
    host=GENERAL_MCP_HOST,
    port=GENERAL_MCP_PORT,
)

# 가짜 데이터
FAQ_DATA = [
    {"id": 1, "question": "날씨 정보는 어떻게 확인하나요?", "answer": "날씨 앱이나 웹사이트를 통해 실시간 날씨 정보를 확인할 수 있습니다.", "category": "일상"},
    {"id": 2, "question": "은행 업무 시간은 언제인가요?", "answer": "일반적으로 평일 9시-16시, 토요일 9시-13시입니다. 은행마다 다를 수 있으니 확인이 필요합니다.", "category": "금융"},
    {"id": 3, "question": "택배 배송 시간은 얼마나 걸리나요?", "answer": "일반택배는 1-2일, 당일배송은 주문 당일, 새벽배송은 다음날 아침에 도착합니다.", "category": "배송"},
    {"id": 4, "question": "여권 발급은 어디서 하나요?", "answer": "여권사무대행기관이나 시청, 구청의 여권 발급 창구에서 신청할 수 있습니다.", "category": "공공서비스"},
    {"id": 5, "question": "교통카드 충전은 어디서 하나요?", "answer": "지하철역, 편의점, 교통카드 충전기에서 충전 가능합니다.", "category": "교통"},
]

ADVICE_CATEGORIES = {
    "생활": ["효율적인 시간 관리", "건강한 라이프스타일", "가계부 관리법", "정리정돈 습관"],
    "인간관계": ["커뮤니케이션 스킬", "갈등 해결 방법", "네트워킹 팁", "가족 관계 개선"],
    "자기계발": ["목표 설정 방법", "학습 효율성", "독서 습관", "새로운 취미 찾기"],
    "업무": ["업무 생산성", "스트레스 관리", "워라밸 유지", "커리어 개발"],
}

@mcp.tool()
async def search_faq(keyword: str, category: str = None) -> Dict[str, Any]:
    """
    자주 묻는 질문(FAQ)을 검색합니다.
    
    Args:
        keyword (str): 검색할 키워드
        category (str, optional): 카테고리 필터 ("일상", "금융", "배송", "공공서비스", "교통")
        
    Returns:
        Dict[str, Any]: 검색된 FAQ 목록
    """
    logger.info(f"FAQ 검색: 키워드={keyword}, 카테고리={category}")
    
    results = []
    for faq in FAQ_DATA:
        # 키워드 매칭
        if keyword.lower() in faq["question"].lower() or keyword.lower() in faq["answer"].lower():
            # 카테고리 필터 적용
            if category is None or faq["category"] == category:
                results.append(faq)
    
    return {
        "total_count": len(results),
        "keyword": keyword,
        "category": category,
        "results": results
    }

@mcp.tool()
async def get_advice(category: str, topic: str = None) -> Dict[str, Any]:
    """
    특정 분야의 조언을 제공합니다.
    
    Args:
        category (str): 조언 분야 ("생활", "인간관계", "자기계발", "업무")
        topic (str, optional): 구체적인 주제
        
    Returns:
        Dict[str, Any]: 조언 내용
    """
    logger.info(f"조언 요청: 분야={category}, 주제={topic}")
    
    if category not in ADVICE_CATEGORIES:
        return {
            "error": f"지원하지 않는 카테고리입니다. 가능한 카테고리: {list(ADVICE_CATEGORIES.keys())}"
        }
    
    available_topics = ADVICE_CATEGORIES[category]
    
    if topic and topic in available_topics:
        selected_topic = topic
    else:
        selected_topic = random.choice(available_topics)
    
    # 가짜 조언 생성
    advice_content = f"{selected_topic}에 대한 조언입니다. 이는 일반적인 가이드라인이며, 개인의 상황에 따라 다를 수 있습니다."
    
    return {
        "category": category,
        "topic": selected_topic,
        "advice": advice_content,
        "timestamp": datetime.now().isoformat(),
        "available_topics": available_topics
    }

@mcp.tool()
async def get_quick_info(info_type: str) -> Dict[str, Any]:
    """
    빠른 정보를 제공합니다.
    
    Args:
        info_type (str): 정보 타입 ("time", "date", "weather", "exchange_rate", "news")
        
    Returns:
        Dict[str, Any]: 요청된 정보
    """
    logger.info(f"빠른 정보 요청: 타입={info_type}")
    
    current_time = datetime.now()
    
    info_responses = {
        "time": {
            "type": "현재 시간",
            "value": current_time.strftime("%H:%M:%S"),
            "date": current_time.strftime("%Y년 %m월 %d일"),
            "weekday": current_time.strftime("%A")
        },
        "date": {
            "type": "오늘 날짜",
            "value": current_time.strftime("%Y년 %m월 %d일"),
            "weekday": current_time.strftime("%A"),
            "week_of_year": current_time.isocalendar()[1]
        },
        "weather": {
            "type": "날씨 정보",
            "temperature": f"{random.randint(15, 25)}°C",
            "condition": random.choice(["맑음", "흐림", "비", "눈", "구름조금"]),
            "humidity": f"{random.randint(40, 80)}%",
            "location": "서울"
        },
        "exchange_rate": {
            "type": "환율 정보",
            "usd_krw": f"{random.randint(1300, 1400):.0f}원",
            "eur_krw": f"{random.randint(1400, 1500):.0f}원",
            "jpy_krw": f"{random.randint(8, 12):.1f}원",
            "update_time": current_time.strftime("%H:%M")
        },
        "news": {
            "type": "주요 뉴스",
            "headlines": [
                "경제 동향 업데이트",
                "새로운 기술 트렌드 소개",
                "생활 정보 안내",
                "건강 관리 팁"
            ],
            "update_time": current_time.strftime("%H:%M")
        }
    }
    
    if info_type not in info_responses:
        return {
            "error": f"지원하지 않는 정보 타입입니다. 가능한 타입: {list(info_responses.keys())}"
        }
    
    return info_responses[info_type]

@mcp.tool()
async def calculate_simple(expression: str) -> Dict[str, Any]:
    """
    간단한 계산을 수행합니다.
    
    Args:
        expression (str): 계산식 (예: "10 + 5", "20 * 3", "100 / 4")
        
    Returns:
        Dict[str, Any]: 계산 결과
    """
    logger.info(f"계산 요청: {expression}")
    
    try:
        # 안전한 계산을 위해 허용된 문자만 사용
        allowed_chars = "0123456789+-*/.()"
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return {"error": "허용되지 않는 문자가 포함되어 있습니다."}
        
        result = eval(expression)
        return {
            "expression": expression,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": f"계산 중 오류 발생: {str(e)}",
            "expression": expression
        }

@mcp.tool()
async def get_recommendations(category: str, preferences: List[str] = None) -> Dict[str, Any]:
    """
    카테고리별 추천을 제공합니다.
    
    Args:
        category (str): 추천 카테고리 ("books", "movies", "restaurants", "activities")
        preferences (List[str], optional): 선호도 키워드
        
    Returns:
        Dict[str, Any]: 추천 목록
    """
    logger.info(f"추천 요청: 카테고리={category}, 선호도={preferences}")
    
    recommendations_data = {
        "books": [
            {"title": "효율적인 삶을 위한 시간 관리", "author": "김철수", "genre": "자기계발"},
            {"title": "인간관계의 심리학", "author": "이영희", "genre": "심리학"},
            {"title": "건강한 라이프스타일", "author": "박민수", "genre": "건강"},
        ],
        "movies": [
            {"title": "힐링 드라마", "genre": "드라마", "rating": 8.5},
            {"title": "모험의 시작", "genre": "어드벤처", "rating": 7.8},
            {"title": "코미디 특집", "genre": "코미디", "rating": 8.2},
        ],
        "restaurants": [
            {"name": "맛있는 한식당", "cuisine": "한식", "price": "중간"},
            {"name": "이탈리안 레스토랑", "cuisine": "이탈리안", "price": "높음"},
            {"name": "카페 브런치", "cuisine": "카페", "price": "낮음"},
        ],
        "activities": [
            {"name": "산책", "type": "야외", "duration": "1-2시간"},
            {"name": "독서", "type": "실내", "duration": "자유"},
            {"name": "요리", "type": "실내", "duration": "1-3시간"},
        ]
    }
    
    if category not in recommendations_data:
        return {
            "error": f"지원하지 않는 카테고리입니다. 가능한 카테고리: {list(recommendations_data.keys())}"
        }
    
    items = recommendations_data[category]
    
    # 선호도가 있으면 랜덤하게 필터링 (실제로는 더 정교한 로직 필요)
    if preferences:
        items = random.sample(items, min(len(items), 2))
    
    return {
        "category": category,
        "preferences": preferences,
        "recommendations": items,
        "total_count": len(items)
    }

if __name__ == "__main__":
    print("일반상담 MCP 서버가 실행 중입니다...")
    print(f"포트: {GENERAL_MCP_PORT}")
    mcp.run(transport="sse") 