# 📱 APK 빌드 검증 및 준비 스크립트

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

def check_build_requirements():
    """빌드 요구사항 검증"""
    print("🔍 빌드 요구사항 검증 중...")
    
    requirements = {
        'files': [
            'main.py',
            'service.py', 
            'web_server.py',
            'sms_service.py',
            'requirements.txt',
            'buildozer.spec',
            'icon.png',
            '.env'
        ],
        'optional_files': [
            'presplash.png'
        ]
    }
    
    # 필수 파일 확인
    missing_files = []
    for file in requirements['files']:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✅ {file} 존재")
    
    if missing_files:
        print(f"❌ 누락된 필수 파일: {', '.join(missing_files)}")
        return False
    
    # 선택적 파일 확인 및 생성
    for file in requirements['optional_files']:
        if not os.path.exists(file):
            if file == 'presplash.png' and os.path.exists('icon.png'):
                shutil.copy2('icon.png', 'presplash.png')
                print(f"✅ {file} 자동 생성됨")
            else:
                print(f"⚠️ {file} 누락됨 (선택사항)")
        else:
            print(f"✅ {file} 존재")
    
    return True

def validate_buildozer_spec():
    """buildozer.spec 파일 검증"""
    print("\n⚙️ buildozer.spec 파일 검증 중...")
    
    if not os.path.exists('buildozer.spec'):
        print("❌ buildozer.spec 파일이 없습니다.")
        return False
    
    with open('buildozer.spec', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 필수 설정 확인
    required_settings = {
        'title': '상품권 관리 시스템',
        'package.name': 'giftcardmanager',
        'package.domain': 'com.giftcard.manager'
    }
    
    for key, expected in required_settings.items():
        if f"{key} = {expected}" in content:
            print(f"✅ {key} 설정 확인됨")
        else:
            print(f"⚠️ {key} 설정 확인 필요")
    
    # 권한 확인
    permissions = [
        'INTERNET',
        'WRITE_EXTERNAL_STORAGE', 
        'READ_EXTERNAL_STORAGE',
        'ACCESS_NETWORK_STATE',
        'WAKE_LOCK',
        'SEND_SMS'
    ]
    
    permission_line = None
    for line in content.split('\n'):
        if 'android.permissions' in line:
            permission_line = line
            break
    
    if permission_line:
        for perm in permissions:
            if perm in permission_line:
                print(f"✅ {perm} 권한 설정됨")
            else:
                print(f"⚠️ {perm} 권한 누락됨")
    
    return True

def check_python_packages():
    """Python 패키지 확인"""
    print("\n📦 Python 패키지 확인 중...")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt 파일이 없습니다.")
        return False
    
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    installed_packages = []
    missing_packages = []
    
    for package in packages:
        package_name = package.split('==')[0].split('>=')[0].split('<=')[0]
        try:
            __import__(package_name.replace('-', '_'))
            installed_packages.append(package_name)
            print(f"✅ {package_name} 설치됨")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} 누락됨")
    
    if missing_packages:
        print(f"\n💡 누락된 패키지 설치 명령어:")
        print(f"pip install {' '.join(missing_packages)}")
    
    return len(missing_packages) == 0

def validate_env_file():
    """환경변수 파일 검증"""
    print("\n🔧 환경변수 파일 검증 중...")
    
    if not os.path.exists('.env'):
        print("❌ .env 파일이 없습니다.")
        return False
    
    required_vars = [
        'NAVER_CLIENT_ID',
        'NAVER_CLIENT_SECRET', 
        'NAVER_ACCESS_TOKEN',
        'NCP_ACCESS_KEY',
        'NCP_SECRET_KEY',
        'NCP_SERVICE_ID',
        'NCP_CALLING_NUMBER'
    ]
    
    with open('.env', 'r', encoding='utf-8') as f:
        env_content = f.read()
    
    for var in required_vars:
        if f"{var}=" in env_content:
            line = [line for line in env_content.split('\n') if line.startswith(f"{var}=")][0]
            value = line.split('=', 1)[1].strip()
            if value and value != 'your_' + var.lower():
                print(f"✅ {var} 설정됨")
            else:
                print(f"⚠️ {var} 값이 기본값입니다. 실제 값으로 변경하세요.")
        else:
            print(f"❌ {var} 누락됨")
    
    return True

