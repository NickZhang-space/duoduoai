# 通宵任务：UI优化 + 爬虫MVP

## ⚠️ 铁律（违反任何一条就停下来）

1. **每改一个功能必须单独 git commit + 测试**，绝对不能一口气改完
2. **改任何文件前必须 `cp file file.bak` 备份**
3. **不要用 sed 做多行修改**，用 python 脚本精确替换
4. **不要动 main.py 的现有路由**，只能新增文件或新增路由
5. **每次 commit 后跑验证脚本**（见底部）
6. **app.html 改完必须跑 JS 括号检查和 div depth 检查**
7. **如果服务崩了超过3次，立刻停下来，不要继续改**
8. **改完一个任务就 git push origin master**

## 安全回滚
- Tag: `v2.1-pre-overnight-20260301`（今晚开始前的状态）
- 备份: `/root/ecommerce-ai-v2-backup-20260301-0156/`
- 如果搞砸了: `cd /root/ecommerce-ai-v2 && git checkout v2.1-pre-overnight-20260301 -- .`

## 服务器信息
- 香港: 43.129.205.237, 密码 Feng15846572185@
- 代码: /root/ecommerce-ai-v2/
- 服务: systemctl restart ecommerce-ai
- Python 3.11.6, 无 node

---

## 任务A：UI优化（优先级高，先做这个）

### A1. 空状态优化
现在很多页面数据为空时显示很丑。优化以下空状态：
- 竞品追踪：空列表时显示引导（"添加第一个竞品，开始监控价格变动"）
- AB测试：空列表时显示引导（"创建第一个实验，用数据驱动决策"）
- 市场洞察：首次加载时自动触发数据加载，不要显示空白
- 每日报告：如果没有报告，显示"暂无报告，系统将在每日自动生成"

### A2. Loading 状态
所有数据加载时显示 loading 动画，不要显示空白或"加载中..."纯文字：
```html
<div class="loading-spinner">
    <div style="width:40px;height:40px;border:4px solid #f3f3f3;border-top:4px solid #E84D1A;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto;"></div>
    <p style="margin-top:10px;color:#999;">加载中...</p>
</div>
```
在 app.html 的 `<style>` 里加 `@keyframes spin { 0%{transform:rotate(0)} 100%{transform:rotate(360deg)} }`

### A3. 首页数据概览卡片
登录后默认显示的选品页面太空。在顶部加一个欢迎横幅：
- 显示用户名、套餐类型、今日分析次数
- 快捷入口按钮：AI选品、投流优化、竞品追踪、市场洞察

### A4. 通知铃铛
通知按钮点击后弹出的面板，加载真实通知数据（调 /api/notifications）

### A5. 移动端细节
- 标签栏在手机上可横向滚动
- 模态框在手机上全屏显示
- 表单输入框字体不小于16px（防iOS缩放）

**每完成一个 A1-A5，单独 commit + push**

---

## 任务B：爬虫MVP（任务A做完再做这个）

### 重要：爬虫代码全部放在新目录 `/root/ecommerce-ai-v2/crawler/`，不要动现有代码！

### B1. 创建爬虫目录结构
```
crawler/
├── __init__.py
├── config.py          # 配置（代理、频率、UA列表）
├── pdd_search.py      # 拼多多搜索页爬虫（类目趋势）
├── pdd_product.py     # 拼多多商品详情爬虫（竞品监控）
├── proxy_pool.py      # 代理池管理
├── db.py              # SQLite 数据库操作
├── scheduler.py       # 定时任务调度
└── run.py             # 入口脚本
```

### B2. 类目趋势爬虫 (pdd_search.py)
- 爬拼多多移动端搜索接口（比PC端反爬弱）
- URL: `https://mobile.yangkeduo.com/proxy/api/search`
- 或者爬拼多多 H5 页面
- 提取：商品名、价格、销量、店铺名、类目
- 每个类目每天爬一次，每次50-100个商品
- 请求间隔 3-5 秒随机
- UA 轮换（准备10个移动端 UA）

### B3. 竞品商品监控 (pdd_product.py)
- 爬拼多多商品详情页
- URL: `https://mobile.yangkeduo.com/goods.html?goods_id=xxx`
- 提取：价格、销量、评价数、评分、优惠券
- 每个监控商品每天爬2次（早晚各一次）
- 数据存入 competitor_snapshots 表

