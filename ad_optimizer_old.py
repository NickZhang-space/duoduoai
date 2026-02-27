import os
import json
import re
from typing import Dict, List
from openai import OpenAI
import time
from datetime import datetime

class AdOptimizer:
    """投流优化分析 - 优化版"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
    

    def _call_api_with_retry(self, messages, max_retries=3):
        """带重试的API调用"""
        for attempt in range(max_retries):
            messages = [
                    {"role": "system", "content": f"你是一个有10年经验的{platform}投流优化专家，擅长数据分析和ROI优化。你的建议总是具体、实用、可执行。"},
                    {"role": "user", "content": prompt}
                ]
            return self._call_api_with_retry(messages)
    async def analyze(self, platform: str, data: str, analysis_type: str) -> Dict:
        """分析投流数据"""
        
        # 解析用户上传的数据
        parsed_data = self._parse_data(data)
        
        if not parsed_data:
            return {
                "success": False,
                "message": "数据格式错误。请确保：\n1. 第一行是列名\n2. 数据用逗号分隔\n3. 至少包含：关键词、花费、ROI等字段"
            }
        
        # 根据分析类型调用不同的分析方法
        if analysis_type == "整体":
            result = await self._analyze_overall(platform, parsed_data)
        elif analysis_type == "关键词":
            result = await self._analyze_keywords(platform, parsed_data)
        elif analysis_type == "素材":
            result = await self._analyze_creative(platform, parsed_data)
        elif analysis_type == "人群":
            result = await self._analyze_audience(platform, parsed_data)
        else:
            return {
                "success": False,
                "message": f"不支持的分析类型：{analysis_type}"
            }
        
        return {
            "success": True,
            "platform": platform,
            "analysis_type": analysis_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_data(self, data: str) -> List[Dict]:
        """解析用户上传的数据（增强版，支持更多格式）"""
        
        lines = data.strip().split("\n")
        if len(lines) < 2:
            return None
        
        # 解析表头（支持中英文、空格、制表符）
        header_line = lines[0]
        # 尝试不同的分隔符
        if "\t" in header_line:
            separator = "\t"
        elif "," in header_line:
            separator = ","
        else:
            separator = None
            return None
        
        headers = [h.strip() for h in header_line.split(separator)]
        
        # 标准化列名（支持多种写法）
        header_mapping = {
            "关键词": ["关键词", "keyword", "词", "名称"],
            "展现量": ["展现量", "展现", "impression", "曝光量", "曝光"],
            "点击量": ["点击量", "点击", "click", "点击数"],
            "花费": ["花费", "消耗", "cost", "金额", "费用"],
            "转化数": ["转化数", "转化", "conversion", "成交数", "订单数"],
            "ROI": ["ROI", "roi", "投产比", "回报率"],
            "点击率": ["点击率", "CTR", "ctr"],
            "转化率": ["转化率", "CVR", "cvr"],
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
                # 尝试转换为数字
                try:
                    value = values[i]
                    # 移除可能的单位（元、%等）
                    value = value.replace("元", "").replace("%", "").replace(",", "")
                    if "." in value:
                        row[header] = float(value)
                    else:
                        row[header] = int(value)
                except:
                    row[header] = values[i]
            
            # 计算缺失的指标
            if "点击率" not in row and "点击量" in row and "展现量" in row:
                if row["展现量"] > 0:
                    row["点击率"] = round(row["点击量"] / row["展现量"] * 100, 2)
            
            if "转化率" not in row and "转化数" in row and "点击量" in row:
                if row["点击量"] > 0:
                    row["转化率"] = round(row["转化数"] / row["点击量"] * 100, 2)
            
            parsed.append(row)
        
        return parsed if parsed else None
    
    async def _analyze_overall(self, platform: str, data: List[Dict]) -> Dict:
        """整体分析"""
        
        # 计算总体指标
        total_spend = sum(row.get("花费", 0) for row in data)
        total_conversions = sum(row.get("转化数", 0) for row in data)
        total_clicks = sum(row.get("点击量", 0) for row in data)
        total_impressions = sum(row.get("展现量", 0) for row in data)
        
        avg_roi = total_conversions / total_spend if total_spend > 0 else 0
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cvr = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        
        # 找出表现最好和最差的项
        sorted_by_roi = sorted(data, key=lambda x: x.get("ROI", 0), reverse=True)
        best_performers = sorted_by_roi[:3]
        worst_performers = sorted_by_roi[-3:]
        
        # 使用 AI 生成优化建议
        ai_suggestions = await self._generate_overall_suggestions(
            platform=platform,
            total_spend=total_spend,
            avg_roi=avg_roi,
            ctr=ctr,
            cvr=cvr,
            best_performers=best_performers,
            worst_performers=worst_performers
        )
        
        return {
            "summary": {
                "总花费": f"{total_spend:.2f}元",
                "总转化数": total_conversions,
                "平均ROI": f"{avg_roi:.2f}",
                "点击率": f"{ctr:.2f}%",
                "转化率": f"{cvr:.2f}%"
            },
            "best_performers": best_performers,
            "worst_performers": worst_performers,
            "ai_suggestions": ai_suggestions
        }
    
    async def _analyze_keywords(self, platform: str, data: List[Dict]) -> Dict:
        """关键词分析"""
        
        # 按ROI排序
        sorted_data = sorted(data, key=lambda x: x.get("ROI", 0), reverse=True)
        
        # 分类关键词
        high_roi = [row for row in sorted_data if row.get("ROI", 0) >= 2.0]
        medium_roi = [row for row in sorted_data if 1.0 <= row.get("ROI", 0) < 2.0]
        low_roi = [row for row in sorted_data if row.get("ROI", 0) < 1.0]
        
        # 使用 AI 生成建议
        ai_suggestions = await self._generate_keyword_suggestions(
            platform=platform,
            high_roi=high_roi,
            medium_roi=medium_roi,
            low_roi=low_roi
        )
        
        # 生成具体操作建议
        actions = {
            "立即增加预算": [kw.get("关键词", "") for kw in high_roi[:3]],
            "保持观察": [kw.get("关键词", "") for kw in medium_roi[:3]],
            "降低出价或暂停": [kw.get("关键词", "") for kw in low_roi[:3]]
        }
        
        return {
            "high_roi_keywords": high_roi[:5],
            "medium_roi_keywords": medium_roi[:5],
            "low_roi_keywords": low_roi[:5],
            "actions": actions,
            "ai_suggestions": ai_suggestions
        }
    
    async def _analyze_creative(self, platform: str, data: List[Dict]) -> Dict:
        """素材分析"""
        
        # 按点击率排序
        sorted_by_ctr = sorted(data, key=lambda x: x.get("点击率", 0), reverse=True)
        
        # 按转化率排序
        sorted_by_cvr = sorted(data, key=lambda x: x.get("转化率", 0), reverse=True)
        
        ai_suggestions = await self._generate_creative_suggestions(
            platform=platform,
            high_ctr=sorted_by_ctr[:3],
            high_cvr=sorted_by_cvr[:3]
        )
        
        return {
            "high_ctr_creatives": sorted_by_ctr[:5],
            "high_cvr_creatives": sorted_by_cvr[:5],
            "ai_suggestions": ai_suggestions
        }
    
    async def _analyze_audience(self, platform: str, data: List[Dict]) -> Dict:
        """人群分析"""
        
        # 按ROI排序
        sorted_data = sorted(data, key=lambda x: x.get("ROI", 0), reverse=True)
        
        ai_suggestions = await self._generate_audience_suggestions(
            platform=platform,
            data=sorted_data
        )
        
        return {
            "high_roi_audiences": sorted_data[:5],
            "low_roi_audiences": sorted_data[-5:],
            "ai_suggestions": ai_suggestions
        }
    
    async def _generate_overall_suggestions(self, platform: str, total_spend: float,
                                           avg_roi: float, ctr: float, cvr: float,
                                           best_performers: List[Dict],
                                           worst_performers: List[Dict]) -> str:
        """生成整体优化建议（优化版提示词）"""
        
        prompt = f"""你是一个有10年经验的{platform}投流优化专家。现在有个商家向你咨询投流优化建议。

