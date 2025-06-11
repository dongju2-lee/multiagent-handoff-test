#!/bin/bash

# 개인비서 MCP 서버들을 한번에 실행하는 스크립트
# Ctrl+C로 모든 서버를 안전하게 종료할 수 있습니다.

set -e  # 오류 발생 시 스크립트 종료

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 서버 정보 배열
declare -a SERVERS=(
    "일반상담:general_consulting_server.py:10001"
    "일정관리:schedule_server.py:10002"
    "캘린더:calendar_server.py:10003"
    "메모관리:memo_server.py:10005"
    "노트저장소:note_storage_server.py:10006"
    "건강관리:health_server.py:10008"
    "피트니스:fitness_server.py:10009"
)

# 프로세스 ID들을 저장할 배열
declare -a PIDS=()

# 스크립트 시작 메시지
echo -e "${BLUE}🤖 개인비서 MCP 서버 시작 스크립트${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# 종료 함수
cleanup() {
    echo ""
    echo -e "${YELLOW}🔄 모든 MCP 서버를 종료합니다...${NC}"
    
    # 모든 백그라운드 프로세스 종료
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}🛑 프로세스 $pid 종료 중...${NC}"
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    
    # 잠시 대기 후 강제 종료
    sleep 2
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${RED}⚠️  프로세스 $pid 강제 종료...${NC}"
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✅ 모든 서버가 종료되었습니다.${NC}"
    exit 0
}

# 신호 핸들러 등록
trap cleanup SIGINT SIGTERM

# 현재 디렉토리 확인
if [ ! -f "general_consulting_server.py" ]; then
    echo -e "${RED}❌ MCP 서버 파일들을 찾을 수 없습니다.${NC}"
    echo -e "${RED}   mcp 디렉토리에서 실행해주세요.${NC}"
    exit 1
fi

# 가상환경 활성화
VENV_PATH="../venv/mcp/bin/activate"
if [ -f "$VENV_PATH" ]; then
    echo -e "${CYAN}🔧 MCP 가상환경 활성화 중...${NC}"
    source "$VENV_PATH"
    echo -e "${GREEN}✅ 가상환경이 활성화되었습니다.${NC}"
else
    echo -e "${YELLOW}⚠️  가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다.${NC}"
fi

# Python 설치 확인
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python이 설치되어 있지 않습니다.${NC}"
    exit 1
fi

# Python 명령어 결정
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo -e "${CYAN}🐍 Python 명령어: $PYTHON_CMD${NC}"

# MCP 패키지 확인
echo -e "${CYAN}📦 MCP 패키지 확인 중...${NC}"
if $PYTHON_CMD -c "import mcp" 2>/dev/null; then
    echo -e "${GREEN}✅ MCP 패키지가 확인되었습니다.${NC}"
else
    echo -e "${RED}❌ MCP 패키지를 찾을 수 없습니다.${NC}"
    echo -e "${RED}   pip install mcp fastmcp 명령으로 설치해주세요.${NC}"
    exit 1
fi
echo ""

# 서버 시작 함수
start_server() {
    local name="$1"
    local file="$2"
    local port="$3"
    
    echo -e "${BLUE}🚀 $name 서버 시작 중... (포트: $port)${NC}"
    
    # 파일 존재 확인
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ 파일을 찾을 수 없습니다: $file${NC}"
        return 1
    fi
    
    # 포트 사용 중인지 확인
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  포트 $port가 이미 사용 중입니다. 계속 진행합니다.${NC}"
    fi
    
    # 서버 실행
    $PYTHON_CMD "$file" > "/tmp/mcp_${name}_${port}.log" 2>&1 &
    local pid=$!
    
    # 잠시 대기 후 프로세스 상태 확인
    sleep 1
    
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}✅ $name 서버가 성공적으로 시작되었습니다. (PID: $pid)${NC}"
        PIDS+=("$pid")
        return 0
    else
        echo -e "${RED}❌ $name 서버 시작 실패${NC}"
        echo -e "${RED}   로그: /tmp/mcp_${name}_${port}.log${NC}"
        return 1
    fi
}

# 모든 서버 시작
echo -e "${PURPLE}🔄 MCP 서버들을 시작합니다...${NC}"
echo ""

started_count=0
total_count=${#SERVERS[@]}

for server_info in "${SERVERS[@]}"; do
    IFS=':' read -r name file port <<< "$server_info"
    
    if start_server "$name" "$file" "$port"; then
        ((started_count++))
    fi
    
    # 서버 간 시작 간격
    sleep 0.5
done

echo ""
echo -e "${CYAN}📊 서버 시작 완료: $started_count/$total_count${NC}"

if [ $started_count -eq 0 ]; then
    echo -e "${RED}❌ 시작된 서버가 없습니다. 오류를 확인해주세요.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✨ 시작된 서버들:${NC}"
for server_info in "${SERVERS[@]}"; do
    IFS=':' read -r name file port <<< "$server_info"
    echo -e "${GREEN}   • $name (포트: $port) - http://localhost:$port/sse${NC}"
done

echo ""
echo -e "${CYAN}🎯 개인비서 시스템이 준비되었습니다!${NC}"
echo -e "${CYAN}   - 일반상담, 일정관리, 메모관리, 건강관리 기능을 사용할 수 있습니다.${NC}"
echo -e "${CYAN}   - Ctrl+C를 눌러 모든 서버를 종료할 수 있습니다.${NC}"
echo ""

# 서버 상태 모니터링
echo -e "${YELLOW}⏳ 서버들이 실행 중입니다. 종료하려면 Ctrl+C를 누르세요.${NC}"
echo ""

# 무한 루프로 서버들이 계속 실행되도록 유지
while true; do
    sleep 5
    
    # 죽은 프로세스 확인
    dead_pids=()
    for i in "${!PIDS[@]}"; do
        pid="${PIDS[i]}"
        if ! kill -0 "$pid" 2>/dev/null; then
            dead_pids+=("$i")
        fi
    done
    
    # 죽은 프로세스가 있으면 알림
    if [ ${#dead_pids[@]} -gt 0 ]; then
        echo -e "${RED}⚠️  일부 서버가 예상치 못하게 종료되었습니다:${NC}"
        for i in "${dead_pids[@]}"; do
            server_info="${SERVERS[i]}"
            IFS=':' read -r name file port <<< "$server_info"
            echo -e "${RED}   - $name${NC}"
        done
        echo -e "${YELLOW}   로그를 확인하려면: ls /tmp/mcp_*.log${NC}"
        break
    fi
done

# 정리 및 종료
cleanup 