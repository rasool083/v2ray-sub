import requests
import re
import base64
import json
import urllib.parse
from bs4 import BeautifulSoup
import logging
import time
from datetime import datetime, timezone

# --- تنظیمات لاگ‌گیری ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- تنظیمات اصلی ---
TELEGRAM_CHANNEL_URL = "https://t.me/s/Farah_VPN"
MAX_CONFIGS = 400
NEW_CONFIG_NAME = "t.me/rghoddoosi رسول قدوسی"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}
REQUEST_TIMEOUT = 30

def save_debug_html(content):
    """در صورت بروز خطا، محتوای HTML صفحه را برای دیباگ ذخیره می‌کند."""
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(content)
    logging.info("محتوای HTML صفحه برای دیباگ در 'debug_page.html' ذخیره شد.")

def is_config_valid(config_str: str) -> bool:
    """ساختار اولیه کانفیگ را برای معتبر بودن بررسی می‌کند."""
    if not config_str: return False
    try:
        if config_str.startswith(("vless://", "trojan://")):
            uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
            return '@' in config_str and re.search(uuid_pattern, config_str) is not None
        elif config_str.startswith("vmess://"):
            b64_part = config_str[8:]
            data = json.loads(base64.b64decode(b64_part + '==').decode('utf-8'))
            return all(key in data for key in ['add', 'port', 'id'])
        elif config_str.startswith("ss://"):
            return '@' in config_str and '#' in config_str
    except Exception:
        return False
    return False

def extract_flag_from_name(name: str) -> str:
    """پرچم ایموجی کشور را استخراج می‌کند."""
    flag_pattern = r'(\[[A-Z]{2}\])|([🇦-🇿]{2})'
    match = re.search(flag_pattern, name, re.IGNORECASE)
    return next((g for g in match.groups() if g), "🇮🇷") if match else "🇮🇷"

def process_config(config_str: str) -> str | None:
    """یک کانفیگ معتبر را پردازش و نام آن را تغییر می‌دهد."""
    try:
        if config_str.startswith("vmess://"):
            b64_part = config_str[8:]
            config_data = json.loads(base64.b64decode(b64_part + '==').decode('utf-8'))
            flag = extract_flag_from_name(config_data.get('ps', ''))
            config_data['ps'] = f"{flag} {NEW_CONFIG_NAME}"
            new_json = json.dumps(config_data, ensure_ascii=False, separators=(',', ':'))
            return "vmess://" + base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
        else:
            parts = config_str.split("#", 1)
            base_config, old_name = parts[0], (urllib.parse.unquote(parts[1]) if len(parts) > 1 else "")
            flag = extract_flag_from_name(old_name)
            new_name_encoded = urllib.parse.quote(f"{flag} {NEW_CONFIG_NAME}")
            return f"{base_config}#{new_name_encoded}"
    except Exception as e:
        logging.error(f"خطا در پردازش کانفیگ: {config_str[:30]}... | خطا: {e}")
        return None

def scrape_telegram_channel():
    """صفحات کانال تلگرام را با منطق پیمایش اصلاح‌شده، پیمایش می‌کند."""
    all_configs = []
    next_page_param = ""
    
    for page_num in range(1, 31): # حداکثر 30 صفحه
        if len(all_configs) >= MAX_CONFIGS:
            logging.info(f"به سقف {MAX_CONFIGS} کانفیگ رسیدیم. پیمایش متوقف می‌شود.")
            break

        full_url = TELEGRAM_CHANNEL_URL + next_page_param
        logging.info(f"--- در حال دریافت صفحه {page_num}: {full_url} ---")

        try:
            response = requests.get(full_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            code_blocks = soup.find_all("code")
            if not code_blocks and page_num == 1:
                logging.warning("هیچ تگ <code> در صفحه اول یافت نشد. ممکن است ساختار تلگرام تغییر کرده باشد.")
                save_debug_html(response.text)

            found_in_page = 0
            for block in code_blocks:
                for line in block.get_text(strip=True).splitlines():
                    if is_config_valid(line.strip()):
                        if (processed := process_config(line.strip())):
                            all_configs.append(processed)
                            found_in_page += 1
            
            logging.info(f"تعداد {found_in_page} کانفیگ معتبر در این صفحه یافت شد.")

            # --- منطق پیمایش اصلاح‌شده و مقاوم ---
            if not (older_posts_link := soup.select_one('a.tgme_widget_message_more[href^="?before="]')):
                logging.info("به انتهای کانال رسیدیم یا لینک صفحه بعد یافت نشد. پایان پیمایش.")
                break
            
            next_page_param = older_posts_link['href']
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            logging.error(f"خطا در اتصال به تلگرام: {e}")
            # در صورت خطا در درخواست، ممکن است بخواهیم HTML را برای بررسی ذخیره کنیم
            if 'response' in locals() and hasattr(response, 'text'):
                save_debug_html(response.text)
            break
    
    return list(dict.fromkeys(all_configs))[:MAX_CONFIGS]

def main():
    logging.info("--- شروع اسکریپت به‌روزرسانی (نسخه با دیباگ و پیمایش اصلاح‌شده) ---")
    try:
        final_configs = scrape_telegram_channel()
        
        # --- افزودن Timestamp برای تضمین تغییر فایل ---
        utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        comment_line = f"# Updated on: {utc_now}"
        
        if not final_configs:
            logging.warning("هیچ کانفیگ معتبری یافت نشد.")
            content = f"{comment_line}\n# ⚠️ هیچ کانفیگ معتبری در این لحظه یافت نشد."
        else:
            logging.info(f"مجموعاً {len(final_configs)} کانفیگ منحصر به فرد و معتبر برای ذخیره یافت شد.")
            # قرار دادن کامنت زمان در بالای لیست کانفیگ‌ها
            content_list = [comment_line] + final_configs
            content = "\n".join(content_list)
            
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    except Exception as e:
        logging.error(f"یک خطای کلی و پیش‌بینی‌نشده در اجرای اسکریپت رخ داد: {e}", exc_info=True)
        error_message = f"# Updated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}\n# ⚠️ خطا در اجرای اسکریپت: {e}"
        encoded_content = base64.b64encode(error_message.encode('utf-8')).decode('utf-8')

    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(encoded_content)
    logging.info("--- عملیات با موفقیت انجام شد. فایل sub.txt به‌روز شد. ---")

if __name__ == "__main__":
    main()
    