def create_build_summary():
    """빌드 요약 정보 생성"""
    print("\n📋 빌드 요약 정보 생성 중...")
    
    summary = {
        "build_info": {
            "app_name": "상품권 관리 시스템",
            "package_name": "com.giftcard.manager",
            "version": "1.0.0",
            "build_date": "2025-07-03",
            "target_platform": "Android"
        },
        "features": [
            "상품권 관리 (추가/수정/삭제)",
            "네이버 커머스 주문 자동 수집",
            "SMS/MMS 자동 발송",
            "24시간 백그라운드 실행",
            "웹 관리 인터페이스",
            "실시간 푸시 알림",
            "오프라인 작업 지원"
        ],
        "technical_specs": {
            "ui_framework": "Kivy/KivyMD",
            "backend": "Flask",
            "database": "SQLite",
            "min_android": "7.0 (API 24)",
            "target_android": "12.0 (API 31)",
            "architecture": "arm64-v8a, armeabi-v7a"
        },
        "build_options": [
            "GitHub Actions (권장)",
            "WSL2 로컬 빌드", 
            "Docker 컨테이너",
            "클라우드 서비스"
        ]
    }
    
    with open('build_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print("✅ build_summary.json 생성 완료")

def generate_github_instructions():
    """GitHub 업로드 가이드 생성"""
    print("\n📖 GitHub 업로드 가이드 생성 중...")
    
    guide = """# 🚀 GitHub Actions APK 빌드 가이드

## 📋 단계별 진행

### 1단계: GitHub 리포지토리 생성
1. https://github.com 접속 후 로그인
2. "New repository" 클릭
3. Repository name: `giftcard-mobile-app`
4. Public 또는 Private 선택
5. "Create repository" 클릭

### 2단계: 파일 업로드
현재 폴더의 모든 파일을 GitHub에 업로드:

#### 방법 1: 웹 인터페이스 (권장)
1. 생성된 리포지토리 페이지에서 "uploading an existing file" 클릭
2. 현재 폴더의 모든 파일 선택 및 드래그 앤 드롭
3. Commit message: "Initial mobile app files" 입력
4. "Commit changes" 클릭

#### 방법 2: Git 명령어 (Git 설치 필요)
```bash
git clone https://github.com/USERNAME/giftcard-mobile-app.git
cd giftcard-mobile-app
# 파일들을 복사한 후
git add .
git commit -m "Initial mobile app files"
git push origin main
```

### 3단계: GitHub Actions 빌드 실행
1. 업로드 완료 후 "Actions" 탭 클릭
2. "Build Android APK" 워크플로우 확인
3. "Run workflow" 버튼 클릭 (수동 실행)
4. 빌드 진행 상황 모니터링 (약 10-20분 소요)

### 4단계: APK 다운로드
1. 빌드 완료 후 "Artifacts" 섹션에서 APK 다운로드
2. 압축 파일 해제
3. `giftcardmanager-1.0.0-debug.apk` 파일 확인

### 5단계: 안드로이드 폰에 설치
1. APK 파일을 안드로이드 폰으로 전송
2. 파일 매니저에서 APK 파일 실행
3. "알 수 없는 소스" 허용
4. 설치 완료 후 앱 실행

## 🔧 문제 해결

### 빌드 실패 시
1. "Actions" 탭에서 실패한 빌드 클릭
2. 로그 확인하여 오류 원인 파악
3. 필요 시 파일 수정 후 재업로드

### 자주 발생하는 오류
- **Java 버전 오류**: GitHub Actions에서 자동 해결
- **Android SDK 라이센스**: 워크플로우에서 자동 수락
- **메모리 부족**: 클라우드 환경에서 자동 관리

## 📱 APK 설치 및 사용

### 최초 설정
1. 앱 실행 후 모든 권한 허용
2. .env 파일 설정 (네이버 API, SMS API)
3. 데이터베이스 초기화 확인
4. 네트워크 연결 테스트

### 기능 테스트
1. 상품권 추가/수정/삭제
2. 주문 수집 테스트
3. SMS 발송 테스트
4. 웹 인터페이스 접속 (http://폰IP:5000)

## 🎉 완료!

축하합니다! 이제 안드로이드 폰이 완전한 상품권 관리 서버가 되었습니다.

- 📱 모바일 앱: 터치 인터페이스
- 🌐 웹 관리: 브라우저 접속
- 🔄 자동화: 24시간 백그라운드 실행
- 📨 알림: 실시간 푸시 알림

**언제 어디서나 스마트폰으로 상품권 비즈니스를 관리하세요!**
"""
    
    with open('GITHUB_BUILD_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ GITHUB_BUILD_GUIDE.md 생성 완료")

def main():
    """메인 검증 프로세스"""
    print("=" * 60)
    print("📱 APK 빌드 준비 및 검증")
    print("=" * 60)
    
    # 1. 빌드 요구사항 검증
    if not check_build_requirements():
        print("\n❌ 빌드 요구사항 검증 실패")
        return False
    
    # 2. buildozer.spec 검증
    if not validate_buildozer_spec():
        print("\n❌ buildozer.spec 검증 실패")
        return False
    
    # 3. Python 패키지 확인
    packages_ok = check_python_packages()
    
    # 4. 환경변수 검증
    validate_env_file()
    
    # 5. 빌드 요약 정보 생성
    create_build_summary()
    
    # 6. GitHub 가이드 생성
    generate_github_instructions()
    
    print("\n" + "=" * 60)
    print("✅ APK 빌드 준비 완료!")
    print("=" * 60)
    
    print("\n🎯 다음 단계:")
    print("1. GITHUB_BUILD_GUIDE.md 참고하여 GitHub에 업로드")
    print("2. GitHub Actions에서 자동 APK 빌드")
    print("3. 빌드된 APK 다운로드 및 설치")
    print("4. 안드로이드 폰에서 앱 실행 및 설정")
    
    if not packages_ok:
        print("\n⚠️ 일부 Python 패키지가 누락되었지만,")
        print("   GitHub Actions에서 자동으로 설치됩니다.")
    
    print("\n🚀 GitHub Actions 빌드를 권장합니다!")
    print("   - 자동화된 빌드 환경")
    print("   - 안정적인 APK 생성") 
    print("   - 무료 사용 가능")
    
    return True

if __name__ == "__main__":
    main()
