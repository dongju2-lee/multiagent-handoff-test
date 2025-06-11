from typing_extensions import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class PersonalAssistantState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    agent_mode: str

# 하위 호환성을 위해 별칭 제공
DevToolState = PersonalAssistantState