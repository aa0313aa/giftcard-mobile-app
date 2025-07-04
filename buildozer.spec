# 📱 Buildozer 설정 파일 - 안드로이드 APK 빌드용

[app]
# 앱 기본 정보
title = 상품권 관리 시스템
package.name = giftcardmanager
package.domain = com.giftcard.manager

# 메인 파일
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db
source.exclude_dirs = tests,bin,.venv,__pycache__

# 앱 버전
version = 1.0.0

# 앱 아이콘 및 스플래시
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

# 권한 설정
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,WAKE_LOCK,VIBRATE,SEND_SMS,READ_SMS,RECEIVE_SMS

# 패키지 요구사항 (최소한으로 줄임)
requirements = python3,kivy,kivymd,requests,apscheduler,python-dotenv,pillow,plyer,pyjnius

# 파이썬 버전 (안정성 우선)
python3 = 3.8

# 빌드 설정
[buildozer]
# 빌드 디렉토리
bin_dir = ./bin
build_dir = ./build

# 로그 레벨
log_level = 2

# 서명 설정 (배포용)
[app:android]
# Android SDK 버전 (더 안정적인 버전)
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.gradle_dependencies = 

# 안드로이드 아키텍처
android.archs = arm64-v8a, armeabi-v7a

# 안드로이드 서비스
android.add_src = 

# 안드로이드 자바 디렉토리
android.add_java_dir = 

# 안드로이드 리소스 디렉토리
android.add_resources = 

# 안드로이드 라이브러리
android.add_libs_dir = 

# 안드로이드 AAR 라이브러리
android.add_aars = 

# 안드로이드 Gradle 템플릿
android.gradle_repositories = 

# 안드로이드 매니페스트 템플릿
android.manifest_template = 

# 안드로이드 매니페스트 플레이스홀더
android.manifest_placeholders = 

# 안드로이드 엔트리 포인트
android.entrypoint = org.kivy.android.PythonActivity

# 안드로이드 앱 테마
android.apptheme = @android:style/Theme.NoTitleBar

# 안드로이드 배경 색상
android.theme.background_color = #ffffff

# 안드로이드 상태바 색상
android.theme.statusbar_color = #2196F3

# 안드로이드 네비게이션바 색상
android.theme.navigationbar_color = #2196F3

# 오리엔테이션 설정
orientation = portrait

# 서비스 설정
services = giftcard_service:service.py

# 디버그 설정
[debug]
# 디버그 모드
android.debug = 1

# 프로가드 설정
[proguard]
# 프로가드 비활성화 (개발 단계)
android.proguard = 0

# 릴리스 설정
[release]
# 릴리스 모드
android.debug = 0
android.proguard = 1

# 추가 최적화 설정
android.private_storage = True
android.optimize_python = True
android.strip_libraries = True
android.minify = True

# 더 나은 성능을 위한 설정
android.gradle_dependencies = androidx.core:core:1.6.0
android.add_compile_options = -Xlint:deprecation

# 백그라운드 서비스 설정
services = giftcard_service:service.py:foreground
