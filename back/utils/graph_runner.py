import asyncio
import logging
import os

from langgraph.checkpoint.memory import MemorySaver
from langfuse.callback import CallbackHandler
from langchain_core.messages import HumanMessage

from graphs.multi_agent import build_multi_agent_graph

logger = logging.getLogger("runner")
logging.basicConfig(level=logging.INFO)
memory = MemorySaver()


class GraphRunner:
    def __init__(self) -> None:
        # 새로운 multi-agent swarm 그래프 사용
        self._graph = build_multi_agent_graph()
        self._lock = asyncio.Lock()
        self.langfuse_handler = CallbackHandler(
            public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
            host=os.environ.get("LANGFUSE_HOST"),
        )

    async def ask(
        self, *, session_id: str, user_input: str, agent_mode: str
    ) -> str:
        logger.info(
            f"GraphRunner received user input: {user_input} "
            f"for session: {session_id}"
            f"system mode : {agent_mode}"
        )
        
        try:
            # multi-agent swarm 그래프 실행
            state = {
                "messages": [HumanMessage(content=user_input)],
                "last_active_agent": "general",  # 항상 general로 시작
            }
            
            config = {"configurable": {"thread_id": session_id},"callbacks": [self.langfuse_handler]}
            
            result = await self._graph.ainvoke(state, config)
            
            # 응답 추출
            if "output" in result:
                response = result["output"]
            elif "messages" in result and result["messages"]:
                # 마지막 메시지에서 응답 추출
                last_message = result["messages"][-1]
                response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                response = "죄송합니다. 응답을 처리하는 중 문제가 발생했습니다."
            
            logger.info(f"response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Graph execution error: {e}")
            raise
    
    async def stream(self, message: str, agent_mode: str, thread_id: str = "default"):
        async with self._lock:
            logger.info(f"Graph 실행 시작: {thread_id}")
            logger.info(f"Agent 모드: {agent_mode}")
            
            # multi-agent swarm 그래프 사용
            state = {
                "messages": [HumanMessage(content=message)],
                "last_active_agent": "general",  # 항상 general로 시작
            }
            
            config = {"configurable": {"thread_id": thread_id}}
            
            async for event in self._graph.astream(state, config):
                logger.info(f"Graph event: {event}")
                yield event