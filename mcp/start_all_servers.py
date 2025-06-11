#!/usr/bin/env python3
"""
개인비서용 MCP 서버들을 모두 실행하는 스크립트
"""

import subprocess
import time
import signal
import sys
import os
from typing import List

# 서버 정보
SERVERS = [
    {"name": "일반상담", "file": "general_consulting_server.py", "port": 10001},
    {"name": "일정관리", "file": "schedule_server.py", "port": 10002},
    {"name": "캘린더", "file": "calendar_server.py", "port": 10003},
    {"name": "메모관리", "file": "memo_server.py", "port": 10005},
    {"name": "노트저장소", "file": "note_storage_server.py", "port": 10006},
    {"name": "건강관리", "file": "health_server.py", "port": 10008},
    {"name": "피트니스", "file": "fitness_server.py", "port": 10009},
]

class MCPServerManager:
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = False
        
    def start_server(self, server_info: dict) -> subprocess.Popen:
        """개별 서버를 시작합니다."""
        try:
            print(f"🚀 {server_info['name']} 서버 시작 중... (포트: {server_info['port']})")
            
            # 서버 파일 경로 확인
            server_file = server_info['file']
            if not os.path.exists(server_file):
                print(f"❌ 서버 파일을 찾을 수 없습니다: {server_file}")
                return None
            
            # 서버 프로세스 시작
            process = subprocess.Popen(
                [sys.executable, server_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 잠시 대기 후 프로세스 상태 확인
            time.sleep(1)
            
            if process.poll() is None:  # 프로세스가 여전히 실행 중
                print(f"✅ {server_info['name']} 서버가 성공적으로 시작되었습니다.")
                return process
            else:
                # 프로세스가 이미 종료됨
                stdout, stderr = process.communicate()
                print(f"❌ {server_info['name']} 서버 시작 실패:")
                if stderr:
                    print(f"   오류: {stderr}")
                if stdout:
                    print(f"   출력: {stdout}")
                return None
                
        except Exception as e:
            print(f"❌ {server_info['name']} 서버 시작 중 예외 발생: {str(e)}")
            return None
    
    def start_all_servers(self):
        """모든 서버를 시작합니다."""
        print("🔄 개인비서 MCP 서버들을 시작합니다...\n")
        
        for server_info in SERVERS:
            process = self.start_server(server_info)
            if process:
                self.processes.append(process)
                server_info['process'] = process
            
            # 서버 간 시작 간격
            time.sleep(0.5)
        
        successful_servers = len(self.processes)
        total_servers = len(SERVERS)
        
        print(f"\n📊 서버 시작 완료: {successful_servers}/{total_servers}")
        
        if successful_servers > 0:
            self.running = True
            print("\n✨ 시작된 서버들:")
            for server_info in SERVERS:
                if 'process' in server_info:
                    print(f"   • {server_info['name']} (포트: {server_info['port']}) - http://localhost:{server_info['port']}/sse")
            
            print(f"\n🎯 개인비서 시스템이 준비되었습니다!")
            print("   - 일반상담, 일정관리, 메모관리, 건강관리 기능을 사용할 수 있습니다.")
            print("   - Ctrl+C를 눌러 모든 서버를 종료할 수 있습니다.")
        else:
            print("\n❌ 시작된 서버가 없습니다. 오류를 확인해주세요.")
    
    def stop_all_servers(self):
        """모든 서버를 중지합니다."""
        if not self.processes:
            return
            
        print("\n🔄 모든 MCP 서버를 중지합니다...")
        
        for i, process in enumerate(self.processes):
            try:
                if process.poll() is None:  # 프로세스가 여전히 실행 중
                    server_name = SERVERS[i]['name']
                    print(f"🛑 {server_name} 서버 중지 중...")
                    process.terminate()
                    
                    # 정상 종료 대기 (최대 5초)
                    try:
                        process.wait(timeout=5)
                        print(f"✅ {server_name} 서버가 정상적으로 종료되었습니다.")
                    except subprocess.TimeoutExpired:
                        print(f"⚠️  {server_name} 서버를 강제로 종료합니다...")
                        process.kill()
                        process.wait()
                        
            except Exception as e:
                print(f"❌ 서버 중지 중 오류 발생: {str(e)}")
        
        self.processes.clear()
        self.running = False
        print("🎯 모든 서버가 중지되었습니다.")
    
    def check_server_status(self):
        """서버 상태를 확인합니다."""
        if not self.processes:
            print("실행 중인 서버가 없습니다.")
            return
            
        print("📊 서버 상태 확인:")
        running_count = 0
        
        for i, process in enumerate(self.processes):
            server_name = SERVERS[i]['name']
            port = SERVERS[i]['port']
            
            if process.poll() is None:
                print(f"   ✅ {server_name} (포트: {port}) - 실행 중")
                running_count += 1
            else:
                print(f"   ❌ {server_name} (포트: {port}) - 중지됨")
        
        print(f"총 {running_count}/{len(self.processes)}개 서버가 실행 중입니다.")
    
    def run(self):
        """메인 실행 함수"""
        # 신호 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            self.start_all_servers()
            
            if self.running:
                # 서버들이 계속 실행되도록 유지
                print("\n⏳ 서버들이 실행 중입니다. 종료하려면 Ctrl+C를 누르세요.")
                
                while self.running:
                    time.sleep(1)
                    
                    # 주기적으로 서버 상태 확인
                    dead_processes = []
                    for i, process in enumerate(self.processes):
                        if process.poll() is not None:  # 프로세스가 종료됨
                            dead_processes.append((i, SERVERS[i]['name']))
                    
                    if dead_processes:
                        print(f"\n⚠️  일부 서버가 예상치 못하게 종료되었습니다:")
                        for i, name in dead_processes:
                            print(f"   - {name}")
                        break
                        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all_servers()
    
    def _signal_handler(self, signum, frame):
        """신호 핸들러"""
        print(f"\n🔔 종료 신호 수신 (신호: {signum})")
        self.running = False

def main():
    """메인 함수"""
    print("🤖 개인비서 MCP 서버 관리자")
    print("=" * 50)
    
    manager = MCPServerManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            # 실행 중인 프로세스 확인 (간단한 포트 체크)
            import socket
            print("📊 포트 상태 확인:")
            for server in SERVERS:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', server['port']))
                    sock.close()
                    
                    if result == 0:
                        print(f"   ✅ {server['name']} (포트: {server['port']}) - 실행 중")
                    else:
                        print(f"   ❌ {server['name']} (포트: {server['port']}) - 중지됨")
                except:
                    print(f"   ❌ {server['name']} (포트: {server['port']}) - 확인 불가")
            return
        
        elif command == "help":
            print("사용법:")
            print(f"  python {sys.argv[0]}        # 모든 서버 시작")
            print(f"  python {sys.argv[0]} status # 서버 상태 확인")
            print(f"  python {sys.argv[0]} help   # 도움말 표시")
            return
    
    # 기본 동작: 모든 서버 시작
    manager.run()

if __name__ == "__main__":
    main() 