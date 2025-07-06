import requests
import re
import base64
import json
import urllib.parse
from bs4 import BeautifulSoup
import logging
import time

# --- تنظیمات لاگ‌گیری برای دیباگ بهتر در GitHub Actions ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- تنظیمات اصلی اسکریپت ---
TELEGRAM_CHANNEL_URL = "https://t.me/s/ConfigsHubPlus"
MAX_CONFIGS = 400
NEW_CONFIG_NAME = "t.me/rghoddoosi رسول قدوسی"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}
REQUEST_TIMEOUT = 30

def is_config_valid(config_str: str) -> bool:
    """یک رشته کانفیگ را برای معتبر بودن ساختار اولیه آن بررسی می‌کند."""
    if not config_str: return False
    try:
        if config_str.startswith("vless://") or config_str.startswith("trojan://"):
            uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
            return '@' in config_str and re.search(uuid_pattern, config_str) is not None
        elif config_str.startswith("vmess://"):
            b64_part = config_str[8:]
            padded_b64 = b64_part + '=' * (-len(b64_part) % 4)
            data = json.loads(base64.b64decode(padded_b64).decode('utf-8'))
            return all(key in data for key in ['add', 'port', 'id', 'ps'])
        elif config_str.startswith("ss://"):
            return '@' in config_str and '#' in config_str
    except Exception:
        return False
    return False

def extract_flag_from_name(name: str) -> str:
    """پرچم ایموجی کشور را از نام کانفیگ استخراج می‌کند."""
    flag_pattern = r'(\[[A-Z]{2}\])|([🇦-🇿]{2})'
    match = re.search(flag_pattern, name, re.IGNORECASE)
    if match:
        return next((group for group in match.groups() if group is not None), "🇮🇷")
    return "🇮🇷"

def process_config(config_str: str) -> str | None:
    """یک کانفیگ معتبر را پردازش کرده و نام آن را تغییر می‌دهد."""
    try:
        if config_str.startswith("vmess://"):
            b64_part = config_str[8:]
            padded_b64 = b64_part + '=' * (-len(b64_part) % 4)
            config_data = json.loads(base64.b64decode(padded_b64).decode('utf-8'))
            flag = extract_flag_from_name(config_data.get('ps', ''))
            config_data['ps'] = f"{flag} {NEW_CONFIG_NAME}"
            new_json = json.dumps(config_data, ensure_ascii=False, separators=(',', ':'))
            return "vmess://" + base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
        else:
            parts = config_str.split("#", 1)
            base_config = parts[0]
            old_name = urllib.parse.unquote(parts[1]) if len(parts) > 1 else ""
            flag = extract_flag_from_name(old_name)
            new_name_encoded = urllib.parse.quote(f"{flag} {NEW_CONFIG_NAME}")
            return f"{base_config}#{new_name_encoded}"
    except Exception as e:
        logging.error(f"خطا در پردازش کانفیگ: {config_str[:30]}... | خطا: {e}")
        return None

def scrape_telegram_channel():
    """
    صفحات کانال تلگرام را با استفاده از روش پیمایش مقاوم، برای استخراج کانفیگ‌ها پیمایش می‌کند.
    """
    all_configs = []
    base_url = "https://t.me"
    current_path = f"/s/{TELEGRAM_CHANNEL_URL.split('/')[-1]}"
    
    # حلقه برای پیمایش صفحات تا رسیدن به سقف کانفیگ‌ها
    for page_num in range(1, 31): # حداکثر 30 صفحه را برای جلوگیری از حلقه بی‌نهایت بررسی می‌کند
        if len(all_configs) >= MAX_CONFIGS:
            logging.info("به سقف ۴۰۰ کانفیگ رسیدیم. پیمایش متوقف می‌شود.")
            break

        full_url = base_url + current_path
        logging.info(f"--- در حال دریافت صفحه {page_num}: {full_url} ---")

        try:
            response = requests.get(full_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # استخراج کانفیگ‌ها از تگ‌های <code>
            code_blocks = soup.find_all("code")
            found_in_page = 0
            for block in code_blocks:
                for line in block.get_text(strip=True).splitlines():
                    clean_line = line.strip()
                    if is_config_valid(clean_line):
                        processed = process_config(clean_line)
                        if processed:
                            all_configs.append(processed)
                            found_in_page += 1
            
            logging.info(f"تعداد {found_in_page} کانفیگ معتبر در این صفحه یافت شد.")

            # --- بخش کلیدی: منطق جدید و مقاوم برای پیدا کردن صفحه بعد ---
            # به دنبال تگ a می‌گردیم که href آن با ?before= شروع می‌شود
            older_posts_link = soup.select_one('a.tgme_widget_message_more[href^="?before="]')
            
            if older_posts_link:
                current_path = older_posts_link['href']
                # افزودن یک تاخیر کوچک بین درخواست‌ها برای جلوگیری از بلاک شدن
                time.sleep(1) 
            else:
                logging.info("به انتهای کانال رسیدیم یا لینک صفحه بعد یافت نشد. پایان پیمایش.")
                break

        except requests.exceptions.RequestException as e:
            logging.error(f"خطا در اتصال به تلگرام: {e}")
            break
    
    unique_configs = list(dict.fromkeys(all_configs))
    return unique_configs[:MAX_CONFIGS]

def main():
    logging.info("--- شروع اسکریپت به‌روزرسانی کانفیگ V2Ray (نسخه با پیمایش اصلاح‌شده) ---")
    try:
        final_configs = scrape_telegram_channel()
        if not final_configs:
            logging.warning("هیچ کانفیگ معتبری یافت نشد.")
            content = "⚠️ هیچ کانفیگ معتبری در این لحظه یافت نشد."
        else:
            logging.info(f"مجموعاً {len(final_configs)} کانفیگ منحصر به فرد و معتبر برای ذخیره یافت شد.")
            content = "\n".join(final_configs)
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logging.error(f"یک خطای کلی و پیش‌بینی‌نشده در اجرای اسکریپت رخ داد: {e}")
        error_message = f"⚠️ خطا در اجرای اسکریپت: {e}"
        encoded_content = base64.b64encode(error_message.encode('utf-8')).decode('utf-8')

    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(encoded_content)
    logging.info(f"--- عملیات با موفقیت انجام شد. فایل sub.txt به‌روز شد. ---")

if __name__ == "__main__":
    main()
