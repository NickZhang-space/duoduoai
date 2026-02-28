"""
自动优化引擎
自动执行广告优化操作（出价、关键词、时段、价格）
"""

import time
from typing import Dict, List
from intelligence.dynamic_pricing import DynamicPricingEngine


class AutoOptimizer:
    """自动优化引擎"""
    
    def __init__(self):
        self.settings_store = {}  # 内存存储，生产环境应使用数据库
        self.logs_store = []
    
    async def run_optimization_cycle(self, user_id: str) -> Dict:
        """运行一轮自动优化"""
        settings = self.settings_store.get(user_id, {})
        
        if not settings or not settings.get('enabled'):
            return {'status': 'disabled', 'message': '自动化未启用'}
        
        # 模拟获取用户的广告计划
        campaigns = self._get_mock_campaigns(user_id)
        all_actions = []
        
        for campaign in campaigns:
            actions = []
            
            # 1. 出价优化
            if settings.get('auto_bid_adjust'):
                bid_actions = await self._optimize_bids(
                    campaign, 
                    settings.get('max_cpc', 5),
                    settings.get('min_cpc', 0.5)
                )
                actions.extend(bid_actions)
            
            # 2. 关键词优化
            if settings.get('auto_keyword_pause'):
                kw_actions = await self._optimize_keywords(
                    campaign,
                    settings.get('roi_threshold', 1.0)
                )
                actions.extend(kw_actions)
            
            # 3. 时段优化
            if settings.get('auto_schedule'):
                schedule_actions = await self._optimize_schedule(campaign)
                actions.extend(schedule_actions)
            
            # 4. 价格优化
            if settings.get('auto_price'):
                price_actions = await self._optimize_price(
                    campaign,
                    settings.get('price_change_limit', 10)
                )
                actions.extend(price_actions)
            
            all_actions.extend(actions)
        
        # 执行并记录
        results = []
        for action in all_actions:
            result = await self._execute_action(action)
            self._log_action(user_id, action, result)
            results.append(result)
        
        return {
            'status': 'completed',
            'actions_count': len(results),
            'actions': results
        }
    
    async def _optimize_bids(self, campaign: Dict, max_cpc: float, min_cpc: float) -> List[Dict]:
        """出价优化"""
        actions = []
        
        for keyword in campaign.get('keywords', []):
            current_bid = keyword.get('bid', 0)
            roi = keyword.get('roi', 0)
            
            if roi > 2.0:
                # ROI高，提高出价
                new_bid = min(current_bid * 1.1, max_cpc)
                if abs(new_bid - current_bid) > 0.01:
                    actions.append({
                        'type': 'adjust_bid',
                        'campaign_id': campaign['id'],
                        'keyword': keyword['text'],
                        'old_value': round(current_bid, 2),
                        'new_value': round(new_bid, 2),
                        'reason': f"ROI {roi:.2f} 表现优秀，提高出价抢流量"
                    })
            elif roi < 1.0 and roi > 0:
                # ROI低，降低出价
                new_bid = max(current_bid * 0.9, min_cpc)
                if abs(new_bid - current_bid) > 0.01:
                    actions.append({
                        'type': 'adjust_bid',
                        'campaign_id': campaign['id'],
                        'keyword': keyword['text'],
                        'old_value': round(current_bid, 2),
                        'new_value': round(new_bid, 2),
                        'reason': f"ROI {roi:.2f} 偏低，降低出价控制成本"
                    })
        
        return actions
    
    async def _optimize_keywords(self, campaign: Dict, roi_threshold: float) -> List[Dict]:
        """关键词优化"""
        actions = []
        
        for keyword in campaign.get('keywords', []):
            daily_roi = keyword.get('daily_roi', [])
            
            # 连续3天ROI低于阈值，暂停
            if len(daily_roi) >= 3 and all(r < roi_threshold for r in daily_roi[-3:]):
                actions.append({
                    'type': 'pause_keyword',
                    'campaign_id': campaign['id'],
                    'keyword': keyword['text'],
                    'old_value': 'active',
                    'new_value': 'paused',
                    'reason': f"连续3天ROI低于{roi_threshold}，暂停投放"
                })
        
        return actions
    
    async def _optimize_schedule(self, campaign: Dict) -> List[Dict]:
        """时段优化"""
        actions = []
        
        hourly_data = campaign.get('hourly_performance', )
        
        if not hourly_data:
            return actions
        
        # 找出高转化时段（前8个小时）
        sorted_hours = sorted(
            hourly_data.items(),
            key=lambda x: x[1].get('conversion_rate', 0),
            reverse=True
        )
        
        best_hours = sorted([int(h[0]) for h in sorted_hours[:8]])
        current_schedule = campaign.get('schedule', list(range(24)))
        
        if set(best_hours) != set(current_schedule):
            actions.append({
                'type': 'adjust_schedule',
                'campaign_id': campaign['id'],
                'old_value': current_schedule,
                'new_value': best_hours,
                'reason': "集中预算在高转化时段"
            })
        
        return actions
    
    async def _optimize_price(self, campaign: Dict, change_limit_pct: float) -> List[Dict]:
        """价格优化"""
        actions = []
        
        pricing_engine = DynamicPricingEngine()
        
        for product in campaign.get('products', []):
            market_data = campaign.get('market_data', {})
            
            suggestion = await pricing_engine.suggest_price(
                product, 
                market_data,
                'balanced'
            )
            
            change_pct = abs(suggestion['change_percent'])
            
            # 变化幅度在1%到限制之间才调整
            if 1 < change_pct <= change_limit_pct:
                actions.append({
                    'type': 'adjust_price',
                    'campaign_id': campaign['id'],
                    'product': product['name'],
                    'old_value': round(product['price'], 2),
                    'new_value': suggestion['suggested_price'],
                    'reason': suggestion['reasoning'][0] if suggestion['reasoning'] else '市场价格调整'
                })
        
        return actions
    
    async def _execute_action(self, action: Dict) -> Dict:
        """执行操作（模拟）"""
        try:
            # 这里是模拟执行，实际需要对接拼多多API
            action['status'] = 'executed'
            action['executed_at'] = int(time.time())
            return action
        except Exception as e:
            action['status'] = 'failed'
            action['error'] = str(e)
            return action
    
    def _log_action(self, user_id: str, action: Dict, result: Dict):
        """记录操作日志"""
        log_entry = {
            'user_id': user_id,
            'action_type': action['type'],
            'campaign_id': action.get('campaign_id'),
            'details': action,
            'result': result['status'],
            'timestamp': int(time.time())
        }
        self.logs_store.append(log_entry)
    
    def save_settings(self, user_id: str, settings: Dict):
        """保存设置"""
        self.settings_store[user_id] = settings
    
    def get_settings(self, user_id: str) -> Dict:
        """获取设置"""
        return self.settings_store.get(user_id, {
            'enabled': False,
            'auto_bid_adjust': False,
            'auto_keyword_pause': False,
            'auto_schedule': False,
            'auto_price': False,
            'max_cpc': 5,
            'min_cpc': 0.5,
            'roi_threshold': 1.0,
            'price_change_limit': 10
        })
    
    def get_logs(self, user_id: str, limit: int = 50) -> List[Dict]:
        """获取操作日志"""
        user_logs = [log for log in self.logs_store if log['user_id'] == user_id]
        return sorted(user_logs, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def _get_mock_campaigns(self, user_id: str) -> List[Dict]:
        """获取模拟广告计划数据"""
        return [
            {
                'id': 'camp_001',
                'name': '春季促销',
                'keywords': [
                    {'text': '无线耳机', 'bid': 2.5, 'roi': 2.3, 'daily_roi': [2.1, 2.3, 2.5]},
                    {'text': '蓝牙耳机', 'bid': 3.0, 'roi': 0.8, 'daily_roi': [0.7, 0.8, 0.9]},
                    {'text': '运动耳机', 'bid': 1.8, 'roi': 0.6, 'daily_roi': [0.5, 0.6, 0.7]}
                ],
                'hourly_performance': {
                    '9': {'conversion_rate': 3.5},
                    '10': {'conversion_rate': 4.2},
                    '11': {'conversion_rate': 3.8},
                    '14': {'conversion_rate': 4.0},
                    '15': {'conversion_rate': 3.6},
                    '20': {'conversion_rate': 4.5},
                    '21': {'conversion_rate': 4.1},
                    '22': {'conversion_rate': 3.9}
                },
                'schedule': list(range(24)),
                'products': [
                    {'name': '无线蓝牙耳机', 'cost': 50, 'price': 99, 'historical_sales': 100}
                ],
                'market_data': {
                    'competitors': [
                        {'price': 89}, {'price': 95}, {'price': 99}, {'price': 105}
                    ]
                }
            }
        ]
