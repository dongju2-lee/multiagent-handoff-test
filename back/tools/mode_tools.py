"""
개인비서 에이전트 모드 관리 도구 모듈

이 모듈은 개인비서 에이전트의 모드를 변경하고 관리하는 도구들을 포함합니다.
모든 에이전트가 공유하여 사용할 수 있도록 설계되었습니다.
"""

import logging
from typing import Dict, Any, Union, Annotated, Optional
from langchain_core.tools import tool, BaseTool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from schema.state import DevToolState

# 로깅 설정
logger = logging.getLogger("mode_tools")

# 유효한 에이전트 모드 목록 - 개인비서 모드들
VALID_MODES = ["general", "schedule", "memo", "health"]


def change_agent_mode(
    new_mode: str,
    state: DevToolState
):
    """
    사용자와의 대화 내용에 따라 더 적합한 개인비서 에이전트 모드로 전환합니다.
    
    Args:
        new_mode (str): 변경할 에이전트 모드. 가능한 값: 
                       "general" (일반상담), "schedule" (일정관리), 
                       "memo" (메모관리), "health" (건강관리)
        tool_call_id (str): 도구 호출 ID (자동 주입됨)
    
    Returns:
        Dict[str, Any]: 모드 변경 결과 및 상태 업데이트 정보
    """
    logger.info(f"개인비서 에이전트 모드 변경 도구 호출됨: {new_mode}")
    
    # 모드 한글명 매핑
    mode_names = {
        "general": "일반상담", 
        "schedule": "일정관리",
        "memo": "메모관리", 
        "health": "건강관리"
    }
            
    # 응답 메시지 구성
    mode_name = mode_names.get(new_mode, new_mode)
    message = f"모드 변경: {mode_name} 모드로 전환합니다."
    logger.info(f"모드 변경 성공: {mode_name}")
    
    state["agent_mode"] = new_mode
    return state