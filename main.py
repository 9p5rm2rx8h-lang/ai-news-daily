"""新闻简报主程序"""

from datetime import datetime

from config import settings
from fetcher import fetch_all_rss_news, fetch_company_news
from mailer import send_email
from renderer import generate_html
from translator import translate_news


def run():
    """执行一次新闻简报生成和发送"""
    now = datetime.now()
    print(f"{'='*50}")
    print(f"📰 新闻简报生成 — {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    # 1. 抓取 RSS 新闻
    print("\n📡 开始抓取新闻...")
    news_data = fetch_all_rss_news()

    total = sum(len(v) for v in news_data.values())
    print(f"\n📊 新闻总计: {total} 条")
    for cat, items in news_data.items():
        print(f"   {cat}: {len(items)} 条")

    # 2. 翻译为中文（如果配置了 OpenAI）
    if settings.OPENAI_API_KEY:
        print("\n🌐 翻译为中文...")
        news_data = translate_news(news_data)

    # 3. 搜索关注公司相关新闻
    print("\n🏢 搜索关注公司动态...")
    company_news = fetch_company_news()
    
    # 翻译公司相关新闻
    if settings.OPENAI_API_KEY:
        # 把公司新闻也翻译
        for company_name, items in company_news.items():
            if items:
                company_news[company_name] = translate_news({company_name: items})[company_name]

    # 4. 生成 HTML
    print("\n🎨 生成简报...")
    html = generate_html(news_data, company_news)

    # 保存到本地（备份）
    backup_path = f"/workspace/news-briefing/archive/briefing_{now.strftime('%Y%m%d')}.html"
    try:
        import os
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"💾 简报已保存: {backup_path}")
    except Exception as e:
        print(f"⚠️  保存备份失败: {e}")

    # 5. 发送邮件
    date_str = now.strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]
    subject = f"📰 每日新闻简报 — {date_str} {weekday}"

    success = send_email(subject, html)

    if success:
        print(f"\n🎉 简报已成功发送！")
    else:
        print(f"\n⚠️  简报发送失败，可查看本地备份: {backup_path}")

    return success


if __name__ == "__main__":
    run()
