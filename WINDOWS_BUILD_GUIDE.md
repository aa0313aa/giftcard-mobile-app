# 📱 Windows에서 안드로이드 앱 빌드 가이드

## 🎯 Windows 환경에서의 한계

Windows에서 Buildozer를 사용한 직접 빌드는 어려움이 있습니다. 
대신 다음과 같은 방법들을 제안합니다:

## 🚀 방법 1: GitHub Actions 사용 (권장)

### 1단계: GitHub 리포지토리 생성
```bash
# GitHub에서 새 리포지토리 생성
# mobile_app 폴더 내용을 업로드
```

### 2단계: GitHub Actions 워크플로우 생성
`.github/workflows/build.yml` 파일 생성:

```yaml
name: Build Android APK

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install buildozer cython
        
    - name: Build with Buildozer
      run: |
        buildozer init
        buildozer android debug
        
    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: android-apk
        path: bin/*.apk
```

## 🚀 방법 2: Docker 사용

### 1단계: Docker 설치
```bash
# Docker Desktop for Windows 설치
# https://www.docker.com/products/docker-desktop
```

### 2단계: Docker 컨테이너에서 빌드
```bash
# Dockerfile 생성
FROM kivy/buildozer:latest

WORKDIR /app
COPY . .

RUN buildozer android debug

# 빌드 실행
docker build -t giftcard-app .
docker run -v ${PWD}:/app giftcard-app
```

## 🚀 방법 3: 가상 머신 사용

### 1단계: Linux 가상 머신 설정
```bash
# VirtualBox 또는 VMware 사용
# Ubuntu 20.04 LTS 설치
```

### 2단계: 가상 머신에서 빌드
```bash
# 가상 머신 내에서
sudo apt update
sudo apt install python3 python3-pip
pip3 install buildozer
buildozer android debug
```

## 🚀 방법 4: 온라인 빌드 서비스 사용

### Replit 사용
1. https://replit.com 접속
2. Python 프로젝트 생성
3. 코드 업로드
4. 빌드 실행

### Gitpod 사용
1. https://gitpod.io 접속
2. GitHub 리포지토리 연결
3. 빌드 환경 자동 설정

## 🚀 방법 5: 직접 실행 (Termux 방식)

Windows에서 APK 빌드 대신, 안드로이드에서 직접 실행:

### 1단계: Termux 설치
```bash
# 안드로이드 폰에서 Termux 설치
# F-Droid 버전 권장
```

### 2단계: 파일 전송
```bash
# PC에서 안드로이드로 파일 복사
# mobile_app 폴더 전체를 복사
```

### 3단계: 안드로이드에서 실행
```bash
# Termux에서 실행
cd mobile_app
pkg install python
pip install -r requirements.txt
python run_mobile_server.py
```

## 📱 권장 솔루션

### 즉시 사용 (5분 설정)
**Termux 방식**을 권장합니다:
- 복잡한 빌드 환경 불필요
- 기존 Python 코드 그대로 사용
- 모든 기능 동일하게 작동

### 완전한 앱 (나중에)
**GitHub Actions**를 사용하여:
- 자동 빌드 설정
- 버전 관리
- 배포 자동화

## 🔧 즉시 실행 패키지

바로 사용할 수 있는 패키지를 생성하겠습니다:

```bash
# 1. 파일 다운로드
# 2. 안드로이드 폰으로 전송
# 3. Termux에서 실행
```

## 📋 다음 단계

1. **즉시 시작** → Termux 방식 사용
2. **완전한 앱** → GitHub Actions 설정
3. **고급 기능** → 푸시 알림, 위젯 추가

어떤 방법을 선택하시겠습니까?
