# 파일명: send_sms_new_version.py (개선된 전체 코드)

import time
import hmac
import hashlib
import base64
import requests
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import bcrypt
import pybase64
import sys

# .env 파일에서 환경 변수 로드
load_dotenv()

# --- SENS API 정보 ---
SENS_ACCESS_KEY = os.getenv("SENS_ACCESS_KEY")
SENS_SECRET_KEY = os.getenv("SENS_SECRET_KEY")
SENS_SERVICE_ID = os.getenv("SENS_SERVICE_ID")
SENS_SENDER = os.getenv("SENS_SENDER")

# --- 네이버 커머스 API 정보 ---
NAVER_API_URL = "https://api.commerce.naver.com"
# 아래 두 줄에 사장님의 ID와 Secret을 직접 입력하거나 .env 파일에 추가하세요.
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "6ltcbDAdlg2dCrUfkmrRKb")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "$2a$04$5vDZMSAHWLWQc9MSH2bFP.")


# === 로깅 함수 ===
def log_message(message):
    """로그 파일에 메시지를 기록하는 함수"""
    print(message)
    try:
        with open("giftcard_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {message}\n")
    except Exception as e:
        print(f"[ERROR] 로그 파일 쓰기 실패: {e}")


# === 네이버 API 관련 함수 ===

def get_naver_api_signature(timestamp, method, path, client_secret):
    """네이버 API 시그니처 생성 (bcrypt 방식)"""
    password = f"{NAVER_CLIENT_ID}_{timestamp}"
    hashed = bcrypt.hashpw(password.encode('utf-8'), client_secret.encode('utf-8'))
    return pybase64.standard_b64encode(hashed).decode('utf-8')

def get_naver_access_token():
    """네이버 API 접근 토큰 발급 (Signature 방식)"""
    timestamp = str(int(time.time() * 1000))
    method = "POST"
    # [오류 수정] '/external' 경로를 추가하여 404 Not Found 오류 해결
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
    response = requests.post(url, data=data, headers=headers)
    
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        log_message(f"[SUCCESS] 네이버 접근 토큰 발급 성공")
        return access_token
    else:
        log_message(f"[ERROR] 네이버 토큰 발급 실패: {response.status_code} {response.text}")
        return None

