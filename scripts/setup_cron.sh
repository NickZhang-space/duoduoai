#!/bin/bash
# 设置爬虫定时任务

# 创建日志目录
mkdir -p /var/log/crawler

# 添加 crontab 任务
(crontab -l 2>/dev/null | grep -v 'ecommerce-ai-v2.*crawler'; cat << CRON
# 类目趋势爬虫：每天凌晨3点
0 3 * * * cd /root/ecommerce-ai-v2 && /usr/bin/python3 -m crawler.run --task=trends >> /var/log/crawler/trends.log 2>&1

# 竞品监控爬虫：每天8点和20点
0 8,20 * * * cd /root/ecommerce-ai-v2 && /usr/bin/python3 -m crawler.run --task=competitors >> /var/log/crawler/competitors.log 2>&1
CRON
) | crontab -

echo '✓ Crontab 任务已配置'
crontab -l | grep crawler
