#!/bin/bash

# 📱 안드로이드 폰 자동 설치 스크립트

echo "📱 상품권 관리 시스템 - 자동 설치"
echo "================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 진행 상황 표시
show_progress() {
    echo -e "${BLUE}🔄 $1...${NC}"
}

show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

show_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# 1. 환경 확인
show_progress "환경 확인 중"

# Android 환경 확인
if [[ -n "$ANDROID_ROOT" ]]; then
    show_success "안드로이드 환경 (Termux) 감지됨"
    ANDROID_ENV=true
else
    show_warning "일반 Linux 환경에서 실행 중"
    ANDROID_ENV=false
fi

# 2. 패키지 업데이트
show_progress "패키지 업데이트 중"

if $ANDROID_ENV; then
    # Termux 환경
    pkg update -y
    pkg upgrade -y
    show_success "Termux 패키지 업데이트 완료"
else
    # 일반 Linux 환경
    sudo apt update -y
    sudo apt upgrade -y
    show_success "시스템 패키지 업데이트 완료"
fi

# 3. Python 설치
show_progress "Python 설치 중"

if $ANDROID_ENV; then
    pkg install python -y
    pkg install python-pip -y
else
    sudo apt install python3 python3-pip -y
fi

# Python 버전 확인
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
show_success "Python $PYTHON_VERSION 설치 완료"

# 4. 필수 패키지 설치
show_progress "필수 패키지 설치 중"

# pip 업그레이드
pip install --upgrade pip

# 필수 패키지 설치
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    show_success "필수 패키지 설치 완료"
else
    show_error "패키지 설치 중 오류 발생"
    exit 1
fi

# 5. 권한 설정 (Android 전용)
if $ANDROID_ENV; then
    show_progress "권한 설정 중"
    
    # 저장소 권한
    termux-setup-storage
    show_success "저장소 권한 설정 완료"
    
    # Wake lock 설정
    termux-wake-lock
    show_success "Wake lock 설정 완료"
fi

# 6. 데이터베이스 초기화
show_progress "데이터베이스 초기화 중"

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

show_success "데이터베이스 초기화 완료"

# 7. 환경 변수 설정
show_progress "환경 변수 설정 중"

if [ ! -f ".env" ]; then
    cat > .env << EOF
# 네이버 커머스 API
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
NAVER_ACCESS_TOKEN=your_access_token

# SMS API (NCP SENS)
NCP_ACCESS_KEY=your_access_key
NCP_SECRET_KEY=your_secret_key
NCP_SERVICE_ID=your_service_id
NCP_CALLING_NUMBER=your_phone_number

# 서버 설정
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
DEBUG_MODE=False

# 백그라운드 서비스 설정
COLLECTION_INTERVAL=30
NOTIFICATION_ENABLED=True
AUTO_RESTART=True
EOF
    show_success "환경 변수 파일 생성 완료"
else
    show_warning "환경 변수 파일이 이미 존재함"
fi

# 8. 자동 시작 스크립트 생성
show_progress "자동 시작 스크립트 생성 중"

cat > start_server.sh << 'EOF'
#!/bin/bash

echo "🚀 상품권 관리 시스템 시작"
echo "========================="

# 프로세스 확인
if pgrep -f "python.*run_mobile_server.py" > /dev/null; then
    echo "⚠️ 서버가 이미 실행 중입니다."
    echo "중지하려면: pkill -f python.*run_mobile_server.py"
    exit 1
fi

# 백그라운드 실행
nohup python run_mobile_server.py > server.log 2>&1 &
SERVER_PID=$!

echo "✅ 서버 시작됨 (PID: $SERVER_PID)"
echo "📝 로그 파일: server.log"
echo "🌐 웹 접속: http://localhost:5000"
echo ""
echo "서버 중지: pkill -f python.*run_mobile_server.py"
echo "로그 확인: tail -f server.log"
EOF

chmod +x start_server.sh
show_success "자동 시작 스크립트 생성 완료"

# 9. 방화벽 설정 (선택사항)
if ! $ANDROID_ENV; then
    show_progress "방화벽 설정 중"
    
    # UFW가 설치되어 있고 활성화되어 있는 경우
    if command -v ufw &> /dev/null; then
        sudo ufw allow 5000/tcp
        show_success "방화벽 포트 5000 허용"
    else
        show_warning "UFW가 설치되지 않음 (선택사항)"
    fi
fi

# 10. 시스템 정보 표시
show_progress "시스템 정보 확인 중"

echo ""
echo "=============================="
echo "📱 설치 완료 - 시스템 정보"
echo "=============================="
echo "🖥️  운영체제: $(uname -s)"
echo "🔧  아키텍처: $(uname -m)"
echo "🐍  Python: $(python --version)"
echo "📦  패키지: $(pip list | wc -l)개 설치됨"
echo "🗄️  데이터베이스: SQLite"
echo "🌐  웹 서버: Flask"
echo "📱  UI 프레임워크: Kivy/KivyMD"
echo ""

if $ANDROID_ENV; then
    echo "📱 안드로이드 전용 설정:"
    echo "   - Wake lock: 활성화"
    echo "   - 저장소 권한: 설정됨"
    echo "   - 백그라운드 실행: 지원"
    echo ""
fi

# 11. 실행 방법 안내
echo "🚀 실행 방법:"
echo "=============================="
echo "1. 직접 실행:"
echo "   python run_mobile_server.py"
echo ""
echo "2. 백그라운드 실행:"
echo "   ./start_server.sh"
echo ""
echo "3. 웹 접속:"
echo "   http://localhost:5000"
echo ""
echo "4. 서버 중지:"
echo "   pkill -f python.*run_mobile_server.py"
echo ""
echo "5. 로그 확인:"
echo "   tail -f server.log"
echo ""

# 12. 마지막 확인
echo "🎯 다음 단계:"
echo "=============================="
echo "1. .env 파일에서 API 키 설정"
echo "2. 서버 실행 테스트"
echo "3. 웹 브라우저에서 접속 확인"
echo "4. 모바일 앱 UI 테스트"
echo "5. SMS 발송 테스트"
echo ""

show_success "🎉 설치 완료! 상품권 관리 시스템을 시작하세요!"

# 즉시 실행 여부 확인
echo ""
read -p "지금 바로 서버를 시작하시겠습니까? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    show_progress "서버 시작 중"
    python run_mobile_server.py
fi
