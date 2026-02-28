"""
拼多多搜索页爬虫 - 类目趋势
"""
import requests
import random
import time
import re
from typing import List, Dict
from .config import (
    USER_AGENTS, REQUEST_TIMEOUT, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX,
    PDD_MOBILE_BASE, CATEGORY_KEYWORDS, CATEGORY_CRAWL_LIMIT
)
from .db import CrawlerDB
from .proxy_pool import ProxyPool


class PDDSearchCrawler:
    def __init__(self):
        self.db = CrawlerDB()
        self.proxy_pool = ProxyPool()
        self.session = requests.Session()
    
    def get_headers(self) -> Dict:
        """获取随机 User-Agent"""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': PDD_MOBILE_BASE,
        }
    
    def crawl_category(self, category: str, keyword: str) -> List[Dict]:
        """
        爬取指定类目的商品数据
        使用拼多多移动端搜索页面
        """
        results = []
        
        try:
            # 拼多多移动端搜索 URL
            search_url = f'{PDD_MOBILE_BASE}/search_result.html'
            params = {
                'q': keyword,
                'search_met': 'history',
            }
            
            print(f'正在爬取类目: {category}, 关键词: {keyword}')
            
            response = self.session.get(
                search_url,
                params=params,
                headers=self.get_headers(),
                timeout=REQUEST_TIMEOUT,
                proxies=self.proxy_pool.get_proxy()
            )
            
            if response.status_code != 200:
                print(f'请求失败: {response.status_code}')
                return results
            
            # 解析 HTML（简化版，提取关键信息）
            html = response.text
            
            # 使用正则提取商品数据（拼多多页面结构可能变化，这里是示例）
            # 实际需要根据页面结构调整
            products = self._parse_products(html, category)
            
            for product in products[:CATEGORY_CRAWL_LIMIT]:
                # 保存到数据库
                self.db.save_category_trend(product)
                results.append(product)
                print(f'  - {product["product_name"]}: ¥{product["price"]}, 销量 {product["sales_count"]}')
            
            # 随机延迟
            time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
            
        except Exception as e:
            print(f'爬取失败: {category} - {keyword}: {e}')
        
        return results
    
    def _parse_products(self, html: str, category: str) -> List[Dict]:
        """
        解析商品数据（简化版）
        实际需要根据拼多多页面结构调整
        """
        products = []
        
        # 示例：使用正则提取（实际可能需要 BeautifulSoup 或其他解析库）
        # 这里返回模拟数据作为 MVP
        
        # 提取商品 ID（示例正则）
        goods_ids = re.findall(r'goods_id["\']?\s*[:=]\s*["\']?(\d+)', html)
        
        # 提取价格（示例正则）
        prices = re.findall(r'[¥￥](\d+\.?\d*)', html)
        
        # 提取销量（示例正则）
        sales = re.findall(r'(\d+\.?\d*[万千]?)人付款', html)
        
        # 组合数据（简化版）
        for i in range(min(len(goods_ids), len(prices), len(sales), CATEGORY_CRAWL_LIMIT)):
            try:
                sales_count = self._parse_sales(sales[i])
                products.append({
                    'category': category,
                    'goods_id': goods_ids[i],
                    'product_name': f'{category}商品{i+1}',  # 实际需要提取真实名称
                    'price': float(prices[i]),
                    'sales_count': sales_count,
                    'shop_name': f'店铺{i+1}',  # 实际需要提取真实店铺名
                    'product_url': f'{PDD_MOBILE_BASE}/goods.html?goods_id={goods_ids[i]}'
                })
            except Exception as e:
                print(f'解析商品数据失败: {e}')
                continue
        
        return products
    
    def _parse_sales(self, sales_str: str) -> int:
        """解析销量字符串"""
        if '万' in sales_str:
            return int(float(sales_str.replace('万', '')) * 10000)
        elif '千' in sales_str:
            return int(float(sales_str.replace('千', '')) * 1000)
        else:
            return int(float(sales_str))
    
    def crawl_all_categories(self):
        """爬取所有类目"""
        print('开始爬取类目趋势数据...')
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                self.crawl_category(category, keyword)
        
        print('类目趋势爬取完成！')


def crawl_category_trends():
    """入口函数"""
    crawler = PDDSearchCrawler()
    crawler.crawl_all_categories()


if __name__ == '__main__':
    crawl_category_trends()
