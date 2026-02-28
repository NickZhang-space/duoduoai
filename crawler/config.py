"""
爬虫配置文件
"""

# 请求配置
REQUEST_TIMEOUT = 10  # 请求超时时间（秒）
REQUEST_DELAY_MIN = 3  # 最小请求间隔（秒）
REQUEST_DELAY_MAX = 5  # 最大请求间隔（秒）

# User-Agent 列表（移动端）
USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/95.0.4638.50 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-A505FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 11; Redmi Note 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.62 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 13_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 9; SAMSUNG SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.0 Chrome/87.0.4280.141 Mobile Safari/537.36',
]

# 拼多多配置
PDD_MOBILE_BASE = 'https://mobile.yangkeduo.com'
PDD_SEARCH_API = f'{PDD_MOBILE_BASE}/proxy/api/search'
PDD_GOODS_URL = f'{PDD_MOBILE_BASE}/goods.html'

# 爬取配置
CATEGORY_CRAWL_LIMIT = 50  # 每个类目爬取商品数量
COMPETITOR_CRAWL_TIMES = 2  # 每天爬取竞品次数（早晚各一次）

# 类目关键词映射
CATEGORY_KEYWORDS = {
    '美妆': ['面膜', '口红', '护肤品', '化妆品'],
    '服饰': ['连衣裙', 'T恤', '牛仔裤', '运动鞋'],
    '食品': ['零食', '坚果', '饼干', '巧克力'],
    '家居': ['收纳盒', '拖鞋', '毛巾', '床上用品'],
    '数码': ['数据线', '充电宝', '耳机', '手机壳'],
    '母婴': ['奶粉', '纸尿裤', '婴儿衣服', '玩具'],
}

# 数据库配置
DB_PATH = '/root/ecommerce-ai-v2/crawler/crawler.db'

# 代理配置（预留）
USE_PROXY = False  # MVP 阶段不使用代理
PROXY_API_URL = None  # 芝麻代理 API（预留）
