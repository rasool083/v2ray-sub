import requests
import re
import base64
import json
import urllib.parse
from bs4 import BeautifulSoup
import logging
import time
import os
from datetime import datetime, timezone

# --- تنظیمات لاگ‌گیری ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- تنظیمات اصلی و منابع ---
MAX_CONFIGS = 1000  # حداکثر ظرفیت فایل (FIFO)
NEW_CONFIG_NAME = "t.me/rghoddoosi رسول قدوسی"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}
REQUEST_TIMEOUT = 30

# منابع خود را می‌توانید به هر تعداد که بخواهید در این بخش مدیریت کنید
SOURCES = [
    {"type": "telegram", "url": "https://t.me/s/Farah_VPN"},
    {"type": "telegram", "url": "https://t.me/s/v2rayng_org"},
    {"type": "raw", "url": "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt"}
]

def load_existing_configs() -> list:
    """کانفیگ‌های موجود در فایل sub.txt فعلی را خوانده و رمزگشایی می‌کند."""
    if not os.path.exists("sub.txt"):
        logging.info("فایل sub.txt یافت نشد. یک لیست جدید ایجاد می‌شود.")
        return []
    
    try:
        with open("sub.txt", "r", encoding="utf-8") as f:
            encoded_content = f.read().strip()
        
        if not encoded_content:
            return []
        
        # مدیریت پدینگ برای دکود کردن صحیح Base64
        padded_content = encoded_content + "=" * ((4 - len(encoded_content) % 4) % 4)
        decoded_text = base64.b64decode(padded_content).decode('utf-8')
        
        configs = []
        for line in decoded_text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                configs.append(line)
        
        logging.info(f"تعداد {len(configs)} کانفیگ از فایل قبلی بازیابی شد.")
        return configs
    except Exception as e:
        logging.error(f"خطا در خواندن کانفیگ‌های قدیمی: {e}")
        return []

def is_config_valid(config_str: str) -> bool:
    """ساختار اولیه کانفیگ را برای معتبر بودن بررسی می‌کند."""
    if not config_str: return False
    try:
        if config_str.startswith("vless://"):
            uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
            return '@' in config_str and re.search(uuid_pattern, config_str) is not None
        elif config_str.startswith("trojan://"):
            return '@' in config_str
        elif config_str.startswith("vmess://"):
            b64_part = config_str[8:]
            b64_part += "=" * ((4 - len(b64_part) % 4) % 4)
            data = json.loads(base64.b64decode(b64_part).decode('utf-8'))
            return all(key in data for key in ['add', 'port', 'id'])
        elif config_str.startswith("ss://"):
            return '@' in config_str
    except Exception:
        return False
    return False

def extract_flag_from_name(name: str) -> str:
    """پرچم ایموجی کشور را استخراج می‌کند."""
    # باگ پرانتز r(...) در این خط اصلاح شد
    flag_pattern = r'(\[[A-Z]{2}\])|([🇦-🇿]{2})'
    match = re.search(flag_pattern, name, re.IGNORECASE)
    return next((g for g in match.groups() if g), "🇮🇷") if match else "🇮🇷"

def process_config(config_str: str) -> str | None:
    """یک کانفیگ معتبر را پردازش و نام آن را تغییر می‌دهد."""
    try:
        if config_str.startswith("vmess://"):
            b64_part = config_str[8:]
            b64_part += "=" * ((4 - len(b64_part) % 4) % 4)
            config_data = json.loads(base64.b64decode(b64_part).decode('utf-8'))
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

