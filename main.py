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
    print("بررسی کانال EPGnews برای پست‌های امروز...")
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
    
    # گرفتن تاریخ امروز به وقت ایران
    Tehran_tz = pytz.timezone('Asia/Tehran')
    today_date = datetime.now(Tehran_tz).strftime('%Y-%m-%d')
    
    todays_images = []
    
    for msg in messages:
        # پیدا کردن تاریخ پست
        time_tag = msg.find('time', class_='tgme_widget_message_date')
        if time_tag and time_tag.has_attr('datetime'):
            dt_str = time_tag['datetime'] # مثل: 2026-11-17T10:00:00+00:00
            # چک کردن اینکه آیا پست متعلق به امروز است
            if today_date in dt_str:
                photo_wrap = msg.find('a', class_='tgme_widget_message_photo_wrap')
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
                            todays_images.append(img_url)

    if not todays_images:
        print("هیچ عکس جدیدی برای امروز یافت نشد.")
        return

    print(f"تعداد {len(todays_images)} عکس متعلق به امروز پیدا شد.")
    
    reader = easyocr.Reader(['fa', 'en'], gpu=False)
    all_reports = []
    
    for index, img_url in enumerate(todays_images):
        print(f"در حال پردازش عکس شماره {index + 1}...")
        try:
            img_data = requests.get(img_url).content
            temp_filename = f'temp_{index}.jpg'
            with open(temp_filename, 'wb') as handler:
                handler.write(img_data)
                
            results = reader.readtext(temp_filename, detail=0)
            full_text = "\n".join(results)
            
            if full_text.strip():
                all_reports.append(f"📌 *برنامه پخش جدید (کانال EPGnews):*\n{full_text}")
                
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
        except Exception as e:
            print(f"خطا در پردازش عکس: {e}")
            
    if all_reports:
        # ارسال گزارش برنامه‌های امروز
        final_msg = "\n\n---\n\n".join(all_reports)
        send_telegram_message(final_msg)

if __name__ == "__main__":
    main()
    
