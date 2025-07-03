# 📱 5분 빠른 시작 가이드

## 🎯 목표
안드로이드 폰을 5분 안에 상품권 관리 서버로 만들기!

## 📋 준비물
- 안드로이드 폰 (Android 7.0 이상)
- WiFi 연결
- 5분의 시간

## 🚀 단계별 실행

### 1단계: Termux 설치 (2분)

#### 방법 1: F-Droid (권장)
```bash
1. 브라우저에서 https://f-droid.org 접속
2. "Termux" 검색 후 다운로드
3. APK 설치 (알 수 없는 소스 허용)
```

#### 방법 2: Google Play Store
```bash
1. Play Store에서 "Termux" 검색
2. 설치 (버전이 오래될 수 있음)
```

### 2단계: 파일 전송 (1분)

#### PC에서 안드로이드로 복사
```bash
# 이 폴더 전체를 안드로이드로 복사
# 권장 위치: /storage/emulated/0/giftcard/
```

#### 방법 1: USB 케이블
```bash
1. 안드로이드 폰을 PC에 연결
2. 파일 전송 모드 선택
3. 내부 저장소에 "giftcard" 폴더 생성
4. 모든 파일 복사
```

#### 방법 2: 클라우드 (구글 드라이브, 드롭박스)
```bash
1. PC에서 파일을 클라우드에 업로드
2. 안드로이드에서 다운로드
3. 압축 해제
```

### 3단계: 실행 (2분)

#### Termux에서 명령어 실행
```bash
# 1. Termux 실행
# 2. 다음 명령어들을 순서대로 입력:

# 저장소 권한 허용
termux-setup-storage

# 프로젝트 폴더로 이동
cd /storage/emulated/0/giftcard

# 패키지 업데이트
pkg update

# Python 설치
pkg install python

# 프로그램 실행
python run_mobile_server.py
```

## 🎉 완료!

성공적으로 실행되면 다음과 같은 화면이 나타납니다:

```
📱 상품권 관리 시스템 - 모바일 서버
=======================================
📱 안드로이드 환경 감지됨 (Termux)
🔒 Wake lock 활성화됨
📁 저장소 권한 설정됨
📦 필요한 패키지를 설치하고 있습니다...
✅ 패키지 설치 완료!
🔄 백그라운드 서비스를 시작합니다...
✅ 백그라운드 서비스 시작됨
🚀 모바일 서버를 시작합니다...
✅ 모바일 서버가 성공적으로 시작되었습니다!
```

## 📱 사용 방법

### 모바일 앱 사용
- 터치 인터페이스로 직관적 조작
- 상품권 추가/관리
- 주문 확인/처리
- 실시간 알림

### 웹 관리 페이지
```bash
# 브라우저에서 접속 (같은 WiFi 네트워크)
http://폰의IP주소:5000

# 예: http://192.168.0.100:5000
```

### 백그라운드 실행
```bash
# 화면을 꺼도 계속 실행
# 자동 주문 수집
# SMS 자동 발송
```

## 🔧 기본 설정

### 환경 변수 설정
```bash
# nano 에디터로 .env 파일 수정
nano .env

# 네이버 API 키 입력
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
NAVER_ACCESS_TOKEN=your_access_token

# SMS 설정
NCP_ACCESS_KEY=your_access_key
NCP_SECRET_KEY=your_secret_key
NCP_SERVICE_ID=your_service_id
NCP_CALLING_NUMBER=your_phone_number
```

### 네트워크 설정
```bash
# IP 주소 확인
ip addr show wlan0

# 포트 확인
netstat -tulpn | grep 5000
```

## 💡 유용한 팁

### 배터리 절약
```bash
# 배터리 최적화 해제
설정 → 배터리 → 앱별 최적화 → Termux 해제

# 자동 잠금 해제
설정 → 디스플레이 → 화면 시간 초과 → 30분

# 절전 모드 해제
설정 → 배터리 → 절전 모드 해제
```

### 안정성 향상
```bash
# 자동 재시작 설정
# 오류 발생 시 자동 복구
# 네트워크 연결 끊김 시 재연결
```

### 보안 설정
```bash
# 화면 잠금 설정
# 원격 접근 차단
# 방화벽 설정
```

## 🆘 문제 해결

### 자주 묻는 질문

**Q: "Permission denied" 오류**
```bash
A: 권한 설정 확인
   termux-setup-storage
   설정 → 앱 → Termux → 권한 → 저장소 허용
```

**Q: 패키지 설치 실패**
```bash
A: 인터넷 연결 확인
   pkg update
   pkg upgrade
```

**Q: 앱이 종료됨**
```bash
A: 백그라운드 앱 제한 해제
   설정 → 배터리 → 백그라운드 앱 제한 해제
```

**Q: 웹 페이지 접속 안됨**
```bash
A: 방화벽 확인
   같은 WiFi 네트워크 연결 확인
   IP 주소 확인
```

## 📞 지원

문제가 있으시면 언제든 문의하세요!

**이제 당신의 안드로이드 폰이 완전한 상품권 관리 서버가 되었습니다!** 🎉📱✨
