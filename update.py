import requests
import re
import base64
import json
import urllib.parse
from bs4 import BeautifulSoup

# --- تنظیمات اولیه ---
# URL کانال تلگرام
TELEGRAM_CHANNEL_URL = "https://t.me/s/ConfigsHubPlus"
# حداکثر تعداد کانفیگ برای جمع‌آوری
MAX_CONFIGS = 400
# نام جدیدی که برای کانفیگ‌ها تنظیم می‌شود
NEW_CONFIG_NAME = "t.me/rghoddoosi رسول قدوسی"
# هدر برای ارسال درخواست‌ها، برای جلوگیری از بلاک شدن
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def process_config(config_str):
    """
    این تابع یک رشته کانفیگ را دریافت کرده، نام آن را تغییر می‌دهد و کانفیگ اصلاح‌شده را برمی‌گرداند.
    """
    try:
        # --- پردازش کانفیگ‌های Vmess ---
        if config_str.startswith("vmess://"):
            raw_b64 = config_str[8:]
            # اطمینان از صحت Base64 padding
            padded_b64 = raw_b64 + '=' * (-len(raw_b64) % 4)
            decoded_json = base64.b64decode(padded_b64).decode('utf-8')
            config_data = json.loads(decoded_json)
            
            # استخراج پرچم کشور از نام قبلی (در صورت وجود)
            original_ps = config_data.get('ps', '')
            flag_match = re.search(r'(\[.*?\])', original_ps)
            flag = flag_match.group(1) if flag_match else "[🏳️]"
            
            # تنظیم نام جدید با پرچم
            config_data['ps'] = f"{flag} {NEW_CONFIG_NAME}"
            
            # کدگذاری مجدد به Base64 و بازگرداندن کانفیگ کامل
            new_json = json.dumps(config_data, ensure_ascii=False, separators=(',', ':'))
            new_b64 = base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
            return "vmess://" + new_b64
            
        # --- پردازش کانفیگ‌های Vless, Trojan, SS ---
        else:
            base_config, *name_part = config_str.split("#", 1)
            old_name = urllib.parse.unquote(name_part[0]) if name_part else ""
            
            # استخراج پرچم کشور از نام قبلی
            flag_match = re.search(r'(\[.*?\])', old_name)
            flag = flag_match.group(1) if flag_match else "[🏳️]"
            
            # ساخت نام جدید و کدگذاری آن برای URL
            new_name_encoded = urllib.parse.quote(f"{flag} {NEW_CONFIG_NAME}")
            
            return f"{base_config}#{new_name_encoded}"

    except Exception as e:
        print(f"[!] خطا در پردازش کانفیگ: {config_str[:30]}... | خطا: {e}")
        return None

def scrape_configs():
    """
    این تابع وظیفه اصلی پیمایش صفحات تلگرام و استخراج کانفیگ‌ها را بر عهده دارد.
    """
    configs = []
    next_page_url = TELEGRAM_CHANNEL_URL

    while next_page_url and len(configs) < MAX_CONFIGS:
        print(f"[*] در حال دریافت صفحه: {next_page_url}")
        try:
            response = requests.get(next_page_url, headers=HEADERS, timeout=20)
            response.raise_for_status()  # بررسی موفقیت درخواست
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # پیدا کردن تمام متن پیام‌ها
            messages = soup.find_all("div", class_="tgme_widget_message_text")
            
            for msg in messages:
                text = msg.get_text('\n')
                # پیدا کردن تمام لینک‌های کانفیگ در متن پیام
                found_links = re.findall(r'(vmess|vless|trojan|ss)://[^\s\'"<>]+', text)
                
                for link in found_links:
                    processed = process_config(link)
                    if processed:
                        configs.append(processed)
                    if len(configs) >= MAX_CONFIGS:
                        break
                if len(configs) >= MAX_CONFIGS:
                    break
            
            # پیدا کردن لینک صفحه بعدی (پست‌های قدیمی‌تر)
            more_posts_link = soup.find('a', class_='tgme_widget_message_more')
            if more_posts_link and 'href' in more_posts_link.attrs:
                next_page_url = "https://t.me" + more_posts_link['href']
            else:
                next_page_url = None # اگر صفحه بعدی وجود نداشت، حلقه تمام می‌شود
                
        except requests.exceptions.RequestException as e:
            print(f"[!] خطا در اتصال به تلگرام: {e}")
            break # در صورت خطا در اتصال، عملیات متوقف می‌شود

    return list(dict.fromkeys(configs))[:MAX_CONFIGS]

def main():
    """
    تابع اصلی برنامه
    """
    print("--- شروع اسکریپت آپدیت کانفیگ V2Ray ---")
    
    try:
        final_configs = scrape_configs()
        print(f"[+] تعداد {len(final_configs)} کانفیگ منحصر به فرد یافت شد.")

        if final_configs:
            # اتصال کانفیگ‌ها با خط جدید و کدگذاری Base64
            subscription_content = "\n".join(final_configs)
            encoded_content = base64.b64encode(subscription_content.encode('utf-8')).decode('utf-8')
        else:
            # پیام خطا در صورت عدم یافتن کانفیگ
            error_message = "⚠️ هیچ کانفیگ معتبری یافت نشد."
            encoded_content = base64.b64encode(error_message.encode('utf-8')).decode('utf-8')
            print(f"[!] {error_message}")

    except Exception as e:
        # پیام خطا در صورت بروز مشکل کلی در اسکریپت
        error_message = f"⚠️ خطا در اجرای اسکریپت: {e}"
        encoded_content = base64.b64encode(error_message.encode('utf-8')).decode('utf-8')
        print(f"[!] {error_message}")

    # ذخیره محتوای نهایی در فایل sub.txt
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(encoded_content)
    
    print("--- عملیات با موفقیت انجام شد. فایل sub.txt به‌روز شد. ---")


if __name__ == "__main__":
    main()
    
