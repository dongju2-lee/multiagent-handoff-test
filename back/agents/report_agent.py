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

logger = logging.getLogger("schedule_agent")
logging.basicConfig(level=logging.INFO)
from utils.config import settings

# 환경 변수 로드
load_dotenv()

# 싱글톤 인스턴스
_llm_instance = None
_mcp_client = None
_mcp_tools_cache = None
_agent_instance = None

langfuse_handler = CallbackHandler(public_key="", secret_key="", host="")

# MCP 서버 URL 설정 - 일정관리용
MCP_SERVERS = {
    "schedule_manager": {
        "url": os.environ.get(
            "SCHEDULE_MCP_URL", "http://localhost:10002/sse"
        ),
        "transport": "sse",
    },
    "calendar": {
        "url": os.environ.get(
            "CALENDAR_MCP_URL", "http://localhost:10003/sse"
        ),
        "transport": "sse",
    },
    # 추후 일정관리에 필요한 추가 MCP 서버들
    # "reminder": {
    #     "url": os.environ.get(
    #         "REMINDER_MCP_URL", "http://localhost:10004/sse"
    #     ),
    #     "transport": "sse",
    # },
}


# MCP 클라이언트 초기화 함수
async def init_mcp_client():
    """MCP 클라이언트를 초기화합니다."""
    global _mcp_client
    if _mcp_client is None:
        print("MCP 클라이언트 초기화 시작")
        try:
            client = MultiServerMCPClient(MCP_SERVERS)
            print("MCP 클라이언트 인스턴스 생성 완료")
            _mcp_client = client
            print("MCP 클라이언트 초기화 완료")
        except Exception as e:
            print(f"MCP 클라이언트 초기화 중 오류 발생: {str(e)}")
            raise
    return _mcp_client


# MCP 클라이언트 종료 함수 (필요시)
async def close_mcp_client():
    """MCP 클라이언트 연결을 안전하게 종료합니다."""
    global _mcp_client
    _mcp_client = None
    print("MCP 클라이언트 인스턴스 해제 완료")


# MCP 도구 가져오기 함수
async def get_mcp_tools() -> List:
    """MCP 도구를 가져오고 상세 정보를 출력합니다."""
    global _mcp_tools_cache
    if _mcp_tools_cache is not None:
        return _mcp_tools_cache
    try:
        client = await init_mcp_client()
        print("MCP 도구 가져오는 중...")
        tools = await client.get_tools()  # await 필수!
        print(f"총 {len(tools)}개의 MCP 도구를 가져왔습니다")
        _mcp_tools_cache = tools
        return tools
    except Exception as e:
        print(f"도구 가져오기 중 오류 발생: {str(e)}")
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
            print(f"도구 정보 변환 중 오류: {str(e)}")
    return tools_info


# LLM 모델 초기화 함수
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
        print(f"LLM 모델 초기화: {model_name}")
        _llm_instance = ChatVertexAI(
            model=model_name, temperature=0.1, max_output_tokens=8190
        )
    return _llm_instance


# 프롬프트 생성 함수
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
        print(f"도구 정보 가져오기 중 오류 발생: {str(e)}")
        tools_text = "도구 정보를 가져오는 중 오류가 발생했습니다. MCP 서버 연결을 확인하세요."
    
    prompt_path = os.path.join(
        os.path.dirname(__file__), "../prompts/report_agent.txt"
    )
    async with aiofiles.open(prompt_path, mode="r", encoding="utf-8") as f:
        prompt_template = await f.read()
    
    # 단순 문자열 대체 사용
    prompt = prompt_template.replace("{tools}", tools_text)
    
    # 템플릿 변수 충돌 방지를 위해 중괄호 이스케이프 처리
    # MCP 도구 설명에서 나올 수 있는 중괄호를 이중 중괄호로 변경
    import re
    # {변수명} 패턴을 {{변수명}}으로 변경 (단, {tools}는 제외)
    prompt = re.sub(r'\{([^}]+)\}', lambda m: '{{' + m.group(1) + '}}' if m.group(1) != 'tools' else m.group(0), prompt)
    
    return prompt


