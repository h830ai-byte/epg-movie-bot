import os
import requests
from bs4 import BeautifulSoup
import easyocr

# تنظیمات تلگرام
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_recent_channel_images():
    url = "https://t.me/s/EPGnews"
    response = requests.get(url)
    if response.status_code != 200:
        print("خطا در دسترسی به صفحه کانال")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all('div', class_='tgme_widget_message_photo')
    
    img_urls = []
    # گرفتن 5 پست آخر برای اطمینان از پوشش کامل عکس‌های شب گذشته تا امروز
    for post in posts[-5:]:
        style_attr = post.get('style', '')
        if 'background-image:' in style_attr:
            start = style_attr.find('url(\'') + 6
            end = style_attr.find('\')', start)
            img_url = style_attr[start:end]
            img_urls.append(img_url)
            
    return img_urls

def extract_movies_from_images(img_urls):
    reader = easyocr.Reader(['fa', 'en'], gpu=False)
    all_movies_text = []
    
    for index, img_url in enumerate(img_urls):
        print(f"در حال پردازش تصویر شماره {index + 1}...")
        img_data = requests.get(img_url).content
        temp_filename = f'temp_banner_{index}.jpg'
        
        with open(temp_filename, 'wb') as handler:
            handler.write(img_data)
            
        results = reader.readtext(temp_filename, detail=0)
        
        # فیلتر هوشمند: جستجوی کلمات کلیدی مرتبط با فیلم سینمایی یا شبکه‌ها
        filtered_lines = []
        for text in results:
            # اگر خط شامل کلمات فیلم، سینمایی، شبکه یا ساعت باشد، نگه می‌داریم
            if any(keyword in text for keyword in ['سینمایی', 'فیلم', 'شبکه', 'ساعت', ':']):
                filtered_lines.append(text)
                
        if filtered_lines:
            all_movies_text.append(f"--- بنر شماره {index + 1} ---\n" + "\n".join(filtered_lines))
            
        # پاکسازی فایل موقت
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            
    return all_movies_text

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
    # تلگرام محدودیت کاراکتر دارد، اگر پیام خیلی طولانی شد آن را خرد می‌کنیم
    if len(message) > 4000:
        message = message[:3900] + "\n\n[متن طولانی بود، ادامه برش خورد...]"
    requests.post(url, json=payload)

if __name__ == "__main__":
    img_urls = get_recent_channel_images()
    if img_urls:
        movie_reports = extract_movies_from_images(img_urls)
        if movie_reports:
            final_message = "🎬 *گزارش اتوماتیک فیلم‌های سینمایی (کانال EPGnews):*\n\n" + "\n\n".join(movie_reports)
            send_telegram_message(final_message)
        else:
            send_telegram_message("🎬 ربات اجرا شد، اما در بنرهای جدید مورد سینمایی خاصی یافت نشد.")
    else:
        print("عکسی یافت نشد.")
