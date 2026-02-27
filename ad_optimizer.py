import os
import json
import re
from typing import Dict, List
from openai import OpenAI
import time
from datetime import datetime

class AdOptimizer:
    """拼多多推广优化分析器"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        
        # 拼多多行业基准数据
        self.pdd_benchmarks = {
            "服饰": {"roi": (2.5, 4.0), "ctr": (3, 5), "cvr": (3, 6)},
            "食品": {"roi": (3.0, 5.0), "ctr": (4, 6), "cvr": (5, 8)},
            "美妆": {"roi": (2.0, 3.5), "ctr": (2, 4), "cvr": (2, 5)},
            "家居": {"roi": (2.5, 4.0), "ctr": (2, 4), "cvr": (3, 5)},
            "数码": {"roi": (1.5, 3.0), "ctr": (1, 3), "cvr": (1, 3)},
            "母婴": {"roi": (3.0, 5.0), "ctr": (3, 5), "cvr": (4, 7)},
        }
    
    def _call_api_with_retry(self, messages, max_retries=3, max_tokens=3000):
        """带重试的API调用"""
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
    
    async def analyze(self, platform: str, data: str, analysis_type: str, category: str = "通用", shop_context: str = "") -> Dict:
        """分析拼多多推广数据"""
        
        # 解析用户上传的数据
        parsed_data = self._parse_pdd_data(data)
        
        if not parsed_data:
            return {
                "success": False,
                "message": "数据格式错误。请确保：\n1. 第一行是列名\n2. 数据用逗号或制表符分隔\n3. 至少包含：关键词、花费、ROI等字段"
            }
        
        # 根据分析类型调用不同的分析方法
        if analysis_type == "整体":
            result = await self._analyze_overall(platform, parsed_data, category)
        elif analysis_type == "关键词":
            result = await self._analyze_keywords(platform, parsed_data, category)
        elif analysis_type == "素材":
            result = await self._analyze_creative(platform, parsed_data, category)
        elif analysis_type == "人群":
            result = await self._analyze_audience(platform, parsed_data, category)
        else:
            return {
                "success": False,
                "message": f"不支持的分析类型：{analysis_type}"
            }
        
        return {
            "success": True,
            "platform": platform,
            "analysis_type": analysis_type,
            "category": category,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_pdd_data(self, data: str) -> List[Dict]:
        """解析拼多多推广数据（支持多种字段名）"""
        
        lines = data.strip().split("\n")
        if len(lines) < 2:
            return None
        
        # 解析表头
        header_line = lines[0]
        if "\t" in header_line:
            separator = "\t"
        elif "," in header_line:
            separator = ","
        else:
            return None
        
        headers = [h.strip() for h in header_line.split(separator)]
        
        # 拼多多字段映射（支持多种写法）
        header_mapping = {
            "关键词": ["关键词", "搜索词", "keyword", "词", "名称", "计划名称"],
            "展现量": ["展现量", "展现", "曝光量", "曝光", "impression", "展现数"],
            "点击量": ["点击量", "点击", "点击数", "click", "clicks"],
            "花费": ["花费", "消耗", "cost", "金额", "费用", "推广费用"],
            "成交金额": ["成交金额", "GMV", "gmv", "交易额", "销售额"],
            "成交笔数": ["成交笔数", "订单数", "成交数", "转化数", "订单"],
            "ROI": ["ROI", "roi", "投产比", "回报率"],
            "点击率": ["点击率", "CTR", "ctr"],
            "转化率": ["转化率", "CVR", "cvr"],
            "平均点击花费": ["平均点击花费", "CPC", "cpc", "点击单价"],
            "千次展现花费": ["千次展现花费", "CPM", "cpm"],
            "推广类型": ["推广类型", "计划类型", "类型", "推广方式"],
        }
        
        # 映射列名
        normalized_headers = []
        for h in headers:
            found = False
            for standard_name, variations in header_mapping.items():
                if h in variations:
                    normalized_headers.append(standard_name)
                    found = True
                    break
            if not found:
                normalized_headers.append(h)
        
        # 解析数据行
        parsed = []
        for line in lines[1:]:
            if not line.strip():
                continue
            
            values = [v.strip() for v in line.split(separator)]
            if len(values) != len(normalized_headers):
                continue
            
            row = {}
            for i, header in enumerate(normalized_headers):
                try:
                    value = values[i]
                    # 移除单位
                    value = value.replace("元", "").replace("%", "").replace(",", "")
                    if "." in value:
                        row[header] = float(value)
                    else:
                        row[header] = int(value) if value.isdigit() else value
                except:
                    row[header] = values[i]
            
            # 计算缺失的指标
            if "点击率" not in row and "点击量" in row and "展现量" in row:
                if row["展现量"] > 0:
                    row["点击率"] = round(row["点击量"] / row["展现量"] * 100, 2)
            
            if "转化率" not in row and "成交笔数" in row and "点击量" in row:
                if row["点击量"] > 0:
                    row["转化率"] = round(row["成交笔数"] / row["点击量"] * 100, 2)
            
            if "ROI" not in row and "成交金额" in row and "花费" in row:
                if row["花费"] > 0:
                    row["ROI"] = round(row["成交金额"] / row["花费"], 2)
            
            if "平均点击花费" not in row and "花费" in row and "点击量" in row:
                if row["点击量"] > 0:
                    row["平均点击花费"] = round(row["花费"] / row["点击量"], 2)
            
            parsed.append(row)
        
        return parsed if parsed else None
    
    async def _analyze_overall(self, platform: str, data: List[Dict], category: str) -> Dict:
        """整体分析（拼多多版）- 返回结构化数据"""
        
        # 计算总体指标
        total_spend = sum(row.get("花费", 0) for row in data)
        total_gmv = sum(row.get("成交金额", 0) for row in data)
        total_orders = sum(row.get("成交笔数", 0) for row in data)
        total_clicks = sum(row.get("点击量", 0) for row in data)
        total_impressions = sum(row.get("展现量", 0) for row in data)
        
        avg_roi = total_gmv / total_spend if total_spend > 0 else 0
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cvr = (total_orders / total_clicks * 100) if total_clicks > 0 else 0
        avg_cpc = total_spend / total_clicks if total_clicks > 0 else 0
        
        # 获取行业基准
        benchmark = self.pdd_benchmarks.get(category, {"roi": (2.0, 3.5), "ctr": (2, 4), "cvr": (3, 5)})
        
        # 找出表现最好和最差的项
        sorted_by_roi = sorted(data, key=lambda x: x.get("ROI", 0), reverse=True)
        best_performers = sorted_by_roi[:3]
        worst_performers = sorted_by_roi[-3:]
        
        # 推广类型分析
        campaign_types = {}
        for row in data:
            camp_type = row.get("推广类型", "未知")
            if camp_type not in campaign_types:
                campaign_types[camp_type] = {"spend": 0, "gmv": 0, "count": 0}
            campaign_types[camp_type]["spend"] += row.get("花费", 0)
            campaign_types[camp_type]["gmv"] += row.get("成交金额", 0)
            campaign_types[camp_type]["count"] += 1
        
        # 使用 AI 生成优化建议
        ai_suggestions = await self._generate_pdd_overall_suggestions(
            platform=platform,
            category=category,
            total_spend=total_spend,
            total_gmv=total_gmv,
            avg_roi=avg_roi,
            ctr=ctr,
            cvr=cvr,
            avg_cpc=avg_cpc,
            benchmark=benchmark,
            best_performers=best_performers,
            worst_performers=worst_performers,
            campaign_types=campaign_types,
            shop_context=shop_context
        )
        
        # 返回结构化数据
        return {
            "summary": f"总花费{total_spend:.2f}元，成交金额{total_gmv:.2f}元，平均ROI {avg_roi:.2f}",
            "metrics": [
                {"label": "总花费", "value": f"{total_spend:.2f}元"},
                {"label": "总成交金额", "value": f"{total_gmv:.2f}元"},
                {"label": "总订单数", "value": total_orders},
                {"label": "平均ROI", "value": f"{avg_roi:.2f}"},
                {"label": "点击率", "value": f"{ctr:.2f}%"},
                {"label": "转化率", "value": f"{cvr:.2f}%"},
                {"label": "平均点击花费", "value": f"{avg_cpc:.2f}元"}
            ],
            "suggestions": ai_suggestions.split("\n") if isinstance(ai_suggestions, str) else [ai_suggestions],
            "keywords_analysis": [
                {
                    "name": kw.get("关键词", "未知"),
                    "spend": kw.get("花费", 0),
                    "clicks": kw.get("点击量", 0),
                    "conversions": kw.get("成交笔数", 0),
                    "roi": kw.get("ROI", 0),
                    "verdict": "加投" if kw.get("ROI", 0) >= 2.5 else ("减投" if kw.get("ROI", 0) < 1.5 else "观察")
                }
                for kw in data[:10]
            ]
        }
    
    async def _analyze_keywords(self, platform: str, data: List[Dict], category: str) -> Dict:
        """关键词分析（拼多多版）- 返回结构化数据"""
        
        # 按ROI排序
        sorted_data = sorted(data, key=lambda x: x.get("ROI", 0), reverse=True)
        
        # 分类关键词
        high_roi = [row for row in sorted_data if row.get("ROI", 0) >= 2.5]
        medium_roi = [row for row in sorted_data if 1.5 <= row.get("ROI", 0) < 2.5]
        low_roi = [row for row in sorted_data if row.get("ROI", 0) < 1.5]
        
        # 使用 AI 生成建议
        ai_suggestions = await self._generate_pdd_keyword_suggestions(
            platform=platform,
            category=category,
            high_roi=high_roi,
            medium_roi=medium_roi,
            low_roi=low_roi
        )
        
        # 生成结构化关键词分析
        keywords_analysis = []
        for kw in sorted_data[:20]:
            roi_val = kw.get("ROI", 0)
            keywords_analysis.append({
                "name": kw.get("关键词", "未知"),
                "spend": kw.get("花费", 0),
                "clicks": kw.get("点击量", 0),
                "conversions": kw.get("成交笔数", 0),
                "roi": roi_val,
                "verdict": "加投" if roi_val >= 2.5 else ("暂停" if roi_val < 1.0 else ("减投" if roi_val < 1.5 else "观察"))
            })
        
        return {
            "summary": f"共分析{len(sorted_data)}个关键词，高ROI关键词{len(high_roi)}个，低ROI关键词{len(low_roi)}个",
            "metrics": [
                {"label": "高ROI关键词", "value": len(high_roi)},
                {"label": "中等ROI关键词", "value": len(medium_roi)},
                {"label": "低ROI关键词", "value": len(low_roi)}
            ],
            "suggestions": ai_suggestions.split("\n") if isinstance(ai_suggestions, str) else [ai_suggestions],
            "keywords_analysis": keywords_analysis
        }
    
    async def _analyze_creative(self, platform: str, data: List[Dict], category: str) -> Dict:
        """素材分析"""
        
        sorted_by_ctr = sorted(data, key=lambda x: x.get("点击率", 0), reverse=True)
        sorted_by_cvr = sorted(data, key=lambda x: x.get("转化率", 0), reverse=True)
        
        ai_suggestions = await self._generate_creative_suggestions(
            platform=platform,
            category=category,
            high_ctr=sorted_by_ctr[:3],
            high_cvr=sorted_by_cvr[:3]
        )
        
        return {
            "summary": "素材分析完成",
            "metrics": [
                {"label": "高点击率素材", "value": len(sorted_by_ctr[:5])},
                {"label": "高转化率素材", "value": len(sorted_by_cvr[:5])}
            ],
            "suggestions": ai_suggestions.split("\n") if isinstance(ai_suggestions, str) else [ai_suggestions],
            "keywords_analysis": []
        }
    
    async def _analyze_audience(self, platform: str, data: List[Dict], category: str) -> Dict:
        """人群分析"""
        
        sorted_data = sorted(data, key=lambda x: x.get("ROI", 0), reverse=True)
        
        ai_suggestions = await self._generate_audience_suggestions(
            platform=platform,
            category=category,
            data=sorted_data
        )
        
        return {
            "summary": "人群分析完成",
            "metrics": [
                {"label": "高ROI人群", "value": len([d for d in sorted_data if d.get("ROI", 0) >= 2.5])}
            ],
            "suggestions": ai_suggestions.split("\n") if isinstance(ai_suggestions, str) else [ai_suggestions],
            "keywords_analysis": []
        }
    
    async def _generate_pdd_overall_suggestions(self, platform: str, category: str, 
                                               total_spend: float, total_gmv: float,
                                               avg_roi: float, ctr: float, cvr: float, avg_cpc: float,
                                               benchmark: Dict, best_performers: List[Dict],
                                               worst_performers: List[Dict], campaign_types: Dict, shop_context: str = "") -> str:
        """生成拼多多整体优化建议 - 升级版"""
        
        # 计算与行业基准的差距
        roi_gap = ((avg_roi - benchmark['roi'][0]) / benchmark['roi'][0] * 100) if benchmark['roi'][0] > 0 else 0
        ctr_gap = ((ctr - benchmark['ctr'][0]) / benchmark['ctr'][0] * 100) if benchmark['ctr'][0] > 0 else 0
        cvr_gap = ((cvr - benchmark['cvr'][0]) / benchmark['cvr'][0] * 0) if benchmark['cvr'][0] > 0 else 0
        
        prompt = f"""你是一位资深的拼多多推广优化师，有5年以上的多多推广经验。现在有个{category}类目商家向你咨询推广优化建议。