# 일정관리 에이전트 생성 함수
async def get_schedule_agent():
    """일정관리 에이전트를 생성하고 반환합니다."""
    global _agent_instance
    if _agent_instance is None:
        prompt = await generate_prompt()
        logger.info("프롬프트 생성 완료")
        system_prompt = ChatPromptTemplate.from_messages(
            [("system", prompt), MessagesPlaceholder(variable_name="messages")]
        )
        llm = await get_llm()
        tools = await get_mcp_tools()
        
        # Handoff tool 추가를 위해 도구 리스트 확장
        try:
            from utils.handoff_tools import transfer_to_general, transfer_to_memo, transfer_to_health, ask_general_for_help, ask_memo_for_help, ask_health_for_help
            handoff_tools = [transfer_to_general, transfer_to_memo, transfer_to_health, ask_general_for_help, ask_memo_for_help, ask_health_for_help]
            all_tools = tools + handoff_tools
            logger.info(f"Handoff tools added to Schedule Agent: {len(handoff_tools)} tools")
        except ImportError:
            logger.warning("Handoff tools not available, using only MCP tools")
            all_tools = tools
        
        _agent_instance = create_react_agent(
            llm, all_tools, prompt=system_prompt, debug=True  # 디버그 모드 활성화
        )
        logger.info("일정관리 에이전트 생성 완료")
    return _agent_instance


# 일정 생성 함수
async def create_schedule(user_query: str) -> str:
    """사용자 요청을 받아 일정을 생성합니다."""
    try:
        logger.info(f"일정 생성 시작: {user_query}")
        agent = await get_schedule_agent()
        
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
            return "일정 생성 중 오류가 발생했습니다."
            
    except Exception as e:
        logger.error(f"일정 생성 중 오류 발생: {str(e)}")
        return f"일정 생성 중 오류가 발생했습니다: {str(e)}"


# 일정 관리 함수
async def manage_schedule(schedule_description: str, action_type: str = "create") -> str:
    """일정을 관리합니다 (생성, 수정, 삭제, 조회)."""
    management_query = f"""
    다음 일정 관리 요청을 처리해주세요:
    
    일정 내용: {schedule_description}
    작업 유형: {action_type}
    
    작업 유형별 처리 방법:
    - create: 새로운 일정 생성
    - update: 기존 일정 수정
    - delete: 일정 삭제
    - view: 일정 조회
    
    적절한 도구를 사용하여 요청을 처리하고 결과를 알려주세요.
    """
    
    return await create_schedule(management_query)


# 알림 설정 함수
async def set_reminder(event_description: str, reminder_time: str) -> str:
    """특정 이벤트에 대한 알림을 설정합니다."""
    reminder_query = f"""
    다음 이벤트에 대한 알림을 설정해주세요:
    
    이벤트: {event_description}
    알림 시간: {reminder_time}
    
    다음 항목들을 포함하여 처리해주세요:
    1. 이벤트 일정 확인
    2. 알림 시간 설정
    3. 알림 방식 설정
    4. 반복 알림 여부 확인
    
    알림이 성공적으로 설정되었는지 확인해주세요.
    """
    
    return await create_schedule(reminder_query)


# 일정 요약 리포트 생성 함수
async def generate_schedule_summary(time_period: str = "week") -> str:
    """특정 기간의 일정을 요약한 리포트를 생성합니다."""
    summary_query = f"""
    다음 기간의 일정을 요약해주세요:
    
    기간: {time_period}
    
    다음 항목들을 포함해주세요:
    1. 예정된 일정 목록
    2. 중요한 이벤트 하이라이트
    3. 시간 충돌 여부 확인
    4. 여유 시간 분석
    5. 일정 관리 제안사항
    
    효율적인 시간 관리를 위한 인사이트를 제공해주세요.
    """
    
    return await create_schedule(summary_query)


# 에이전트 정리 함수
async def cleanup_agent():
    """에이전트 리소스를 정리합니다."""
    global _agent_instance, _mcp_client, _mcp_tools_cache, _llm_instance
    
    _agent_instance = None
    _mcp_tools_cache = None
    _llm_instance = None
    
    if _mcp_client:
        await close_mcp_client()
    
    logger.info("일정관리 에이전트 리소스 정리 완료")