# 📱 간단한 앱 아이콘 생성 스크립트

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    """앱 아이콘 생성 (512x512)"""
    # 아이콘 크기
    size = 512
    
    # 배경 생성 (그라디언트 효과)
    img = Image.new('RGB', (size, size), '#2196F3')
    draw = ImageDraw.Draw(img)
    
    # 그라디언트 배경
    for i in range(size):
        color = int(255 * (i / size))
        draw.line([(0, i), (size, i)], fill=(33, 150, 243, color))
    
    # 원형 배경
    draw.ellipse([50, 50, size-50, size-50], fill='#1976D2', outline='#0D47A1', width=10)
    
    # 상품권 아이콘 그리기
    # 카드 모양
    card_x, card_y = 150, 200
    card_w, card_h = 212, 130
    
    # 카드 배경
    draw.rounded_rectangle([card_x, card_y, card_x+card_w, card_y+card_h], 
                          radius=20, fill='#FFFFFF', outline='#E0E0E0', width=3)
    
    # 카드 상단 줄무늬
    draw.rectangle([card_x+20, card_y+20, card_x+card_w-20, card_y+40], fill='#FFC107')
    
    # 카드 번호 (점선)
    for i in range(4):
        x = card_x + 30 + i * 40
        draw.rectangle([x, card_y+60, x+25, card_y+70], fill='#BDBDBD')
    
    # 로고 텍스트
    try:
        # 큰 폰트로 이모지
        font_size = 60
        # 시스템 폰트 사용
        font = ImageFont.load_default()
        
        # 상품권 이모지
        draw.text((size//2-30, 120), "🎁", fill='#FFFFFF', font=font)
        
        # 앱 이름
        draw.text((size//2-80, 370), "상품권", fill='#FFFFFF', font=font)
        draw.text((size//2-60, 420), "관리", fill='#FFFFFF', font=font)
        
    except:
        # 폰트 로드 실패 시 기본 텍스트
        draw.text((size//2-50, 120), "GIFT", fill='#FFFFFF')
        draw.text((size//2-50, 370), "CARD", fill='#FFFFFF')
        draw.text((size//2-50, 420), "MANAGER", fill='#FFFFFF')
    
    # 저장
    img.save('icon.png', 'PNG', quality=100)
    print("✅ 앱 아이콘 생성 완료: icon.png")

def create_splash_screen():
    """스플래시 스크린 생성 (1920x1080)"""
    # 스플래시 크기
    width, height = 1920, 1080
    
    # 배경 생성
    img = Image.new('RGB', (width, height), '#2196F3')
    draw = ImageDraw.Draw(img)
    
    # 그라디언트 배경
    for i in range(height):
        color_ratio = i / height
        r = int(33 + (63 * color_ratio))
        g = int(150 + (105 * color_ratio))
        b = int(243 + (12 * color_ratio))
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    # 중앙 원형 배경
    center_x, center_y = width // 2, height // 2
    radius = 200
    
    draw.ellipse([center_x-radius, center_y-radius, center_x+radius, center_y+radius], 
                 fill='#1976D2', outline='#0D47A1', width=8)
    
    # 상품권 아이콘 (큰 버전)
    card_x, card_y = center_x - 150, center_y - 80
    card_w, card_h = 300, 160
    
    # 카드 배경
    draw.rounded_rectangle([card_x, card_y, card_x+card_w, card_y+card_h], 
                          radius=25, fill='#FFFFFF', outline='#E0E0E0', width=4)
    
    # 카드 상단 줄무늬
    draw.rectangle([card_x+30, card_y+25, card_x+card_w-30, card_y+50], fill='#FFC107')
    
    # 카드 번호 (점선)
    for i in range(4):
        x = card_x + 40 + i * 55
        draw.rectangle([x, card_y+80, x+40, card_y+95], fill='#BDBDBD')
    
    # 앱 제목
    try:
        font = ImageFont.load_default()
        
        # 메인 제목
        title_y = center_y + 250
        draw.text((center_x-200, title_y), "상품권 관리 시스템", fill='#FFFFFF', font=font)
        
        # 부제목
        draw.text((center_x-150, title_y+50), "Mobile Server Edition", fill='#E3F2FD', font=font)
        
        # 버전 정보
        draw.text((center_x-50, title_y+100), "v1.0.0", fill='#BBDEFB', font=font)
        
    except:
        # 폰트 로드 실패 시 기본 텍스트
        draw.text((center_x-150, center_y+250), "GIFTCARD MANAGER", fill='#FFFFFF')
        draw.text((center_x-100, center_y+300), "MOBILE SERVER", fill='#E3F2FD')
    
    # 저장
    img.save('presplash.png', 'PNG', quality=100)
    print("✅ 스플래시 스크린 생성 완료: presplash.png")

def create_multiple_icon_sizes():
    """다양한 크기의 아이콘 생성"""
    sizes = [36, 48, 72, 96, 144, 192, 512]
    
    # 기본 아이콘 로드
    if os.path.exists('icon.png'):
        base_icon = Image.open('icon.png')
        
        for size in sizes:
            resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(f'icon-{size}.png', 'PNG', quality=100)
            print(f"✅ 아이콘 생성: icon-{size}.png")

if __name__ == "__main__":
    print("🎨 앱 아이콘 및 스플래시 스크린 생성 중...")
    
    create_app_icon()
    create_splash_screen()
    create_multiple_icon_sizes()
    
    print("\n🎉 모든 이미지 생성 완료!")
    print("📁 생성된 파일:")
    print("   - icon.png (512x512)")
    print("   - presplash.png (1920x1080)")
    print("   - icon-36.png ~ icon-512.png (다양한 크기)")
