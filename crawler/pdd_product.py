"""
拼多多商品详情爬虫 - 竞品监控
"""
import requests
import random
import time
import re
import json
from typing import List, Dict, Optional
from .config import (
    USER_AGENTS, REQUEST_TIMEOUT, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX,
    PDD_GOODS_URL
)
from .db import CrawlerDB
from .proxy_pool import ProxyPool


class PDDProductCrawler:
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
            'Referer': 'https://mobile.yangkeduo.com/',
        }
    
    def crawl_product(self, goods_id: str, competitor_id: Optional[int] = None) -> Optional[Dict]:
        """
        爬取商品详情
        """
        try:
            url = f'{PDD_GOODS_URL}?goods_id={goods_id}'
            
            print(f'正在爬取商品: {goods_id}')
            
            response = self.session.get(
                url,
                headers=self.get_headers(),
                timeout=REQUEST_TIMEOUT,
                proxies=self.proxy_pool.get_proxy()
            )
            
            if response.status_code != 200:
                print(f'请求失败: {response.status_code}')
                return None
            
            # 解析商品数据
            product_data = self._parse_product(response.text, goods_id, competitor_id)
            
            if product_data:
                # 保存到数据库
                self.db.save_competitor_snapshot(product_data)
                print(f'  - {product_data["product_name"]}: ¥{product_data["price"]}, 销量 {product_data["sales_count"]}')
                return product_data
            
            # 随机延迟
            time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
            
        except Exception as e:
            print(f'爬取商品失败 {goods_id}: {e}')
        
        return None
    
    def _parse_product(self, html: str, goods_id: str, competitor_id: Optional[int]) -> Optional[Dict]:
        """
        解析商品详情（简化版）
        实际需要根据拼多多页面结构调整
        """
        try:
            # 提取商品名称
            name_match = re.search(r'<title>(.*?)</title>', html)
            product_name = name_match.group(1) if name_match else f'商品{goods_id}'
            
            # 提取价格（多种可能的格式）
            price_patterns = [
                r'"price"\s*:\s*"?(\d+\.?\d*)"?',
                r'"minOnSaleGroupPrice"\s*:\s*"?(\d+\.?\d*)"?',
                r'[¥￥](\d+\.?\d*)',
            ]
            price = None
            for pattern in price_patterns:
                price_match = re.search(pattern, html)
                if price_match:
                    price = float(price_match.group(1))
                    break
            
            # 提取原价
            original_price_match = re.search(r'"marketPrice"\s*:\s*"?(\d+\.?\d*)"?', html)
            original_price = float(original_price_match.group(1)) if original_price_match else price
            
            # 提取销量
            sales_patterns = [
                r'"salesTip"\s*:\s*"已拼(\d+\.?\d*[万千]?)件"',
                r'已拼(\d+\.?\d*[万千]?)件',
                r'"soldQuantity"\s*:\s*"?(\d+)"?',
            ]
            sales_count = 0
            for pattern in sales_patterns:
                sales_match = re.search(pattern, html)
                if sales_match:
                    sales_count = self._parse_sales(sales_match.group(1))
                    break
            
            # 提取评价数
            review_patterns = [
                r'"reviewNum"\s*:\s*"?(\d+)"?',
                r'(\d+)条评价',
            ]
            review_count = 0
            for pattern in review_patterns:
                review_match = re.search(pattern, html)
                if review_match:
                    review_count = int(review_match.group(1))
                    break
            
            # 提取评分
            rating_match = re.search(r'"avgServeScore"\s*:\s*"?(\d+\.?\d*)"?', html)
            rating = float(rating_match.group(1)) if rating_match else 0.0
            
            # 提取优惠券信息
            coupon_match = re.search(r'券(\d+)元', html)
            coupon_info = f'券{coupon_match.group(1)}元' if coupon_match else None
            
            return {
                'competitor_id': competitor_id,
                'goods_id': goods_id,
                'product_name': product_name.strip(),
                'price': price or 0.0,
                'original_price': original_price or price or 0.0,
                'sales_count': sales_count,
                'review_count': review_count,
                'rating': rating,
                'coupon_info': coupon_info,
            }
            
        except Exception as e:
            print(f'解析商品数据失败: {e}')
            return None
    
    def _parse_sales(self, sales_str: str) -> int:
        """解析销量字符串"""
        try:
            if '万' in sales_str:
                return int(float(sales_str.replace('万', '')) * 10000)
            elif '千' in sales_str:
                return int(float(sales_str.replace('千', '')) * 1000)
            else:
                return int(float(sales_str))
        except:
            return 0
    
    def crawl_competitors_from_db(self):
        """
        从数据库读取竞品列表并爬取
        需要先在主系统中添加竞品
        """
        print('开始爬取竞品数据...')
        
        # 这里需要从主数据库读取竞品列表
        # 暂时使用示例数据
        competitors = [
            {'id': 1, 'goods_id': '123456789'},
            {'id': 2, 'goods_id': '987654321'},
        ]
        
        for comp in competitors:
            self.crawl_product(comp['goods_id'], comp['id'])
        
        print('竞品爬取完成！')


def crawl_competitors():
    """入口函数"""
    crawler = PDDProductCrawler()
    crawler.crawl_competitors_from_db()


if __name__ == '__main__':
    crawl_competitors()
