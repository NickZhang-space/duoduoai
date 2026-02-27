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
    
    def _call_api_with_retry(self, messages, max_retries=3):
        """带重试的API调用"""
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
    
    async def analyze(self, platform: str, data: str, analysis_type: str, category: str = "通用") -> Dict:
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
        """整体分析（拼多多版）"""
        
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
            campaign_types=campaign_types
        )
        
        return {
            "summary": {
                "总花费": f"{total_spend:.2f}元",
                "总成交金额": f"{total_gmv:.2f}元",
                "总订单数": total_orders,
                "平均ROI": f"{avg_roi:.2f}",
                "点击率": f"{ctr:.2f}%",
                "转化率": f"{cvr:.2f}%",
                "平均点击花费": f"{avg_cpc:.2f}元"
            },
            "benchmark": {
                "行业": category,
                "ROI基准": f"{benchmark['roi'][0]}-{benchmark['roi'][1]}",
                "CTR基准": f"{benchmark['ctr'][0]}-{benchmark['ctr'][1]}%",
                "CVR基准": f"{benchmark['cvr'][0]}-{benchmark['cvr'][1]}%"
            },
            "campaign_types": campaign_types,
            "best_performers": best_performers,
            "worst_performers": worst_performers,
            "ai_suggestions": ai_suggestions
        }
    
    async def _analyze_keywords(self, platform: str, data: List[Dict], category: str) -> Dict:
        """关键词分析（拼多多版）"""
        
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
        
        # 生成具体操作建议
        actions = {
            "立即提高出价（加投）": [
                {
                    "关键词": kw.get("关键词", ""),
                    "当前ROI": kw.get("ROI", 0),
                    "当前花费": kw.get("花费", 0),
                    "建议": f"提高出价20-30%，预计增加{int(kw.get('成交笔数', 0) * 0.3)}单"
                }
                for kw in high_roi[:3]
            ],
            "保持观察": [kw.get("关键词", "") for kw in medium_roi[:3]],
            "降低出价或暂停": [
                {
                    "关键词": kw.get("关键词", ""),
                    "当前ROI": kw.get("ROI", 0),
                    "浪费金额": kw.get("花费", 0),
                    "建议": "暂停或降价50%"
                }
                for kw in low_roi[:3]
            ]
        }
        
        return {
            "high_roi_keywords": high_roi[:5],
            "medium_roi_keywords": medium_roi[:5],
            "low_roi_keywords": low_roi[:5],
            "actions": actions,
            "ai_suggestions": ai_suggestions
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
            "high_ctr_creatives": sorted_by_ctr[:5],
            "high_cvr_creatives": sorted_by_cvr[:5],
            "ai_suggestions": ai_suggestions
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
            "high_roi_audiences": sorted_data[:5],
            "low_roi_audiences": sorted_data[-5:],
            "ai_suggestions": ai_suggestions
        }
    
    async def _generate_pdd_overall_suggestions(self, platform: str, category: str, 
                                               total_spend: float, total_gmv: float,
                                               avg_roi: float, ctr: float, cvr: float, avg_cpc: float,
                                               benchmark: Dict, best_performers: List[Dict],
                                               worst_performers: List[Dict], campaign_types: Dict) -> str:
        """生成拼多多整体优化建议"""
        
        prompt = f"""你是一位资深的拼多多推广优化师，有5年以上的多多推广经验。现在有个{category}类目商家向你咨询推广优化建议。

**当前数据：**
- 总花费：{total_spend:.2f}元
- 总成交金额：{total_gmv:.2f}元
- 平均ROI：{avg_roi:.2f}
- 点击率：{ctr:.2f}%
- 转化率：{cvr:.2f}%
- 平均点击花费：{avg_cpc:.2f}元

**{category}行业基准：**
- ROI基准：{benchmark['roi'][0]}-{benchmark['roi'][1]}
- CTR基准：{benchmark['ctr'][0]}-{benchmark['ctr'][1]}%
- CVR基准：{benchmark['cvr'][0]}-{benchmark['cvr'][1]}%

**推广类型分布：**
{json.dumps(campaign_types, ensure_ascii=False, indent=2)}

**表现最好的3个：**
{json.dumps(best_performers, ensure_ascii=False, indent=2)}

**表现最差的3个：**
{json.dumps(worst_performers, ensure_ascii=False, indent=2)}

请以资深拼多多推广优化师的身份，给出实用的优化建议：

1. **账户健康度诊断**（2-3句话）
   - 当前ROI {avg_roi:.2f} 在{category}行业处于什么水平？
   - 最大的问题是什么？

2. **立即执行的优化动作**（3-5条，每条要具体可执行）
   - 例如："暂停ROI<1.0的关键词XX、XX，每天可节省XX元"
   - 例如："把ROI>3.0的关键词XX的出价提高30%，从XX元提到XX元，预计每天多出XX单"
   - 如果是全站推广，给出ROI目标设置建议
   - 如果是标准推广，给出关键词出价+人群溢价建议

3. **预期效果**（1-2句话）
   - 执行这些优化，ROI预计能提升到多少？
   - 多久能看到效果？

**要求：**
- 用商家听得懂的大白话，不要太多专业术语
- 给出具体的数字和操作步骤
- 每句话都要有价值
- 总字数控制在300字以内
"""
        
        messages = [
            {"role": "system", "content": "你是一位资深的拼多多推广优化师，有5年以上的多多推广经验。你精通全站推广、标准推广、活动推广的区别和最佳实践。你的建议总是具体、实用、可执行，用大白话讲解。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_with_retry(messages)
    
    async def _generate_pdd_keyword_suggestions(self, platform: str, category: str,
                                               high_roi: List[Dict], medium_roi: List[Dict], 
                                               low_roi: List[Dict]) -> str:
        """生成拼多多关键词优化建议"""
        
        prompt = f"""你是一个拼多多关键词优化专家。请分析{category}类目的关键词数据，给出优化建议：

**高ROI关键词（ROI>=2.5）：**
{json.dumps(high_roi[:5], ensure_ascii=False, indent=2)}

**中等ROI关键词（1.5<=ROI<2.5）：**
{json.dumps(medium_roi[:5], ensure_ascii=False, indent=2)}

**低ROI关键词（ROI<1.5）：**
{json.dumps(low_roi[:5], ensure_ascii=False, indent=2)}

请给出：

1. **高ROI关键词策略**（2-3句话）
   - 这些词为什么ROI高？
   - 具体怎么加投？（提高出价X%，预计增加Y单）

2. **低ROI关键词处理**（2-3条）
   - 例如："关键词XX，ROI只有0.8，建议暂停，每天节省XX元"
   - 例如："关键词XX，点击率低，建议降价50%测试"

3. **关键词分层策略**（1-2句话）
   - 大词引流 + 长尾词转化的组合建议

**要求：**
- 具体可执行，给出数字
- 用大白话
- 控制在250字以内
"""
        
        messages = [
            {"role": "system", "content": "你是一个拼多多关键词优化专家，精通关键词出价策略和人群溢价优化。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_with_retry(messages)
    
    async def _generate_creative_suggestions(self, platform: str, category: str,
                                            high_ctr: List[Dict], high_cvr: List[Dict]) -> str:
        """生成素材优化建议"""
        
        prompt = f"""你是一个拼多多素材优化专家。请分析{category}类目的素材数据：

**高点击率素材：**
{json.dumps(high_ctr, ensure_ascii=False, indent=2)}

**高转化率素材：**
{json.dumps(high_cvr, ensure_ascii=False, indent=2)}

请给出：
1. 高点击率素材的特点（2句话）
2. 高转化率素材的特点（2句话）
3. 素材优化建议（3条）

控制在150字以内，用大白话。
"""
        
        messages = [
            {"role": "system", "content": f"你是一个拼多多素材优化专家。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_with_retry(messages)
    
    async def _generate_audience_suggestions(self, platform: str, category: str, data: List[Dict]) -> str:
        """生成人群优化建议"""
        
        prompt = f"""你是一个拼多多人群定向专家。请分析{category}类目的人群数据：

{json.dumps(data[:10], ensure_ascii=False, indent=2)}

请给出：
1. 高ROI人群的特征（2句话）
2. 人群定向优化建议（3条）

控制在120字以内，用大白话。
"""
        
        messages = [
            {"role": "system", "content": f"你是一个拼多多人群定向专家。"},
            {"role": "user", "content": prompt}
        ]
        return self._call_api_with_retry(messages)
