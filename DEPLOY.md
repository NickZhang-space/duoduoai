# 部署文档

## 服务器信息
- IP: 47.97.159.167
- 用户: root
- 密码: Feng15846572185@

## 部署步骤

### 方法1：自动部署（推荐）

1. 连接服务器：
```bash
ssh root@47.97.159.167
```

2. 上传项目文件到服务器：
```bash
# 在本地执行
cd /root/.openclaw-claude/workspace/ecommerce-ai-v2
tar -czf ecommerce-ai.tar.gz *
scp ecommerce-ai.tar.gz root@47.97.159.167:/root/
```

3. 在服务器上解压并部署：
```bash
# 在服务器上执行
cd /root
tar -xzf ecommerce-ai.tar.gz -C /var/www/ecommerce-ai
cd /var/www/ecommerce-ai
chmod +x deploy.sh
./deploy.sh
```

### 方法2：手动部署

1. 连接服务器并安装依赖：
```bash
ssh root@47.97.159.167
yum update -y
yum install python3 python3-pip nginx supervisor -y
```

2. 创建项目目录：
```bash
mkdir -p /var/www/ecommerce-ai
cd /var/www/ecommerce-ai
```

3. 上传所有项目文件到 /var/www/ecommerce-ai/

4. 安装Python依赖：
```bash
cd /var/www/ecommerce-ai
pip3 install -r requirements.txt
```

5. 创建管理员账号：
```bash
python3 create_admin.py
```

6. 配置Nginx：
```bash
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

systemctl start nginx
systemctl enable nginx
```

7. 配置Supervisor：
```bash
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

systemctl start supervisord
systemctl enable supervisord
supervisorctl reread
supervisorctl update
supervisorctl start ecommerce-ai
```

## 访问地址

- 首页: http://47.97.159.167
- 管理后台: http://47.97.159.167/static/admin.html

## 管理员账号

- 用户名: admin
- 密码: admin123456
- **请登录后立即修改密码！**

## 常用命令

### 查看应用状态
```bash
supervisorctl status ecommerce-ai
```

### 重启应用
```bash
supervisorctl restart ecommerce-ai
```

### 查看日志
```bash
tail -f /var/log/ecommerce-ai.log
```

### 停止应用
```bash
supervisorctl stop ecommerce-ai
```

### 启动应用
```bash
supervisorctl start ecommerce-ai
```

## 更新代码

1. 上传新代码到服务器
2. 重启应用：
```bash
supervisorctl restart ecommerce-ai
```

## 故障排查

### 应用无法启动
```bash
# 查看日志
tail -100 /var/log/ecommerce-ai.log

# 手动启动测试
cd /var/www/ecommerce-ai
python3 main.py
```

### Nginx无法访问
```bash
# 检查Nginx状态
systemctl status nginx

# 重启Nginx
systemctl restart nginx

# 查看Nginx日志
tail -f /var/log/nginx/error.log
```

### 端口被占用
```bash
# 查看8000端口占用
netstat -tlnp | grep 8000

# 杀死进程
kill -9 <PID>
```

## 安全建议

1. 修改管理员密码
2. 配置防火墙（只开放80端口）
3. 定期备份数据库
4. 配置HTTPS（使用Let's Encrypt）

## 备份数据库

```bash
# 备份
cp /var/www/ecommerce-ai/ecommerce_ai.db /root/backup_$(date +%Y%m%d).db

# 恢复
cp /root/backup_20260226.db /var/www/ecommerce-ai/ecommerce_ai.db
supervisorctl restart ecommerce-ai
```
