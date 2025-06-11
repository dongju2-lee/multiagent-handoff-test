import os
from typing import Dict, List, Any
import aiofiles

from langchain_google_vertexai import ChatVertexAI
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langfuse.callback import CallbackHandler
import logging

logger = logging.getLogger("health_agent")
logging.basicConfig(level=logging.INFO)
from utils.config import settings

# 환경 변수 로드
load_dotenv()

# 싱글톤 인스턴스
_llm_instance = None
_mcp_client = None
_mcp_tools_cache = None

langfuse_handler = CallbackHandler(public_key="", secret_key="", host="")

# MCP 서버 URL 설정 - 건강관리용
MCP_SERVERS = {
    "health_tracker": {
        "url": os.environ.get(
            "HEALTH_MCP_URL", "http://localhost:10008/sse"
        ),
        "transport": "sse",
    },
    "fitness_manager": {
        "url": os.environ.get(
            "FITNESS_MCP_URL", "http://localhost:10009/sse"
        ),
        "transport": "sse",
    },
    # 추후 건강관리에 필요한 추가 MCP 서버들
    # "nutrition_tracker": {
    #     "url": os.environ.get(
    #         "NUTRITION_MCP_URL", "http://localhost:10010/sse"
    #     ),
    #     "transport": "sse",
    # },
}


# MCP 클라이언트 초기화 함수
async def init_mcp_client():
    """MCP 클라이언트를 초기화합니다."""
    global _mcp_client
    if _mcp_client is None:
        logger.info("MCP 클라이언트 초기화 시작")
        try:
            client = MultiServerMCPClient(MCP_SERVERS)
            logger.info("MCP 클라이언트 인스턴스 생성 완료")
            _mcp_client = client
            logger.info("MCP 클라이언트 초기화 완료")
        except Exception as e:
            logger.info(f"MCP 클라이언트 초기화 중 오류 발생: {str(e)}")
            raise
    return _mcp_client


# MCP 클라이언트 종료 함수 (필요시)
async def close_mcp_client():
    """MCP 클라이언트 연결을 안전하게 종료합니다."""
    global _mcp_client
    _mcp_client = None
    logger.info("MCP 클라이언트 인스턴스 해제 완료")


# MCP 도구 가져오기 함수
async def get_mcp_tools() -> List:
    """MCP 도구를 가져오고 상세 정보를 출력합니다."""
    global _mcp_tools_cache
    if _mcp_tools_cache is not None:
        return _mcp_tools_cache
    try:
        client = await init_mcp_client()
        logger.info("MCP 도구 가져오는 중...")
        tools = await client.get_tools()  # await 필수!
        logger.info(f"총 {len(tools)}개의 MCP 도구를 가져왔습니다")
        _mcp_tools_cache = tools
        return tools
    except Exception as e:
        logger.info(f"도구 가져오기 중 오류 발생: {str(e)}")
        return []


# MCP 도구 정보 변환 함수
async def convert_mcp_tools_to_info() -> List[Dict[str, Any]]:
    """MCP 도구를 사용자 친화적인 형식으로 변환합니다."""
    tools = await get_mcp_tools()
    tools_info = []
    for tool in tools:
        try:
            tool_info = {
                "name": getattr(tool, "name", "Unknown"),
                "description": getattr(tool, "description", "설명 없음"),
                "parameters": [],
            }
            if hasattr(tool, "args_schema") and tool.args_schema is not None:
                schema_props = getattr(tool.args_schema, "schema", {}).get(
                    "properties", {}
                )
                if schema_props:
                    tool_info["parameters"] = list(schema_props.keys())
            tools_info.append(tool_info)
        except Exception as e:
            logger.info(f"도구 정보 변환 중 오류: {str(e)}")
    return tools_info


async def get_llm():
    """LLM 모델을 초기화하고 반환합니다."""

    import vertexai

    vertexai.init(
        project=settings.gcp_project_id,
        location=settings.gcp_vertexai_location,
    )

    global _llm_instance
    if _llm_instance is None:
        model_name = os.environ.get("VERTEX_MODEL", "gemini-2.0-flash")
        logger.info(f"LLM 모델 초기화: {model_name}")
        _llm_instance = ChatVertexAI(
            model=model_name, temperature=0.1, max_output_tokens=8190
        )
    return _llm_instance

async def generate_prompt() -> str:
    """사용자 요청에 따른 프롬프트를 생성합니다."""
    try:
        tools_info = await convert_mcp_tools_to_info()
        tools_text = "\n".join(
            [
                f"{i+1}. {tool['name']}: {tool['description']}"
                for i, tool in enumerate(tools_info)
            ]
        )
        if not tools_text:
            tools_text = (
                "현재 사용 가능한 도구가 없습니다. MCP 서버 연결을 확인하세요."
            )
    except Exception as e:
        logger.error(f"도구 정보 가져오기 중 오류 발생: {str(e)}")
        tools_text = "도구 정보를 가져오는 중 오류가 발생했습니다. MCP 서버 연결을 확인하세요."
    
    prompt_path = os.path.join(
        os.path.dirname(__file__), "../prompts/health_agent.txt"
    )
    async with aiofiles.open(prompt_path, mode="r", encoding="utf-8") as f:
        prompt_template = await f.read()
    
    # 단순 문자열 대체 사용
    prompt = prompt_template.replace("{tools}", tools_text)
    
    return prompt


