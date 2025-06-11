import streamlit as st
import time
import os
from dotenv import load_dotenv

from utils.logging_config import setup_logger

load_dotenv()

logger = setup_logger(__name__)

def voice_chatbot_page():
    logger.info("개인비서 음성 페이지가 로드되었습니다.")

    st.markdown(
        """
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        header {
            visibility: hidden;
        }
        #MainMenu {
            visibility: hidden;
        }
        footer {
            visibility: hidden;
        }
        .stDeployButton {
            display: none;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    if "conversations" not in st.session_state:
        st.session_state.conversations = []
    if "js_messages" not in st.session_state:
        st.session_state.js_messages = []

    # CSS 파일들 로드
    css_files = [
        "base.css",
        "animations.css", 
        "dots.css",
        "button.css",
        "effects.css",
        "sse-notifications.css"
    ]
    
    css_content = ""
    css_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets/css")
    
    for css_file in css_files:
        css_path = os.path.join(css_dir, css_file)
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css_content += f"/* === {css_file} === */\n"
                css_content += f.read()
                css_content += "\n\n"
        except FileNotFoundError:
            logger.warning(f"CSS 파일을 찾을 수 없습니다: {css_path}")

    # JS 파일들 로드 (config.js를 첫 번째로)
    js_files = [
        "config.js",
        "audio-manager.js",
        "dots-manager.js", 
        "api-client.js",
        "ui-controller.js",
        "sse-client.js",
        "voice-chatbot.js"
    ]
    
    js_content = ""
    js_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets/js")
    
    for js_file in js_files:
        js_path = os.path.join(js_dir, js_file)
        try:
            with open(js_path, "r", encoding="utf-8") as f:
                js_content += f"/* === {js_file} === */\n"
                js_content += f.read()
                js_content += "\n\n"
        except FileNotFoundError:
            logger.warning(f"JS 파일을 찾을 수 없습니다: {js_path}")

    processing_css = """
    /* 처리 중 상태 스타일 */
    .mic-button.processing {
        background-color: #fff3cd;
        animation: processing-pulse 1.5s ease-in-out infinite;
    }

    @keyframes processing-pulse {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }
    """

    logger.debug(f"CSS 및 JS 파일을 성공적으로 로드했습니다.")

    voice_interface_html = f"""
    <html>
    <head>
        <style>
            {css_content}
            {processing_css}
        </style>
    </head>
    <body>
        <div class="voice-container">
            <!-- OpenAI 스타일 파도 애니메이션 -->
            <div id="waveContainer" class="wave-container">
                <div class="wave-bar idle"></div>
                <div class="wave-bar idle"></div>
                <div class="wave-bar idle"></div>
                <div class="wave-bar idle"></div>
                <div class="wave-bar idle"></div>
                <div class="wave-bar idle"></div>
                <div class="wave-bar idle"></div>
                <div class="wave-bar idle"></div>
            </div>
           
            <div id="circleContainer" class="circle-container idle">
                <div class="voice-circle">
                    <canvas id="audioCanvas" class="audio-canvas"></canvas>
                    <div class="stars" id="starsContainer"></div>
                    <div class="voice-visualizer">
                        <div class="audio-pulse audio-pulse-1"></div>
                        <div class="audio-pulse audio-pulse-2"></div>
                        <div class="audio-pulse audio-pulse-3"></div>
                    </div>
                </div>
            </div>
           
            <div class="voice-indicator">
                개인비서 음성 Assistant
                <div class="info-icon">🤖</div>
            </div>
           
            <div class="controls">
                <button id="micButton" class="mic-button">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        <line x1="12" y1="19" x2="12" y2="23"></line>
                        <line x1="8" y1="23" x2="16" y2="23"></line>
                    </svg>
                </button>
            </div>
        </div>
        
        <!-- SSE 상태 표시 -->
        <div id="sse-status" class="sse-status sse-status-disconnected" title="SSE 연결 대기 중..." onclick="toggleMessages()">
            <div class="sse-status-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 19V20H3V19L5 17V11C5 7.9 7 5.2 10 4.3V4C10 2.9 10.9 2 12 2S14 2.9 14 4V4.3C17 5.2 19 7.9 19 11V17L21 19ZM12 22C10.9 22 10 21.1 10 20H14C14 21.1 13.1 22 12 22Z"/>
                </svg>
            </div>
        </div>
       
        <script>
            {js_content}
        </script>
    </body>
    </html>
    """

    # HTML 컴포넌트 표시
    component_value = st.components.v1.html(voice_interface_html, height=700)
    logger.debug("HTML 컴포넌트가 렌더링되었습니다.")