from typing import Annotated, Literal
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.graph import MessagesState
from langgraph.types import Command

def create_handoff_tool(*, agent_name: str, description: str | None = None):
    """에이전트 간 handoff를 위한 도구를 생성합니다."""
    name = f"transfer_to_{agent_name}"
    description = description or f"Transfer to {agent_name}"

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": name,
            "tool_call_id": tool_call_id,
        }
        return Command(
            goto=agent_name,
            update={"messages": state["messages"] + [tool_message]},
            graph=Command.PARENT,
        )
    return handoff_tool

def create_task_handoff_tool(*, agent_name: str, description: str | None = None):
    """특정 작업 설명과 함께 handoff하는 도구를 생성합니다."""
    name = f"ask_{agent_name}_for_help"
    description = description or f"Ask {agent_name} for help with specific task"

    @tool(name, description=description)
    def task_handoff_tool(
        task_description: Annotated[
            str,
            "Description of what the next agent should do, including all relevant context.",
        ],
        state: Annotated[MessagesState, InjectedState],
    ) -> Command:
        task_message = {"role": "user", "content": task_description}
        agent_input = {**state, "messages": [task_message]}
        return Command(
            goto=agent_name,
            update=agent_input,
            graph=Command.PARENT,
        )
    return task_handoff_tool

# 각 에이전트별 handoff tool 생성 - 개인비서 에이전트들
transfer_to_general = create_handoff_tool(
    agent_name="general_agent",
    description="일반상담 에이전트로 전환 - 일상적인 질문과 다양한 도움 요청 처리"
)

transfer_to_schedule = create_handoff_tool(
    agent_name="schedule_agent", 
    description="일정관리 에이전트로 전환 - 스케줄, 약속, 캘린더 관리 전담"
)

transfer_to_memo = create_handoff_tool(
    agent_name="memo_agent",
    description="메모관리 에이전트로 전환 - 메모 작성, 할일 관리, 정보 저장 전담"
)

transfer_to_health = create_handoff_tool(
    agent_name="health_agent",
    description="건강관리 에이전트로 전환 - 운동, 식단, 건강 관리 전담"
)

# 작업 기반 handoff tool들 - 개인비서 에이전트들
ask_general_for_help = create_task_handoff_tool(
    agent_name="general_agent", 
    description="일반상담 에이전트에게 도움 요청 - 일반적인 질문이나 조언이 필요할 때"
)

ask_schedule_for_help = create_task_handoff_tool(
    agent_name="schedule_agent",
    description="일정관리 에이전트에게 도움 요청 - 특정 일정 관리나 스케줄링 작업"
)

ask_memo_for_help = create_task_handoff_tool(
    agent_name="memo_agent",
    description="메모관리 에이전트에게 도움 요청 - 메모 작성이나 할일 관리 작업"
)

ask_health_for_help = create_task_handoff_tool(
    agent_name="health_agent",
    description="건강관리 에이전트에게 도움 요청 - 운동이나 건강 관련 작업"
) 