#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能问答升级系统
基于DeepSeek + 知识库的智能问答，让对话更自然、更有用
"""

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

class IntelligentQA:
    """智能问答系统"""
    
    def __init__(self, deepseek_api_key: str = None):
        """
        初始化智能问答系统
        
        Args:
            deepseek_api_key: DeepSeek API密钥（可选，从环境变量读取）
        """
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        self.knowledge_base = self._build_knowledge_base()
        self.logger = self._setup_logger()
        
        if not self.api_key:
            self.logger.warning("DeepSeek API密钥未设置，部分功能可能受限")
    
    def _setup_logger(self):
        """设置日志记录器"""
        import logging
        logger = logging.getLogger(__name__)
        return logger
    
    def _build_knowledge_base(self) -> Dict[str, List[Dict]]:
        """构建电商知识库（手动整理 + 用户案例）"""
        
        # 定价策略库
        pricing_strategies = [
            {
                "id": "price_strategy_1",
                "name": "渗透定价法",
                "description": "新产品上市时设定较低价格，快速占领市场份额",
                "适用场景": ["新产品上市", "竞争激烈市场", "价格敏感用户"],
                "优点": ["快速获取用户", "建立市场壁垒", "规模效应降低成本"],
                "缺点": ["初期利润低", "可能损害品牌形象", "提价困难"],
                "案例": "某手机品牌新品定价比竞品低20%，首月销量增长300%"
            },
            {
                "id": "price_strategy_2",
                "name": "撇脂定价法",
                "description": "新产品上市时设定较高价格，获取高额利润",
                "适用场景": ["创新产品", "品牌优势明显", "目标用户价格不敏感"],
                "优点": ["高利润回报", "树立高端形象", "为后续降价留空间"],
                "缺点": ["市场接受慢", "吸引竞争者进入", "需要强品牌支撑"],
                "案例": "某高端耳机品牌定价是市场均价3倍，仍保持高销量"
            },
            {
                "id": "price_strategy_3",
                "name": "竞争定价法",
                "description": "根据竞争对手价格设定自己的价格",
                "适用场景": ["成熟市场", "产品同质化", "价格透明市场"],
                "优点": ["降低价格战风险", "保持市场地位", "简单易行"],
                "缺点": ["利润空间受限", "缺乏差异化", "被动跟随"],
                "案例": "某充电器品牌始终比市场领头羊低5-10元"
            },
            {
                "id": "price_strategy_4",
                "name": "心理定价法",
                "description": "利用消费者心理设定价格，如9.9元、99元等",
                "适用场景": ["大众消费品", "冲动购买商品", "价格敏感品类"],
                "优点": ["提高购买意愿", "增加销量", "简单有效"],
                "缺点": ["可能损害品牌", "长期效果递减", "不适合高端产品"],
                "案例": "某日用品品牌将价格从10元调整为9.9元，销量增长25%"
            }
        ]
        
        # 广告优化案例库
        ad_optimization = [
            {
                "id": "ad_case_1",
                "title": "关键词优化提升ROI 150%",
                "问题": "广告点击成本高，转化率低",
                "解决方案": [
                    "分析搜索词报告，剔除无效关键词",
                    "增加长尾关键词，提高精准度",
                    "优化广告创意，突出产品卖点",
                    "分时段投放，集中在高转化时段"
                ],
                "效果": "ROI从1.2提升到3.0，点击成本降低40%",
                "适用产品": "电子产品、家居用品"
            },
            {
                "id": "ad_case_2",
                "title": "人群定向优化提升转化率80%",
                "问题": "广告曝光量大但转化少",
                "解决方案": [
                    "分析用户画像，精准定位目标人群",
                    "根据购买历史创建相似受众",
                    "排除无效人群（如已购买用户）",
                    "测试不同人群包，找到最优组合"
                ],
                "效果": "转化率从2%提升到3.6%，客单价提高20%",
                "适用产品": "服装、美妆、食品"
            },
            {
                "id": "ad_case_3",
                "title": "创意A/B测试优化点击率120%",
                "问题": "广告创意陈旧，点击率下降",
                "解决方案": [
                    "创建多版本创意（图片、文案、视频）",
                    "进行A/B测试，找到最优组合",
                    "分析用户反馈，持续优化",
                    "季节性更新创意，保持新鲜感"
                ],
                "效果": "点击率从1.5%提升到3.3%，转化成本降低35%",
                "适用产品": "所有品类"
            }
        ]
        
        # 季节性建议
        seasonal_tips = [
            {
                "season": "春季（3-5月）",
                "tips": [
                    "春季新品上市，注重产品图片和描述",
                    "配合节日营销（妇女节、劳动节）",
                    "清理冬季库存，回笼资金",
                    "准备夏季产品预热"
                ],
                "热门品类": ["春装", "户外用品", "家居清洁", "美妆护肤"]
            },
            {
                "season": "夏季（6-8月）",
                "tips": [
                    "防晒、降温产品需求旺盛",
                    "暑假期间，学生用品销量增长",
                    "注意物流时效，高温产品需特殊包装",
                    "夏季促销活动（618、暑期特惠）"
                ],
                "热门品类": ["夏装", "防晒用品", "冷饮", "游泳装备", "电子产品"]
            },
            {
                "season": "秋季（9-11月）",
                "tips": [
                    "开学季，文具、电子产品热销",
                    "秋季新品上市，注重品质和设计",
                    "双11大促准备，提前备货",
                    "换季清仓，处理夏季库存"
                ],
                "热门品类": ["秋装", "学习用品", "家电", "食品礼盒"]
            },
            {
                "season": "冬季（12-2月）",
                "tips": [
                    "保暖产品需求大，注重产品实用性",
                    "节日营销（双12、圣诞节、春节）",
                    "物流压力大，提前发货",
                    "年终促销，清理全年库存"
                ],
                "热门品类": ["冬装", "保暖用品", "年货", "礼品", "家居装饰"]
            }
        ]
        
        # 成功案例库
        success_cases = [
            {
                "id": "case_1",
                "商家类型": "小型服装店",
                "问题": "新品推广效果差，广告花费高",
                "解决方案": "使用智能选品+精准广告优化",
                "实施步骤": [
                    "分析市场趋势，选择潜力款式",
                    "优化产品标题和图片",
                    "精准关键词投放，排除无效流量",
                    "分时段优化广告出价"
                ],
                "效果": "月销售额从5万提升到15万，广告ROI从1.5提升到2.8",
                "关键成功因素": "数据驱动决策，持续优化"
            },
            {
                "id": "case_2",
                "商家类型": "电子产品代理商",
                "问题": "价格竞争激烈，利润空间小",
                "解决方案": "动态定价+差异化营销",
                "实施步骤": [
                    "实时监控竞品价格，自动调整",
                    "突出产品独特卖点（售后、赠品）",
                    "创建品牌内容，建立信任",
                    "优化产品组合，提高客单价"
                ],
                "效果": "利润率从15%提升到25%，复购率提高40%",
                "关键成功因素": "价格敏感度分析，价值营销"
            },
            {
                "id": "case_3",
                "商家类型": "食品特产店",
                "问题": "季节性明显，销量波动大",
                "解决方案": "季节性规划+多渠道营销",
                "实施步骤": [
                    "提前规划季节性产品线",
                    "建立私域流量（微信群、公众号）",
                    "节日营销活动策划",
                    "跨界合作，扩大受众"
                ],
                "效果": "全年销售额增长200%，淡季销量提升80%",
                "关键成功因素": "提前规划，多渠道布局"
            }
        ]
        
        # 常见问题解答
        faq = [
            {
                "question": "如何提高产品点击率？",
                "answer": "1. 优化产品主图（清晰、突出卖点）\n2. 撰写吸引人的标题（包含关键词）\n3. 设置有竞争力的价格\n4. 积累好评和销量数据\n5. 参与平台活动获取流量",
                "tags": ["点击率", "产品优化", "流量"]
            },
            {
                "question": "广告花费高但转化少怎么办？",
                "answer": "1. 检查关键词是否精准\n2. 优化广告创意和落地页\n3. 分析用户画像，调整定向\n4. 测试不同出价策略\n5. 排除无效流量来源",
                "tags": ["广告优化", "转化率", "ROI"]
            },
            {
                "question": "新品如何快速起量？",
                "answer": "1. 做好市场调研和竞品分析\n2. 优化产品基础信息（标题、图片、详情）\n3. 初期适当让利获取首批用户\n4. 积累基础销量和评价\n5. 配合广告推广扩大曝光",
                "tags": ["新品", "起量", "推广"]
            },
            {
                "question": "如何应对价格战？",
                "answer": "1. 分析成本结构，找到降价空间\n2. 突出产品差异化优势\n3. 提供增值服务（售后、赠品）\4. 建立品牌忠诚度\n5. 考虑产品组合销售提高客单价",
                "tags": ["价格战", "竞争", "差异化"]
            }
        ]
        
        return {
            "pricing_strategies": pricing_strategies,
            "ad_optimization": ad_optimization,
            "seasonal_tips": seasonal_tips,
            "success_cases": success_cases,
            "faq": faq
        }
    
    def _retrieve_knowledge(self, question: str, max_results: int = 3) -> List[Dict]:
        """检索相关知识"""
        relevant_knowledge = []
        
        # 简单的关键词匹配检索
        question_lower = question.lower()
        
        # 检查定价策略
        for strategy in self.knowledge_base["pricing_strategies"]:
            if any(keyword in question_lower for keyword in ["定价", "价格", "成本", "利润"]):
                relevant_knowledge.append({
                    "type": "pricing_strategy",
                    "content": strategy
                })
        
        # 检查广告优化
        for ad_case in self.knowledge_base["ad_optimization"]:
            if any(keyword in question_lower for keyword in ["广告", "推广", "投放", "流量", "roi"]):
                relevant_knowledge.append({
                    "type": "ad_optimization",
                    "content": ad_case
                })
        
        # 检查季节性建议
        for season_tip in self.knowledge_base["seasonal_tips"]:
            if any(keyword in question_lower for keyword in ["季节", "旺季", "淡季", "节日"]):
                relevant_knowledge.append({
                    "type": "seasonal_tip",
                    "content": season_tip
                })
        
        # 检查成功案例
        for case in self.knowledge_base["success_cases"]:
            if any(keyword in question_lower for keyword in ["案例", "成功", "经验", "效果"]):
                relevant_knowledge.append({
                    "type": "success_case",
                    "content": case
                })
        
        # 检查FAQ
        for faq_item in self.knowledge_base["faq"]:
            if faq_item["question"].lower() in question_lower or \
               any(keyword in question_lower for keyword in faq_item["tags"]):
                relevant_knowledge.append({
                    "type": "faq",
                    "content": faq_item
                })
        
        return relevant_knowledge[:max_results]
    
    async def answer(self, question: str, user_context: Dict = None) -> Dict[str, Any]:
        """
        智能回答用户问题
        
        Args:
            question: 用户问题
            user_context: 用户上下文（可选）
            
        Returns:
            Dict: 回答结果
        """
        if user_context is None:
            user_context = {}
        
        try:
            # 1. 检索相关知识
            relevant_knowledge = self._retrieve_knowledge(question)
            
            # 2. 准备上下文
            context = {
                'user_history': user_context.get('history', '暂无历史记录'),
                'current_products': user_context.get('products', '暂无产品信息'),
                'knowledge': relevant_knowledge,
                'question_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 3. 构建提示词
            prompt = self._build_prompt(question, context)
            
            # 4. 调用DeepSeek生成回答
            answer_text = await self._call_deepseek(prompt)
            
            # 5. 提取可执行操作
            actions = self._extract_actions(answer_text)
            
            # 6. 查找相似案例
            similar_cases = self._find_similar_cases(question)
            
            result = {
                'answer': answer_text,
                'suggested_actions': actions,
                'related_cases': similar_cases,
                'relevant_knowledge': relevant_knowledge,
                'confidence': self._calculate_confidence(question, answer_text),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"智能问答完成: 问题长度={len(question)}, 相关知识点={len(relevant_knowledge)}")
            return result
            
        except Exception as e:
            self.logger.error(f"智能问答失败: {e}")
            return self._get_fallback_answer(question)
    
    def _build_prompt(self, question: str, context: Dict) -> str:
        """构建提示词"""
        
        # 格式化相关知识
        knowledge_text = ""
        for item in context['knowledge']:
            knowledge_text += f"\n【{item['type']}】\n"
            if item['type'] == 'pricing_strategy':
                strategy = item['content']
                knowledge_text += f"策略名称：{strategy['name']}\n"
                knowledge_text += f"描述：{strategy['description']}\n"
                knowledge_text += f"适用场景：{', '.join(strategy['适用场景'])}\n"
                knowledge_text += f"案例：{strategy['案例']}\n"
            elif item['type'] == 'ad_optimization':
                case = item['content']
                knowledge_text += f"案例标题：{case['title']}\n"
                knowledge_text += f"解决方案：{'；'.join(case['解决方案'])}\n"
                knowledge_text += f"效果：{case['效果']}\n"
            elif item['type'] == 'faq':
                faq = item['content']
                knowledge_text += f"问题：{faq['question']}\n"
                knowledge_text += f"答案：{faq['answer']}\n"
        
        prompt = f"""你是拼多多运营专家，拥有丰富的电商运营经验。请根据以下信息回答用户问题。

