# 📰 每日新闻简报

自动化新闻简报系统，每天早晨 7:00 抓取新闻并发送到邮箱。

## 覆盖分类

| 分类 | 来源 |
|------|------|
| 🌍 海外热点 | Google News、Al Jazeera、Reuters、BBC、AP News |
| 🤖 AI | The Verge AI、TechCrunch AI、MIT Tech Review、AI News |
| 💻 科技 | Hacker News、The Verge、Ars Technica、Engadget |
| 🖨️ 3D打印 | 3D Printing Industry、All3DP、3DPrint.com、Hackaday |
| 📊 关注股票 | 腾讯(0700.HK)、泡泡玛特(9992.HK)、茅台(600519.SS)、中国神华(601088.SS) |

## 快速配置

### 1. 配置邮箱

编辑 `.env` 文件：

```bash
# QQ 邮箱配置
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=你的QQ号@qq.com
SMTP_PASSWORD=你的授权码    # 不是QQ密码！在 QQ邮箱→设置→账户→生成授权码
RECIPIENT=你的QQ号@qq.com   # 收件地址
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 手动运行一次（测试）

```bash
python main.py
```

### 4. 设置定时任务

```bash
# 方法一：crontab
crontab -e
# 添加以下行（每天7:00执行）：
0 7 * * * cd /workspace/news-briefing && python3 main.py >> logs/briefing.log 2>&1

# 方法二：使用 run.sh
0 7 * * * /workspace/news-briefing/run.sh
```

## 项目结构

```
news-briefing/
├── main.py            # 主程序入口
├── config.py          # 配置管理
├── fetcher.py         # 新闻抓取 + 股票查询
├── renderer.py        # HTML 简报渲染
├── mailer.py          # 邮件发送
├── run.sh             # cron 启动脚本
├── archive/           # 每日简报 HTML 备份
├── logs/              # 运行日志
├── .env.example       # 配置模板
└── requirements.txt   # Python 依赖
```

## QQ 邮箱授权码获取

1. 登录 [QQ 邮箱](https://mail.qq.com)
2. 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
3. 开启 IMAP/SMTP 服务
4. 点击"生成授权码"，按提示用手机发送短信
5. 获得的16位授权码填入 `.env` 的 `SMTP_PASSWORD`

## 自定义

- **添加新闻源**：编辑 `fetcher.py` 的 `RSS_SOURCES` 字典
- **添加股票**：编辑 `fetcher.py` 的 `STOCK_SYMBOLS` 字典
- **修改简报样式**：编辑 `renderer.py`
- **每类新闻条数**：修改 `.env` 中的 `MAX_NEWS_PER_CATEGORY`
