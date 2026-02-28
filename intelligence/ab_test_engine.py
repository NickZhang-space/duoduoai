"""
A/B测试引擎
提供实验创建、流量分配、数据追踪、结果分析功能
"""

import hashlib
import time
from typing import List, Dict, Optional
import statistics


class ABTestEngine:
    """A/B测试引擎"""
    
    def __init__(self):
        self.experiments = {}
        self.conversions = []
    
    def create_experiment(self, name: str, variants: List[Dict], metrics: List[str], 
                         traffic_split: Optional[List[float]] = None, user_id: str = "1") -> Dict:
        """创建实验"""
        if not traffic_split:
            traffic_split = [1.0 / len(variants)] * len(variants)
        
        if abs(sum(traffic_split) - 1.0) > 0.01:
            raise ValueError("流量分配总和必须为100%")
        
        experiment_id = hashlib.md5(f"{name}_{time.time()}".encode()).hexdigest()[:8]
        
        experiment = {
            'id': experiment_id,
            'user_id': user_id,
            'name': name,
            'variants': variants,
            'metrics': metrics,
            'traffic_split': traffic_split,
            'status': 'running',
            'start_time': int(time.time()),
            'end_time': None,
            'created_at': int(time.time())
        }
        
        self.experiments[experiment_id] = experiment
        return experiment
    
    def assign_variant(self, user_id: str, experiment_id: str) -> str:
        """为用户分配实验组（一致性哈希）"""
        if experiment_id not in self.experiments:
            raise ValueError(f"实验 {experiment_id} 不存在")
        
        experiment = self.experiments[experiment_id]
        hash_value = int(hashlib.md5(f"{user_id}_{experiment_id}".encode()).hexdigest(), 16)
        random_value = (hash_value % 10000) / 10000
        
        cumulative = 0
        for i, split in enumerate(experiment['traffic_split']):
            cumulative += split
            if random_value < cumulative:
                return experiment['variants'][i]['name']
        
        return experiment['variants'][-1]['name']
    
    def track_conversion(self, user_id: str, experiment_id: str, metrics_data: Dict):
        """记录转化数据"""
        if experiment_id not in self.experiments:
            raise ValueError(f"实验 {experiment_id} 不存在")
        
        variant = self.assign_variant(user_id, experiment_id)
        
        conversion = {
            'experiment_id': experiment_id,
            'variant': variant,
            'user_id': user_id,
            'metrics': metrics_data,
            'timestamp': int(time.time())
        }
        
        self.conversions.append(conversion)
        return conversion
    
    def analyze_results(self, experiment_id: str) -> Dict:
        """分析实验结果"""
        if experiment_id not in self.experiments:
            raise ValueError(f"实验 {experiment_id} 不存在")
        
        experiment = self.experiments[experiment_id]
        data = [c for c in self.conversions if c['experiment_id'] == experiment_id]
        
        results = {}
        for variant in experiment['variants']:
            variant_name = variant['name']
            variant_data = [d for d in data if d['variant'] == variant_name]
            
            if not variant_data:
                results[variant_name] = {
                    'sample_size': 0,
                    'metrics': {},
                    'config': variant.get('config', {})
                }
                continue
            
            metrics = {}
            for metric in experiment['metrics']:
                values = [d['metrics'].get(metric, 0) for d in variant_data]
                if values:
                    metrics[metric] = {
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0
                    }
            
            results[variant_name] = {
                'sample_size': len(variant_data),
                'metrics': metrics,
                'config': variant.get('config', {})
            }
        
        winner, confidence = self._determine_winner(results, experiment['metrics'][0])
        
        return {
            'experiment_id': experiment_id,
            'experiment_name': experiment['name'],
            'status': experiment['status'],
            'results': results,
            'winner': winner,
            'confidence': confidence,
            'recommendation': self._generate_recommendation(results, winner, confidence),
            'winner_config': results.get(winner, {}).get('config', {}) if winner else {}
        }
    
    def _determine_winner(self, results: Dict, primary_metric: str) -> tuple:
        """确定获胜者"""
        variants = list(results.keys())
        
        for variant in variants:
            if results[variant]['sample_size'] < 10:
                return None, 0
        
        best_variant = None
        best_value = -float('inf')
        
        for variant in variants:
            if primary_metric in results[variant]['metrics']:
                value = results[variant]['metrics'][primary_metric]['mean']
                if value > best_value:
                    best_value = value
                    best_variant = variant
        
        if best_variant:
            sample_sizes = [results[v]['sample_size'] for v in variants]
            min_sample = min(sample_sizes)
            confidence = min(0.95, 0.5 + (min_sample / 100) * 0.45)
        else:
            confidence = 0
        
        return best_variant, confidence
    
    def _generate_recommendation(self, results: Dict, winner: Optional[str], confidence: float) -> str:
        """生成建议"""
        if not winner:
            return "样本量不足，建议继续收集数据后再做决策。"
        
        if confidence < 0.7:
            return f"方案{winner}表现较好，但置信度较低（{confidence*100:.0f}%），建议继续观察。"
        
        return f"方案{winner}明显优于其他方案（置信度{confidence*100:.0f}%），建议应用该方案。"
    
    def list_experiments(self, user_id: str = None) -> List[Dict]:
        """获取实验列表"""
        experiments = list(self.experiments.values())
        if user_id:
            experiments = [e for e in experiments if e.get('user_id') == user_id]
        return sorted(experiments, key=lambda x: x['created_at'], reverse=True)
    
    def stop_experiment(self, experiment_id: str):
        """停止实验"""
        if experiment_id in self.experiments:
            self.experiments[experiment_id]['status'] = 'stopped'
            self.experiments[experiment_id]['end_time'] = int(time.time())
