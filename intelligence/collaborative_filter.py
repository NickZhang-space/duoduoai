"""
协同过滤推荐模块
基于用户行为的简单协同过滤算法
"""
import math
from typing import Dict, List, Tuple
from collections import defaultdict

class CollaborativeFilter:
    """协同过滤推荐引擎"""
    
    def __init__(self):
        # 用户-商品矩阵 {user_id: {product_id: rating}}
        self.user_item_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
        # 商品信息 {product_id: product_info}
        self.products: Dict[str, Dict] = {}
        
        # 初始化模拟数据
        self._init_mock_data()
    
    def _init_mock_data(self):
        """初始化模拟数据"""
        # 模拟商品
        categories = ["数码配件", "服装", "食品", "家居", "美妆"]
        for i in range(1, 51):
            self.products[f"P{i}"] = {
                "id": f"P{i}",
                "name": f"商品{i}",
                "category": categories[i % len(categories)],
                "price": round(10 + (i * 3.5), 1),
                "rating": round(4.0 + (i % 10) * 0.1, 1)
            }
        
        # 模拟用户行为数据
        import random
        for user_id in range(1, 21):
            uid = str(user_id)
            # 每个用户随机浏览/购买10-20个商品
            num_items = random.randint(10, 20)
            items = random.sample(list(self.products.keys()), num_items)
            for item in items:
                # 评分1-5
                self.user_item_matrix[uid][item] = random.randint(1, 5)
    
    def add_behavior(self, user_id: str, product_id: str, rating: float):
        """添加用户行为"""
        self.user_item_matrix[user_id][product_id] = rating
    
    def cosine_similarity(self, user1: str, user2: str) -> float:
        """计算两个用户的余弦相似度"""
        items1 = set(self.user_item_matrix.get(user1, {}).keys())
        items2 = set(self.user_item_matrix.get(user2, {}).keys())
        
        # 共同评分的商品
        common_items = items1 & items2
        
        if not common_items:
            return 0.0
        
        # 计算余弦相似度
        numerator = sum(
            self.user_item_matrix[user1][item] * self.user_item_matrix[user2][item]
            for item in common_items
        )
        
        sum1 = sum(self.user_item_matrix[user1][item] ** 2 for item in items1)
        sum2 = sum(self.user_item_matrix[user2][item] ** 2 for item in items2)
        
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def find_similar_users(self, user_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """找到最相似的N个用户"""
        similarities = []
        
        for other_user in self.user_item_matrix.keys():
            if other_user != user_id:
                sim = self.cosine_similarity(user_id, other_user)
                if sim > 0:
                    similarities.append((other_user, sim))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]
    
    def recommend(self, user_id: str, top_n: int = 10) -> List[Dict]:
        """为用户推荐商品"""
        # 如果用户不存在，返回热门商品
        if user_id not in self.user_item_matrix:
            return self._get_popular_products(top_n)
        
        # 找到相似用户
        similar_users = self.find_similar_users(user_id, top_n=5)
        
        if not similar_users:
            return self._get_popular_products(top_n)
        
        # 用户已经交互过的商品
        user_items = set(self.user_item_matrix[user_id].keys())
        
        # 候选商品及其加权评分
        candidate_scores = defaultdict(float)
        candidate_weights = defaultdict(float)
        
        for similar_user, similarity in similar_users:
            for item, rating in self.user_item_matrix[similar_user].items():
                if item not in user_items:
                    candidate_scores[item] += similarity * rating
                    candidate_weights[item] += similarity
        
        # 计算加权平均分
        recommendations = []
        for item, score in candidate_scores.items():
            if item in self.products:
                weighted_score = score / candidate_weights[item] if candidate_weights[item] > 0 else 0
                product = self.products[item].copy()
                product["recommendation_score"] = round(weighted_score, 2)
                product["reason"] = "基于相似用户喜好"
                recommendations.append(product)
        
        # 按推荐分数排序
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return recommendations[:top_n]
    
    def _get_popular_products(self, top_n: int = 10) -> List[Dict]:
        """获取热门商品（冷启动）"""
        products = list(self.products.values())
        # 按评分排序
        products.sort(key=lambda x: x["rating"], reverse=True)
        
        result = []
        for p in products[:top_n]:
            product = p.copy()
            product["recommendation_score"] = p["rating"]
            product["reason"] = "热门商品"
            result.append(product)
        
        return result
    
    def get_user_stats(self, user_id: str) -> Dict:
        """获取用户统计信息"""
        if user_id not in self.user_item_matrix:
            return {
                "user_id": user_id,
                "total_items": 0,
                "avg_rating": 0,
                "favorite_category": "未知"
            }
        
        user_data = self.user_item_matrix[user_id]
        ratings = list(user_data.values())
        
        # 统计最喜欢的类目
        category_count = defaultdict(int)
        for item_id in user_data.keys():
            if item_id in self.products:
                category = self.products[item_id]["category"]
                category_count[category] += 1
        
        favorite_category = max(category_count.items(), key=lambda x: x[1])[0] if category_count else "未知"
        
        return {
            "user_id": user_id,
            "total_items": len(user_data),
            "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
            "favorite_category": favorite_category,
            "categories": dict(category_count)
        }
