#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单趋势预测系统
基于历史数据的轻量级趋势预测，不需要复杂机器学习模型
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import statistics
import math

class SimpleTrendPredictor:
    """简单趋势预测器"""
    
    def __init__(self):
        """初始化趋势预测器"""
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        import logging
        logger = logging.getLogger(__name__)
        return logger
    
    def predict_sales_trend(self, product_history: List[Dict]) -> Dict[str, Any]:
        """
        使用移动平均 + 季节性调整预测销量
        
        Args:
            product_history: 产品历史数据列表，每个元素包含：
                - date: 日期 (YYYY-MM-DD)
                - sales: 销量
                - price: 价格 (可选)
                - competitors: 竞品数量 (可选)
                
        Returns:
            Dict: 预测结果
        """
        if not product_history or len(product_history) < 7:
            return self._get_default_prediction(product_history)
        
        try:
            # 提取销量数据
            sales_data = [item.get('sales', 0) for item in product_history]
            dates = [item.get('date') for item in product_history]
            
            # 7天移动平均
            ma_7 = self._moving_average(sales_data, window=7)
            
            # 检测季节性（周末 vs 工作日）
            seasonality = self._detect_seasonality(product_history)
            
            # 简单线性趋势
            trend = self._linear_trend(sales_data)
            
            # 组合预测
            if ma_7:
                base_prediction = ma_7[-1]  # 最近一天的移动平均
            else:
                base_prediction = statistics.mean(sales_data[-7:]) if len(sales_data) >= 7 else sales_data[-1]
            
            # 应用季节性和趋势调整
            adjusted_prediction = base_prediction * seasonality * trend
            
            # 预测未来7天
            next_7_days = []
            current_base = base_prediction
            for i in range(7):
                # 每天应用趋势增长
                day_prediction = current_base * (trend ** (i + 1))
                
                # 应用季节性（假设未来日期模式与历史相似）
                day_of_week = (datetime.now().weekday() + i) % 7
                day_seasonality = seasonality.get(f'day_{day_of_week}', 1.0)
                day_prediction *= day_seasonality
                
                next_7_days.append({
                    'day': i + 1,
                    'predicted_sales': max(0, round(day_prediction, 2)),
                    'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                })
                current_base = day_prediction
            
            prediction = {
                'next_7_days': next_7_days,
                'confidence': self._calculate_confidence(sales_data),
                'risk_level': self._assess_risk(trend, sales_data),
                'trend_direction': 'up' if trend > 1 else 'down' if trend < 1 else 'stable',
                'trend_strength': abs(trend - 1),
                'seasonality_pattern': seasonality,
                'moving_average_7': ma_7[-1] if ma_7 else base_prediction,
                'historical_avg': statistics.mean(sales_data) if sales_data else 0
            }
            
            self.logger.info(f"销量趋势预测完成: 历史数据点={len(product_history)}, 置信度={prediction['confidence']:.2f}")
            return prediction
            
        except Exception as e:
            self.logger.error(f"销量趋势预测失败: {e}")
            return self._get_default_prediction(product_history)
    
    def detect_opportunities(self, market_data: List[Dict]) -> List[Dict]:
        """
        发现市场机会（价格洼地、流量机会）
        
        Args:
            market_data: 市场数据列表，每个元素包含：
                - product_id: 产品ID
                - product_name: 产品名称
                - price: 价格
                - sales: 销量
                - sales_trend: 销量趋势（正数表示上升）
                - market_avg_price: 市场均价 (可选)
                - competition_level: 竞争程度 (可选)
                
        Returns:
            List[Dict]: 机会列表
        """
        if not market_data:
            return []
        
        try:
            # 计算市场均价（如果未提供）
            prices = [item.get('price', 0) for item in market_data if item.get('price', 0) > 0]
            market_avg = statistics.mean(prices) if prices else 0
            
            opportunities = []
            
            for product in market_data:
                product_opportunities = []
                
                price = product.get('price', 0)
                sales_trend = product.get('sales_trend', 0)
                sales = product.get('sales', 0)
                
                # 1. 价格机会：价格低于市场均价 20% 且销量上升
                if price > 0 and market_avg > 0:
                    price_ratio = price / market_avg
                    if price_ratio < 0.8 and sales_trend > 0:
                        product_opportunities.append({
                            'type': 'price_opportunity',
                            'reason': f'价格优势 ({price_ratio:.1%} 市场均价) + 销量上升 ({sales_trend:.1%})',
                            'score': 0.8 - price_ratio + min(sales_trend, 0.3),  # 评分
                            'suggestion': '考虑增加库存或提高曝光'
                        })
                
                # 2. 增长机会：销量快速增长但价格合理
                if sales_trend > 0.3 and price_ratio < 1.2:  # 增长超过30%，价格不超过市场20%
                    product_opportunities.append({
                        'type': 'growth_opportunity',
                        'reason': f'快速增长 ({sales_trend:.1%}) + 合理定价',
                        'score': min(sales_trend, 1.0) * 0.8,
                        'suggestion': '加大广告投入，抢占市场份额'
                    })
                
                # 3. 低竞争机会：销量稳定但竞争少
                competition = product.get('competition_level', 1.0)
                if competition < 0.5 and sales > 10:  # 竞争低且有基础销量
                    product_opportunities.append({
                        'type': 'low_competition_opportunity',
                        'reason': f'竞争程度低 ({competition:.1%}) + 稳定销量 ({sales})',
                        'score': (1 - competition) * 0.7,
                        'suggestion': '建立品牌优势，提高客户忠诚度'
                    })
                
                # 4. 季节性机会：检测季节性模式
                seasonal_pattern = self._detect_seasonal_pattern(product)
                if seasonal_pattern.get('is_seasonal', False):
                    product_opportunities.append({
                        'type': 'seasonal_opportunity',
                        'reason': f'季节性产品，{seasonal_pattern["peak_season"]}为旺季',
                        'score': seasonal_pattern.get('strength', 0.5),
                        'suggestion': f'在{seasonal_pattern["next_peak"]}前备货'
                    })
                
                # 如果有机会，添加到结果
                if product_opportunities:
                    # 按评分排序
                    product_opportunities.sort(key=lambda x: x['score'], reverse=True)
                    
                    opportunities.append({
                        'product_id': product.get('product_id'),
                        'product_name': product.get('product_name', '未知产品'),
                        'current_price': price,
                        'current_sales': sales,
                        'opportunities': product_opportunities[:3],  # 最多3个机会
                        'overall_score': statistics.mean([opp['score'] for opp in product_opportunities[:3]])
                    })
            
            # 按总体评分排序
            opportunities.sort(key=lambda x: x['overall_score'], reverse=True)
            
            self.logger.info(f"市场机会检测完成: 分析产品数={len(market_data)}, 发现机会数={len(opportunities)}")
            return opportunities[:10]  # 返回前10个机会
            
        except Exception as e:
            self.logger.error(f"市场机会检测失败: {e}")
            return []
    
    def _moving_average(self, data: List[float], window: int = 7) -> List[float]:
        """计算移动平均"""
        if len(data) < window:
            return []
        
        ma = []
        for i in range(window - 1, len(data)):
            window_data = data[i - window + 1:i + 1]
            ma.append(statistics.mean(window_data))
        
        return ma
    
    def _detect_seasonality(self, product_history: List[Dict]) -> Dict[str, float]:
        """检测季节性模式"""
        if len(product_history) < 14:  # 至少2周数据
            return {'day_0': 1.0, 'day_1': 1.0, 'day_2': 1.0, 'day_3': 1.0, 
                    'day_4': 1.0, 'day_5': 1.0, 'day_6': 1.0}
        
        # 按星期几分组
        weekday_sales = {i: [] for i in range(7)}
        
        for item in product_history:
            try:
                date_str = item.get('date')
                if date_str:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    weekday = date.weekday()
                    sales = item.get('sales', 0)
                    if sales > 0:
                        weekday_sales[weekday].append(sales)
            except:
                continue
        
        # 计算每个工作日的平均销量
        weekday_avgs = {}
        for weekday, sales_list in weekday_sales.items():
            if sales_list:
                weekday_avgs[f'day_{weekday}'] = statistics.mean(sales_list)
            else:
                weekday_avgs[f'day_{weekday}'] = 0
        
        # 计算整体平均
        all_sales = [s for sales_list in weekday_sales.values() for s in sales_list]
        overall_avg = statistics.mean(all_sales) if all_sales else 1
        
        # 计算季节性因子（相对于整体平均）
        seasonality = {}
        for weekday, avg in weekday_avgs.items():
            if overall_avg > 0:
                seasonality[weekday] = avg / overall_avg
            else:
                seasonality[weekday] = 1.0
        
        return seasonality
    
    def _linear_trend(self, data: List[float]) -> float:
        """计算简单线性趋势"""
        if len(data) < 2:
            return 1.0
        
        try:
            # 使用最近14天数据计算趋势
            recent_data = data[-14:] if len(data) >= 14 else data
            
            # 简单趋势计算：最后一天/第一天
            if recent_data[0] > 0:
                trend = recent_data[-1] / recent_data[0]
            else:
                trend = 1.0
            
            # 限制趋势范围在合理区间
            return max(0.5, min(trend, 2.0))
            
        except:
            return 1.0
    
    def _calculate_confidence(self, data: List[float]) -> float:
        """计算预测置信度"""
        if len(data) < 7:
            return 0.3  # 数据不足，置信度低
        
        try:
            # 基于数据稳定性的置信度
            if len(data) >= 7:
                recent_std = statistics.stdev(data[-7:]) if len(data[-7:]) > 1 else 0
                recent_mean = statistics.mean(data[-7:]) if data[-7:] else 1
                
                if recent_mean > 0:
                    cv = recent_std / recent_mean  # 变异系数
                    # 变异系数越小，置信度越高
                    confidence = max(0.1, 1.0 - min(cv, 1.0))
                else:
                    confidence = 0.5
            else:
                confidence = 0.5
            
            # 基于数据量的调整
            data_factor = min(1.0, len(data) / 30)  # 30天数据达到最大置信度
            
            return round(confidence * data_factor, 2)
            
        except:
            return 0.5
    
    def _assess_risk(self, trend: float, data: List[float]) -> str:
        """评估风险等级"""
        if len(data) < 7:
            return 'high'  # 数据不足，风险高
        
        try:
            # 基于趋势的风险
            if trend < 0.8:
                trend_risk = 'high'
            elif trend < 0.95:
                trend_risk = 'medium'
            else:
                trend_risk = 'low'
            
            # 基于数据稳定性的风险
            if len(data) >= 7:
                recent_data = data[-7:]
                if len(recent_data) > 1:
                    std = statistics.stdev(recent_data)
                    mean = statistics.mean(recent_data)
                    
                    if mean > 0:
                        cv = std / mean
                        if cv > 0.5:
                            stability_risk = 'high'
                        elif cv > 0.3:
                            stability_risk = 'medium'
                        else:
                            stability_risk = 'low'
                    else:
                        stability_risk = 'high'
                else:
                    stability_risk = 'medium'
            else:
                stability_risk = 'high'
            
            # 综合风险
            if trend_risk == 'high' or stability_risk == 'high':
                return 'high'
            elif trend_risk == 'medium' or stability_risk == 'medium':
                return 'medium'
            else:
                return 'low'
                
        except:
            return 'medium'
    
    def _detect_seasonal_pattern(self, product: Dict) -> Dict[str, Any]:
        """检测产品季节性模式"""
        # 这里可以扩展为更复杂的季节性检测
        # 目前返回简单结果
        return {
            'is_seasonal': False,
            'strength': 0.0,
            'peak_season': '',
            'next_peak': ''
        }
    
    def _get_default_prediction(self, product_history: List[Dict]) -> Dict[str, Any]:
        """获取默认预测结果"""
        if product_history:
            recent_sales = [item.get('sales', 0) for item in product_history[-3:]]
            avg_sales = statistics.mean(recent_sales) if recent_sales else 0
        else:
            avg_sales = 0
        
        return {
            'next_7_days': [
                {'day': i+1, 'predicted_sales': avg_sales, 'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')}
                for i in range(7)
            ],
            'confidence': 0.3,
            'risk_level': 'high',
            'trend_direction': 'stable',
            'trend_strength': 0.0,
            'seasonality_pattern': {},
            'moving_average_7': avg_sales,
            'historical_avg': avg_sales,
            'note': '数据不足，使用默认预测'
        }
    
    def generate_market_report(self, market_data: List[Dict], product_history: List[Dict] = None) -> Dict[str, Any]:
        """
        生成市场分析报告
        
        Args:
            market_data: 市场数据
            product_history: 产品历史数据（可选）
            
        Returns:
            Dict: 市场分析报告
        """
        opportunities = self.detect_opportunities(market_data)
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'market_overview': {
                'total_products_analyzed': len(market_data),
                'avg_price': statistics.mean([p.get('price', 0) for p in market_data]) if market_data else 0,
                'avg_sales': statistics.mean([p.get('sales', 0) for p in market_data]) if market_data else 0,
                'opportunities_found': len(opportunities)
            },
            'top_opportunities': opportunities[:5],
            'recommendations': []
        }
        
        # 添加推荐
        if opportunities:
            report['recommendations'].append({
                'type': 'focus_high_opportunity',
                'message': f'发现 {len(opportunities)} 个市场机会，建议优先关注评分最高的产品',
                'priority': 'high'
            })
        
        if product_history:
            trend_prediction = self.predict_sales_trend(product_history)
            report['sales_trend'] = trend_prediction
            report['recommendations'].append({
                'type': 'trend_based_action',
                'message': f'销量趋势：{trend_prediction["trend_direction"]}，置信度 {trend_prediction["confidence"]:.0%}',
                'priority': 'medium'
            })
        
        return report

