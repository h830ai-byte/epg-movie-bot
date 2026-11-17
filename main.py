import os
import requests
from bs4 import BeautifulSoup
import easyocr

# تنظیمات تلگرام (از تنظیمات امنیتی گیت‌هاب خوانده می‌شود)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_latest_channel_image():
    url = "https://t.me/s/EPGnews"
    response = requests.get(url)
    if response.status_code != 200:
        print("خطا در دسترسی به صفحه کانال")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_photo')
    if not posts:
        return None
    
    latest_post = posts[-1]
    style_attr = latest_post.get('style', '')
    if 'background-image:' in style_attr:
        start = style_attr.find('url(\'') + 6
        end = style_attr.find('\')', start)
        img_url = style_attr[start:end]
        return img_url
    return None

def extract_text_from_image(img_url):
    print("در حال دانلود و پردازش تصویر با هوش مصنوعی... لطفاً صبور باشید.")
    img_data = requests.get(img_url).content
    with open('temp_banner.jpg', 'wb') as handler:
        handler.write(img_data)
    
    # راه‌اندازی EasyOCR برای خواندن زبان فارسی و انگلیسی
    reader = easyocr.Reader(['fa', 'en'], gpu=False)
    results = reader.readtext('temp_banner.jpg', detail=0)
    
    return results

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        print("توکن تلگرام یا چت آیدی تنظیم نشده است.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    img_url = get_latest_channel_image()
    if img_url:
        texts = extract_text_from_image(img_url)
        print("متن استخراج شده از عکس:", texts)
        
        # ساخت پیام و ارسال به تلگرام شما
        result_text = "🎬 *برنامه سینمایی کانال EPGnews استخراج شد:*\n\n" + "\n".join(texts[:20])
        send_telegram_message(result_text)
    else:
        print("عکسی در آخرین پست کانال یافت نشد.")
      
