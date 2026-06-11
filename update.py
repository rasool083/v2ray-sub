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
MAX_CONFIGS = 20000  # حداکثر ظرفیت فایل (FIFO)
NEW_CONFIG_NAME = "t.me/rghoddoosi رسول قدوسی"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}
REQUEST_TIMEOUT = 30

# اضافه شدن شناسه (id) به هر منبع برای تشخیص اینکه کانفیگ از کدام مخزن آمده است
SOURCES = [
    {"id": "1", "type": "telegram", "url": "https://t.me/s/Farah_VPN"},
    {"id": "2", "type": "telegram", "url": "https://t.me/s/NETMelliAnti"},
    {"id": "3", "type": "telegram", "url": "https://t.me/s/ConfigsHUB2"},
    {"id": "4", "type": "raw", "url": "https://raw.githubusercontent.com/SOSIranConnect/cloudconfig/refs/heads/main/CloudActive.txt"},
    {"id": "5", "type": "raw", "url": "https://raw.githubusercontent.com/ThomasJasperthecat/sub/main/sublist1.txt"},
    {"id": "6", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/sub/sub_merge.txt"},
{"id": "7", "type": "raw", "url": "https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/ocean/sub_merge.txt"},
{"id": "8", "type": "raw", "url": "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt"},
{"id": "9", "type": "raw", "url": "https://raw.githubusercontent.com/yebekhe/telegram-configs-collector/main/sub/sub_merge.txt"},
{"id": "10", "type": "raw", "url": "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub"},
{"id": "11", "type": "raw", "url": "https://raw.githubusercontent.com/v2rayplus/subscription/main/all.txt"},
{"id": "12", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/sub/sub_merge_new.txt"},
{"id": "13", "type": "raw", "url": "https://raw.githubusercontent.com/mfuu/v2ray/main/sub"},
{"id": "14", "type": "raw", "url": "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2"},
{"id": "15", "type": "raw", "url": "https://raw.githubusercontent.com/BlackSnowDot/subscription/main/subscription.txt"},
{"id": "16", "type": "raw", "url": "https://raw.githubusercontent.com/ssrsub/ssr/master/V2Ray.txt"},
{"id": "17", "type": "raw", "url": "https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg"},
{"id": "18", "type": "raw", "url": "https://raw.githubusercontent.com/freefq/free/master/v2"},
{"id": "19", "type": "raw", "url": "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt"},
{"id": "20", "type": "raw", "url": "https://raw.githubusercontent.com/Alvin9999/pac2/master/ss-subscribe.txt"},
{"id": "21", "type": "raw", "url": "https://raw.githubusercontent.com/du5/free/master/v2"},
{"id": "22", "type": "raw", "url": "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/sub/sub_merge.txt"},
{"id": "23", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/sub/clash_config.txt"},
{"id": "24", "type": "raw", "url": "https://raw.githubusercontent.com/ermaozi/sub/main/subscribe.txt"},
{"id": "25", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/sub/mini.txt"},
{"id": "26", "type": "raw", "url": "https://raw.githubusercontent.com/mfuu/v2ray/main/mini.txt"},
{"id": "27", "type": "raw", "url": "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/mini.txt"},
{"id": "28", "type": "raw", "url": "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash_mini.yml"},
{"id": "29", "type": "raw", "url": "https://raw.githubusercontent.com/v2rayplus/subscription/main/mini.txt"},
{"id": "30", "type": "raw", "url": "https://raw.githubusercontent.com/BlackSnowDot/subscription/main/mini.txt"},
{"id": "31", "type": "raw", "url": "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list_mini.txt"},
{"id": "32", "type": "raw", "url": "https://raw.githubusercontent.com/du5/free/master/mini.txt"},
{"id": "33", "type": "raw", "url": "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/mini.txt"},
{"id": "34", "type": "raw", "url": "https://raw.githubusercontent.com/freefq/free/master/v2ray.txt"},
{"id": "35", "type": "raw", "url": "https://raw.githubusercontent.com/ssrsub/ssr/master/mini.txt"},
{"id": "36", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/sub/irancell.txt"},
{"id": "37", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/sub/mci.txt"},
{"id": "38", "type": "raw", "url": "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/mci.txt"},
{"id": "39", "type": "raw", "url": "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/irancell.txt"},
{"id": "40", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/sub/test.txt"},
{"id": "41", "type": "raw", "url": "https://raw.githubusercontent.com/du5/free/master/irancell.txt"},
{"id": "42", "type": "raw", "url": "https://raw.githubusercontent.com/du5/free/master/mci.txt"},
{"id": "43", "type": "raw", "url": "https://skymun016.github.io/hysteria2-subscription/subscription.txt"},
{"id": "44", "type": "raw", "url": "https://raw.githubusercontent.com/Iam54r1n4/Hysteria2/main/config.json"},
{"id": "45", "type": "raw", "url": "https://raw.githubusercontent.com/TheyCallMeSecond/config-examples/main/Hysteria/Hysteria2.json"},
{"id": "46", "type": "raw", "url": "https://raw.githubusercontent.com/zhcharles/Hysteria2-Management/main/config.json"},
{"id": "47", "type": "raw", "url": "https://raw.githubusercontent.com/10ium/HiN-VPN/main/subscription/normal/hysteria"},
{"id": "48", "type": "raw", "url": "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/hysteria2"},
{"id": "49", "type": "raw", "url": "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/python/hysteria2"},
{"id": "50", "type": "raw", "url": "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/all_sub.txt"},
{"id": "51", "type": "raw", "url": "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/super-sub.txt"},
{"id": "52", "type": "raw", "url": "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/hy2.txt"},
{"id": "53", "type": "raw", "url": "https://raw.githubusercontent.com/PlanAsli/configs-collector-v2ray/main/sub/protocols/vless.txt"},
{"id": "54", "type": "raw", "url": "https://raw.githubusercontent.com/PlanAsli/configs-collector-v2ray/main/sub/networks/reality.txt"},
{"id": "55", "type": "raw", "url": "https://raw.githubusercontent.com/PlanAsli/configs-collector-v2ray/main/sub/splitted/mixed_1.txt"},
{"id": "56", "type": "raw", "url": "https://raw.githubusercontent.com/snakem982/proxypool/main/source/v2ray-2.txt"},
{"id": "57", "type": "raw", "url": "https://raw.githubusercontent.com/snakem982/proxypool/main/source/clash-meta.yaml"},
{"id": "58", "type": "raw", "url": "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/all_sub.txt"},
{"id": "59", "type": "raw", "url": "https://raw.githubusercontent.com/PlanAsli/configs-collector-v2ray/main/sub/splitted/mixed_1.txt"},
{"id": "60", "type": "raw", "url": "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/sub.txt"},
{"id": "61", "type": "raw", "url": "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/sub/sub_merge.txt"},
{"id": "62", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/AzadNet.txt"},
{"id": "63", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/sub/sub_merge.txt"},
{"id": "64", "type": "raw", "url": "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/all"},
{"id": "65", "type": "raw", "url": "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub1.txt"},
{"id": "66", "type": "raw", "url": "https://raw.githubusercontent.com/Pasimand/v2ray-config-agg/main/config.txt"},
{"id": "67", "type": "raw", "url": "https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg"},
{"id": "68", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/sub/irancell.txt"},
{"id": "69", "type": "raw", "url": "https://raw.githubusercontent.com/AzadNetCH/Clash/main/sub/mci.txt"},
{"id": "70", "type": "raw", "url": "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/mci.txt"},
{"id": "71", "type": "raw", "url": "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/irancell.txt"},
{"id": "72", "type": "raw", "url": "https://raw.githubusercontent.com/du5/free/master/irancell.txt"},
{"id": "73", "type": "raw", "url": "https://raw.githubusercontent.com/du5/free/master/mci.txt"},
{"id": "74", "type": "raw", "url": "https://skymun016.github.io/hysteria2-subscription/subscription.txt"},
{"id": "75", "type": "raw", "url": "https://raw.githubusercontent.com/Iam54r1n4/Hysteria2/main/config.json"},
{"id": "76", "type": "raw", "url": "https://raw.githubusercontent.com/TheyCallMeSecond/config-examples/main/Hysteria/Hysteria2.json"},
{"id": "77", "type": "raw", "url": "https://raw.githubusercontent.com/zhcharles/Hysteria2-Management/main/config.json"},
{"id": "78", "type": "raw", "url": "https://raw.githubusercontent.com/10ium/HiN-VPN/main/subscription/normal/hysteria"},
{"id": "79", "type": "raw", "url": "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/hysteria2"},
{"id": "80", "type": "raw", "url": "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt"},
    
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
    flag_pattern = r'(\[[A-Z]{2}\])|([🇦-🇿]{2})'
    match = re.search(flag_pattern, name, re.IGNORECASE)
    return next((g for g in match.groups() if g), "🇮🇷") if match else "🇮🇷"

def process_config(config_str: str, source_id: str) -> str | None:
    """یک کانفیگ معتبر را پردازش و نام آن را به همراه شناسه منبع تغییر می‌دهد."""
    try:
        if config_str.startswith("vmess://"):
            b64_part = config_str[8:]
            b64_part += "=" * ((4 - len(b64_part) % 4) % 4)
            config_data = json.loads(base64.b64decode(b64_part).decode('utf-8'))
            flag = extract_flag_from_name(config_data.get('ps', ''))
            
            # قرار دادن شناسه مخزن در انتهای نام
            config_data['ps'] = f"{flag} {NEW_CONFIG_NAME} - {source_id}"
            
            new_json = json.dumps(config_data, ensure_ascii=False, separators=(',', ':'))
            return "vmess://" + base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
        else:
            parts = config_str.split("#", 1)
            base_config = parts[0]
            old_name = urllib.parse.unquote(parts[1]) if len(parts) > 1 else ""
            flag = extract_flag_from_name(old_name)
            
            # قرار دادن شناسه مخزن در انتهای نام
            new_name_raw = f"{flag} {NEW_CONFIG_NAME} - {source_id}"
            new_name_encoded = urllib.parse.quote(new_name_raw)
            
            return f"{base_config}#{new_name_encoded}"
    except Exception as e:
        logging.error(f"خطا در پردازش کانفیگ: {config_str[:30]}... | خطا: {e}")
        return None

def scrape_telegram_source(url: str, source_id: str) -> list:
    """صفحات یک کانال تلگرام را پیمایش می‌کند."""
    configs = []
    current_url = url
    
    for page_num in range(1, 6):
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
                        # پاس دادن شناسه منبع به تابع پردازش
                        if (processed := process_config(cleaned_line, source_id)):
                            configs.append(processed)
                            found_in_page += 1
            
            logging.info(f"تعداد {found_in_page} کانفیگ معتبر در این صفحه یافت شد.")

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

def fetch_raw_source(url: str, source_id: str) -> list:
    """کانفیگ‌ها را از لینک‌های خام استخراج می‌کند."""
    configs = []
    logging.info(f"در حال دریافت منبع خارجی: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        text = response.text.strip()
        
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
                # پاس دادن شناسه منبع به تابع پردازش
                if (processed := process_config(cleaned_line, source_id)):
                    configs.append(processed)
                    
        logging.info(f"تعداد {len(configs)} کانفیگ از منبع متنی استخراج شد.")
    except Exception as e:
        logging.error(f"خطا در دریافت منبع متنی {url}: {e}")
    return configs

def main():
    logging.info("--- شروع اسکریپت به‌روزرسانی هوشمند مخزن کانفیگ ---")
    
    existing_configs = load_existing_configs()
    
    new_configs = []
    # پاس دادن شناسه به توابع دریافت اطلاعات
    for source in SOURCES:
        if source["type"] == "telegram":
            new_configs.extend(scrape_telegram_source(source["url"], source["id"]))
        elif source["type"] == "raw":
            new_configs.extend(fetch_raw_source(source["url"], source["id"]))
            
    combined = existing_configs + new_configs
    unique_reversed = []
    seen = set()
    for config in reversed(combined):
        if config not in seen:
            seen.add(config)
            unique_reversed.append(config)
            
    final_configs = list(reversed(unique_reversed))
    
    if len(final_configs) > MAX_CONFIGS:
        dropped_count = len(final_configs) - MAX_CONFIGS
        final_configs = final_configs[-MAX_CONFIGS:]
        logging.info(f"تعداد {dropped_count} کانفیگ قدیمی به دلیل رسیدن به سقف ظرفیت {MAX_CONFIGS} حذف شدند.")
        
    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    comment_line = f"# Updated on: {utc_now}\n# Total Active Configs: {len(final_configs)}"
    
    if not final_configs:
        content = f"{comment_line}\n# ⚠️ هیچ کانفیگ معتبری یافت نشد."
    else:
        content = comment_line + "\n" + "\n".join(final_configs)
        
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(encoded_content)
        
    logging.info(f"--- عملیات با موفقیت پایان یافت. تعداد {len(final_configs)} کانفیگ یکتا ذخیره شد. ---")

if __name__ == "__main__":
    main()
    
