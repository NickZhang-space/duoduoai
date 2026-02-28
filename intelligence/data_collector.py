"""
数据采集模块 - 市场数据收集框架
当前使用模拟数据，未来可接入真实数据源
"""
import random
from datetime import datetime, timedelta

class MarketDataCollector:
    """市场数据采集器"""
    
    def get_category_trends(self, category: str) -> dict:
        """获取类目趋势数据"""
        # 模拟数据，未来接真实API
        days = 30
        base_sales = random.randint(5000, 50000)
        trend_data = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d')
            sales = int(base_sales * (1 + random.uniform(-0.15, 0.15)))
            trend_data.append({"date": date, "sales": sales})
        
        return {
            "category": category,
            "period": f"近{days}天",
            "avg_daily_sales": base_sales,
            "trend": "上升" if trend_data[-1]["sales"] > trend_data[0]["sales"] else "下降",
            "daily_data": trend_data,
            "top_products": self._get_top_products(category),
            "price_range": {"min": round(random.uniform(5, 20), 1), "max": round(random.uniform(50, 200), 1)},
            "competition_level": random.choice(["低", "中", "高", "极高"])
        }
    
    def get_competitor_prices(self, product_name: str) -> dict:
        """获取竞品价格数据"""
        competitors = []
        for i in range(5):
            competitors.append({
                "shop_name": f"竞品店铺{i+1}",
                "price": round(random.uniform(10, 100), 1),
                "monthly_sales": random.randint(100, 10000),
                "rating": round(random.uniform(4.0, 5.0), 1),
                "has_coupon": random.choice([True, False])
            })
        return {
            "product": product_name,
            "competitors": sorted(competitors, key=lambda x: x["price"]),
            "avg_price": round(sum(c["price"] for c in competitors) / len(competitors), 1),
            "price_suggestion": round(sum(c["price"] for c in competitors) / len(competitors) * 0.95, 1)
        }
    
    def get_hot_keywords(self, category: str) -> list:
        """获取热门关键词"""
        keywords_pool = {
            "数码配件": ["手机壳", "充电器", "数据线", "耳机", "手机膜", "支架", "充电宝", "蓝牙耳机"],
            "服装": ["T恤", "连衣裙", "牛仔裤", "卫衣", "外套", "短裤", "衬衫", "运动裤"],
            "食品": ["零食", "坚果", "饼干", "巧克力", "牛肉干", "果干", "糕点", "辣条"],
            "家居": ["收纳盒", "垃圾袋", "拖鞋", "毛巾", "抱枕", "地垫", "衣架", "保鲜膜"]
        }
        kws = keywords_pool.get(category, ["热门商品", "爆款", "新品", "特价", "包邮"])
        result = []
        for kw in kws:
            result.append({
                "keyword": kw,
                "search_volume": random.randint(1000, 100000),
                "competition": random.choice(["低", "中", "高"]),
                "avg_cpc": round(random.uniform(0.3, 3.0), 2),
                "trend": random.choice(["上升", "稳定", "下降"])
            })
        return sorted(result, key=lambda x: x["search_volume"], reverse=True)
    
    def _get_top_products(self, category: str) -> list:
        products = []
        for i in range(10):
            products.append({
                "rank": i + 1,
                "name": f"{category}热销商品{i+1}",
                "price": round(random.uniform(10, 200), 1),
                "monthly_sales": random.randint(1000, 50000),
                "rating": round(random.uniform(4.0, 5.0), 1)
            })
        return products
