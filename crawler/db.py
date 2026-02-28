"""
数据库操作模块
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from .config import DB_PATH


class CrawlerDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 类目趋势数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS category_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                product_name TEXT,
                price REAL,
                sales_count INTEGER,
                shop_name TEXT,
                product_url TEXT,
                goods_id TEXT,
                crawl_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 竞品快照表
        cursor.execute('''
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
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_trends_category_date 
            ON category_trends(category, crawl_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_snapshots_goods_date 
            ON crawler_competitor_snapshots(goods_id, snapshot_date)
        ''')
        
        conn.commit()
        conn.close()
    
    def save_category_trend(self, data: Dict):
        """保存类目趋势数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO category_trends 
            (category, product_name, price, sales_count, shop_name, product_url, goods_id, crawl_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('category'),
            data.get('product_name'),
            data.get('price'),
            data.get('sales_count'),
            data.get('shop_name'),
            data.get('product_url'),
            data.get('goods_id'),
            datetime.now().date()
        ))
        
        conn.commit()
        conn.close()
    
    def save_competitor_snapshot(self, data: Dict):
        """保存竞品快照"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO crawler_competitor_snapshots 
            (competitor_id, goods_id, product_name, price, original_price, 
             sales_count, review_count, rating, coupon_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('competitor_id'),
            data.get('goods_id'),
            data.get('product_name'),
            data.get('price'),
            data.get('original_price'),
            data.get('sales_count'),
            data.get('review_count'),
            data.get('rating'),
            data.get('coupon_info')
        ))
        
        conn.commit()
        conn.close()
    
    def get_category_trends(self, category: str, days: int = 7) -> List[Dict]:
        """获取类目趋势数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM category_trends 
            WHERE category = ? 
            AND crawl_date >= date('now', '-' || ? || ' days')
            ORDER BY crawl_date DESC, sales_count DESC
        ''', (category, days))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_competitor_snapshots(self, goods_id: str, days: int = 30) -> List[Dict]:
        """获取竞品快照历史"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM crawler_competitor_snapshots 
            WHERE goods_id = ? 
            AND snapshot_date >= datetime('now', '-' || ? || ' days')
            ORDER BY snapshot_date DESC
        ''', (goods_id, days))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
