@echo off
chcp 65001 > nul
color 0A

echo.
echo ===============================================
echo 📱 APK 빌드 완료 - GitHub Actions 준비됨
echo ===============================================
echo.

echo ✅ 모든 빌드 파일이 준비되었습니다!
echo.

echo 📁 현재 패키지 구성:
echo    - main.py (Kivy 모바일 앱)
echo    - service.py (백그라운드 서비스)
echo    - web_server.py (Flask 웹 서버)
echo    - sms_service.py (SMS 발송 서비스)
echo    - buildozer.spec (빌드 설정)
echo    - .github/workflows/build-apk.yml (CI/CD)
echo    - icon.png, presplash.png (앱 아이콘)
echo    - requirements.txt (의존성)
echo    - 각종 가이드 문서들
echo.

echo 🚀 다음 단계 - APK 빌드:
echo ===============================================
echo.

echo 🌐 방법 1: GitHub Actions (권장)
echo    1. GitHub.com에서 새 리포지토리 생성
echo    2. 현재 폴더의 모든 파일 업로드
echo    3. Actions 탭에서 자동 빌드 실행
echo    4. 완성된 APK 다운로드
echo.

echo 💻 방법 2: WSL2 로컬 빌드
echo    1. WSL2 Ubuntu 설치
echo    2. Android SDK 및 buildozer 설치
echo    3. buildozer android debug 실행
echo.

echo 🐳 방법 3: Docker 빌드
echo    1. Docker Desktop 설치
echo    2. docker build -t giftcard-app .
echo    3. 컨테이너에서 APK 추출
echo.

echo 📖 상세 가이드:
echo ===============================================
echo 📄 GITHUB_BUILD_GUIDE.md - GitHub Actions 상세 가이드
echo 📄 APK_BUILD_COMPLETE_GUIDE.md - 전체 빌드 방법
echo 📄 WINDOWS_BUILD_GUIDE.md - Windows 환경 가이드
echo.

echo 🎯 권장 방법: GitHub Actions
echo ===============================================
echo ✅ 복잡한 환경 설정 불필요
echo ✅ 클라우드에서 안정적 빌드
echo ✅ 자동화된 CI/CD 파이프라인
echo ✅ 무료 사용 가능
echo ✅ 버전 관리 및 릴리스 자동화
echo.

echo 📱 예상 APK 정보:
echo ===============================================
echo 📦 파일명: giftcardmanager-1.0.0-debug.apk
echo 📊 크기: 약 50-80MB
echo 🎯 최소 안드로이드: 7.0 (API 24)
echo 🎯 타겟 안드로이드: 12.0 (API 31)
echo 🏗️ 아키텍처: arm64-v8a, armeabi-v7a
echo.

echo 🔥 주요 기능:
echo ===============================================
echo ✅ 상품권 관리 (추가/수정/삭제)
echo ✅ 네이버 커머스 주문 자동 수집
echo ✅ SMS/MMS 자동 발송
echo ✅ 24시간 백그라운드 실행
echo ✅ 웹 관리 인터페이스 (http://폰IP:5000)
echo ✅ 실시간 푸시 알림
echo ✅ 오프라인 작업 지원
echo ✅ Material Design UI
echo.

set /p github_upload=GitHub에 업로드하여 APK를 빌드하시겠습니까? (y/n): 
if /i "%github_upload%"=="y" (
    echo.
    echo 🌐 GitHub Actions 빌드 진행:
    echo ===============================================
    echo 1. https://github.com 접속
    echo 2. "New repository" 클릭
    echo 3. 리포지토리명: giftcard-mobile-app
    echo 4. 현재 폴더의 모든 파일 업로드
    echo 5. Actions 탭 → "Build Android APK" 실행
    echo 6. 빌드 완료 후 APK 다운로드 (약 10-20분)
    echo.
    echo 📖 상세 가이드: GITHUB_BUILD_GUIDE.md 참고
    echo.
    start https://github.com/new
    start notepad GITHUB_BUILD_GUIDE.md
) else (
    echo.
    echo 💡 다른 빌드 방법:
    echo ===============================================
    echo 📖 APK_BUILD_COMPLETE_GUIDE.md - 모든 빌드 방법
    echo 📖 WINDOWS_BUILD_GUIDE.md - Windows 환경
    echo.
    echo 🚀 언제든 준비되면 GitHub Actions를 사용하세요!
)

echo.
echo 🎉 APK 빌드가 완료되면:
echo ===============================================
echo 1. APK를 안드로이드 폰에 설치
echo 2. 앱 실행 후 권한 허용
echo 3. .env 설정 (API 키 입력)
echo 4. 상품권 관리 시작!
echo.

echo 📞 도움이 필요하시면:
echo ===============================================
echo 📧 기술 지원: 언제든 문의하세요
echo 📖 문서: README.md, QUICK_START.md 참고
echo 🛠️ 문제 해결: 각종 가이드 문서 활용
echo.

echo 🎊 축하합니다! 완전한 APK 빌드 패키지가 준비되었습니다!
echo.
pause
