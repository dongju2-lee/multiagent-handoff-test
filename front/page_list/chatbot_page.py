import os
import json
import uuid
import asyncio
import requests
from dotenv import load_dotenv

import streamlit as st

from schema.state import SessionState, Response, Request
from utils.logging_config import setup_logger

load_dotenv()

logger = setup_logger(__name__)

AGENT_SERVER_HOST = os.environ.get("AGENT_SERVER_HOST", "http://localhost:8800")

# 비서 모드 상수 정의
AGENT_MODES = {
    "general": "일반 상담",  
    "schedule": "일정 관리",  
    "memo": "메모 관리",
    "health": "건강 관리",
}


def generate_session_id():
    """Generate New session id"""
    return str(uuid.uuid4())


def initialize():
    """Initialize session id and message"""
    if SessionState.SESSION_ID.value not in st.session_state:
        st.session_state.session_id = generate_session_id()

    if SessionState.MESSAGES.value not in st.session_state:
        st.session_state.messages = []

    # 비서 모드 초기화
    if "agent_mode" not in st.session_state:
        st.session_state.agent_mode = "general"


def get_chat_response(message, session_id=None):
    """Sends a message to the /chat API and returns the response."""

    url = f"{AGENT_SERVER_HOST}/ask"
    headers = {"Content-Type": "application/json"}
    data = {Request.MESSAGE.value: message}

    if session_id:
        data[Request.SESSION_ID.value] = session_id

    # 비서 모드 정보도 전달
    data[Request.AGENT_MODE.value] = st.session_state.agent_mode

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to server: {e}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON response: {e}")
        return None


def render_sidebar():

    with st.sidebar:
        # 비서 모드 선택 섹션
        st.header("비서 모드")

        # 모드 옵션 포맷 함수
        def format_mode(mode):
            return f"{AGENT_MODES[mode]}"

        # 세그먼트 컨트롤로 모드 선택
        selected_mode = st.segmented_control(
            "모드 선택",
            options=list(AGENT_MODES.keys()),
            format_func=format_mode,
            selection_mode="single",
            default=st.session_state.agent_mode,
        )

        # 모드가 변경되면 세션 상태 업데이트하고 즉시 페이지 리프레시
        if selected_mode and selected_mode != st.session_state.agent_mode:
            st.session_state.agent_mode = selected_mode
            st.success(f"{AGENT_MODES[selected_mode]} 모드로 변경되었습니다!")
            # 즉시 페이지 리프레시
            st.rerun()

        # 모드별 설명 표시
        mode_descriptions = {
            "general": "일상적인 질문과 도움이 필요할 때 사용하는 표준 모드입니다.",
            "schedule": "일정 관리, 약속 관리, 캘린더 기능을 제공하는 모드입니다.",
            "memo": "메모 작성, 할 일 관리, 중요한 정보 저장을 도와주는 모드입니다.",
            "health": "건강 관리, 운동 계획, 식단 관리에 도움을 주는 모드입니다.",
        }

        st.info(mode_descriptions[st.session_state.agent_mode])

        st.divider()

        # 세션 관리 섹션
        st.header("대화 관리")

        current_session = (
            st.session_state.session_id
            if st.session_state.session_id
            else "활성 세션 없음"
        )
        st.info(f"현재 세션 ID: {current_session}")

        if st.button("새 대화 시작"):
            new_session_id = generate_session_id()
            st.session_state.session_id = new_session_id
            st.session_state.messages = []
            st.success(f"새 대화가 시작되었습니다: {new_session_id}")
            st.rerun()

        st.divider()


def display_chat_history():
    """Show chat messages stored in session state"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


async def process_chat(user_input):
    """Process user input asynchronously"""
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        status_placeholder = st.status(
            "Processing your request...", expanded=False
        )
        message_placeholder = st.empty()
        st.container()

    if not st.session_state.session_id:
        st.session_state.session_id = generate_session_id()
        st.sidebar.info(
            f"New session created with ID: {st.session_state.session_id}"
        )

    response_data = get_chat_response(user_input, st.session_state.session_id)

    if response_data:
        if (
            Response.SESSION_ID.value in response_data
            and response_data[Response.SESSION_ID.value]
            != st.session_state.session_id
        ):
            st.session_state.session_id = response_data[
                Response.SESSION_ID.value
            ]
            st.sidebar.info(
                f"Session ID updated: {st.session_state.session_id}"
            )

        response_text = response_data[Response.RESPONSE.value]
        message_placeholder.markdown(response_text)

        image_data = []
        message_type = "normal"

        status_placeholder.update(
            label="✅ Complete", state="complete", expanded=False
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response_text,
                "images": image_data,
                "type": message_type,
            }
        )
    else:
        message_placeholder.error(
            "Failed to get a valid response from the server"
        )
        status_placeholder.update(
            label="❌ Error", state="error", expanded=True
        )


def chatbot_page():
    st.title("개인비서 Assistant")

    initialize()

    render_sidebar()

    # 현재 비서 모드 표시
    st.caption(
        f"현재 {AGENT_MODES[st.session_state.agent_mode]} 모드로 도움을 드리고 있습니다."
    )

    display_chat_history()

    if prompt := st.chat_input("무엇을 도와드릴까요?"):
        asyncio.run(process_chat(prompt))