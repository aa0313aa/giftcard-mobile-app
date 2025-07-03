# 📱 APK 빌드 완전 가이드 - Windows 환경

## 🎯 Windows에서 APK 빌드하기

Windows에서 안드로이드 APK를 빌드하는 방법들을 단계별로 안내합니다.

## 🚀 방법 1: GitHub Actions 사용 (권장)

### 1단계: GitHub 리포지토리 생성

```bash
# 1. GitHub.com에서 새 리포지토리 생성
# 2. 리포지토리 이름: giftcard-mobile-app
# 3. Public 또는 Private 선택
```

### 2단계: 파일 업로드

현재 mobile_app 폴더의 모든 파일을 GitHub에 업로드합니다:

```bash
# 방법 1: GitHub 웹 인터페이스 사용
1. GitHub 리포지토리 페이지에서 "Upload files" 클릭
2. mobile_app 폴더의 모든 파일 드래그 앤 드롭
3. "Commit changes" 클릭

# 방법 2: Git 명령어 사용 (Git 설치 필요)
git clone https://github.com/your-username/giftcard-mobile-app.git
cd giftcard-mobile-app
# 파일들 복사 후
git add .
git commit -m "Initial mobile app files"
git push origin main
```

### 3단계: GitHub Actions 워크플로우 생성

리포지토리에서 `.github/workflows/build-apk.yml` 파일을 생성:

```yaml
name: Build Android APK

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:  # 수동 실행 허용

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          build-essential \
          git \
          python3-dev \
          python3-pip \
          python3-setuptools \
          python3-wheel \
          libssl-dev \
          libffi-dev \
          libpng-dev \
          libjpeg-dev \
          zlib1g-dev
    
    - name: Install Java 8
      uses: actions/setup-java@v3
      with:
        distribution: 'temurin'
        java-version: '8'
    
    - name: Setup Android SDK
      uses: android-actions/setup-android@v2
      with:
        api-level: 31
        build-tools: 31.0.0
        ndk-version: 25.2.9519653
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install buildozer cython
    
    - name: Create presplash.png (if missing)
      run: |
        if [ ! -f presplash.png ]; then
          cp icon.png presplash.png
        fi
    
    - name: Initialize buildozer
      run: |
        # buildozer.spec 파일이 이미 있으므로 초기화 건너뛰기
        echo "Using existing buildozer.spec"
    
    - name: Build APK
      run: |
        buildozer android debug
    
    - name: Upload APK artifact
      uses: actions/upload-artifact@v3
      with:
        name: android-apk
        path: bin/*.apk
        retention-days: 30
    
    - name: Create Release (on tag)
      if: startsWith(github.ref, 'refs/tags/')
      uses: softprops/action-gh-release@v1
      with:
        files: bin/*.apk
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 4단계: 빌드 실행

```bash
# 1. GitHub 리포지토리의 Actions 탭으로 이동
# 2. "Build Android APK" 워크플로우 선택
# 3. "Run workflow" 버튼 클릭
# 4. 빌드 완료까지 대기 (약 10-20분)
# 5. Artifacts에서 APK 다운로드
```

## 🚀 방법 2: WSL2 사용

### 1단계: WSL2 설치

```powershell
# PowerShell을 관리자 권한으로 실행
wsl --install
# 재부팅 후 Ubuntu 설치 완료
```

### 2단계: WSL2에서 빌드 환경 설정

```bash
# WSL2 Ubuntu에서 실행
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y python3-pip python3-dev build-essential git

# Java 8 설치
sudo apt install openjdk-8-jdk

# Android SDK 설치
wget https://dl.google.com/android/repository/commandlinetools-linux-8512546_latest.zip
unzip commandlinetools-linux-8512546_latest.zip
mkdir -p ~/android-sdk/cmdline-tools
mv cmdline-tools ~/android-sdk/cmdline-tools/latest

# 환경변수 설정
echo 'export ANDROID_SDK_ROOT=~/android-sdk' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin' >> ~/.bashrc
source ~/.bashrc

# SDK 구성요소 설치
sdkmanager "platform-tools" "platforms;android-31" "build-tools;31.0.0"
sdkmanager --install "ndk;25.2.9519653"
```

### 3단계: Buildozer 설치 및 빌드

```bash
# Python 패키지 설치
pip3 install buildozer cython

# 프로젝트 파일 복사 (Windows에서 WSL2로)
cp -r /mnt/f/newsms/mobile_app ~/giftcard-app
cd ~/giftcard-app

