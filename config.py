"""配置管理"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # 邮件
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.qq.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    RECIPIENT: str = os.getenv("RECIPIENT", "")

    # 新闻
    MAX_NEWS_PER_CATEGORY: int = int(os.getenv("MAX_NEWS_PER_CATEGORY", "8"))

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # 时区
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Shanghai")


settings = Settings()
