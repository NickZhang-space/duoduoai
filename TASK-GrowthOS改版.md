# TASK: PDD GrowthOS 全面改版

## 背景
当前产品"多多AI优化师"定位偏工具后台，需要升级为 **PDD GrowthOS** — 投放+运营+AI闭环的一体化产品。

## 目标
把现有网站从"普通工具页"改成品牌化产品，覆盖搜索推广+全站/场景，核心呈现4大能力。

## 产品定位
**PDD GrowthOS** — 拼多多投放与运营一体的 AI 优化师
- 不是报表工具，不是聊天机器人
- 是"诊断→动作→执行→复盘"的闭环系统

## 4大核心能力（必须在UI中清晰呈现）
1. **数据统一** — 搜索/全站/场景统一指标口径
2. **诊断系统** — 自动判断问题出在哪（流量/承接/价格/人群/预算）
3. **动作系统** — 优化建议变成可执行的改动清单
4. **执行闭环** — 人审一键执行 → 跟踪效果 → 自动复盘

## 改版范围

### A. 首页改版（index.html）— 最高优先级
现状：普通登录引导页，没有产品说服力
目标：品牌化产品介绍页，先打动用户再转化

必须包含：
- A1: 首屏 Hero — 大标题"PDD GrowthOS"，副标题说清价值，CTA按钮
- A2: 4大能力展示区 — 图标+标题+描述，一眼看懂产品
- A3: 功能亮点区 — 搜索推广优化 + 全站/场景优化 + 运营策略，三栏并列
- A4: AI 工作流展示 — 诊断师→策略师→执行（三步流程图）
- A5: 定价区 — 免费/基础¥49/专业¥129
- A6: 底部 CTA — 立即开始免费试用
- 配色：主色 #E84D1A（拼多多橙），辅色深蓝 #1a1a2e，白底卡片
- 字体：大标题粗体，正文 16px，行高 1.6
- 移动端适配必须做

### B. 登录页改版（login.html）
- 左侧品牌区（GrowthOS logo + slogan + 特性列表）
- 右侧登录表单
- 整体风格与首页统一

### C. 应用主页改版（app.html）— 信息架构重组
现状：标签页太多太杂，没有主次
目标：按 MVP 5大核心入口重组

新的导航结构：
1. 📊 **数据总览** — 搜索/全站分开看 + 总体利润ROI（整合现有 dashboard）
2. 🔍 **诊断中心** — 亏损雷达 Top5 拖累项 + 钻取到词/人群/商品（整合现有分析功能）
3. 🚀 **增长机会** — 放量清单 Top5 可扩量项 + 扩量路径（整合现有推荐功能）
4. 🤖 **AI 建议** — 今日 3-10 条动作卡片 + 一键生成执行方案（整合现有 AI 中心）
5. ⚙️ **设置** — 店铺管理/通知设置/套餐/自动化规则

每个入口点进去是完整的功能页面，不是简单标签切换。

### C1: 动作卡片设计（AI建议页核心组件）
每张卡片包含：
- 动作类型图标（调预算/调出价/否词/换素材等）
- 问题描述（一句话说清问题）
- 建议动作（具体怎么改）
- 预期效果（改了会怎样）
- 风险等级（低/中/高，用颜色标识）
- 观察窗口（改动后看多久验证）
- [执行] [忽略] [稍后] 三个按钮

### C2: 诊断卡片设计（诊断中心核心组件）
- 指标异常高亮（红色下降/绿色上升）
- 问题归因链路（CTR低 → 主图点击率差 → 建议方向）
- 影响排名（Top 3 拖累项）
- 钻取按钮（查看详情）

### D. 全局 UI 升级
- D1: 统一配色方案（#E84D1A 主色 + #1a1a2e 深色 + #f8f9fa 背景）
- D2: 卡片组件统一（圆角 12px，阴影 0 2px 8px rgba(0,0,0,0.08)）
- D3: 按钮样式统一（主按钮橙色，次按钮描边，hover 过渡动画）
- D4: 图标系统（用 emoji 或 SVG，保持一致）
- D5: 移动端全面适配（768px/480px 断点）

