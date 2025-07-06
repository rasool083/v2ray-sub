import requests
import re
import base64
import json
import urllib.parse
from bs4 import BeautifulSoup
import logging

# --- تنظیمات لاگ‌گیری برای دیباگ بهتر در GitHub Actions ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- تنظیمات اصلی اسکریپت ---
# URL کانال تلگرام برای استخراج کانفیگ‌ها
TELEGRAM_CHANNEL_URL = "https://t.me/s/ConfigsHubPlus"
# حداکثر تعداد کانفیگ برای جمع‌آوری در هر بار اجرا
MAX_CONFIGS = 400
# نام جدیدی که برای کانفیگ‌ها تنظیم می‌شود (پرچم به صورت خودکار اضافه خواهد شد)
NEW_CONFIG_NAME = "t.me/rghoddoosi رسول قدوسی"
# هدر User-Agent برای شبیه‌سازی یک مرورگر واقعی و جلوگیری از بلاک شدن
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}
# زمان انتظار برای هر درخواست (به ثانیه)
REQUEST_TIMEOUT = 25

def extract_flag_from_name(name: str) -> str:
    """
    یک نام را دریافت کرده و سعی می‌کند پرچم ایموجی کشور را از آن استخراج کند.
    الگوهای رایج مانند [🇨🇦] یا 🇺🇸 را پیدا می‌کند.
    """
    # الگو برای پیدا کردن ایموجی‌های پرچم که ممکن است در براکت باشند یا نباشند
    flag_pattern = r'(\[[A-Z]{2}\])|([🇦-🇿]{2})'
    match = re.search(flag_pattern, name, re.IGNORECASE)
    if match:
        # برگرداندن اولین گروه پیدا شده که خالی نیست
        return next((group for group in match.groups() if group is not None), "🇮🇷")
    return "🇮🇷" # پرچم پیش‌فرض در صورت عدم یافتن

def process_config(config_str: str) -> str | None:
    """
    یک رشته کانفیگ خام را پردازش کرده، نام آن را تغییر می‌دهد و کانفیگ اصلاح‌شده را برمی‌گرداند.
    در صورت بروز خطا یا نامعتبر بودن کانفیگ، None را برمی‌گرداند.
    """
    try:
        # --- پردازش کانفیگ‌های Vmess ---
        if config_str.startswith("vmess://"):
            try:
                # افزودن padding صحیح برای جلوگیری از خطای Base64
                b64_part = config_str[8:]
                padded_b64 = b64_part + '=' * (-len(b64_part) % 4)
                decoded_json = base64.b64decode(padded_b64).decode('utf-8')
                config_data = json.loads(decoded_json)
                
                original_ps = config_data.get('ps', '')
                flag = extract_flag_from_name(original_ps)
                
                config_data['ps'] = f"{flag} {NEW_CONFIG_NAME}"
                
                new_json = json.dumps(config_data, ensure_ascii=False, separators=(',', ':'))
                new_b64 = base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
                return "vmess://" + new_b64
            except (json.JSONDecodeError, base64.Error, UnicodeDecodeError) as e:
                logging.warning(f"کانفیگ Vmess نامعتبر است و نادیده گرفته شد: {config_str[:30]}... | خطا: {e}")
                return None

        # --- پردازش کانفیگ‌های Vless, Trojan, SS ---
        elif any(config_str.startswith(p) for p in ["vless://", "trojan://", "ss://"]):
            parts = config_str.split("#", 1)
            base_config = parts[0]
            
            # اگر کانفیگ فاقد بدنه اصلی بود، آن را نامعتبر بدان
            if not base_config:
                return None

            old_name = urllib.parse.unquote(parts[1]) if len(parts) > 1 else ""
            flag = extract_flag_from_name(old_name)
            
            # ساخت نام جدید و کدگذاری صحیح آن برای استفاده در URL
            new_name_encoded = urllib.parse.quote(f"{flag} {NEW_CONFIG_NAME}")
            
            return f"{base_config}#{new_name_encoded}"
        
        else:
            # اگر پروتکل پشتیبانی نمی‌شد، آن را نادیده بگیر
            return None

    except Exception as e:
        logging.error(f"خطای غیرمنتظره در پردازش کانفیگ: {config_str[:30]}... | خطا: {e}")
        return None

