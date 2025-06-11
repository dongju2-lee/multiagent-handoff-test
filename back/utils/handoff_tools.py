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

# 각 에이전트별 handoff tool 생성
transfer_to_research = create_handoff_tool(
    agent_name="research_agent",
    description="Transfer to research agent for detailed investigation and data analysis"
)

transfer_to_report = create_handoff_tool(
    agent_name="report_agent", 
    description="Transfer to report agent for generating comprehensive reports and documentation"
)

transfer_to_general = create_handoff_tool(
    agent_name="general_agent",
    description="Transfer to general agent for general purpose tasks and coordination"
)

# 작업 기반 handoff tool들
ask_research_for_help = create_task_handoff_tool(
    agent_name="research_agent",
    description="Ask research agent for help with specific research or analysis task"
)

ask_report_for_help = create_task_handoff_tool(
    agent_name="report_agent",
    description="Ask report agent for help with generating specific reports or documentation"
)

ask_general_for_help = create_task_handoff_tool(
    agent_name="general_agent", 
    description="Ask general agent for help with general tasks or coordination"
) 