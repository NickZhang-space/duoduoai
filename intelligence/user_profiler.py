#!/usr/bin/env python3
"""
用户画像分析器（增强版）
分析用户行为数据，生成完整的用户画像
新增：用户标签系统、用户分群、画像可视化
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
            'lifecycle_stage': self._determine_lifecycle_stage(behaviors),
            # 新增功能
            'tags': self._generate_user_tags(behaviors),
            'segment': self._determine_user_segment(behaviors),
            'value_score': self._calculate_value_score(behaviors),
            'visualization_data': self._prepare_visualization_data(behaviors)
        }
        
        return profile
    
    def _get_mock_behaviors(self, user_id: str) -> List[Dict]:
        """获取模拟行为数据"""
        import random
        
        # 根据user_id生成不同的行为模式
        seed = int(user_id) if user_id.isdigit() else hash(user_id)
        random.seed(seed)
        
        behaviors = []
        categories = ['服装', '数码配件', '美妆', '食品', '家居']
        actions = ['product_selection', 'ad_optimization', 'pricing_strategy', 'competitor_analysis']
        
        # 生成5-20条行为记录
        num_behaviors = random.randint(5, 20)
        for i in range(num_behaviors):
            days_ago = random.randint(0, 30)
            timestamp = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            behaviors.append({
                'action': random.choice(actions),
                'category': random.choice(categories),
                'price': round(random.uniform(20, 200), 1),
                'success': random.choice([True, True, True, False]),  # 75%成功率
                'timestamp': timestamp
            })
        
        return sorted(behaviors, key=lambda x: x['timestamp'])
    
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
    
    def _generate_user_tags(self, behaviors: List[Dict]) -> List[str]:
        """生成用户标签"""
        tags = []
        
        if not behaviors:
            return ['新用户']
        
        # 活跃度标签
        active_days = len(set([b['timestamp'][:10] for b in behaviors]))
        if active_days >= 20:
            tags.append('高活跃')
        elif active_days >= 10:
            tags.append('中活跃')
        else:
            tags.append('低活跃')
        
        # 消费能力标签
        prices = [b['price'] for b in behaviors if 'price' in b]
        if prices:
            avg_price = statistics.mean(prices)
            if avg_price >= 150:
                tags.append('高消费')
            elif avg_price >= 80:
                tags.append('中消费')
            else:
                tags.append('低消费')
        
        # 偏好类目标签
        categories = {}
        for b in behaviors:
            cat = b.get('category', '未知')
            categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            top_cat = max(categories.items(), key=lambda x: x[1])[0]
            tags.append(f'{top_cat}爱好者')
        
        # 成功率标签
        success_count = sum(1 for b in behaviors if b.get('success', False))
        success_rate = success_count / len(behaviors) if behaviors else 0
        if success_rate >= 0.8:
            tags.append('优化高手')
        elif success_rate >= 0.6:
            tags.append('稳定发展')
        else:
            tags.append('需要指导')
        
        # 行为特征标签
        actions = [b.get('action') for b in behaviors]
        if actions.count('ad_optimization') > len(actions) * 0.4:
            tags.append('广告优化专家')
        if actions.count('pricing_strategy') > len(actions) * 0.3:
            tags.append('定价策略师')
        
        return tags
    
    def _determine_user_segment(self, behaviors: List[Dict]) -> Dict:
        """用户分群"""
        if not behaviors:
            return {
                'segment': '新用户',
                'description': '刚注册的新用户',
                'strategy': '提供新手引导和基础教程'
            }
        
        # 计算关键指标
        total_actions = len(behaviors)
        active_days = len(set([b['timestamp'][:10] for b in behaviors]))
        success_count = sum(1 for b in behaviors if b.get('success', False))
        success_rate = success_count / total_actions if total_actions > 0 else 0
        prices = [b['price'] for b in behaviors if 'price' in b]
        avg_price = statistics.mean(prices) if prices else 0
        
        # 分群逻辑
        if total_actions >= 20 and success_rate >= 0.7 and avg_price >= 100:
            return {
                'segment': '高价值用户',
                'description': '活跃度高、成功率高、消费能力强',
                'strategy': '提供VIP服务和高级功能',
                'color': '#FFD700'
            }
        elif total_actions >= 10 and success_rate >= 0.6:
            return {
                'segment': '成长用户',
                'description': '有一定经验，表现稳定',
                'strategy': '推荐进阶功能和优化技巧',
                'color': '#4CAF50'
            }
        elif total_actions < 5:
            return {
                'segment': '新用户',
                'description': '刚开始使用系统',
                'strategy': '提供新手引导和基础教程',
                'color': '#2196F3'
            }
        elif active_days < 3 and total_actions < 10:
            return {
                'segment': '流失风险用户',
                'description': '活跃度低，可能流失',
                'strategy': '发送激活邮件，提供优惠券',
                'color': '#F44336'
            }
        else:
            return {
                'segment': '普通用户',
                'description': '正常使用中',
                'strategy': '持续提供价值，增加粘性',
                'color': '#9E9E9E'
            }
    
    def _calculate_value_score(self, behaviors: List[Dict]) -> Dict:
        """计算用户价值分"""
        if not behaviors:
            return {
                'total_score': 0,
                'activity_score': 0,
                'success_score': 0,
                'consumption_score': 0,
                'level': '青铜'
            }
        
        # 活跃度得分 (0-40分)
        active_days = len(set([b['timestamp'][:10] for b in behaviors]))
        activity_score = min(40, active_days * 2)
        
        # 成功率得分 (0-30分)
        success_count = sum(1 for b in behaviors if b.get('success', False))
        success_rate = success_count / len(behaviors) if behaviors else 0
        success_score = int(success_rate * 30)
        
        # 消费能力得分 (0-30分)
        prices = [b['price'] for b in behaviors if 'price' in b]
        avg_price = statistics.mean(prices) if prices else 0
        consumption_score = min(30, int(avg_price / 5))
        
        # 总分
        total_score = activity_score + success_score + consumption_score
        
        # 等级判定
        if total_score >= 80:
            level = '王者'
        elif total_score >= 60:
            level = '钻石'
        elif total_score >= 40:
            level = '黄金'
        elif total_score >= 20:
            level = '白银'
        else:
            level = '青铜'
        
        return {
            'total_score': total_score,
            'activity_score': activity_score,
            'success_score': success_score,
            'consumption_score': consumption_score,
            'level': level
        }
    
    def _prepare_visualization_data(self, behaviors: List[Dict]) -> Dict:
        """准备可视化数据"""
        if not behaviors:
            return {
                'category_distribution': {},
                'action_timeline': [],
                'success_trend': []
            }
        
        # 类目分布
        categories = {}
        for b in behaviors:
            cat = b.get('category', '未知')
            categories[cat] = categories.get(cat, 0) + 1
        
        # 行为时间线（最近10条）
        action_timeline = []
        for b in behaviors[-10:]:
            action_timeline.append({
                'time': b['timestamp'],
                'action': b['action'],
                'category': b.get('category', '未知'),
                'success': b.get('success', False)
            })
        
        # 成功率趋势（按天统计）
        daily_stats = {}
        for b in behaviors:
            date = b['timestamp'][:10]
            if date not in daily_stats:
                daily_stats[date] = {'total': 0, 'success': 0}
            daily_stats[date]['total'] += 1
            if b.get('success', False):
                daily_stats[date]['success'] += 1
        
        success_trend = []
        for date in sorted(daily_stats.keys()):
            stats = daily_stats[date]
            success_rate = round(stats['success'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
            success_trend.append({
                'date': date,
                'success_rate': success_rate,
                'total_actions': stats['total']
            })
        
        return {
            'category_distribution': categories,
            'action_timeline': action_timeline,
            'success_trend': success_trend
        }
    
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
