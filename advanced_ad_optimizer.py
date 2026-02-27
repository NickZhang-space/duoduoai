import os
import json
from typing import Dict, List
from openai import OpenAI
from datetime import datetime
import time

class AdvancedAdOptimizer:
    """拼多多高级推广优化器 - 深度分析"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.pdd_benchmarks = {
            "服饰": {"roi": (2.5, 4.0), "ctr": (3, 5), "cvr": (3, 6)},
            "食品": {"roi": (3.0, 5.0), "ctr": (4, 6), "cvr": (5, 8)},
            "美妆": {"roi": (2.0, 3.5), "ctr": (2, 4), "cvr": (2, 5)},
            "家居": {"roi": (2.5, 4.0), "ctr": (2, 4), "cvr": (3, 5)},
            "数码": {"roi": (1.5, 3.0), "ctr": (1, 3), "cvr": (1, 3)},
            "母婴": {"roi": (3.0, 5.0), "ctr": (3, 5), "cvr": (4, 7)},
        }
    
    def _call_api_with_retry(self, messages, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"API调用失败: {str(e)}"
                time.sleep(2 ** attempt)
    
    async def deep_analyze(self, platform: str, data: List[Dict], budget: float, goal: str, category: str = "通用") -> Dict:
        diagnosis = self._diagnose_pdd_account(data, budget, category)
        problems = self._identify_pdd_problems(data, diagnosis, category)
        opportunities = self._find_pdd_opportunities(data, diagnosis, category)
        optimization_plan = await self._generate_pdd_optimization_plan(
            platform, data, diagnosis, problems, opportunities, budget, goal, category
        )
        action_steps = self._create_pdd_action_steps(optimization_plan, data)
        expected_results = self._calculate_pdd_expected_results(data, action_steps, budget)
        
        return {
            "success": True,
            "diagnosis": diagnosis,
            "problems": problems,
            "opportunities": opportunities,
            "optimization_plan": optimization_plan,
            "action_steps": action_steps,
            "expected_results": expected_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _diagnose_pdd_account(self, data: List[Dict], budget: float, category: str) -> Dict:
        total_spend = sum(row.get("花费", 0) for row in data)
        total_gmv = sum(row.get("成交金额", 0) for row in data)
        total_orders = sum(row.get("成交笔数", 0) for row in data)
        total_clicks = sum(row.get("点击量", 0) for row in data)
        total_impressions = sum(row.get("展现量", 0) for row in data)
        
        avg_roi = total_gmv / total_spend if total_spend > 0 else 0
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cvr = (total_orders / total_clicks * 100) if total_clicks > 0 else 0
        cpc = total_spend / total_clicks if total_clicks > 0 else 0
        cpa = total_spend / total_orders if total_orders > 0 else 0
        
        benchmark = self.pdd_benchmarks.get(category, {"roi": (2.0, 3.5), "ctr": (2, 4), "cvr": (3, 5)})
        
        health_score = 0
        health_details = []
        
        if avg_roi >= benchmark["roi"][1]:
            health_score += 30
            health_details.append(f"ROI优秀（≥{benchmark['roi'][1]}）")
        elif avg_roi >= benchmark["roi"][0]:
            health_score += 20
            health_details.append(f"ROI良好")
        else:
            health_details.append("ROI需提升⚠️")
        
        if ctr >= benchmark["ctr"][1]:
            health_score += 25
            health_details.append("点击率优秀")
        elif ctr >= benchmark["ctr"][0]:
            health_score += 15
            health_details.append("点击率良好")
        else:
            health_details.append("点击率偏低⚠️")
        
        if cvr >= benchmark["cvr"][1]:
            health_score += 25
            health_details.append("转化率优秀")
        elif cvr >= benchmark["cvr"][0]:
            health_score += 15
            health_details.append("转化率良好")
        else:
            health_details.append("转化率偏低⚠️")
        
        budget_usage = (total_spend / budget * 100) if budget > 0 else 0
        if 80 <= budget_usage <= 100:
            health_score += 20
            health_details.append("预算使用合理")
        
        campaign_types = {}
        for row in data:
            camp_type = row.get("推广类型", "未知")
            if camp_type not in campaign_types:
                campaign_types[camp_type] = {"count": 0, "spend": 0, "gmv": 0}
            campaign_types[camp_type]["count"] += 1
            campaign_types[camp_type]["spend"] += row.get("花费", 0)
            campaign_types[camp_type]["gmv"] += row.get("成交金额", 0)
        
        return {
            "health_score": health_score,
            "health_level": "优秀" if health_score >= 80 else "良好" if health_score >= 60 else "及格" if health_score >= 40 else "不及格",
            "health_details": health_details,
            "metrics": {
                "总花费": f"{total_spend:.2f}元",
                "总成交金额": f"{total_gmv:.2f}元",
                "总订单数": total_orders,
                "平均ROI": f"{avg_roi:.2f}",
                "点击率": f"{ctr:.2f}%",
                "转化率": f"{cvr:.2f}%",
                "平均点击成本": f"{cpc:.2f}元",
                "平均获客成本": f"{cpa:.2f}元"
            },
            "benchmark": {
                "行业": category,
                "ROI基准": f"{benchmark['roi'][0]}-{benchmark['roi'][1]}",
                "CTR基准": f"{benchmark['ctr'][0]}-{benchmark['ctr'][1]}%",
                "CVR基准": f"{benchmark['cvr'][0]}-{benchmark['cvr'][1]}%"
            },
            "campaign_types": campaign_types,
            "budget_usage": f"{budget_usage:.1f}%"
        }
    
    def _identify_pdd_problems(self, data: List[Dict], diagnosis: Dict, category: str) -> List[Dict]:
        problems = []
        benchmark = self.pdd_benchmarks.get(category, {"roi": (2.0, 3.5), "ctr": (2, 4), "cvr": (3, 5)})
        
        low_roi_items = [r for r in data if r.get("ROI", 0) < benchmark["roi"][0] * 0.6]
        if len(low_roi_items) > len(data) * 0.3:
            total_waste = sum(r.get("花费", 0) for r in low_roi_items)
            problems.append({
                "type": "低ROI项目过多",
                "severity": "严重",
                "description": f"有{len(low_roi_items)}个项目ROI过低",
                "impact": f"浪费预算约{total_waste:.2f}元",
                "solution": "立即暂停或降低出价50%"
            })
        
        return problems
    
    def _find_pdd_opportunities(self, data: List[Dict], diagnosis: Dict, category: str) -> List[Dict]:
        opportunities = []
        benchmark = self.pdd_benchmarks.get(category, {"roi": (2.0, 3.5), "ctr": (2, 4), "cvr": (3, 5)})
        
        high_roi_items = [r for r in data if r.get("ROI", 0) >= benchmark["roi"][1]]
        if len(high_roi_items) > 0:
            opportunities.append({
                "type": "高ROI项目放量",
                "potential": "高",
                "description": f"有{len(high_roi_items)}个高ROI项目可加投",
                "action": "建议提高出价20-30%"
            })
        
        return opportunities
    
    async def _generate_pdd_optimization_plan(self, platform, data, diagnosis, problems, opportunities, budget, goal, category):
        prompt = f"""你是拼多多推广优化师，为{category}商家制定优化方案。

