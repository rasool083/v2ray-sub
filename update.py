import feedparser
import re

rss_url = "https://rsshub.app/telegram/channel/ConfigsHubPlus"
feed = feedparser.parse(rss_url)

with open("sub.txt", "w", encoding="utf-8") as f:
    count = 0
    for entry in feed.entries:
        text = entry.get("title", "") + " " + entry.get("description", "")
        configs = re.findall(r'(?:vmess|vless|trojan|ss)://[^\s\'"]+', text)
        for cfg in configs:
            f.write(cfg.strip() + "\n")
            count += 1
            if count >= 400:
                break
        if count >= 400:
            break
