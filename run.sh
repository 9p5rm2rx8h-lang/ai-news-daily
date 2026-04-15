#!/bin/bash
# 每日新闻简报启动脚本

cd /workspace/news-briefing
python3 main.py >> /workspace/news-briefing/logs/briefing.log 2>&1
