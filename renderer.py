"""简报生成 — 将新闻数据渲染为 HTML 邮件"""

from __future__ import annotations

from datetime import datetime

from fetcher import NewsItem


def _stock_arrow(change_pct: float) -> str:
    if change_pct > 0:
        return "🔴"
    elif change_pct < 0:
        return "🟢"
    return "⚪"


def _format_price(price: float, currency: str) -> str:
    if currency == "HKD":
        return f"HK${price:.2f}"
    elif currency == "CNY":
        return f"¥{price:.2f}"
    return f"{currency} {price:.2f}"


def render_news_section(category: str, items: list[NewsItem]) -> str:
    if not items:
        return f"""
        <div class="category">
            <h2>{category}</h2>
            <p class="empty">今日暂无相关新闻</p>
        </div>
        """

    news_rows = ""
    for i, item in enumerate(items, 1):
        summary_html = ""
        if item.summary:
            summary_html = f'<p class="summary">{item.summary}</p>'
        source_tag = f'<span class="source">{item.source}</span>'
        news_rows += f"""
        <div class="news-item">
            <div class="news-title">
                <span class="idx">{i}.</span>
                <a href="{item.link}" target="_blank">{item.title}</a>
                {source_tag}
            </div>
            {summary_html}
        </div>
        """

    return f"""
    <div class="category">
        <h2>{category}</h2>
        {news_rows}
    </div>
    """


def render_stock_section(stocks: list[dict]) -> str:
    if not stocks:
        return ""

    rows = ""
    for s in stocks:
        arrow = _stock_arrow(s["change_pct"])
        price_str = _format_price(s["price"], s.get("currency", "HKD"))
        change_str = f'{s["change"]:+.2f} ({s["change_pct"]:+.2f}%)'
        error_note = ""
        if s.get("error"):
            error_note = f' <span class="error">（数据获取失败）</span>'
        rows += f"""
        <tr>
            <td class="stock-name">{arrow} {s["name"]}</td>
            <td class="stock-symbol">{s["symbol"]}</td>
            <td class="stock-price">{price_str}</td>
            <td class="stock-change {'up' if s['change_pct'] > 0 else 'down' if s['change_pct'] < 0 else ''}">{change_str}</td>
            <td>{error_note}</td>
        </tr>
        """

    return f"""
    <div class="category">
        <h2>📊 关注股票</h2>
        <table class="stock-table">
            <thead>
                <tr><th>名称</th><th>代码</th><th>现价</th><th>涨跌</th><th></th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """


def generate_html(news_data: dict[str, list[NewsItem]], stocks: list[dict]) -> str:
    """生成完整的 HTML 邮件"""
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]

    # 新闻板块
    news_sections = ""
    category_emojis = {"海外热点": "🌍", "AI": "🤖", "科技": "💻", "3D打印": "🖨️"}
    for cat, items in news_data.items():
        emoji = category_emojis.get(cat, "📰")
        news_sections += render_news_section(f"{emoji} {cat}", items)

    # 股票板块
    stock_section = render_stock_section(stocks)

    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #f5f5f5;
    margin: 0;
    padding: 20px;
    color: #333;
    line-height: 1.6;
  }}
  .container {{
    max-width: 720px;
    margin: 0 auto;
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  }}
  .header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white;
    padding: 32px 28px;
    text-align: center;
  }}
  .header h1 {{
    margin: 0;
    font-size: 24px;
    font-weight: 700;
  }}
  .header .date {{
    margin-top: 8px;
    font-size: 14px;
    opacity: 0.8;
  }}
  .content {{
    padding: 24px 28px;
  }}
  .category {{
    margin-bottom: 28px;
  }}
  .category h2 {{
    font-size: 17px;
    font-weight: 600;
    color: #1a1a2e;
    border-bottom: 2px solid #e8e8e8;
    padding-bottom: 8px;
    margin-bottom: 14px;
  }}
  .news-item {{
    margin-bottom: 12px;
    padding: 8px 0;
    border-bottom: 1px solid #f0f0f0;
  }}
  .news-item:last-child {{
    border-bottom: none;
  }}
  .news-title {{
    font-size: 14px;
  }}
  .news-title .idx {{
    color: #999;
    margin-right: 4px;
  }}
  .news-title a {{
    color: #1a1a2e;
    text-decoration: none;
    font-weight: 500;
  }}
  .news-title a:hover {{
    color: #0f3460;
    text-decoration: underline;
  }}
  .news-title .source {{
    font-size: 11px;
    background: #f0f0f5;
    color: #666;
    padding: 1px 6px;
    border-radius: 3px;
    margin-left: 8px;
  }}
  .summary {{
    font-size: 13px;
    color: #666;
    margin: 4px 0 0 20px;
    line-height: 1.5;
  }}
  .empty {{
    color: #999;
    font-size: 13px;
    font-style: italic;
  }}
  .stock-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}
  .stock-table th {{
    text-align: left;
    padding: 8px 6px;
    border-bottom: 2px solid #e8e8e8;
    color: #666;
    font-weight: 500;
  }}
  .stock-table td {{
    padding: 8px 6px;
    border-bottom: 1px solid #f0f0f0;
  }}
  .stock-name {{
    font-weight: 500;
  }}
  .stock-symbol {{
    color: #999;
    font-size: 12px;
  }}
  .stock-price {{
    font-weight: 500;
  }}
  .stock-change.up {{
    color: #e74c3c;
  }}
  .stock-change.down {{
    color: #2ecc71;
  }}
  .error {{
    color: #e74c3c;
    font-size: 12px;
  }}
  .footer {{
    text-align: center;
    padding: 20px;
    font-size: 12px;
    color: #999;
    border-top: 1px solid #f0f0f0;
  }}
  .footer a {{
    color: #0f3460;
    text-decoration: none;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📰 每日新闻简报</h1>
    <div class="date">{date_str} {weekday}</div>
  </div>
  <div class="content">
    {news_sections}
    {stock_section}
  </div>
  <div class="footer">
    本简报由自动化系统生成 · 新闻版权归原作者所有
  </div>
</div>
</body>
</html>
    """
    return html.strip()
