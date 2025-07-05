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

# مرحله 1: یافتن شناسه آخرین پست کانال به‌صورت خودکار
def get_latest_post_id():
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    posts = soup.find_all("div", class_="tgme_widget_message_wrap")
    if posts:
        last_post_id = int(posts[-1]['data-post'].split('/')[-1])
        return last_post_id
    return 93446  # مقدار پشتیبان

current_msg_id = get_latest_post_id()

for _ in range(max_pages):
    url = f"{base_url}?before={current_msg_id}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    messages = soup.find_all("div", class_="tgme_widget_message_text")
    if not messages:
        break

    for msg in messages:
        text = msg.get_text()
        found = re.findall(r'(?:vmess|vless|trojan|ss)://[^\s\'"<>]+', text)

        # اصلاح شماره 3: جایگزینی فقط نام "ConfigsHubPlus" با "rghoddoosi"
        updated = []
        for cfg in found:
            # تلاش برای دیکد و جایگزینی داخل فیلد ps
            try:
                if cfg.startswith("vmess://"):
                    raw = cfg[8:]
                    decoded = base64.b64decode(raw + '=' * (-len(raw) % 4)).decode('utf-8')
                    replaced = decoded.replace("ConfigsHubPlus", "rghoddoosi")
                    recoded = base64.b64encode(replaced.encode('utf-8')).decode('utf-8')
                    cfg = "vmess://" + recoded
                else:
                    cfg = cfg.replace("ConfigsHubPlus", "rghoddoosi")
            except Exception:
                pass
            updated.append(cfg)

        configs.extend(updated)

        if len(configs) >= max_configs:
            break

    if len(configs) >= max_configs:
        break

    current_msg_id -= 20  # هر صفحه تقریباً 20 پست عقب‌تر

# حذف تکراری‌ها و کوتاه‌سازی
unique_configs = list(dict.fromkeys(configs))[:max_configs]

# مرحله 2: نوشتن هر کانفیگ در یک خط برای حفظ فرمت
if unique_configs:
    joined = '\n'.join(unique_configs)
    encoded = base64.b64encode(joined.encode('utf-8')).decode('utf-8')
else:
    encoded = base64.b64encode("No configs found".encode('utf-8')).decode('utf-8')

with open("sub.txt", "w", encoding="utf-8") as f:
    f.write(encoded)
