// ==================== A/B测试功能 ====================

let currentExperiments = [];

// 加载实验列表
async function loadExperiments() {
    try {
        const response = await fetch('/api/ab-test/list?user_id=1');
        const data = await response.json();
        
        if (data.success) {
            currentExperiments = data.data;
            renderExperimentsList(data.data);
        } else {
            console.error('加载实验列表失败:', data.error);
        }
    } catch (error) {
        console.error('加载实验列表失败:', error);
    }
}

// 渲染实验列表
function renderExperimentsList(experiments) {
    const list = document.getElementById('experiments-list');
    
    if (experiments.length === 0) {
        list.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #999;">
                <div style="font-size: 2em; margin-bottom: 10px;">🧪</div>
                <div>还没有创建实验</div>
            </div>
        `;
        return;
    }
    
    list.innerHTML = experiments.map(exp => `
        <div style="border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; background: white;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                <div>
                    <h4 style="margin: 0 0 5px 0; color: #333;">${exp.name}</h4>
                    <span style="display: inline-block; padding: 4px 12px; background: ${exp.status === 'running' ? '#e8f5e9' : '#f5f5f5'}; color: ${exp.status === 'running' ? '#4caf50' : '#999'}; border-radius: 12px; font-size: 0.85em;">
                        ${exp.status === 'running' ? '🟢 进行中' : '⚫ 已停止'}
                    </span>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button onclick="viewExperimentResults('${exp.id}')" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em;">
                        查看结果
                    </button>
                    ${exp.status === 'running' ? `
                        <button onclick="stopExperiment('${exp.id}')" style="background: #f56565; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em;">
                            停止
                        </button>
                    ` : ''}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                ${exp.variants.map((v, i) => `
                    <div style="padding: 12px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-weight: 500; margin-bottom: 5px;">方案${v.name}</div>
                        <div style="font-size: 0.9em; color: #666;">流量: ${(exp.traffic_split[i] * 100).toFixed(0)}%</div>
                    </div>
                `).join('')}
            </div>
            
            <div style="margin-top: 10px; font-size: 0.85em; color: #999;">
                创建时间: ${new Date(exp.created_at * 1000).toLocaleString()}
            </div>
        </div>
    `).join('');
}

// 显示创建实验模态框
function showCreateExperimentModal() {
    document.getElementById('create-experiment-modal').style.display = 'flex';
}

// 关闭创建实验模态框
function closeCreateExperimentModal() {
    document.getElementById('create-experiment-modal').style.display = 'none';
    document.getElementById('experiment-form').reset();
}

// 更新流量分配显示
function updateTrafficSplit(value) {
    document.getElementById('split-a').textContent = value;
    document.getElementById('split-b').textContent = 100 - value;
}

// 创建实验
document.getElementById('experiment-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const name = document.getElementById('exp-name').value;
    const metric = document.getElementById('exp-metric').value;
    const trafficSplit = parseInt(document.getElementById('traffic-split').value) / 100;
    
    const variantA = {
        name: 'A',
        config: {
            name: document.getElementById('variant-a-name').value || '方案A',
            price: parseFloat(document.getElementById('variant-a-price').value) || 0,
            title: document.getElementById('variant-a-title').value || ''
        }
    };
    
    const variantB = {
        name: 'B',
        config: {
            name: document.getElementById('variant-b-name').value || '方案B',
            price: parseFloat(document.getElementById('variant-b-price').value) || 0,
            title: document.getElementById('variant-b-title').value || ''
        }
    };
    
    try {
        const response = await fetch('/api/ab-test/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: name,
                variants: [variantA, variantB],
                metrics: [metric],
                traffic_split: [trafficSplit, 1 - trafficSplit],
                user_id: '1'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ 实验创建成功！');
            closeCreateExperimentModal();
            loadExperiments();
        } else {
            alert('❌ 创建失败: ' + data.error);
        }
    } catch (error) {
        console.error('创建实验失败:', error);
        alert('❌ 创建失败');
    }
});

// 查看实验结果
async function viewExperimentResults(experimentId) {
    try {
        const response = await fetch(`/api/ab-test/results/${experimentId}`);
        const data = await response.json();
        
        if (data.success) {
            renderExperimentResults(data.data);
            document.getElementById('experiment-results').style.display = 'block';
            document.getElementById('experiment-results').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert('获取结果失败: ' + data.error);
        }
    } catch (error) {
        console.error('获取结果失败:', error);
        alert('获取结果失败');
    }
}

// 渲染实验结果
function renderExperimentResults(results) {
    const resultsContent = document.getElementById('results-content');
    
    const variants = Object.keys(results.results);
    
    let html = `
        <div style="margin-bottom: 20px;">
            <h4 style="margin: 0 0 10px 0;">${results.experiment_name}</h4>
            <span style="display: inline-block; padding: 4px 12px; background: ${results.status === 'running' ? '#e8f5e9' : '#f5f5f5'}; color: ${results.status === 'running' ? '#4caf50' : '#999'}; border-radius: 12px; font-size: 0.85em;">
                ${results.status === 'running' ? '🟢 进行中' : '⚫ 已停止'}
            </span>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 25px;">
    `;
    
    variants.forEach(variant => {
        const result = results.results[variant];
        const isWinner = variant === results.winner;
        
        html += `
            <div style="border: 2px solid ${isWinner ? '#4caf50' : '#e0e0e0'}; border-radius: 12px; padding: 20px; background: ${isWinner ? '#f1f8f4' : 'white'}; position: relative;">
                ${isWinner ? '<div style="position: absolute; top: 10px; right: 10px; font-size: 1.5em;">👑</div>' : ''}
                
                <h4 style="margin: 0 0 15px 0; color: #333;">方案${variant}</h4>
                
                <div style="margin-bottom: 15px;">
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">样本量</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #E84D1A;">${result.sample_size}</div>
                </div>
                
                ${Object.entries(result.metrics).map(([metric, values]) => `
                    <div style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-size: 0.85em; color: #666; margin-bottom: 3px;">${metric}</div>
                        <div style="font-size: 1.2em; font-weight: 500; color: #333;">${values.mean.toFixed(2)}</div>
                    </div>
                `).join('')}
                
                ${result.config && Object.keys(result.config).length > 0 ? `
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e0e0e0;">
                        <div style="font-size: 0.85em; color: #666; margin-bottom: 8px;">配置</div>
                        ${Object.entries(result.config).map(([key, value]) => `
                            <div style="font-size: 0.9em; color: #333; margin-bottom: 3px;">
                                ${key}: ${value}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    html += `
        </div>
        
        <div style="padding: 20px; background: #fff3e0; border-radius: 12px; border-left: 4px solid #FFA940;">
            <h4 style="margin: 0 0 10px 0; color: #333;">💡 建议</h4>
            <p style="margin: 0; color: #666;">${results.recommendation}</p>
            ${results.winner && results.confidence > 0.7 ? `
                <button onclick="alert('应用功能开发中')" style="margin-top: 15px; background: linear-gradient(135deg, #E84D1A 0%, #FF6B35 100%); color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 500;">
                    应用方案${results.winner}
                </button>
            ` : ''}
        </div>
    `;
    
    resultsContent.innerHTML = html;
}

// 停止实验
async function stopExperiment(experimentId) {
    if (!confirm('确定要停止这个实验吗？')) return;
    
    try {
        const response = await fetch(`/api/ab-test/stop/${experimentId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ 实验已停止');
            loadExperiments();
        } else {
            alert('❌ 停止失败: ' + data.error);
        }
    } catch (error) {
        console.error('停止实验失败:', error);
        alert('❌ 停止失败');
    }
}

// 扩展 switchTab 函数
(function() {
    const originalSwitchTab = window.switchTab;
    window.switchTab = function(tabName) {
        if (originalSwitchTab) {
            originalSwitchTab(tabName);
        }
        if (tabName === 'ab-test') {
            setTimeout(() => loadExperiments(), 100);
        }
    };
})();
