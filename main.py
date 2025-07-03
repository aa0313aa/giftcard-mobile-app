# 📱 상품권 관리 시스템 - 안드로이드 앱
# Kivy 기반 모바일 앱

import os
import sys
import json
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

# Kivy 라이브러리
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

# KivyMD for Material Design
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.toolbar import MDToolbar
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar

# 기존 모듈 임포트
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# HTTP 서버 기능
from flask import Flask, request, jsonify
import requests
from apscheduler.schedulers.background import BackgroundScheduler

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_path="giftcards.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 상품권 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giftcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                pin_number TEXT NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP,
                order_id TEXT
            )
        ''')
        
        # 주문 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                customer_name TEXT,
                customer_phone TEXT,
                product_name TEXT,
                quantity INTEGER,
                total_amount INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_giftcards(self, status=None):
        """상품권 목록 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM giftcards WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM giftcards ORDER BY created_at DESC")
        
        cards = cursor.fetchall()
        conn.close()
        return cards
    
    def add_giftcard(self, product_name, pin_number, amount):
        """상품권 추가"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO giftcards (product_name, pin_number, amount)
            VALUES (?, ?, ?)
        ''', (product_name, pin_number, amount))
        
        conn.commit()
        conn.close()
    
    def get_orders(self, status=None):
        """주문 목록 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
        
        orders = cursor.fetchall()
        conn.close()
        return orders

class MainScreen(MDScreen):
    """메인 화면"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.build_ui()
    
    def build_ui(self):
        """UI 구성"""
        main_layout = MDBoxLayout(orientation="vertical", spacing=10, padding=20)
        
        # 상단 툴바
        toolbar = MDToolbar(title="📱 상품권 관리 시스템")
        toolbar.md_bg_color = (0.2, 0.6, 1, 1)
        main_layout.add_widget(toolbar)
        
        # 통계 카드들
        stats_layout = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=120)
        
        # 총 상품권 수
        total_cards = len(self.db.get_giftcards())
        stats_card1 = self.create_stats_card("총 상품권", str(total_cards), "💳")
        stats_layout.add_widget(stats_card1)
        
        # 사용 가능한 상품권
        available_cards = len(self.db.get_giftcards("available"))
        stats_card2 = self.create_stats_card("사용 가능", str(available_cards), "✅")
        stats_layout.add_widget(stats_card2)
        
        # 대기 중인 주문
        pending_orders = len(self.db.get_orders("pending"))
        stats_card3 = self.create_stats_card("대기 주문", str(pending_orders), "⏳")
        stats_layout.add_widget(stats_card3)
        
        main_layout.add_widget(stats_layout)
        
        # 기능 버튼들
        button_layout = MDBoxLayout(orientation="vertical", spacing=10)
        
        # 상품권 관리 버튼
        manage_btn = MDRaisedButton(
            text="📋 상품권 관리",
            size_hint_y=None,
            height=60,
            md_bg_color=(0.3, 0.7, 0.3, 1)
        )
        manage_btn.bind(on_release=self.open_giftcard_manager)
        button_layout.add_widget(manage_btn)
        
        # 주문 관리 버튼
        order_btn = MDRaisedButton(
            text="📦 주문 관리",
            size_hint_y=None,
            height=60,
            md_bg_color=(0.7, 0.3, 0.3, 1)
        )
        order_btn.bind(on_release=self.open_order_manager)
        button_layout.add_widget(order_btn)
        
        # 자동 수집 버튼
        auto_btn = MDRaisedButton(
            text="🔄 자동 수집 시작",
            size_hint_y=None,
            height=60,
            md_bg_color=(0.3, 0.3, 0.7, 1)
        )
        auto_btn.bind(on_release=self.start_auto_collection)
        button_layout.add_widget(auto_btn)
        
        # 서버 상태 버튼
        server_btn = MDRaisedButton(
            text="🖥️ 서버 상태",
            size_hint_y=None,
            height=60,
            md_bg_color=(0.7, 0.7, 0.3, 1)
        )
        server_btn.bind(on_release=self.show_server_status)
        button_layout.add_widget(server_btn)
        
        main_layout.add_widget(button_layout)
        
        self.add_widget(main_layout)
    
    def create_stats_card(self, title, value, icon):
        """통계 카드 생성"""
        card = MDCard(
            orientation="vertical",
            padding=10,
            spacing=5,
            elevation=3,
            md_bg_color=(1, 1, 1, 1)
        )
        
        layout = MDBoxLayout(orientation="vertical", spacing=5)
        
        # 아이콘과 값
        icon_label = MDLabel(text=f"{icon} {value}", font_style="H4", halign="center")
        layout.add_widget(icon_label)
        
        # 제목
        title_label = MDLabel(text=title, font_style="Caption", halign="center")
        layout.add_widget(title_label)
        
        card.add_widget(layout)
        return card
    
    def open_giftcard_manager(self, instance):
        """상품권 관리 화면 열기"""
        self.manager.current = "giftcard_screen"
    
    def open_order_manager(self, instance):
        """주문 관리 화면 열기"""
        self.manager.current = "order_screen"
    
    def start_auto_collection(self, instance):
        """자동 수집 시작"""
        self.show_snackbar("🔄 자동 수집이 시작되었습니다!")
        # 여기에 자동 수집 로직 추가
    
    def show_server_status(self, instance):
        """서버 상태 표시"""
        self.show_snackbar("🖥️ 서버가 정상 동작 중입니다!")
    
    def show_snackbar(self, message):
        """스낵바 표시"""
        snackbar = Snackbar(text=message)
        snackbar.open()

