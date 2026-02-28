#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险监控系统
实时监控广告和产品，及时发现风险
"""

from datetime import datetime, timedelta
from typing import Dict, List
import random

class RiskMonitor:
    """风险监控器"""
    
    def __init__(self):
        self.risk_thresholds = {
            'roi_low': 0.5,  # ROI低于0.5为高风险
            'budget_overrun': 1.2,  # 预算超支20%为中风险
            'conversion_drop': 0.3  # 转化率下降30%为高风险
        }
    
    async def monitor_campaigns(self, user_id: int) -> List[Dict]:
        """
        监控用户的广告活动
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Dict]: 风险列表
        """
        risks = []
        
        # 模拟风险检测（实际应该从数据库读取真实数据）
        # 这里先返回示例数据
        
        # 随机生成一些风险示例
        risk_types = [
            {
                'severity': 'high',
                'title': 'ROI 严重偏低',
                'description': '广告计划 #1234 的 ROI 仅为 0.3，远低于目标值',
                'suggestion': '建议暂停该计划，重新优化定向和创意'
            },
            {
                'severity': 'medium',
                'title': '预算即将超支',
                'description': '本月广告预算已使用 85%，还有 10 天',
                'suggestion': '建议调整日预算或暂停低效计划'
            },
            {
                'severity': 'low',
                'title': '转化率小幅下降',
                'description': '产品 A 的转化率从 3.5% 降至 3.2%',
                'suggestion': '关注用户反馈，优化详情页'
            }
        ]
        
        # 随机返回 0-3 个风险
        num_risks = random.randint(0, 3)
        risks = random.sample(risk_types, num_risks) if num_risks > 0 else []
        
        return risks
    
    def calculate_risk_score(self, metrics: Dict) -> float:
        """
        计算风险评分
        
        Args:
            metrics: 指标数据
            
        Returns:
            float: 风险评分 (0-1)
        """
        score = 0.0
        
        # ROI 风险
        if 'roi' in metrics:
            if metrics['roi'] < self.risk_thresholds['roi_low']:
                score += 0.4
        
        # 预算风险
        if 'budget_usage' in metrics:
            if metrics['budget_usage'] > self.risk_thresholds['budget_overrun']:
                score += 0.3
        
        # 转化率风险
        if 'conversion_change' in metrics:
            if metrics['conversion_change'] < -self.risk_thresholds['conversion_drop']:
                score += 0.3
        
        return min(score, 1.0)
    
    def get_risk_level(self, score: float) -> str:
        """
        根据评分获取风险等级
        
        Args:
            score: 风险评分
            
        Returns:
            str: 风险等级 (high/medium/low)
        """
        if score >= 0.7:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        else:
            return 'low'
