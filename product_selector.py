import os
import json
from typing import Dict, List
from openai import OpenAI
from datetime import datetime
import time

class ProductSelector:
    """拼多多智能选品助手"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        
        # 拼多多热门商品数据
        self.pdd_products = {
            "美妆": [
                {"name": "平价口红套装（5支）", "price_range": "9.9-19.9元", "monthly_sales": "50000-100000", "competition": "高", "profit_margin": "40-50%", "difficulty": "低", "reason": "拼多多价格敏感用户多，走量大"},
                {"name": "面膜大礼包（50片）", "price_range": "19.9-39.9元", "monthly_sales": "60000-120000", "competition": "高", "profit_margin": "45-55%", "difficulty": "低", "reason": "刚需消耗品，复购率极高"},
                {"name": "化妆刷套装", "price_range": "9.9-19.9元", "monthly_sales": "30000-60000", "competition": "中", "profit_margin": "50-60%", "difficulty": "低", "reason": "工具类产品，利润高"},
                {"name": "美妆蛋套装（10个）", "price_range": "5.9-9.9元", "monthly_sales": "40000-80000", "competition": "高", "profit_margin": "55-65%", "difficulty": "低", "reason": "超低价引流款，走量巨大"},
                {"name": "卸妆水/卸妆油", "price_range": "9.9-29.9元", "monthly_sales": "25000-50000", "competition": "中", "profit_margin": "40-50%", "difficulty": "低", "reason": "日常必需品"},
            ],
            "服饰": [
                {"name": "基础款T恤", "price_range": "9.9-19.9元", "monthly_sales": "80000-150000", "competition": "高", "profit_margin": "25-35%", "difficulty": "低", "reason": "价格战激烈，但走量巨大"},
                {"name": "家居服套装", "price_range": "19.9-39.9元", "monthly_sales": "40000-80000", "competition": "中", "profit_margin": "35-45%", "difficulty": "低", "reason": "舒适需求，复购率高"},
                {"name": "儿童服装套装", "price_range": "19.9-49.9元", "monthly_sales": "30000-60000", "competition": "中", "profit_margin": "40-50%", "difficulty": "中", "reason": "家长愿意买，但尺码复杂"},
                {"name": "袜子套装（10双）", "price_range": "9.9-19.9元", "monthly_sales": "50000-100000", "competition": "高", "profit_margin": "50-60%", "difficulty": "低", "reason": "消耗品，利润可观"},
                {"name": "内衣套装", "price_range": "19.9-39.9元", "monthly_sales": "35000-70000", "competition": "中", "profit_margin": "40-50%", "difficulty": "低", "reason": "刚需，复购率高"},
            ],
            "食品": [
                {"name": "零食大礼包", "price_range": "19.9-49.9元", "monthly_sales": "100000-200000", "competition": "高", "profit_margin": "20-30%", "difficulty": "低", "reason": "走量巨大，但利润低"},
                {"name": "地方特产（如螺蛳粉）", "price_range": "19.9-39.9元", "monthly_sales": "30000-60000", "competition": "中", "profit_margin": "40-50%", "difficulty": "中", "reason": "有特色，差异化强"},
                {"name": "坚果混合装（500g）", "price_range": "19.9-39.9元", "monthly_sales": "40000-80000", "competition": "中", "profit_margin": "35-45%", "difficulty": "低", "reason": "健康零食，需求稳定"},
                {"name": "速食火锅/自热米饭", "price_range": "9.9-19.9元", "monthly_sales": "50000-100000", "competition": "高", "profit_margin": "30-40%", "difficulty": "低", "reason": "方便食品，走量大"},
                {"name": "茶叶/花茶", "price_range": "19.9-49.9元", "monthly_sales": "20000-40000", "competition": "中", "profit_margin": "45-55%", "difficulty": "中", "reason": "健康趋势，利润高"},
            ],
            "家居": [
                {"name": "收纳用品套装", "price_range": "9.9-29.9元", "monthly_sales": "80000-150000", "competition": "高", "profit_margin": "45-55%", "difficulty": "低", "reason": "刚需，利润可观"},
                {"name": "厨房小工具", "price_range": "5.9-19.9元", "monthly_sales": "60000-120000", "competition": "中", "profit_margin": "50-60%", "difficulty": "低", "reason": "实用性强，走量大"},
                {"name": "清洁用品套装", "price_range": "19.9-39.9元", "monthly_sales": "50000-100000", "competition": "中", "profit_margin": "40-50%", "difficulty": "低", "reason": "消耗品，复购率高"},
                {"name": "毛巾浴巾套装", "price_range": "19.9-39.9元", "monthly_sales": "40000-80000", "competition": "中", "profit_margin": "45-55%", "difficulty": "低", "reason": "家庭必需品"},
                {"name": "拖鞋（家用）", "price_range": "9.9-19.9元", "monthly_sales": "50000-100000", "competition": "高", "profit_margin": "50-60%", "difficulty": "低", "reason": "低价高频，利润高"},
            ],
            "数码": [
                {"name": "数据线（3条装）", "price_range": "5.9-9.9元", "monthly_sales": "120000-250000", "competition": "高", "profit_margin": "40-50%", "difficulty": "低", "reason": "走量巨大，消耗品"},
                {"name": "手机壳", "price_range": "5.9-19.9元", "monthly_sales": "100000-200000", "competition": "高", "profit_margin": "55-65%", "difficulty": "低", "reason": "利润高，款式多"},
                {"name": "耳机（有线）", "price_range": "9.9-19.9元", "monthly_sales": "60000-120000", "competition": "中", "profit_margin": "45-55%", "difficulty": "低", "reason": "价格敏感用户多"},
                {"name": "手机支架", "price_range": "5.9-9.9元", "monthly_sales": "50000-100000", "competition": "高", "profit_margin": "50-60%", "difficulty": "低", "reason": "刚需小件"},
                {"name": "钢化膜（3片装）", "price_range": "5.9-9.9元", "monthly_sales": "80000-150000", "competition": "高", "profit_margin": "60-70%", "difficulty": "低", "reason": "超高利润，走量大"},
            ],
            "母婴": [
                {"name": "婴儿湿巾（10包）", "price_range": "19.9-39.9元", "monthly_sales": "50000-100000", "competition": "中", "profit_margin": "35-45%", "difficulty": "低", "reason": "刚需消耗品"},
                {"name": "儿童玩具套装", "price_range": "19.9-49.9元", "monthly_sales": "30000-60000", "competition": "中", "profit_margin": "40-50%", "difficulty": "中", "reason": "家长愿意买"},
                {"name": "婴儿纸尿裤", "price_range": "29.9-69.9元", "monthly_sales": "40000-80000", "competition": "中", "profit_margin": "30-40%", "difficulty": "中", "reason": "高频刚需"},
                {"name": "儿童餐具套装", "price_range": "19.9-39.9元", "monthly_sales": "25000-50000", "competition": "低", "profit_margin": "45-55%", "difficulty": "低", "reason": "安全需求，利润高"},
                {"name": "婴儿衣服套装", "price_range": "29.9-59.9元", "monthly_sales": "35000-70000", "competition": "中", "profit_margin": "40-50%", "difficulty": "中", "reason": "成长快，需求大"},
            ],
        }
    
    def _call_api_with_retry(self, messages, max_retries=3, max_tokens=3000):
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"API调用失败: {str(e)}"
                time.sleep(2 ** attempt)
    
    async def analyze(self, budget: int, category: str, experience: str, platform: str = "拼多多") -> Dict:
        """分析并推荐拼多多商品"""
        
        products = self.pdd_products.get(category, [])
        
        if not products:
            return {
                "success": False,
                "message": f"暂不支持 {category} 品类"
            }
        
        filtered_products = self._filter_products(products, budget, experience)
        
        # 为每个商品添加评分
        for product in filtered_products:
            product["score"] = self._calculate_score(product, experience)
            product["tags"] = self._generate_tags(product)
            product["risk_level"] = self._assess_risk(product, experience)
        
        ai_analysis = await self._generate_pdd_analysis(
            platform=platform,
            category=category,
            budget=budget,
            experience=experience,
            products=filtered_products,
            shop_context=shop_context
        )
        
        return {
            "success": True,
            "platform": platform,
            "category": category,
            "budget": budget,
            "products": filtered_products[:5],
            "ai_analysis": ai_analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_score(self, product: Dict, experience: str) -> int:
        """计算商品评分（0-100）- 多维度评分"""
        
        # 基础分
        score = 50
        
        # 1. 利润空间评分（0-25分）
        profit_num = int(product["profit_margin"].split("-")[0].replace("%", ""))
        if profit_num >= 50:
            profit_score = 25
        elif profit_num >= 40:
            profit_score = 20
        elif profit_num >= 30:
            profit_score = 15
        elif profit_num >= 20:
            profit_score = 10
        else:
            profit_score = 5
        score += profit_score
        
        # 2. 竞争程度评分（0-25分）
        if product["competition"] == "低":
            competition_score = 25
        elif product["competition"] == "中":
            competition_score = 15
        else:
            competition_score = 5
        score += competition_score
        
        # 3. 上手难度评分（0-20分）
        if product["difficulty"] == "低":
            difficulty_score = 20
        elif product["difficulty"] == "中":
            difficulty_score = 12
        else:
            difficulty_score = 5
        score += difficulty_score
        
        # 4. 市场趋势评分（0-10分）
        if "走量" in product["reason"] or "刚需" in product["reason"]:
            trend_score = 10
        elif "复购" in product["reason"]:
            trend_score = 8
        else:
            trend_score = 5
        score += trend_score
        
        # 新手额外加权
        if experience == "新手":
            if product["difficulty"] == "低":
                score += 5
            if product["competition"] == "低":
                score += 5
        
        return min(score, 100)
    
    def _generate_tags(self, product: Dict) -> List[str]:
        """生成商品标签"""
        tags = []
        
        profit_num = int(product["profit_margin"].split("-")[0].replace("%", ""))
        if profit_num > 40:
            tags.append("高利润")
        
        if product["competition"] == "低":
            tags.append("竞争小")
        elif product["competition"] == "高":
            tags.append("竞争激烈")
        
        if product["difficulty"] == "低":
            tags.append("易上手")
        
        if "走量" in product["reason"]:
            tags.append("走量款")
        
        if "复购" in product["reason"]:
            tags.append("高复购")
        
        return tags[:3]
    
    def _assess_risk(self, product: Dict, experience: str) -> str:
        """评估风险等级"""
        risk_score = 0
        
        if product["competition"] == "高":
            risk_score += 2
        elif product["competition"] == "中":
            risk_score += 1
        
        if product["difficulty"] == "高":
            risk_score += 2
        elif product["difficulty"] == "中":
            risk_score += 1
        
        profit_num = int(product["profit_margin"].split("-")[0].replace("%", ""))
        if profit_num < 30:
            risk_score += 1
        
        if experience == "新手":
            risk_score += 1
        
        if risk_score >= 4:
            return "高"
        elif risk_score >= 2:
            return "中"
        else:
            return "低"
    
    def _filter_products(self, products: List[Dict], budget: int, experience: str) -> List[Dict]:
        """根据预算和经验筛选商品"""
        filtered = []
        
        for product in products:
            price_str = product["price_range"].replace("元", "")
            if "-" in price_str:
                min_price = float(price_str.split("-")[0])
            else:
                min_price = float(price_str)
            
            if min_price > budget * 0.3:
                continue
            
            if experience == "新手" and product["difficulty"] == "高":
                continue
            
            filtered.append(product)
        
        def sort_key(p):
            competition_score = {"低": 3, "中": 2, "高": 1}[p["competition"]]
            profit_score = float(p["profit_margin"].split("-")[0].replace("%", ""))
            difficulty_score = {"低": 3, "中": 2, "高": 1}[p["difficulty"]]
            
            if experience == "新手":
                return (difficulty_score, competition_score, profit_score)
            else:
                return (profit_score, competition_score, difficulty_score)
        
        filtered.sort(key=sort_key, reverse=True)
        return filtered
    
    async def _generate_pdd_analysis(self, platform: str, category: str, budget: int, 
                                    experience: str, products: List[Dict]) -> str:
        """生成拼多多选品分析 - 升级版"""
        
        # 准备商品详情
        products_details = []
        for i, p in enumerate(products[:5], 1):
            # 计算利润
            price_range = p["price_range"].replace("元", "")
            if "-" in price_range:
                avg_price = (float(price_range.split("-")[0]) + float(price_range.split("-")[1])) / 2
            else:
                avg_price = float(price_range)
            
            profit_margin = int(p["profit_margin"].split("-")[0].replace("%", ""))
            estimated_profit = avg_price * profit_margin / 100
            cost_price = avg_price - estimated_profit
            
            # 获取月销量范围
            sales_range = p["monthly_sales"]
            
            products_details.append(f"""
{i}. {p['name']}
   - 售价：{p['price_range']}（建议定价：{avg_price:.1f}元）
   - 进货成本：约{cost_price:.1f}元
   - 利润空间：{p['profit_margin']}（扣除平台费后净利约{estimated_profit:.1f}元/件）
   - 月销量：{sales_range}件
   - 竞争程度：{p['competition']}
   - 上手难度：{p['difficulty']}
   - 综合评分：{p['score']}/100
