import requests
import re
import base64
from bs4 import BeautifulSoup

base_url = "https://t.me/s/ConfigsHubPlus"
max_pages = 30
max_configs = 400
configs = []

headers = {
    'User-Agent': 'Mozilla/5.0'
}

def get_latest_post_id():
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        posts = soup.find_all("div", class_="tgme_widget_message_wrap")
        if posts:
            return int(posts[-1]['data-post'].split('/')[-1])
        return 93446
    except Exception as e:
        print(f"[!] خطا در یافتن آخرین شناسه پست: {e}")
        return 93446

try:
    current_msg_id = get_latest_post_id()

    for _ in range(max_pages):
        url = f"{base_url}?before={current_msg_id}"
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        messages = soup.find_all("div", class_="tgme_widget_message_text")
        if not messages:
            break

        for msg in messages:
            text = msg.get_text()
            found = re.findall(r'(?:vmess|vless|trojan|ss)://[^\s\'"<>]+', text)

            updated = []
            for cfg in found:
                try:
                    if cfg.startswith("vmess://"):
                        raw = cfg[8:]
                        padded = raw + '=' * (-len(raw) % 4)
                        decoded = base64.b64decode(padded).decode('utf-8')
                        replaced = decoded.replace("ConfigsHubPlus", "rghoddoosi")
                        recoded = base64.b64encode(replaced.encode('utf-8')).decode('utf-8')
                        cfg = "vmess://" + recoded
                    else:
                        # نام کانفیگ = پرچم + t.me/rghoddoosi + رسول قدوسی
                        flag = ""
                        if "#" in cfg:
                            parts = cfg.split("#", 1)
                            cfg = parts[0]
                            all_tags = parts[1].strip().split()
                            if all_tags:
                                flag = all_tags[0]  # مثلاً 🇫🇮[FI]
                        cfg += f"#{flag} t.me/rghoddoosi رسول قدوسی"
                    updated.append(cfg)
                except Exception as e:
                    print(f"[!] خطا در پردازش کانفیگ: {e}")
                    continue

            configs.extend(updated)
            if len(configs) >= max_configs:
                break

        if len(configs) >= max_configs:
            break

        current_msg_id -= 20

    # حذف کانفیگ‌های تکراری (بر اساس رشته کامل)، فقط 400 عدد
    unique_configs = list(dict.fromkeys(configs))[:max_configs]

    if unique_configs:
        joined = '\n'.join(unique_configs)
        encoded = base64.b64encode(joined.encode('utf-8')).decode('utf-8')
    else:
        encoded = base64.b64encode("⚠️ هیچ کانفیگی یافت نشد".encode('utf-8')).decode('utf-8')

except Exception as e:
    error_message = f"⚠️ خطا در اجرای اسکریپت: {e}"
    encoded = base64.b64encode(error_message.encode('utf-8')).decode('utf-8')
    print(error_message)

# ذخیره در sub.txt فقط محتوای base64
with open("sub.txt", "w", encoding="utf-8") as f:
    f.write(encoded)