# 使用示例
if __name__ == "__main__":
    predictor = SimpleTrendPredictor()
    
    # 示例：销量趋势预测
    sample_history = [
        {'date': '2026-02-21', 'sales': 100, 'price': 99.9},
        {'date': '2026-02-22', 'sales': 110, 'price': 99.9},
        {'date': '2026-02-23', 'sales': 105, 'price': 99.9},
        {"date": "2026-02-24", "sales": 120, "price": 99.9},
        {'date': '2026-02-25', 'sales': 115, 'price': 99.9},
        {'date': '2026-02-26', 'sales': 125, 'price': 99.9},
        {'date': '2026-02-27', 'sales': 130, 'price': 99.9},
        {'date': '2026-02-28', 'sales': 135, 'price': 99.9},
    ]
    
    trend_prediction = predictor.predict_sales_trend(sample_history)
    print("销量趋势预测:", json.dumps(trend_prediction, indent=2, ensure_ascii=False))
    
    # 示例：市场机会检测
    sample_market_data = [
        {'product_id': 1, 'product_name': '手机充电器', 'price': 29.9, 'sales': 1000, 'sales_trend': 0.2},
        {'product_id': 2, 'product_name': '无线耳机', 'price': 199.9, 'sales': 500, 'sales_trend': 0.4},
        {'product_id': 3, 'product_name': '手机壳', 'price': 19.9, 'sales': 2000, 'sales_trend': 0.1},
        {'product_id': 4, 'product_name': '充电宝', 'price': 79.9, 'sales': 800, 'sales_trend': 0.3},
    ]
    
    opportunities = predictor.detect_opportunities(sample_market_data)
    print("\n市场机会检测:", json.dumps(opportunities, indent=2, ensure_ascii=False))
    
    # 示例：生成市场报告
    report = predictor.generate_market_report(sample_market_data, sample_history)
    print("\n市场分析报告:", json.dumps(report, indent=2, ensure_ascii=False))
