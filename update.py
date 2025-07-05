import requests
import re
import base64
from bs4 import BeautifulSoup

base_url = "https://t.me/s/ConfigsHubPlus"
max_pages = 30
max_configs = 400
configs = []

# شروع از آخرین پست کانال (با آخرین عدد شناخته‌شده)
current_msg_id = 91436

for _ in range(max_pages):
    url = f"{base_url}?before={current_msg_id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    messages = soup.find_all("div", class_="tgme_widget_message_text")
    if not messages:
        break

    for msg in messages:
        text = msg.get_text()
        found = re.findall(r'(?:vmess|vless|trojan|ss)://[^\s\'"]+', text)
        configs.extend(found)
        if len(configs) >= max_configs:
            break
    if len(configs) >= max_configs:
        break

    # کاهش ID برای رفتن به صفحه قبل
    current_msg_id -= 20  # تقریباً 20 پیام در هر صفحه

# حذف تکراری‌ها و آماده‌سازی خروجی
unique_configs = list(dict.fromkeys(configs))[:max_configs]
if unique_configs:
    joined = '\n'.join(unique_configs)
    encoded = base64.b64encode(joined.encode('utf-8')).decode('utf-8')
else:
    encoded = base64.b64encode("No configs found".encode('utf-8')).decode('utf-8')

with open("sub.txt", "w", encoding="utf-8") as f:
    f.write(encoded)
