"""
市场洞察报告模块
整合市场数据生成洞察报告
"""
from typing import Dict, List
from datetime import datetime
from .data_collector import MarketDataCollector

class MarketInsights:
    """市场洞察分析器"""
    
    def __init__(self):
        self.collector = MarketDataCollector()
    
    def generate_report(self, category: str) -> Dict:
        """生成市场洞察报告"""
        # 收集数据
        trends = self.collector.get_category_trends(category)
        keywords = self.collector.get_hot_keywords(category)
        
        # 分析市场规模
        market_size = self._analyze_market_size(trends)
        
        # 分析竞争格局
        competition = self._analyze_competition(trends, keywords)
        
        # 识别机会点
        opportunities = self._identify_opportunities(trends, keywords)
        
        # 识别风险点
        risks = self._identify_risks(trends, keywords)
        
        # 生成建议
        recommendations = self._generate_recommendations(trends, keywords, opportunities, risks)
        
        return {
            "category": category,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "market_size": market_size,
            "competition": competition,
            "opportunities": opportunities,
            "risks": risks,
            "recommendations": recommendations,
            "summary": self._generate_summary(market_size, competition, opportunities)
        }
    
    def _analyze_market_size(self, trends: Dict) -> Dict:
        """分析市场规模"""
        avg_sales = trends["avg_daily_sales"]
        
        # 估算月度和年度规模
        monthly_sales = avg_sales * 30
        yearly_sales = avg_sales * 365
        
        # 判断市场规模等级
        if avg_sales < 10000:
            size_level = "小型市场"
        elif avg_sales < 30000:
            size_level = "中型市场"
        elif avg_sales < 50000:
            size_level = "大型市场"
        else:
            size_level = "超大型市场"
        
        return {
            "daily_avg": avg_sales,
            "monthly_estimate": monthly_sales,
            "yearly_estimate": yearly_sales,
            "size_level": size_level,
            "trend": trends["trend"]
        }
    
    def _analyze_competition(self, trends: Dict, keywords: List[Dict]) -> Dict:
        """分析竞争格局"""
        competition_level = trends["competition_level"]
        
        # 统计关键词竞争度
        high_competition_kws = [kw for kw in keywords if kw["competition"] == "高"]
        medium_competition_kws = [kw for kw in keywords if kw["competition"] == "中"]
        low_competition_kws = [kw for kw in keywords if kw["competition"] == "低"]
        
        # 计算平均CPC
        avg_cpc = sum(kw["avg_cpc"] for kw in keywords) / len(keywords) if keywords else 0
        
        return {
            "level": competition_level,
            "high_competition_keywords": len(high_competition_kws),
            "medium_competition_keywords": len(medium_competition_kws),
            "low_competition_keywords": len(low_competition_kws),
            "avg_cpc": round(avg_cpc, 2),
            "top_competitors": trends["top_products"][:5]
        }
    
    def _identify_opportunities(self, trends: Dict, keywords: List[Dict]) -> List[Dict]:
        """识别机会点"""
        opportunities = []
        
        # 机会1：市场趋势上升
        if trends["trend"] == "上升":
            opportunities.append({
                "type": "市场增长",
                "description": "该类目整体呈上升趋势，市场需求增长",
                "priority": "高",
                "action": "加大投入，抢占市场份额"
            })
        
        # 机会2：低竞争高搜索关键词
        low_comp_high_search = [
            kw for kw in keywords 
            if kw["competition"] == "低" and kw["search_volume"] > 10000
        ]
        if low_comp_high_search:
            opportunities.append({
                "type": "蓝海关键词",
                "description": f"发现{len(low_comp_high_search)}个低竞争高搜索量关键词",
                "priority": "高",
                "action": f"重点优化：{', '.join([kw['keyword'] for kw in low_comp_high_search[:3]])}",
                "keywords": [kw["keyword"] for kw in low_comp_high_search[:5]]
            })
        
        # 机会3：价格区间机会
        price_range = trends["price_range"]
        if price_range["max"] - price_range["min"] > 50:
            opportunities.append({
                "type": "价格分层",
                "description": f"价格区间跨度大（¥{price_range['min']}-¥{price_range['max']}），可针对不同人群定价",
                "priority": "中",
                "action": "开发高中低三档产品线"
            })
        
        # 机会4：上升趋势关键词
        rising_keywords = [kw for kw in keywords if kw["trend"] == "上升"]
        if rising_keywords:
            opportunities.append({
                "type": "趋势关键词",
                "description": f"{len(rising_keywords)}个关键词搜索量上升",
                "priority": "中",
                "action": f"关注热词：{', '.join([kw['keyword'] for kw in rising_keywords[:3]])}",
                "keywords": [kw["keyword"] for kw in rising_keywords[:5]]
            })
        
        return opportunities
    
    def _identify_risks(self, trends: Dict, keywords: List[Dict]) -> List[Dict]:
        """识别风险点"""
        risks = []
        
        # 风险1：竞争激烈
        if trends["competition_level"] in ["高", "极高"]:
            risks.append({
                "type": "竞争风险",
                "level": "高" if trends["competition_level"] == "极高" else "中",
                "description": f"市场竞争{trends['competition_level']}，新进入者难度大",
                "mitigation": "差异化定位，避开头部竞品直接竞争"
            })
        
        # 风险2：市场下降
        if trends["trend"] == "下降":
            risks.append({
                "type": "市场萎缩",
                "level": "高",
                "description": "类目整体销量下降，市场需求减弱",
                "mitigation": "谨慎投入，考虑转向其他类目"
            })
        
        # 风险3：高CPC
        high_cpc_kws = [kw for kw in keywords if kw["avg_cpc"] > 2.0]
        if len(high_cpc_kws) > len(keywords) * 0.5:
            risks.append({
                "type": "推广成本高",
                "level": "中",
                "description": f"超过一半关键词CPC>¥2，推广成本较高",
                "mitigation": "优化长尾词，提升自然流量占比"
            })
        
        # 风险4：下降趋势关键词
        declining_keywords = [kw for kw in keywords if kw["trend"] == "下降"]
        if len(declining_keywords) > 3:
            risks.append({
                "type": "需求下降",
                "level": "中",
                "description": f"{len(declining_keywords)}个关键词搜索量下降",
                "mitigation": "及时调整关键词策略，关注新兴热词"
            })
        
        return risks
    
    def _generate_recommendations(self, trends: Dict, keywords: List[Dict], 
                                  opportunities: List[Dict], risks: List[Dict]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于市场趋势
        if trends["trend"] == "上升":
            recommendations.append("✅ 市场向好，建议加大投入力度")
        else:
            recommendations.append("⚠️ 市场下行，建议谨慎投入或寻找细分机会")
        
        # 基于竞争程度
        if trends["competition_level"] in ["低", "中"]:
            recommendations.append("✅ 竞争适中，适合新手入场")
        else:
            recommendations.append("⚠️ 竞争激烈，需要差异化策略")
        
        # 基于机会点
        if any(opp["type"] == "蓝海关键词" for opp in opportunities):
            recommendations.append("💡 发现蓝海关键词，优先布局可快速获取流量")
        
        # 基于风险
        if any(risk["level"] == "高" for risk in risks):
            recommendations.append("⚠️ 存在高风险因素，需制定应对预案")
        
        # 价格策略
        price_range = trends["price_range"]
        avg_price = (price_range["min"] + price_range["max"]) / 2
        recommendations.append(f"💰 建议定价区间：¥{round(avg_price * 0.9, 1)}-¥{round(avg_price * 1.1, 1)}")
        
        # 关键词策略
        top_keywords = keywords[:3]
        if top_keywords:
            kw_names = [kw["keyword"] for kw in top_keywords]
            recommendations.append(f"🔑 核心关键词：{', '.join(kw_names)}")
        
        return recommendations
    
    def _generate_summary(self, market_size: Dict, competition: Dict, 
                         opportunities: List[Dict]) -> str:
        """生成摘要"""
        summary_parts = []
        
        # 市场规模
        summary_parts.append(f"该类目为{market_size['size_level']}")
        
        # 趋势
        trend_text = "呈上升趋势" if market_size['trend'] == "上升" else "呈下降趋势"
        summary_parts.append(trend_text)
        
        # 竞争
        summary_parts.append(f"竞争程度{competition['level']}")
        
        # 机会
        high_priority_opps = [opp for opp in opportunities if opp.get("priority") == "高"]
        if high_priority_opps:
            summary_parts.append(f"存在{len(high_priority_opps)}个高优先级机会")
        
        return "，".join(summary_parts) + "。"