def get_new_dispatch_waiting_order_ids(access_token):
    """신규주문(발주 후) 상태의 주문 조회 - 정확한 API 사용"""
    path = "/external/v1/pay-order/seller/product-orders"
    url = f"{NAVER_API_URL}{path}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 한국 시간 기준, 1일 전부터 현재까지 조회
    kst = timezone(timedelta(hours=9))
    to_datetime = datetime.now(kst)
    from_datetime = to_datetime - timedelta(hours=24)

    # ISO-8601 포맷 (정확한 포맷)
    def to_iso8601(dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+09:00"

    params = {
        "from": to_iso8601(from_datetime),
        "to": to_iso8601(to_datetime),
        "rangeType": "PAYED_DATETIME",  # 결제 일시 기준
        "productOrderStatuses": ["PAYED"],  # 결제 완료 상태
        "placeOrderStatusType": "OK",  # 발주 확인 완료 (발주 후)
        "pageSize": 100,
        "page": 1
    }

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        response_data = response.json()
        log_message(f"전체 응답 구조: {response_data}")
        
        data = response_data.get('data', [])
        order_ids = []
        
        log_message(f"결제완료+발주확인 주문 조회 완료")
        log_message(f"data 타입: {type(data)}")
        log_message(f"data 내용: {data}")
        
        # 응답이 배열인지 딕셔너리인지 확인
        if isinstance(data, list):
            log_message(f"배열 형태 데이터: {len(data)}건")
            for i, order in enumerate(data):
                log_message(f"주문 {i}: {type(order)} - {order}")
                if isinstance(order, dict):
                    product_order = order.get('productOrder', {})
                    product_order_id = product_order.get('productOrderId')
                    if product_order_id:
                        order_ids.append(product_order_id)
                        order_info = order.get('order', {})
                        log_message(f"발견된 주문: {product_order_id} - {order_info.get('ordererName')}")
        elif isinstance(data, dict):
            log_message(f"딕셔너리 형태 데이터: {list(data.keys())}")
            # 네이버 API 응답 구조: data.contents 배열
            if 'contents' in data:
                orders = data.get('contents', [])
                log_message(f"contents에서 {len(orders)}건 주문 발견")
                for order_data in orders:
                    if isinstance(order_data, dict):
                        # 구조: order_data.content.order, order_data.content.productOrder
                        product_order_id = order_data.get('productOrderId')
                        content = order_data.get('content', {})
                        order_info = content.get('order', {})
                        product_order = content.get('productOrder', {})
                        
                        if product_order_id:
                            order_ids.append(product_order_id)
                            log_message(f"발견된 주문: {product_order_id} - {order_info.get('ordererName')} - {product_order.get('productName')}")
            elif 'content' in data:
                orders = data.get('content', [])
                log_message(f"content에서 {len(orders)}건 주문 발견")
                for order in orders:
                    if isinstance(order, dict):
                        product_order = order.get('productOrder', {})
                        product_order_id = product_order.get('productOrderId')
                        if product_order_id:
                            order_ids.append(product_order_id)
                            order_info = order.get('order', {})
                            log_message(f"발견된 주문: {product_order_id} - {order_info.get('ordererName')}")
        
        log_message(f"처리 대상 주문 ID: {order_ids}")
        return order_ids
    else:
        log_message(f"[ERROR] 신규 주문 조회 실패: {response.status_code} {response.text}")
        return []

def get_order_details(access_token, product_order_ids):
    """주문 ID 목록으로 상세 정보 조회 - 이미 조회된 데이터 활용"""
    # 이미 get_new_dispatch_waiting_order_ids에서 상세 정보를 조회했으므로
    # 별도 조회 없이 해당 정보를 반환하도록 수정
    # 하지만 기존 구조를 유지하기 위해 동일한 API 재호출
    if not product_order_ids:
        return []
        
    path = "/external/v1/pay-order/seller/product-orders/query"
    url = f"{NAVER_API_URL}{path}"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"productOrderIds": product_order_ids}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json().get('data', [])
    else:
        log_message(f"[ERROR] 주문 상세 정보 조회 실패: {response.status_code} {response.text}")
        return []
        