def scrape_telegram_source(url: str) -> list:
    """صفحات یک کانال تلگرام را با منطق اصلاح‌شده پیمایش می‌کند."""
    configs = []
    current_url = url
    
    for page_num in range(1, 6):  # بررسی تا ۵ صفحه عقب‌تر برای هر کانال
        logging.info(f"در حال استخراج تلگرام: صفحه {page_num} از منبع {url}")
        try:
            response = requests.get(current_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            code_blocks = soup.find_all("code")
            found_in_page = 0
            for block in code_blocks:
                for line in block.get_text(strip=True).splitlines():
                    cleaned_line = line.strip()
                    if is_config_valid(cleaned_line):
                        if (processed := process_config(cleaned_line)):
                            configs.append(processed)
                            found_in_page += 1
            
            logging.info(f"تعداد {found_in_page} کانفیگ معتبر در این صفحه یافت شد.")

            # منطق پیجینیشن کاملاً هوشمند و داینامیک
            next_link = soup.find("a", class_="tgme_widget_message_more")
            if next_link and "before=" in next_link.get("href", ""):
                href = next_link["href"]
                if href.startswith("/s/"):
                    current_url = "https://t.me" + href
                elif href.startswith("?"):
                    current_url = url.split('?')[0] + href
                else:
                    current_url = href
                time.sleep(1.5)
            else:
                break
        except Exception as e:
            logging.error(f"خطا در اسکرپ کانال تلگرام {url}: {e}")
            break
            
    return configs

def fetch_raw_source(url: str) -> list:
    """کانفیگ‌ها را از لینک‌های متنی خام یا ساب‌اسکریپشن‌های متنی (حتی Base64) استخراج می‌کند."""
    configs = []
    logging.info(f"در حال دریافت منبع خارجی: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        text = response.text.strip()
        
        # دکود کردن خودکار در صورتی که کل سورس Base64 باشد
        try:
            padded_text = text + "=" * ((4 - len(text) % 4) % 4)
            decoded = base64.b64decode(padded_text).decode('utf-8')
            if any(p in decoded for p in ["vmess://", "vless://", "ss://", "trojan://"]):
                text = decoded
        except Exception:
            pass
            
        for line in text.splitlines():
            cleaned_line = line.strip()
            if is_config_valid(cleaned_line):
                if (processed := process_config(cleaned_line)):
                    configs.append(processed)
                    
        logging.info(f"تعداد {len(configs)} کانفیگ از منبع متنی استخراج شد.")
    except Exception as e:
        logging.error(f"خطا در دریافت منبع متنی {url}: {e}")
    return configs

def main():
    logging.info("--- شروع اسکریپت به‌روزرسانی هوشمند مخزن کانفیگ ---")
    
    # ۱. بارگذاری داده‌های قبلی برای جلوگیری از پاک شدن فرآیند
    existing_configs = load_existing_configs()
    
    # ۲. جمع‌آوری از تمامی منابع ورودی جدید
    new_configs = []
    for source in SOURCES:
        if source["type"] == "telegram":
            new_configs.extend(scrape_telegram_source(source["url"]))
        elif source["type"] == "raw":
            new_configs.extend(fetch_raw_source(source["url"]))
            
    # ۳. ادغام و حذف همپوشانی‌ها به صورت FIFO معکوس
    # این متد تضمین می‌کند کانفیگی که جدیداً پیدا شده، جایگزین نسخه قدیمی گشته و انقضایش تمدید می‌شود
    combined = existing_configs + new_configs
    unique_reversed = []
    seen = set()
    for config in reversed(combined):
        if config not in seen:
            seen.add(config)
            unique_reversed.append(config)
            
    final_configs = list(reversed(unique_reversed))
    
    # اعمال سقف ظرفیت ۱۰۰۰ عددی (حذف قدیمی‌ترین‌ها در صورت سرریز شدن)
    if len(final_configs) > MAX_CONFIGS:
        dropped_count = len(final_configs) - MAX_CONFIGS
        final_configs = final_configs[-MAX_CONFIGS:]
        logging.info(f"تعداد {dropped_count} کانفیگ قدیمی به دلیل رسیدن به سقف ظرفیت {MAX_CONFIGS} حذف شدند.")
        
    # ۴. ساخت بدنه نهایی دیتای خروجی
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    comment_line = f"# Updated on: {utc_now}\n# Total Active Configs: {len(final_configs)}"
    
    if not final_configs:
        content = f"{comment_line}\n# ⚠️ هیچ کانفیگ معتبری یافت نشد."
    else:
        content = comment_line + "\n" + "\n".join(final_configs)
        
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    # ۵. اوررایت نهایی روی فایل پایگاه داده
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(encoded_content)
        
    logging.info(f"--- عملیات با موفقیت پایان یافت. تعداد {len(final_configs)} کانفیگ یکتا ذخیره شد. ---")

if __name__ == "__main__":
    main()
            
