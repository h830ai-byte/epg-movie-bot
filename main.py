import os
import requests
from bs4 import BeautifulSoup
import easyocr

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
    print("شروع بررسی ۲۰۰ عکس اخیر کانال EPGnews...")
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
    
    # بررسی ۲۰۰ پست آخر کانال
    recent_messages = messages[-200:]
    todays_reports = []
    reader = None
    
    for index, msg in enumerate(recent_messages):
        # ۱. بررسی متن پست
        text_div = msg.find('div', class_='tgme_widget_message_text')
        msg_text = text_div.get_text(separator='\n') if text_div else ""
        
        # ۲. بررسی عکس پست
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
                        print(f"در حال پردازش عکس پست شماره {index + 1}...")
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
        
        combined_content = []
        if msg_text.strip():
            combined_content.append(msg_text)
        if img_text.strip():
            combined_content.append(img_text)
            
        if combined_content:
            todays_reports.append(f"--- پست شماره {index + 1} ---\n" + "\n".join(combined_content))

    if not todays_reports:
        print("هیچ محتوایی یافت نشد.")
        send_telegram_message("🎬 ربات بررسی کرد، اما پستی یافت نشد.")
        return

    print(f"تعداد {len(todays_reports)} پست استخراج شد. در حال ارسال گزارش...")
    
    # از آنجایی که متن ۲۰۰ پست ممکن است بسیار طولانی باشد، آن را بخش به بخش می‌فرستیم تا تلگرام ارور ندهد
    chunk = ""
    for report in todays_reports:
        if len(chunk) + len(report) > 3500:
            send_telegram_message(chunk)
            chunk = ""
        chunk += report + "\n\n"
        
    if chunk.strip():
        send_telegram_message(chunk)
        
    print("گزارش کامل با موفقیت ارسال شد.")

if __name__ == "__main__":
    main()
