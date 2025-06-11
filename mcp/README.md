# 개인비서 MCP 서버 집합

이 디렉토리에는 개인비서 시스템을 위한 7개의 MCP (Model Context Protocol) 서버가 포함되어 있습니다.

## 📋 서버 목록

### 주요 서버
1. **일반상담 서버** (`general_consulting_server.py`) - 포트 10001
   - FAQ 검색, 조언 제공, 빠른 정보 조회, 계산, 추천 등
   
2. **일정관리 서버** (`schedule_server.py`) - 포트 10002
   - 일정 생성/수정/삭제, 시간 충돌 확인, 가능한 시간 슬롯 찾기
   
3. **메모관리 서버** (`memo_server.py`) - 포트 10005
   - 메모 작성/검색/관리, 할일 목록 관리, 통계 제공

4. **건강관리 서버** (`health_server.py`) - 포트 10008
   - 건강 데이터 추적, 목표 설정, 약물 관리, 건강 인사이트

### 보조 서버
5. **캘린더 서버** (`calendar_server.py`) - 포트 10003
   - 월별 캘린더 생성, 날짜 계산, 반복 일정 처리, 공휴일 정보

6. **노트 저장소 서버** (`note_storage_server.py`) - 포트 10006
   - 파일 저장/버전 관리, 백업/복원, 저장소 통계

7. **피트니스 서버** (`fitness_server.py`) - 포트 10009
   - 운동 기록/계획, 칼로리 계산, 운동 추천, 피트니스 통계

## 🚀 빠른 시작

### 1. 모든 서버 한번에 실행
```bash
cd mcp
python start_all_servers.py
```

### 2. 서버 상태 확인
```bash
python start_all_servers.py status
```

### 3. 개별 서버 실행
```bash
# 예시: 일반상담 서버만 실행
python general_consulting_server.py
```

## 🔧 설정

각 서버는 `.env` 파일의 환경 변수를 참조합니다:

```env
GENERAL_CONSULTING_MCP_URL="http://localhost:10001/sse"
SCHEDULE_MCP_URL="http://localhost:10002/sse"
CALENDAR_MCP_URL="http://localhost:10003/sse"
MEMO_MCP_URL="http://localhost:10005/sse"
NOTE_STORAGE_MCP_URL="http://localhost:10006/sse"
HEALTH_MCP_URL="http://localhost:10008/sse"
FITNESS_MCP_URL="http://localhost:10009/sse"
```

## 📚 서버별 상세 기능

### 🗣️ 일반상담 서버 (포트 10001)
**도구들:**
- `search_faq`: FAQ 검색
- `get_advice`: 분야별 조언 제공
- `get_quick_info`: 시간, 날짜, 날씨, 환율, 뉴스 정보
- `calculate_simple`: 간단한 수학 계산
- `get_recommendations`: 책, 영화, 음식점, 활동 추천

### 📅 일정관리 서버 (포트 10002)
**도구들:**
- `create_schedule`: 새 일정 생성
- `get_schedule`: 일정 상세 조회
- `list_schedules`: 일정 목록 조회
- `update_schedule`: 일정 수정
- `delete_schedule`: 일정 삭제
- `check_conflicts`: 시간 충돌 확인
- `get_available_slots`: 사용 가능한 시간대 찾기

### 📝 메모관리 서버 (포트 10005)
**도구들:**
- `create_memo`: 메모 생성
- `get_memo`: 메모 조회
- `search_memos`: 메모 검색
- `update_memo`: 메모 수정
- `delete_memo`: 메모 삭제
- `create_todo`: 할일 생성
- `list_todos`: 할일 목록 조회
- `update_todo_status`: 할일 상태 변경
- `get_memo_statistics`: 메모/할일 통계

### 🏥 건강관리 서버 (포트 10008)
**도구들:**
- `add_health_record`: 건강 기록 추가
- `get_health_records`: 건강 기록 조회
- `create_health_goal`: 건강 목표 생성
- `update_goal_progress`: 목표 진행도 업데이트
- `add_medication`: 복용 약물 추가
- `get_medication_schedule`: 약물 복용 일정 조회
- `get_health_insights`: 건강 인사이트 제공
- `get_health_summary`: 건강 상태 요약

### 📆 캘린더 서버 (포트 10003)
**도구들:**
- `get_monthly_calendar`: 월별 캘린더 생성
- `calculate_date_difference`: 날짜 차이 계산
- `get_date_info`: 특정 날짜 정보
- `generate_recurring_dates`: 반복 일정 날짜 생성
- `find_available_time_blocks`: 사용 가능한 시간 블록 찾기
- `get_holidays_info`: 공휴일 정보

### 💾 노트 저장소 서버 (포트 10006)
**도구들:**
- `save_note_file`: 노트 파일 저장
- `get_file`: 파일 조회
- `update_file`: 파일 업데이트
- `list_files`: 파일 목록 조회
- `get_file_versions`: 파일 버전 히스토리
- `restore_file_version`: 파일 버전 복원
- `create_backup`: 백업 생성
- `list_backups`: 백업 목록
- `restore_from_backup`: 백업 복원
- `get_storage_stats`: 저장소 통계

### 💪 피트니스 서버 (포트 10009)
**도구들:**
- `log_workout`: 운동 기록 추가
- `get_workouts`: 운동 기록 조회
- `create_workout_plan`: 운동 계획 생성
- `get_workout_plans`: 운동 계획 목록
- `suggest_workout`: 조건별 운동 추천
- `calculate_calories_burned`: 칼로리 소모 계산
- `get_exercise_library`: 운동 라이브러리 조회
- `get_fitness_stats`: 피트니스 통계

## 🔗 백엔드 연동

백엔드의 개인비서 에이전트들이 이 MCP 서버들을 사용합니다:

- **일반상담 에이전트** → 일반상담 서버
- **일정관리 에이전트** → 일정관리 서버 + 캘린더 서버
- **메모관리 에이전트** → 메모관리 서버 + 노트 저장소 서버
- **건강관리 에이전트** → 건강관리 서버 + 피트니스 서버

## 🛠️ 개발 및 확장

### 새로운 도구 추가
각 서버 파일에서 `@mcp.tool()` 데코레이터를 사용하여 새로운 도구를 추가할 수 있습니다:

```python
@mcp.tool()
async def new_tool(param1: str, param2: int = 0) -> Dict[str, Any]:
    """새로운 도구 설명"""
    # 도구 로직 구현
    return {"result": "success"}
```

### 새로운 서버 추가
1. 새 서버 파일 생성 (예: `new_server.py`)
2. `start_all_servers.py`의 `SERVERS` 리스트에 서버 정보 추가
3. 백엔드 `.env` 파일에 새 서버 URL 추가

## 🐛 문제 해결

### 서버가 시작되지 않는 경우
1. 포트가 이미 사용 중인지 확인:
   ```bash
   netstat -an | grep :10001
   ```

2. Python 의존성 확인:
   ```bash
   pip install fastmcp python-dotenv
   ```

3. 로그 확인:
   각 서버는 실행 시 로그를 출력합니다.

### 연결 문제
- 방화벽 설정 확인
- localhost 대신 127.0.0.1 사용 시도
- 백엔드 .env 파일의 URL 형식 확인

## 📝 라이센스

이 프로젝트는 MIT 라이센스를 따릅니다. 