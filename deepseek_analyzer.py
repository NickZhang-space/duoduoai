"""
DeepSeek AI 分析模块 - 调试版本
"""

import os
import json
from typing import Dict, List, Any
import httpx
from datetime import datetime
import traceback

# DeepSeek API 配置
DEEPSEEK_API_KEY = "sk-7ca3b444853141068d412409878078b7"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

async def analyze_with_deepseek(data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
    """使用 DeepSeek 分析数据"""
    
    print(f"[DEBUG] 开始分析，类型: {analysis_type}")
    
    try:
        # 构建提示词
        if analysis_type == "suggestions":
            prompt = build_suggestions_prompt(data)
        elif analysis_type == "diagnosis":
            prompt = build_diagnosis_prompt(data)
        elif analysis_type == "growth":
            prompt = build_growth_prompt(data)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        print(f"[DEBUG] 提示词长度: {len(prompt)}")
        
        # 调用 DeepSeek API
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("[DEBUG] 开始调用 DeepSeek API...")
            
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的拼多多广告优化专家，擅长分析推广数据并给出可执行的优化建议。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            print(f"[DEBUG] API 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                print(f"[DEBUG] AI 返回内容长度: {len(content)}")
                print(f"[DEBUG] AI 返回内容前100字: {content[:100]}")
                
                # 解析 AI 返回的 JSON
                try:
                    parsed = json.loads(content)
                    return {
                        "success": True,
                        "data": parsed,
                        "timestamp": datetime.now().isoformat()
                    }
                except json.JSONDecodeError as je:
                    print(f"[DEBUG] JSON 解析失败: {je}")
                    # 如果不是 JSON，返回原始文本
                    return {
                        "success": True,
                        "data": {"text": content},
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                error_msg = f"API error: {response.status_code}, {response.text}"
                print(f"[DEBUG] API 错误: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "message": "DeepSeek API 返回错误"
                }
                
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"[DEBUG] 异常发生: {e}")
        print(f"[DEBUG] 异常详情:\n{error_detail}")
        return {
            "success": False,
            "error": str(e),
            "error_detail": error_detail,
            "message": "调用 DeepSeek API 失败"
        }

def build_suggestions_prompt(data: Dict[str, Any]) -> str:
    """构建 AI 建议的提示词"""
    
    prompt = f"""
你是一位资深的拼多多推广优化专家，拥有10年以上的电商运营经验。请分析以下推广数据，生成3条非常具体、可执行的优化建议。

数据概览：
{json.dumps(data, ensure_ascii=False, indent=2)}

请以 JSON 格式返回，格式如下：
{{
  "suggestions": [
    {{
      "type": "调整预算/优化关键词/调整时段/优化人群/调整出价",
      "problem": "详细的问题描述，包含具体数据和对比",
      "suggestion": "非常具体的操作步骤，包含：1)哪个计划/关键词 2)从多少调整到多少 3)为什么这样调整 4)具体操作路径",
      "expected_effect": "量化的预期效果，包含具体数字和时间范围",
      "risk_level": "低风险/中风险/高风险",
      "observation_days": 3-7
    }}
  ]
}}

要求（非常重要）：
1. **problem** 必须包含：
   - 具体的数据（如：ROI从2.5降到1.8，下降28%）
   - 时间范围（如：过去7天）
   - 对比数据（如：行业平均ROI 2.2）
   
2. **suggestion** 必须包含：
   - 具体的计划/关键词名称（如：计划A"夏季新款"）
   - 精确的调整数值（如：日预算从200元提升至350元）
   - 调整理由（如：该计划ROI 3.2，远高于平均1.8）
   - 操作步骤（如：进入推广后台 → 找到计划A → 修改日预算）
   
3. **expected_effect** 必须包含：
   - 量化指标（如：ROI从1.8提升至2.1-2.3）
   - 时间范围（如：3-5天内）
   - 具体收益（如：预计增加销售额15%-20%，约¥3000-¥4000）

4. 建议类型要多样化：
   - 第1条：预算调整（具体到计划名称和金额）
   - 第2条：关键词优化（列出具体要暂停/提价的词）
   - 第3条：时段或人群优化（具体时段和溢价比例）

5. 数据要真实可信：
   - 使用合理的数字范围
   - 符合拼多多推广的实际情况
   - 避免过于夸张的效果预期

示例（参考这个详细程度）：
{{
  "type": "调整预算",
  "problem": "计划A'夏季连衣裙'的ROI为3.2，远高于整体平均ROI 1.8，但日预算仅200元，在下午3点就花完了，错失了晚上8-11点的黄金时段（该时段转化率是全天平均的1.8倍）。而计划B'秋季外套'的ROI仅1.1，低于盈亏平衡线1.5，却每天消耗150元。",
  "suggestion": "1. 将计划A'夏季连衣裙'的日预算从200元提升至350元（+75%）\n2. 将计划B'秋季外套'的日预算从150元降低至80元（-47%）\n3. 操作路径：推广后台 → 搜索推广 → 找到对应计划 → 点击'修改预算'\n4. 调整理由：计划A每花1元能赚3.2元，应该加大投入；计划B每花1元只赚1.1元，接近亏损，应该减少投入。",
  "expected_effect": "预计3-5天内：\n- 整体ROI从1.8提升至2.1-2.3（+17%-28%）\n- 日销售额从¥2500增加至¥2900-¥3100（+16%-24%）\n- 总广告花费保持在350元左右（基本不变）\n- 计划A销售额预计增加¥800-¥1000/天",
  "risk_level": "低风险",
  "observation_days": 5
}}
"""
    return prompt

def build_diagnosis_prompt(data: Dict[str, Any]) -> str:
    """构建诊断分析的提示词"""
    
    prompt = f"""
请诊断以下拼多多推广数据中的问题，找出 Top 3 拖累项。

数据概览：
{json.dumps(data, ensure_ascii=False, indent=2)}

请以 JSON 格式返回。
"""
    return prompt

def build_growth_prompt(data: Dict[str, Any]) -> str:
    """构建增长机会的提示词"""
    
    prompt = f"""
请分析以下拼多多推广数据，找出 3 个增长机会。

数据概览：
{json.dumps(data, ensure_ascii=False, indent=2)}

请以 JSON 格式返回。
"""
    return prompt

def get_sample_data() -> Dict[str, Any]:
    """获取示例数据"""
    return {
        "search_campaigns": [
            {
                "date": "2026-03-02",
                "plan_name": "搜索推广-日常",
                "keyword": "女装连衣裙",
                "bid": 0.8,
                "impressions": 12500,
                "clicks": 380,
                "ctr": 3.04,
                "cpc": 0.75,
                "cost": 285,
                "orders": 15,
                "revenue": 1200,
                "roi": 4.21
            }
        ]
    }
