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
TELEGRAM_CHANNEL_URL = "https://t.me/s/ConfigsHubPlus"
MAX_CONFIGS = 400
NEW_CONFIG_NAME = "t.me/rghoddoosi رسول قدوسی"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}
REQUEST_TIMEOUT = 25

def is_config_valid(config_str: str) -> bool:
    """
    یک رشته کانفیگ را دریافت کرده و ساختار اولیه آن را برای معتبر بودن بررسی می‌کند.
    این تابع از توقف پردازش در V2RayNG به دلیل یک کانفیگ نامعتبر جلوگیری می‌کند.
    """
    if not config_str:
        return False
    
    try:
        # --- اعتبارسنجی Vless و Trojan ---
        if config_str.startswith("vless://") or config_str.startswith("trojan://"):
            # حداقل بررسی: باید شامل یک UUID و علامت @ باشد.
            # الگوی UUID: 8-4-4-4-12 کاراکتر هگزادسیمال
            uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
            if '@' in config_str and re.search(uuid_pattern, config_str):
                return True
            logging.warning(f"ساختار Vless/Trojan نامعتبر است: {config_str[:40]}...")
            return False

        # --- اعتبارسنجی Vmess ---
        elif config_str.startswith("vmess://"):
            b64_part = config_str[8:]
            padded_b64 = b64_part + '=' * (-len(b64_part) % 4)
            decoded_json = base64.b64decode(padded_b64).decode('utf-8')
            data = json.loads(decoded_json)
            # بررسی وجود فیلدهای ضروری در کانفیگ Vmess
            if all(key in data for key in ['add', 'port', 'id', 'ps']):
                return True
            logging.warning(f"فیلدهای ضروری Vmess یافت نشد: {config_str[:30]}...")
            return False
            
        # --- اعتبارسنجی SS (بسیار ساده) ---
        elif config_str.startswith("ss://"):
             # حداقل بررسی: باید شامل علامت @ و # باشد
            if '@' in config_str and '#' in config_str:
                return True
            logging.warning(f"ساختار SS نامعتبر است: {config_str[:40]}...")
            return False

    except Exception as e:
        logging.error(f"خطا در اعتبارسنجی کانفیگ: {config_str[:40]}... | خطا: {e}")
        return False
    
    return False


def extract_flag_from_name(name: str) -> str:
    """
    یک نام را دریافت کرده و سعی می‌کند پرچم ایموجی کشور را از آن استخراج کند.
    """
    flag_pattern = r'(\[[A-Z]{2}\])|([🇦-🇿]{2})'
    match = re.search(flag_pattern, name, re.IGNORECASE)
    if match:
        return next((group for group in match.groups() if group is not None), "🇮🇷")
    return "🇮🇷"

def process_config(config_str: str) -> str | None:
    """
    یک رشته کانفیگ خام معتبر را پردازش کرده و نام آن را تغییر می‌دهد.
    """
    try:
        if config_str.startswith("vmess://"):
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
        else:
            parts = config_str.split("#", 1)
            base_config = parts[0]
            old_name = urllib.parse.unquote(parts[1]) if len(parts) > 1 else ""
            flag = extract_flag_from_name(old_name)
            new_name_encoded = urllib.parse.quote(f"{flag} {NEW_CONFIG_NAME}")
            return f"{base_config}#{new_name_encoded}"
    except Exception as e:
        logging.error(f"خطا در پردازش کانفیگ معتبر: {config_str[:30]}... | خطا: {e}")
        return None

def scrape_telegram_channel():
    """
    صفحات کانال تلگرام را برای استخراج کانفیگ‌ها پیمایش می‌کند.
    """
    all_configs = []
    current_url = TELEGRAM_CHANNEL_URL
    processed_urls = set()

    while current_url and len(all_configs) < MAX_CONFIGS:
        if current_url in processed_urls:
            logging.warning("URL تکراری شناسایی شد، پیمایش متوقف می‌شود.")
            break
        
        logging.info(f"در حال دریافت صفحه: {current_url}")
        processed_urls.add(current_url)

        try:
            response = requests.get(current_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            code_blocks = soup.find_all("code")
            for block in code_blocks:
                for line in block.get_text(strip=True).splitlines():
                    clean_line = line.strip()
                    
                    # --- مرحله جدید: اول اعتبارسنجی، سپس پردازش ---
                    if is_config_valid(clean_line):
                        processed = process_config(clean_line)
                        if processed:
                            all_configs.append(processed)
                    
                    if len(all_configs) >= MAX_CONFIGS:
                        break
                if len(all_configs) >= MAX_CONFIGS:
                    break
            
            older_posts_link = soup.find('a', class_='tgme_widget_message_more', attrs={'href': True})
            if older_posts_link:
                current_url = "https://t.me" + older_posts_link['href']
            else:
                logging.info("به انتهای کانال رسیدیم.")
                current_url = None

        except requests.exceptions.RequestException as e:
            logging.error(f"خطا در اتصال به تلگرام: {e}")
            break
    
    unique_configs = list(dict.fromkeys(all_configs))
    return unique_configs[:MAX_CONFIGS]

def main():
    logging.info("--- شروع اسکریپت به‌روزرسانی کانفیگ V2Ray (نسخه با اعتبارسنجی) ---")
    
    try:
        final_configs = scrape_telegram_channel()
        
        if not final_configs:
            logging.warning("هیچ کانفیگ معتبری یافت نشد.")
            content = "⚠️ هیچ کانفیگ معتبری در این لحظه یافت نشد."
        else:
            logging.info(f"تعداد {len(final_configs)} کانفیگ معتبر و پردازش شده یافت شد.")
            content = "\n".join(final_configs)
            
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    except Exception as e:
        logging.error(f"یک خطای کلی و پیش‌بینی‌نشده در اجرای اسکریپت رخ داد: {e}")
        error_message = f"⚠️ خطا در اجرای اسکریپت: {e}"
        encoded_content = base64.b64encode(error_message.encode('utf-8')).decode('utf-8')

    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(encoded_content)
    
    logging.info(f"--- عملیات با موفقیت انجام شد. فایل sub.txt با {len(encoded_content)} بایت به‌روز شد. ---")

if __name__ == "__main__":
    main()
    
