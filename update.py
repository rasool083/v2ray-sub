import requests
import re
import base64
from bs4 import BeautifulSoup

url = "https://t.me/s/ConfigsHubPlus"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# پیدا کردن تمام پیام‌ها
messages = soup.find_all("div", class_="tgme_widget_message_text")

configs = []
for msg in messages:
    text = msg.get_text()
    found = re.findall(r'(?:vmess|vless|trojan|ss)://[^\s\'"]+', text)
    configs.extend(found)
    if len(configs) >= 400:
        break

# اگر کانفیگ پیدا شد → base64 رمزگذاری کن
if configs:
    joined = '\n'.join(configs[:400])
    encoded = base64.b64encode(joined.encode('utf-8')).decode('utf-8')
else:
    encoded = base64.b64encode("No configs found".encode('utf-8')).decode('utf-8')

# ذخیره در فایل
with open("sub.txt", "w", encoding="utf-8") as f:
    f.write(encoded)