账户诊断：{json.dumps(diagnosis, ensure_ascii=False)}
问题：{json.dumps(problems, ensure_ascii=False)}
机会：{json.dumps(opportunities, ensure_ascii=False)}
目标：{goal}，预算{budget}元

请给出：
1. 整体策略（2-3句）
2. 立即执行动作（3-5条，具体数字）
3. 短期优化（3-7天）
4. 预期效果

用大白话，控制在600字内。"""
        
        messages = [
            {"role": "system", "content": "你是资深拼多多推广优化师，精通全站推广、标准推广、活动推广，用大白话讲解。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_with_retry(messages)
    
    def _create_pdd_action_steps(self, optimization_plan, data):
        steps = []
        low_roi = [r for r in data if r.get("ROI", 0) < 1.0]
        if low_roi:
            steps.append({
                "priority": "立即执行",
                "action": "关停低ROI项目",
                "details": f"暂停{len(low_roi)}个ROI<1.0的项目",
                "expected_saving": f"{sum(r.get('花费', 0) for r in low_roi):.2f}元/天"
            })
        
        high_roi = [r for r in data if r.get("ROI", 0) >= 3.0]
        if high_roi:
            steps.append({
                "priority": "立即执行",
                "action": "加量高ROI项目",
                "details": f"提高{len(high_roi)}个高ROI项目出价25%"
            })
        
        return steps
    
    def _calculate_pdd_expected_results(self, data, action_steps, budget):
        current_spend = sum(r.get("花费", 0) for r in data)
        current_gmv = sum(r.get("成交金额", 0) for r in data)
        current_roi = current_gmv / current_spend if current_spend > 0 else 0
        expected_roi = current_roi * 1.3
        
        return {
            "current": {"roi": f"{current_roi:.2f}", "spend": f"{current_spend:.2f}元"},
            "expected": {"roi": f"{expected_roi:.2f}"},
            "improvement": {"roi_increase": f"{30:.1f}%"},
            "timeline": "预计3-7天见效"
        }
