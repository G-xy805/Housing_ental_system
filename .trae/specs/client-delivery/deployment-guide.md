# 房屋租赁系统部署实施流程文档

**版本：** 1.0  
**最后更新：** 2026-02-28  
**适用系统：** 房屋租赁管理系统（Flask + Vue 3）

---

## 目录

1. [环境检查清单](#1-环境检查清单)
2. [后端部署步骤](#2-后端部署步骤)
3. [前端部署步骤](#3-前端部署步骤)
4. [系统联调与验证](#4-系统联调与验证)
5. [常见问题排查](#5-常见问题排查)

---

## 1. 环境检查清单

### 1.1 服务器环境要求

#### 硬件配置

| 组件 | 最低配置 | 推荐配置 | 生产环境配置 |
|------|----------|----------|--------------|
| CPU | 2 核心 | 4 核心 | 8 核心+ |
| 内存 | 4 GB | 8 GB | 16 GB+ |
| 存储 | 20 GB | 50 GB | 100 GB+ SSD |
| 操作系统 | Windows 10 / Linux | Windows Server 2019 / Ubuntu 20.04+ | Ubuntu 22.04 LTS / CentOS 8+ |

#### 操作系统兼容性

- ✅ **Windows**: Windows 10/11, Windows Server 2019/2022
- ✅ **Linux**: Ubuntu 20.04+, CentOS 8+, Debian 11+
- ✅ **macOS**: macOS 11+ (仅开发环境)

### 1.2 网络要求

#### 端口配置

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| Flask 应用 | 5000 | TCP | 后端 API 服务 |
| Gunicorn/uWSGI | 8000 | TCP | 生产环境 WSGI 服务器 |
| Nginx | 80/443 | TCP | Web 服务器/反向代理 |
| MySQL | 3306 | TCP | 数据库（如使用） |
| PostgreSQL | 5432 | TCP | 数据库（如使用） |

#### 带宽要求

- **开发环境**: 10 Mbps
- **生产环境**: 100 Mbps+
- **高并发场景**: 1 Gbps+

#### 防火墙配置

**Windows 防火墙配置：**

```powershell
# 开放后端端口
netsh advfirewall firewall add rule name="Flask API" dir=in action=allow protocol=TCP localport=5000
netsh advfirewall firewall add rule name="Gunicorn" dir=in action=allow protocol=TCP localport=8000

# 开放 Web 端口
netsh advfirewall firewall add rule name="HTTP" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="HTTPS" dir=in action=allow protocol=TCP localport=443

# 开放数据库端口（如需要远程访问）
netsh advfirewall firewall add rule name="MySQL" dir=in action=allow protocol=TCP localport=3306
```

**Linux (UFW) 防火墙配置：**

```bash
# 启用 UFW
sudo ufw enable

# 允许 SSH
sudo ufw allow 22/tcp

# 允许 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许应用端口
sudo ufw allow 5000/tcp
sudo ufw allow 8000/tcp

# 查看状态
sudo ufw status verbose
```

### 1.3 数据库要求

#### 支持的数据库类型

| 数据库 | 版本 | 推荐场景 |
|--------|------|----------|
| SQLite | 3.35+ | 开发/测试环境 |
| MySQL | 8.0+ | 生产环境 |
| PostgreSQL | 13+ | 生产环境 |

#### SQLite 配置（开发环境）

```bash
# SQLite 内置于 Python，无需额外安装
# 验证 SQLite 版本
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

#### MySQL 配置（生产环境）

**安装 MySQL (Ubuntu)：**

```bash
# 添加 MySQL 仓库
wget https://dev.mysql.com/get/mysql-apt-config_0.8.29-1_all.deb
sudo dpkg -i mysql-apt-config_0.8.29-1_all.deb
sudo apt update
sudo apt install mysql-server

# 启动 MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置
sudo mysql_secure_installation
```

**创建数据库和用户：**

```sql
-- 登录 MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE housing_rental CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'housing_user'@'localhost' IDENTIFIED BY 'your_secure_password';

-- 授权
GRANT ALL PRIVILEGES ON housing_rental.* TO 'housing_user'@'localhost';
FLUSH PRIVILEGES;

-- 验证
SHOW GRANTS FOR 'housing_user'@'localhost';
```

#### PostgreSQL 配置（生产环境）

**安装 PostgreSQL (Ubuntu)：**

```bash
# 添加 PostgreSQL 仓库
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
sudo apt update
sudo apt install postgresql postgresql-contrib

# 启动 PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**创建数据库和用户：**

```bash
# 切换到 postgres 用户
sudo -i -u postgres

# 进入 PostgreSQL
psql

-- 创建数据库
CREATE DATABASE housing_rental;

-- 创建用户
CREATE USER housing_user WITH PASSWORD 'your_secure_password';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE housing_rental TO housing_user;

-- 退出
\q
exit
```

### 1.4 依赖软件版本

#### 必需软件

| 软件 | 最低版本 | 推荐版本 | 验证命令 |
|------|----------|----------|----------|
| Python | 3.8 | 3.10+ | `python --version` |
| Node.js | 16.x | 18.x LTS | `node --version` |
| npm | 7.x | 9.x | `npm --version` |
| Nginx | 1.18 | 1.24+ | `nginx -v` |

#### Python 依赖

核心依赖（来自 [`requirements.txt`](file:///d:/Pro/Housing_ental_system/requirements.txt)）：

```
Flask==3.0.0
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.1.1
PyJWT==2.8.0
Werkzeug==3.0.1
python-dotenv==1.0.0
openpyxl==3.1.2
reportlab==4.0.7
APScheduler==3.10.4
```

#### Node.js 依赖

核心依赖（来自 [`package.json`](file:///d:/Pro/Housing_ental_system/package.json)）：

```json
{
  "vue": "^3.5.0",
  "vue-router": "^4.4.0",
  "pinia": "^2.2.0",
  "element-plus": "^2.8.0",
  "axios": "^1.7.0",
  "echarts": "^5.5.0",
  "vite": "^5.0.8"
}
```

---

## 2. 后端部署步骤

### 2.1 Python 环境配置

#### 步骤 1：安装 Python

**Windows:**

```powershell
# 使用 Chocolatey 安装
choco install python3.10

# 或使用官方安装程序
# 下载地址：https://www.python.org/downloads/windows/
```

**Linux (Ubuntu):**

```bash
# 安装 Python 3.10
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev python3-pip

# 验证安装
python3 --version
pip3 --version
```

#### 步骤 2：创建虚拟环境

```bash
# 进入项目目录
cd d:\Pro\Housing_ental_system

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.\.venv\Scripts\activate

# Linux/macOS:
source .venv/bin/activate
```

#### 步骤 3：安装依赖

```bash
# 升级 pip
python -m pip install --upgrade pip

# 安装生产环境依赖
pip install -r requirements.txt

# 如需使用 MySQL，额外安装
pip install pymysql

# 如需使用 PostgreSQL，额外安装
pip install psycopg2-binary

# 安装 Gunicorn（Linux 生产环境）
pip install gunicorn

# 或使用 waitress（Windows 生产环境）
pip install waitress
```

### 2.2 数据库配置和初始化

#### 配置数据库连接

编辑 `.env` 文件：

**SQLite 配置（开发环境）：**

```ini
DATABASE_URI=sqlite:///housing_rental.db
```

**MySQL 配置（生产环境）：**

```ini
DATABASE_URI=mysql+pymysql://housing_user:your_secure_password@localhost:3306/housing_rental?charset=utf8mb4
```

**PostgreSQL 配置（生产环境）：**

```ini
DATABASE_URI=postgresql://housing_user:your_secure_password@localhost:5432/housing_rental
```

#### 初始化数据库

```bash
# 激活虚拟环境后，进入 Python shell
python

# 在 Python shell 中执行
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
...     print("数据库初始化完成！")
>>> exit()
```

或创建初始化脚本 `init_db.py`：

```python
"""
数据库初始化脚本
"""
from app import create_app, db
from app.models import User, House, Contract, Payment

app = create_app()

with app.app_context():
    # 创建所有表
    db.create_all()
    print("✓ 数据库表创建成功！")
    
    # 创建默认管理员账户
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@housing.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        db.session.commit()
        print("✓ 默认管理员账户创建成功！")
        print("  用户名：admin")
        print("  密码：admin123")
        print("  ⚠️  请首次登录后立即修改密码！")
```

执行初始化：

```bash
python init_db.py
```

### 2.3 环境变量配置

#### 生产环境配置模板

创建 `.env.production` 文件：

```ini
# Flask Configuration
FLASK_APP=app
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Security
SECRET_KEY=your-super-secret-key-min-32-characters-long
JWT_SECRET_KEY=your-jwt-secret-key-min-32-characters-long
JWT_ACCESS_TOKEN_EXPIRES=86400

# Database Configuration
DATABASE_URI=mysql+pymysql://housing_user:your_secure_password@localhost:3306/housing_rental?charset=utf8mb4

# CORS Configuration
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# File Upload
UPLOAD_FOLDER=/var/www/housing/uploads
MAX_CONTENT_LENGTH=16777216

# Scheduler
SCHEDULER_API_ENABLED=False

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/housing/app.log
```

#### 安全密钥生成

```python
# 生成安全密钥
import secrets

print("SECRET_KEY:", secrets.token_hex(32))
print("JWT_SECRET_KEY:", secrets.token_hex(32))
```

### 2.4 Flask 应用部署

#### 开发环境启动

```bash
# 激活虚拟环境
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux

# 直接运行
python run.py

# 或使用 Flask 命令
flask run --host=0.0.0.0 --port=5000
```

#### 生产环境部署 - Gunicorn (Linux)

**安装 Gunicorn：**

```bash
pip install gunicorn
```

**创建 Gunicorn 配置文件 `gunicorn.conf.py`：**

```python
"""
Gunicorn 配置文件
"""
import multiprocessing

# 绑定地址
bind = "0.0.0.0:8000"

# Worker 进程数
workers = multiprocessing.cpu_count() * 2 + 1

# Worker 类型
worker_class = "sync"

# 单 Worker 最大连接数
worker_connections = 1000

# Worker 最大请求数（达到后重启）
max_requests = 1000
max_requests_jitter = 50

# 超时设置
timeout = 120
keepalive = 5

# 进程命名
proc_name = "housing-rental"

# 守护进程
daemon = False

# PID 文件
pidfile = "/var/run/housing-rental.pid"

# 日志配置
accesslog = "/var/log/housing/access.log"
errorlog = "/var/log/housing/error.log"
loglevel = "info"

# 在每个 worker 进程启动后启动 APScheduler
def post_worker_init(worker):
    """Worker 初始化后的钩子"""
    from app import create_app
    app = create_app('production')
    with app.app_context():
        # 初始化调度器
        if hasattr(app, 'scheduler') and not app.scheduler.running:
            app.scheduler.start()
```

**创建 systemd 服务文件 `/etc/systemd/system/housing-rental.service`：**

```ini
[Unit]
Description=Housing Rental System Gunicorn Instance
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/housing-rental
ExecStart=/var/www/housing-rental/.venv/bin/gunicorn --config gunicorn.conf.py app:app

# 环境变量
Environment="PATH=/var/www/housing-rental/.venv/bin"
EnvironmentFile=/var/www/housing-rental/.env.production

# 重启策略
Restart=always
RestartSec=10

# 安全设置
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**启动服务：**

```bash
# 创建日志目录
sudo mkdir -p /var/log/housing
sudo chown www-data:www-data /var/log/housing

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable housing-rental

# 启动服务
sudo systemctl start housing-rental

# 查看状态
sudo systemctl status housing-rental

# 查看日志
sudo journalctl -u housing-rental -f
```

#### 生产环境部署 - Waitress (Windows)

**安装 Waitress：**

```bash
pip install waitress
```

**创建 `start_production.py` 脚本：**

```python
"""
Windows 生产环境启动脚本 - 使用 Waitress
"""
import os
from dotenv import load_dotenv
from waitress import serve
from app import create_app, db

# 加载环境变量
load_dotenv('.env.production')

# 创建应用
app = create_app('production')

# 获取配置
host = os.getenv('FLASK_HOST', '0.0.0.0')
port = int(os.getenv('FLASK_PORT', 8000))
threads = int(os.getenv('WAITRESS_THREADS', 4))
connection_limit = int(os.getenv('WAITRESS_CONNECTION_LIMIT', 100))

print(f"启动房屋租赁系统（生产环境）...")
print(f"使用 Waitress WSGI 服务器")
print(f"地址：http://{host}:{port}")
print(f"线程数：{threads}")

# 启动服务器
serve(
    app,
    host=host,
    port=port,
    threads=threads,
    connection_limit=connection_limit,
    url_scheme='http'
)
```

**创建 Windows 服务（使用 NSSM）：**

```powershell
# 下载 NSSM
# 下载地址：https://nssm.cc/download

# 安装服务
nssm install HousingRental "d:\Pro\Housing_ental_system\.venv\Scripts\python.exe" "d:\Pro\Housing_ental_system\start_production.py"

# 配置服务参数
nssm set HousingRental DisplayName "Housing Rental System"
nssm set HousingRental Description "房屋租赁管理系统后端服务"
nssm set HousingRental Start SERVICE_AUTO_START
nssm set HousingRental AppDirectory "d:\Pro\Housing_ental_system"
nssm set HousingRental AppStdout "d:\Pro\Housing_ental_system\logs\app.log"
nssm set HousingRental AppStderr "d:\Pro\Housing_ental_system\logs\error.log"

# 启动服务
nssm start HousingRental
```

### 2.5 定时任务配置

APScheduler 已在应用中集成。配置说明：

**在应用工厂中启用调度器：**

```python
# app/__init__.py 中的配置
from apscheduler.schedulers.background import BackgroundScheduler

def create_app(config_name):
    # ... 其他配置
    
    scheduler = BackgroundScheduler()
    
    if config_name != 'testing':
        # 添加定时任务
        scheduler.add_job(
            func=your_scheduled_function,
            trigger="cron",
            hour=2,
            minute=0,
            id='daily_task',
            replace_existing=True
        )
        scheduler.start()
    
    # 在应用上下文中存储调度器
    app.scheduler = scheduler
    
    return app
```

**生产环境注意事项：**

- 确保只有一个 Gunicorn worker 运行调度器，避免重复执行
- 使用 Redis 或数据库锁确保分布式环境下的任务唯一性
- 配置任务执行日志记录

### 2.6 日志配置

#### 创建日志目录

```bash
# Linux
sudo mkdir -p /var/log/housing
sudo chown www-data:www-data /var/log/housing

# Windows
mkdir logs
```

#### 日志配置代码

在应用工厂中添加日志配置：

```python
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_name):
    # ... 其他配置
    
    # 配置日志
    if not app.debug:
        # 确保日志目录存在
        log_dir = os.getenv('LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 文件日志处理器
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        # 错误日志处理器
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, 'error.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=10
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        error_handler.setLevel(logging.ERROR)
        
        # 添加处理器
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
        app.logger.setLevel(logging.INFO)
        
        app.logger.info('房屋租赁系统启动')
    
    return app
```

---

## 3. 前端部署步骤

### 3.1 Node.js 环境配置

#### 安装 Node.js

**Windows:**

```powershell
# 使用 Chocolatey
choco install nodejs-lts

# 或使用官方安装程序
# 下载地址：https://nodejs.org/
```

**Linux (Ubuntu):**

```bash
# 使用 NodeSource 仓库安装 LTS 版本
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证安装
node --version
npm --version
```

**使用 NVM（推荐）：**

```bash
# 安装 NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# 重新加载配置
source ~/.bashrc

# 安装 Node.js LTS
nvm install 18
nvm use 18
nvm alias default 18

# 验证
node --version
npm --version
```

#### 配置 npm 镜像（中国大陆）

```bash
# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 验证
npm config get registry
```

### 3.2 前端项目构建

#### 步骤 1：安装依赖

```bash
# 进入项目目录
cd d:\Pro\Housing_ental_system

# 安装依赖
npm install

# 或使用 yarn
yarn install
```

#### 步骤 2：配置 API 地址

编辑 `vite.config.js` 中的代理配置（开发环境）：

```javascript
server: {
  port: 5173,
  host: true,
  proxy: {
    '/api': {
      target: 'http://localhost:5000',  // 生产环境改为实际后端地址
      changeOrigin: true,
      secure: false
    }
  }
}
```

生产环境建议在 `.env.production` 中配置：

```ini
VITE_API_BASE_URL=https://api.your-domain.com
```

在代码中使用：

```javascript
// src/utils/request.js 或类似文件
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
```

#### 步骤 3：构建生产版本

```bash
# 构建
npm run build

# 构建产物位置
# dist/
#   ├── index.html
#   ├── static/
#   │   ├── assets/
#   │   │   ├── index-[hash].js
#   │   │   ├── vendor-vue-[hash].js
#   │   │   └── ...
#   │   └── ...
#   └── ...
```

**构建配置说明（来自 [`vite.config.js`](file:///d:/Pro/Housing_ental_system/vite.config.js)）：**

```javascript
build: {
  outDir: 'dist',              // 输出目录
  assetsDir: 'static',         // 静态资源目录
  sourcemap: false,            // 不生成 source map（生产环境）
  rollupOptions: {
    output: {
      manualChunks: {
        'vendor-vue': ['vue', 'vue-router', 'pinia'],
        'vendor-element': ['element-plus'],
        'vendor-echarts': ['echarts']
      }
    }
  }
}
```

#### 步骤 4：本地预览构建结果

```bash
# 预览构建结果
npm run preview

# 访问 http://localhost:4173
```

### 3.3 Nginx 配置

#### 安装 Nginx

**Windows:**

```powershell
# 使用 Chocolatey
choco install nginx

# 下载地址：http://nginx.org/en/download.html
```

**Linux (Ubuntu):**

```bash
sudo apt update
sudo apt install nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### Nginx 配置文件

**完整配置示例 `/etc/nginx/sites-available/housing-rental`：**

```nginx
# 上游服务器配置（后端 API）
upstream housing_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# HTTP 服务器配置
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS 服务器配置
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL 证书配置
    ssl_certificate /etc/ssl/certs/housing-rental.crt;
    ssl_certificate_key /etc/ssl/private/housing-rental.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    # 根目录（前端静态文件）
    root /var/www/housing-rental/dist;
    index index.html;
    
    # 静态文件缓存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # 前端路由 - 所有未匹配的路径都返回 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 反向代理
    location /api/ {
        proxy_pass http://housing_backend;
        proxy_http_version 1.1;
        
        # 代理头设置
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering off;
    }
    
    # 文件上传目录
    location /uploads/ {
        alias /var/www/housing-rental/uploads/;
        expires 30d;
        add_header Cache-Control "public";
        
        # 安全设置 - 禁止执行 PHP 等脚本
        location ~ \.(php|py|jsp|asp|sh|cgi)$ {
            deny all;
        }
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 访问日志
    access_log /var/log/nginx/housing-rental-access.log;
    error_log /var/log/nginx/housing-rental-error.log;
    
    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json image/svg+xml;
    gzip_comp_level 6;
}
```

#### 部署前端文件

```bash
# 创建部署目录
sudo mkdir -p /var/www/housing-rental

# 复制构建产物
sudo cp -r dist/* /var/www/housing-rental/

# 创建上传目录
sudo mkdir -p /var/www/housing-rental/uploads

# 设置权限
sudo chown -R www-data:www-data /var/www/housing-rental
sudo chmod -R 755 /var/www/housing-rental
```

#### 启用站点

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/housing-rental /etc/nginx/sites-enabled/

# 删除默认站点（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx
```

### 3.4 CDN 配置（可选）

#### 使用 Cloudflare CDN

1. **注册 Cloudflare 账户**
   - 访问 https://www.cloudflare.com/

2. **添加站点**
   - 输入域名
   - 更新 DNS 服务器到 Cloudflare

3. **配置缓存规则**
   - Page Rules → Create Page Rule
   - URL: `your-domain.com/static/*`
   - 设置：Cache Level = Cache Everything, Edge Cache TTL = 7 days

#### 使用阿里云 OSS + CDN

**步骤 1：创建 OSS Bucket**

```bash
# 使用 ossutil 工具
ossutil mb oss://your-housing-cdn
```

**步骤 2：上传静态资源**

```bash
# 上传构建产物
ossutil cp -r dist/ oss://your-housing-cdn/static/
```

**步骤 3：配置 CDN 加速**

- 登录阿里云 CDN 控制台
- 添加域名，源站选择 OSS Bucket
- 配置缓存规则

**步骤 4：修改前端配置**

在 `.env.production` 中：

```ini
VITE_CDN_URL=https://cdn.your-domain.com
```

在 `vite.config.js` 中：

```javascript
build: {
  assetsDir: 'static',
  rollupOptions: {
    output: {
      manualChunks: {
        'vendor-vue': ['vue', 'vue-router', 'pinia'],
        'vendor-element': ['element-plus'],
        'vendor-echarts': ['echarts']
      }
    }
  },
  // CDN 配置
  rollupOptions: {
    external: ['vue', 'vue-router', 'pinia', 'element-plus', 'echarts'],
    output: {
      globals: {
        vue: 'Vue',
        'vue-router': 'VueRouter',
        pinia: 'Pinia',
        'element-plus': 'ElementPlus',
        echarts: 'echarts'
      }
    }
  }
}
```

---

## 4. 系统联调与验证

### 4.1 前后端联调测试

#### 启动服务

**终端 1 - 后端服务：**

```bash
# 激活虚拟环境
.\.venv\Scripts\activate

# 启动后端
python run.py
```

**终端 2 - 前端开发服务器：**

```bash
# 启动前端
npm run dev
```

#### 验证服务状态

| 服务 | URL | 预期结果 |
|------|-----|----------|
| 前端 | http://localhost:5173 | 页面正常加载 |
| 后端 API | http://localhost:5000/api/health | 返回健康状态 JSON |
| 登录接口 | http://localhost:5000/api/auth/login | 返回登录表单验证 |

### 4.2 接口连通性测试

#### 使用 cURL 测试

```bash
# 测试健康检查接口
curl http://localhost:5000/api/health

# 测试登录接口
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 测试需要认证的接口（使用返回的 token）
curl http://localhost:5000/api/users \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 使用 Postman 测试

1. **创建集合**：Housing Rental System API
2. **添加环境变量**：
   - `base_url`: http://localhost:5000
   - `access_token`: (登录后自动保存)
3. **测试认证流程**：
   - POST `/api/auth/login`
   - 保存返回的 token 到环境变量
   - 使用 token 访问受保护接口

### 4.3 功能验证清单

#### 用户管理模块

- [ ] 用户注册功能
- [ ] 用户登录/登出
- [ ] JWT Token 刷新
- [ ] 用户信息查看
- [ ] 用户信息修改
- [ ] 密码修改
- [ ] 用户列表查询（管理员）
- [ ] 用户角色管理（管理员）

#### 房屋管理模块

- [ ] 房屋信息录入
- [ ] 房屋信息编辑
- [ ] 房屋信息删除
- [ ] 房屋列表查询
- [ ] 房屋详情查看
- [ ] 房屋图片上传
- [ ] 房屋状态管理（出租/空置）

#### 合同管理模块

- [ ] 合同创建
- [ ] 合同信息编辑
- [ ] 合同续签
- [ ] 合同终止
- [ ] 合同列表查询
- [ ] 合同详情查看
- [ ] 合同到期提醒

#### 财务管理模块

- [ ] 租金支付记录
- [ ] 押金管理
- [ ] 账单生成
- [ ] 账单查询
- [ ] 逾期提醒
- [ ] 财务报表导出（Excel）

#### 系统功能

- [ ] 数据导入（Excel）
- [ ] 数据导出（Excel/PDF）
- [ ] 定时任务执行
- [ ] 日志记录
- [ ] 错误处理
- [ ] 跨域访问

### 4.4 性能基准测试

#### 使用 Apache Bench (ab)

```bash
# 安装 Apache Bench
# Ubuntu: sudo apt install apache2-utils
# Windows: 包含在 Apache 中

# 测试登录接口
ab -n 1000 -c 10 -p login.json -T application/json \
  http://localhost:5000/api/auth/login

# 参数说明
# -n: 总请求数
# -c: 并发数
# -p: 请求体文件
# -T: Content-Type
```

#### 使用 wrk

```bash
# 安装 wrk
# Ubuntu: sudo apt install wrk
# macOS: brew install wrk

# 测试 API
wrk -t12 -c400 -d30s http://localhost:5000/api/houses

# 使用 Lua 脚本进行复杂测试
wrk -t12 -c400 -d30s -s test.lua http://localhost:5000/api/houses
```

#### 性能指标参考

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 响应时间 (P95) | < 200ms | 95% 请求响应时间 |
| 响应时间 (P99) | < 500ms | 99% 请求响应时间 |
| 吞吐量 | > 1000 RPS | 每秒请求数 |
| 错误率 | < 0.1% | 失败请求比例 |
| CPU 使用率 | < 70% | 平均负载 |
| 内存使用 | < 80% | 内存占用 |

#### 前端性能测试

**使用 Lighthouse：**

1. 打开 Chrome DevTools
2. 选择 Lighthouse 面板
3. 生成性能报告

**目标分数：**

- Performance: ≥ 90
- Accessibility: ≥ 90
- Best Practices: ≥ 90
- SEO: ≥ 90

**使用 WebPageTest：**

- 访问 https://www.webpagetest.org/
- 输入 URL 进行测试
- 分析加载时间和瀑布图

---

## 5. 常见问题排查

### 5.1 部署失败处理

#### 问题：后端服务无法启动

**症状：**

```bash
Error: Cannot find module 'app'
或
ModuleNotFoundError: No module named 'flask'
```

**排查步骤：**

1. **检查虚拟环境是否激活**

```bash
# Windows
.\.venv\Scripts\activate

# Linux
source .venv/bin/activate
```

2. **重新安装依赖**

```bash
pip install -r requirements.txt --force-reinstall
```

3. **检查 Python 版本**

```bash
python --version  # 应为 3.8+
```

4. **检查应用入口**

```bash
# 验证 app 模块是否存在
python -c "from app import create_app; print('OK')"
```

#### 问题：前端构建失败

**症状：**

```bash
ERROR: Failed to download Chromium
或
Module not found: Error: Can't resolve 'vue'
```

**排查步骤：**

1. **清理 node_modules**

```bash
# 删除 node_modules 和 package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

2. **检查 Node.js 版本**

```bash
node --version  # 应为 16.x 或更高
```

3. **使用淘宝镜像**

```bash
npm config set registry https://registry.npmmirror.com
```

4. **检查磁盘空间**

```bash
# 确保有足够空间（至少 1GB）
df -h  # Linux/macOS
dir    # Windows
```

### 5.2 数据库连接问题

#### 问题：SQLite 数据库锁定

**症状：**

```python
sqlite3.OperationalError: database is locked
```

**解决方案：**

1. **检查是否有其他进程占用**

```bash
# Linux
lsof housing_rental.db

# Windows 使用 Process Explorer
```

2. **增加超时时间**

在 `DATABASE_URI` 中添加参数：

```ini
DATABASE_URI=sqlite:///housing_rental.db?timeout=30
```

3. **优化数据库连接**

在应用配置中：

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
```

#### 问题：MySQL 连接失败

**症状：**

```python
sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server")
```

**排查步骤：**

1. **检查 MySQL 服务状态**

```bash
# Linux
sudo systemctl status mysql

# Windows
sc query MySQL80
```

2. **验证连接信息**

```bash
# 测试连接
mysql -u housing_user -p -h localhost housing_rental
```

3. **检查防火墙**

```bash
# Linux
sudo ufw status | grep 3306

# Windows
netsh advfirewall firewall show rule name=all | findstr 3306
```

4. **检查用户权限**

```sql
-- 登录 MySQL 检查
mysql -u root -p

-- 查看用户权限
SHOW GRANTS FOR 'housing_user'@'localhost';

-- 如果需要，允许远程连接
CREATE USER 'housing_user'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON housing_rental.* TO 'housing_user'@'%';
FLUSH PRIVILEGES;
```

### 5.3 跨域问题

#### 问题：CORS 错误

**症状：**

```javascript
Access to XMLHttpRequest at 'http://localhost:5000/api/houses' 
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**解决方案：**

1. **检查 Flask-CORS 配置**

确保 `.env` 文件中配置正确：

```ini
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

2. **验证应用工厂中的 CORS 设置**

```python
from flask_cors import CORS

def create_app(config_name):
    # ...
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    # ...
```

3. **开发环境使用代理**

`vite.config.js` 中已配置代理：

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
    secure: false
  }
}
```

4. **生产环境使用 Nginx**

确保 Nginx 配置中包含：

```nginx
location /api/ {
    proxy_pass http://housing_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    
    # CORS 头（如需要）
    add_header Access-Control-Allow-Origin $http_origin;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";
}
```

### 5.4 权限问题

#### 问题：文件上传失败

**症状：**

```python
PermissionError: [Errno 13] Permission denied: '/var/www/housing/uploads'
```

**解决方案：**

1. **检查目录权限**

```bash
# Linux
ls -la /var/www/housing/uploads

# 设置正确权限
sudo chown -R www-data:www-data /var/www/housing/uploads
sudo chmod -R 755 /var/www/housing/uploads
```

2. **Windows 权限设置**

```powershell
# 使用 icacls 设置权限
icacls "d:\Pro\Housing_ental_system\uploads" /grant IIS_IUSRS:(OI)(CI)M
```

3. **检查 SELinux（CentOS/RHEL）**

```bash
# 查看 SELinux 状态
getenforce

# 临时禁用（测试用）
sudo setenforce 0

# 或设置正确的上下文
sudo chcon -R -t httpd_sys_rw_content_t /var/www/housing/uploads
```

#### 问题：日志文件无法写入

**症状：**

```python
PermissionError: [Errno 13] Permission denied: '/var/log/housing/app.log'
```

**解决方案：**

```bash
# 创建日志目录
sudo mkdir -p /var/log/housing

# 设置权限
sudo chown -R www-data:www-data /var/log/housing
sudo chmod -R 755 /var/log/housing

# 验证
sudo -u www-data touch /var/log/housing/test.log
```

### 5.5 Nginx 问题

#### 问题：502 Bad Gateway

**症状：**

访问网站显示 502 Bad Gateway

**排查步骤：**

1. **检查后端服务是否运行**

```bash
# Linux
sudo systemctl status housing-rental

# Windows
sc query HousingRental
```

2. **检查 Nginx 配置**

```bash
# 测试配置
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/housing-rental-error.log
```

3. **验证 upstream 配置**

确保 `proxy_pass` 指向正确的后端地址：

```nginx
upstream housing_backend {
    server 127.0.0.1:8000;  # 检查端口是否正确
}
```

#### 问题：404 Not Found（前端路由）

**症状：**

刷新页面时出现 404

**解决方案：**

确保 Nginx 配置中包含：

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### 5.6 性能问题

#### 问题：响应缓慢

**排查步骤：**

1. **检查数据库查询**

```python
# 启用 SQL 日志
SQLALCHEMY_ECHO = True

# 查看慢查询
```

2. **添加数据库索引**

```python
# 在模型中添加索引
class House(db.Model):
    __tablename__ = 'houses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True)  # 添加索引
    status = db.Column(db.String(20), index=True)  # 添加索引
```

3. **启用缓存**

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=300)
def get_houses():
    # ...
```

4. **优化前端构建**

```javascript
// vite.config.js
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        // 代码分割
      }
    }
  }
}
```

### 5.7 紧急故障恢复

#### 数据库备份与恢复

**备份：**

```bash
# SQLite
cp housing_rental.db housing_rental.db.backup.$(date +%Y%m%d)

# MySQL
mysqldump -u housing_user -p housing_rental > backup_$(date +%Y%m%d).sql

# PostgreSQL
pg_dump -U housing_user housing_rental > backup_$(date +%Y%m%d).sql
```

**恢复：**

```bash
# SQLite
cp housing_rental.db.backup.20260228 housing_rental.db

# MySQL
mysql -u housing_user -p housing_rental < backup_20260228.sql

# PostgreSQL
psql -U housing_user housing_rental < backup_20260228.sql
```

#### 服务回滚

```bash
# 停止当前服务
sudo systemctl stop housing-rental

# 恢复代码
git checkout <previous-version>

# 重新部署
pip install -r requirements.txt
npm run build

# 启动服务
sudo systemctl start housing-rental
```

---

## 附录

### A. 配置文件模板

#### .env.production 完整模板

```ini
# Flask Configuration
FLASK_APP=app
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Security
SECRET_KEY=your-super-secret-key-min-32-characters-long
JWT_SECRET_KEY=your-jwt-secret-key-min-32-characters-long
JWT_ACCESS_TOKEN_EXPIRES=86400

# Database Configuration
DATABASE_URI=mysql+pymysql://housing_user:your_secure_password@localhost:3306/housing_rental?charset=utf8mb4

# CORS Configuration
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# File Upload
UPLOAD_FOLDER=/var/www/housing-rental/uploads
MAX_CONTENT_LENGTH=16777216

# Scheduler
SCHEDULER_API_ENABLED=False

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/housing/app.log
LOG_DIR=/var/log/housing

# Waitress (Windows only)
WAITRESS_THREADS=4
WAITRESS_CONNECTION_LIMIT=100
```

#### Nginx 配置快速模板

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;
    
    root /var/www/housing-rental/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /uploads/ {
        alias /var/www/housing-rental/uploads/;
    }
}
```

### B. 快速命令参考

```bash
# 后端命令
python -m venv .venv                    # 创建虚拟环境
.\.venv\Scripts\activate                # 激活虚拟环境 (Windows)
pip install -r requirements.txt         # 安装依赖
python run.py                           # 启动开发服务器
python init_db.py                       # 初始化数据库

# 前端命令
npm install                             # 安装依赖
npm run dev                             # 启动开发服务器
npm run build                           # 构建生产版本
npm run preview                         # 预览构建结果

# 系统命令
sudo systemctl status housing-rental    # 查看服务状态
sudo systemctl restart housing-rental   # 重启服务
sudo journalctl -u housing-rental -f    # 查看日志
sudo nginx -t                           # 测试 Nginx 配置
sudo systemctl reload nginx             # 重新加载 Nginx
```

### C. 联系支持

如遇到文档未涵盖的问题，请检查：

1. 应用日志：`/var/log/housing/` 或 `logs/` 目录
2. Nginx 日志：`/var/log/nginx/`
3. 系统日志：`journalctl -xe` (Linux) 或 事件查看器 (Windows)

---

**文档结束**
