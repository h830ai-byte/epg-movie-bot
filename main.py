import os
import requests
from bs4 import BeautifulSoup
import easyocr
from datetime import datetime
import pytz

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
SENT_FILE = 'sent_images.txt'

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

def load_sent_images():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_sent_image(img_url):
    with open(SENT_FILE, 'a', encoding='utf-8') as f:
        f.write(img_url + '\n')

def main():
    print("بررسی کانال EPGnews بر اساس تاریخ امروز...")
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
    
    # گرفتن تاریخ امروز به وقت ایران (تهران)
    tehran_tz = pytz.timezone('Asia/Tehran')
    today_date = datetime.now(tehran_tz).strftime('%Y-%m-%d')
    print(f"تاریخ امروز (به وقت ایران): {today_date}")
    
    sent_images = load_sent_images()
    todays_new_images = []
    
    for msg in messages:
        time_tag = msg.find('time', class_='tgme_widget_message_date')
        if time_tag and time_tag.has_attr('datetime'):
            dt_str = time_tag['datetime'] # فرمت مثل: 2026-11-17T10:00:00+00:00
            
            # بررسی اینکه آیا پست مربوط به امروز است
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
                            
                            # اگر این عکس قبلاً فرستاده نشده باشد، آن را اضافه می‌کنیم
                            if img_url not in sent_images:
                                todays_new_images.append(img_url)

    if not todays_new_images:
        print("هیچ عکس جدیدی برای امروز که قبلا ارسال نشده باشد یافت نشد.")
        return

    print(f"تعداد {len(todays_new_images)} عکس جدید متعلق به امروز پیدا شد.")
    
    reader = easyocr.Reader(['fa', 'en'], gpu=False)
    
    for index, img_url in enumerate(todays_new_images):
        print(f"در حال پردازش عکس جدید شماره {index + 1}...")
        try:
            img_data = requests.get(img_url).content
            temp_filename = f'temp_{index}.jpg'
            with open(temp_filename, 'wb') as handler:
                handler.write(img_data)
                
            results = reader.readtext(temp_filename, detail=0)
            full_text = "\n".join(results)
            
            if full_text.strip():
                msg = f"🎬 *برنامه پخش جدید (کانال EPGnews):*\n\n{full_text}"
                send_telegram_message(msg)
                # بلافاصله لینک را ذخیره می‌کنیم تا تکراری فرستاده نشود
                save_sent_image(img_url)
                
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
        except Exception as e:
            print(f"خطا در پردازش عکس: {e}")

if __name__ == "__main__":
    main()
    
