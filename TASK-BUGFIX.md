# 紧急任务：app.html 全面质量检查与修复

## 背景
你之前做的 Phase 2 合并留下了一堆结构性问题，小牛马已经修了一部分，但需要你做全面检查。

## 已修复的问题（不要重复改）
1. ✅ HTML section 嵌套深度 — 所有 section 已统一在 depth=2
2. ✅ switchSmartTab tabMap 缺 daily-report 和 market-insights
3. ✅ switchSmartTab(market-insights) 缺引号
4. ✅ switchTab 缺 AB测试加载触发
5. ✅ 风险预警标签页碎片重组
6. ✅ iframe 套娃 bug（tutorials/pricing/dashboard 返回按钮）
7. ✅ 行3152 压缩代码导致 JS 括号不匹配（已删除）

## 你的任务：全面检查 app.html

### 1. JS 语法检查
- 确认所有 `<script>` 块的括号 `{}()[]` 完全匹配
- 检查是否还有压缩成一行的代码块（你之前的习惯），如果有且和正常代码重复，删掉
- 确认所有 function 定义完整，没有被截断

### 2. HTML 结构检查
- 用脚本验证所有 `<div>` 开闭标签匹配
- 确认 13 个 section 全部在 depth=2（和 body 的关系）
- 检查是否有孤立的 HTML 碎片（之前风险卡片被拆成两半的情况）

### 3. 功能逐项测试
用 curl 测试以下 API，确认全部返回正常：
```bash
# 先登录获取 token
TOKEN=$(curl -s -X POST http://localhost/api/auth/login -H 'Content-Type: application/json' -d '{"email":"jinmeijiangcuo@gmail.com","password":"Feng15846572185@"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')

# 核心 API
curl -s http://localhost/api/dashboard-stats -H "Authorization: Bearer $TOKEN"
curl -s http://localhost/api/competitors -H "Authorization: Bearer $TOKEN"
curl -s http://localhost/api/notifications?user_id=1 -H "Authorization: Bearer $TOKEN"
curl -s http://localhost/api/ab-test/list?user_id=1
curl -s http://localhost/api/intelligence/recommendations/1
curl -s http://localhost/api/intelligence/daily-report/1
curl -s http://localhost/api/intelligence/risk-assessment/1
curl -s http://localhost/api/market/insights?category=数码配件
curl -s http://localhost/api/market/trends?category=数码配件
curl -s http://localhost/api/shop -H "Authorization: Bearer $TOKEN"
```

### 4. 前端标签页检查
确认以下标签页切换后能正确显示内容（不是空白）：
- AI选品、投流优化、定价计算、历史记录、新手教程
- 🏪 我的店铺、🎯 竞品跟踪、🧪 A/B测试
- ⚡ 自动化、🔔 通知设置、套餐升级
- 🤖 AI中心（含子标签：推荐/趋势/问答/风险预警/市场洞察/日报）

### 5. 检查 static/js/ 外部 JS 文件
- ab_test.js — 确认 loadExperiments 等函数完整
- 其他 js 文件如果有的话也检查

## 重要规则
- **改之前必须 `cp app.html app.html.bak` 备份！**
- **不要用 sed 做多行修改！** 用 python 脚本精确替换
- **每修一个问题单独 git commit**，不要一口气改完
- **改完跑一遍括号匹配检查**确认没搞坏
- 如果发现问题但不确定怎么修，先报告不要动

## 验证脚本（改完必跑）
```python
import re
with open('/root/ecommerce-ai-v2/static/app.html', 'r') as f:
    content = f.read()

# 1. JS 括号检查
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
assert b == 0 and p == 0 and k == 0, f'JS括号不匹配! {b} {p} {k}'

# 2. Section depth 检查
lines = content.split('\n')
depth = 0
in_body = False
for i, line in enumerate(lines, 1):
    if '<body' in line: in_body = True
    if in_body:
        opens = line.count('<div')
        closes = line.count('</div')
        if 'class="section"' in line:
            assert depth == 2, f'Line {i}: section at depth {depth}, expected 2'
        depth += opens - closes

print('ALL CHECKS PASSED ✅')
```

## 当前代码位置
- 服务器：香港 43.129.205.237
- 代码：/root/ecommerce-ai-v2/
- 分支：master
- 最新 commit：0baee7f