{shop_context}
【当前数据】
- 总花费：{total_spend:.2f}元
- 总成交金额：{total_gmv:.2f}元
- 平均ROI：{avg_roi:.2f}
- 点击率：{ctr:.2f}%
- 转化率：{cvr:.2f}%
- 平均点击花费：{avg_cpc:.2f}元

【{category}行业基准对比】
- ROI基准：{benchmark['roi'][0]}-{benchmark['roi'][1]}，你的ROI {avg_roi:.2f}，{'高于' if roi_gap > 0 else '低于'}基准 {abs(roi_gap):.1f}%
- CTR基准：{benchmark['ctr'][0]}-{benchmark['ctr'][1]}%，你的CTR {ctr:.2f}%，{'高于' if ctr_gap > 0 else '低于'}基准 {abs(ctr_gap):.1f}%
- CVR基准：{benchmark['cvr'][0]}-{benchmark['cvr'][1]}%，你的CVR {cvr:.2f}%，{'高于' if cvr_gap > 0 else '低于'}基准 {abs(cvr_gap):.1f}%

【表现最好的关键词】
{chr(10).join([f"- {p.get('关键词', '未知')}：ROI {p.get('ROI', 0):.2f}，花费 {p.get('花费', 0):.2f}元" for p in best_performers[:3]])}

