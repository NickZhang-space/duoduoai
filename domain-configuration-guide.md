# 域名配置说明 - duoduoyouhua.com

## 架构图

```
用户浏览器
    ↓
https://duoduoyouhua.com
    ↓
Cloudflare CDN (172.67.198.8 / 104.21.68.190)
    ↓
香港服务器 43.129.205.237:80
    ↓
Python FastAPI (main.py)
```

---

## 域名解析配置

### 当前状态
- **域名：** duoduoyouhua.com
- **DNS 解析：** 指向 Cloudflare CDN
  - IP1: 172.67.198.8
  - IP2: 104.21.68.190
- **CDN 提供商：** Cloudflare
- **源站（Origin Server）：** 43.129.205.237:80

### Cloudflare 的作用
1. **CDN 加速** - 全球节点缓存静态资源
2. **HTTPS 证书** - 自动提供 SSL/TLS 加密
3. **DDoS 防护** - 防止攻击
4. **流量代理** - 隐藏真实服务器 IP

---

## 配置位置

### 1. Cloudflare 控制台
- **登录地址：** https://dash.cloudflare.com
- **需要配置的地方：**
  - DNS 记录（A 记录指向 43.129.205.237）
  - SSL/TLS 设置（推荐：Full 或 Full (strict)）
  - 防火墙规则
  - 缓存规则

### 2. 服务器端
- **监听端口：** 80 (HTTP)
- **程序：** Python FastAPI (main.py)
- **无需 Nginx** - 直接监听 80 端口
- **进程 PID：** 661433

---

## 如何修改域名配置

### 场景1：更换服务器 IP

如果要换到新服务器（比如从 43.129.205.237 换到新 IP）：

1. **在 Cloudflare 控制台修改 DNS 记录**
   - 登录 Cloudflare
   - 选择域名 duoduoyouhua.com
   - 进入 DNS 管理
   - 找到 A 记录（指向 43.129.205.237）
   - 修改为新的 IP 地址
   - 保存

2. **在新服务器上部署代码**
   ```bash
   # 在新服务器上
   git clone https://github.com/NickZhang-space/duoduoai.git /root/ecommerce-ai-v2
   cd /root/ecommerce-ai-v2
   nohup python3 main.py > server.log 2>&1 &
   ```

3. **验证**
   ```bash
   curl http://新IP:80/api/intelligence/health
   ```

### 场景2：添加新域名

如果要添加新域名（比如 www.duoduoyouhua.com）：

1. **在 Cloudflare 添加 DNS 记录**
   - 类型：A 或 CNAME
   - 名称：www
   - 内容：43.129.205.237 或 duoduoyouhua.com
   - 代理状态：已代理（橙色云朵）

2. **无需修改服务器代码** - FastAPI 会自动处理所有域名

### 场景3：启用 HTTPS

当前已通过 Cloudflare 启用 HTTPS，如果需要调整：

1. **在 Cloudflare 控制台**
   - SSL/TLS → 概述
   - 选择加密模式：
     - **Full** - Cloudflare 到源站用 HTTP（当前推荐）
     - **Full (strict)** - 需要源站有有效证书
     - **Flexible** - 源站用 HTTP，用户到 Cloudflare 用 HTTPS

2. **如果选择 Full (strict)，需要在服务器配置 SSL**
   ```bash
   # 安装 certbot
   apt install certbot
   
   # 获取证书
   certbot certonly --standalone -d duoduoyouhua.com
   
   # 修改 main.py 使用 HTTPS
   # 或使用 Nginx 反向代理
   ```

---

## 当前配置检查

### DNS 解析
```bash
# 检查域名解析
nslookup duoduoyouhua.com
# 应该返回 Cloudflare 的 IP（172.67.198.8 等）

# 检查真实源站 IP
curl -H "Host: duoduoyouhua.com" http://43.129.205.237/
```

### 服务器监听
```bash
# 检查端口 80 是否监听
netstat -tlnp | grep :80
# 应该显示：python3 (PID 661433) 监听 0.0.0.0:80
```

### 网站访问
```bash
# 通过域名访问
curl -I https://duoduoyouhua.com

# 通过 IP 访问（绕过 Cloudflare）
curl -I http://43.129.205.237
```

---

## 故障排查

### 问题1：网站打不开

**检查步骤：**
1. 检查服务器是否运行
   ```bash
   ssh root@43.129.205.237
   ps aux | grep 'python3 main.py'
   ```

2. 检查端口是否监听
   ```bash
   netstat -tlnp | grep :80
   ```

3. 检查 Cloudflare 状态
   - 登录 Cloudflare 控制台
   - 查看是否有攻击或异常流量

4. 检查 DNS 解析
   ```bash
   nslookup duoduoyouhua.com
   ```

### 问题2：HTTPS 证书错误

**原因：** Cloudflare SSL 模式配置不当

**解决：**
1. 登录 Cloudflare
2. SSL/TLS → 概述
3. 改为 "Full" 模式（不是 Full strict）

### 问题3：网站很慢

**可能原因：**
1. Cloudflare 缓存未生效
2. 服务器性能问题
3. 数据库查询慢

**优化：**
1. 在 Cloudflare 设置缓存规则
2. 优化服务器代码
3. 添加数据库索引

---

## 给其他 AI 的说明

如果需要告诉其他 AI 关于域名配置：

```
域名：duoduoyouhua.com
架构：Cloudflare CDN → 香港服务器

Cloudflare 配置：
- DNS A 记录指向 43.129.205.237
- SSL 模式：Full
- 代理状态：已启用（橙色云朵）

服务器配置：
- IP: 43.129.205.237
- 端口: 80 (HTTP)
- 程序: Python FastAPI (main.py)
- 无 Nginx，直接监听 80 端口

修改域名配置需要：
1. 登录 Cloudflare 控制台
2. 修改 DNS 记录
3. 无需修改服务器代码

Cloudflare 登录信息需要 Nick 提供
```

---

## 重要提醒

1. **Cloudflare 账号信息**
   - 需要 Nick 提供登录邮箱和密码
   - 或者添加你为协作者

2. **不要直接暴露服务器 IP**
   - Cloudflare 隐藏了真实 IP
   - 保护服务器免受攻击

3. **修改 DNS 需要时间**
   - DNS 传播需要几分钟到几小时
   - 可以用 `nslookup` 检查是否生效

4. **备份 Cloudflare 配置**
   - 定期导出 DNS 记录
   - 记录防火墙规则

---

**文档创建时间：** 2026-03-02 23:35  
**创建人：** 小C (Claude)  
**用途：** 说明域名如何连接到服务器
