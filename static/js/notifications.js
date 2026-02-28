/**
 * 通知管理器
 * 管理浏览器通知权限和推送
 */

class NotificationManager {
    constructor() {
        this.permission = Notification.permission;
        this.settings = this.loadSettings();
    }

    /**
     * 请求通知权限
     */
    async requestPermission() {
        if (!('Notification' in window)) {
            console.warn('浏览器不支持通知');
            return false;
        }

        if (this.permission === 'default') {
            const permission = await Notification.requestPermission();
            this.permission = permission;
            return permission === 'granted';
        }

        return this.permission === 'granted';
    }

    /**
     * 发送通知
     */
    send(title, body, options = {}) {
        if (this.permission !== 'granted') {
            console.warn('通知权限未授予');
            return;
        }

        const defaultOptions = {
            icon: '/static/logo.png',
            badge: '/static/badge.png',
            tag: 'duoduo-ai',
            requireInteraction: false,
            ...options
        };

        try {
            const notification = new Notification(title, {
                body: body,
                ...defaultOptions
            });

            // 点击通知时聚焦窗口
            notification.onclick = function() {
                window.focus();
                notification.close();
            };

            return notification;
        } catch (error) {
            console.error('发送通知失败:', error);
        }
    }

    /**
     * 发送风险预警通知
     */
    sendRiskAlert(risk) {
        if (!this.settings.notifyRisks) return;

        const icons = {
            high: '🔴',
            medium: '🟡',
            low: '🟢'
        };

        this.send(
            `${icons[risk.level] || '⚠️'} 风险预警`,
            risk.message,
            { tag: 'risk-alert' }
        );
    }

    /**
     * 发送机会发现通知
     */
    sendOpportunity(opportunity) {
        if (!this.settings.notifyOpportunities) return;

        this.send(
            '💰 市场机会',
            opportunity.description,
            { tag: 'opportunity' }
        );
    }

    /**
     * 发送每日报告通知
     */
    sendDailyReport(report) {
        if (!this.settings.notifyReports) return;

        this.send(
            '📊 每日智能报告已生成',
            '点击查看今日运营建议',
            { tag: 'daily-report' }
        );
    }

    /**
     * 加载通知设置
     */
    loadSettings() {
        const defaultSettings = {
            notifyRisks: true,
            notifyOpportunities: true,
            notifyReports: true
        };

        const saved = localStorage.getItem('notificationSettings');
        return saved ? JSON.parse(saved) : defaultSettings;
    }

    /**
     * 保存通知设置
     */
    saveSettings(settings) {
        this.settings = { ...this.settings, ...settings };
        localStorage.setItem('notificationSettings', JSON.stringify(this.settings));
    }

    /**
     * 获取通知设置
     */
    getSettings() {
        return { ...this.settings };
    }
}

// 全局实例
const notificationManager = new NotificationManager();

/**
 * 风险监控
 * 定期检查风险并推送通知
 */
class RiskMonitor {
    constructor(checkInterval = 300000) { // 默认5分钟
        this.checkInterval = checkInterval;
        this.intervalId = null;
        this.lastCheck = null;
    }

    start() {
        if (this.intervalId) {
            console.warn('风险监控已在运行');
            return;
        }

        console.log('启动风险监控...');
        this.check(); // 立即检查一次
        this.intervalId = setInterval(() => this.check(), this.checkInterval);
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('风险监控已停止');
        }
    }

    async check() {
        try {
            const currentUser = JSON.parse(localStorage.getItem('currentUser'));
            if (!currentUser) return;

            const response = await fetch(`/intelligence/check-risks?user_id=${currentUser.id}`);
            const data = await response.json();

            if (data.success && data.data.high_risk.length > 0) {
                // 只通知高风险
                const highRisk = data.data.high_risk[0];
                notificationManager.sendRiskAlert({
                    level: 'high',
                    message: highRisk.title + ': ' + highRisk.description
                });
            }

            this.lastCheck = new Date();
        } catch (error) {
            console.error('风险检查失败:', error);
        }
    }
}

// 全局风险监控实例
const riskMonitor = new RiskMonitor();
