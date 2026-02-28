// ==================== 每日报告 ====================
async function loadDailyReport() {
    if (!currentUser) {
        document.getElementById('report-content').innerHTML = '<div style="text-align: center; padding: 60px; color: #999;">请先登录</div>';
        return;
    }
    
    try {
        const response = await fetch(`/intelligence/daily-report/${currentUser.id}`);
        const data = await response.json();
        
        if (data.success) {
            displayReport(data.data);
        } else {
            document.getElementById('report-content').innerHTML = '<div style="text-align: center; padding: 60px; color: #f44;">加载失败</div>';
        }
    } catch (error) {
        console.error('加载报告失败:', error);
        document.getElementById('report-content').innerHTML = '<div style="text-align: center; padding: 60px; color: #f44;">加载失败</div>';
    }
}

function displayReport(report) {
    const yesterday = report.summary.yesterday;
    const today = report.summary.today_prediction;
    
    let html = `
        <div class="report-header" style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; margin-bottom: 30px;">
            <h3 style="font-size: 1.5em; margin-bottom: 10px;">${report.date}</h3>
            <p style="opacity: 0.9;">生成时间: ${new Date(report.generated_at).toLocaleString()}</p>
        </div>
        
        <div class="report-section" style="margin-bottom: 30px;">
            <h3 style="color: #333; margin-bottom: 15px; border-left: 4px solid #E84D1A; padding-left: 12px;">📈 昨日表现</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 15px;">
                <div style="padding: 15px; background: #f8f9fa; border-radius: 12px;">
                    <div style="color: #666; font-size: 0.9em;">销量</div>
                    <div style="font-size: 1.8em; font-weight: bold; color: #E84D1A;">${yesterday.sales}</div>
                    <div style="color: #52C41A; font-size: 0.9em;">${yesterday.sales_change}</div>
                </div>
                <div style="padding: 15px; background: #f8f9fa; border-radius: 12px;">
                    <div style="color: #666; font-size: 0.9em;">订单数</div>
                    <div style="font-size: 1.8em; font-weight: bold; color: #E84D1A;">${yesterday.orders}</div>
                    <div style="color: #52C41A; font-size: 0.9em;">${yesterday.orders_change}</div>
                </div>
                <div style="padding: 15px; background: #f8f9fa; border-radius: 12px;">
                    <div style="color: #666; font-size: 0.9em;">营收</div>
                    <div style="font-size: 1.8em; font-weight: bold; color: #E84D1A;">¥${yesterday.revenue}</div>
                    <div style="color: #52C41A; font-size: 0.9em;">${yesterday.revenue_change}</div>
                </div>
                <div style="padding: 15px; background: #f8f9fa; border-radius: 12px;">
                    <div style="color: #666; font-size: 0.9em;">转化率</div>
                    <div style="font-size: 1.8em; font-weight: bold; color: #E84D1A;">${yesterday.conversion_rate}%</div>
                    <div style="color: #52C41A; font-size: 0.9em;">${yesterday.conversion_change}</div>
                </div>
            </div>
            <div style="padding: 15px; background: #e8f5e9; border-radius: 12px; border-left: 4px solid #52C41A;">
                <div style="font-weight: bold; margin-bottom: 8px;">✨ 亮点</div>
                <ul style="margin: 0; padding-left: 20px;">
                    ${yesterday.highlights.map(h => `<li>${h}</li>`).join('')}
                </ul>
            </div>
        </div>
        
        <div class="report-section" style="margin-bottom: 30px;">
            <h3 style="color: #333; margin-bottom: 15px; border-left: 4px solid #667eea; padding-left: 12px;">🔮 今日预测</h3>
            <div style="padding: 20px; background: #f8f9fa; border-radius: 12px;">
                <p style="font-size: 1.1em; margin-bottom: 15px;">${today.summary}</p>
                <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                    <div>
                        <span style="color: #666;">预计销量：</span>
                        <span style="font-weight: bold; color: #E84D1A;">${today.expected_sales}</span>
                    </div>
                    <div>
                        <span style="color: #666;">置信度：</span>
                        <span style="font-weight: bold; color: #52C41A;">${(today.confidence * 100).toFixed(0)}%</span>
                    </div>
                </div>
                <div style="font-size: 0.9em; color: #666;">
                    ${today.factors.map(f => `• ${f}`).join('<br>')}
                </div>
            </div>
        </div>
        
        <div class="report-section" style="margin-bottom: 30px;">
            <h3 style="color: #333; margin-bottom: 15px; border-left: 4px solid #FFA940; padding-left: 12px;">💡 智能建议</h3>
            <div style="display: grid; gap: 12px;">
                ${report.recommendations.map(rec => `
                    <div style="padding: 15px; background: #fff7e6; border-radius: 12px; border-left: 4px solid #FFA940;">
                        <span style="font-size: 1.2em; margin-right: 8px;">${rec.icon}</span>
                        <span>${rec.text}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    if (report.risks && report.risks.length > 0) {
        html += `
            <div class="report-section">
                <h3 style="color: #333; margin-bottom: 15px; border-left: 4px solid #FF4D4F; padding-left: 12px;">⚠️ 风险提示</h3>
                <div style="display: grid; gap: 12px;">
                    ${report.risks.map(risk => `
                        <div style="padding: 15px; background: #fff1f0; border-radius: 12px; border-left: 4px solid #FF4D4F;">
                            ${risk.message}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } else {
        html += `
            <div class="report-section">
                <h3 style="color: #333; margin-bottom: 15px; border-left: 4px solid #52C41A; padding-left: 12px;">⚠️ 风险提示</h3>
                <div style="padding: 20px; background: #f6ffed; border-radius: 12px; text-align: center; color: #52C41A;">
                    ✅ 暂无风险，运营状态良好
                </div>
            </div>
        `;
    }
    
    document.getElementById('report-content').innerHTML = html;
}

async function regenerateReport() {
    if (!currentUser) {
        alert('请先登录');
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '🔄 生成中...';
    
    try {
        const response = await fetch('/intelligence/report/regenerate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayReport(data.data);
            alert('✅ 报告已重新生成');
        } else {
            alert('生成失败');
        }
    } catch (error) {
        alert('生成失败');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 重新生成';
    }
}

// 扩展 switchTab 函数，切换到报告标签时自动加载
(function() {
    const originalSwitchTab = window.switchTab;
    window.switchTab = function(tabName) {
        if (originalSwitchTab) {
            originalSwitchTab(tabName);
        }
        if (tabName === 'daily-report') {
            setTimeout(() => loadDailyReport(), 100);
        }
    };
})();
