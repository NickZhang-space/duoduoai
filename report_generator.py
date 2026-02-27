import json
from datetime import datetime
from typing import Dict, Any

class ReportGenerator:
    def generate_html_report(self, history_data: Dict[str, Any]) -> str:
        analysis_type = history_data.get('analysis_type', 'unknown')
        
        if analysis_type == 'ad':
            return self._generate_ad_report(history_data)
        elif analysis_type == 'product':
            return self._generate_product_report(history_data)
        else:
            return self._generate_generic_report(history_data)
    
    def _generate_ad_report(self, history_data: Dict[str, Any]) -> str:
        input_data = json.loads(history_data.get('input_data', '{}'))
        result_data = json.loads(history_data.get('result_data', '{}'))
        created_at = history_data.get('created_at', datetime.now())
        
        platform = input_data.get('platform', '未知平台')
        analysis_type = input_data.get('analysis_type', '未知类型')
        keywords = result_data.get('keywords', [])
        suggestions = result_data.get('suggestions', [])
        metrics = result_data.get('metrics', {})
        
        html_parts = []
        html_parts.append('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">')
        html_parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append('<title>投流分析报告 - 多多AI优化师</title><style>')
        html_parts.append('* { margin: 0; padding: 0; box-sizing: border-box; }')
        html_parts.append('body { font-family: "PingFang SC", "Microsoft YaHei", sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px; }')
        html_parts.append('.container { max-width: 900px; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }')
        html_parts.append('.header { text-align: center; border-bottom: 3px solid #1890ff; padding-bottom: 20px; margin-bottom: 30px; }')
        html_parts.append('.logo { font-size: 28px; font-weight: bold; color: #1890ff; margin-bottom: 10px; }')
        html_parts.append('.report-title { font-size: 24px; font-weight: bold; margin: 15px 0; }')
        html_parts.append('.meta-info { color: #666; font-size: 14px; }')
        html_parts.append('.section { margin: 30px 0; }')
        html_parts.append('.section-title { font-size: 20px; font-weight: bold; color: #1890ff; margin-bottom: 15px; padding-left: 10px; border-left: 4px solid #1890ff; }')
        html_parts.append('.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }')
        html_parts.append('.metric-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }')
        html_parts.append('.metric-label { font-size: 14px; color: #666; margin-bottom: 8px; }')
        html_parts.append('.metric-value { font-size: 28px; font-weight: bold; color: #1890ff; }')
        html_parts.append('table { width: 100%; border-collapse: collapse; margin: 15px 0; }')
        html_parts.append('th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e8e8e8; }')
        html_parts.append('th { background: #fafafa; font-weight: 600; color: #333; }')
        html_parts.append('tr:hover { background: #f5f5f5; }')
        html_parts.append('.suggestion-list { list-style: none; }')
        html_parts.append('.suggestion-item { background: #f0f7ff; padding: 15px; margin: 10px 0; border-left: 4px solid #1890ff; border-radius: 4px; }')
        html_parts.append('.suggestion-title { font-weight: bold; color: #1890ff; margin-bottom: 5px; }')
        html_parts.append('.footer { margin-top: 50px; padding-top: 20px; border-top: 2px solid #e8e8e8; text-align: center; color: #999; font-size: 14px; }')
        html_parts.append('.print-btn { position: fixed; top: 20px; right: 20px; background: #1890ff; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 14px; box-shadow: 0 2px 8px rgba(24,144,255,0.3); }')
        html_parts.append('.print-btn:hover { background: #40a9ff; }')
        html_parts.append('@media print { body { background: white; padding: 0; } .container { box-shadow: none; padding: 20px; } .print-btn { display: none; } }')
        html_parts.append('@page { size: A4; margin: 15mm; }')
        html_parts.append('</style></head><body>')
        html_parts.append('<button class="print-btn" onclick="window.print()">打印/下载 PDF</button>')
        html_parts.append('<div class="container"><div class="header">')
        html_parts.append('<div class="logo">🚀 多多AI优化师</div>')
        html_parts.append('<div class="report-title">投流分析报告</div>')
        
        time_str = created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(created_at, datetime) else str(created_at)
        html_parts.append(f'<div class="meta-info">平台：{platform} | 分析类型：{analysis_type} | 生成时间：{time_str}</div>')
        html_parts.append('</div><div class="section"><div class="section-title">📊 关键指标摘要</div><div class="metrics-grid">')
        
        if metrics:
            for key, value in metrics.items():
                html_parts.append(f'<div class="metric-card"><div class="metric-label">{key}</div><div class="metric-value">{value}</div></div>')
        else:
            html_parts.append('<div class="metric-card"><div class="metric-label">分析完成</div><div class="metric-value">✓</div></div>')
        
        html_parts.append('</div></div>')
        
        if keywords:
            html_parts.append('<div class="section"><div class="section-title">🔍 关键词分析</div><table><thead><tr>')
            html_parts.append('<th>关键词</th><th>搜索量</th><th>竞争度</th><th>建议出价</th></tr></thead><tbody>')
            for kw in keywords[:10]:
                html_parts.append(f'<tr><td>{kw.get(keyword, -)}</td><td>{kw.get(volume, -)}</td>')
                html_parts.append(f'<td>{kw.get(competition, -)}</td><td>{kw.get(bid, -)}</td></tr>')
            html_parts.append('</tbody></table></div>')
        
        if suggestions:
            html_parts.append('<div class="section"><div class="section-title">💡 优化建议</div><ul class="suggestion-list">')
            for i, suggestion in enumerate(suggestions[:8], 1):
                if isinstance(suggestion, dict):
                    title = suggestion.get('title', f'建议 {i}')
                    content = suggestion.get('content', '')
                else:
                    title = f'建议 {i}'
                    content = str(suggestion)
                html_parts.append(f'<li class="suggestion-item"><div class="suggestion-title">{title}</div><div>{content}</div></li>')
            html_parts.append('</ul></div>')
        
        html_parts.append('<div class="footer"><p>由多多AI优化师生成 | partnerdesk.online</p>')
        html_parts.append('<p style="margin-top: 5px; font-size: 12px;">本报告仅供参考，实际投放效果可能因市场变化而有所不同</p></div>')
        html_parts.append('</div></body></html>')
        
        return ''.join(html_parts)
    
    def _generate_product_report(self, history_data: Dict[str, Any]) -> str:
        input_data = json.loads(history_data.get('input_data', '{}'))
        result_data = json.loads(history_data.get('result_data', '{}'))
        created_at = history_data.get('created_at', datetime.now())
        
        platform = input_data.get('platform', '未知平台')
        category = input_data.get('category', '未知类目')
        budget = input_data.get('budget', 0)
        products = result_data.get('products', [])
        
        html_parts = []
        html_parts.append('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">')
        html_parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append('<title>选品分析报告 - 多多AI优化师</title><style>')
        html_parts.append('* { margin: 0; padding: 0; box-sizing: border-box; }')
        html_parts.append('body { font-family: "PingFang SC", "Microsoft YaHei", sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px; }')
        html_parts.append('.container { max-width: 900px; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }')
        html_parts.append('.header { text-align: center; border-bottom: 3px solid #52c41a; padding-bottom: 20px; margin-bottom: 30px; }')
        html_parts.append('.logo { font-size: 28px; font-weight: bold; color: #52c41a; margin-bottom: 10px; }')
        html_parts.append('.report-title { font-size: 24px; font-weight: bold; margin: 15px 0; }')
        html_parts.append('.meta-info { color: #666; font-size: 14px; }')
        html_parts.append('.section { margin: 30px 0; }')
        html_parts.append('.section-title { font-size: 20px; font-weight: bold; color: #52c41a; margin-bottom: 15px; padding-left: 10px; border-left: 4px solid #52c41a; }')
        html_parts.append('.product-card { background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border: 1px solid #e8e8e8; }')
        html_parts.append('.product-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }')
        html_parts.append('.product-name { font-size: 18px; font-weight: bold; color: #333; }')
        html_parts.append('.product-score { background: #52c41a; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }')
        html_parts.append('.product-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 15px 0; }')
        html_parts.append('.detail-item { padding: 10px; background: white; border-radius: 4px; }')
        html_parts.append('.detail-label { font-size: 12px; color: #999; }')
        html_parts.append('.detail-value { font-size: 16px; font-weight: bold; color: #333; margin-top: 5px; }')
        html_parts.append('.risk-warning { background: #fff7e6; border-left: 4px solid #faad14; padding: 15px; margin: 15px 0; border-radius: 4px; }')
        html_parts.append('.risk-title { font-weight: bold; color: #faad14; margin-bottom: 8px; }')
        html_parts.append('.footer { margin-top: 50px; padding-top: 20px; border-top: 2px solid #e8e8e8; text-align: center; color: #999; font-size: 14px; }')
        html_parts.append('.print-btn { position: fixed; top: 20px; right: 20px; background: #52c41a; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 14px; box-shadow: 0 2px 8px rgba(82,196,26,0.3); }')
        html_parts.append('.print-btn:hover { background: #73d13d; }')
        html_parts.append('@media print { body { background: white; padding: 0; } .container { box-shadow: none; padding: 20px; } .print-btn { display: none; } }')
        html_parts.append('@page { size: A4; margin: 15mm; }')
        html_parts.append('</style></head><body>')
        html_parts.append('<button class="print-btn" onclick="window.print()">打印/下载 PDF</button>')
        html_parts.append('<div class="container"><div class="header">')
        html_parts.append('<div class="logo">🎯 多多AI优化师</div>')
        html_parts.append('<div class="report-title">选品分析报告</div>')
        
        time_str = created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(created_at, datetime) else str(created_at)
        html_parts.append(f'<div class="meta-info">平台：{platform} | 类目：{category} | 预算：¥{budget} | 生成时间：{time_str}</div>')
        html_parts.append('</div><div class="section"><div class="section-title">🏆 推荐商品</div>')
        
        if products:
            for i, product in enumerate(products[:5], 1):
                name = product.get('name', f'商品 {i}')
                score = product.get('score', 0)
                price = product.get('price', 0)
                cost = product.get('cost', 0)
                profit = product.get('profit', 0)
                margin = product.get('margin', 0)
                
                html_parts.append(f'<div class="product-card"><div class="product-header">')
                html_parts.append(f'<div class="product-name">#{i} {name}</div>')
                html_parts.append(f'<div class="product-score">评分: {score}</div></div>')
                html_parts.append('<div class="product-details">')
                html_parts.append(f'<div class="detail-item"><div class="detail-label">建议售价</div><div class="detail-value">¥{price}</div></div>')
                html_parts.append(f'<div class="detail-item"><div class="detail-label">成本</div><div class="detail-value">¥{cost}</div></div>')
                html_parts.append(f'<div class="detail-item"><div class="detail-label">预估利润</div><div class="detail-value">¥{profit}</div></div>')
                html_parts.append(f'<div class="detail-item"><div class="detail-label">利润率</div><div class="detail-value">{margin}%</div></div>')
                html_parts.append('</div>')
                
                risks = product.get('risks', [])
                if risks:
                    html_parts.append('<div class="risk-warning"><div class="risk-title">⚠️ 风险提示</div><ul style="margin-left: 20px;">')
                    for risk in risks:
                        html_parts.append(f'<li>{risk}</li>')
                    html_parts.append('</ul></div>')
                
                html_parts.append('</div>')
        else:
            html_parts.append('<p style="color: #999; text-align: center; padding: 40px;">暂无推荐商品</p>')
        
        html_parts.append('</div><div class="footer"><p>由多多AI优化师生成 | partnerdesk.online</p>')
        html_parts.append('<p style="margin-top: 5px; font-size: 12px;">本报告仅供参考，实际选品需结合市场实时情况</p></div>')
        html_parts.append('</div></body></html>')
        
        return ''.join(html_parts)
    
    def _generate_generic_report(self, history_data: Dict[str, Any]) -> str:
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_str = json.dumps(history_data, ensure_ascii=False, indent=2)
        return f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>分析报告</title><style>body {{ font-family: sans-serif; padding: 40px; max-width: 900px; margin: 0 auto; }} h1 {{ color: #1890ff; }}</style></head><body><h1>分析报告</h1><p>报告生成时间：{time_str}</p><pre>{data_str}</pre></body></html>'

report_generator = ReportGenerator()
