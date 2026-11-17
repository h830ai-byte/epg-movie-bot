import os
import requests
from bs4 import BeautifulSoup
import easyocr

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("خطا: توکن تلگرام یا چت آیدی تنظیم نشده است.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, json=payload)
    print("پاسخ تلگرام:", response.text)

def main():
    print("شروع اجرای ربات EPG...")
    url = "https://t.me/s/EPGnews"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("خطا در دسترسی به کانال تلگرام")
        send_telegram_message("⚠️ ربات اجرا شد اما در اتصال به کانال EPGnews خطا رخ داد.")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    images = soup.find_all('a', class_='tgme_widget_message_photo_wrap')
    
    if not images:
        print("هیچ عکسی در پست‌های اخیر یافت نشد.")
        send_telegram_message("🎬 ربات اجرا شد، اما عکسی در آخرین پست‌های کانال EPGnews یافت نشد.")
        return
    
    latest_img = images[-1]
    style_attr = latest_img.get('style', '')
    
    img_url = None
    if 'background-image:' in style_attr:
        start = style_attr.find('url(\'') + 6
        end = style_attr.find('\')', start)
        img_url = style_attr[start:end]
        
    if not img_url:
        print("لینک عکس در استایل پیدا نشد.")
        send_telegram_message("🎬 ربات اجرا شد اما لینک عکس استخراج نشد.")
        return
    
    # اصلاح خودکار در صورتی که حرف h اول لینک افتاده باشد
    if img_url.startswith('ttp://') or img_url.startswith('ttps://'):
        img_url = 'h' + img_url
    elif img_url.startswith('//'):
        img_url = 'https:' + img_url
        
    print(f"لینک اصلاح‌شده‌ی عکس: {img_url}")
    
    # دانلود و پردازش عکس با OCR
    print("در حال دانلود تصویر...")
    img_data = requests.get(img_url).content
    with open('temp_banner.jpg', 'wb') as handler:
        handler.write(img_data)
        
    print("در حال پردازش متن تصویر با EasyOCR...")
    reader = easyocr.Reader(['fa', 'en'], gpu=False)
    results = reader.readtext('temp_banner.jpg', detail=0)
    
    full_text = "\n".join(results)
    print("متن استخراج شده:\n", full_text)
    
    if full_text.strip():
        msg = f"🎬 *آخرین جدول پخش کانال EPGnews:*\n\n{full_text[:3500]}"
        send_telegram_message(msg)
    else:
        send_telegram_message("🎬 ربات عکس را پیدا کرد اما متنی داخل آن تشخیص داده نشد.")

if __name__ == "__main__":
    main()
    
