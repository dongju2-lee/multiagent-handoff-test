import logging
import traceback
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command
from schema.state import DevToolState
from agents.general_agent import get_general_agent
from agents.research_agent import get_memo_agent
from agents.report_agent import get_schedule_agent
from agents.health_agent import get_health_agent

logger = logging.getLogger("supervisor")
logging.basicConfig(level=logging.INFO)


def router_node(state: DevToolState):
    agent_mode = state.get("agent_mode", "general")
    
    if agent_mode == "general":
        logger.info("일반상담 에이전트 모드로 라우팅합니다.")
        return {"next": "general"}
    elif agent_mode == "schedule":
        logger.info("일정관리 에이전트 모드로 라우팅합니다.")
        return {"next": "schedule"}
    elif agent_mode == "memo":
        logger.info("메모관리 에이전트 모드로 라우팅합니다.")
        return {"next": "memo"}
    elif agent_mode == "health":
        logger.info("건강관리 에이전트 모드로 라우팅합니다.")
        return {"next": "health"}
    else:
        logger.info(f"알 수 없는 모드 '{agent_mode}'. 일반상담 모드로 라우팅합니다.")
        return {"next": "general"}

async def general_node(state: DevToolState):
    logger.info("일반상담 에이전트 실행 중...")
    try:
        agent = await get_general_agent()
        result = await agent.ainvoke(state)
        logger.info(f"일반상담 에이전트 실행 완료 result : {result}")
        
        # handoff Command가 있는지 확인
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            for msg in messages:
                if hasattr(msg, 'additional_kwargs') and 'tool_calls' in msg.additional_kwargs:
                    for tool_call in msg.additional_kwargs['tool_calls']:
                        if tool_call['function']['name'].startswith('transfer_to_'):
                            target_agent = tool_call['function']['name'].replace('transfer_to_', '')
                            logger.info(f"Handoff detected: transferring to {target_agent}")
                            return Command(goto=f"{target_agent}_agent", update=result)
        
        return result
    except Exception as e:
        logger.error(f"일반상담 에이전트 실행 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        # 에러 발생시 기본 응답 반환
        return {"output": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"}


async def schedule_node(state: DevToolState):
    logger.info("일정관리 에이전트 실행 중...")
    query = state.get("input", "")
    logger.info(f"일정관리 쿼리: {query[:100]}..." if len(query) > 100 else f"일정관리 쿼리: {query}")
    
    try:
        # 상태 로깅
        logger.info(f"State 구조: {list(state.keys())}")
        for key, value in state.items():
            logger.info(f"State[{key}] 타입: {type(value).__name__}")
        
        agent = await get_schedule_agent()
        logger.info("일정관리 에이전트 가져오기 성공")
        
        # invoke 전 상태 확인
        logger.info(f"Agent 타입: {type(agent).__name__}")
        logger.info("에이전트 호출 시작...")
        
        result = await agent.ainvoke(state)
        
        # handoff Command가 있는지 확인
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            for msg in messages:
                if hasattr(msg, 'additional_kwargs') and 'tool_calls' in msg.additional_kwargs:
                    for tool_call in msg.additional_kwargs['tool_calls']:
                        if tool_call['function']['name'].startswith('transfer_to_'):
                            target_agent = tool_call['function']['name'].replace('transfer_to_', '')
                            logger.info(f"Schedule agent handoff: transferring to {target_agent}")
                            return Command(goto=f"{target_agent}_agent", update=result)
        
        logger.info("일정관리 완료. 결과 반환.")
        return result
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"일정관리 에이전트 실행 중 오류 발생: {str(e)}")
        logger.error(error_detail)
        
        # 에러 발생시 기본 응답 반환
        return {
            "output": f"일정관리 중 오류가 발생했습니다. 자세한 내용은 로그를 확인해주세요.\n오류: {str(e)}"
        }


async def memo_node(state: DevToolState):
    logger.info("메모관리 에이전트 실행 중...")
    query = state.get("input", "")
    logger.info(f"메모관리 쿼리: {query[:100]}..." if len(query) > 100 else f"메모관리 쿼리: {query}")
    
    try:
        # 상태 로깅
        logger.info(f"State 구조: {list(state.keys())}")
        for key, value in state.items():
            logger.info(f"State[{key}] 타입: {type(value).__name__}")
        
        agent = await get_memo_agent()
        logger.info("메모관리 에이전트 가져오기 성공")
        
        # invoke 전 상태 확인
        logger.info(f"Agent 타입: {type(agent).__name__}")
        logger.info("에이전트 호출 시작...")
        
        result = await agent.ainvoke(state)
        
        # handoff Command가 있는지 확인
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            for msg in messages:
                if hasattr(msg, 'additional_kwargs') and 'tool_calls' in msg.additional_kwargs:
                    for tool_call in msg.additional_kwargs['tool_calls']:
                        if tool_call['function']['name'].startswith('transfer_to_'):
                            target_agent = tool_call['function']['name'].replace('transfer_to_', '')
                            logger.info(f"Memo agent handoff: transferring to {target_agent}")
                            return Command(goto=f"{target_agent}_agent", update=result)
        
        logger.info("메모관리 완료. 결과 반환.")
        return result
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"메모관리 에이전트 실행 중 오류 발생: {str(e)}")
        logger.error(error_detail)
        
        # 에러 발생시 기본 응답 반환
        return {
            "output": f"메모관리 중 오류가 발생했습니다. 자세한 내용은 로그를 확인해주세요.\n오류: {str(e)}"
        }