【表现最差的关键词】
{chr(10).join([f"- {p.get('关键词', '未知')}：ROI {p.get('ROI', 0):.2f}，花费 {p.get('花费', 0):.2f}元" for p in worst_performers[:3]])}

请按以下格式输出优化建议，每条建议必须包含具体数字：

## 诊断结论
（2-3句话，指出核心问题和机会点）

## 立即执行（优先级从高到低）
1. [具体操作]：预计节省/增加X元/天
2. [具体操作]：预计节省/增加X元/天
3. [具体操作]：预计节省/增加X元/天

## 一周内优化
1. [具体操作]
2. [具体操作]

## 预期效果
（1-2句话，给出优化后的预期ROI、花费等数据）

要求：
- 每条建议必须给出具体数字（如"CPC从2.3降到1.8"、"ROI低于1.5的词暂停"）
- 给出优先级排序和预期效果
- 用商家听得懂的大白话
- 总字数控制在500字以内
"""
        
        messages = [
            {"role": "system", "content": "你是一位资深的拼多多推广优化师，有5年以上的多多推广经验。你精通全站推广、标准推广、活动推广的区别和最佳实践。你的建议总是具体、实用、可执行，用大白话讲解，并且每条建议都包含具体数字。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_with_retry(messages, max_tokens=3000)
    
    async def _generate_pdd_keyword_suggestions(self, platform: str, category: str,
                                               high_roi: List[Dict], medium_roi: List[Dict], 
                                               low_roi: List[Dict]) -> str:
        """生成拼多多关键词优化建议 - 升级版"""
        
        # 准备详细的关键词数据
        high_roi_details = "\n".join([
            f"- {kw.get('关键词', '未知')}：ROI {kw.get('ROI', 0):.2f}，CPC {kw.get('平均点击花费', 0):.2f}元，花费 {kw.get('花费', 0):.2f}元"
            for kw in high_roi[:5]
        ])
        
        low_roi_details = "\n".join([
            f"- {kw.get('关键词', '未知')}：ROI {kw.get('ROI', 0):.2f}，CPC {kw.get('平均点击花费', 0):.2f}元，花费 {kw.get('花费', 0):.2f}元"
            for kw in low_roi[:5]
        ])
        
        prompt = f"""你是一个拼多多关键词优化专家。请分析{category}类目的关键词数据，给出优化建议：