**当前数据：**
- 总花费：{total_spend:.2f}元
- 平均ROI：{avg_roi:.2f}
- 点击率：{ctr:.2f}%
- 转化率：{cvr:.2f}%

**表现最好的3个：**
{json.dumps(best_performers, ensure_ascii=False, indent=2)}

**表现最差的3个：**
{json.dumps(worst_performers, ensure_ascii=False, indent=2)}

请以资深投流专家的身份，给出实用的优化建议：

1. **问题诊断**（2-3句话）
   - 当前最大的问题是什么？
   - ROI {avg_roi:.2f} 在行业中处于什么水平？

2. **立即执行的优化动作**（3-5条，每条要具体可执行）
   - 例如："暂停ROI<0.8的关键词XX、XX，每天可节省XX元"
   - 例如："把ROI>2.5的关键词XX的预算提高50%，从XX元/天增加到XX元/天"
   - 例如："点击率低于1%的素材全部下线，重新制作"

3. **预期效果**（1-2句话）
   - 如果执行这些优化，ROI预计能提升到多少？
   - 多久能看到效果？

**要求：**
- 语言简洁实用，像老师傅教徒弟一样
- 给出具体的数字和操作步骤
- 不要空话套话，每句话都要有价值
- 总字数控制在250字以内
"""
        
        messages = [
                    {"role": "system", "content": f"你是一个有10年经验的{platform}投流优化专家，擅长数据分析和ROI优化。你的建议总是具体、实用、可执行。"},
                    {"role": "user", "content": prompt}
            ]
        return self._call_api_with_retry(messages)
    async def _generate_keyword_suggestions(self, platform: str, high_roi: List[Dict],
                                           medium_roi: List[Dict], low_roi: List[Dict]) -> str:
        """生成关键词优化建议（优化版）"""
        
        prompt = f"""你是一个{platform}关键词优化专家。请分析以下关键词数据，给出优化建议：

