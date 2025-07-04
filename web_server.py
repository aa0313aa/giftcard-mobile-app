#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 기반 상품권 관리 시스템
Flask를 사용한 브라우저 인터페이스
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, make_response
import sqlite3
import random
import string
import traceback
from datetime import datetime, timedelta, timezone
import os
import sys
import time
import hmac
import hashlib
import base64
import requests
import json
# import bcrypt  # 안드로이드 빌드에서 문제가 되므로 주석 처리
# import pybase64  # 안드로이드 빌드에서 문제가 되므로 주석 처리
from dotenv import load_dotenv
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import subprocess
import threading
import atexit
from datetime import datetime, timedelta
import cv2
import numpy as np
from PIL import Image
import easyocr
import re
import io

# .env 파일에서 환경 변수 로드
load_dotenv()

# 네이버 커머스 API 정보
NAVER_API_URL = "https://api.commerce.naver.com"
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "6ltcbDAdlg2dCrUfkmrRKb")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "$2a$04$5vDZMSAHWLWQc9MSH2bFP.")

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 실제 운영 시 변경 필요

# 스케줄러 초기화
scheduler = BackgroundScheduler()
scheduler.start()

# 애플리케이션 종료 시 스케줄러 정리
atexit.register(lambda: scheduler.shutdown())

# 주문 자동 수집을 위한 스케줄러 및 상태 관리 변수
order_scheduler = None
order_collection_status = {
    'running': False,
    'last_collection': None,
    'total_orders': 0,
    'new_orders': 0,
    'errors': 0,
    'last_error': None
}

# 데이터베이스 및 설정 파일 경로
DATABASE_PATH = 'gift_cards.db'

# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    
    # 필요한 테이블들 생성
    cursor = conn.cursor()
    
    # 기존 products 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 기존 giftcards 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS giftcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            code TEXT,
            pin_number TEXT,
            expiry_date TEXT,
            status TEXT DEFAULT 'active',
            used INTEGER DEFAULT 0,
            used_date TIMESTAMP,
            customer_name TEXT,
            phone_number TEXT,
            product_order_id TEXT,
            image_path TEXT,
            file_path TEXT,
            link_url TEXT,
            description TEXT,
            type TEXT DEFAULT 'pin',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # 수동 등록 상품 테이블 추가
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manual_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price INTEGER,
            description TEXT,
            keywords TEXT,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 기존 orders 테이블에 notes 컬럼이 없으면 추가 (마이그레이션)
    try:
        cursor.execute("SELECT notes FROM orders LIMIT 1")
    except sqlite3.OperationalError:
        print("[INFO] orders 테이블에 notes 컬럼 추가 중...")
        cursor.execute("ALTER TABLE orders ADD COLUMN notes TEXT")
        print("[INFO] notes 컬럼 추가 완료")
    
    # 기존 orders 테이블에 collected_at 컬럼이 없으면 추가 (마이그레이션)
    try:
        cursor.execute("SELECT collected_at FROM orders LIMIT 1")
    except sqlite3.OperationalError:
        print("[INFO] orders 테이블에 collected_at 컬럼 추가 중...")
        # SQLite에서는 DEFAULT CURRENT_TIMESTAMP를 ALTER TABLE에서 사용할 수 없음
        cursor.execute("ALTER TABLE orders ADD COLUMN collected_at TIMESTAMP")
        # 기존 레코드에 현재 시간 설정
        cursor.execute("UPDATE orders SET collected_at = datetime('now') WHERE collected_at IS NULL")
        print("[INFO] collected_at 컬럼 추가 완료")
    
    conn.commit()
    return conn

def generate_pin():
    """랜덤 핀번호 생성"""
    return f"GIFT-{''.join(random.choices(string.ascii_uppercase + string.digits, k=7))}"

# === 네이버 API 관련 함수 ===