用户问题：{question}

用户背景信息：
- 历史记录：{context['user_history']}
- 当前产品：{context['current_products']}
- 提问时间：{context['question_time']}

相关知识库：
{knowledge_text}

请按照以下格式给出回答：
1. 【直接回答】用简洁的语言直接回答用户问题
2. 【具体建议】提供3-5条具体、可操作的建议
3. 【预期效果】说明实施建议后的预期效果
4. 【注意事项】提醒需要注意的风险或要点

请确保回答：
- 专业、准确、实用
- 基于电商运营最佳实践
- 考虑拼多多平台特点
- 给出可量化的建议

现在开始回答："""
        
        return prompt
    
    async def _call_deepseek(self, prompt: str) -> str:
        """调用DeepSeek API"""
        if not self.api_key:
            # 如果没有API密钥，使用模拟回答
            return self._generate_mock_answer(prompt)
        
        try:
            import openai
            
            # 配置OpenAI客户端（DeepSeek兼容OpenAI API）
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是拼多多运营专家，专门帮助商家优化店铺运营。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"调用DeepSeek API失败: {e}")
            return self._generate_mock_answer(prompt)
    
    def _generate_mock_answer(self, prompt: str) -> str:
        """生成
模拟回答（用于测试）"""
        # 从提示词中提取关键信息
        if "定价" in prompt or "价格" in prompt:
            return """【直接回答】关于定价策略，我建议采用竞争定价法结合心理定价。