class GiftCardScreen(MDScreen):
    """상품권 관리 화면"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.build_ui()
    
    def build_ui(self):
        """UI 구성"""
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=20)
        
        # 툴바
        toolbar = MDToolbar(title="📋 상품권 관리")
        toolbar.md_bg_color = (0.3, 0.7, 0.3, 1)
        toolbar.left_action_items = [["arrow-left", lambda x: self.go_back()]]
        layout.add_widget(toolbar)
        
        # 상품권 추가 섹션
        add_layout = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None, height=200)
        
        add_title = MDLabel(text="새 상품권 추가", font_style="H6")
        add_layout.add_widget(add_title)
        
        self.product_input = MDTextField(hint_text="상품명", size_hint_y=None, height=40)
        add_layout.add_widget(self.product_input)
        
        self.pin_input = MDTextField(hint_text="PIN 번호", size_hint_y=None, height=40)
        add_layout.add_widget(self.pin_input)
        
        self.amount_input = MDTextField(hint_text="금액", size_hint_y=None, height=40)
        add_layout.add_widget(self.amount_input)
        
        add_btn = MDRaisedButton(
            text="➕ 상품권 추가",
            size_hint_y=None,
            height=40,
            md_bg_color=(0.2, 0.6, 0.2, 1)
        )
        add_btn.bind(on_release=self.add_giftcard)
        add_layout.add_widget(add_btn)
        
        layout.add_widget(add_layout)
        
        # 상품권 목록
        list_title = MDLabel(text="상품권 목록", font_style="H6")
        layout.add_widget(list_title)
        
        self.giftcard_list = MDList()
        scroll = ScrollView()
        scroll.add_widget(self.giftcard_list)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
        self.refresh_giftcard_list()
    
    def add_giftcard(self, instance):
        """상품권 추가"""
        product_name = self.product_input.text.strip()
        pin_number = self.pin_input.text.strip()
        amount = self.amount_input.text.strip()
        
        if not all([product_name, pin_number, amount]):
            self.show_snackbar("모든 필드를 입력해주세요!")
            return
        
        try:
            amount = int(amount)
            self.db.add_giftcard(product_name, pin_number, amount)
            self.show_snackbar("✅ 상품권이 추가되었습니다!")
            
            # 입력 필드 초기화
            self.product_input.text = ""
            self.pin_input.text = ""
            self.amount_input.text = ""
            
            self.refresh_giftcard_list()
            
        except ValueError:
            self.show_snackbar("올바른 금액을 입력해주세요!")
    
    def refresh_giftcard_list(self):
        """상품권 목록 새로고침"""
        self.giftcard_list.clear_widgets()
        
        cards = self.db.get_giftcards()
        for card in cards:
            item_text = f"🎁 {card[1]} - {card[2]} ({card[3]:,}원) [{card[4]}]"
            item = OneLineListItem(text=item_text)
            self.giftcard_list.add_widget(item)
    
    def go_back(self):
        """뒤로가기"""
        self.manager.current = "main_screen"
    
    def show_snackbar(self, message):
        """스낵바 표시"""
        snackbar = Snackbar(text=message)
        snackbar.open()

class OrderScreen(MDScreen):
    """주문 관리 화면"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.build_ui()
    
    def build_ui(self):
        """UI 구성"""
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=20)
        
        # 툴바
        toolbar = MDToolbar(title="📦 주문 관리")
        toolbar.md_bg_color = (0.7, 0.3, 0.3, 1)
        toolbar.left_action_items = [["arrow-left", lambda x: self.go_back()]]
        layout.add_widget(toolbar)
        
        # 주문 목록
        list_title = MDLabel(text="주문 목록", font_style="H6")
        layout.add_widget(list_title)
        
        self.order_list = MDList()
        scroll = ScrollView()
        scroll.add_widget(self.order_list)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
        self.refresh_order_list()
    
    def refresh_order_list(self):
        """주문 목록 새로고침"""
        self.order_list.clear_widgets()
        
        orders = self.db.get_orders()
        for order in orders:
            item_text = f"📋 {order[1]} - {order[3]} ({order[6]:,}원) [{order[7]}]"
            item = OneLineListItem(text=item_text)
            self.order_list.add_widget(item)
    
    def go_back(self):
        """뒤로가기"""
        self.manager.current = "main_screen"

class GiftCardApp(MDApp):
    """메인 앱 클래스"""
    
    def build(self):
        """앱 빌드"""
        self.title = "📱 상품권 관리 시스템"
        self.theme_cls.primary_palette = "Blue"
        
        # 화면 매니저
        sm = MDScreenManager()
        
        # 화면들 추가
        sm.add_widget(MainScreen(name="main_screen"))
        sm.add_widget(GiftCardScreen(name="giftcard_screen"))
        sm.add_widget(OrderScreen(name="order_screen"))
        
        return sm
    
    def on_start(self):
        """앱 시작 시 실행"""
        print("🚀 상품권 관리 앱이 시작되었습니다!")
        
        # 백그라운드 작업 시작
        self.start_background_services()
    
    def start_background_services(self):
        """백그라운드 서비스 시작"""
        # 여기에 자동 수집, 알림 등의 백그라운드 작업 추가
        pass

if __name__ == "__main__":
    # 앱 실행
    GiftCardApp().run()
