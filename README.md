# 📱 상품권 관리 시스템 - 즉시 실행 패키지

## 🎯 개요
이 패키지는 안드로이드 폰에서 즉시 실행할 수 있는 상품권 관리 시스템입니다.
복잡한 빌드 과정 없이 바로 사용할 수 있습니다.

## 📦 패키지 구성

### 핵심 파일들
- `run_mobile_server.py` - 메인 실행 파일
- `main.py` - Kivy 앱 UI
- `service.py` - 백그라운드 서비스
- `web_server.py` - Flask 웹 서버
- `sms_service.py` - SMS 발송 서비스
- `requirements.txt` - 의존성 패키지
- `.env` - 환경 설정

### 가이드 문서
- `QUICK_START.md` - 5분 빠른 시작
- `TERMUX_GUIDE.md` - Termux 상세 가이드
- `FEATURE_GUIDE.md` - 기능 설명서

## 🚀 5분 빠른 시작

### 1단계: Termux 설치
```bash
# 안드로이드 폰에서 Termux 설치
# Google Play Store 또는 F-Droid
```

### 2단계: 파일 전송
```bash
# PC에서 이 폴더 전체를 안드로이드로 복사
# 권장 위치: /storage/emulated/0/giftcard/
```

### 3단계: 실행
```bash
# Termux에서 실행
cd /storage/emulated/0/giftcard
pkg install python
python run_mobile_server.py
```

## 🎯 실행 결과

### 메인 앱 실행
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

### 웹 인터페이스
```
🌐 웹 관리 페이지: http://localhost:5000
📱 모바일 앱 UI: 터치 인터페이스
🔄 백그라운드 서비스: 자동 실행
📨 SMS 발송: 준비됨
```

## 🔧 주요 기능

### 📱 모바일 앱 기능
- ✅ 터치 친화적 UI
- ✅ 상품권 관리
- ✅ 주문 관리
- ✅ 실시간 알림
- ✅ 오프라인 지원

### 🔄 백그라운드 서비스
- ✅ 24시간 자동 운영
- ✅ 주문 자동 수집
- ✅ SMS 자동 발송
- ✅ 재고 관리
- ✅ 상태 모니터링

### 🌐 웹 관리
- ✅ 원격 접속 지원
- ✅ 전체 기능 제공
- ✅ 통계 대시보드
- ✅ 설정 관리

## 💡 사용 팁

### 배터리 최적화
```bash
# 배터리 절약 모드 해제
# 앱별 배터리 최적화 해제
# Wake lock 기능 활용
```

### 네트워크 설정
```bash
# WiFi 연결 유지
# 모바일 데이터 백업
# 자동 재연결 설정
```

### 알림 설정
```bash
# 푸시 알림 허용
# 중요 알림만 활성화
# 무음 시간 설정
```

## 🔧 고급 설정

### 환경 변수 (.env)
```env
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
```

### 서비스 설정
```python
# service.py에서 수정 가능
COLLECTION_INTERVAL = 30  # 초 (기본: 30초)
NOTIFICATION_ENABLED = True
AUTO_RESTART = True
```

## 📊 모니터링

### 실시간 상태 확인
```bash
# 터미널에서 상태 확인
# 로그 파일 확인
# 웹 대시보드 접속
```

### 성능 모니터링
```bash
# CPU 사용량 확인
# 메모리 사용량 확인
# 네트워크 트래픽 확인
```

## 🔒 보안 고려사항

### 기본 보안
- ✅ 로컬 데이터베이스 암호화
- ✅ API 키 환경변수 저장
- ✅ HTTPS 지원
- ✅ 접근 제어

### 추가 보안
- 🔒 방화벽 설정
- 🔒 VPN 연결
- 🔒 정기 백업
- 🔒 로그 모니터링

## 🆘 문제 해결

### 자주 발생하는 문제

**Q: 앱이 시작되지 않음**
```bash
A: 권한 확인
   - 저장소 권한 허용
   - 네트워크 권한 허용
   - 전화 권한 허용
```

**Q: 백그라운드에서 종료됨**
```bash
A: 배터리 최적화 해제
   - 설정 → 배터리 → 앱별 최적화 해제
   - 자동 잠금 해제
   - Wake lock 활성화
```

**Q: SMS 발송 실패**
```bash
A: API 설정 확인
   - NCP 콘솔에서 SMS 서비스 활성화
   - 잔액 확인
   - 발신번호 등록 확인
```

**Q: 웹 접속 안됨**
```bash
A: 네트워크 확인
   - 방화벽 설정 확인
   - 포트 5000 개방
   - IP 주소 확인
```

## 📞 지원

### 기술 지원
- 📧 이메일: support@giftcard.com
- 💬 카카오톡: @giftcard
- 📞 전화: 1588-1234

### 커뮤니티
- 🌐 공식 홈페이지
- 📱 사용자 커뮤니티
- 🔧 개발자 포럼

## 🎉 즉시 사용 가능!

이 패키지는 **바로 사용할 수 있도록** 모든 것이 준비되어 있습니다!

1. **Termux 설치** (2분)
2. **파일 복사** (1분)
3. **명령어 실행** (2분)

총 **5분**이면 완성! 🚀

---

**상품권 관리 시스템으로 스마트한 비즈니스를 시작하세요!** 📱✨