【具体建议】
1. 分析竞品价格分布，设定比市场均价低5-10%的价格
2. 使用心理定价，如99元、199元等尾数定价
3. 根据销量和利润动态调整价格
4. 提供价格保护，建立用户信任
5. 考虑产品组合定价，提高客单价

【预期效果】
- 价格竞争力提升，点击率增加20-30%
- 转化率提高15-25%
- 整体销售额增长30-50%

【注意事项】
- 避免恶性价格战，保持合理利润空间
- 定期监控竞品价格变化
- 考虑成本上涨对定价的影响"""
        elif "广告" in prompt or "推广" in prompt:
            return """【直接回答】关于广告优化，我建议从关键词、创意、定向三方面入手。

【具体建议】
1. 分析搜索词报告，剔除无效关键词，增加长尾词
2. 进行创意A/B测试，优化图片和文案
3. 精准人群定向，根据用户画像调整投放
4. 分时段优化出价，集中在高转化时段
5. 设置预算预警，避免超支

【预期效果】
- 广告点击率提升50-100%
- 转化成本降低20-40%
- ROI从1.5提升到2.5以上

【注意事项】
- 避免频繁调整，每次测试至少3-5天
- 关注广告疲劳度，定期更新创意
- 结合自然流量，优化整体流量结构"""
        else:
            return """【直接回答】根据您的提问，我提供以下综合建议。

