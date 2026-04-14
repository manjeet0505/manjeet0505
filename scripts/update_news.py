import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ── Sources (no API key needed) ────────────────────────────────────────────────
FEEDS = [
    {
        "name": "Hacker News · AI",
        "url": "https://hnrss.org/newest?q=artificial+intelligence+OR+LLM+OR+ChatGPT&count=4&points=50",
    },
    {
        "name": "MIT Tech Review · AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    },
    {
        "name": "VentureBeat · AI",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
]

NAMESPACES = {"dc": "http://purl.org/dc/elements/1.1/"}


def fetch_feed(url: str, max_items: int = 3) -> list[dict]:
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            tree = ET.parse(resp)
        root = tree.getroot()

        # handle Atom vs RSS
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        for item in root.iter(f"{ns}item"):
            title_el = item.find(f"{ns}title")
            link_el  = item.find(f"{ns}link")
            if title_el is None or link_el is None:
                continue
            title = (title_el.text or "").strip()
            link  = (link_el.text  or "").strip()
            if title and link:
                items.append({"title": title[:90] + ("…" if len(title) > 90 else ""), "link": link})
            if len(items) >= max_items:
                break
    except Exception as e:
        print(f"  ⚠  Feed error ({url[:60]}…): {e}")
    return items


def build_news_block(all_items: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%b %d, %Y — %H:%M UTC")
    rows = ""
    for i, item in enumerate(all_items[:7], 1):
        rows += f"| {i} | {item['title']} | [→ Read]({item['link']}) |\n"

    return f"""<!-- AI_NEWS_START -->
## 🤖 Daily AI News  <sub>— auto-updated every morning</sub>

> 🕐 Last refreshed: **{now}**

| # | 📰 Headline | 🔗 |
|---|------------|-----|
{rows.rstrip()}

<sub>Powered by GitHub Actions · Sources: Hacker News, MIT Tech Review, VentureBeat</sub>

<!-- AI_NEWS_END -->"""


def update_readme(block: str, path: str = "README.md") -> None:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"<!-- AI_NEWS_START -->.*?<!-- AI_NEWS_END -->"
    if re.search(pattern, content, re.DOTALL):
        updated = re.sub(pattern, block, content, flags=re.DOTALL)
    else:
        # append before the footer wave if present, else at end
        footer_marker = '<img width="100%" src="https://capsule-render'
        if footer_marker in content:
            updated = content.replace(footer_marker, block + "\n---\n\n" + footer_marker, 1)
        else:
            updated = content + "\n\n" + block

    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)
    print("✅ README.md updated successfully!")


if __name__ == "__main__":
    print("🔍 Fetching AI news feeds…")
    all_items: list[dict] = []
    for feed in FEEDS:
        print(f"  → {feed['name']}")
        all_items.extend(fetch_feed(feed["url"], max_items=3))
        if len(all_items) >= 7:
            break

    if not all_items:
        print("⚠  No items fetched — keeping existing README unchanged.")
    else:
        print(f"✅ Collected {len(all_items)} headlines")
        block = build_news_block(all_items)
        update_readme(block)