## 执行顺序（严格按此顺序）
1. A1-A6（首页）→ commit
2. B（登录页）→ commit
3. D1-D5（全局UI）→ commit
4. C（app.html 信息架构重组）→ commit
5. C1-C2（动作卡片+诊断卡片）→ commit

## ⛔ 铁律（违反任何一条立刻停止）

1. **每个功能独立 commit**，commit message 用中文说清改了什么
2. **改任何文件前先 `cp file file.bak`**
3. **绝对不用 sed 做多行插入**，用 Python 脚本或直接写完整文件
4. **不动 main.py 的任何路由逻辑**，只改前端文件
5. **不动 intelligence_api.py**
6. **不动 database.py**
7. **不删除任何现有 API 端点**
8. **app.html 修改后必须验证**：
   - HTML div 嵌套深度检查（所有 section depth=2）
   - JS 括号匹配检查（braces/parens/brackets 全部=0）
   - 没有压缩代码行（单行不超过 500 字符）
9. **崩溃 3 次就停止，写报告等人来看**
10. **不要生成压缩/minified 代码**，所有代码必须可读
11. **每完成一个阶段，用 verify.py 跑一次验证**

## 验证脚本（每阶段必跑）
```bash
# 1. 服务是否正常
curl -s -o /dev/null -w "%{http_code}" http://localhost:80/ | grep 200

# 2. 登录页
curl -s -o /dev/null -w "%{http_code}" http://localhost:80/static/login.html | grep 200

# 3. app页
curl -s -o /dev/null -w "%{http_code}" http://localhost:80/static/app.html | grep 200

# 4. API 健康
curl -s -o /dev/null -w "%{http_code}" http://localhost:80/api/intelligence/health | grep 200

# 5. HTML 结构检查
python3 -c "
import re
html = open('/root/ecommerce-ai-v2/static/app.html').read()
depth = 0
for m in re.finditer(r'<(/?)div', html):
    if m.group(1) == '': depth += 1
    else: depth -= 1
print(f'Final div depth: {depth}')
assert depth == 0, 'DIV NOT BALANCED!'
print('HTML structure OK')
"

# 6. JS 括号检查
python3 -c "
import re
html = open('/root/ecommerce-ai-v2/static/app.html').read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
js = '\n'.join(scripts)
# 去掉字符串和注释
js = re.sub(r'\"(?:[^\"\\\\]|\\\\.)*\"', '', js)
js = re.sub(r\"'(?:[^'\\\\\\\\]|\\\\\\\\.)*'\", '', js)
js = re.sub(r'//[^\n]*', '', js)
js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
b = js.count('{') - js.count('}')
p = js.count('(') - js.count(')')
s = js.count('[') - js.count(']')
print(f'Braces: {b}, Parens: {p}, Brackets: {s}')
assert b == 0 and p == 0 and s == 0, 'JS BRACKETS NOT BALANCED!'
print('JS brackets OK')
"

# 7. 长行检查
python3 -c "
lines = open('/root/ecommerce-ai-v2/static/app.html').readlines()
bad = [(i+1, len(l)) for i, l in enumerate(lines) if len(l) > 500]
if bad:
    print(f'WARNING: {len(bad)} lines > 500 chars: {bad[:5]}')
else:
    print('No long lines OK')
"
```

## 备份信息
- Git tag: `v2.2-pre-growthOS-20260302`
- 目录备份: `/root/ecommerce-ai-v2-backup-20260302/`
- 回滚: `cd /root/ecommerce-ai-v2 && git checkout v2.2-pre-growthOS-20260302`

## 交付要求
完成后写一份 `CHANGELOG-GrowthOS.md`，包含：
1. 每个 commit 的改动说明（人话版）
2. 新的页面结构说明
3. 已知问题/未完成项
4. 验证结果截图/日志
