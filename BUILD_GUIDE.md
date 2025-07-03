# 📱 안드로이드 앱 빌드 및 배포 가이드

## 🚀 개발 환경 설정

### 1. 필수 도구 설치
```bash
# Python 3.9 이상 설치
python --version

# pip 업그레이드
pip install --upgrade pip

# 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. Android 개발 환경 설정
```bash
# Java 8 설치 (필수)
# Android SDK 설치
# Android NDK 설치

# Buildozer 설치
pip install buildozer

# 초기 설정
buildozer init
```

### 3. 앱 아이콘 및 스플래시 준비
```bash
# 앱 아이콘 (512x512 PNG)
# 파일명: icon.png

# 스플래시 스크린 (1920x1080 PNG)  
# 파일명: presplash.png
```

## 🏗️ 앱 빌드 과정

### 1. 디버그 빌드
```bash
# 안드로이드 디버그 APK 생성
buildozer android debug

# 실행 및 테스트
adb install bin/giftcardmanager-1.0.0-debug.apk
adb shell am start -n com.giftcard.manager/org.kivy.android.PythonActivity
```

### 2. 릴리스 빌드
```bash
# 키스토어 생성 (최초 1회)
keytool -genkey -v -keystore giftcard-release-key.keystore -alias giftcard -keyalg RSA -keysize 2048 -validity 10000

# 릴리스 APK 생성
buildozer android release

# APK 서명
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore giftcard-release-key.keystore bin/giftcardmanager-1.0.0-release-unsigned.apk giftcard

# APK 최적화
zipalign -v 4 bin/giftcardmanager-1.0.0-release-unsigned.apk bin/giftcardmanager-1.0.0-release.apk
```

## 📱 앱 기능 설명

### 🎯 주요 기능
1. **상품권 관리**
   - 상품권 추가/수정/삭제
   - PIN 번호 자동 생성
   - 상태별 필터링 (사용가능/발송완료/사용완료)

2. **주문 관리**
   - 네이버 커머스 API 연동
   - 자동 주문 수집
   - 주문 상태 관리

3. **자동 발송**
   - SMS/MMS 자동 발송
   - 스케줄 관리
   - 발송 이력 추적

4. **실시간 알림**
   - 새 주문 알림
   - 재고 부족 경고
   - 시스템 상태 알림

### 🔧 백그라운드 서비스
- 24시간 자동 운영
- 배터리 최적화
- 오프라인 작업 지원
- 자동 재시작 기능

## 🛠️ 커스터마이징

### 1. UI 테마 변경
```python
# main.py에서 테마 수정
class GiftCardApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Purple"  # 색상 변경
        self.theme_cls.accent_palette = "Orange"
        self.theme_cls.theme_style = "Dark"  # 다크 모드
```

### 2. 알림 설정
```python
# service.py에서 알림 빈도 조정
def run_service(self):
    while self.running:
        time.sleep(60)  # 1분마다 실행 (기본 30초)
```

### 3. 권한 추가
```ini
# buildozer.spec에서 권한 추가
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,CAMERA,RECORD_AUDIO
```

## 🔍 디버깅 및 테스트

### 1. 로그 확인
```bash
# 앱 로그 실시간 확인
adb logcat -s python

# 특정 태그 필터링
adb logcat -s "GiftCardApp"
```

### 2. 성능 모니터링
```bash
# CPU 사용량 확인
adb shell top | grep giftcard

# 메모리 사용량 확인
adb shell dumpsys meminfo com.giftcard.manager
```

### 3. 네트워크 테스트
```python
# 네트워크 연결 확인
import requests
response = requests.get('https://httpbin.org/ip')
print(response.json())
```

## 🚀 배포 및 운영

### 1. Google Play Store 배포
1. **개발자 계정 생성**
   - https://play.google.com/console
   - 등록비 $25 (1회)

2. **앱 정보 준비**
   - 앱 이름: "상품권 관리 시스템"
   - 설명: 상품권 자동 관리 및 발송 시스템
   - 카테고리: 비즈니스
   - 스크린샷: 최소 2장 이상

3. **업로드 및 검토**
   - APK 파일 업로드
   - 개인정보 처리방침 작성
   - 콘텐츠 등급 설정

### 2. 사이드로딩 (개인 사용)
```bash
# APK 파일 직접 설치
adb install -r giftcardmanager-1.0.0-release.apk

# 또는 파일 탐색기로 APK 파일 실행
```

### 3. 업데이트 배포
```bash
# 버전 업데이트
# buildozer.spec에서 version 수정
version = 1.0.1

# 새 APK 빌드
buildozer android release

# 업데이트 배포
```

## 📊 성능 최적화

### 1. 앱 크기 최적화
```python
# 불필요한 라이브러리 제거
# requirements.txt에서 미사용 패키지 삭제

# 이미지 최적화
from PIL import Image
img = Image.open('icon.png')
img.save('icon.png', optimize=True, quality=85)
```

### 2. 메모리 관리
```python
# 주기적 메모리 정리
import gc
gc.collect()

# 대용량 데이터 처리 시 청크 단위로 처리
def process_large_data(data):
    chunk_size = 1000
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        # 처리 로직
```

### 3. 배터리 최적화
```python
# 불필요한 백그라운드 작업 최소화
# 네트워크 요청 배치 처리
# 화면 꺼짐 시 작업 일시 중단
```

## 🔒 보안 고려사항

### 1. 코드 난독화
```bash
# ProGuard 활성화
# buildozer.spec에서 설정
android.proguard = 1
```

### 2. API 키 보안
```python
# 환경 변수 사용
import os
API_KEY = os.environ.get('NAVER_API_KEY')

# 로컬 암호화 저장
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher_suite = Fernet(key)
```

### 3. 네트워크 보안
```python
# HTTPS 강제 사용
import ssl
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_REQUIRED
```

## 📱 최종 APK 파일

빌드가 완료되면 다음 위치에 APK 파일이 생성됩니다:
- 디버그: `bin/giftcardmanager-1.0.0-debug.apk`
- 릴리스: `bin/giftcardmanager-1.0.0-release.apk`

이 APK 파일을 안드로이드 폰에 설치하여 사용하시면 됩니다!

## 🎯 다음 단계

1. **기본 앱 테스트** → 기능 검증
2. **UI/UX 개선** → 사용자 경험 최적화  
3. **고급 기능 추가** → 푸시 알림, 클라우드 동기화
4. **성능 최적화** → 속도 및 안정성 개선
5. **스토어 배포** → 공식 배포 또는 개인 사용

도움이 필요하시면 언제든 말씀해주세요! 🚀
