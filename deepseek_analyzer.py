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
请分析以下拼多多推广数据，生成 3 条具体的优化建议。

数据概览：
{json.dumps(data, ensure_ascii=False, indent=2)}

请以 JSON 格式返回，格式如下：
{{
  "suggestions": [
    {{
      "type": "调整预算",
      "problem": "问题描述",
      "suggestion": "具体建议",
      "expected_effect": "预期效果",
      "risk_level": "低风险",
      "observation_days": 3
    }}
  ]
}}

要求：
1. 建议要具体可执行
2. 包含数据支撑
3. 说明预期效果
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