def scrape_telegram_channel():
    """
    صفحات کانال تلگرام را برای استخراج کانفیگ‌ها پیمایش می‌کند.
    """
    all_configs = []
    current_url = TELEGRAM_CHANNEL_URL
    processed_urls = set() # برای جلوگیری از افتادن در حلقه بی‌نهایت

    while current_url and len(all_configs) < MAX_CONFIGS:
        if current_url in processed_urls:
            logging.warning("URL تکراری شناسایی شد، پیمایش متوقف می‌شود.")
            break
        
        logging.info(f"در حال دریافت صفحه: {current_url}")
        processed_urls.add(current_url)

        try:
            response = requests.get(current_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status() # اگر کد وضعیت خطا بود (مثل 404 یا 500)، استثنا ایجاد می‌کند
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # استخراج کانفیگ‌ها از تگ‌های <code> که روشی دقیق و قابل اعتماد است
            code_blocks = soup.find_all("code")
            for block in code_blocks:
                # استفاده از splitlines برای جدا کردن کانفیگ‌ها در صورتی که در یک بلوک کد باشند
                for line in block.get_text(strip=True).splitlines():
                    clean_line = line.strip()
                    if any(clean_line.startswith(p) for p in ["vmess://", "vless://", "trojan://", "ss://"]):
                        processed = process_config(clean_line)
                        if processed:
                            all_configs.append(processed)
                        if len(all_configs) >= MAX_CONFIGS:
                            break
                if len(all_configs) >= MAX_CONFIGS:
                    break
            
            # پیدا کردن لینک "Older posts" برای رفتن به صفحه بعد
            older_posts_link = soup.find('a', class_='tgme_widget_message_more', attrs={'href': True})
            if older_posts_link:
                current_url = "https://t.me" + older_posts_link['href']
            else:
                logging.info("به انتهای کانال رسیدیم. لینک 'Older posts' یافت نشد.")
                current_url = None # پایان پیمایش

        except requests.exceptions.RequestException as e:
            logging.error(f"خطا در اتصال به تلگرام: {e}")
            break # در صورت خطا در اتصال، عملیات متوقف می‌شود
    
    # حذف موارد تکراری با حفظ ترتیب و محدود کردن به تعداد حداکثر
    unique_configs = list(dict.fromkeys(all_configs))
    return unique_configs[:MAX_CONFIGS]

def main():
    """ تابع اصلی برنامه """
    logging.info("--- شروع اسکریپت به‌روزرسانی کانفیگ V2Ray ---")
    
    try:
        final_configs = scrape_telegram_channel()
        
        if not final_configs:
            logging.warning("هیچ کانفیگ معتبری یافت نشد. فایل sub.txt با پیام خطا به‌روز می‌شود.")
            content = "⚠️ هیچ کانفیگ معتبری در این لحظه یافت نشد."
        else:
            logging.info(f"تعداد {len(final_configs)} کانفیگ منحصر به فرد یافت شد.")
            content = "\n".join(final_configs)
            
        # کدگذاری کل محتوای نهایی به Base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    except Exception as e:
        logging.error(f"یک خطای کلی و پیش‌بینی‌نشده در اجرای اسکریپت رخ داد: {e}")
        error_message = f"⚠️ خطا در اجرای اسکریپت: {e}"
        encoded_content = base64.b64encode(error_message.encode('utf-8')).decode('utf-8')

    # ذخیره محتوای نهایی در فایل sub.txt
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(encoded_content)
    
    logging.info(f"--- عملیات با موفقیت انجام شد. فایل sub.txt با {len(encoded_content)} بایت به‌روز شد. ---")

if __name__ == "__main__":
    main()
    
