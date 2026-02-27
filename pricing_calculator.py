from pydantic import BaseModel
from typing import Optional

class PricingCalculator:
    """定价计算器"""
    
    @staticmethod
    def calculate_price(cost: float, target_margin: float, shipping: float = 0) -> dict:
        """
        计算建议售价
        
        Args:
            cost: 成本价
            target_margin: 目标毛利率（0-1之间，如0.4表示40%）
            shipping: 运费
        
        Returns:
            包含建议售价、利润等信息的字典
        """
        if cost <= 0:
            return {"error": "成本价必须大于0"}
        
        if target_margin < 0 or target_margin >= 1:
            return {"error": "毛利率必须在0-100%之间"}
        
        # 计算售价
        base_price = cost / (1 - target_margin)
        final_price = base_price + shipping
        
        # 计算利润
        profit = final_price - cost - shipping
        actual_margin = profit / final_price if final_price > 0 else 0
        
        # 建议定价（尾数优化）
        suggested_prices = []
        
        # 方案1：原价
        suggested_prices.append({
            "name": "标准定价",
            "price": round(final_price, 2),
            "display_price": f"{round(final_price, 2):.2f}元",
            "profit": round(profit, 2),
            "margin": f"{actual_margin * 100:.1f}%"
        })
        
        # 方案2：尾数.9
        price_9 = int(final_price) + 0.9
        profit_9 = price_9 - cost - shipping
        margin_9 = profit_9 / price_9 if price_9 > 0 else 0
        suggested_prices.append({
            "name": "心理定价（.9）",
            "price": price_9,
            "display_price": f"{price_9:.1f}元",
            "profit": round(profit_9, 2),
            "margin": f"{margin_9 * 100:.1f}%",
            "reason": "消费者心理：59.9元比60元更便宜"
        })
        
        # 方案3：尾数.99
        price_99 = int(final_price) + 0.99
        profit_99 = price_99 - cost - shipping
        margin_99 = profit_99 / price_99 if price_99 > 0 else 0
        suggested_prices.append({
            "name": "促销定价（.99）",
            "price": price_99,
            "display_price": f"{price_99:.2f}元",
            "profit": round(profit_99, 2),
            "margin": f"{margin_99 * 100:.1f}%",
            "reason": "适合促销活动"
        })
        
        # 方案4：整数定价
        price_round = round(final_price / 10) * 10
        if price_round < final_price:
            price_round += 10
        profit_round = price_round - cost - shipping
        margin_round = profit_round / price_round if price_round > 0 else 0
        suggested_prices.append({
            "name": "整数定价",
            "price": price_round,
            "display_price": f"{price_round:.0f}元",
            "profit": round(profit_round, 2),
            "margin": f"{margin_round * 100:.1f}%",
            "reason": "简洁大方，适合高端产品"
        })
        
        return {
            "success": True,
            "cost": cost,
            "shipping": shipping,
            "target_margin": f"{target_margin * 100:.0f}%",
            "suggested_prices": suggested_prices,
            "tips": [
                "建议选择.9或.99结尾的价格，更容易成交",
                "定价要参考竞品，不能过高或过低",
                "新品可以适当降低利润率，先打开市场",
                "爆款可以适当提高价格，提升利润"
            ]
        }
    
    @staticmethod
    def compare_with_competitors(your_price: float, competitor_prices: list) -> dict:
        """
        与竞品价格对比
        
        Args:
            your_price: 你的定价
            competitor_prices: 竞品价格列表
        
        Returns:
            对比分析结果
        """
        if not competitor_prices:
            return {"error": "请至少输入一个竞品价格"}
        
        avg_price = sum(competitor_prices) / len(competitor_prices)
        min_price = min(competitor_prices)
        max_price = max(competitor_prices)
        
        # 判断你的定价位置
        if your_price < min_price:
            position = "最低价"
            suggestion = "价格过低，可能影响利润。建议适当提高。"
        elif your_price > max_price:
            position = "最高价"
            suggestion = "价格过高，可能影响销量。建议适当降低。"
        elif your_price < avg_price:
            position = "低于平均价"
            suggestion = "价格有竞争力，适合快速打开市场。"
        elif your_price > avg_price:
            position = "高于平均价"
            suggestion = "价格偏高，需要突出产品优势。"
        else:
            position = "平均价"
            suggestion = "价格适中，可以尝试差异化竞争。"
        
        return {
            "success": True,
            "your_price": your_price,
            "competitor_avg": round(avg_price, 2),
            "competitor_min": min_price,
            "competitor_max": max_price,
            "position": position,
            "suggestion": suggestion,
            "price_difference": {
                "vs_avg": f"{((your_price - avg_price) / avg_price * 100):.1f}%",
                "vs_min": f"{((your_price - min_price) / min_price * 100):.1f}%",
                "vs_max": f"{((your_price - max_price) / max_price * 100):.1f}%"
            }
        }
    
    @staticmethod
    def calculate_profit_scenarios(cost: float, shipping: float, prices: list) -> dict:
        """
        计算不同定价下的利润情况
        
        Args:
            cost: 成本
            shipping: 运费
            prices: 不同的定价方案
        
        Returns:
            各方案的利润对比
        """
        scenarios = []
        
        for price in prices:
            profit = price - cost - shipping
            margin = profit / price if price > 0 else 0
            
            scenarios.append({
                "price": price,
                "profit": round(profit, 2),
                "margin": f"{margin * 100:.1f}%",
                "monthly_revenue_100": round(price * 100, 2),  # 月销100件
                "monthly_profit_100": round(profit * 100, 2)
            })
        
        return {
            "success": True,
            "scenarios": scenarios,
            "note": "假设月销100件的情况"
        }
