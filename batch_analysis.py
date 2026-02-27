# batch_analysis.py - 批量分析模块

from typing import List, Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class BatchAnalysisService:
    """批量分析服务"""
    
    def __init__(self, product_selector, ad_optimizer):
        self.product_selector = product_selector
        self.ad_optimizer = ad_optimizer
        self.max_workers = 5
    
    async def batch_product_analysis(self, requests: List[Dict]) -> List[Dict]:
        """批量商品分析"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for req in requests:
                future = executor.submit(
                    self._analyze_single_product,
                    req
                )
                futures.append(future)
            
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=30)
                    results.append({
                        'index': i,
                        'success': True,
                        'data': result
                    })
                except Exception as e:
                    logger.error(f"批量分析失败 #{i}: {e}")
                    results.append({
                        'index': i,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def _analyze_single_product(self, request: Dict) -> Dict:
        """分析单个商品"""
        platform = request.get('platform', 'douyin')
        category = request.get('category', 'beauty')
        budget = request.get('budget', 'low')
        experience = request.get('experience', 'beginner')
        
        recommendations = self.product_selector.get_recommendations(
            platform, category, budget, experience
        )
        
        ai_suggestion = self.product_selector.generate_ai_suggestion(
            platform, category, budget, experience, recommendations
        )
        
        return {
            'platform': platform,
            'category': category,
            'recommendations': recommendations,
            'ai_suggestion': ai_suggestion
        }
    
    async def batch_ad_analysis(self, requests: List[Dict]) -> List[Dict]:
        """批量投流分析"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for req in requests:
                future = executor.submit(
                    self._analyze_single_ad,
                    req
                )
                futures.append(future)
            
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=30)
                    results.append({
                        'index': i,
                        'success': True,
                        'data': result
                    })
                except Exception as e:
                    logger.error(f"批量投流分析失败 #{i}: {e}")
                    results.append({
                        'index': i,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def _analyze_single_ad(self, request: Dict) -> Dict:
        """分析单个投流数据"""
        platform = request.get('platform', 'qianchuan')
        analysis_type = request.get('analysis_type', 'overall')
        data = request.get('data', '')
        
        parsed_data = self.ad_optimizer.parse_data(data)
        analysis = self.ad_optimizer.analyze_data(parsed_data, analysis_type)
        suggestions = self.ad_optimizer.generate_suggestions(
            platform, analysis_type, analysis
        )
        
        return {
            'platform': platform,
            'analysis_type': analysis_type,
            'analysis': analysis,
            'suggestions': suggestions
        }
    
    def batch_export(self, results: List[Dict], format: str = 'json') -> str:
        """批量导出结果"""
        if format == 'json':
            import json
            return json.dumps(results, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            
            if results and len(results) > 0:
                # 提取所有可能的字段
                fieldnames = set()
                for result in results:
                    if result.get('success') and 'data' in result:
                        fieldnames.update(result['data'].keys())
                
                fieldnames = ['index', 'success'] + sorted(list(fieldnames))
                
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    row = {
                        'index': result.get('index', ''),
                        'success': result.get('success', False)
                    }
                    
                    if result.get('success') and 'data' in result:
                        row.update(result['data'])
                    
                    writer.writerow(row)
            
            return output.getvalue()
        
        elif format == 'markdown':
            lines = ['# 批量分析结果\n']
            
            for result in results:
                index = result.get('index', 0)
                lines.append(f"\n## 分析 #{index + 1}\n")
                
                if result.get('success'):
                    data = result.get('data', {})
                    for key, value in data.items():
                        if isinstance(value, (list, dict)):
                            lines.append(f"**{key}:**\n```json\n{json.dumps(value, ensure_ascii=False, indent=2)}\n```\n")
                        else:
                            lines.append(f"**{key}:** {value}\n")
                else:
                    error = result.get('error', '未知错误')
                    lines.append(f"❌ 分析失败: {error}\n")
            
            return '\n'.join(lines)
        
        else:
            raise ValueError(f"不支持的导出格式: {format}")