【高ROI关键词（ROI>=2.5）】：{len(high_roi)}个
{high_roi_details}

【中等ROI关键词（1.5<=ROI<2.5）】：{len(medium_roi)}个

【低ROI关键词（ROI<1.5）】：{len(low_roi)}个
{low_roi_details}

请按以下格式输出：

## 逐个关键词操作建议
（针对上述高ROI和低ROI关键词，逐个给出操作建议）
- [关键词名称]：[加投/减投/暂停/观察]，出价从X元调整到Y元，预计ROI变化：从A到B

## 关键词分组策略
（如：高转化词单独建计划、长尾词低价跑量等）

## 预估调整后ROI变化
（给出整体ROI的预期变化）

要求：
- 每个关键词给出具体出价调整数字
- 给出关键词分组策略
- 预估调整后的ROI变化
- 用大白话，控制在400字以内
"""
        
        messages = [
            {"role": "system", "content": "你是一个拼多多关键词优化专家，精通关键词出价策略和人群溢价优化。你的建议总是包含具体数字和可执行的操作步骤。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_with_retry(messages, max_tokens=3000)
    
    async def _generate_creative_suggestions(self, platform: str, category: str,
                                            high_ctr: List[Dict], high_cvr: List[Dict]) -> str:
        """生成素材优化建议 - 升级版"""
        
        high_ctr_details = "\n".join([
            f"- {c.get('关键词', '未知')}：CTR {c.get('点击率', 0):.2f}%，CVR {c.get('转化率', 0):.2f}%"
            for c in high_ctr[:3]
        ])
        
        high_cvr_details = "\n".join([
            f"- {c.get('关键词', '未知')}：CVR {c.get('转化率', 0):.2f}%，CTR {c.get('点击率', 0):.2f}%"
            for c in high_cvr[:3]
        ])
        
        prompt = f"""你是一个拼多多素材优化专家。请分析{category}类目的素材数据：

