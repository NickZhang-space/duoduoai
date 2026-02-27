#!/bin/bash

# 部署脚本

echo "开始部署电商AI助手..."

# 1. 更新系统
echo "1. 更新系统..."
yum update -y

# 2. 安装Python3和依赖
echo "2. 安装Python3..."
yum install python3 python3-pip git -y

# 3. 创建项目目录
echo "3. 创建项目目录..."
mkdir -p /var/www/ecommerce-ai
cd /var/www/ecommerce-ai

# 4. 上传代码（需要手动上传或使用git）
echo "4. 代码已准备..."

# 5. 安装Python依赖
echo "5. 安装依赖..."
pip3 install -r requirements.txt

# 6. 创建管理员账号
echo "6. 创建管理员账号..."
python3 create_admin.py

# 7. 安装并配置Nginx
echo "7. 安装Nginx..."
yum install nginx -y

# 8. 配置Nginx
cat > /etc/nginx/conf.d/ecommerce-ai.conf << 'EOF'
server {
    listen 80;
    server_name 47.97.159.167;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /var/www/ecommerce-ai/static;
    }
}
EOF

# 9. 启动Nginx
echo "8. 启动Nginx..."
systemctl start nginx
systemctl enable nginx

# 10. 安装supervisor管理进程
echo "9. 安装Supervisor..."
yum install supervisor -y

# 11. 配置supervisor
cat > /etc/supervisord.d/ecommerce-ai.ini << 'EOF'
[program:ecommerce-ai]
command=/usr/bin/python3 /var/www/ecommerce-ai/main.py
directory=/var/www/ecommerce-ai
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ecommerce-ai.log
EOF

# 12. 启动supervisor
echo "10. 启动应用..."
systemctl start supervisord
systemctl enable supervisord
supervisorctl reread
supervisorctl update
supervisorctl start ecommerce-ai

echo "部署完成！"
echo "访问地址: http://47.97.159.167"
echo "管理后台: http://47.97.159.167/static/admin.html"
echo "管理员账号: admin / admin123456"
