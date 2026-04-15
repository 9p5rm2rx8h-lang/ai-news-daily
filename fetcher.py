"""新闻抓取模块 — 多源多分类"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

import feedparser
import requests
from bs4 import BeautifulSoup

from config import settings


@dataclass
class NewsItem:
    title: str
    link: str
    source: str
    summary: str = ""
    published: str = ""
    category: str = ""


# ===== RSS 源配置 =====

RSS_SOURCES = {
    "海外热点": [
        {"name": "Google News World", "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en&gl=US&ceid=US:en", "lang": "en"},
        {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "lang": "en"},
        {"name": "Reuters World", "url": "https://feeds.reuters.com/reuters/worldNews", "lang": "en"},
        {"name": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "lang": "en"},
        {"name": "RSSHub World", "url": "https://rsshub.app/apnews/topics/world-news", "lang": "en"},
    ],
    "AI": [
        {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "lang": "en"},
        {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "lang": "en"},
        {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/", "lang": "en"},
        {"name": "AI News", "url": "https://rsshub.app/ainews", "lang": "en"},
        {"name": "Artificial Intelligence News", "url": "https://artificialintelligence-news.com/feed/", "lang": "en"},
    ],
    "科技": [
        {"name": "Hacker News", "url": "https://hnrss.org/frontpage", "lang": "en"},
        {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "lang": "en"},
        {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "lang": "en"},
        {"name": "Engadget", "url": "https://www.engadget.com/rss.xml", "lang": "en"},
    ],
    "3D打印": [
        {"name": "3D Printing Industry", "url": "https://3dprintingindustry.com/feed/", "lang": "en"},
        {"name": "All3DP", "url": "https://all3dp.com/feed/", "lang": "en"},
        {"name": "3DPrint.com", "url": "https://3dprint.com/feed/", "lang": "en"},
        {"name": "Hackaday 3D", "url": "https://hackaday.com/tag/3d-printing/feed/", "lang": "en"},
    ],
}

# 股票关注列表
STOCK_SYMBOLS = {
    "腾讯": "0700.HK",
    "泡泡玛特": "9992.HK",
    "茅台": "600519.SS",
    "中国神华": "601088.SS",
}


def _fetch_rss(url: str, source_name: str, category: str, max_items: int = 10) -> list[NewsItem]:
    """抓取单个 RSS 源"""
    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_items]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue
            summary = entry.get("summary", "")
            # 清理 HTML 标签
            if summary:
                soup = BeautifulSoup(summary, "lxml")
                summary = soup.get_text()[:300].strip()
            published = entry.get("published", "") or entry.get("updated", "")
            items.append(NewsItem(
                title=title,
                link=link,
                source=source_name,
                summary=summary,
                published=published,
                category=category,
            ))
    except Exception as e:
        print(f"  ⚠️  RSS 抓取失败 [{source_name}]: {e}")
    return items


def fetch_category_news(category: str, sources: list[dict]) -> list[NewsItem]:
    """抓取某分类下所有源的新闻"""
    all_items = []
    max_per_source = max(3, settings.MAX_NEWS_PER_CATEGORY // len(sources))
    for src in sources:
        print(f"  📡 抓取: {src['name']} ({src['url'][:50]}...)")
        items = _fetch_rss(src["url"], src["name"], category, max_items=max_per_source)
        all_items.extend(items)
        time.sleep(0.5)  # 礼貌性延迟
    # 去重（按标题相似度）
    seen_titles = set()
    unique = []
    for item in all_items:
        key = re.sub(r"\s+", "", item.title.lower())[:40]
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(item)
    return unique[:settings.MAX_NEWS_PER_CATEGORY]


def fetch_all_rss_news() -> dict[str, list[NewsItem]]:
    """抓取所有分类的 RSS 新闻"""
    results = {}
    for category, sources in RSS_SOURCES.items():
        print(f"\n📁 分类: {category}")
        items = fetch_category_news(category, sources)
        results[category] = items
        print(f"  ✅ 获取 {len(items)} 条")
    return results


# ===== 股市数据 =====

def fetch_stock_data() -> list[dict]:
    """通过 Yahoo Finance 抓取股票行情"""
    stocks = []
    for name, symbol in STOCK_SYMBOLS.items():
        print(f"  📈 查询: {name} ({symbol})")
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            result = data["chart"]["result"][0]
            meta = result["meta"]

            current = meta.get("regularMarketPrice", 0)
            prev = meta.get("chartPreviousClose", 0) or meta.get("previousClose", 0)
            change = current - prev
            change_pct = (change / prev * 100) if prev else 0
            currency = meta.get("currency", "HKD")

            stocks.append({
                "name": name,
                "symbol": symbol,
                "price": current,
                "change": change,
                "change_pct": change_pct,
                "currency": currency,
            })
        except Exception as e:
            print(f"  ⚠️  股票查询失败 [{name}]: {e}")
            stocks.append({
                "name": name,
                "symbol": symbol,
                "price": 0,
                "change": 0,
                "change_pct": 0,
                "currency": "--",
                "error": str(e),
            })
        time.sleep(0.3)
    return stocks
