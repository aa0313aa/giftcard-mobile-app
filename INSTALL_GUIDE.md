# 📱 휴대폰 서버 간편 설치 가이드

## 🎯 안드로이드 폰을 서버로 만들기

### 방법 1: 앱 설치 (권장) 🚀

#### 1단계: APK 파일 다운로드
```bash
# PC에서 APK 빌드 후 폰으로 전송
# 또는 미리 빌드된 APK 파일 사용
```

#### 2단계: 앱 설치
1. 안드로이드 폰에서 "설정" → "보안" → "알 수 없는 소스" 허용
2. APK 파일 실행하여 설치
3. 앱 실행

#### 3단계: 권한 설정
- 📱 전화 권한 (SMS 발송용)
- 📁 저장소 권한 (데이터 저장용)
- 🌐 네트워크 권한 (API 호출용)
- 🔔 알림 권한 (상태 알림용)

#### 4단계: 환경 설정
앱 내에서 네이버 API 키 입력:
- 네이버 Client ID
- 네이버 Client Secret
- 네이버 Access Token
- NCP SMS 설정

### 방법 2: Termux 사용 🐧

#### 1단계: Termux 설치
```bash
# Google Play Store에서 Termux 설치
# 또는 F-Droid에서 설치 (권장)
```

#### 2단계: 환경 설정
```bash
# 패키지 업데이트
pkg update && pkg upgrade

# Python 설치
pkg install python

# 프로젝트 파일 복사
# PC에서 mobile_app 폴더를 폰으로 복사
```

#### 3단계: 의존성 설치
```bash
cd mobile_app
pip install -r requirements.txt
```

#### 4단계: 서버 실행
```bash
python run_mobile_server.py
```

## 📊 성능 비교

### 📱 **안드로이드 앱 방식**
- ✅ 사용자 친화적 UI
- ✅ 백그라운드 자동 실행
- ✅ 시스템 최적화
- ✅ 푸시 알림 지원
- ❌ 개발 시간 필요

### 🐧 **Termux 방식**
- ✅ 빠른 설치
- ✅ 기존 코드 재사용
- ✅ 디버깅 용이
- ❌ 터미널 지식 필요
- ❌ UI 제한적

## 🔧 운영 팁

### 1. 배터리 최적화
```bash
# 배터리 절약 모드 해제
# 앱별 배터리 최적화 해제
# 자동 잠금 시간 증가
```

### 2. 네트워크 설정
```bash
# WiFi 연결 유지
# 모바일 데이터 백업 활성화
# 네트워크 자동 재연결 설정
```

### 3. 보안 설정
```bash
# 화면 잠금 설정
# 원격 접근 차단
# API 키 암호화 저장
```

## 📱 실행 화면 예시

### 메인 화면
```
┌─────────────────────────────┐
│  📱 상품권 관리 시스템        │
├─────────────────────────────┤
│  💳 총 상품권: 1,247개       │
│  ✅ 사용 가능: 892개         │
│  ⏳ 대기 주문: 15개          │
├─────────────────────────────┤
│  📋 상품권 관리              │
│  📦 주문 관리                │
│  🔄 자동 수집 시작           │
│  🖥️ 서버 상태               │
└─────────────────────────────┘
```

### 알림 예시
```
🔔 새 주문 도착!
상품: 구글 플레이 기프트카드
수량: 3개
고객: 010-1234-5678
```

## 🚀 고급 기능

### 1. 원격 모니터링
- 📊 실시간 대시보드
- 📈 매출 통계
- 🔍 주문 추적

### 2. 자동화 스케줄
- ⏰ 정시 수집
- 📅 주간 리포트
- 🔄 자동 백업

### 3. 다중 계정 지원
- 👥 여러 네이버 계정
- 🏪 매장별 관리
- 📱 계정별 알림

## 🔧 문제 해결

### 자주 발생하는 문제

**Q: 앱이 백그라운드에서 종료됨**
```bash
A: 배터리 최적화 해제
   설정 → 앱 → 상품권관리 → 배터리 → 최적화 안함
```

**Q: SMS 발송이 안됨**
```bash
A: 권한 확인 및 API 키 점검
   - 전화 권한 허용
   - NCP SMS 설정 확인
   - 잔액 확인
```

**Q: 네트워크 연결 불안정**
```bash
A: WiFi 절전 모드 해제
   설정 → WiFi → 고급 → WiFi 절전 모드 해제
```

## 📞 지원 및 문의

### 기술 지원
- 📧 이메일: support@giftcard.com
- 💬 카카오톡: @giftcard
- 📱 전화: 1588-1234

### 업데이트 정보
- 🔄 자동 업데이트 활성화
- 📢 공지사항 알림
- 🆕 새 기능 안내

---

이제 안드로이드 폰이 완전한 상품권 관리 서버가 됩니다! 🎉

언제 어디서나 스마트폰으로 상품권 비즈니스를 관리하세요. 📱✨
