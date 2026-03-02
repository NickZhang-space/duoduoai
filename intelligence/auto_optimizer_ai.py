"""
自动优化引擎 - DeepSeek AI 增强版
使用 DeepSeek AI 分析数据并自动执行优化操作
"""

import time
from typing import Dict, List
from datetime import datetime
import json
from deepseek_analyzer import analyze_with_deepseek


class AutoOptimizerAI:
    """AI 驱动的自动优化引擎"""
    
    def __init__(self):
        self.settings_store = {}  # 内存存储，生产环境应使用数据库
        self.logs_store = []
    
    async def run_optimization_cycle(self, user_id: str) -> Dict:
        """运行一轮自动优化"""
        settings = self.settings_store.get(user_id, {})
        
        if not settings or not settings.get('enabled'):
            return {'status': 'disabled', 'message': '自动化未启用'}
        
        print(f"[AutoOptimizer] 开始为用户 {user_id} 运行优化...")
        
        # 获取用户的广告数据（这里应该从数据库获取真实数据）
        campaigns_data = self._get_user_campaigns_data(user_id)
        
        all_actions = []
        
        # 使用 DeepSeek AI 分析并生成优化建议
        try:
            ai_result = await analyze_with_deepseek(campaigns_data, 'suggestions')
            
            if ai_result['success'] and ai_result['data']:
                suggestions = []
                
                # 解析 AI 返回的建议
                if 'text' in ai_result['data']:
                    try:
                        json_match = ai_result['data']['text']
                        if '{' in json_match:
                            start = json_match.find('{')
                            end = json_match.rfind('}') + 1
                            parsed = json.loads(json_match[start:end])
                            suggestions = parsed.get('suggestions', [])
                    except:
                        pass
                elif 'suggestions' in ai_result['data']:
                    suggestions = ai_result['data']['suggestions']
                
                print(f"[AutoOptimizer] AI 生成了 {len(suggestions)} 条建议")
                
                # 根据 AI 建议执行自动化操作
                for suggestion in suggestions:
                    # 只执行低风险和中风险的建议
                    if suggestion.get('risk_level') in ['低风险', '中风险']:
                        action = await self._execute_suggestion(
                            user_id, 
                            suggestion, 
                            settings
                        )
                        if action:
                            all_actions.append(action)
                            self._log_action(user_id, action)
            
        except Exception as e:
            print(f"[AutoOptimizer] AI 分析失败: {e}")
            # 如果 AI 失败，使用基础规则
            all_actions = await self._fallback_optimization(user_id, campaigns_data, settings)
        
        return {
            'status': 'completed',
            'actions_count': len(all_actions),
            'actions': all_actions,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _execute_suggestion(self, user_id: str, suggestion: Dict, settings: Dict) -> Dict:
        """执行 AI 建议"""
        action_type = suggestion.get('type', '')
        
        # 根据建议类型执行不同的操作
        if '出价' in action_type:
            return await self._execute_bid_adjustment(user_id, suggestion, settings)
        elif '关键词' in action_type:
            return await self._execute_keyword_adjustment(user_id, suggestion, settings)
        elif '时段' in action_type or '投放' in action_type:
            return await self._execute_schedule_adjustment(user_id, suggestion, settings)
        elif '预算' in action_type:
            return await self._execute_budget_adjustment(user_id, suggestion, settings)
        
        return None
    
    async def _execute_bid_adjustment(self, user_id: str, suggestion: Dict, settings: Dict) -> Dict:
        """执行出价调整"""
        if not settings.get('auto_bid_adjust'):
            return None
        
        # 从建议中提取出价信息
        suggestion_text = suggestion.get('suggestion', '')
        
        # 简单的出价提取逻辑（实际应该更复杂）
        import re
        bid_match = re.search(r'(\d+\.?\d*)元', suggestion_text)
        
        if bid_match:
            new_bid = float(bid_match.group(1))
            max_cpc = settings.get('max_cpc', 5)
            min_cpc = settings.get('min_cpc', 0.5)
            
            # 限制在设置的范围内
            new_bid = max(min_cpc, min(max_cpc, new_bid))
            
            return {
                'action_type': 'adjust_bid',
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'keyword': '关键词',  # 实际应该从建议中提取
                    'old_value': 0.8,  # 实际应该从数据库获取
                    'new_value': new_bid,
                    'reason': suggestion.get('problem', '')
                },
                'result': 'executed'
            }
        
        return None
    
    async def _execute_keyword_adjustment(self, user_id: str, suggestion: Dict, settings: Dict) -> Dict:
        """执行关键词调整"""
        if not settings.get('auto_keyword_pause'):
            return None
        
        suggestion_text = suggestion.get('suggestion', '')
        
        # 如果建议中提到暂停或删除
        if '暂停' in suggestion_text or '删除' in suggestion_text:
            return {
                'action_type': 'pause_keyword',
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'keyword': '低效关键词',
                    'old_value': '运行中',
                    'new_value': '已暂停',
                    'reason': suggestion.get('problem', '')
                },
                'result': 'executed'
            }
        
        return None
    
    async def _execute_schedule_adjustment(self, user_id: str, suggestion: Dict, settings: Dict) -> Dict:
        """执行时段调整"""
        if not settings.get('auto_schedule'):
            return None
        
        return {
            'action_type': 'adjust_schedule',
            'timestamp': datetime.now().isoformat(),
            'details': {
                'old_value': {'peak_hours': '全天'},
                'new_value': {'peak_hours': '18:00-23:00'},
                'reason': suggestion.get('problem', '')
            },
            'result': 'executed'
        }
    
    async def _execute_budget_adjustment(self, user_id: str, suggestion: Dict, settings: Dict) -> Dict:
        """执行预算调整"""
        return {
            'action_type': 'adjust_budget',
            'timestamp': datetime.now().isoformat(),
            'details': {
                'campaign': '搜索推广',
                'old_value': 500,
                'new_value': 600,
                'reason': suggestion.get('problem', '')
            },
            'result': 'executed'
        }
    
    async def _fallback_optimization(self, user_id: str, data: Dict, settings: Dict) -> List[Dict]:
        """备用优化逻辑（当 AI 失败时）"""
        actions = []
        
        # 基础规则：ROI < 2 的关键词降价
        if settings.get('auto_bid_adjust'):
            actions.append({
                'action_type': 'adjust_bid',
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'keyword': '低ROI关键词',
                    'old_value': 1.0,
                    'new_value': 0.8,
                    'reason': 'ROI低于阈值，自动降价'
                },
                'result': 'executed'
            })
        
        return actions
    
    def _get_user_campaigns_data(self, user_id: str) -> Dict:
        """获取用户的广告数据（示例）"""
        # 实际应该从数据库获取
        return {
            "search_campaigns": [
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
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
    
    def _log_action(self, user_id: str, action: Dict):
        """记录操作日志"""
        action['user_id'] = user_id
        self.logs_store.append(action)
        print(f"[AutoOptimizer] 记录操作: {action['action_type']}")
    
    def get_logs(self, user_id: str, limit: int = 50) -> List[Dict]:
        """获取操作日志"""
        user_logs = [log for log in self.logs_store if log.get('user_id') == user_id]
        return user_logs[-limit:]
    
    def save_settings(self, user_id: str, settings: Dict):
        """保存设置"""
        self.settings_store[user_id] = settings
        print(f"[AutoOptimizer] 保存设置: {settings}")
    
    def get_settings(self, user_id: str) -> Dict:
        """获取设置"""
        return self.settings_store.get(user_id, {})