# 건강관리 에이전트 생성 함수
async def get_health_agent() -> str:
    """건강관리 에이전트를 생성하고 반환합니다."""
    global _agent_instance
    prompt = await generate_prompt()
    logger.info("프롬프트 생성 완료")
    system_prompt = ChatPromptTemplate.from_messages(
        [("system", prompt), MessagesPlaceholder(variable_name="messages")]
    )
    llm = await get_llm()
    tools = await get_mcp_tools()
    
    # Handoff tool 추가를 위해 도구 리스트 확장
    try:
        from utils.handoff_tools import transfer_to_general, transfer_to_schedule, transfer_to_memo, ask_general_for_help, ask_schedule_for_help, ask_memo_for_help
        handoff_tools = [transfer_to_general, transfer_to_schedule, transfer_to_memo, ask_general_for_help, ask_schedule_for_help, ask_memo_for_help]
        all_tools = tools + handoff_tools
        logger.info(f"Handoff tools added to Health Agent: {len(handoff_tools)} tools")
    except ImportError:
        logger.warning("Handoff tools not available, using only MCP tools")
        all_tools = tools
    
    _agent_instance = create_react_agent(
        llm, all_tools, prompt=system_prompt, debug=True  # 디버그 모드 활성화
    )
    logger.info("건강관리 에이전트 생성 완료")
    return _agent_instance


# 건강 기록 관리 함수
async def track_health_data(user_query: str) -> str:
    """사용자 요청을 받아 건강 데이터를 기록하고 관리합니다."""
    try:
        logger.info(f"건강 데이터 추적 시작: {user_query}")
        agent = await get_health_agent()
        
        # 에이전트 실행
        result = await agent.ainvoke(
            {"messages": [("user", user_query)]},
            config={"callbacks": [langfuse_handler]}
        )
        
        # 결과에서 최종 답변 추출
        if "messages" in result and result["messages"]:
            final_message = result["messages"][-1]
            if hasattr(final_message, "content"):
                return final_message.content
            else:
                return str(final_message)
        else:
            return "건강 데이터 처리 중 오류가 발생했습니다."
            
    except Exception as e:
        logger.error(f"건강 데이터 추적 중 오류 발생: {str(e)}")
        return f"건강 데이터 처리 중 오류가 발생했습니다: {str(e)}"


# 운동 계획 생성 함수
async def create_workout_plan(fitness_goal: str, current_level: str = "beginner") -> str:
    """운동 목표와 현재 수준에 맞는 운동 계획을 생성합니다."""
    workout_query = f"""
    다음 정보를 바탕으로 개인 맞춤 운동 계획을 수립해주세요:
    
    운동 목표: {fitness_goal}
    현재 수준: {current_level}
    
    다음 항목들을 포함하여 계획해주세요:
    1. 주간 운동 스케줄 (빈도, 시간)
    2. 운동 종류별 세부 프로그램
    3. 강도 조절 방법
    4. 진척도 측정 방법
    5. 안전 수칙 및 주의사항
    
    실현 가능하고 효과적인 운동 계획을 제공해주세요.
    """
    
    return await track_health_data(workout_query)


# 식단 관리 함수
async def manage_nutrition(dietary_goal: str, dietary_restrictions: str = "") -> str:
    """식단 목표와 제한사항에 맞는 영양 관리 계획을 제공합니다."""
    nutrition_query = f"""
    다음 정보를 바탕으로 개인 맞춤 식단 관리 계획을 수립해주세요:
    
    식단 목표: {dietary_goal}
    식단 제한사항: {dietary_restrictions}
    
    다음 항목들을 포함하여 계획해주세요:
    1. 일일 권장 칼로리 및 영양소
    2. 식사별 메뉴 추천
    3. 간식 및 수분 섭취 가이드
    4. 영양 균형 유지 방법
    5. 식단 기록 및 모니터링 방법
    
    건강하고 지속 가능한 식단 계획을 제공해주세요.
    """
    
    return await track_health_data(nutrition_query)


# 건강 리포트 생성 함수
async def generate_health_report(time_period: str = "month") -> str:
    """특정 기간의 건강 데이터를 분석하여 리포트를 생성합니다."""
    report_query = f"""
    다음 기간의 건강 데이터를 종합하여 건강 리포트를 작성해주세요:
    
    분석 기간: {time_period}
    
    다음 항목들을 포함해주세요:
    1. 운동 목표 달성률 및 진척도
    2. 체중/체성분 변화 추이
    3. 식단 관리 현황
    4. 수면 패턴 분석
    5. 스트레스 레벨 변화
    6. 전반적인 건강 상태 평가
    7. 개선 권장사항
    
    데이터 기반의 객관적인 건강 분석과 맞춤형 개선 방안을 제공해주세요.
    """
    
    return await track_health_data(report_query)


# 에이전트 정리 함수
async def cleanup_agent():
    """에이전트 리소스를 정리합니다."""
    global _agent_instance, _mcp_client, _mcp_tools_cache, _llm_instance
    
    _agent_instance = None
    _mcp_tools_cache = None
    _llm_instance = None
    
    if _mcp_client:
        await close_mcp_client()
    
    logger.info("건강관리 에이전트 리소스 정리 완료") 