**高ROI关键词（ROI>=2.0）：**
{json.dumps(high_roi[:5], ensure_ascii=False, indent=2)}

**中等ROI关键词（1.0<=ROI<2.0）：**
{json.dumps(medium_roi[:5], ensure_ascii=False, indent=2)}

**低ROI关键词（ROI<1.0）：**
{json.dumps(low_roi[:5], ensure_ascii=False, indent=2)}

请给出：

1. **高ROI关键词的共同特点**（2-3句话）
   - 为什么这些词ROI高？
   - 有什么规律？

2. **具体优化动作**（3-5条）
   - 例如："高ROI词XX，立即提高出价20%，从XX元提到XX元"
   - 例如："低ROI词XX，ROI只有0.5，建议暂停，每天节省XX元"

3. **新词拓展建议**（1-2句话）
   - 基于高ROI词，推荐哪些新词？

**要求：**
- 具体可执行
- 给出数字
- 控制在200字以内
"""
        
        messages = [
                    {"role": "system", "content": f"你是一个{platform}关键词优化专家。"},
                    {"role": "user", "content": prompt}
            ]
        return self._call_api_with_retry(messages)
    async def _generate_creative_suggestions(self, platform: str, high_ctr: List[Dict],
                                            high_cvr: List[Dict]) -> str:
        """生成素材优化建议"""
        
        prompt = f"""你是一个{platform}素材优化专家。请分析素材数据：

**高点击率素材：**
{json.dumps(high_ctr, ensure_ascii=False, indent=2)}

**高转化率素材：**
{json.dumps(high_cvr, ensure_ascii=False, indent=2)}

请给出：
1. 高点击率素材的特点（2句话）
2. 高转化率素材的特点（2句话）
3. 素材优化建议（3条）

控制在150字以内。
"""
        
        messages = [
                    {"role": "system", "content": f"你是一个{platform}素材优化专家。"},
                    {"role": "user", "content": prompt}
            ]
        return self._call_api_with_retry(messages)
    async def _generate_audience_suggestions(self, platform: str, data: List[Dict]) -> str:
        """生成人群优化建议"""
        
        prompt = f"""你是一个{platform}人群定向专家。请分析人群数据：

{json.dumps(data[:10], ensure_ascii=False, indent=2)}

请给出：
1. 高ROI人群的特征（2句话）
2. 人群定向优化建议（3条）

控制在120字以内。
"""
        
        messages = [
                    {"role": "system", "content": f"你是一个{platform}人群定向专家。"},
                    {"role": "user", "content": prompt}
            ]
        return self._call_api_with_retry(messages)