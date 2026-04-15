"""新闻抓取模块 — 多源多分类"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

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

# 关注的公司/关键词（用于搜索相关新闻）
WATCHED_COMPANIES = {
    "腾讯": ["Tencent", "腾讯"],
    "泡泡玛特": ["Pop Mart", "泡泡玛特", "9992.HK"],
    "茅台": ["Moutai", "Kweichow Moutai", "茅台", "600519.SS"],
    "中国神华": ["China Shenhua Energy", "中国神华", "601088.SS"],
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
            if summary:
                soup = BeautifulSoup(summary, "lxml")
                summary = soup.get_text()[:300].strip()
            published = entry.get("published", "") or entry.get("updated", "")
            items.append(NewsItem(
                title=title, link=link, source=source_name,
                summary=summary, published=published, category=category,
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
        time.sleep(0.5)
    # 去重
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


# ===== 关注公司相关新闻 =====

def _search_google_news(keywords: list[str], max_results: int = 5) -> list[NewsItem]:
    """通过 Google News RSS 搜索特定关键词的相关新闻"""
    items = []
    query = " ".join(keywords)
    # URL 编码
    encoded_query = requests.utils.quote(query)
    
    # 尝试多个 Google News 搜索源
    urls = [
        f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en",
        f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    ]
    
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_results]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or not link:
                    continue
                # 去掉 Google 重定向链接
                if "&url=" in link:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(link)
                    qs = parse_qs(parsed.query)
                    if "url" in qs:
                        link = qs["url"][0]

                summary = entry.get("summary", "")
                if summary:
                    soup = BeautifulSoup(summary, "lxml")
                    summary = soup.get_text()[:200].strip()

                published = entry.get("published", "")
                
                # 标记来源为 Google News
                source_tag = entry.get("source", {}).get("title", "") if isinstance(entry.get("source"), dict) else ""
                source = source_tag or "Google News"
                
                items.append(NewsItem(
                    title=title, link=link, source=source,
                    summary=summary, published=published,
                    category="关注动态",
                ))
            
            if items:
                break  # 成功获取到结果就不再尝试下一个源
                
        except Exception as e:
            print(f"    ⚠️ 搜索失败: {e}")
            continue
    
    return items


def fetch_company_news() -> dict[str, list[NewsItem]]:
    """搜索所有关注公司的相关新闻"""
    all_company_news = {}  # 公司名称 → 新闻列表
    total = 0
    
    for company_name, keywords in WATCHED_COMPANIES.items():
        print(f"  🔍 搜索 [{company_name}] 相关新闻 (关键词: {keywords})")
        
        # 先搜英文关键词，再搜中文关键词
        en_keywords = [k for k in keywords if all(ord(c) < 128 for c in k)]
        zh_keywords = [k for k in keywords if any(ord(c) > 128 for c in k)]
        
        items = []
        
        # 英文搜索
        if en_keywords:
            items.extend(_search_google_news(en_keywords, max_results=4))
            time.sleep(0.5)
        
        # 中文搜索
        if zh_keywords:
            items.extend(_search_google_news(zh_keywords, max_results=4))
            time.sleep(0.5)
        
        # 去重
        seen_titles = set()
        unique = []
        for item in items:
            key = re.sub(r"\s+", "", item.title.lower())[:40]
            if key not in seen_titles:
                seen_titles.add(key)
                unique.append(item)
        
        all_company_news[company_name] = unique[:8]  # 每个公司最多8条
        total += len(unique)
        print(f"    ✅ 找到 {len(unique)} 条")
    
    print(f"\n📊 公司相关新闻总计: {total} 条")
    return all_company_news
