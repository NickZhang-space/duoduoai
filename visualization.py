# visualization.py - 数据可视化模块

import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict
import pandas as pd
import json

class DataVisualizer:
    """数据可视化工具"""
    
    def __init__(self):
        self.colors = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444'
        }
    
    def create_roi_chart(self, data: List[Dict]) -> str:
        """创建ROI趋势图"""
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['roi'],
            mode='lines+markers',
            name='ROI',
            line=dict(color=self.colors['primary'], width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='ROI 趋势',
            xaxis_title='日期',
            yaxis_title='ROI',
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig.to_json()
    
    def create_keyword_performance_chart(self, keywords: List[Dict]) -> str:
        """创建关键词性能对比图"""
        df = pd.DataFrame(keywords)
        
        fig = go.Figure()
        
        # ROI柱状图
        fig.add_trace(go.Bar(
            x=df['keyword'],
            y=df['roi'],
            name='ROI',
            marker_color=self.colors['primary']
        ))
        
        # 点击率折线图
        fig.add_trace(go.Scatter(
            x=df['keyword'],
            y=df['ctr'],
            name='点击率 (%)',
            yaxis='y2',
            line=dict(color=self.colors['success'], width=2),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='关键词性能对比',
            xaxis_title='关键词',
            yaxis_title='ROI',
            yaxis2=dict(
                title='点击率 (%)',
                overlaying='y',
                side='right'
            ),
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig.to_json()
    
    def create_funnel_chart(self, data: Dict) -> str:
        """创建转化漏斗图"""
        stages = ['展现', '点击', '加购', '下单', '支付']
        values = [
            data.get('impressions', 0),
            data.get('clicks', 0),
            data.get('add_to_cart', 0),
            data.get('orders', 0),
            data.get('payments', 0)
        ]
        
        fig = go.Figure(go.Funnel(
            y=stages,
            x=values,
            textinfo="value+percent initial",
            marker=dict(
                color=[self.colors['primary'], self.colors['secondary'], 
                       self.colors['success'], self.colors['warning'], 
                       self.colors['danger']]
            )
        ))
        
        fig.update_layout(
            title='转化漏斗',
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def create_cost_breakdown_chart(self, data: Dict) -> str:
        """创建成本分解饼图"""
        labels = list(data.keys())
        values = list(data.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=[self.colors['primary'], self.colors['secondary'], 
                               self.colors['success'], self.colors['warning']])
        )])
        
        fig.update_layout(
            title='成本分解',
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def create_time_series_chart(self, data: List[Dict], metrics: List[str]) -> str:
        """创建时间序列多指标图"""
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        colors = [self.colors['primary'], self.colors['success'], 
                 self.colors['warning'], self.colors['danger']]
        
        for i, metric in enumerate(metrics):
            if metric in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df[metric],
                    mode='lines+markers',
                    name=metric,
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=6)
                ))
        
        fig.update_layout(
            title='多指标趋势',
            xaxis_title='日期',
            yaxis_title='数值',
            template='plotly_white',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig.to_json()
    
    def create_heatmap(self, data: List[List[float]], x_labels: List[str], y_labels: List[str]) -> str:
        """创建热力图"""
        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=x_labels,
            y=y_labels,
            colorscale='Blues',
            text=data,
            texttemplate='%{text}',
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title='数据热力图',
            template='plotly_white'
        )
        
        return fig.to_json()
    
    def create_comparison_chart(self, categories: List[str], series_data: Dict[str, List[float]]) -> str:
        """创建对比柱状图"""
        fig = go.Figure()
        
        colors = [self.colors['primary'], self.colors['success'], 
                 self.colors['warning'], self.colors['danger']]
        
        for i, (name, values) in enumerate(series_data.items()):
            fig.add_trace(go.Bar(
                name=name,
                x=categories,
                y=values,
                marker_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(
            title='数据对比',
            xaxis_title='类别',
            yaxis_title='数值',
            barmode='group',
            template='plotly_white'
        )
        
        return fig.to_json()


# 全局可视化实例
visualizer = DataVisualizer()
