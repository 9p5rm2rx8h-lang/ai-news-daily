"""翻译模块 — 将英文新闻翻译为中文"""

from __future__ import annotations

import time
from openai import OpenAI

from config import settings


def _translate_batch(texts: list[str]) -> list[str]:
    """批量翻译文本列表（使用 OpenAI）"""
    if not texts or not settings.OPENAI_API_KEY:
        return texts

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    # 构建批量翻译 prompt
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    prompt = f"""将以下英文新闻标题/摘要翻译为中文。要求：
1. 保持专业术语的准确性
2. 保留原文中的专有名词（如人名、公司名、产品名）
3. 只输出编号对应的中文翻译，每行一条，不要添加额外内容
4. 如果原文已经是中文则原样输出

{numbered}"""

    try:
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        result_text = resp.choices[0].message.content.strip()
        lines = [l.strip() for l in result_text.split("\n") if l.strip()]
        
        translations = []
        for line in lines:
            # 去除编号前缀，如 "1. xxx" → "xxx"
            if ". " in line and line.split(". ")[0].strip().isdigit():
                text = line.split(". ", 1)[1]
            else:
                text = line
            translations.append(text)

        # 确保数量一致
        while len(translations) < len(texts):
            translations.append(texts[len(translations)])
        
        return translations[:len(texts)]
    
    except Exception as e:
        print(f"⚠️  翻译失败: {e}")
        return texts


def translate_news(news_data: dict[str, list]) -> dict[str, list]:
    """翻译所有分类的新闻标题和摘要"""
    if not settings.OPENAI_API_KEY:
        print("ℹ️  未配置 OpenAI API Key，跳过翻译")
        return news_data

    translated = {}
    for category, items in news_data.items():
        if not items:
            translated[category] = items
            continue
        
        print(f"  🔄 翻译 [{category}] {len(items)} 条...")
        
        # 收集所有需要翻译的文本
        texts_to_translate = []
        for item in items:
            texts_to_translate.append(item.title)
            texts_to_translate.append(item.summary if item.summary else "")
        
        # 批量翻译
        results = _translate_batch(texts_to_translate)
        
        # 回填翻译结果
        new_items = []
        for idx, item in enumerate(items):
            title_idx = idx * 2
            summary_idx = idx * 2 + 1
            
            new_item = type(item)(
                title=results[title_idx] if title_idx < len(results) else item.title,
                link=item.link,
                source=item.source,
                summary=results[summary_idx].strip() if summary_idx < len(results) and item.summary else item.summary,
                published=item.published,
                category=item.category,
            )
            new_items.append(new_item)
        
        translated[category] = new_items
        time.sleep(0.3)
    
    print("✅ 翻译完成")
    return translated
