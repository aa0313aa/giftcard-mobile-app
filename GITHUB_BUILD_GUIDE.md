# 🚀 GitHub Actions APK 빌드 가이드

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