【具体建议】
1. 做好市场调研，了解目标用户需求
2. 优化产品基础信息（标题、图片、详情页）
3. 建立数据监控体系，跟踪关键指标
4. 制定季节性营销计划，提前布局
5. 注重用户评价和口碑建设

【预期效果】
- 店铺整体流量提升30-50%
- 转化率提高20-30%
- 用户复购率增加15-25%

【注意事项】
- 电商运营需要持续优化，不能一蹴而就
- 关注平台规则变化，及时调整策略
- 建立风险预警机制，应对市场变化"""
    
    def _extract_actions(self, answer_text: str) -> List[Dict]:
        """从回答中提取可执行操作"""
        actions = []
        
        # 提取具体建议部分
        if "【具体建议】" in answer_text:
            suggestions_section = answer_text.split("【具体建议】")[1].split("【")[0]
            suggestions = [s.strip() for s in suggestions_section.split("\n") if s.strip() and not s.startswith("【")]
            
            for i, suggestion in enumerate(suggestions[:5], 1):
                # 清理编号
                clean_suggestion = re.sub(r'^\d+[\.、]?\s*', '', suggestion)
                if clean_suggestion:
                    actions.append({
                        'id': f'action_{i}',
                        'description': clean_suggestion,
                        'priority': 'high' if i <= 2 else 'medium',
                        'estimated_time': '1-3天',
                        'expected_impact': '中高'
                    })
        
        # 如果没有提取到，添加默认操作
        if not actions:
            actions = [
                {
                    'id': 'action_1',
                    'description': '分析当前店铺数据，找出优化点',
                    'priority': 'high',
                    'estimated_time': '1天',
                    'expected_impact': '高'
                },
                {
                    'id': 'action_2',
                    'description': '制定本周优化计划，设定具体目标',
                    'priority': 'high',
                    'estimated_time': '半天',
                    'expected_impact': '中'
                },
                {
                    'id': 'action_3',
                    'description': '执行优化措施，监控效果',
                    'priority': 'medium',
                    'estimated_time': '持续',
                    'expected_impact': '中高'
                }
            ]
        
        return actions
    
    def _find_similar_cases(self, question: str) -> List[Dict]:
        """查找相似案例"""
        similar_cases = []
        question_lower = question.lower()
        
        for case in self.knowledge_base["success_cases"]:
            # 简单关键词匹配
            case_text = json.dumps(case, ensure_ascii=False).lower()
            if any(keyword in question_lower for keyword in ["新品", "推广", "广告", "定价", "竞争"]):
                # 检查是否有相关关键词在案例中
                keywords_in_case = sum(1 for keyword in ["新品", "推广", "广告", "定价", "竞争"] 
                                     if keyword in case_text)
                if keywords_in_case >= 1:
                    similar_cases.append(case)
        
        return similar_cases[:2]  # 最多返回2个相似案例
    
    def _calculate_confidence(self, question: str, answer: str) -> float:
        """计算回答置信度"""
        # 简单置信度计算
        confidence = 0.7  # 基础置信度
        
        # 根据问题长度调整
        if len(question) > 20:
            confidence += 0.1
        
        # 根据回答质量调整
        if "【具体建议】" in answer and len(answer) > 100:
            confidence += 0.1
        
        # 根据是否有案例调整
        if "案例" in answer or "经验" in answer:
            confidence += 0.1
        
        return min(confidence, 0.95)
    
    def _get_fallback_answer(self, question: str) -> Dict[str, Any]:
        """获取备用回答"""
        return {
            'answer': f"关于'{question}'，我建议您：\n1. 分析当前店铺数据，找出关键问题点\n2. 参考行业最佳实践，制定优化方案\n3. 小范围测试，验证效果后再全面推广\n4. 持续监控数据，及时调整策略\n\n如果您需要更具体的建议，请提供更多背景信息。",
            'suggested_actions': [
                {
                    'id': 'action_1',
                    'description': '收集店铺运营数据，进行初步分析',
                    'priority': 'high',
                    'estimated_time': '1天',
                    'expected_impact': '中'
                }
            ],
            'related_cases': [],
            'relevant_knowledge': [],
            'confidence': 0.5,
            'generated_at': datetime.utcnow().isoformat(),
            'note': '系统暂时无法提供详细建议，建议咨询专业运营人员'
        }
    
    def get_quick_answer(self, question: str) -> str:
        """
        快速回答（不调用API，基于知识库）
        
        Args:
            question: 用户问题
            
        Returns:
            str: 快速回答
        """
        # 检查FAQ
        for faq_item in self.knowledge_base["faq"]:
            if faq_item["question"].lower() in question.lower():
                return faq_item["answer"]
        
        # 根据关键词提供快速建议
        question_lower = question.lower()
        
        if any(keyword in question_lower for keyword in ["定价", "价格"]):
            return "定价建议：1. 分析竞品价格 2. 考虑成本利润 3. 使用心理定价 4. 动态调整"
        elif any(keyword in question_lower for keyword in ["广告", "推广"]):
            return "广告优化：1. 精准关键词 2. 优化创意 3. 人群定向 4. 分时段投放"
        elif any(keyword in question_lower for keyword in ["新品", "起量"]):
            return "新品推广：1. 优化基础信息 2. 积累基础销量 3. 配合广告 4. 收集反馈"
        else:
            return "建议：1. 数据分析 2. 制定计划 3. 测试优化 4. 持续改进"
    
    def export_knowledge_summary(self) -> Dict[str, Any]:
        """导出知识库摘要"""
        summary = {
            'total_strategies': len(self.knowledge_base["pricing_strategies"]),
            'total_ad_cases': len(self.knowledge_base["ad_optimization"]),
            'total_seasonal_tips': len(self.knowledge_base["seasonal_tips"]),
            'total_success_cases': len(self.knowledge_base["success_cases"]),
            'total_faq': len(self.knowledge_base["faq"]),
            'last_updated': datetime.utcnow().isoformat(),
            'coverage_areas': ['定价策略', '广告优化', '季节性运营', '成功案例', '常见问题']
        }
        
        return summary

# 使用示例
if __name__ == "__main__":
    import asyncio
    
    qa_system = IntelligentQA()
    
    # 示例：快速回答
    quick_answer = qa_system.get_quick_answer("如何提高广告转化率？")
    print("快速回答:", quick_answer)
    
    # 示例：完整问答
    async def test_full_qa():
        user_context = {
            'history': '经营服装店3个月，主要销售女装',
            'products': '夏季连衣裙、T恤、短裤',
            'monthly_sales': '5万元',
            'ad_spend': '5000元'
        }
        
        result = await qa_system.answer("新品如何快速起量？", user_context)
        print("\n完整问答结果:", json.dumps(result, indent=2, ensure_ascii=False))
    
    # 运行异步测试
    asyncio.run(test_full_qa())
    
    # 示例：知识库摘要
    summary = qa_system.export_knowledge_summary()
    print("\n知识库摘要:", json.dumps(summary, indent=2, ensure_ascii=False))
