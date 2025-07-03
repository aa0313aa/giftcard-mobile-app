@echo off
chcp 65001 > nul
color 0A

echo.
echo ===============================================
echo 📱 상품권 관리 시스템 - Windows 설치 도우미
echo ===============================================
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 관리자 권한이 필요합니다.
    echo 💡 우클릭 → "관리자 권한으로 실행"
    pause
    exit /b 1
)

echo ✅ 관리자 권한 확인됨
echo.

:: Python 설치 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다.
    echo.
    echo 🔗 Python 다운로드: https://python.org/downloads
    echo 💡 "Add Python to PATH" 체크 박스 선택 필수
    echo.
    pause
    exit /b 1
)

echo ✅ Python 설치 확인됨
python --version
echo.

:: 가상환경 생성
echo 🔄 가상환경 생성 중...
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ 가상환경 생성 실패
    pause
    exit /b 1
)

echo ✅ 가상환경 생성 완료
echo.

:: 가상환경 활성화
echo 🔄 가상환경 활성화 중...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ 가상환경 활성화 실패
    pause
    exit /b 1
)

echo ✅ 가상환경 활성화 완료
echo.

:: pip 업그레이드
echo 🔄 pip 업그레이드 중...
python -m pip install --upgrade pip
echo.

:: 필수 패키지 설치
echo 🔄 필수 패키지 설치 중...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 패키지 설치 실패
    echo.
    echo 💡 인터넷 연결을 확인하고 다시 시도하세요.
    pause
    exit /b 1
)

echo ✅ 필수 패키지 설치 완료
echo.

:: 데이터베이스 초기화
echo 🔄 데이터베이스 초기화 중...
python -c "
import sqlite3
import os

# 데이터베이스 파일 생성
db_path = 'giftcards.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 상품권 테이블 생성
cursor.execute('''
    CREATE TABLE IF NOT EXISTS giftcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        pin_number TEXT NOT NULL,
        amount INTEGER NOT NULL,
        status TEXT DEFAULT 'available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used_at TIMESTAMP,
        order_id TEXT
    )
''')

# 주문 테이블 생성
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE NOT NULL,
        customer_name TEXT,
        customer_phone TEXT,
        product_name TEXT,
        quantity INTEGER,
        total_amount INTEGER,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP
    )
''')

conn.commit()
conn.close()
print('데이터베이스 초기화 완료')
"

echo ✅ 데이터베이스 초기화 완료
echo.

:: 환경 변수 파일 생성
echo 🔄 환경 변수 파일 생성 중...
if not exist .env (
    (
        echo # 네이버 커머스 API
        echo NAVER_CLIENT_ID=your_client_id
        echo NAVER_CLIENT_SECRET=your_client_secret
        echo NAVER_ACCESS_TOKEN=your_access_token
        echo.
        echo # SMS API ^(NCP SENS^)
        echo NCP_ACCESS_KEY=your_access_key
        echo NCP_SECRET_KEY=your_secret_key
        echo NCP_SERVICE_ID=your_service_id
        echo NCP_CALLING_NUMBER=your_phone_number
        echo.
        echo # 서버 설정
        echo SERVER_HOST=0.0.0.0
        echo SERVER_PORT=5000
        echo DEBUG_MODE=False
        echo.
        echo # 백그라운드 서비스 설정
        echo COLLECTION_INTERVAL=30
        echo NOTIFICATION_ENABLED=True
        echo AUTO_RESTART=True
    ) > .env
    echo ✅ 환경 변수 파일 생성 완료
) else (
    echo ⚠️ 환경 변수 파일이 이미 존재함
)
echo.

:: 시작 스크립트 생성
echo 🔄 시작 스크립트 생성 중...
(
    echo @echo off
    echo chcp 65001 ^> nul
    echo color 0B
    echo.
    echo echo ===============================================
    echo echo 📱 상품권 관리 시스템 - 서버 시작
    echo echo ===============================================
    echo echo.
    echo.
    echo :: 가상환경 활성화
    echo call venv\Scripts\activate.bat
    echo.
    echo :: 서버 시작
    echo echo 🚀 서버 시작 중...
    echo echo 🌐 웹 접속: http://localhost:5000
    echo echo 🛑 종료: Ctrl+C
    echo echo.
    echo python run_mobile_server.py
    echo.
    echo pause
) > start_server.bat

echo ✅ 시작 스크립트 생성 완료
echo.

:: 방화벽 설정 (선택사항)
echo 🔄 방화벽 설정 중...
netsh advfirewall firewall add rule name="GiftCard Server" dir=in action=allow protocol=TCP localport=5000 > nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 방화벽 포트 5000 허용됨
) else (
    echo ⚠️ 방화벽 설정 실패 (선택사항)
)
echo.

:: 바탕화면 바로가기 생성
echo 🔄 바탕화면 바로가기 생성 중...
set DESKTOP=%USERPROFILE%\Desktop
set SCRIPT_PATH=%CD%\start_server.bat
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%DESKTOP%\상품권 관리 시스템.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%SCRIPT_PATH%" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CD%" >> CreateShortcut.vbs
echo oLink.Description = "상품권 관리 시스템 서버" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs > nul 2>&1
del CreateShortcut.vbs > nul 2>&1
echo ✅ 바탕화면 바로가기 생성 완료
echo.

:: 설치 완료 정보 출력
echo ===============================================
echo 🎉 설치 완료! - 시스템 정보
echo ===============================================
echo.
echo 🖥️  운영체제: Windows
echo 🐍  Python: 
python --version
echo 📦  패키지: 설치됨
echo 🗄️  데이터베이스: SQLite
echo 🌐  웹 서버: Flask
echo 📱  UI 프레임워크: Kivy/KivyMD
echo.
echo 📁 설치 위치: %CD%
echo 🔧 가상환경: %CD%\venv
echo 📄 환경 설정: %CD%\.env
echo 🗄️ 데이터베이스: %CD%\giftcards.db
echo.

echo ===============================================
echo 🚀 실행 방법
echo ===============================================
echo.
echo 1. 바탕화면 바로가기 더블클릭
echo    "상품권 관리 시스템.lnk"
echo.
echo 2. 또는 배치 파일 실행
echo    start_server.bat
echo.
echo 3. 웹 브라우저에서 접속
echo    http://localhost:5000
echo.
echo 4. 모바일 앱 UI 사용
echo    터치 인터페이스 지원
echo.

echo ===============================================
echo 🎯 다음 단계
echo ===============================================
echo.
echo 1. .env 파일에서 API 키 설정
echo    - 네이버 커머스 API 키
echo    - NCP SMS API 키
echo.
echo 2. 서버 실행 테스트
echo    - 바탕화면 바로가기 실행
echo    - 웹 브라우저 접속 확인
echo.
echo 3. 기능 테스트
echo    - 상품권 추가/관리
echo    - 주문 처리
echo    - SMS 발송
echo.
echo 4. 모바일 앱 버전 사용
echo    - 안드로이드 폰에 설치
echo    - Termux 또는 APK 방식
echo.

:: 즉시 실행 여부 확인
echo.
set /p answer=지금 바로 서버를 시작하시겠습니까? (y/n): 
if /i "%answer%"=="y" (
    echo.
    echo 🚀 서버 시작 중...
    echo.
    python run_mobile_server.py
) else (
    echo.
    echo 💡 나중에 실행하려면 바탕화면의 바로가기를 사용하세요.
    echo.
    pause
)