【高点击率素材】
{high_ctr_details}

【高转化率素材】
{high_cvr_details}

请给出：
1. 高点击率素材的特点分析（2-3句话，分析为什么点击率高）
2. 高转化率素材的特点分析（2-3句话，分析为什么转化率高）
3. 素材优化建议（3-4条具体建议，包含数字目标）

要求：用大白话，给出具体优化方向和数字目标，控制在300字以内
"""
        
        messages = [
            {"role": "system", "content": f"你是一个拼多多素材优化专家，精通拼多多主图、详情页优化。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_with_retry(messages, max_tokens=3000)
    
    async def _generate_audience_suggestions(self, platform: str, category: str, data: List[Dict]) -> str:
        """生成人群优化建议 - 升级版"""
        
        high_roi_audience = [d for d in data if d.get("ROI", 0) >= 2.5]
        
        audience_details = "\n".join([
            f"- {a.get('关键词', '未知')}：ROI {a.get('ROI', 0):.2f}，花费 {a.get('花费', 0):.2f}元"
            for a in high_roi_audience[:5]
        ])
        
        prompt = f"""你是一个拼多多人群定向专家。请分析{category}类目的人群数据：

【高ROI人群】（{len(high_roi_audience)}个）
{audience_details}

请给出：
1. 高ROI人群的特征分析（2-3句话）
2. 人群定向优化建议（3-4条，包含具体溢价比例建议）
3. 预期效果（给出优化后的ROI预期）

要求：用大白话，给出具体溢价比例，控制在250字以内
"""
        
        messages = [
            {"role": "system", "content": f"你是一个拼多多人群定向专家，精通人群溢价和定向策略。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_with_retry(messages, max_tokens=3000)