async def health_node(state: DevToolState):
    logger.info("건강관리 에이전트 실행 중...")
    query = state.get("input", "")
    logger.info(f"건강관리 쿼리: {query[:100]}..." if len(query) > 100 else f"건강관리 쿼리: {query}")
    
    try:
        # 상태 로깅
        logger.info(f"State 구조: {list(state.keys())}")
        for key, value in state.items():
            logger.info(f"State[{key}] 타입: {type(value).__name__}")
        
        agent = await get_health_agent()
        logger.info("건강관리 에이전트 가져오기 성공")
        
        # invoke 전 상태 확인
        logger.info(f"Agent 타입: {type(agent).__name__}")
        logger.info("에이전트 호출 시작...")
        
        result = await agent.ainvoke(state)
        
        # handoff Command가 있는지 확인
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            for msg in messages:
                if hasattr(msg, 'additional_kwargs') and 'tool_calls' in msg.additional_kwargs:
                    for tool_call in msg.additional_kwargs['tool_calls']:
                        if tool_call['function']['name'].startswith('transfer_to_'):
                            target_agent = tool_call['function']['name'].replace('transfer_to_', '')
                            logger.info(f"Health agent handoff: transferring to {target_agent}")
                            return Command(goto=f"{target_agent}_agent", update=result)
        
        logger.info("건강관리 완료. 결과 반환.")
        return result
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"건강관리 에이전트 실행 중 오류 발생: {str(e)}")
        logger.error(error_detail)
        
        # 에러 발생시 기본 응답 반환
        return {
            "output": f"건강관리 중 오류가 발생했습니다. 자세한 내용은 로그를 확인해주세요.\n오류: {str(e)}"
        }

def build_supervisor_graph():
    logger.info("개인비서 슈퍼바이저 그래프 빌드 시작")
    try:
        sg = StateGraph(DevToolState)
        sg.add_node("router", router_node)
        sg.add_node("general", general_node)
        sg.add_node("schedule", schedule_node)
        sg.add_node("memo", memo_node)
        sg.add_node("health", health_node)
        
        # handoff를 위한 별칭 노드들도 추가
        sg.add_node("general_agent", general_node)
        sg.add_node("schedule_agent", schedule_node)
        sg.add_node("memo_agent", memo_node)
        sg.add_node("health_agent", health_node)

        sg.add_edge(START, "router")

        sg.add_conditional_edges(
            "router",
            lambda state: state.get("agent_mode", "general"),
            {
                "general": "general",
                "schedule": "schedule", 
                "memo": "memo",
                "health": "health",
            },
        )

        # 기존 END 에지들
        sg.add_edge("general", END)
        sg.add_edge("schedule", END)
        sg.add_edge("memo", END)
        sg.add_edge("health", END)
        
        # handoff용 별칭 노드들도 END로 연결
        sg.add_edge("general_agent", END)
        sg.add_edge("schedule_agent", END)
        sg.add_edge("memo_agent", END)
        sg.add_edge("health_agent", END)
        
        logger.info("개인비서 슈퍼바이저 그래프 빌드 완료")
        return sg
    except Exception as e:
        logger.error(f"슈퍼바이저 그래프 빌드 중 오류: {str(e)}")
        logger.error(traceback.format_exc())
        raise