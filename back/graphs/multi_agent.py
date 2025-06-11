import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver

from agents.general_agent import get_llm, get_mcp_tools as get_general_tools, generate_prompt as generate_general_prompt
from agents.report_agent import get_mcp_tools as get_schedule_tools, generate_prompt as generate_schedule_prompt
from agents.research_agent import get_mcp_tools as get_memo_tools, generate_prompt as generate_memo_prompt
from agents.health_agent import get_mcp_tools as get_health_tools, generate_prompt as generate_health_prompt
from utils.handoff_tools import (
    transfer_to_general, transfer_to_schedule, transfer_to_memo, transfer_to_health,
    ask_general_for_help, ask_schedule_for_help, ask_memo_for_help, ask_health_for_help
)

logger = logging.getLogger(__name__)

class MultiAgentState(MessagesState):
    """Multi-agent state with last active agent tracking"""
    last_active_agent: str

# 일반상담 에이전트
async def call_general_agent(state: MultiAgentState) -> Command[Literal["general", "schedule", "memo", "health", "__end__"]]:
    """일반상담 에이전트 호출"""
    logger.info("일반상담 에이전트 실행 중...")
    
    try:
        # 도구와 프롬프트 준비
        llm = await get_llm()
        tools = await get_general_tools()
        handoff_tools = [transfer_to_schedule, transfer_to_memo, transfer_to_health, ask_schedule_for_help, ask_memo_for_help, ask_health_for_help]
        all_tools = tools + handoff_tools
        
        prompt = await generate_general_prompt()
        
        # ReAct 에이전트 생성
        agent = create_react_agent(llm, all_tools, prompt=prompt)
        
        # 에이전트 실행
        response = await agent.ainvoke(state)
        
        # 응답에서 Command 확인 (핸드오프 시)
        if "messages" in response and response["messages"]:
            last_message = response["messages"][-1]
            # ToolMessage에서 핸드오프 확인
            if hasattr(last_message, 'name') and last_message.name in ['transfer_to_schedule', 'transfer_to_memo', 'transfer_to_health', 'ask_schedule_for_help', 'ask_memo_for_help', 'ask_health_for_help']:
                logger.info(f"핸드오프 감지: {last_message.name}")
                # 핸드오프 대상 결정
                if 'schedule' in last_message.name:
                    target = 'schedule'
                elif 'memo' in last_message.name:
                    target = 'memo'
                elif 'health' in last_message.name:
                    target = 'health'
                else:
                    target = '__end__'
                
                # 상태 업데이트하고 해당 에이전트로 이동
                update = {**response, "last_active_agent": "general"}
                return Command(update=update, goto=target)
        
        # 핸드오프가 없으면 END로 이동
        update = {**response, "last_active_agent": "general"}
        return Command(update=update)
        
    except Exception as e:
        logger.error(f"일반상담 에이전트 실행 중 오류: {str(e)}")
        return Command(
            update={
                "messages": [{"role": "assistant", "content": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"}],
                "last_active_agent": "general"
            }
        )

# 일정관리 에이전트
async def call_schedule_agent(state: MultiAgentState) -> Command[Literal["general", "schedule", "memo", "health", "__end__"]]:
    """일정관리 에이전트 호출"""
    logger.info("일정관리 에이전트 실행 중...")
    
    try:
        # 도구와 프롬프트 준비
        llm = await get_llm()
        tools = await get_schedule_tools()
        handoff_tools = [transfer_to_general, transfer_to_memo, transfer_to_health, ask_general_for_help, ask_memo_for_help, ask_health_for_help]
        all_tools = tools + handoff_tools
        
        prompt = await generate_schedule_prompt()
        
        # ReAct 에이전트 생성
        agent = create_react_agent(llm, all_tools, prompt=prompt)
        
        # 에이전트 실행
        response = await agent.ainvoke(state)
        
        # 응답에서 Command 확인 (핸드오프 시)
        if "messages" in response and response["messages"]:
            last_message = response["messages"][-1]
            # ToolMessage에서 핸드오프 확인
            if hasattr(last_message, 'name') and last_message.name in ['transfer_to_general', 'transfer_to_memo', 'transfer_to_health', 'ask_general_for_help', 'ask_memo_for_help', 'ask_health_for_help']:
                logger.info(f"핸드오프 감지: {last_message.name}")
                # 핸드오프 대상 결정
                if 'general' in last_message.name:
                    target = 'general'
                elif 'memo' in last_message.name:
                    target = 'memo'
                elif 'health' in last_message.name:
                    target = 'health'
                else:
                    target = '__end__'
                
                # 상태 업데이트하고 해당 에이전트로 이동
                update = {**response, "last_active_agent": "schedule"}
                return Command(update=update, goto=target)
        
        # 핸드오프가 없으면 END로 이동
        update = {**response, "last_active_agent": "schedule"}
        return Command(update=update)
        
    except Exception as e:
        logger.error(f"일정관리 에이전트 실행 중 오류: {str(e)}")
        return Command(
            update={
                "messages": [{"role": "assistant", "content": f"일정관리 중 오류가 발생했습니다: {str(e)}"}],
                "last_active_agent": "schedule"
            }
        )

# 메모관리 에이전트
async def call_memo_agent(state: MultiAgentState) -> Command[Literal["general", "schedule", "memo", "health", "__end__"]]:
    """메모관리 에이전트 호출"""
    logger.info("메모관리 에이전트 실행 중...")
    
    try:
        # 도구와 프롬프트 준비
        llm = await get_llm()
        tools = await get_memo_tools()
        handoff_tools = [transfer_to_general, transfer_to_schedule, transfer_to_health, ask_general_for_help, ask_schedule_for_help, ask_health_for_help]
        all_tools = tools + handoff_tools
        
        prompt = await generate_memo_prompt()
        
        # ReAct 에이전트 생성
        agent = create_react_agent(llm, all_tools, prompt=prompt)
        
        # 에이전트 실행
        response = await agent.ainvoke(state)
        
        # 응답에서 Command 확인 (핸드오프 시)
        if "messages" in response and response["messages"]:
            last_message = response["messages"][-1]
            # ToolMessage에서 핸드오프 확인
            if hasattr(last_message, 'name') and last_message.name in ['transfer_to_general', 'transfer_to_schedule', 'transfer_to_health', 'ask_general_for_help', 'ask_schedule_for_help', 'ask_health_for_help']:
                logger.info(f"핸드오프 감지: {last_message.name}")
                # 핸드오프 대상 결정
                if 'general' in last_message.name:
                    target = 'general'  
                elif 'schedule' in last_message.name:
                    target = 'schedule'
                elif 'health' in last_message.name:
                    target = 'health'
                else:
                    target = '__end__'
                
                # 상태 업데이트하고 해당 에이전트로 이동
                update = {**response, "last_active_agent": "memo"}
                return Command(update=update, goto=target)
        
        # 핸드오프가 없으면 END로 이동
        update = {**response, "last_active_agent": "memo"}
        return Command(update=update)
        
    except Exception as e:
        logger.error(f"메모관리 에이전트 실행 중 오류: {str(e)}")
        return Command(
            update={
                "messages": [{"role": "assistant", "content": f"메모관리 중 오류가 발생했습니다: {str(e)}"}],
                "last_active_agent": "memo"
            }
        )

# 건강관리 에이전트
async def call_health_agent(state: MultiAgentState) -> Command[Literal["general", "schedule", "memo", "health", "__end__"]]:
    """건강관리 에이전트 호출"""
    logger.info("건강관리 에이전트 실행 중...")
    
    try:
        # 도구와 프롬프트 준비
        llm = await get_llm()
        tools = await get_health_tools()
        handoff_tools = [transfer_to_general, transfer_to_schedule, transfer_to_memo, ask_general_for_help, ask_schedule_for_help, ask_memo_for_help]
        all_tools = tools + handoff_tools
        
        prompt = await generate_health_prompt()
        
        # ReAct 에이전트 생성
        agent = create_react_agent(llm, all_tools, prompt=prompt)
        
        # 에이전트 실행
        response = await agent.ainvoke(state)
        
        # 응답에서 Command 확인 (핸드오프 시)
        if "messages" in response and response["messages"]:
            last_message = response["messages"][-1]
            # ToolMessage에서 핸드오프 확인
            if hasattr(last_message, 'name') and last_message.name in ['transfer_to_general', 'transfer_to_schedule', 'transfer_to_memo', 'ask_general_for_help', 'ask_schedule_for_help', 'ask_memo_for_help']:
                logger.info(f"핸드오프 감지: {last_message.name}")
                # 핸드오프 대상 결정
                if 'general' in last_message.name:
                    target = 'general'  
                elif 'schedule' in last_message.name:
                    target = 'schedule'
                elif 'memo' in last_message.name:
                    target = 'memo'
                else:
                    target = '__end__'
                
                # 상태 업데이트하고 해당 에이전트로 이동
                update = {**response, "last_active_agent": "health"}
                return Command(update=update, goto=target)
        
        # 핸드오프가 없으면 END로 이동
        update = {**response, "last_active_agent": "health"}
        return Command(update=update)
        
    except Exception as e:
        logger.error(f"건강관리 에이전트 실행 중 오류: {str(e)}")
        return Command(
            update={
                "messages": [{"role": "assistant", "content": f"건강관리 중 오류가 발생했습니다: {str(e)}"}],
                "last_active_agent": "health"
            }
        )

def build_multi_agent_graph():
    """Multi-agent swarm 그래프 빌드"""
    logger.info("Multi-agent swarm 그래프 빌드 시작")
    
    try:
        builder = StateGraph(MultiAgentState)
        
        # 에이전트 노드들 추가 (human 노드 제거)
        builder.add_node("general", call_general_agent)
        builder.add_node("schedule", call_schedule_agent)
        builder.add_node("memo", call_memo_agent)
        builder.add_node("health", call_health_agent)
        
        # 항상 일반상담 에이전트로 시작
        builder.add_edge(START, "general")
        
        # 메모리 설정
        checkpointer = MemorySaver()
        graph = builder.compile(checkpointer=checkpointer)
        
        logger.info("Multi-agent swarm 그래프 빌드 완료")
        return graph
        
    except Exception as e:
        logger.error(f"Multi-agent 그래프 빌드 중 오류: {str(e)}")
        raise 