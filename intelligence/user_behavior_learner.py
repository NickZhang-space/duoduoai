#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户行为学习系统
记录并学习用户操作模式，为个性化推荐提供数据支持
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import statistics

class UserBehaviorLearner:
    """用户行为学习系统"""
    
    def __init__(self, db_session: Session):
        """
        初始化用户行为学习系统
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        import logging
        logger = logging.getLogger(__name__)
        return logger
    
    def track_action(self, user_id: int, action_type: str, context: Dict, result: str) -> bool:
        """
        记录用户操作行为
        
        Args:
            user_id: 用户ID
            action_type: 操作类型（select_product, analyze_ads, pricing, etc.）
            context: 操作上下文（JSON格式）
            result: 操作结果（success, failure, neutral）
            
        Returns:
            bool: 记录是否成功
        """
        try:
            from database import UsageLog
            
            # 创建使用记录
            log = UsageLog(
                user_id=user_id,
                action=action_type,
                details=json.dumps({
                    'context': context,
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat()
                }),
                created_at=datetime.utcnow()
            )
            
            self.db.add(log)
            self.db.commit()
            
            self.logger.info(f"记录用户行为: user_id={user_id}, action={action_type}, result={result}")
            return True
            
        except Exception as e:
            self.logger.error(f"记录用户行为失败: {e}")
            self.db.rollback()
            return False
    
    def learn_patterns(self, user_id: int) -> Dict[str, Any]:
        """
        分析用户成功模式
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 用户行为模式
        """
        try:
            from database import UsageLog
            
            # 获取用户最近30天的行为记录
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            behaviors = self.db.query(UsageLog).filter(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= thirty_days_ago
            ).all()
            
            if not behaviors:
                return self._get_default_patterns()
            
            # 解析行为数据
            parsed_behaviors = []
            for behavior in behaviors:
                try:
                    details = json.loads(behavior.details) if behavior.details else {}
                    parsed_behaviors.append({
                        'action': behavior.action,
                        'context': details.get('context', {}),
                        'result': details.get('result', 'neutral'),
                        'timestamp': behavior.created_at
                    })
                except json.JSONDecodeError:
                    continue
            
            # 筛选成功的行为
            successful_behaviors = [b for b in parsed_behaviors if b['result'] == 'success']
            
            # 提取成功模式
            patterns = {
                'preferred_categories': self._extract_categories(successful_behaviors),
                'price_range': self._extract_price_range(successful_behaviors),
                'timing_patterns': self._extract_timing(successful_behaviors),
                'success_rate_by_strategy': self._calculate_success_rates(parsed_behaviors),
                'frequent_actions': self._extract_frequent_actions(parsed_behaviors),
                'recent_trends': self._analyze_recent_trends(parsed_behaviors)
            }
            
            self.logger.info(f"分析用户模式完成: user_id={user_id}, 成功行为数={len(successful_behaviors)}")
            return patterns
            
        except Exception as e:
            self.logger.error(f"分析用户模式失败: {e}")
            return self._get_default_patterns()
    
    def _extract_categories(self, behaviors: List[Dict]) -> List[str]:
        """提取用户偏好的商品类别"""
        categories = []
        for behavior in behaviors:
            context = behavior.get('context', {})
            if 'category' in context:
                categories.append(context['category'])
            elif 'categories' in context:
                if isinstance(context['categories'], list):
                    categories.extend(context['categories'])
        
        # 统计频率，返回前5个最常出现的类别
        from collections import Counter
        if categories:
            counter = Counter(categories)
            return [item[0] for item in counter.most_common(5)]
        return []
    
    def _extract_price_range(self, behaviors: List[Dict]) -> Dict[str, float]:
        """提取用户偏好的价格区间"""
        prices = []
        for behavior in behaviors:
            context = behavior.get('context', {})
            if 'price' in context and isinstance(context['price'], (int, float)):
                prices.append(float(context['price']))
            elif 'price_range' in context:
                price_range = context['price_range']
                if isinstance(price_range, dict) and 'min' in price_range and 'max' in price_range:
                    prices.append((price_range['min'] + price_range['max']) / 2)
        
        if prices:
            return {
                'min': min(prices),
                'max': max(prices),
                'avg': statistics.mean(prices),
                'median': statistics.median(prices)
            }
        return {'min': 0, 'max': 1000, 'avg': 100, 'median': 100}
    
    def _extract_timing(self, behaviors: List[Dict]) -> Dict[str, Any]:
        """提取用户操作的时间模式"""
        if not behaviors:
            return {'best_hours': [], 'best_days': []}
        
        # 按小时统计
        hour_counts = {}
        day_counts = {}
        
        for behavior in behaviors:
            timestamp = behavior.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        continue
                else:
                    dt = timestamp
                
                hour = dt.hour
                day = dt.weekday()  # 0=Monday, 6=Sunday
                
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
                day_counts[day] = day_counts.get(day, 0) + 1
        
        # 找出最佳时间段（频率最高的前3个）
        best_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        best_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'best_hours': [hour for hour, _ in best_hours],
            'best_days': [day for day, _ in best_days],
            'hour_distribution': hour_counts,
            'day_distribution': day_counts
        }
    
    def _calculate_success_rates(self, behaviors: List[Dict]) -> Dict[str, float]:
        """计算不同策略的成功率"""
        if not behaviors:
            return {}
        
        # 按操作类型分组
        action_groups = {}
        for behavior in behaviors:
            action = behavior.get('action', 'unknown')
            result = behavior.get('result', 'neutral')
            
            if action not in action_groups:
                action_groups[action] = {'total': 0, 'success': 0}
            
            action_groups[action]['total'] += 1
            if result == 'success':
                action_groups[action]['success'] += 1
        
        # 计算成功率
        success_rates = {}
        for action, stats in action_groups.items():
            if stats['total'] > 0:
                success_rates[action] = stats['success'] / stats['total']
            else:
                success_rates[action] = 0.0
        
        return success_rates
    
    def _extract_frequent_actions(self, behaviors: List[Dict]) -> List[Dict]:
        """提取用户频繁执行的操作"""
        if not behaviors:
            return []
        
        from collections import Counter
        action_counter = Counter([b.get('action', 'unknown') for b in behaviors])
        
        frequent_actions = []
        for action, count in action_counter.most_common(10):
            frequent_actions.append({
                'action': action,
                'count': count,
                'frequency': count / len(behaviors)
            })
        
        return frequent_actions
    
    def _analyze_recent_trends(self, behaviors: List[Dict]) -> Dict[str, Any]:
        """分析用户近期行为趋势"""
        if len(behaviors) < 5:
            return {'trend': 'stable', 'change_rate': 0.0}
        
        # 按周分组
        weekly_counts = {}
        for behavior in behaviors:
            timestamp = behavior.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        continue
                else:
                    dt = timestamp
                
                week_key = f"{dt.year}-W{dt.isocalendar()[1]}"
                weekly_counts[week_key] = weekly_counts.get(week_key, 0) + 1
        
        # 计算趋势
        if len(weekly_counts) >= 2:
            weeks = sorted(weekly_counts.keys())
            recent_counts = [weekly_counts[w] for w in weeks[-2:]]
            
            if recent_counts[1] > recent_counts[0]:
                change_rate = (recent_counts[1] - recent_counts[0]) / recent_counts[0]
                trend = 'increasing'
            elif recent_counts[1] < recent_counts[0]:
                change_rate = (recent_counts[0] - recent_counts[1]) / recent_counts[0]
                trend = 'decreasing'
            else:
                change_rate = 0.0
                trend = 'stable'
        else:
            change_rate = 0.0
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_rate': change_rate,
            'weekly_activity': weekly_counts,
            'total_actions': len(behaviors)
        }
    
    def _get_default_patterns(self) -> Dict[str, Any]:
        """获取默认的用户模式"""
        return {
            'preferred_categories': [],
            'price_range': {'min': 0, 'max': 1000, 'avg': 100, 'median': 100},
            'timing_patterns': {'best_hours': [9, 14, 20], 'best_days': [0, 1, 2]},
            'success_rate_by_strategy': {},
            'frequent_actions': [],
            'recent_trends': {'trend': 'stable', 'change_rate': 0.0}
        }
    
    def get_personalized_recommendations(self, user_id: int, context: Dict) -> Dict[str, Any]:
        """
        基于用户行为模式生成个性化推荐
        
        Args:
            user_id: 用户ID
            context: 当前上下文
            
        Returns:
            Dict: 个性化推荐
        """
        patterns = self.learn_patterns(user_id)
        
        recommendations = {
            'based_on_history': True,
            'confidence_score': 0.7,  # 置信度分数
            'recommendations': []
        }
        
        # 基于类别偏好的推荐
        if patterns['preferred_categories']:
            recommendations['recommendations'].append({
                'type': 'category_focus',
                'message': f"根据您的历史偏好，建议关注以下类别：{', '.join(patterns['preferred_categories'][:3])}",
                'priority': 'high'
            })
        
        # 基于价格区间的推荐
        price_range = patterns['price_range']
        recommendations['recommendations'].append({
            'type': 'price_optimization',
            'message': f"您的成功价格区间为 ¥{price_range['min']:.2f} - ¥{price_range['max']:.2f}，平均 ¥{price_range['avg']:.2f}",
            'priority': 'medium'
        })
        
        # 基于时间模式的推荐
        timing = patterns['timing_patterns']
        if timing['best_hours']:
            best_hours_str = ', '.join([f"{h}:00" for h in sorted(timing['best_hours'])])
            recommendations['recommendations'].append({
                'type': 'timing_suggestion',
                'message': f"您在以下时间段操作效果最佳：{best_hours_str}",
                'priority': 'low'
            })
        
        # 基于成功率的推荐
        success_rates = patterns['success_rate_by_strategy']
        if success_rates:
            best_strategy = max(success_rates.items(), key=lambda x: x[1])
            if best_strategy[1] > 0.6:  # 成功率超过60%
                recommendations['recommendations'].append({
                    'type': 'strategy_recommendation',
                    'message': f"您的'{best_strategy[0]}'策略成功率最高（{best_strategy[1]:.0%}），建议优先使用",
                    'priority': 'high'
                })
        
        return recommendations
    
    def export_user_insights(self, user_id: int) -> Dict[str, Any]:
        """
        导出用户行为洞察报告
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 用户洞察报告
        """
        patterns = self.learn_patterns(user_id)
        
        return {
            'user_id': user_id,
            'generated_at': datetime.utcnow().isoformat(),
            'behavior_summary': {
                'preferred_categories': patterns['preferred_categories'],
                'price_range': patterns['price_range'],
                'optimal_timing': patterns['timing_patterns'],
                'strategy_effectiveness': patterns['success_rate_by_strategy']
            },
            'action_analysis': {
                'frequent_actions': patterns['frequent_actions'],
                'recent_trends': patterns['recent_trends']
            },
            'recommendations': self.get_personalized_recommendations(user_id, {})
        }

# 使用示例
if __name__ == "__main__":
    from database import get_db
    
    # 获取数据库会话
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 创建行为学习器
        learner = UserBehaviorLearner(db)
        
        # 示例：记录用户行为
        learner.track_action(
            user_id=1,
            action_type="select_product",
            context={
                "category": "电子产品",
                "price": 299.99,
                "keywords": ["手机", "充电器"]
            },
            result="success"
        )
        
        # 示例：分析用户模式
        patterns = learner.learn_patterns(1)
        print("用户行为模式:", json.dumps(patterns, indent=2, ensure_ascii=False))
        
        # 示例：获取个性化推荐
        recommendations = learner.get_personalized_recommendations(1, {})
        print("\n个性化推荐:", json.dumps(recommendations, indent=2, ensure_ascii=False))
        
        # 示例：导出用户洞察
        insights = learner.export_user_insights(1)
        print("\n用户洞察报告:", json.dumps(insights, indent=2, ensure_ascii=False))
        
    finally:
        db.close()
