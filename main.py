import os
import requests
from bs4 import BeautifulSoup
import easyocr
from datetime import datetime
import pytz

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    if len(message) > 4000:
        message = message[:3900] + "\n\n[ادامه پیام...]"
    requests.post(url, json=payload)

def main():
    print("شروع بررسی پست‌های امروز کانال EPGnews...")
    url = "https://t.me/s/EPGnews"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("خطا در اتصال به کانال")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message')
    
    if not messages:
        print("پستی یافت نشد.")
        return
    
    # تعیین تاریخ امروز به وقت تهران
    tehran_tz = pytz.timezone('Asia/Tehran')
    today_date = datetime.now(tehran_tz).strftime('%Y-%m-%d')
    print(f"تاریخ امروز (تهران): {today_date}")
    
    todays_reports = []
    reader = None # تنبلی در بارگذاری لایبرری تا زمانی که نیاز باشد
    
    for msg in messages:
        time_tag = msg.find('time', class_='tgme_widget_message_date')
        if time_tag and time_tag.has_attr('datetime'):
            dt_str = time_tag['datetime'] # فرمت: 2026-11-17T...
            
            # بررسی اینکه آیا پست متعلق به امروز است
            if today_date in dt_str:
                # ۱. بررسی اگر پست متن دارد
                text_div = msg.find('div', class_='tgme_widget_message_text')
                msg_text = text_div.get_text(separator='\n') if text_div else ""
                
                # ۲. بررسی اگر پست عکس دارد
                photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
                img_text = ""
                if photo_wrap:
                    style_attr = photo_wrap.get('style', '')
                    if 'background-image:' in style_attr:
                        start = style_attr.find('url(\'') + 6
                        end = style_attr.find('\')', start)
                        img_url = style_attr[start:end]
                        if img_url:
                            if img_url.startswith('ttp://') or img_url.startswith('ttps://'):
                                img_url = 'h' + img_url
                            elif img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            
                            try:
                                print("دانلود و پردازش تصویر با OCR...")
                                img_data = requests.get(img_url).content
                                with open('temp_img.jpg', 'wb') as handler:
                                    handler.write(img_data)
                                    
                                if reader is None:
                                    reader = easyocr.Reader(['fa', 'en'], gpu=False)
                                results = reader.readtext('temp_img.jpg', detail=0)
                                img_text = "\n".join(results)
                                
                                if os.path.exists('temp_img.jpg'):
                                    os.remove('temp_img.jpg')
                            except Exception as e:
                                print(f"خطا در پردازش عکس: {e}")
                
                # ترکیب متن پست و متن استخراج شده از عکس
                combined_content = []
                if msg_text.strip():
                    combined_content.append(msg_text)
                if img_text.strip():
                    combined_content.append(img_text)
                    
                if combined_content:
                    todays_reports.append("\n".join(combined_content))

    if not todays_reports:
        print("هیچ پست یا برنامه‌ای برای امروز یافت نشد.")
        send_telegram_message("🎬 ربات بررسی کرد، اما امروز تا این لحظه پست جدیدی در کانال EPGnews یافت نشد.")
        return

    print(f"تعداد {len(todays_reports)} پست برای امروز پیدا شد. در حال ارسال...")
    final_msg = "🎬 *گزارش برنامه‌های امروز کانال EPGnews:*\n\n\n" + "\n\n---\n\n".join(todays_reports)
    send_telegram_message(final_msg)
    print("گزارش با موفقیت ارسال شد.")

if __name__ == "__main__":
    main()