""")
        
        prompt = f"""你是拼多多电商运营专家。现在有个{experience}商家向你咨询{category}类目选品建议。
{shop_context}

【商家情况】
- 平台：拼多多
- 品类：{category}
- 启动预算：{budget}元
- 经验：{experience}

【推荐商品详情】
{''.join(products_details)}

请按以下格式输出分析建议：

## 每个商品的详细分析
（针对每个推荐商品，给出：）
1. [商品名称]
   - 利润计算：进货价X元，售价Y元，扣除平台费（约5%）后净利Z元
   - 竞争分析：该品类前10名价格区间X-Y元，月销量Z-W件
   - 风险提示：[季节性/退货率/物流要求等]
   - 启动建议：首批进货量X件（预算Y元），测款预算Z元，推广策略[具体策略]
   - 综合评分：[利润空间X分/竞争程度Y分/上手难度Z分/市场趋势W分]

## 选品策略总结
（2-3句话，总结选品思路）

## 具体执行建议
1. [具体操作步骤]
2. [具体操作步骤]
3. [具体操作步骤]

## 避坑提示
1. [风险点和应对方法]
2. [风险点和应对方法]

要求：
- 每个商品给出具体利润计算（包含平台费用）
- 给出竞争分析数据（价格区间、销量区间）
- 给出风险提示和启动建议
- 给出0-100的综合评分，分维度打分
- 用大白话，像老师傅教徒弟
- 控制在800字以内
"""
        
        messages = [
            {"role": "system", "content": "你是拼多多电商运营专家，精通拼多多选品和运营策略，特别了解拼多多低价特性和用户特点。你的建议总是包含具体数字、利润计算、竞争分析和风险提示。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_with_retry(messages, max_tokens=3000)

    def select(self, platform: str, category: str, budget: int, experience: str, shop_context: str = "") -> Dict:
        """同步包装器，用于向后兼容"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.analyze(budget, category, experience, platform, shop_context))
        finally:
            loop.close()
