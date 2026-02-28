"""
动态定价引擎
根据市场数据和用户目标，智能推荐最优价格
"""

import statistics
from typing import Dict, List, Optional


class DynamicPricingEngine:
    """动态定价引擎"""
    
    def __init__(self):
        pass
    
    async def suggest_price(self, product: Dict, market_data: Dict, user_goal: str = 'balanced') -> Dict:
        """
        智能定价建议
        
        Args:
            product: 产品信息 {id, name, cost, price, historical_sales}
            market_data: 市场数据 {competitors: [{name, price, sales}]}
            user_goal: 定价目标 (balanced/maximize_profit/maximize_sales)
        
        Returns:
            定价建议 {suggested_price, reasoning, prediction}
        """
        
        # 1. 成本底线（至少10%利润）
        cost = product.get('cost', 0)
        cost_floor = cost * 1.1
        
        # 2. 市场价格分析
        competitors = market_data.get('competitors', [])
        competitor_prices = [c['price'] for c in competitors if 'price' in c]
        
        if not competitor_prices:
            # 没有竞品数据，使用成本加成
            suggested_price = cost_floor * 1.5
            market_stats = None
        else:
            market_stats = {
                'mean': statistics.mean(competitor_prices),
                'median': statistics.median(competitor_prices),
                'std': statistics.stdev(competitor_prices) if len(competitor_prices) > 1 else 0,
                'q25': self._percentile(competitor_prices, 25),
                'q75': self._percentile(competitor_prices, 75),
                'min': min(competitor_prices),
                'max': max(competitor_prices)
            }
            
            # 3. 根据目标计算最优价格
            if user_goal == 'maximize_profit':
                # 利润最大化：定价略高于中位数
                suggested_price = market_stats['median'] * 1.05
            elif user_goal == 'maximize_sales':
                # 销量最大化：定价略低于25分位
                suggested_price = market_stats['q25'] * 0.95
            else:  # balanced
                # 平衡策略：市场中位数
                suggested_price = market_stats['median']
        
        # 4. 确保不低于成本
        final_price = max(suggested_price, cost_floor)
        
        # 5. 预测效果
        prediction = await self._predict_outcome(final_price, market_data, product)
        
        # 6. 计算市场位置
        if competitor_prices:
            position_percentile = sum(1 for p in competitor_prices if p > final_price) / len(competitor_prices) * 100
        else:
            position_percentile = 50
        
        # 7. 计算变化
        current_price = product.get('price', 0)
        change_amount = final_price - current_price
        change_percent = (change_amount / current_price * 100) if current_price > 0 else 0
        
        return {
            'suggested_price': round(final_price, 2),
            'current_price': current_price,
            'change_amount': round(change_amount, 2),
            'change_percent': round(change_percent, 1),
            'market_position': f"低于{position_percentile:.0f}%的竞品",
            'predicted_sales': prediction['sales'],
            'predicted_profit': prediction['profit'],
            'predicted_roi': prediction['roi'],
            'confidence': prediction['confidence'],
            'reasoning': self._explain_pricing(final_price, market_stats, user_goal, cost_floor)
        }
    
    async def simulate_price(self, product: Dict, price: float, market_data: Dict) -> Dict:
        """
        价格模拟
        
        Args:
            product: 产品信息
            price: 模拟价格
            market_data: 市场数据
        
        Returns:
            预测结果 {sales, revenue, profit, roi}
        """
        return await self._predict_outcome(price, market_data, product)
    
    async def _predict_outcome(self, price: float, market_data: Dict, product: Dict) -> Dict:
        """预测定价效果"""
        # 基础销量
        base_sales = product.get('historical_sales', 100)
        cost = product.get('cost', 0)
        
        competitors = market_data.get('competitors', [])
        
        if competitors:
            # 计算平均竞品价格
            competitor_prices = [c['price'] for c in competitors if 'price' in c]
            if competitor_prices:
                avg_competitor_price = statistics.mean(competitor_prices)
                price_ratio = price / avg_competitor_price
                
                # 价格越低，销量越高（简化的需求曲线）
                # 价格比竞品低10%，销量增加15%
                sales_multiplier = 1.5 - price_ratio * 0.5
                sales_multiplier = max(0.5, min(2.0, sales_multiplier))  # 限制在0.5-2.0之间
            else:
                sales_multiplier = 1.0
        else:
            sales_multiplier = 1.0
        
        # 预测销量
        predicted_sales = int(base_sales * sales_multiplier)
        
        # 预测收益
        predicted_revenue = predicted_sales * price
        predicted_cost = predicted_sales * cost
        predicted_profit = predicted_revenue - predicted_cost
        predicted_roi = (predicted_profit / predicted_cost) if predicted_cost > 0 else 0
        
        # 置信度（基于数据完整性）
        confidence = 0.7
        if competitors:
            confidence = min(0.9, 0.7 + len(competitors) * 0.02)
        
        return {
            'sales': predicted_sales,
            'revenue': round(predicted_revenue, 2),
            'profit': round(predicted_profit, 2),
            'roi': round(predicted_roi, 2),
            'confidence': confidence
        }
    
    def _explain_pricing(self, price: float, market_stats: Optional[Dict], goal: str, cost_floor: float) -> List[str]:
        """解释定价逻辑"""
        reasons = []
        
        reasons.append(f"成本底线：¥{cost_floor:.2f}（成本+10%利润）")
        
        if market_stats:
            reasons.append(f"市场均价：¥{market_stats['mean']:.2f}")
            reasons.append(f"市场中位数：¥{market_stats['median']:.2f}")
            
            if goal == 'maximize_profit':
                reasons.append("策略：利润最大化，定价略高于市场中位数")
            elif goal == 'maximize_sales':
                reasons.append("策略：销量最大化，定价低于市场25分位")
            else:
                reasons.append("策略：平衡策略，定价接近市场中位数")
        else:
            reasons.append("无竞品数据，使用成本加成定价（50%加成）")
        
        return reasons
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        index = max(0, min(index, len(sorted_data) - 1))
        return sorted_data[index]
