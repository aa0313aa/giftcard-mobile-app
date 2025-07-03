# 📱 안드로이드 백그라운드 서비스
# 상품권 자동 수집 및 관리 서비스

import os
import sys
import time
import sqlite3
import threading
import requests
from datetime import datetime, timedelta

# Android 서비스 관련
from jnius import autoclass, cast
from android.runnable import run_on_ui_thread
from plyer import notification
from plyer.platforms.android import activity

# 안드로이드 서비스 클래스
PythonService = autoclass('org.kivy.android.PythonService')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Intent = autoclass('android.content.Intent')
Context = autoclass('android.content.Context')

class GiftCardService:
    """상품권 관리 백그라운드 서비스"""
    
    def __init__(self):
        self.running = False
        self.db_path = "/storage/emulated/0/Android/data/com.giftcard.manager/files/giftcards.db"
        self.service_thread = None
        
    def start_service(self):
        """서비스 시작"""
        if not self.running:
            self.running = True
            self.service_thread = threading.Thread(target=self.run_service)
            self.service_thread.daemon = True
            self.service_thread.start()
            
            # 시작 알림
            self.send_notification("서비스 시작", "상품권 관리 서비스가 시작되었습니다.")
    
    def stop_service(self):
        """서비스 중지"""
        self.running = False
        if self.service_thread:
            self.service_thread.join()
            
        # 중지 알림
        self.send_notification("서비스 중지", "상품권 관리 서비스가 중지되었습니다.")
    
    def run_service(self):
        """서비스 메인 루프"""
        while self.running:
            try:
                # 30초마다 실행
                time.sleep(30)
                
                if not self.running:
                    break
                
                # 자동 수집 실행
                self.auto_collect_orders()
                
                # 자동 발송 실행
                self.auto_send_giftcards()
                
                # 상태 확인
                self.check_system_status()
                
            except Exception as e:
                print(f"서비스 오류: {e}")
                self.send_notification("서비스 오류", f"오류가 발생했습니다: {e}")
    
    def auto_collect_orders(self):
        """자동 주문 수집"""
        try:
            # 네이버 커머스 API 호출
            from dotenv import load_dotenv
            load_dotenv()
            
            naver_client_id = os.getenv('NAVER_CLIENT_ID')
            naver_client_secret = os.getenv('NAVER_CLIENT_SECRET')
            naver_access_token = os.getenv('NAVER_ACCESS_TOKEN')
            
            if not all([naver_client_id, naver_client_secret, naver_access_token]):
                return
            
            # API 호출 로직
            headers = {
                'X-Naver-Client-Id': naver_client_id,
                'X-Naver-Client-Secret': naver_client_secret,
                'Authorization': f'Bearer {naver_access_token}'
            }
            
            # 주문 조회 API 호출
            response = requests.get(
                'https://commerce.naver.com/api/v1/orders',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                orders = response.json()
                new_orders = self.process_new_orders(orders)
                
                if new_orders > 0:
                    self.send_notification("새 주문", f"{new_orders}개의 새 주문이 접수되었습니다.")
                    
        except Exception as e:
            print(f"자동 수집 오류: {e}")
    
    def process_new_orders(self, orders_data):
        """새 주문 처리"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            new_count = 0
            
            for order in orders_data.get('orders', []):
                order_id = order.get('orderId')
                
                # 기존 주문 확인
                cursor.execute("SELECT id FROM orders WHERE order_id = ?", (order_id,))
                if cursor.fetchone():
                    continue
                
                # 새 주문 추가
                cursor.execute('''
                    INSERT INTO orders (order_id, customer_name, customer_phone, product_name, quantity, total_amount, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_id,
                    order.get('customerName', ''),
                    order.get('customerPhone', ''),
                    order.get('productName', ''),
                    order.get('quantity', 1),
                    order.get('totalAmount', 0),
                    'pending'
                ))
                
                new_count += 1
            
            conn.commit()
            conn.close()
            
            return new_count
            
        except Exception as e:
            print(f"주문 처리 오류: {e}")
            return 0
    
    def auto_send_giftcards(self):
        """자동 상품권 발송"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 대기 중인 주문 조회
            cursor.execute("SELECT * FROM orders WHERE status = 'pending' LIMIT 10")
            pending_orders = cursor.fetchall()
            
            sent_count = 0
            
            for order in pending_orders:
                order_id = order[1]
                customer_phone = order[3]
                product_name = order[4]
                quantity = order[5]
                
                # 사용 가능한 상품권 조회
                cursor.execute('''
                    SELECT * FROM giftcards 
                    WHERE product_name = ? AND status = 'available' 
                    LIMIT ?
                ''', (product_name, quantity))
                
                available_cards = cursor.fetchall()
                
                if len(available_cards) >= quantity:
                    # 상품권 발송
                    if self.send_sms_with_giftcards(customer_phone, available_cards):
                        # 상품권 상태 업데이트
                        for card in available_cards:
                            cursor.execute('''
                                UPDATE giftcards 
                                SET status = 'sent', used_at = ?, order_id = ?
                                WHERE id = ?
                            ''', (datetime.now(), order_id, card[0]))
                        
                        # 주문 상태 업데이트
                        cursor.execute('''
                            UPDATE orders 
                            SET status = 'sent', sent_at = ?
                            WHERE id = ?
                        ''', (datetime.now(), order[0]))
                        
                        sent_count += 1
            
            conn.commit()
            conn.close()
            
            if sent_count > 0:
                self.send_notification("자동 발송", f"{sent_count}개 주문이 자동 발송되었습니다.")
                
        except Exception as e:
            print(f"자동 발송 오류: {e}")
    
    def send_sms_with_giftcards(self, phone_number, giftcards):
        """상품권 SMS 발송"""
        try:
            from send_sms_new_version import send_sms
            
            # 상품권 정보 구성
            message = "🎁 상품권이 도착했습니다!\n\n"
            
            for card in giftcards:
                message += f"상품명: {card[1]}\n"
                message += f"PIN: {card[2]}\n"
                message += f"금액: {card[3]:,}원\n\n"
            
            message += "감사합니다! 😊"
            
            # SMS 발송
            return send_sms(phone_number, message)
            
        except Exception as e:
            print(f"SMS 발송 오류: {e}")
            return False
    
    def check_system_status(self):
        """시스템 상태 확인"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 사용 가능한 상품권 수 확인
            cursor.execute("SELECT COUNT(*) FROM giftcards WHERE status = 'available'")
            available_count = cursor.fetchone()[0]
            
            # 대기 중인 주문 수 확인
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
            pending_count = cursor.fetchone()[0]
            
            conn.close()
            
            # 재고 부족 경고
            if available_count < 10:
                self.send_notification("재고 부족", f"사용 가능한 상품권이 {available_count}개 남았습니다.")
            
            # 대기 주문 많음 경고
            if pending_count > 20:
                self.send_notification("주문 대기", f"처리 대기 중인 주문이 {pending_count}개 있습니다.")
                
        except Exception as e:
            print(f"상태 확인 오류: {e}")
    
    def send_notification(self, title, message):
        """알림 발송"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="상품권 관리",
                app_icon=None,
                timeout=10,
                toast=True
            )
        except Exception as e:
            print(f"알림 오류: {e}")

# 서비스 인스턴스
service = GiftCardService()

def start_service():
    """서비스 시작 함수"""
    service.start_service()

def stop_service():
    """서비스 중지 함수"""
    service.stop_service()

# 메인 실행
if __name__ == "__main__":
    print("📱 상품권 관리 서비스 시작")
    start_service()
    
    try:
        # 서비스 유지
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("📱 상품권 관리 서비스 중지")
        stop_service()