# 빌드 실행
buildozer android debug
```

## 🚀 방법 3: Docker 사용

### 1단계: Docker Desktop 설치

```bash
# Docker Desktop for Windows 다운로드 및 설치
# https://www.docker.com/products/docker-desktop
```

### 2단계: Dockerfile 생성

`mobile_app` 폴더에 `Dockerfile` 생성:

```dockerfile
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# 시스템 업데이트 및 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    wget \
    unzip \
    openjdk-8-jdk \
    && rm -rf /var/lib/apt/lists/*

# Android SDK 설치
ENV ANDROID_SDK_ROOT=/opt/android-sdk
RUN mkdir -p $ANDROID_SDK_ROOT && \
    cd $ANDROID_SDK_ROOT && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-8512546_latest.zip && \
    unzip commandlinetools-linux-8512546_latest.zip && \
    mkdir -p cmdline-tools && \
    mv cmdline-tools cmdline-tools/latest

ENV PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools

# Android SDK 구성요소 설치
RUN yes | sdkmanager --licenses && \
    sdkmanager "platform-tools" "platforms;android-31" "build-tools;31.0.0" && \
    sdkmanager --install "ndk;25.2.9519653"

# Python 패키지 설치
RUN pip3 install buildozer cython

# 작업 디렉토리 설정
WORKDIR /app

# 프로젝트 파일 복사
COPY . .

# presplash.png 생성 (없는 경우)
RUN if [ ! -f presplash.png ]; then cp icon.png presplash.png; fi

# 빌드 실행
RUN buildozer android debug

# APK 파일을 호스트로 복사할 수 있도록 볼륨 설정
VOLUME ["/app/bin"]
```

### 3단계: Docker 빌드 실행

```powershell
# PowerShell에서 실행 (mobile_app 폴더에서)
docker build -t giftcard-app .

# 컨테이너 실행 및 APK 복사
docker create --name giftcard-container giftcard-app
docker cp giftcard-container:/app/bin ./bin
docker rm giftcard-container
```

## 🚀 방법 4: 클라우드 서비스 사용

### Replit 사용

```bash
# 1. https://replit.com 접속
# 2. "Create Repl" 클릭
# 3. Python 템플릿 선택
# 4. 프로젝트 파일 업로드
# 5. Shell에서 buildozer 설치 및 빌드 실행
```

### CodeSpaces 사용

```bash
# 1. GitHub Codespaces 활성화
# 2. 리포지토리에서 "Code" → "Open with Codespaces"
# 3. 클라우드 환경에서 빌드 실행
```

## 📱 APK 설치 및 테스트

### 1단계: APK 다운로드

빌드가 완료되면 `bin/` 폴더에 APK 파일이 생성됩니다:
- `giftcardmanager-1.0.0-debug.apk`

### 2단계: 안드로이드 폰에 설치

```bash
# 방법 1: ADB 사용
adb install -r giftcardmanager-1.0.0-debug.apk

# 방법 2: 파일 탐색기 사용
1. APK 파일을 안드로이드 폰으로 복사
2. 파일 매니저에서 APK 파일 실행
3. "알 수 없는 소스" 허용
4. 설치 완료
```

### 3단계: 앱 실행 및 테스트

```bash
# 1. 앱 아이콘을 찾아 실행
# 2. 권한 허용 (저장소, 전화, 네트워크)
# 3. 환경 변수 설정 (.env 파일 내용)
# 4. 기능 테스트
```

## 🔧 빌드 최적화

### 빌드 속도 향상

```bash
# buildozer.spec 최적화
android.gradle_dependencies = 
android.archs = arm64-v8a  # 단일 아키텍처로 빌드 시간 단축
```

### APK 크기 최소화

```bash
# 불필요한 패키지 제거
requirements = python3,kivy,kivymd,sqlite3,requests,python-dotenv,plyer

# ProGuard 활성화 (릴리스 빌드)
android.proguard = 1
```

### 메모리 최적화

```bash
# 빌드 시 메모리 설정
export GRADLE_OPTS="-Xmx4g -XX:MaxPermSize=512m"
```

## 🎯 권장 방법

### 초보자: **GitHub Actions** 
- 설정 한 번만 하면 자동 빌드
- 클라우드에서 안정적으로 빌드
- 무료 사용 가능

### 중급자: **WSL2**
- 로컬에서 빌드 가능
- 디버깅 용이
- Windows와 Linux 장점 결합

### 고급자: **Docker**
- 환경 일관성 보장
- 재현 가능한 빌드
- CI/CD 파이프라인 구성 가능

## 🆘 문제 해결

### 자주 발생하는 오류

**빌드 메모리 부족**
```bash
# Gradle 메모리 설정
export GRADLE_OPTS="-Xmx4g"
```

**SDK 라이센스 오류**
```bash
# 라이센스 수락
yes | sdkmanager --licenses
```

**NDK 오류**
```bash
# NDK 버전 확인 및 재설치
sdkmanager --uninstall "ndk-bundle"
sdkmanager --install "ndk;25.2.9519653"
```

## 🎉 빌드 성공!

APK 파일이 성공적으로 생성되면:

1. **설치**: 안드로이드 폰에 APK 설치
2. **테스트**: 모든 기능 동작 확인
3. **배포**: Google Play Store 또는 사이드로딩
4. **업데이트**: 버전 업그레이드 시 재빌드

**이제 완전한 안드로이드 앱으로 상품권 관리 시스템을 사용하세요!** 🎊📱✨
