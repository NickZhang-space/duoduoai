#!/usr/bin/env python3
"""
用户画像分析器
分析用户行为数据，生成完整的用户画像
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics

class UserProfiler:
    """用户画像分析器"""
    
    def __init__(self, db=None):
        self.db = db
    
    async def build_profile(self, user_id: str) -> Dict[str, Any]:
        """构建用户完整画像"""
        
        # 模拟数据（实际应从数据库获取）
        behaviors = self._get_mock_behaviors(user_id)
        
        profile = {
            'user_id': user_id,
            'demographics': self._analyze_demographics(behaviors),
            'preferences': self._analyze_preferences(behaviors),
            'behavior_patterns': self._analyze_behavior_patterns(behaviors),
            'success_factors': self._analyze_success_factors(behaviors),
            'lifecycle_stage': self._determine_lifecycle_stage(behaviors)
        }
        
        return profile
    
    def _get_mock_behaviors(self, user_id: str) -> List[Dict]:
        """获取模拟行为数据"""
        return [
            {'action': 'product_selection', 'category': '服装', 'price': 89, 'success': True, 'timestamp': '2026-02-27 10:30:00'},
            {'action': 'ad_optimization', 'category': '服装', 'price': 120, 'success': True, 'timestamp': '2026-02-27 14:20:00'},
            {'action': 'product_selection', 'category': '美妆', 'price': 150, 'success': False, 'timestamp': '2026-02-26 09:15:00'},
            {'action': 'pricing_strategy', 'category': '服装', 'price': 99, 'success': True, 'timestamp': '2026-02-26 16:45:00'},
            {'action': 'ad_optimization', 'category': '食品', 'price': 45, 'success': True, 'timestamp': '2026-02-25 11:30:00'},
        ]
    
    def _analyze_demographics(self, behaviors: List[Dict]) -> Dict:
        """分析用户基本信息"""
        if not behaviors:
            return {
                'active_days': 0,
                'total_actions': 0,
                'avg_daily_actions': 0
            }
        
        dates = set([b['timestamp'][:10] for b in behaviors])
        
        return {
            'active_days': len(dates),
            'total_actions': len(behaviors),
            'avg_daily_actions': round(len(behaviors) / max(len(dates), 1), 1)
        }
    
    def _analyze_preferences(self, behaviors: List[Dict]) -> Dict:
        """分析用户偏好"""
        if not behaviors:
            return {
                'preferred_categories': [],
                'avg_price': 0,
                'price_range': {'min': 0, 'max': 0}
            }
        
        # 统计品类
        categories = {}
        for b in behaviors:
            cat = b.get('category', '未知')
            categories[cat] = categories.get(cat, 0) + 1
        
        # 排序
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        preferred_categories = [cat for cat, _ in sorted_cats[:3]]
        
        # 价格分析
        prices = [b['price'] for b in behaviors if 'price' in b]
        
        return {
            'preferred_categories': preferred_categories,
            'avg_price': round(statistics.mean(prices), 2) if prices else 0,
            'price_range': {
                'min': min(prices) if prices else 0,
                'max': max(prices) if prices else 0
            }
        }
    
    def _analyze_behavior_patterns(self, behaviors: List[Dict]) -> Dict:
        """分析行为模式"""
        if not behaviors:
            return {
                'peak_hours': [],
                'peak_days': [],
                'action_distribution': {}
            }
        
        # 时间分析
        hours = {}
        days = {}
        actions = {}
        
        for b in behaviors:
            timestamp = b.get('timestamp', '')
            if timestamp:
                hour = int(timestamp[11:13])
                day = datetime.strptime(timestamp[:10], '%Y-%m-%d').strftime('%A')
                
                hours[hour] = hours.get(hour, 0) + 1
                days[day] = days.get(day, 0) + 1
            
            action = b.get('action', '未知')
            actions[action] = actions.get(action, 0) + 1
        
        # 找出高峰时段
        sorted_hours = sorted(hours.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [h for h, _ in sorted_hours[:3]]
        
        sorted_days = sorted(days.items(), key=lambda x: x[1], reverse=True)
        peak_days = [d for d, _ in sorted_days[:2]]
        
        return {
            'peak_hours': peak_hours,
            'peak_days': peak_days,
            'action_distribution': actions
        }
    
    def _analyze_success_factors(self, behaviors: List[Dict]) -> Dict:
        """分析成功因素"""
        if not behaviors:
            return {
                'success_rate': 0,
                'success_patterns': []
            }
        
        total = len(behaviors)
        success_count = sum(1 for b in behaviors if b.get('success', False))
        success_rate = round(success_count / total * 100, 1) if total > 0 else 0
        
        # 分析成功模式
        success_behaviors = [b for b in behaviors if b.get('success', False)]
        
        patterns = []
        if success_behaviors:
            # 成功的品类
            success_cats = {}
            for b in success_behaviors:
                cat = b.get('category', '未知')
                success_cats[cat] = success_cats.get(cat, 0) + 1
            
            if success_cats:
                top_cat = max(success_cats.items(), key=lambda x: x[1])
                patterns.append(f"{top_cat[0]}品类成功率高")
            
            # 成功的价格区间
            success_prices = [b['price'] for b in success_behaviors if 'price' in b]
            if success_prices:
                avg_success_price = round(statistics.mean(success_prices), 2)
                patterns.append(f"¥{avg_success_price}左右价格段表现好")
        
        return {
            'success_rate': success_rate,
            'success_patterns': patterns
        }
    
    def _determine_lifecycle_stage(self, behaviors: List[Dict]) -> str:
        """判断用户生命周期阶段"""
        if not behaviors:
            return '新用户'
        
        total_actions = len(behaviors)
        
        if total_actions < 5:
            return '新手期'
        elif total_actions < 20:
            return '成长期'
        elif total_actions < 50:
            return '成熟期'
        else:
            return '专家级'
    
    async def get_behavior_heatmap(self, user_id: str) -> Dict[str, Any]:
        """获取行为热力图数据"""
        
        # 模拟7天x24小时的热力图数据
        heatmap = {
            'labels': [f'{i}时' for i in range(24)],
            'datasets': []
        }
        
        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        for day in days:
            # 生成模拟数据（实际应从数据库统计）
            data = [0] * 24
            # 模拟高峰时段
            for hour in [9, 10, 11, 14, 15, 16, 20, 21]:
                data[hour] = 3 + (hash(day + str(hour)) % 5)
            
            heatmap['datasets'].append({
                'label': day,
                'data': data
            })
        
        return heatmap

