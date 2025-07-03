# 📱 앱 빌드 자동화 스크립트

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_prerequisites():
    """필수 조건 확인"""
    print("🔍 빌드 환경 확인 중...")
    
    # Python 버전 확인
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor} 확인됨")
    
    # 필요한 패키지 확인
    required_packages = ['buildozer', 'cython', 'kivymd']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 설치됨")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 누락됨")
    
    if missing_packages:
        print(f"\n📦 누락된 패키지 설치 중: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✅ 패키지 설치 완료")
        except subprocess.CalledProcessError:
            print("❌ 패키지 설치 실패")
            return False
    
    return True

def create_simple_icons():
    """간단한 아이콘 생성 (SVG 기반)"""
    print("🎨 앱 아이콘 생성 중...")
    
    # SVG 아이콘 생성
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <!-- 배경 그라디언트 -->
  <defs>
    <linearGradient id="bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2196F3;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1976D2;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- 배경 원형 -->
  <circle cx="256" cy="256" r="256" fill="url(#bg-gradient)"/>
  
  <!-- 상품권 카드 -->
  <rect x="150" y="200" width="212" height="130" rx="20" ry="20" fill="#FFFFFF" stroke="#E0E0E0" stroke-width="3"/>
  
  <!-- 카드 상단 줄무늬 -->
  <rect x="170" y="220" width="172" height="20" fill="#FFC107"/>
  
  <!-- 카드 번호 (점선) -->
  <rect x="180" y="260" width="25" height="10" fill="#BDBDBD"/>
  <rect x="220" y="260" width="25" height="10" fill="#BDBDBD"/>
  <rect x="260" y="260" width="25" height="10" fill="#BDBDBD"/>
  <rect x="300" y="260" width="25" height="10" fill="#BDBDBD"/>
  
  <!-- 텍스트 -->
  <text x="256" y="120" text-anchor="middle" font-family="Arial, sans-serif" font-size="48" fill="#FFFFFF">🎁</text>
  <text x="256" y="380" text-anchor="middle" font-family="Arial, sans-serif" font-size="32" fill="#FFFFFF">상품권</text>
  <text x="256" y="420" text-anchor="middle" font-family="Arial, sans-serif" font-size="32" fill="#FFFFFF">관리</text>
