# 📱 휴대폰 서버 실행 스크립트

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

def install_requirements():
    """필요한 패키지 설치"""
    print("📦 필요한 패키지를 설치하고 있습니다...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 패키지 설치 완료!")
    except subprocess.CalledProcessError:
        print("❌ 패키지 설치 실패!")
        return False
    
    return True

def check_android_environment():
    """안드로이드 환경 확인"""
    # Termux 환경 확인
    if 'ANDROID_ROOT' in os.environ:
        print("📱 안드로이드 환경 감지됨 (Termux)")
        return True
    
    # 일반 PC 환경
    print("🖥️ PC 환경에서 실행")
    return False

def setup_android_permissions():
    """안드로이드 권한 설정"""
    try:
        # Wake lock 활성화 (Termux)
        subprocess.run(["termux-wake-lock"], check=False)
        print("🔒 Wake lock 활성화됨")
        
        # 저장소 권한 요청
        subprocess.run(["termux-setup-storage"], check=False)
        print("📁 저장소 권한 설정됨")
        
    except FileNotFoundError:
        print("⚠️ Termux API를 찾을 수 없습니다. 일반 모드로 실행합니다.")

def run_mobile_server():
    """모바일 서버 실행"""
    print("🚀 모바일 서버를 시작합니다...")
    
    try:
        # 메인 앱 실행
        from main import GiftCardApp
        app = GiftCardApp()
        app.run()
        
    except ImportError:
        print("❌ 앱 모듈을 찾을 수 없습니다.")
        return False
    except Exception as e:
        print(f"❌ 서버 실행 오류: {e}")
        return False
    
    return True

def run_background_service():
    """백그라운드 서비스 실행"""
    print("🔄 백그라운드 서비스를 시작합니다...")
    
    try:
        from service import start_service
        start_service()
        print("✅ 백그라운드 서비스 시작됨")
        
    except ImportError:
        print("❌ 서비스 모듈을 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 서비스 실행 오류: {e}")

def signal_handler(signum, frame):
    """시그널 핸들러"""
    print("\n🛑 서버를 종료합니다...")
    
    try:
        # Wake lock 해제
        subprocess.run(["termux-wake-unlock"], check=False)
    except:
        pass
    
    sys.exit(0)

def main():
    """메인 함수"""
    print("=" * 50)
    print("📱 상품권 관리 시스템 - 모바일 서버")
    print("=" * 50)
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 안드로이드 환경 확인
    is_android = check_android_environment()
    
    if is_android:
        setup_android_permissions()
    
    # 패키지 설치
    if not install_requirements():
        print("❌ 필수 패키지 설치에 실패했습니다.")
        return
    
    # 백그라운드 서비스 시작
    service_thread = threading.Thread(target=run_background_service)
    service_thread.daemon = True
    service_thread.start()
    
    # 메인 서버 실행
    if not run_mobile_server():
        print("❌ 모바일 서버 실행에 실패했습니다.")
        return
    
    print("✅ 모바일 서버가 성공적으로 시작되었습니다!")
    
    try:
        # 서버 유지
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