def get_naver_api_signature(timestamp, method, path, client_secret):
    """네이버 API 시그니처 생성 (HMAC 방식)"""
    password = f"{NAVER_CLIENT_ID}_{timestamp}"
    # bcrypt 대신 HMAC-SHA256 사용
    signature = hmac.new(
        client_secret.encode('utf-8'),
        password.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')

def get_naver_access_token():
    """네이버 API 접근 토큰 발급 (Signature 방식)"""
    # 먼저 환경 변수에서 저장된 토큰 확인
    stored_token = os.getenv("NAVER_ACCESS_TOKEN")
    if stored_token and stored_token != "YOUR_NAVER_ACCESS_TOKEN_HERE":
        print(f"[INFO] .env 파일에 저장된 네이버 접근 토큰 사용")
        return stored_token
    
    # 저장된 토큰이 없으면 실시간 발급 시도
    timestamp = str(int(time.time() * 1000))
    method = "POST"
    path = "/external/v1/oauth2/token"
    
    signature = get_naver_api_signature(timestamp, method, path, NAVER_CLIENT_SECRET)
    
    url = f"{NAVER_API_URL}{path}"
    data = {
        "client_id": NAVER_CLIENT_ID,
        "timestamp": timestamp,
        "client_secret_sign": signature,
        "grant_type": "client_credentials",
        "type": "SELF"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    print(f"[INFO] 네이버 API 토큰 발급 시도: {NAVER_CLIENT_ID}")
    try:
        response = requests.post(url, data=data, headers=headers, timeout=20)
        
        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get('access_token')
            if access_token:
                print(f"[SUCCESS] 네이버 접근 토큰 발급 성공")
                return access_token
            else:
                print(f"[ERROR] 응답에서 토큰을 찾을 수 없음: {response_data}")
                return None
        else:
            print(f"[ERROR] 네이버 토큰 발급 실패: {response.status_code}")
            print(f"[ERROR] 응답 내용: {response.text}")
            print(f"[ERROR] 네이버 API 계정 설정을 확인해주세요. (.env 파일)")
            return None
    except Exception as e:
        print(f"[EXCEPTION] 네이버 토큰 발급 중 오류: {e}")
        return None

def get_new_dispatch_waiting_order_ids(access_token):
    """신규주문(발주 후) 상태의 주문 조회"""
    # 토큰이 없는 경우 테스트 데이터 반환
    if not access_token or access_token == "YOUR_NAVER_ACCESS_TOKEN_HERE":
        print("[INFO] 네이버 API 토큰이 설정되지 않음. 테스트 모드로 실행")
        return []  # 빈 배열 반환하여 "새로운 주문이 없습니다" 메시지 출력
    
    path = "/external/v1/pay-order/seller/product-orders"
    url = f"{NAVER_API_URL}{path}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 한국 시간 기준, 24시간 전부터 현재까지 조회
    kst = timezone(timedelta(hours=9))
    to_datetime = datetime.now(kst)
    from_datetime = to_datetime - timedelta(hours=24)

    # ISO-8601 포맷 (밀리초 포함 - 네이버 API 요구사항)
    def to_iso8601(dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+09:00"

    params = {
        "from": to_iso8601(from_datetime),
        "to": to_iso8601(to_datetime),
        "rangeType": "PAYED_DATETIME",
        "productOrderStatuses": ["PAYED"],  # 배열 형태로 변경 (더 많은 주문 발견)
        "placeOrderStatusType": "OK",
        "pageSize": 100,
        "page": 1
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"네이버 API 응답: {response_data}")
            
            data = response_data.get('data', {})
            orders = []
            
            if isinstance(data, dict) and 'contents' in data:
                contents = data.get('contents', [])
                print(f"contents에서 {len(contents)}건 주문 발견")
                
                for order_data in contents:
                    if isinstance(order_data, dict):
                        product_order_id = order_data.get('productOrderId')
                        content = order_data.get('content', {})
                        order_info = content.get('order', {})
                        product_order = content.get('productOrder', {})
                        
                        if product_order_id:
                            orders.append({
                                'product_order_id': product_order_id,
                                'product_name': product_order.get('productName', ''),
                                'customer_name': order_info.get('ordererName', ''),
                                'customer_phone': order_info.get('ordererTel', ''),
                                'quantity': product_order.get('quantity', 1),
                                'unit_price': product_order.get('unitPrice', 0),
                                'order_date': order_info.get('orderDate', ''),
                                'status': product_order.get('productOrderStatus', 'PAYED')
                            })
                            print(f"주문 파싱: {product_order_id} - {product_order.get('productName')} ({order_info.get('ordererName')})")
            
            print(f"파싱된 주문 총 {len(orders)}개")
            return orders
            
        else:
            print(f"[ERROR] 네이버 주문 조회 실패: {response.status_code} {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 네이버 주문 조회 중 오류: {str(e)}")
        return None

def get_naver_products(access_token, page=1, search_keyword=None, category_filter=None):
    """네이버 스마트스토어 상품 목록 조회 - 공식 API 사용"""
    # 공식 API 명세에 따른 엔드포인트 사용
    url = f"{NAVER_API_URL}/external/v1/products/search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # API 명세에 맞게 요청 본문 구성
    request_data = {
        "page": page,  # 공식 API는 1부터 시작
        "size": 20
    }
    
    # 검색어가 있는 경우 검색 조건 추가
    if search_keyword:
        # 상품명 기준으로 검색
        request_data["searchQuery"] = search_keyword
        print(f"[INFO] 검색어 '{search_keyword}'로 상품 검색")
    
    # 카테고리 필터가 있는 경우
    if category_filter:
        request_data["categoryId"] = category_filter
        print(f"[INFO] 카테고리 '{category_filter}'로 필터링")
    
    # 상품 상태별 필터링 (기본: 판매 중인 상품만)
    request_data["productStatusTypes"] = ["SALE"]
    
    # 정렬 기준 (기본: 상품 번호순)
    request_data["orderType"] = "NO"
    
    print(f"[INFO] 네이버 상품 API 요청: {url}")
    print(f"[INFO] 요청 데이터: {request_data}")
    
    try:
        # POST 요청으로 상품 검색 (공식 API는 GET이 아닌 POST 사용)
        response = requests.post(url, headers=headers, json=request_data, timeout=20)
        print(f"[INFO] 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"[SUCCESS] 네이버 상품 API 응답: {response_data}")
            
            # 응답에서 상품 목록 추출
            contents = response_data.get('contents', [])
            products = []
            
            if contents:
                print(f"[INFO] {len(contents)}개 상품 발견")
                
                for product_data in contents:
                    # 기본 상품 정보 추출
                    channel_products = product_data.get('channelProducts', [])
                    
                    # 원상품 번호 가져오기
                    origin_product_no = product_data.get('originProductNo', '')
                    
                    for channel_product in channel_products:
                        product_name = channel_product.get('name', '')
                        product_id = channel_product.get('channelProductNo', '')
                        status = channel_product.get('statusType', '')
                        created_date = channel_product.get('regDate', '')
                        
                        # 카테고리 정보 추출
                        category = channel_product.get('wholeCategoryName', '')
                        
                        # 가격 정보 추출
                        price = channel_product.get('salePrice', 0)
                        
                        products.append({
                            'product_id': str(product_id) or str(origin_product_no),
                            'product_name': product_name,
                            'category': category,
                            'price': price,
                            'status': status,
                            'created_date': created_date
                        })
                        print(f"[INFO] 상품 파싱: {product_id} - {product_name}")
            
            # 페이지네이션 정보 추출
            total_elements = response_data.get('totalElements', len(products))
            total_pages = response_data.get('totalPages', 1)
            current_page = response_data.get('page', 1)
            
            print(f"[SUCCESS] 총 {len(products)}개 상품 조회 완료 (페이지 {current_page}/{total_pages})")
            
            return {
                'products': products,
                'totalPages': total_pages,
                'totalElements': total_elements,
                'currentPage': current_page
            }
        
        else:
            print(f"[ERROR] 네이버 상품 조회 실패: {response.status_code}")
            try:
                error_message = response.json()
                print(f"[ERROR] 오류 상세: {error_message}")
            except Exception:
                print(f"[ERROR] 응답 본문: {response.text}")
    
    except Exception as e:
        print(f"[EXCEPTION] 네이버 상품 조회 예외: {e}")
    
    # 오류 발생 시 로깅하고 최소한의 응답 반환
    print(f"[ERROR] 네이버 API 연결에 실패했습니다. .env 파일의 NAVER_ACCESS_TOKEN이 올바르게 설정되었는지 확인하세요.")
    return {
        'products': [],
        'totalPages': 0,
        'totalElements': 0,
        'currentPage': page
    }
    # 모든 엔드포인트 실패 시 - 네이버 API 인증 문제 진단
    print("[ERROR] 모든 네이버 API 엔드포인트 호출 실패")
    print("[INFO] .env 파일에서 NAVER_ACCESS_TOKEN 설정을 확인하세요")
    print("[INFO] NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 값이 올바른지 확인하세요")
    
    # 테스트용 더미 데이터는 최소화 (1개만 포함)
    dummy_products = [
        {
            'product_id': 'ERROR_001',
            'product_name': '[알림] 네이버 API 연결 실패 - 관리자에게 문의하세요',
            'status': 'ERROR',
            'created_date': '2025-07-03'
        }
    ]
    
    return {
        'products': dummy_products,
        'totalPages': 1,
        'totalElements': len(dummy_products),
        'currentPage': page,
        'note': 'API 연결 실패로 임시 데이터를 표시합니다. 네이버 커머스 API 설정을 확인해주세요.'
    }

# === 기존 코드 ===

@app.route('/')
def index():
    """메인 페이지"""
    conn = get_db_connection()
    
    # 등록된 상품 목록
    products = conn.execute("""
        SELECT p.id, p.product_name, p.is_active, 
               COUNT(g.id) as total_pins,
               SUM(CASE WHEN g.used = 0 AND (g.product_order_id IS NULL OR g.product_order_id = '') THEN 1 ELSE 0 END) as available_pins,
               SUM(CASE WHEN g.used = 1 THEN 1 ELSE 0 END) as used_pins
        FROM products p
        LEFT JOIN giftcards g ON p.id = g.product_id
        GROUP BY p.id, p.product_name, p.is_active
        ORDER BY p.created_date DESC
    """).fetchall()
    
    conn.close()
    
    # 캐시 방지 헤더와 함께 응답 생성
    response = make_response(render_template('index.html', products=products))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/add_product', methods=['POST'])
def add_product():
    """새 상품 등록"""
    product_name = request.form['product_name'].strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '기타').strip()  # 기본값 설정
    price = request.form.get('price', 0)  # 기본값 0
    
    # 가격 처리
    try:
        price = int(price) if price else 0
    except (ValueError, TypeError):
        price = 0
    
    if not product_name:
        flash('상품명을 입력해주세요.', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    try:
        # 중복 확인
        existing = conn.execute(
            "SELECT id FROM products WHERE product_name = ?", 
            (product_name,)
        ).fetchone()
        
        if existing:
            flash(f'이미 등록된 상품입니다: {product_name}', 'error')
        else:
            conn.execute("""
                INSERT INTO products (product_name, category, price, description, is_active, created_date) 
                VALUES (?, ?, ?, ?, 1, datetime('now'))
            """, (product_name, category, price, description))
            conn.commit()
            flash(f'상품이 등록되었습니다: {product_name} (카테고리: {category})', 'success')
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/add_pins', methods=['POST'])
def add_pins():
    """핀번호 추가"""
    product_id = request.form['product_id']
    pin_type = request.form['pin_type']
    
    conn = get_db_connection()
    try:
        # 상품 확인
        product = conn.execute(
            "SELECT product_name FROM products WHERE id = ?", 
            (product_id,)
        ).fetchone()
        
        if not product:
            flash('존재하지 않는 상품입니다.', 'error')
            return redirect(url_for('index'))
        
        added_pins = []
        
        if pin_type == 'manual':
            # 수동 입력
            pins_text = request.form['manual_pins'].strip()
            if pins_text:
                pins = [pin.strip() for pin in pins_text.split('\n') if pin.strip()]
                for pin in pins:
                    if pin:
                        conn.execute("""
                            INSERT INTO giftcards (code, pin_number, product_id, used, created_date)
                            VALUES (?, ?, ?, 0, ?)
                        """, (pin, pin, product_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                        added_pins.append(pin)
        
        elif pin_type == 'file':
            # 파일 업로드 (텍스트 및 이미지)
            print("📁 파일 업로드 처리 시작...")
            
            if 'pin_file' in request.files:
                file = request.files['pin_file']
                print(f"📋 업로드된 파일: {file.filename if file else 'None'}")
                
                if file and file.filename:
                    try:
                        filename = file.filename.lower()
                        print(f"📝 파일명: {filename}")
                        
                        # 이미지 파일인지 확인
                        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
                        is_image = any(filename.endswith(ext) for ext in image_extensions)
                        
                        print(f"🖼️ 이미지 파일 여부: {is_image}")
                        
                        if is_image:
                            # 이미지에서 PIN 추출
                            print("🔍 이미지에서 PIN 추출 시작...")
                            file.seek(0)  # 파일 포인터 리셋
                            extracted_pins = extract_pins_from_image(file)
                            
                            print(f"📊 추출된 PIN들: {extracted_pins}")  # 디버깅용
                            
                            if extracted_pins:
                                for pin in extracted_pins:
                                    print(f"🔍 PIN 검증 중: {pin}")  # 디버깅용
                                    if validate_pin_format(pin):
                                        conn.execute("""
                                            INSERT INTO giftcards (code, pin_number, product_id, used, created_date)
                                            VALUES (?, ?, ?, 0, ?)
                                        """, (pin, pin, product_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                                        added_pins.append(pin)
                                        print(f"✅ PIN 추가됨: {pin}")  # 디버깅용
                                    else:
                                        print(f"❌ PIN 형식 불일치: {pin}")  # 디버깅용
                                
                                if not added_pins:
                                    print("⚠️ 유효한 PIN을 찾을 수 없음")
                                    flash('이미지에서 유효한 PIN을 찾을 수 없습니다. 추출된 텍스트를 확인해주세요.', 'warning')
                            else:
                                print("❌ PIN 추출 실패")
                                flash('이미지에서 PIN을 추출할 수 없습니다. 더 선명한 이미지를 사용해주세요.', 'error')
                        else:
                            # 텍스트 파일 처리
                            print("📄 텍스트 파일 처리 시작...")
                            file.seek(0)  # 파일 포인터 리셋
                            content = file.read().decode('utf-8')
                            print(f"📝 파일 내용 크기: {len(content)} 문자")
                            
                            pins = [pin.strip() for pin in content.split('\n') if pin.strip()]
                            print(f"📋 발견된 PIN 후보: {len(pins)}개")
                            
                            for pin in pins:
                                if pin and validate_pin_format(pin):
                                    conn.execute("""
                                        INSERT INTO giftcards (code, pin_number, product_id, used, created_date)
                                        VALUES (?, ?, ?, 0, ?)
                                    """, (pin, pin, product_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                                    added_pins.append(pin)
                                    print(f"✅ 텍스트 PIN 추가됨: {pin}")
                                else:
                                    print(f"❌ 텍스트 PIN 형식 불일치: {pin}")
                                    
                    except Exception as e:
                        print(f"❌ 파일 처리 오류: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        flash(f'파일 처리 오류: {str(e)}', 'error')
                        return redirect(url_for('index'))
                else:
                    print("❌ 파일이 선택되지 않음")
                    flash('파일을 선택해주세요.', 'error')
                    return redirect(url_for('index'))
            else:
                print("❌ pin_file 필드가 없음")
                flash('파일 업로드 필드를 찾을 수 없습니다.', 'error')
                return redirect(url_for('index'))
        
        elif pin_type == 'link':
            # 링크 발송 (링크를 데이터베이스에 저장)
            print("🔗 링크 발송 처리 시작...")
            
            link_url = request.form.get('link_url', '').strip()
            link_description = request.form.get('link_description', '').strip()
            link_message = request.form.get('link_message', '').strip()
            
            if not link_url:
                flash('발송할 링크 URL을 입력해주세요.', 'error')
                return redirect(url_for('index'))
            
            if not link_description:
                link_description = '링크'
            
            if not link_message:
                link_message = f'{link_description}: {link_url}'
            else:
                link_message = f'{link_message}\n{link_url}'
            
            try:
                print(f"📝 링크 URL: {link_url}")
                print(f"📝 링크 설명: {link_description}")
                print(f"📝 발송 메시지: {link_message}")
                
                # 데이터베이스에 링크 정보 저장 (type='link'로 구분)
                print("💽 데이터베이스에 저장 중...")
                conn.execute("""
                    INSERT INTO giftcards (code, pin_number, product_id, used, created_date, description, type)
                    VALUES (?, ?, ?, 0, ?, ?, 'link')
                """, (link_url, link_message, product_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), link_description))
                
                added_pins.append(f"링크: {link_description}")
                print(f"✅ 링크 등록 완료: {link_description}")
                flash(f'링크가 등록되었습니다: {link_description}', 'success')
                
            except Exception as e:
                print(f"❌ 링크 처리 오류: {str(e)}")
                flash(f'링크 처리 오류: {str(e)}', 'error')
                return redirect(url_for('index'))
        
        elif pin_type == 'image_send':
            # 이미지 파일 발송 (PIN 추출 없이 파일 자체를 발송용으로 저장)
            print("🖼️ 이미지 파일 발송 처리 시작...")
            
            if 'image_file' in request.files:
                file = request.files['image_file']
                print(f"📁 업로드된 파일: {file.filename if file else 'None'}")
                
                if file and file.filename:
                    try:
                        # 파일 확장자 확인
                        filename = file.filename.lower()
                        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
                        
                        print(f"📋 파일명: {filename}")
                        print(f"🔍 지원 확장자: {image_extensions}")
                        
                        if not any(filename.endswith(ext) for ext in image_extensions):
                            print(f"❌ 지원하지 않는 파일 형식: {filename}")
                            flash('이미지 파일만 업로드할 수 있습니다.', 'error')
                            return redirect(url_for('index'))
                        
                        # 파일명 생성 (timestamp + 원본 파일명)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        safe_filename = f"{timestamp}_{file.filename}"
                        file_path = os.path.join('static', 'images', safe_filename)
                        
                        print(f"💾 저장 경로: {file_path}")
                        
                        # 디렉토리가 없으면 생성
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        print(f"📁 디렉토리 생성/확인 완료: {os.path.dirname(file_path)}")
                        
                        # 파일 저장
                        file.save(file_path)
                        print(f"💾 파일 저장 완료: {file_path}")
                        
                        # 파일이 실제로 저장되었는지 확인
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            print(f"✅ 파일 저장 확인: 크기 {file_size} bytes")
                        else:
                            print(f"❌ 파일 저장 실패: {file_path}")
                            flash('파일 저장에 실패했습니다.', 'error')
                            return redirect(url_for('index'))
                        
                        # 이미지 설명 가져오기
                        description = request.form.get('image_description', '').strip()
                        if not description:
                            description = '상품권 이미지'
                        
                        print(f"📝 이미지 설명: {description}")
                        
                        # 데이터베이스에 이미지 정보 저장 (type='image'로 구분)
                        print("💽 데이터베이스에 저장 중...")
                        conn.execute("""
                            INSERT INTO giftcards (code, pin_number, product_id, used, created_date, file_path, description, type)
                            VALUES (?, ?, ?, 0, ?, ?, ?, 'image')
                        """, (safe_filename, description, product_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), file_path, description))
                        
                        added_pins.append(f"이미지: {safe_filename}")
                        print(f"✅ 이미지 파일 등록 완료: {safe_filename}")
                        flash(f'이미지 파일이 등록되었습니다: {safe_filename}', 'success')
                        
                    except Exception as e:
                        print(f"❌ 이미지 파일 처리 오류: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        flash(f'이미지 파일 처리 오류: {str(e)}', 'error')
                        return redirect(url_for('index'))
                else:
                    print("❌ 파일이 선택되지 않음")
                    flash('이미지 파일을 선택해주세요.', 'error')
                    return redirect(url_for('index'))
            else:
                print("❌ image_file 필드가 없음")
                flash('파일 업로드 필드를 찾을 수 없습니다.', 'error')
                return redirect(url_for('index'))
        
        conn.commit()
        if len(added_pins) > 0:
            flash(f'{product["product_name"]}에 {len(added_pins)}개의 항목이 추가되었습니다.', 'success')
        else:
            flash('추가된 항목이 없습니다.', 'warning')
        
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/toggle_product/<int:product_id>')
def toggle_product(product_id):
    """상품 활성화/비활성화"""
    conn = get_db_connection()
    try:
        product = conn.execute(
            "SELECT product_name, is_active FROM products WHERE id = ?", 
            (product_id,)
        ).fetchone()
        
        if product:
            new_status = 0 if product['is_active'] else 1
            conn.execute(
                "UPDATE products SET is_active = ? WHERE id = ?", 
                (new_status, product_id)
            )
            conn.commit()
            
            status_text = "활성화" if new_status else "비활성화"
            flash(f'{product["product_name"]}이 {status_text}되었습니다.', 'success')
        else:
            flash('존재하지 않는 상품입니다.', 'error')
    except Exception as e:
        flash(f'오류가 발생했습니다: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/product_pins/<int:product_id>')
def product_pins(product_id):
    """상품별 핀번호 목록"""
    conn = get_db_connection()
    
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", 
        (product_id,)
    ).fetchone()
    
    if not product:
        flash('존재하지 않는 상품입니다.', 'error')
        return redirect(url_for('index'))
    
    pins = conn.execute("""
        SELECT id, pin_number, used, used_date, customer_name, phone_number, product_order_id, type, description, file_path
        FROM giftcards 
        WHERE product_id = ? 
        ORDER BY created_date DESC
    """, (product_id,)).fetchall()
    
    conn.close()
    return render_template('product_pins.html', product=product, pins=pins)

@app.route('/api/get_naver_products', methods=['GET'])
def api_get_naver_products():
    """네이버 상품 목록 불러오기 API"""
    try:
        # 페이지 파라미터 안전 처리
        page_param = request.args.get('page', '0')
        try:
            page = int(page_param)
        except (ValueError, TypeError):
            print(f"잘못된 page 파라미터: {page_param}, 기본값 0 사용")
            page = 0
        
        category_filter = request.args.get('category', None)  # 카테고리 필터 추가
        
        print(f"=== 네이버 상품 불러오기 시작 (페이지: {page}, 카테고리: {category_filter}) ===")
        
        # 네이버 API 토큰 발급
        access_token = get_naver_access_token()
        if not access_token:
            return jsonify({
                'success': False,
                'message': '네이버 API 토큰 발급에 실패했습니다.'
            })
        
        print("토큰 발급 성공")
        
        # 상품 목록 조회
        result = get_naver_products(access_token, page, None, category_filter)
        
        if result is not None:
            products = result.get('products', [])
            if products:
                print(f"상품 불러오기 성공: {len(products)}개")
                
                # 카테고리와 가격 정보 제거
                for product in products:
                    if 'category' in product:
                        del product['category']
                    if 'price' in product:
                        del product['price']
                        
                message = f'전체 카테고리에서 {len(products)}개 상품을 불러왔습니다.'
                return jsonify({
                    'success': True,
                    'products': products,
                    'totalPages': result.get('totalPages', 1),
                    'totalElements': result.get('totalElements', len(products)),
                    'currentPage': result.get('currentPage', page+1),
                    'message': message + f' (페이지: {result.get('currentPage', page+1)})'
                })
            else:
                error_message = '상품을 찾을 수 없습니다.'
                return jsonify({
                    'success': False,
                    'products': [],
                    'totalPages': result.get('totalPages', 1),
                    'totalElements': result.get('totalElements', 0),
                    'currentPage': result.get('currentPage', page+1),
                    'message': error_message
                })
        else:
            error_message = '상품을 찾을 수 없습니다.'
            return jsonify({
                'success': False,
                'products': [],
                'totalPages': 0,
                'totalElements': 0,
                'currentPage': page+1,
                'message': error_message
            })
    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        })

@app.route('/api/search_naver_products', methods=['GET'])
def api_search_naver_products():
    """네이버 상품 검색 API (로컬 필터링 방식)"""
    try:
        keyword = request.args.get('keyword', '').strip()
        
        if not keyword:
            return jsonify({
                'success': False,
                'message': '검색 키워드를 입력해주세요.'
            })
        
        print(f"=== 네이버 상품 검색 시작 (키워드: {keyword}) ===")
        
        # 네이버 API 토큰 발급
        access_token = get_naver_access_token()
        if not access_token:
            return jsonify({
                'success': False,
                'message': '네이버 API 토큰 발급에 실패했습니다.'
            })
        
        print("토큰 발급 성공")
        
        # 로컬에서 상품 검색
        result = search_products_locally(access_token, keyword)
        products = result['products']
        
        # 카테고리와 가격 정보 제거
        for product in products:
            if 'category' in product:
                del product['category']
            if 'price' in product:
                del product['price']
        
        # 수동 등록된 상품도 검색에 포함
        manual_products = search_manual_products(keyword)
        if manual_products:
            # 수동 등록 상품에서도 카테고리와 가격 정보 제거
            for product in manual_products:
                if 'category' in product:
                    del product['category']
                if 'price' in product:
                    del product['price']
            products.extend(manual_products)
            print(f"수동 등록 상품 {len(manual_products)}개 추가")
        
        # 검색 결과가 없을 때 대체 방안 제공
        if not products:
            # 특정 상품에 대한 대체 제안
            suggested_products = get_alternative_products(keyword)
            manual_registration_info = get_manual_registration_info(keyword)
            
            return jsonify({
                'success': False,
                'message': f'"{keyword}" 검색 결과가 없습니다.',
                'suggestions': suggested_products,
                'manual_registration': manual_registration_info,
                'keyword': keyword
            })
        
        if products:
            print(f"상품 검색 성공: {len(products)}개")
            return jsonify({
                'success': True,
                'products': products,
                'totalPages': 1,
                'totalElements': len(products),
                'currentPage': 0,
                'keyword': keyword,
                'message': f'"{keyword}" 검색 결과: {len(products)}개 상품을 찾았습니다.'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'"{keyword}" 검색 결과가 없습니다.'
            })
    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        })

@app.route('/api/run_automation', methods=['POST'])
def run_automation():
    """자동화 시스템 실행 - 주문 수집 + 문자 발송"""
    try:
        print("🚀 자동화 시스템 시작...")
        
        # 1단계: 주문 수집
        print("1️⃣ 주문 수집 실행...")
        collection_result = collect_orders()
        
        # 2단계: 수집된 주문 처리 및 문자 발송
        print("2️⃣ 주문 처리 및 문자 발송...")
        processing_result = process_orders()
        
        # 3단계: 기존 자동화 스크립트도 실행 (선택사항)
        print("3️⃣ 기존 자동화 스크립트 실행...")
        legacy_result = None
        try:
            import subprocess
            result = subprocess.run(['python', 'send_sms_new_version.py'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                legacy_result = {"success": True, "output": result.stdout}
            else:
                legacy_result = {"success": False, "error": result.stderr}
        except Exception as e:
            legacy_result = {"success": False, "error": str(e)}
        
        # 결과 종합
        total_message = []
        if collection_result.get('success'):
            total_message.append(f"📦 주문 수집: {collection_result.get('new_orders', 0)}개")
        
        if processing_result.get('success'):
            total_message.append(f"📱 문자 발송: {processing_result.get('processed_orders', 0)}개")
        
        if legacy_result and legacy_result.get('success'):
            total_message.append("✅ 기존 자동화 완료")
        
        return jsonify({
            'success': True, 
            'message': '자동화 완료: ' + ', '.join(total_message),
            'details': {
                'collection': collection_result,
                'processing': processing_result,
                'legacy': legacy_result
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'자동화 실행 오류: {str(e)}'
        })

def collect_orders():
    """네이버 스마트스토어에서 신규 주문 수집"""
    global order_collection_status
    try:
        print("[INFO] 주문 수집 작업 시작")
        
        # API 토큰 발급
        access_token = get_naver_access_token()
        if not access_token:
            print("[ERROR] API 토큰 발급 실패")
            return {'success': False, 'message': '네이버 API 토큰 발급 실패', 'new_orders': 0}
            
        # 신규 주문 조회
        orders = get_new_dispatch_waiting_order_ids(access_token)
        if not orders:
            print("[INFO] 새로운 주문이 없습니다.")
            return {'success': True, 'message': '새로운 주문이 없습니다.', 'new_orders': 0}
            
        # 주문 정보 저장
        conn = get_orders_db_connection()
        cursor = conn.cursor()
        
        new_orders = 0
        for order in orders:
            # 이미 존재하는 주문인지 확인
            cursor.execute("SELECT id FROM orders WHERE order_number = ?", (order['product_order_id'],))
            if cursor.fetchone():
                print(f"[INFO] 이미 존재하는 주문 건너뜀: {order['product_order_id']}")
                continue
                
            # 새 주문 추가
            try:
                cursor.execute("""
                    INSERT INTO orders (
                        order_number, product_name, customer_name, phone_number,
                        quantity, price, status, order_date, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    order['product_order_id'], 
                    order['product_name'],
                    order['customer_name'],
                    order['customer_phone'],
                    order['quantity'],
                    order['unit_price'],
                    'pending',
                    order['order_date']
                ))
                new_orders += 1
                print(f"[SUCCESS] 새로운 주문 추가: {order['product_order_id']} - {order['product_name']}")
            except Exception as e:
                print(f"[ERROR] 주문 추가 실패: {order['product_order_id']} - {str(e)}")
                
        conn.commit()
        conn.close()
        
        # 수집 결과 반환
        message = f"{new_orders}개의 새로운 주문을 수집했습니다."
        print(f"[INFO] {message}")
        
        # 전역 상태 업데이트
        order_collection_status['last_collection'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        order_collection_status['total_orders'] += new_orders
        order_collection_status['new_orders'] = new_orders
        
        return {'success': True, 'message': message, 'new_orders': new_orders}
        
    except Exception as e:
        print(f"[ERROR] 주문 수집 중 오류 발생: {str(e)}")
        traceback.print_exc()
        
        # 오류 상태 업데이트
        order_collection_status['errors'] += 1
        order_collection_status['last_error'] = str(e)
        
        return {'success': False, 'message': f'주문 수집 중 오류 발생: {str(e)}', 'new_orders': 0}

def process_orders():
    """DB에 저장된 신규 주문 처리 (PIN 할당 및 SMS 발송)"""
    global order_collection_status
    try:
        print("[INFO] 주문 처리 작업 시작")
        
        # 주문 조회용 연결 (giftcards.db)
        orders_conn = get_orders_db_connection()
        orders_cursor = orders_conn.cursor()
        
        # 상품/PIN 조회용 연결 (products.db)
        products_conn = get_db_connection()
        products_cursor = products_conn.cursor()
        
        # 처리되지 않은 주문 조회
        orders_cursor.execute("""
            SELECT id, order_number, product_name, customer_name, phone_number, quantity
            FROM orders 
            WHERE status = 'pending'
            ORDER BY order_date ASC
        """)
        pending_orders = orders_cursor.fetchall()
        
        if not pending_orders:
            print("[INFO] 처리할 주문이 없습니다.")
            orders_conn.close()
            products_conn.close()
            return {'success': True, 'message': '처리할 주문이 없습니다.', 'processed_orders': 0}
            
        print(f"[INFO] 처리 대기 중인 주문: {len(pending_orders)}개")
        
        processed_orders = 0
        for order in pending_orders:
            try:
                order_id = order['id']
                order_number = order['order_number']
                product_name = order['product_name']
                customer_name = order['customer_name']
                phone_number = order['phone_number']
                quantity = order['quantity']
                
                print(f"[INFO] 주문 처리 중: {order_number} - {product_name} (수량: {quantity})")
                
                # 1. 상품명으로 상품 ID 조회 (더 유연한 매칭) - products.db에서
                product_row = None
                # 정확한 매칭 시도
                products_cursor.execute("""
                    SELECT id FROM products 
                    WHERE product_name = ? AND is_active = 1
                    LIMIT 1
                """, (product_name,))
                product_row = products_cursor.fetchone()
                
                # 정확한 매칭이 안되면 부분 매칭 시도
                if not product_row:
                    products_cursor.execute("""
                        SELECT id FROM products 
                        WHERE product_name LIKE ? AND is_active = 1
                        LIMIT 1
                    """, (f"%{product_name}%",))
                    product_row = products_cursor.fetchone()
                
                # 여전히 안되면 역방향 매칭 시도 (주문 상품명이 더 긴 경우)
                if not product_row:
                    products_cursor.execute("""
                        SELECT id FROM products 
                        WHERE ? LIKE '%' || product_name || '%' AND is_active = 1
                        LIMIT 1
                    """, (product_name,))
                    product_row = products_cursor.fetchone()
                
                if not product_row:
                    print(f"[ERROR] 주문 처리 실패: 상품을 찾을 수 없음 - '{product_name}'")
                    print(f"[INFO] 등록된 상품들과 매칭되지 않습니다. 상품명을 확인해주세요.")
                    orders_cursor.execute("UPDATE orders SET status = 'error', notes = ? WHERE id = ?", 
                                  (f"상품을 찾을 수 없음: {product_name}", order_id))
                    continue
                    
                product_id = product_row['id']
                
                # 2. 사용 가능한 PIN 조회 (주문 수량만큼) - products.db에서
                # 이미지 타입을 우선적으로 선택하도록 ORDER BY 추가
                products_cursor.execute("""
                    SELECT id, pin_number, type, file_path, description FROM giftcards 
                    WHERE product_id = ? AND used = 0 
                    AND (product_order_id IS NULL OR product_order_id = '')
                    ORDER BY CASE WHEN type = 'image' THEN 0 ELSE 1 END, id
                    LIMIT ?
                """, (product_id, quantity))
                available_pins = products_cursor.fetchall()
                
                if len(available_pins) < quantity:
                    print(f"[ERROR] 주문 처리 실패: 사용 가능한 PIN 부족 - 필요: {quantity}, 가용: {len(available_pins)}")
                    orders_cursor.execute("UPDATE orders SET status = 'error', notes = ? WHERE id = ?", 
                                  (f"사용 가능한 PIN 부족 (필요: {quantity}, 가용: {len(available_pins)})", order_id))
                    continue
                    
                # 로그에 PIN 정보 출력 (디버깅용)
                print(f"[INFO] 할당할 PIN {len(available_pins)}개: {[pin['pin_number'] for pin in available_pins]}")
                
                # 3. PIN 할당 및 SMS 발송
                success = send_pins_via_sms(customer_name, phone_number, available_pins, product_name, order_number)
                
                if success:
                    # 4. 주문 상태 및 PIN 상태 업데이트
                    for pin in available_pins:
                        products_cursor.execute("""
                            UPDATE giftcards SET 
                            used = 1, 
                            used_date = datetime('now'), 
                            customer_name = ?,
                            phone_number = ?,
                            product_order_id = ?
                            WHERE id = ?
                        """, (customer_name, phone_number, order_number, pin['id']))
                    
                    orders_cursor.execute("UPDATE orders SET status = 'completed' WHERE id = ?", (order_id,))
                    
                    # 5. 네이버 스마트스토어 발송 상태 업데이트
                    try:
                        access_token = get_naver_access_token()
                        if access_token:
                            update_result = update_naver_order_status(access_token, order_number)
                            if update_result:
                                print(f"[SUCCESS] 네이버 스토어 발송처리 완료: {order_number}")
                            else:
                                print(f"[WARNING] 네이버 스토어 발송처리 실패: {order_number}")
                        else:
                            print(f"[INFO] 네이버 API 토큰 없음 - 수동으로 발송처리 필요: {order_number}")
                    except Exception as e:
                        print(f"[WARNING] 네이버 발송처리 중 오류: {str(e)}")
                    
                    processed_orders += 1
                    print(f"[SUCCESS] 주문 처리 완료: {order_number}")
                else:
                    orders_cursor.execute("UPDATE orders SET status = 'error', notes = ? WHERE id = ?", 
                                  ("SMS 발송 실패", order_id))
                    print(f"[ERROR] 주문 처리 실패: SMS 발송 오류 - {order_number}")
                
            except Exception as e:
                print(f"[ERROR] 주문 처리 중 오류: {str(e)}")
                try:
                    orders_cursor.execute("UPDATE orders SET status = 'error', notes = ? WHERE id = ?", 
                                  (str(e)[:200], order['id']))
                except:
                    pass
        
        orders_conn.commit()
        products_conn.commit()
        orders_conn.close()
        products_conn.close()
        
        # 처리 결과 반환
        message = f"{processed_orders}개 주문을 처리했습니다."
        print(f"[INFO] {message}")
        return {'success': True, 'message': message, 'processed_orders': processed_orders}
        
    except Exception as e:
        print(f"[ERROR] 주문 처리 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return {'success': False, 'message': f'주문 처리 중 오류 발생: {str(e)}', 'processed_orders': 0}

def send_pins_via_sms(customer_name, phone_number, pins, product_name, order_id):
    """핀번호를 SMS/MMS로 발송 (이미지 포함)"""
    try:
        # 전화번호에서 하이픈 제거 (NCP SMS API 요구사항)
        clean_phone_number = phone_number.replace('-', '').replace(' ', '')
        print(f"[INFO] 전화번호 정리: {phone_number} → {clean_phone_number}")
        
        # SMS/MMS 발송 함수 임포트
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from send_sms_new_version import send_sens_sms, send_sens_mms_with_image
        
        # 타입별 PIN 분류
        text_pins = []
        image_pins = []
        link_messages = []
        
        for pin in pins:
            # sqlite3.Row 객체에서 안전하게 값 가져오기
            try:
                pin_type = pin['type'] if pin['type'] else 'pin'
            except (KeyError, TypeError):
                pin_type = 'pin'
            
            if pin_type == 'image':
                image_pins.append(pin)
            elif pin_type == 'link':
                link_messages.append(pin['pin_number'])
            else:
                # 일반 텍스트 PIN
                text_pins.append(pin['pin_number'])
        
        # 발송 성공 카운터
        success_count = 0
        total_count = len(text_pins) + len(image_pins) + len(link_messages)
        
        # 1. 일반 텍스트 PIN이 있으면 SMS로 발송
        if text_pins or link_messages:
            message = f"[상품권발송] {customer_name}님, 주문하신 {product_name} 상품권입니다.\n\n"
            
            if text_pins:
                message += "상품권 정보:\n"
                for i, pin in enumerate(text_pins):
                    message += f"{i+1}. {pin}\n"
            
            # 링크 메시지 추가
            for link_msg in link_messages:
                message += f"\n{link_msg}"
            
            if image_pins:
                message += f"\n※ 추가로 이미지 상품권 {len(image_pins)}개를 별도 발송합니다."
            
            try:
                result = send_sens_sms(clean_phone_number, message)
                if result:
                    success_count += len(text_pins) + len(link_messages)
                    print(f"[SUCCESS] SMS 발송 완료: 텍스트 PIN {len(text_pins)}개, 링크 {len(link_messages)}개")
                else:
                    print(f"[ERROR] SMS 발송 실패")
            except Exception as e:
                print(f"[ERROR] SMS 발송 실패: {str(e)}")
        
        # 2. 이미지 PIN이 있으면 각각 MMS로 발송
        for i, image_pin in enumerate(image_pins):
            try:
                # sqlite3.Row 객체에서 안전하게 값 가져오기
                file_path = image_pin['file_path'] if 'file_path' in image_pin.keys() else ''
                description = image_pin['description'] if 'description' in image_pin.keys() else '상품권 이미지'
                
                if not file_path or not os.path.exists(file_path):
                    print(f"[ERROR] 이미지 파일을 찾을 수 없음: {file_path}")
                    continue
                
                # 이미지 MMS 메시지 구성
                mms_message = f"[상품권발송] {customer_name}님\n{product_name} - {description}\n주문번호: {order_id}"
                
                result = send_sens_mms_with_image(clean_phone_number, mms_message, file_path)
                if result:
                    success_count += 1
                    print(f"[SUCCESS] 이미지 MMS 발송 완료: {description}")
                else:
                    print(f"[ERROR] 이미지 MMS 발송 실패: {description}")
                    
            except Exception as e:
                print(f"[ERROR] 이미지 MMS 발송 중 오류: {str(e)}")
        
        # 전체 발송 결과 확인
        if success_count == total_count:
            print(f"[SUCCESS] 모든 상품권 발송 완료: {success_count}/{total_count}")
            return True
        elif success_count > 0:
            print(f"[WARNING] 일부 상품권 발송 완료: {success_count}/{total_count}")
            return True
        else:
            print(f"[ERROR] 모든 상품권 발송 실패: {success_count}/{total_count}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 상품권 발송 중 오류: {str(e)}")
        traceback.print_exc()
        return False

# === 이미지 처리 및 OCR 함수들 ===
def extract_pins_from_image(image_file):
    """이미지에서 PIN 번호 추출"""
    try:
        print("🔍 이미지 OCR 처리 시작...")
        
        # 이미지 읽기
        image_bytes = image_file.read()
        print(f"📁 이미지 파일 크기: {len(image_bytes)} bytes")
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            print("❌ 이미지 디코딩 실패")
            return []
        
        print(f"🖼️ 이미지 크기: {image.shape}")
        
        # 이미지 전처리
        processed_image = preprocess_image_for_ocr(image)
        print("✅ 이미지 전처리 완료")
        
        # EasyOCR로 텍스트 추출
        print("🤖 EasyOCR 초기화 중...")
        reader = easyocr.Reader(['en', 'ko'])
        print("📖 텍스트 인식 시작...")
        results = reader.readtext(processed_image)
        print(f"📝 인식된 텍스트 수: {len(results)}")
        
        # 인식된 모든 텍스트 출력 (디버깅용)
        for i, (bbox, text, confidence) in enumerate(results):
            print(f"  {i+1}. '{text}' (신뢰도: {confidence:.2f})")
        
        # PIN 패턴 추출
        pins = []
        pin_patterns = [
            r'GIFT-[A-Z0-9]{3,7}',  # GIFT-XXX 형태
            r'[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}',  # XXXX-XXXX-XXXX 형태
            r'[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z0-9]{3}',  # XXX-XXX-XXX 형태
            r'[A-Z0-9]{12,16}',  # 연속된 영숫자 12-16자리
            r'[A-Z0-9]{8,12}',   # 8-12자리 영숫자 (더 넓은 범위)
        ]
        
        print("🔎 PIN 패턴 검색 중...")
        for (bbox, text, confidence) in results:
            try:
                conf_value = float(confidence) if confidence else 0.0
                text_clean = text.strip().upper()
                print(f"  검사 중: '{text_clean}' (신뢰도: {conf_value:.2f})")
                
                if conf_value > 0.3:  # 신뢰도 30% 이상으로 낮춤
                    for pattern in pin_patterns:
                        matches = re.findall(pattern, text_clean)
                        if matches:
                            print(f"    ✅ 매칭: {matches} (패턴: {pattern})")
                            pins.extend(matches)
                        
            except (ValueError, TypeError) as e:
                print(f"    ⚠️ 신뢰도 처리 오류: {e}")
                # 신뢰도 변환 실패시 텍스트만 처리
                text_clean = text.strip().upper()
                for pattern in pin_patterns:
                    matches = re.findall(pattern, text_clean)
                    if matches:
                        print(f"    ✅ 매칭 (신뢰도 무시): {matches}")
                        pins.extend(matches)
        
        # 중복 제거 및 정리
        unique_pins = list(set(pins))
        print(f"🎯 중복 제거 후: {unique_pins}")
        
        # 너무 짧거나 긴 PIN 제거
        filtered_pins = [pin for pin in unique_pins if 6 <= len(pin.replace('-', '').replace(' ', '')) <= 20]
        print(f"✅ 최종 추출된 PIN: {filtered_pins}")
        
        return filtered_pins
        
    except Exception as e:
        print(f"❌ 이미지 OCR 처리 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def preprocess_image_for_ocr(image):
    """OCR을 위한 이미지 전처리"""
    # 그레이스케일 변환
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 노이즈 제거
    denoised = cv2.medianBlur(gray, 3)
    
    # 대비 향상
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # 이진화
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 모폴로지 연산으로 텍스트 개선
    kernel = np.ones((1,1), np.uint8)
    processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return processed

def validate_pin_format(pin):
    """PIN 형식 유효성 검사"""
    if not pin:
        return False
    
    # 기본 길이 체크
    clean_pin = pin.replace('-', '').replace(' ', '')
    if len(clean_pin) < 6 or len(clean_pin) > 20:
        return False
    
    # 영숫자만 포함하는지 체크
    if not re.match(r'^[A-Z0-9\-\s]+$', pin):
        return False
    
    # 너무 단순한 패턴 제외 (예: AAAAAAA, 1111111)
    if len(set(clean_pin)) < 3:
        return False
    
    return True

@app.route('/api/get_order_details/<order_id>', methods=['GET'])
def api_get_order_details(order_id):
    """주문 상세 정보 조회 API"""
    try:
        conn = get_orders_db_connection()
        cursor = conn.cursor()
        
        # 주문 기본 정보 조회 (orders 테이블)
        cursor.execute("""
            SELECT * FROM orders WHERE order_number = ?
        """, (order_id,))
        
        order_basic = cursor.fetchone()
        
        if not order_basic:
            return jsonify({
                'success': False,
                'message': '주문 정보를 찾을 수 없습니다.'
            })
        
        # 주문에 할당된 상품권 조회 (giftcards 테이블)
        cursor.execute("""
            SELECT g.*, p.product_name 
            FROM giftcards g
            LEFT JOIN products p ON g.product_id = p.id
            WHERE g.product_order_id = ?
        """, (order_id,))
        
        giftcards = cursor.fetchall()
        giftcard_list = []
        
        for card in giftcards:
            giftcard_list.append({
                'id': card['id'],
                'pin_number': card['pin_number'],
                'type': card['type'] or 'pin',
                'description': card['description'],
                'used_date': card['used_date'],
                'product_name': card['product_name']
            })
        
        # 주문 정보를 JSON으로 변환
        order_data = {
            'order_id': order_basic['order_number'],
            'product_order_id': order_basic['order_number'],
            'status': order_basic['status'],
            'product_name': order_basic['product_name'],
            'product_option': '',  # 기본값
            'order_status': order_basic['status'],
            'payment_date': order_basic['order_date'],
            'orderer_name': order_basic['customer_name'],
            'orderer_phone': order_basic['phone_number'],
            'receiver_name': order_basic['customer_name'],
            'receiver_phone': order_basic['phone_number'],
            'receiver_email': '',  # 이메일 정보가 없으므로 빈 값
            'quantity': order_basic['quantity'] if 'quantity' in order_basic.keys() else 1,
            'price': order_basic['price'] if 'price' in order_basic.keys() else 0,
            'giftcards': giftcard_list,
            'collected_at': order_basic['collected_at'] if 'collected_at' in order_basic.keys() else None
        }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'order': order_data
        })
        
    except Exception as e:
        print(f"❌ 주문 정보 조회 중 오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'주문 정보 조회 중 오류가 발생했습니다: {str(e)}'
        })

@app.route('/api/order_collection_status', methods=['GET'])
def api_order_collection_status():
    """주문 수집 상태 API"""
    global order_collection_status
    
    return jsonify({
        'success': True,
        'status': order_collection_status
    })

@app.route('/api/start_auto_order_collection', methods=['POST'])
def api_start_auto_order_collection():
    """주문 자동 수집 시작 API"""
    global order_scheduler, order_collection_status
    
    try:
        # 이미 실행 중인 경우
        if order_collection_status['running']:
            return jsonify({
                'success': False,
                'message': '이미 자동 수집이 실행 중입니다.'
            })
        
        # 스케줄러 설정
        data = request.get_json() or {}
        interval = int(data.get('interval', 30))  # 기본 30초
        
        # 최소 10초 간격 강제
        if interval < 10:
            interval = 10
        
        # 트리거 생성
        trigger = IntervalTrigger(seconds=interval)
        
        # 작업 등록 - 주문 수집과 처리를 함께 실행하는 함수로 변경
        order_scheduler = scheduler.add_job(
            run_order_collection_and_processing,
            trigger=trigger,
            id='auto_order_collection',
            replace_existing=True
        )
        
        # 상태 업데이트
        order_collection_status['running'] = True
        order_collection_status['interval'] = interval
        
        return jsonify({
            'success': True,
            'message': f'자동 수집이 {interval}초 간격으로 시작되었습니다.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'자동 수집 시작 중 오류: {str(e)}'
        })

@app.route('/api/stop_auto_order_collection', methods=['POST'])
def api_stop_auto_order_collection():
    """주문 자동 수집 중지 API"""
    global order_collection_status, scheduler
    
    try:
        # 스케줄러에서 작업 제거
        scheduler.remove_job('auto_order_collection')
        
        # 상태 업데이트
        order_collection_status['running'] = False
        
        return jsonify({
            'success': True,
            'message': '자동 수집이 중지되었습니다.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'자동 수집 중지 중 오류: {str(e)}'
        })

@app.route('/api/manual_order_collection', methods=['POST'])
def api_manual_order_collection():
    """수동 주문 수집 실행 API"""
    try:
        # 주문 수집 실행
        result = collect_orders()
        
        if result.get('success'):
            # 수집된 주문이 있는 경우 처리도 실행
            if result.get('new_orders', 0) > 0:
                process_result = process_orders()
                if process_result.get('success'):
                    return jsonify({
                        'success': True,
                        'message': f'{result["new_orders"]}개 주문 수집, {process_result["processed_orders"]}개 처리 완료'
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': f'{result["new_orders"]}개 주문 수집됨. 처리 중 오류: {process_result["message"]}'
                    })
            else:
                return jsonify({
                    'success': True,
                    'message': result['message']
                })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'수동 수집 중 오류: {str(e)}'
        })

def run_order_collection_and_processing():
    """주문 수집과 처리를 연속으로 실행하는 함수 (스케줄러용)"""
    try:
        print("[SCHEDULER] 자동 주문 수집 및 처리 시작")
        
        # 1. 주문 수집
        collection_result = collect_orders()
        
        # 2. 수집된 주문이 있으면 처리 실행
        if collection_result.get('success') and collection_result.get('new_orders', 0) > 0:
            print(f"[SCHEDULER] {collection_result.get('new_orders')}개 주문 수집됨, 처리 시작")
            process_result = process_orders()
            
            if process_result.get('success'):
                print(f"[SCHEDULER] {process_result.get('processed_orders')}개 주문 처리 완료")
            else:
                print(f"[SCHEDULER] 주문 처리 실패: {process_result.get('message')}")
        else:
            print("[SCHEDULER] 새로운 주문이 없거나 수집 실패")
            
    except Exception as e:
        print(f"[SCHEDULER] 자동 주문 처리 중 오류: {str(e)}")
        traceback.print_exc()

# --- 주문 전용 데이터베이스 연결 함수 추가 ---
def get_orders_db_connection():
    """주문 전용 데이터베이스 연결"""
    conn = sqlite3.connect('giftcards.db')
    conn.row_factory = sqlite3.Row
    
    # 필요한 테이블들 생성
    cursor = conn.cursor()
    
    # 새로운 orders 테이블 추가
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            customer_name TEXT,
            phone_number TEXT,
            quantity INTEGER DEFAULT 1,
            price INTEGER,
            status TEXT DEFAULT 'pending',
            order_date TIMESTAMP,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')
    
    # 기존 orders 테이블에 notes 컬럼이 없으면 추가 (마이그레이션)
    try:
        cursor.execute("SELECT notes FROM orders LIMIT 1")
    except sqlite3.OperationalError:
        print("[INFO] orders 테이블에 notes 컬럼 추가 중...")
        cursor.execute("ALTER TABLE orders ADD COLUMN notes TEXT")
        print("[INFO] notes 컬럼 추가 완료")
    
    # 기존 orders 테이블에 collected_at 컬럼이 없으면 추가 (마이그레이션)
    try:
        cursor.execute("SELECT collected_at FROM orders LIMIT 1")
    except sqlite3.OperationalError:
        print("[INFO] orders 테이블에 collected_at 컬럼 추가 중...")
        # SQLite에서는 DEFAULT CURRENT_TIMESTAMP를 ALTER TABLE에서 사용할 수 없음
        cursor.execute("ALTER TABLE orders ADD COLUMN collected_at TIMESTAMP")
        # 기존 레코드에 현재 시간 설정
        cursor.execute("UPDATE orders SET collected_at = datetime('now') WHERE collected_at IS NULL")
        print("[INFO] collected_at 컬럼 추가 완료")
    
    conn.commit()
    return conn

@app.route('/api/process_pending_orders', methods=['POST'])
def api_process_pending_orders():
    """데이터베이스에 있는 pending 상태 주문들을 강제 처리하는 API"""
    try:
        print("[INFO] 기존 pending 주문 강제 처리 시작")
        
        # 주문 처리 실행
        result = process_orders()
        
        return jsonify({
            'success': result.get('success', False),
            'message': result.get('message', '알 수 없는 오류'),
            'processed_orders': result.get('processed_orders', 0)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'주문 처리 중 오류: {str(e)}'
        })

def update_naver_order_status(access_token, order_id, status="DISPATCHED"):
    """네이버 스마트스토어 주문 상태를 발송완료로 업데이트 (최신 API 명세)"""
    try:
        print(f"[DEBUG] 네이버 발송처리 함수 호출됨 - 주문번호: {order_id}")
        print(f"[DEBUG] 토큰 존재 여부: {bool(access_token)}")
        
        if not access_token or access_token == "YOUR_NAVER_ACCESS_TOKEN_HERE":
            print(f"[WARNING] 네이버 API 토큰이 설정되지 않아 주문 상태 업데이트를 건너뜁니다: {order_id}")
            # 토큰 발급 재시도
            print(f"[INFO] 토큰 발급 재시도 중...")
            access_token = get_naver_access_token()
            if not access_token:
                print(f"[ERROR] 토큰 발급 재시도 실패")
                return False
            print(f"[SUCCESS] 토큰 발급 재시도 성공")
        
        # 최신 네이버 커머스 API 명세에 따른 발송처리 엔드포인트
        endpoint = "/external/v1/pay-order/seller/product-orders/dispatch"
        url = f"{NAVER_API_URL}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # 최신 API 명세에 따른 데이터 구조
        dispatch_data = {
            "dispatchProductOrders": [
                {
                    "productOrderId": order_id,
                    "deliveryMethod": "NOTHING",  # 배송 방법 (DELIVERY, NOTHING 등)
                    "deliveryCompanyCode": "ETC",  # 택배사 코드
                    "trackingNumber": "",  # 송장번호 (없으면 빈 문자열)
                    "dispatchDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+09:00")  # ISO 8601 형식
                }
            ]
        }
        
        print(f"[INFO] 네이버 발송처리 API 호출 시작...")
        print(f"[INFO] URL: {url}")
        print(f"[DEBUG] 요청 데이터: {dispatch_data}")
        
        try:
            response = requests.post(url, headers=headers, json=dispatch_data, timeout=20)
            print(f"[DEBUG] 응답 상태: {response.status_code}")
            print(f"[DEBUG] 응답 내용: {response.text}")
            
            if response.status_code in [200, 204]:
                print(f"[SUCCESS] 네이버 주문 발송처리 완료: {order_id}")
                return True
            elif response.status_code == 409:
                # 이미 발송처리된 주문인 경우
                print(f"[INFO] 주문이 이미 발송처리됨: {order_id}")
                return True
            elif response.status_code == 400:
                print(f"[ERROR] 잘못된 요청: {response.text}")
                
                # 대안으로 다른 deliveryMethod 시도
                alternative_methods = ["DELIVERY", "DIRECT_DELIVERY", "VISITRECEIVE"]
                for method in alternative_methods:
                    print(f"[INFO] 대안 deliveryMethod 시도: {method}")
                    
                    alt_data = {
                        "dispatchProductOrders": [
                            {
                                "productOrderId": order_id,
                                "deliveryMethod": method,
                                "deliveryCompanyCode": "ETC",
                                "trackingNumber": "",
                                "dispatchDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+09:00")
                            }
                        ]
                    }
                    
                    try:
                        alt_response = requests.post(url, headers=headers, json=alt_data, timeout=20)
                        print(f"[DEBUG] 대안 응답: {alt_response.status_code} - {alt_response.text}")
                        
                        if alt_response.status_code in [200, 204]:
                            print(f"[SUCCESS] 대안 방법으로 발송처리 완료: {order_id} (방법: {method})")
                            return True
                        elif alt_response.status_code == 409:
                            print(f"[INFO] 주문이 이미 발송처리됨: {order_id}")
                            return True
                    except Exception as e:
                        print(f"[ERROR] 대안 방법 요청 중 오류: {str(e)}")
                        continue
                
                return False
            elif response.status_code == 404:
                print(f"[ERROR] API 엔드포인트를 찾을 수 없음: {endpoint}")
                return False
            elif response.status_code == 401:
                print(f"[ERROR] 인증 실패 - 토큰이 유효하지 않음")
                return False
            else:
                print(f"[ERROR] 발송처리 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] 요청 중 오류: {str(e)}")
            return False
        
    except Exception as e:
        print(f"[ERROR] 네이버 주문 상태 업데이트 중 오류: {str(e)}")
        traceback.print_exc()
        return False

# === PIN 관리 API 엔드포인트 ===

@app.route('/api/resend_pin/<int:pin_id>', methods=['POST'])
def api_resend_pin(pin_id):
    """개별 PIN 재전송"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # PIN 정보 조회
        cursor.execute("""
            SELECT g.*, p.product_name 
            FROM giftcards g 
            JOIN products p ON g.product_id = p.id 
            WHERE g.id = ?
        """, (pin_id,))
        
        pin = cursor.fetchone()
        if not pin:
            return jsonify({'success': False, 'message': 'PIN을 찾을 수 없습니다.'})
        
        # 고객 정보 확인

        customer_name = pin['customer_name']
        phone_number = pin['phone_number']
        
        if not customer_name or not phone_number:
            return jsonify({'success': False, 'message': '고객 정보가 없어 재전송할 수 없습니다.'})
        
        # PIN 정보 준비
        pins_to_send = [pin]
        product_name = pin['product_name']
        order_id = pin['product_order_id'] or f"RESEND-{pin_id}"
        
        # SMS/MMS 발송
        success = send_pins_via_sms(customer_name, phone_number, pins_to_send, product_name, order_id)
        
        if success:
            # 재전송 로그 추가 (선택사항)
            return jsonify({
                'success': True, 
                'message': f'{customer_name}님에게 {product_name} PIN이 재전송되었습니다.'
            })
        else:
            return jsonify({'success': False, 'message': 'SMS/MMS 발송에 실패했습니다.'})
        
    except Exception as e:
        print(f"[ERROR] PIN 재전송 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'재전송 중 오류가 발생했습니다: {str(e)}'})
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/resend_multiple_pins', methods=['POST'])
def api_resend_multiple_pins():
    """대량 PIN 재전송"""
    try:
        data = request.get_json()
        pin_ids = data.get('pin_ids', [])
        
        if not pin_ids:
            return jsonify({'success': False, 'message': '재전송할 PIN을 선택해주세요.'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # PIN 정보들 조회
        placeholders = ','.join(['?'] * len(pin_ids))
        cursor.execute(f"""
            SELECT g.*, p.product_name 
            FROM giftcards g 
            JOIN products p ON g.product_id = p.id 
            WHERE g.id IN ({placeholders})
            AND g.customer_name IS NOT NULL 
            AND g.phone_number IS NOT NULL
        """, pin_ids)
        
        pins = cursor.fetchall()
        
        if not pins:
            return jsonify({'success': False, 'message': '재전송 가능한 PIN이 없습니다.'})
        
        # 고객별로 그룹화
        customer_groups = {}
        for pin in pins:
            customer_key = f"{pin['customer_name']}_{pin['phone_number']}"
            if customer_key not in customer_groups:
                customer_groups[customer_key] = {
                    'customer_name': pin['customer_name'],
                    'phone_number': pin['phone_number'],
                    'pins': [],
                    'product_name': pin['product_name']
                }
            customer_groups[customer_key]['pins'].append(pin)
        
        # 고객별로 재전송
        success_count = 0
        total_customers = len(customer_groups)
        
        for customer_key, group in customer_groups.items():
            try:
                success = send_pins_via_sms(
                    group['customer_name'], 
                    group['phone_number'], 
                    group['pins'],
                    group['product_name'],
                    f"BULK-RESEND-{int(time.time())}"
                )
                if success:
                    success_count += 1
            except Exception as e:
                print(f"[ERROR] 고객 {group['customer_name']} 재전송 실패: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'{success_count}/{total_customers}명의 고객에게 PIN이 재전송되었습니다.'
        })
        
    except Exception as e:
        print(f"[ERROR] 대량 재전송 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'재전송 중 오류가 발생했습니다: {str(e)}'})
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/edit_pin/<int:pin_id>', methods=['POST'])
def api_edit_pin(pin_id):
    """PIN 수정"""
    try:
        data = request.get_json()
        new_pin_number = data.get('new_pin_number', '').strip()
        
        if not new_pin_number:
            return jsonify({'success': False, 'message': '새 PIN 번호를 입력해주세요.'})
        
        # PIN 형식 유효성 검사
        if not validate_pin_format(new_pin_number):
            return jsonify({'success': False, 'message': 'PIN 형식이 올바르지 않습니다. (6-20자, 영숫자)'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 기존 PIN 확인
        cursor.execute("SELECT id, pin_number FROM giftcards WHERE id = ?", (pin_id,))
        existing_pin = cursor.fetchone()
        
        if not existing_pin:
            return jsonify({'success': False, 'message': 'PIN을 찾을 수 없습니다.'})
        
        # 중복 PIN 확인
        cursor.execute("SELECT id FROM giftcards WHERE pin_number = ? AND id != ?", (new_pin_number, pin_id))
        duplicate_pin = cursor.fetchone()
        
        if duplicate_pin:
            return jsonify({'success': False, 'message': '이미 존재하는 PIN 번호입니다.'})
        
        # PIN 업데이트
        cursor.execute("""
            UPDATE giftcards 
            SET pin_number = ?, code = ?
            WHERE id = ?
        """, (new_pin_number, new_pin_number, pin_id))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'PIN이 성공적으로 수정되었습니다. ({existing_pin["pin_number"]} → {new_pin_number})'
        })
        
    except Exception as e:
        print(f"[ERROR] PIN 수정 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'PIN 수정 중 오류가 발생했습니다: {str(e)}'})
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/delete_pin/<int:pin_id>', methods=['POST'])
def api_delete_pin(pin_id):
    """개별 PIN 삭제"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # PIN 정보 조회
        cursor.execute("SELECT pin_number FROM giftcards WHERE id = ?", (pin_id,))
        pin = cursor.fetchone()
        
        if not pin:
            return jsonify({'success': False, 'message': 'PIN을 찾을 수 없습니다.'})
        
        # PIN 삭제
        cursor.execute("DELETE FROM giftcards WHERE id = ?", (pin_id,))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'PIN "{pin["pin_number"]}"이 삭제되었습니다.'
        })
        
    except Exception as e:
        print(f"[ERROR] PIN 삭제 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'PIN 삭제 중 오류가 발생했습니다: {str(e)}'})
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/delete_multiple_pins', methods=['POST'])
def api_delete_multiple_pins():
    """대량 PIN 삭제"""
    try:
        data = request.get_json()
        pin_ids = data.get('pin_ids', [])
        
        if not pin_ids:
            return jsonify({'success': False, 'message': '삭제할 PIN을 선택해주세요.'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # PIN 정보들 조회
        placeholders = ','.join(['?'] * len(pin_ids))
        cursor.execute(f"SELECT id, pin_number FROM giftcards WHERE id IN ({placeholders})", pin_ids)
        pins = cursor.fetchall()
        
        if not pins:
            return jsonify({'success': False, 'message': '삭제할 PIN을 찾을 수 없습니다.'})
        
        # PIN들 삭제
        cursor.execute(f"DELETE FROM giftcards WHERE id IN ({placeholders})", pin_ids)
        deleted_count = cursor.rowcount
        conn.commit();
        
        return jsonify({
            'success': True,
            'message': f'{deleted_count}개의 PIN이 삭제되었습니다.'
        })
        
    except Exception as e:
        print(f"[ERROR] 대량 PIN 삭제 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'PIN 삭제 중 오류가 발생했습니다: {str(e)}'})
    finally:
        if 'conn' in locals():
            conn.close()

def search_products_locally(access_token, keyword):
    """로컬에서 네이버 상품 검색"""
    try:
        print(f"로컬 상품 검색 시작: {keyword}")
        
        # 네이버 API를 통한 상품 검색
        result = get_naver_products(access_token, page=1, search_keyword=keyword)
        
        if result and result.get('success', False):
            products = result.get('products', [])
            print(f"네이버 API에서 {len(products)}개 상품 검색됨")
            
            # 키워드 필터링 (로컬에서 추가 필터링)
            filtered_products = []
            keyword_lower = keyword.lower()
            
            for product in products:
                product_name = product.get('name', '').lower()
                product_description = product.get('description', '').lower()
                
                # 키워드가 상품명이나 설명에 포함되어 있으면 포함
                if (keyword_lower in product_name or 
                    keyword_lower in product_description or
                    any(k in product_name for k in keyword_lower.split())):
                    filtered_products.append(product)
            
            print(f"필터링 후 {len(filtered_products)}개 상품")
            
            return {
                'success': True,
                'products': filtered_products,
                'total': len(filtered_products)
            }
        else:
            print("네이버 API 검색 실패")
            return {
                'success': False,
                'products': [],
                'total': 0
            }
            
    except Exception as e:
        print(f"로컬 상품 검색 오류: {e}")
        return {
            'success': False,
            'products': [],
            'total': 0
        }

def search_manual_products(keyword):
    """수동 등록된 상품 검색"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 수동 등록 상품 테이블에서 검색
        query = """
            SELECT id, name, description, price, category, image_url, created_at
            FROM manual_products 
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
        """
        keyword_pattern = f"%{keyword}%"
        cursor.execute(query, (keyword_pattern, keyword_pattern))
        
        rows = cursor.fetchall()
        products = []
        
        for row in rows:
            product = {
                'id': f"manual_{row[0]}",
                'name': row[1],
                'description': row[2],
                'price': row[3],
                'category': row[4],
                'image_url': row[5],
                'created_at': row[6],
                'source': 'manual'  # 수동 등록 상품임을 표시
            }
            products.append(product)
        
        conn.close()
        print(f"수동 등록 상품 검색 결과: {len(products)}개")
        return products
        
    except Exception as e:
        print(f"수동 등록 상품 검색 오류: {e}")
        return []

def get_alternative_products(keyword):
    """검색 결과가 없을 때 대체 상품 제안"""
    try:
        # 키워드 기반 유사 상품 추천 로직
        suggestions = []
        
        # 간단한 키워드 매칭을 통한 대체 상품 제안
        keyword_lower = keyword.lower()
        
        # 일반적인 상품 카테고리별 추천
        category_suggestions = {
            '상품권': ['문화상품권', '도서상품권', '온라인상품권'],
            '게임': ['게임아이템', '게임머니', '게임쿠폰'],
            '음식': ['외식상품권', '배달쿠폰', '커피쿠폰'],
            '쇼핑': ['쇼핑몰상품권', '백화점상품권', '온라인쇼핑쿠폰']
        }
        
        for category, items in category_suggestions.items():
            if category in keyword_lower:
                suggestions.extend(items)
                break
        
        # 기본 추천 상품 (검색 결과가 없을 때)
        if not suggestions:
            suggestions = ['문화상품권', '도서상품권', '게임아이템', '외식상품권']
        
        return suggestions[:5]  # 최대 5개까지
        
    except Exception as e:
        print(f"대체 상품 제안 오류: {e}")
        return []

def get_manual_registration_info(keyword):
    """수동 등록 안내 정보"""
    return {
        'message': f'"{keyword}" 상품을 직접 등록할 수 있습니다.',
        'steps': [
            '1. 상품 관리 메뉴로 이동',
            '2. "상품 추가" 버튼 클릭',
            '3. 상품 정보 입력 후 저장'
        ],
        'benefits': [
            '즉시 판매 가능',
            '가격 자유 설정',
            '재고 관리 용이'
        ]
    }

if __name__ == '__main__':
    print("🎯 상품권 관리 시스템 웹 서버 시작")
    print("📱 접속 URL: http://localhost:5000")
    print("🔄 주문 자동 수집: 활성화")
    print("📤 SMS 자동 발송: 활성화")
    print("🖼️ 이미지 MMS 발송: 지원")
    print("-" * 50)
    
    # 데이터베이스 초기화
    print("🗄️ 데이터베이스 초기화 중...")
    get_orders_db_connection()
    print("✅ 데이터베이스 초기화 완료")
    
    # 개발 모드로 실행 (디버그 활성화)
    app.run(
        host='0.0.0.0',  # 모든 IP에서 접속 가능
        port=5000,       # 포트 5000
        debug=True,      # 디버그 모드 (코드 변경시 자동 재시작)
        threaded=True    # 멀티스레드 지원
    )