### B4. 代理池 (proxy_pool.py)
- MVP 先不用付费代理，直接用香港服务器 IP
- 如果被封，加一个简单的免费代理获取（从 free-proxy-list 抓）
- 预留付费代理接口（芝麻代理 API）

### B5. 数据库 (db.py)
```sql
-- 类目趋势数据
CREATE TABLE IF NOT EXISTS category_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    product_name TEXT,
    price REAL,
    sales_count INTEGER,
    shop_name TEXT,
    product_url TEXT,
    crawl_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 竞品快照（复用现有 competitor_snapshots 表结构）
CREATE TABLE IF NOT EXISTS crawler_competitor_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id INTEGER,
    goods_id TEXT,
    product_name TEXT,
    price REAL,
    original_price REAL,
    sales_count INTEGER,
    review_count INTEGER,
    rating REAL,
    coupon_info TEXT,
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trends_category_date ON category_trends(category, crawl_date);
CREATE INDEX IF NOT EXISTS idx_snapshots_goods_date ON crawler_competitor_snapshots(goods_id, snapshot_date);
```

### B6. 与现有系统集成（最后做）
- 在 main.py 里**只新增**两个 API：
  - `GET /api/market/real-data?category=xxx` — 返回爬虫采集的真实类目数据
  - `GET /api/competitor/real-snapshots?goods_id=xxx` — 返回真实竞品快照
- 前端市场洞察页面调用新 API 替换模拟数据
- **不要改现有的 /api/market/insights 等路由**，新增路由并行存在

### B7. 定时任务
```bash
# 类目趋势：每天凌晨3点爬
0 3 * * * cd /root/ecommerce-ai-v2 && python3 -m crawler.run --task=trends >> /var/log/crawler-trends.log 2>&1

# 竞品监控：每天8点和20点爬
0 8,20 * * * cd /root/ecommerce-ai-v2 && python3 -m crawler.run --task=competitors >> /var/log/crawler-competitors.log 2>&1
```

**每完成 B1-B7 中的一个，单独 commit + push**

---

## 验证脚本（每次 commit 前必跑）

```python
import re, subprocess

# 1. 服务是否正常
result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost/static/app.html'], capture_output=True, text=True)
assert result.stdout == '200', f'Service down! HTTP {result.stdout}'

# 2. JS 括号检查
with open('/root/ecommerce-ai-v2/static/app.html', 'r') as f:
    content = f.read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
combined = '\n'.join(scripts)
b, p, k = 0, 0, 0
for ch in combined:
    if ch == '{': b += 1
    elif ch == '}': b -= 1
    elif ch == '(': p += 1
    elif ch == ')': p -= 1
    elif ch == '[': k += 1
    elif ch == ']': k -= 1
assert b == 0 and p == 0 and k == 0, f'JS brackets mismatch! {{ {b}, ( {p}, [ {k}'

# 3. Section depth
lines = content.split('\n')
depth = 0
in_body = False
for i, line in enumerate(lines, 1):
    if '<body' in line: in_body = True
    if in_body:
        depth += line.count('<div') - line.count('</div')
        if 'class="section"' in line:
            assert depth - (line.count('<div') - line.count('</div')) == 2, f'L{i}: section depth wrong'

# 4. 核心 API
import urllib.request, json
apis = ['/static/app.html', '/api/health', '/api/ab-test/list?user_id=1']
for api in apis:
    try:
        r = urllib.request.urlopen(f'http://localhost{api}')
        assert r.status == 200, f'{api} returned {r.status}'
    except Exception as e:
        print(f'WARNING: {api} failed: {e}')

print('ALL CHECKS PASSED ✅')
```

保存为 `/root/ecommerce-ai-v2/scripts/verify.py`，每次 commit 前跑 `python3 scripts/verify.py`

---

## 工作顺序
1. A1 → commit → push → verify
2. A2 → commit → push → verify
3. A3 → commit → push → verify
4. A4 → commit → push → verify
5. A5 → commit → push → verify
6. B1 → commit → push
7. B2 → commit → push → 手动测试爬虫
8. B3 → commit → push → 手动测试爬虫
9. B4 → commit → push
10. B5 → commit → push
11. B6 → commit → push → verify（改了前端）
12. B7 → 配置 crontab → commit → push

**预计总工时：4-6小时**
