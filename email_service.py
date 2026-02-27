# email_service.py - 邮件服务模块

import os
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """邮件服务"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "电商AI助手")
        
        # 验证码存储（生产环境应该用Redis）
        self.verification_codes = {}
        self.reset_tokens = {}
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """发送邮件"""
        try:
            # 如果没有配置SMTP，记录日志但不报错
            if not self.smtp_user or not self.smtp_password:
                logger.warning(f"SMTP未配置，邮件内容: to={to_email}, subject={subject}")
                logger.info(f"邮件内容:\n{html_content}")
                return True
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def send_verification_code(self, email: str) -> Optional[str]:
        """发送验证码"""
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # 存储验证码（5分钟有效）
        self.verification_codes[email] = {
            'code': code,
            'expire_at': datetime.now() + timedelta(minutes=5)
        }
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background: #f5f7fa; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .code {{ font-size: 32px; font-weight: bold; color: #667eea; text-align: center; letter-spacing: 5px; margin: 30px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="color: #667eea;">🚀 电商AI助手</h1>
                    <p>邮箱验证码</p>
                </div>
                <p>您好，</p>
                <p>您的验证码是：</p>
                <div class="code">{code}</div>
                <p>验证码有效期为5分钟，请尽快使用。</p>
                <p>如果这不是您的操作，请忽略此邮件。</p>
                <div class="footer">
                    <p>© 2026 电商AI助手 - 让电商运营更简单</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        success = self.send_email(email, "【电商AI助手】邮箱验证码", html_content)
        return code if success else None
    
    def verify_code(self, email: str, code: str) -> bool:
        """验证验证码"""
        if email not in self.verification_codes:
            return False
        
        stored = self.verification_codes[email]
        
        # 检查是否过期
        if datetime.now() > stored['expire_at']:
            del self.verification_codes[email]
            return False
        
        # 验证码匹配
        if stored['code'] == code:
            del self.verification_codes[email]
            return True
        
        return False
    
    def send_welcome_email(self, email: str, username: str) -> bool:
        """发送欢迎邮件"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background: #f5f7fa; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="color: #667eea;">🚀 欢迎加入电商AI助手</h1>
                </div>
                <p>Hi {username}，</p>
                <p>欢迎注册电商AI助手！我们很高兴能帮助你在电商运营中取得成功。</p>
                <p><strong>你已获得免费版套餐：</strong></p>
                <ul>
                    <li>每月3次智能选品分析</li>
                    <li>每月3次投流优化分析</li>
                    <li>定价计算器</li>
                    <li>新手教程库</li>
                </ul>
                <p style="text-align: center;">
                    <a href="https://yourdomain.com/static/app.html" class="button">立即开始使用</a>
                </p>
                <p>如有任何问题，欢迎随时联系我们。</p>
                <div class="footer">
                    <p>© 2026 电商AI助手 - 让电商运营更简单</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, "欢迎加入电商AI助手", html_content)
    
    def send_password_reset_email(self, email: str, username: str) -> Optional[str]:
        """发送密码重置邮件"""
        token = secrets.token_urlsafe(32)
        
        # 存储重置令牌（30分钟有效）
        self.reset_tokens[token] = {
            'email': email,
            'expire_at': datetime.now() + timedelta(minutes=30)
        }
        
        reset_url = f"https://yourdomain.com/reset-password?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background: #f5f7fa; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="color: #667eea;">🔐 重置密码</h1>
                </div>
                <p>Hi {username}，</p>
                <p>我们收到了你的密码重置请求。</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">重置密码</a>
                </p>
                <p>此链接30分钟内有效。</p>
                <p>如果这不是你的操作，请忽略此邮件，你的密码不会被更改。</p>
                <div class="footer">
                    <p>© 2026 电商AI助手 - 让电商运营更简单</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        success = self.send_email(email, "【电商AI助手】重置密码", html_content)
        return token if success else None
    
    def verify_reset_token(self, token: str) -> Optional[str]:
        """验证重置令牌"""
        if token not in self.reset_tokens:
            return None
        
        stored = self.reset_tokens[token]
        
        # 检查是否过期
        if datetime.now() > stored['expire_at']:
            del self.reset_tokens[token]
            return None
        
        email = stored['email']
        del self.reset_tokens[token]
        return email


# 全局邮件服务实例
email_service = EmailService()