def dispatch_naver_order(access_token, product_order_id):
    """네이버 주문 발송 처리"""
    path = "/external/v1/pay-order/seller/product-orders/dispatch"
    url = f"{NAVER_API_URL}{path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 현재 시간을 발송일시로 설정 (ISO 8601 형식)
    from datetime import timezone, timedelta
    kst = timezone(timedelta(hours=9))
    dispatch_date = datetime.now(kst).strftime("%Y-%m-%dT%H:%M:%S.000+09:00")
    
    payload = {
        "dispatchProductOrders": [{
            "productOrderId": product_order_id,
            "deliveryMethod": "NOTHING",  # 배송없음
            "dispatchDate": dispatch_date,
            "etcDeliveryCompanyName": "쿠폰/콘텐츠 발송",
            "etcDeliveryNumber": "즉시발송완료"
        }]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        response_data = response.json()
        success_ids = response_data.get('data', {}).get('successProductOrderIds', [])
        fail_infos = response_data.get('data', {}).get('failProductOrderInfos', [])
        
        if product_order_id in success_ids:
            log_message(f"[SUCCESS] 네이버 발송 처리 완료: {product_order_id}")
            return True
        else:
            log_message(f"[ERROR] 발송 처리 실패: {fail_infos}")
            return False
    else:
        log_message(f"[ERROR] 네이버 발송 처리 실패: {product_order_id}, 응답: {response.text}")
        return False

# === 문자 발송 및 DB 처리 함수 ===

def make_sens_signature(method, uri, timestamp, access_key, secret_key):
    """SENS API의 서명을 생성하는 함수 (누락된 부분 추가)"""
    message = f"{method} {uri}\n{timestamp}\n{access_key}"
    signingKey = bytes(secret_key, 'UTF-8')
    message_bytes = bytes(message, 'UTF-8')
    sign = hmac.new(signingKey, message_bytes, digestmod=hashlib.sha256).digest()
    return base64.b64encode(sign).decode('UTF-8')

def send_sens_sms(receiver, message):
    """네이버 클라우드 SENS를 이용한 SMS 발송"""
    if not all([SENS_ACCESS_KEY, SENS_SECRET_KEY, SENS_SERVICE_ID, SENS_SENDER]):
        log_message("[ERROR] SENS API 정보가 설정되지 않았습니다.")
        return False

    # 이모지 및 특수문자 제거 (NCP SMS 제한사항)
    import re
    clean_message = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ.,!?\-\[\]():]+', '', message)

    method = "POST"
    uri = f"/sms/v2/services/{SENS_SERVICE_ID}/messages"
    url = f"https://sens.apigw.ntruss.com{uri}"
    timestamp = str(int(time.time() * 1000))
    
    # [오류 수정] 정의된 make_sens_signature 함수를 호출하도록 수정
    signature = make_sens_signature(method, uri, timestamp, SENS_ACCESS_KEY, SENS_SECRET_KEY)
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": SENS_ACCESS_KEY,
        "x-ncp-apigw-signature-v2": signature,
    }
    body = {
        "type": "LMS", # LMS로 변경하여 장문 메시지 지원
        "from": SENS_SENDER,
        "content": clean_message,
        "messages": [{"to": receiver}]
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    
    print(f"SMS 발송 요청 상세:")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Body: {body}")
    print(f"Response Status: {response.status_code}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 202:
        log_message(f"문자 발송 요청 성공: {receiver}")
        return True
    else:
        log_message(f"[ERROR] 문자 발송 요청 실패: {response.status_code} {response.text}")
        return False

def optimize_image_for_mms(image_path):
    """MMS 발송을 위해 이미지를 최적화하는 함수"""
    try:
        from PIL import Image
        import tempfile
        
        # 이미지 열기
        with Image.open(image_path) as img:
            # RGBA를 RGB로 변환 (투명도 제거)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 해상도 제한: 1500x1440 이하로 조정
            max_width, max_height = 1500, 1440
            width, height = img.size
            
            if width > max_width or height > max_height:
                # 비율 유지하면서 리사이즈
                ratio = min(max_width / width, max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"이미지 리사이즈: {width}x{height} → {new_width}x{new_height}")
            
            # 임시 파일로 저장 (파일명 단축)
            temp_dir = tempfile.gettempdir()
            temp_filename = f"mms_{int(time.time())}.jpg"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # 품질 최적화하여 저장
            img.save(temp_path, 'JPEG', quality=85, optimize=True)
            
            print(f"최적화된 이미지 저장: {temp_path}")
            print(f"파일명 길이: {len(temp_filename)} 문자")
            
            return temp_path
            
    except ImportError:
        print("[WARNING] PIL 모듈이 없어 이미지 최적화를 건너뜁니다.")
        return image_path
    except Exception as e:
        print(f"[ERROR] 이미지 최적화 실패: {str(e)}")
        return image_path

def send_sens_mms_with_image(receiver, message, image_path):
    """네이버 클라우드 SENS를 이용한 이미지 MMS 발송 (최적화 포함)"""
    if not all([SENS_ACCESS_KEY, SENS_SECRET_KEY, SENS_SERVICE_ID, SENS_SENDER]):
        log_message("[ERROR] SENS API 정보가 설정되지 않았습니다.")
        return False

    # 이미지 파일이 존재하는지 확인
    if not os.path.exists(image_path):
        log_message(f"[ERROR] 이미지 파일을 찾을 수 없습니다: {image_path}")
        return False

    # 이미지 최적화
    print(f"원본 이미지: {image_path}")
    optimized_image_path = optimize_image_for_mms(image_path)
    print(f"최적화된 이미지: {optimized_image_path}")

    # 이모지 및 특수문자 제거 (NCP SMS 제한사항)
    import re
    clean_message = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ.,!?\-\[\]():]+', '', message)

    method = "POST"
    uri = f"/sms/v2/services/{SENS_SERVICE_ID}/messages"
    url = f"https://sens.apigw.ntruss.com{uri}"
    timestamp = str(int(time.time() * 1000))
    
    signature = make_sens_signature(method, uri, timestamp, SENS_ACCESS_KEY, SENS_SECRET_KEY)
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": SENS_ACCESS_KEY,
        "x-ncp-apigw-signature-v2": signature,
    }
    
    # 이미지를 base64로 인코딩
    try:
        with open(optimized_image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # 짧은 파일명 사용
        short_filename = os.path.basename(optimized_image_path)
        if len(short_filename) > 40:
            # 파일명이 40자를 초과하면 단축
            name_part, ext = os.path.splitext(short_filename)
            short_filename = name_part[:36] + ext
        
        body = {
            "type": "MMS",  # MMS로 설정 (이미지 발송용)
            "from": SENS_SENDER,
            "content": clean_message,
            "messages": [{"to": receiver}],
            "files": [{
                "name": short_filename,
                "body": image_data
            }]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(body))
        
        print(f"MMS 이미지 발송 요청:")
        print(f"URL: {url}")
        print(f"이미지 파일: {optimized_image_path}")
        print(f"파일명: {short_filename} ({len(short_filename)}자)")
        print(f"메시지: {clean_message}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Text: {response.text}")
        
        # 임시 파일 정리
        if optimized_image_path != image_path and os.path.exists(optimized_image_path):
            try:
                os.remove(optimized_image_path)
                print(f"임시 파일 삭제: {optimized_image_path}")
            except:
                pass
        
        if response.status_code == 202:
            log_message(f"이미지 MMS 발송 요청 성공: {receiver}")
            return True
        else:
            log_message(f"[ERROR] 이미지 MMS 발송 요청 실패: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        log_message(f"[ERROR] 이미지 처리 중 오류: {str(e)}")
        return False

# === 주문 처리 및 SMS 발송 통합 함수 ===

def process_order_and_send_sms(order_detail):
    """단일 주문 처리: 등록된 상품만 처리하여 상품권 할당, 문자 발송, DB 업데이트"""
    product_order_id = order_detail.get("productOrder", {}).get("productOrderId")
    product_name = order_detail.get("productOrder", {}).get("productName", "")
    # 수량 정보는 productOrder에서 직접 가져오기
    quantity = order_detail.get("productOrder", {}).get("quantity", 1)
    
    # 배송지 정보 사용 (실제 수신자)
    shipping_address = order_detail.get("productOrder", {}).get("shippingAddress", {})
    receiver_name = shipping_address.get("name", "")
    receiver_tel = shipping_address.get("tel1", "")
    
    # 배송지 정보가 없으면 주문자 정보 사용 (fallback)
    if not receiver_name or not receiver_tel:
        receiver_name = order_detail.get("order", {}).get("ordererName", "")
        receiver_tel = order_detail.get("order", {}).get("ordererTel", "")
    
    if not all([product_order_id, receiver_tel, receiver_name]):
        log_message(f"[SKIP] 처리 불가: 필수 정보 부족. 주문 ID: {product_order_id}")
        return False

    log_message(f"주문 상품명: '{product_name}', 수량: {quantity}")
    log_message(f"수신자: {receiver_name}, 전화번호: {receiver_tel}")
    
    conn = None
    try:
        conn = sqlite3.connect('products.db')
        c = conn.cursor()

        # 1. 등록된 상품인지 확인
        c.execute("""
            SELECT p.id, p.product_name 
            FROM products p 
            WHERE p.product_name = ? AND p.is_active = 1
        """, (product_name,))
        product = c.fetchone()
        
        if not product:
            log_message(f"[SKIP] 등록되지 않은 상품 - 처리하지 않음: {product_name}")
            log_message(f"상품을 처리하려면 product_giftcard_manager.py에서 먼저 등록하세요.")
            return False
        
        product_id = product[0]
        log_message(f"[PROCESS] 등록된 상품 발견 - 처리 진행: {product_name} (ID: {product_id})")

        # 2. 이미 처리된 주문인지 확인
        c.execute("SELECT id FROM giftcards WHERE product_order_id = ?", (product_order_id,))
        existing_count = len(c.fetchall())
        if existing_count >= quantity:
            log_message(f"[SKIP] 이미 처리된 주문입니다: {product_order_id} (처리완료: {existing_count}개)")
            return True  # 이미 처리되었으므로 성공으로 간주
        elif existing_count > 0:
            log_message(f"[INFO] 부분 처리된 주문: {product_order_id} (처리완료: {existing_count}개, 남은수량: {quantity - existing_count}개)")
            quantity = quantity - existing_count  # 남은 수량만 처리

        # 3. 해당 상품의 사용 가능한 상품권을 수량만큼 조회 및 할당 (PIN과 이미지 모두 포함)
        c.execute("""
            SELECT id, pin_number, type, file_path, description 
            FROM giftcards 
            WHERE product_id = ? AND used = 0 AND product_order_id IS NULL 
            LIMIT ?
        """, (product_id, quantity))
        giftcards = c.fetchall()

        if len(giftcards) < quantity:
            log_message(f"[CRITICAL] '{product_name}' 상품의 사용 가능한 상품권이 부족합니다.")
            log_message(f"필요 수량: {quantity}개, 보유 수량: {len(giftcards)}개")
            log_message(f"product_giftcard_manager.py에서 해당 상품의 핀번호를 추가하세요.")
            return False

        phone_number = receiver_tel.replace("-", "")
        
        # 수량만큼 상품권 처리 (PIN 및 이미지 구분)
        pin_numbers = []
        image_items = []
        successful_updates = []
        
        for giftcard_data in giftcards:
            giftcard_id = giftcard_data[0]
            pin_number = giftcard_data[1]
            item_type = giftcard_data[2] if len(giftcard_data) > 2 else 'pin'
            file_path = giftcard_data[3] if len(giftcard_data) > 3 else None
            description = giftcard_data[4] if len(giftcard_data) > 4 else None
            
            if item_type == 'image':
                image_items.append({
                    'id': giftcard_id,
                    'file_path': file_path,
                    'description': description or pin_number
                })
            else:
                pin_numbers.append(pin_number)
            
            # DB에 사용 처리 및 주문 정보 기록
            c.execute("""
                UPDATE giftcards 
                SET used = 1, used_date = ?, customer_name = ?, phone_number = ?, product_order_id = ?
                WHERE id = ?
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), receiver_name, phone_number, product_order_id, giftcard_id))
            successful_updates.append(giftcard_id)

        # 발송 성공 여부
        sms_success = True
        
        # PIN 번호가 있는 경우 문자 발송
        if pin_numbers:
            if len(pin_numbers) == 1:
                message = f"[{os.getenv('STORE_NAME', '스토어')}] {receiver_name}님, 구매하신 상품권이 도착했습니다.\n핀번호: {pin_numbers[0]}"
            else:
                pin_list = "\n".join([f"{i+1}. {pin}" for i, pin in enumerate(pin_numbers)])
                message = f"[{os.getenv('STORE_NAME', '스토어')}] {receiver_name}님, 구매하신 상품권 {len(pin_numbers)}개가 도착했습니다.\n핀번호:\n{pin_list}"
            
            if not send_sens_sms(phone_number, message):
                sms_success = False
                log_message(f"[ERROR] PIN 문자 발송 실패: {product_order_id}")
        
        # 이미지가 있는 경우 MMS 발송
        if image_items:
            for idx, image_item in enumerate(image_items):
                if image_item['file_path']:
                    message = f"[{os.getenv('STORE_NAME', '스토어')}] {receiver_name}님, 구매하신 {image_item['description']}가 도착했습니다."
                    if not send_sens_mms_with_image(phone_number, message, image_item['file_path']):
                        sms_success = False
                        log_message(f"[ERROR] 이미지 MMS 발송 실패: {image_item['file_path']}")

        # 4. 최종 결과 처리
        if sms_success:
            # 5. DB 커밋 (모든 상품권 업데이트 확정)
            conn.commit()
            log_message(f"DB 업데이트 완료: {len(successful_updates)}개 상품권 처리, order_id={product_order_id}")
            if pin_numbers:
                log_message(f"발송된 핀번호: {', '.join(pin_numbers)}")
            if image_items:
                log_message(f"발송된 이미지: {len(image_items)}개")
            return True
        else:
            log_message(f"[ERROR] SMS/MMS 발송 실패 - 롤백 수행: {product_order_id}")
            conn.rollback()  # SMS 발송 실패 시 DB 변경사항 롤백
            return False
            
    except sqlite3.Error as e:
        log_message(f"[ERROR] DB 처리 중 오류 발생: {e}")
        return False
    finally:
        if conn:
            conn.close()


# === 메인 실행 로직 ===
def main():
    """자동화 전체 로직을 실행하는 메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SMS 발송 도구')
    parser.add_argument('--phone', help='메시지를 보낼 전화번호')
    parser.add_argument('--message', help='보낼 메시지 내용')
    parser.add_argument('--auto', action='store_true', help='자동 주문 처리 실행')
    
    args = parser.parse_args()
    
    # 전화번호와 메시지가 제공되었으면 직접 SMS 발송
    if args.phone and args.message:
        log_message("직접 SMS 발송 모드로 실행합니다.")
        success = send_sens_sms(args.phone, args.message)
        if success:
            log_message("SMS 발송 성공")
            sys.exit(0)
        else:
            log_message("SMS 발송 실패")
            sys.exit(1)
    
    # --auto 옵션이 있거나 다른 옵션이 없으면 자동 주문 처리 실행
    elif args.auto or not (args.phone or args.message):
        log_message("="*30)
        log_message("자동 주문 처리 시스템을 시작합니다.")
        
        # 1. 네이버 API 토큰 발급
        access_token = get_naver_access_token()
        if not access_token:
            log_message("시스템을 종료합니다: 토큰 발급 실패")
            return

        # 2. 신규 결제완료 주문 ID 목록 조회 (수정된 함수 호출)
        order_ids_to_process = get_new_dispatch_waiting_order_ids(access_token)
        if not order_ids_to_process:
            log_message("처리할 신규 주문이 없습니다.")
            log_message("시스템을 종료합니다.")
            return
            
        # 3. 주문 상세 정보 조회
        order_details = get_order_details(access_token, order_ids_to_process)

        # 4. 각 주문에 대해 순차적으로 처리
        for detail in order_details:
            product_order_id = detail.get('productOrder', {}).get('productOrderId')
            product_name = detail.get('productOrder', {}).get('productName', '')
            
            log_message(f"--- 주문 처리 시작: {product_order_id} ({product_name}) ---")
            
            # 4-1. 문자 발송 및 DB 업데이트
            sms_result = process_order_and_send_sms(detail)
            
            # 4-2. 등록된 상품 처리 성공 시 네이버 발송 처리
            if sms_result == True:  # 등록된 상품 처리 성공
                log_message(f"등록된 상품 처리 성공 - 발송처리 진행: {product_order_id}")
                dispatch_naver_order(access_token, product_order_id)
            else:  # 처리 실패 또는 미등록 상품
                log_message(f"처리 실패 또는 미등록 상품 - 발송처리 안함: {product_order_id}")
            
            log_message(f"--- 주문 처리 종료: {product_order_id} ---")

        log_message("자동 주문 처리 시스템이 작업을 완료했습니다.")
        log_message("="*30 + "\n")
    
    # 옵션이 잘못된 경우
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
