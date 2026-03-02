# 香港服务器部署说明文档

## 服务器基本信息

### 连接信息
- **IP地址：** 43.129.205.237
- **SSH用户：** root
- **SSH密码：** Feng15846572185@
- **连接命令：**
  ```bash
  ssh root@43.129.205.237
  # 或使用 sshpass（自动输入密码）
  sshpass -p 'Feng15846572185@' ssh root@43.129.205.237
  ```

### 项目路径
- **代码目录：** `/root/ecommerce-ai-v2/`
- **静态文件：** `/root/ecommerce-ai-v2/static/`
- **主程序：** `/root/ecommerce-ai-v2/main.py`

---

## 网站架构

### 服务运行方式
```
Python FastAPI 服务
├── 主程序: main.py
├── 端口: 80 (HTTP)
├── 进程: python3 main.py
└── 运行方式: 后台持续运行
```

### 服务状态检查
```bash
# 检查服务是否运行
ps aux | grep 'python3 main.py' | grep -v grep

# 查看进程详情
ps aux | grep 661433  # 当前 PID
```

### 重启服务（如果需要）
```bash
# 1. 找到进程 PID
ps aux | grep 'python3 main.py' | grep -v grep

# 2. 杀掉进程
kill <PID>

# 3. 重新启动
cd /root/ecommerce-ai-v2
nohup python3 main.py > server.log 2>&1 &

# 4. 验证启动成功
curl http://localhost:80/api/intelligence/health
```

---

## Git 仓库管理

### 仓库信息
- **GitHub 仓库：** https://github.com/NickZhang-space/duoduoai.git
- **分支：** master
- **本地路径：** `/root/ecommerce-ai-v2/`

### 常用 Git 命令

#### 1. 查看当前状态
```bash
cd /root/ecommerce-ai-v2
git status
```

#### 2. 查看提交历史
```bash
git log --oneline -10  # 查看最近10条提交
```

#### 3. 提交代码
```bash
# 添加所有修改的文件
git add .

# 或添加特定文件
git add static/app.html

# 提交（带说明）
git commit -m "你的提交说明"

# 推送到 GitHub
git push origin master
```

#### 4. 拉取最新代码
```bash
git pull origin master
```

#### 5. 查看远程仓库
```bash
git remote -v
```

#### 6. 回滚到某个版本（如果需要）
```bash
# 查看提交历史，找到要回滚的 commit hash
git log --oneline

# 回滚（保留修改）
git reset --soft <commit-hash>

# 回滚（丢弃修改）
git reset --hard <commit-hash>

# 强制推送（谨慎使用）
git push -f origin master
```

---

## 网站访问地址

### 公网访问
- **首页：** http://43.129.205.237/static/index.html
- **登录页：** http://43.129.205.237/static/login.html
- **应用主页：** http://43.129.205.237/static/app.html
- **API健康检查：** http://43.129.205.237/api/intelligence/health

### 本地测试（在服务器上）
```bash
curl http://localhost:80/static/index.html
curl http://localhost:80/api/intelligence/health
```

---

## 文件结构

```
/root/ecommerce-ai-v2/
├── main.py                    # 主程序入口
├── intelligence_api.py        # AI 功能 API
├── database.py                # 数据库操作
├── static/                    # 静态文件目录
│   ├── index.html            # 首页
│   ├── login.html            # 登录页
│   ├── app.html              # 应用主页
│   ├── dashboard.html        # 数据仪表盘
│   ├── automation.html       # 自动化设置
│   ├── ab_test.html          # A/B测试
│   ├── pricing.html          # 定价页
│   └── js/                   # JavaScript 文件
│       ├── notifications.js
│       └── report.js
├── intelligence/              # AI 模块
│   ├── user_profiler.py
│   ├── ab_test_engine.py
│   ├── dynamic_pricing.py
│   ├── auto_optimizer.py
│   └── ...
├── crawler/                   # 爬虫模块
├── scripts/                   # 脚本目录
└── CHANGELOG-GrowthOS.md     # 改版日志
```

---

## 修改代码的完整流程

### 方式1：直接在服务器上修改（推荐给 AI）

```bash
# 1. SSH 连接服务器
ssh root@43.129.205.237

# 2. 进入项目目录
cd /root/ecommerce-ai-v2

# 3. 备份要修改的文件
cp static/app.html static/app.html.bak

# 4. 编辑文件（使用 vim 或其他编辑器）
vim static/app.html

# 5. 测试修改（访问网站检查）
curl http://localhost:80/static/app.html

# 6. 提交到 Git
git add static/app.html
git commit -m "描述你的修改"
git push origin master
```

### 方式2：本地修改后上传

```bash
# 1. 在本地修改文件

# 2. 使用 scp 上传到服务器
scp local-file.html root@43.129.205.237:/root/ecommerce-ai-v2/static/

# 3. SSH 连接服务器
ssh root@43.129.205.237

# 4. 提交到 Git
cd /root/ecommerce-ai-v2
git add static/file.html
git commit -m "描述修改"
git push origin master
```

---

## 常见问题处理

### 问题1：网站打不开
```bash
# 检查服务是否运行
ps aux | grep 'python3 main.py'

# 如果没运行，重启服务
cd /root/ecommerce-ai-v2
nohup python3 main.py > server.log 2>&1 &
```

### 问题2：修改后没生效
```bash
# 1. 检查文件是否真的修改了
cat /root/ecommerce-ai-v2/static/app.html | grep "你修改的内容"

# 2. 清除浏览器缓存
# 在浏览器中按 Ctrl+Shift+R 强制刷新

# 3. 检查服务器日志
tail -f /root/ecommerce-ai-v2/server.log
```

### 问题3：Git 推送失败
```bash
# 先拉取最新代码
git pull origin master

# 如果有冲突，解决冲突后再推送
git add .
git commit -m "解决冲突"
git push origin master
```

### 问题4：服务器连接不上
```bash
# 检查 IP 是否正确
ping 43.129.205.237

# 检查 SSH 端口是否开放
telnet 43.129.205.237 22

# 确认密码正确：Feng15846572185@
```

---

## 给其他 AI 的说明模板

如果我（小C）出问题了，你可以这样告诉其他 AI：

```
香港服务器信息：
- IP: 43.129.205.237
- 用户: root
- 密码: Feng15846572185@
- 项目路径: /root/ecommerce-ai-v2/

连接命令：
ssh root@43.129.205.237
或
sshpass -p 'Feng15846572185@' ssh root@43.129.205.237

网站代码在 /root/ecommerce-ai-v2/ 目录
主程序是 main.py，运行在端口 80
静态文件在 static/ 目录下

Git 仓库：https://github.com/NickZhang-space/duoduoai.git
分支：master

修改代码后记得：
1. 备份原文件
2. 测试修改
3. git add + git commit + git push

服务重启：
kill <PID>
cd /root/ecommerce-ai-v2
nohup python3 main.py > server.log 2>&1 &
```

---

## 重要提醒

1. **修改前先备份**
   ```bash
   cp file.html file.html.bak
   ```

2. **每次修改都提交 Git**
   ```bash
   git add .
   git commit -m "说明"
   git push
   ```

3. **不要删除 .bak 备份文件**
   - 它们是回滚的保险

4. **修改后验证**
   ```bash
   curl http://localhost:80/static/app.html
   ```

5. **查看日志排查问题**
   ```bash
   tail -f server.log
   ```

---

**文档创建时间：** 2026-03-02 23:30  
**创建人：** 小C (Claude)  
**用途：** 给 Nick 和其他 AI 参考
