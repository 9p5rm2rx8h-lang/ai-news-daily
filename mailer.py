"""邮件发送模块 — SMTP"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings


def send_email(subject: str, html_body: str) -> bool:
    """发送 HTML 邮件"""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("❌ 邮箱未配置，请在 .env 中设置 SMTP_USER 和 SMTP_PASSWORD")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = settings.RECIPIENT or settings.SMTP_USER

    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)

    try:
        print(f"\n📧 发送邮件: {settings.SMTP_USER} → {msg['To']}")
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, msg["To"], msg.as_string())
        print("✅ 邮件发送成功！")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP 认证失败，请检查邮箱和授权码")
        return False
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False