</svg>'''
    
    # SVG 파일 저장
    with open('icon.svg', 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print("✅ SVG 아이콘 생성 완료")
    
    # 간단한 PNG 아이콘 생성 (텍스트 기반)
    try:
        # PIL이 있으면 사용
        from PIL import Image, ImageDraw, ImageFont
        
        # 512x512 이미지 생성
        img = Image.new('RGB', (512, 512), '#2196F3')
        draw = ImageDraw.Draw(img)
        
        # 원형 배경
        draw.ellipse([50, 50, 462, 462], fill='#1976D2', outline='#0D47A1', width=10)
        
        # 카드 모양
        draw.rectangle([150, 200, 362, 330], fill='#FFFFFF', outline='#E0E0E0', width=3)
        draw.rectangle([170, 220, 342, 240], fill='#FFC107')
        
        # 카드 번호
        for i in range(4):
            x = 180 + i * 40
            draw.rectangle([x, 260, x+25, 270], fill='#BDBDBD')
        
        # 저장
        img.save('icon.png', 'PNG')
        print("✅ PNG 아이콘 생성 완료")
        
    except ImportError:
        print("⚠️ PIL이 없어 SVG 아이콘만 생성됨")
        
        # 대체 방법: 간단한 텍스트 기반 아이콘 설명 파일 생성
        icon_info = """
# 📱 아이콘 생성 안내

SVG 아이콘이 생성되었습니다: icon.svg

PNG 아이콘이 필요한 경우:
1. 온라인 SVG to PNG 변환기 사용
2. 또는 다음 명령어로 PIL 설치 후 재실행:
   pip install Pillow

아이콘 크기: 512x512
배경색: 파란색 그라디언트 (#2196F3 → #1976D2)
"""
        
        with open('ICON_INFO.md', 'w', encoding='utf-8') as f:
            f.write(icon_info)

def setup_buildozer_config():
    """Buildozer 설정 최적화"""
    print("⚙️ Buildozer 설정 최적화 중...")
    
    # buildozer.spec 파일이 있는지 확인하고 최적화
    if os.path.exists('buildozer.spec'):
        with open('buildozer.spec', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 최적화 설정 추가
        optimizations = """
# 추가 최적화 설정
android.private_storage = True
android.optimize_python = True
android.strip_libraries = True
android.minify = True

# 더 나은 성능을 위한 설정
android.gradle_dependencies = androidx.core:core:1.6.0
android.add_compile_options = -Xlint:deprecation

# 백그라운드 서비스 설정
services = giftcard_service:service.py:foreground
"""
        
        # 설정 파일 업데이트
        with open('buildozer.spec', 'a', encoding='utf-8') as f:
            f.write(optimizations)
        
        print("✅ Buildozer 설정 최적화 완료")
    else:
        print("⚠️ buildozer.spec 파일을 찾을 수 없습니다.")

def build_apk():
    """APK 빌드 실행"""
    print("🚀 APK 빌드 시작...")
    
    try:
        # 디버그 빌드 먼저 실행
        print("1️⃣ 디버그 APK 빌드 중...")
        result = subprocess.run(['buildozer', 'android', 'debug'], 
                              capture_output=True, text=True, timeout=3600)
        
        if result.returncode == 0:
            print("✅ 디버그 APK 빌드 성공!")
            
            # bin 폴더 확인
            if os.path.exists('bin'):
                apk_files = [f for f in os.listdir('bin') if f.endswith('.apk')]
                if apk_files:
                    print(f"📱 생성된 APK 파일: {apk_files[0]}")
                    
                    # APK 파일 크기 확인
                    apk_path = os.path.join('bin', apk_files[0])
                    size_mb = os.path.getsize(apk_path) / (1024 * 1024)
                    print(f"📊 APK 크기: {size_mb:.2f} MB")
                    
                    return True
            
        else:
            print("❌ 디버그 APK 빌드 실패!")
            print("오류 출력:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ 빌드 시간 초과 (1시간)")
        return False
    except Exception as e:
        print(f"❌ 빌드 오류: {e}")
        return False

def create_installation_package():
    """설치 패키지 생성"""
    print("📦 설치 패키지 생성 중...")
    
    # 설치 패키지 폴더 생성
    package_dir = "GiftCard_Mobile_Package"
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # 필요한 파일들 복사
    files_to_copy = [
        'main.py',
        'service.py',
        'requirements.txt',
        'run_mobile_server.py',
        '.env',
        'INSTALL_GUIDE.md',
        'BUILD_GUIDE.md'
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, package_dir)
    
    # bin 폴더의 APK 파일 복사
    if os.path.exists('bin'):
        apk_files = [f for f in os.listdir('bin') if f.endswith('.apk')]
        if apk_files:
            shutil.copy2(os.path.join('bin', apk_files[0]), package_dir)
    
    # 설치 스크립트 생성
    install_script = '''@echo off
echo 📱 상품권 관리 시스템 - 모바일 앱 설치
echo ======================================

echo 🔍 안드로이드 기기 연결 확인 중...
adb devices

echo 📦 APK 설치 중...
for %%f in (*.apk) do (
    echo 설치 중: %%f
    adb install -r "%%f"
    if %errorlevel% equ 0 (
        echo ✅ 설치 완료!
    ) else (
        echo ❌ 설치 실패!
    )
)

echo 🎉 설치 완료! 안드로이드 기기에서 앱을 실행하세요.
pause
'''
    
    with open(os.path.join(package_dir, 'install.bat'), 'w', encoding='utf-8') as f:
        f.write(install_script)
    
    print(f"✅ 설치 패키지 생성 완료: {package_dir}")
    print("📁 패키지 내용:")
    for file in os.listdir(package_dir):
        print(f"   - {file}")

def main():
    """메인 빌드 프로세스"""
    print("=" * 60)
    print("📱 상품권 관리 시스템 - 안드로이드 앱 빌드")
    print("=" * 60)
    
    # 1. 필수 조건 확인
    if not check_prerequisites():
        print("❌ 빌드 환경 설정을 완료한 후 다시 시도하세요.")
        return
    
    # 2. 아이콘 생성
    create_simple_icons()
    
    # 3. Buildozer 설정 최적화
    setup_buildozer_config()
    
    # 4. APK 빌드
    if build_apk():
        print("🎉 APK 빌드 성공!")
        
        # 5. 설치 패키지 생성
        create_installation_package()
        
        print("\n✅ 완전한 안드로이드 앱 빌드 완료!")
        print("📱 다음 단계:")
        print("1. 안드로이드 기기를 USB로 연결")
        print("2. 개발자 옵션 및 USB 디버깅 활성화")
        print("3. install.bat 실행하여 앱 설치")
        print("4. 앱 실행 및 환경 설정")
        
    else:
        print("❌ APK 빌드 실패!")
        print("📋 문제 해결 방법:")
        print("1. Java 8 설치 확인")
        print("2. Android SDK 설정 확인")
        print("3. 빌드 로그 확인")
        print("4. 디스크 공간 확인 (최소 5GB)")

if __name__ == "__main__":
    main()
