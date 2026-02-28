# 文档移交流程

本文档定义了房屋租赁管理系统交付给客户时需要提供的完整文档清单、格式规范和移交流程。

---

## 目录

1. [技术文档清单](#1-技术文档清单)
2. [用户文档清单](#2-用户文档清单)
3. [运维文档清单](#3-运维文档清单)
4. [文档格式规范](#4-文档格式规范)
5. [文档移交流程](#5-文档移交流程)
6. [附录：文档模板示例](#6-附录文档模板示例)

---

## 1. 技术文档清单

技术文档面向开发团队和技术人员，用于系统维护、扩展和二次开发。

### 1.1 系统架构文档

**文档名称**：`system-architecture.md`

**内容要求**：

#### 1.1.1 系统概述
- 系统定位与目标
- 核心功能模块
- 用户角色定义
- 业务流程概述

#### 1.1.2 技术栈说明
| 层级 | 技术选型 | 版本号 | 说明 |
|------|----------|--------|------|
| 前端框架 | React/Vue | x.x.x | UI 框架 |
| 后端框架 | Flask | x.x.x | Web 框架 |
| 数据库 | MySQL/PostgreSQL | x.x.x | 数据存储 |
| 缓存 | Redis | x.x.x | 缓存服务 |
| 消息队列 | RabbitMQ | x.x.x | 异步处理 |
| 容器化 | Docker | x.x.x | 容器部署 |

#### 1.1.3 系统架构图
```
┌─────────────────────────────────────────────────────────┐
│                      负载均衡层                          │
│                    (Nginx / SLB)                        │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   应用节点 1   │   │   应用节点 2   │   │   应用节点 N   │
│   (Flask)     │   │   (Flask)     │   │   (Flask)     │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    MySQL      │   │    Redis      │   │  文件存储     │
│   主从集群     │   │    缓存       │   │   (OSS)       │
└───────────────┘   └───────────────┘   └───────────────┘
```

#### 1.1.4 部署架构
- 开发环境配置
- 测试环境配置
- 生产环境配置
- 灾备方案

**交付位置**：`.trae/docs/technical/system-architecture.md`

---

### 1.2 数据库设计文档

**文档名称**：`database-design.md`

**内容要求**：

#### 1.2.1 数据库概述
- 数据库类型及版本
- 字符集配置（推荐：utf8mb4）
- 存储引擎（推荐：InnoDB）
- 命名规范

#### 1.2.2 ER 图
```mermaid
erDiagram
    USER ||--o{ TENANT : manages
    USER ||--o{ PROPERTY : manages
    PROPERTY ||--o{ TENANT : has
    PROPERTY ||--o{ CONTRACT : has
    TENANT ||--o{ PAYMENT : makes
```

#### 1.2.3 数据表清单

| 序号 | 表名 | 中文名 | 说明 |
|------|------|--------|------|
| 1 | users | 用户表 | 系统用户信息 |
| 2 | properties | 房源表 | 房屋基本信息 |
| 3 | tenants | 租客表 | 租客信息 |
| 4 | contracts | 合同表 | 租赁合同信息 |
| 5 | payments | 收款表 | 租金收款记录 |
| 6 | rooms | 房间表 | 房屋房间信息 |
| 7 | bills | 账单表 | 水电费账单 |

#### 1.2.4 表结构详细说明

**示例：users 用户表**

| 字段名 | 数据类型 | 长度 | 允许 NULL | 默认值 | 说明 |
|--------|----------|------|-----------|--------|------|
| id | INT | - | NO | AUTO_INCREMENT | 主键 ID |
| username | VARCHAR | 50 | NO | - | 用户名（唯一） |
| password_hash | VARCHAR | 255 | NO | - | 密码哈希 |
| email | VARCHAR | 100 | YES | NULL | 邮箱 |
| phone | VARCHAR | 20 | YES | NULL | 手机号 |
| role | ENUM | - | NO | 'user' | 角色：admin/user/landlord |
| status | TINYINT | 1 | NO | 1 | 状态：1 启用 0 禁用 |
| created_at | DATETIME | - | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | - | NO | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引信息**：
```sql
PRIMARY KEY (id)
UNIQUE KEY uk_username (username)
KEY idx_email (email)
KEY idx_phone (phone)
KEY idx_status (status)
```

**交付位置**：`.trae/docs/technical/database-design.md`

---

### 1.3 API 接口文档

**文档名称**：`api-reference.md`

**内容要求**：

#### 1.3.1 接口规范
- 基础 URL
- 认证方式（JWT Token）
- 请求格式（JSON）
- 响应格式
- 错误码规范

#### 1.3.2 接口分类

**用户管理模块**
| 接口路径 | 方法 | 说明 | 权限 |
|----------|------|------|------|
| /api/v1/users | GET | 获取用户列表 | admin |
| /api/v1/users/{id} | GET | 获取用户详情 | admin/self |
| /api/v1/users | POST | 创建用户 | admin |
| /api/v1/users/{id} | PUT | 更新用户 | admin/self |
| /api/v1/users/{id} | DELETE | 删除用户 | admin |

**房源管理模块**
| 接口路径 | 方法 | 说明 | 权限 |
|----------|------|------|------|
| /api/v1/properties | GET | 获取房源列表 | all |
| /api/v1/properties/{id} | GET | 获取房源详情 | all |
| /api/v1/properties | POST | 创建房源 | landlord |
| /api/v1/properties/{id} | PUT | 更新房源 | owner |
| /api/v1/properties/{id} | DELETE | 删除房源 | owner/admin |

#### 1.3.3 接口详细示例

**获取用户列表**
```http
GET /api/v1/users?page=1&size=20&role=user
Authorization: Bearer <token>
```

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "username": "zhangsan",
        "email": "zhangsan@example.com",
        "phone": "13800138000",
        "role": "user",
        "status": 1,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "size": 20
  }
}
```

**错误响应示例**：
```json
{
  "code": 401,
  "message": "未授权访问",
  "error": "INVALID_TOKEN"
}
```

#### 1.3.4 错误码表

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| 200 | 200 | 成功 |
| 400 | 400 | 请求参数错误 |
| 401 | 401 | 未授权 |
| 403 | 403 | 禁止访问 |
| 404 | 404 | 资源不存在 |
| 500 | 500 | 服务器内部错误 |

**交付位置**：`.trae/docs/technical/api-reference.md`

---

### 1.4 代码结构说明

**文档名称**：`code-structure.md`

**内容要求**：

#### 1.4.1 项目目录结构
```
Housing_ental_system/
├── .trae/                          # Trae IDE 配置
│   └── specs/                      # 规格说明书
├── .venv/                          # Python 虚拟环境
├── app/                            # 应用主目录
│   ├── __init__.py                 # 应用工厂
│   ├── models/                     # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py                 # 用户模型
│   │   ├── property.py             # 房源模型
│   │   └── tenant.py               # 租客模型
│   ├── routes/                     # 路由定义
│   │   ├── __init__.py
│   │   ├── auth.py                 # 认证路由
│   │   ├── users.py                # 用户路由
│   │   └── properties.py           # 房源路由
│   ├── services/                   # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── property_service.py
│   ├── utils/                      # 工具函数
│   │   ├── __init__.py
│   │   ├── validators.py           # 数据验证
│   │   └── helpers.py              # 辅助函数
│   └── templates/                  # HTML 模板
├── migrations/                     # 数据库迁移
├── tests/                          # 测试用例
│   ├── __init__.py
│   ├── test_users.py
│   └── test_properties.py
├── .env                            # 环境变量配置
├── .env.example                    # 环境变量示例
├── requirements.txt                # Python 依赖
└── README.md                       # 项目说明
```

#### 1.4.2 模块说明

| 模块 | 说明 | 主要功能 |
|------|------|----------|
| models | 数据模型层 | 定义数据库模型、关系映射 |
| routes | 路由控制层 | 处理 HTTP 请求、参数验证 |
| services | 业务逻辑层 | 核心业务逻辑实现 |
| utils | 工具模块 | 通用工具函数、数据验证 |

#### 1.4.3 编码规范

**命名规范**：
- 文件名：小写字母 + 下划线（如：`user_service.py`）
- 类名：大驼峰命名（如：`UserService`）
- 函数名：小写字母 + 下划线（如：`get_user_by_id`）
- 常量名：全大写字母 + 下划线（如：`MAX_RETRY_COUNT`）

**代码注释规范**：
```python
def create_user(username, email, password):
    """
    创建新用户
    
    Args:
        username (str): 用户名
        email (str): 邮箱地址
        password (str): 密码（明文）
    
    Returns:
        dict: 创建的用户信息
        
    Raises:
        ValueError: 用户名已存在时
        EmailError: 邮箱格式不正确时
    """
    pass
```

**交付位置**：`.trae/docs/technical/code-structure.md`

---

## 2. 用户文档清单

用户文档面向最终用户，帮助用户快速上手和熟练使用系统。

### 2.1 用户操作手册

**文档名称**：`user-manual.md`

**内容要求**：

#### 2.1.1 分角色操作指南

**管理员角色**
- 系统配置管理
- 用户权限管理
- 数据备份恢复
- 系统监控

**房东角色**
- 房源管理（添加、编辑、删除）
- 租客管理
- 合同管理
- 收款管理

**租客角色**
- 查看房源
- 在线签约
- 账单查询
- 报修申请

#### 2.1.2 功能操作详解

每个功能点包含：
- 功能说明
- 操作步骤（带截图）
- 注意事项
- 常见问题

**示例：发布房源**
```
步骤 1：登录系统后，点击顶部导航栏「房源管理」
步骤 2：点击右上角「发布房源」按钮
步骤 3：填写房源基本信息
  - 房屋地址
  - 房屋面积
  - 房间数量
  - 租金价格
步骤 4：上传房屋照片（最多 10 张）
步骤 5：点击「提交审核」
```

**交付位置**：`docs/user/user-manual.md`

---

### 2.2 快速入门指南

**文档名称**：`quick-start.md`

**内容要求**：

#### 2.2.1 新手引导
- 系统注册流程
- 首次登录配置
- 基础功能介绍
- 快速上手任务

#### 2.2.2 5 分钟快速开始
```
1. 访问系统首页 (http://your-domain.com)
2. 点击右上角「注册」创建账号
3. 验证邮箱/手机
4. 登录系统
5. 完成新手引导
6. 开始使用核心功能
```

#### 2.2.3 视频教程链接
- 系统介绍视频（3 分钟）
- 核心功能演示视频（10 分钟）
- 高级功能视频（15 分钟）

**交付位置**：`docs/user/quick-start.md`

---

### 2.3 常见问题解答

**文档名称**：`faq.md`

**内容要求**：

#### 2.3.1 账号相关
**Q1：忘记密码怎么办？**
A：点击登录页「忘记密码」，通过注册邮箱或手机号重置密码。

**Q2：如何修改登录密码？**
A：登录后进入「个人中心」>「账号安全」>「修改密码」。

#### 2.3.2 房源相关
**Q1：发布房源需要审核吗？**
A：是的，发布的房源需要经过管理员审核后才能展示。

**Q2：房源信息如何修改？**
A：进入「房源管理」> 找到对应房源 > 点击「编辑」进行修改。

#### 2.3.3 合同相关
**Q1：电子合同有法律效力吗？**
A：本系统采用第三方电子签名服务，符合《电子签名法》规定。

**Q2：合同到期如何处理？**
A：系统会自动提醒，可选择续签或退租。

#### 2.3.4 支付相关
**Q1：支持哪些支付方式？**
A：支持微信支付、支付宝、银行转账。

**Q2：支付失败怎么办？**
A：检查网络后重试，如多次失败请联系客服。

**交付位置**：`docs/user/faq.md`

---

### 2.4 最佳实践指南

**文档名称**：`best-practices.md`

**内容要求**：

#### 2.4.1 房东最佳实践
- 如何快速找到优质租客
- 合理定价策略
- 合同条款建议
- 租客沟通技巧

#### 2.4.2 租客最佳实践
- 如何筛选合适房源
- 看房注意事项
- 合同签署要点
- 维权途径

#### 2.4.3 管理员最佳实践
- 审核流程优化
- 纠纷处理流程
- 数据分析方法
- 系统安全建议

**交付位置**：`docs/user/best-practices.md`

---

## 3. 运维文档清单

运维文档面向运维人员，确保系统稳定运行。

### 3.1 系统部署手册

**文档名称**：`deployment-guide.md`

**内容要求**：

#### 3.1.1 环境要求
| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核 |
| 内存 | 4GB | 8GB |
| 磁盘 | 50GB | 100GB SSD |
| 操作系统 | CentOS 7+ / Ubuntu 18.04+ | Ubuntu 20.04 LTS |

#### 3.1.2 依赖软件
- Python 3.9+
- MySQL 8.0+
- Redis 6.0+
- Nginx 1.18+
- Docker 20.10+

#### 3.1.3 部署步骤

**步骤 1：安装系统依赖**
```bash
# Ubuntu 系统
sudo apt update
sudo apt install -y python3.9 python3.9-venv python3-pip
sudo apt install -y mysql-server redis-server nginx
```

**步骤 2：克隆代码**
```bash
git clone <repository-url> /opt/housing-rental
cd /opt/housing-rental
```

**步骤 3：创建虚拟环境**
```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**步骤 4：配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等
```

**步骤 5：初始化数据库**
```bash
flask db upgrade
```

**步骤 6：启动服务**
```bash
# 开发环境
flask run

# 生产环境（使用 Gunicorn）
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

**步骤 7：配置 Nginx**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**交付位置**：`docs/ops/deployment-guide.md`

---

### 3.2 配置管理文档

**文档名称**：`configuration-management.md`

**内容要求**：

#### 3.2.1 配置文件说明

**.env 文件配置项**
```bash
# 应用配置
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# 数据库配置
DATABASE_URL=mysql://user:password@localhost:3306/housing_rental

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=3600

# 邮件配置
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password

# 文件存储配置
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET=housing-rental
OSS_ACCESS_KEY=your-access-key
OSS_SECRET_KEY=your-secret-key
```

#### 3.2.2 环境变量说明

| 变量名 | 说明 | 是否必需 | 默认值 |
|--------|------|----------|--------|
| FLASK_ENV | 运行环境 | 是 | production |
| SECRET_KEY | 应用密钥 | 是 | - |
| DATABASE_URL | 数据库连接串 | 是 | - |
| REDIS_URL | Redis 连接串 | 否 | - |

#### 3.2.3 配置更新流程
1. 备份当前配置
2. 修改配置文件
3. 验证配置正确性
4. 重启应用服务
5. 验证服务正常

**交付位置**：`docs/ops/configuration-management.md`

---

### 3.3 备份恢复手册

**文档名称**：`backup-restore.md`

**内容要求**：

#### 3.3.1 备份策略

| 数据类型 | 备份频率 | 保留周期 | 备份方式 |
|----------|----------|----------|----------|
| 数据库 | 每日全量 + 每小时增量 | 30 天 | mysqldump + binlog |
| 文件存储 | 实时同步 | 90 天 | OSS 版本控制 |
| 配置文件 | 每次变更后 | 永久 | Git 版本控制 |
| 日志文件 | 每日归档 | 180 天 | logrotate |

#### 3.3.2 数据库备份

**全量备份脚本**
```bash
#!/bin/bash
BACKUP_DIR="/backup/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="housing_rental"
DB_USER="backup_user"
DB_PASS="backup_password"

mysqldump -u$DB_USER -p$DB_PASS \
  --single-transaction \
  --routines \
  --triggers \
  $DB_NAME > $BACKUP_DIR/full_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/full_$DATE.sql

# 删除 30 天前的备份
find $BACKUP_DIR -name "full_*.sql.gz" -mtime +30 -delete
```

**定时任务配置**
```bash
# 每天凌晨 2 点执行备份
0 2 * * * /opt/scripts/backup_mysql.sh
```

#### 3.3.3 数据恢复流程

**数据库恢复**
```bash
# 1. 解压备份文件
gunzip full_20240101_020000.sql.gz

# 2. 恢复数据
mysql -u root -p housing_rental < full_20240101_020000.sql

# 3. 验证数据
mysql -u root -p -e "SELECT COUNT(*) FROM housing_rental.users;"
```

**交付位置**：`docs/ops/backup-restore.md`

---

### 3.4 故障排查手册

**文档名称**：`troubleshooting.md`

**内容要求**：

#### 3.4.1 常见问题及解决方案

**问题 1：服务无法启动**
```
排查步骤：
1. 检查应用日志：tail -f /var/log/app/error.log
2. 检查端口占用：netstat -tlnp | grep 8000
3. 检查依赖服务：systemctl status mysql redis
4. 检查环境变量：cat .env
```

**问题 2：数据库连接失败**
```
排查步骤：
1. 检查 MySQL 服务状态：systemctl status mysql
2. 测试数据库连接：mysql -h localhost -u user -p
3. 检查网络连接：telnet localhost 3306
4. 检查数据库配置：grep DATABASE_URL .env
```

**问题 3：Redis 缓存异常**
```
排查步骤：
1. 检查 Redis 服务：systemctl status redis
2. 测试 Redis 连接：redis-cli ping
3. 检查 Redis 内存：redis-cli info memory
4. 清理过期缓存：redis-cli FLUSHDB
```

**问题 4：Nginx 反向代理失败**
```
排查步骤：
1. 检查 Nginx 配置：nginx -t
2. 查看 Nginx 日志：tail -f /var/log/nginx/error.log
3. 检查后端服务：curl http://127.0.0.1:8000/health
4. 重启 Nginx：systemctl restart nginx
```

#### 3.4.2 日志文件位置

| 日志类型 | 文件路径 | 说明 |
|----------|----------|------|
| 应用日志 | /var/log/app/ | Flask 应用日志 |
| Nginx 日志 | /var/log/nginx/ | Web 服务器日志 |
| MySQL 日志 | /var/log/mysql/ | 数据库日志 |
| Redis 日志 | /var/log/redis/ | 缓存服务日志 |

**交付位置**：`docs/ops/troubleshooting.md`

---

### 3.5 监控告警文档

**文档名称**：`monitoring-alerting.md`

**内容要求**：

#### 3.5.1 监控指标

**系统资源监控**
| 指标 | 阈值 | 告警级别 | 说明 |
|------|------|----------|------|
| CPU 使用率 | > 80% | 警告 | 持续 5 分钟 |
| CPU 使用率 | > 95% | 严重 | 持续 5 分钟 |
| 内存使用率 | > 85% | 警告 | 持续 5 分钟 |
| 磁盘使用率 | > 90% | 严重 | - |
| 网络流量 | 异常波动 | 警告 | 环比>50% |

**应用监控**
| 指标 | 阈值 | 告警级别 | 说明 |
|------|------|----------|------|
| HTTP 错误率 | > 1% | 警告 | 5xx 错误 |
| HTTP 错误率 | > 5% | 严重 | 5xx 错误 |
| 响应时间 P95 | > 2s | 警告 | - |
| 响应时间 P99 | > 5s | 严重 | - |
| QPS | 异常波动 | 警告 | 环比>50% |

**数据库监控**
| 指标 | 阈值 | 告警级别 | 说明 |
|------|------|----------|------|
| 连接数 | > 80% | 警告 | 最大连接数 |
| 慢查询 | > 10/min | 警告 | 执行>1s |
| 主从延迟 | > 60s | 严重 | - |

#### 3.5.2 告警配置

**Prometheus 告警规则示例**
```yaml
groups:
  - name: housing_rental_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高 CPU 使用率"
          description: "{{ $labels.instance }} CPU 使用率超过 80%"

      - alert: ServiceDown
        expr: up{job="housing_rental"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务宕机"
          description: "{{ $labels.instance }} 服务不可用"
```

#### 3.5.3 告警通知渠道
- 邮件通知
- 短信通知
- 钉钉/企业微信机器人
- PagerDuty（可选）

**交付位置**：`docs/ops/monitoring-alerting.md`

---

## 4. 文档格式规范

### 4.1 文档命名规范

#### 4.1.1 文件名命名规则
- 使用小写字母
- 单词间使用中划线分隔
- 使用有意义的英文名称
- 避免使用特殊字符和空格

**示例**：
```
✅ system-architecture.md
✅ api-reference.md
✅ user-manual.md
❌ SystemArchitecture.md
❌ api_reference.md
❌ 用户手册.md
```

#### 4.1.2 目录结构
```
docs/
├── technical/              # 技术文档
│   ├── system-architecture.md
│   ├── database-design.md
│   ├── api-reference.md
│   └── code-structure.md
├── user/                   # 用户文档
│   ├── user-manual.md
│   ├── quick-start.md
│   ├── faq.md
│   └── best-practices.md
├── ops/                    # 运维文档
│   ├── deployment-guide.md
│   ├── configuration-management.md
│   ├── backup-restore.md
│   ├── troubleshooting.md
│   └── monitoring-alerting.md
└── templates/              # 文档模板
    ├── technical-template.md
    ├── user-manual-template.md
    └── ops-guide-template.md
```

---

### 4.2 文档版本控制

#### 4.2.1 版本号规范
采用语义化版本号：`主版本号。次版本号。修订号`

| 版本变更 | 说明 | 示例 |
|----------|------|------|
| 主版本号 | 重大变更，不兼容 | 1.0.0 → 2.0.0 |
| 次版本号 | 新增功能，兼容 | 1.2.0 → 1.3.0 |
| 修订号 | Bug 修复，小改动 | 1.2.3 → 1.2.4 |

#### 4.2.2 文档头部信息
每篇文档开头应包含：
```markdown
# 文档标题

| 属性 | 值 |
|------|-----|
| 版本 | 1.0.0 |
| 作者 | 张三 |
| 创建日期 | 2024-01-01 |
| 最后更新 | 2024-01-15 |
| 审核人 | 李四 |
| 状态 | 已发布 |
```

#### 4.2.3 变更历史记录
```markdown
## 变更历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0.0 | 2024-01-01 | 张三 | 初始版本 |
| 1.0.1 | 2024-01-15 | 张三 | 修复错别字 |
| 1.1.0 | 2024-02-01 | 李四 | 新增 API 接口说明 |
```

---

### 4.3 文档模板样式

#### 4.3.1 技术文档模板

```markdown
# {文档标题}

| 属性 | 值 |
|------|-----|
| 版本 | 1.0.0 |
| 作者 | {作者名} |
| 创建日期 | {YYYY-MM-DD} |
| 最后更新 | {YYYY-MM-DD} |
| 审核人 | {审核人名} |
| 状态 | {草稿/评审中/已发布} |

## 1. 概述

{简要描述文档目的和范围}

## 2. {章节标题}

### 2.1 {子章节标题}

{详细内容}

#### 2.1.1 {详细子章节}

{表格、代码块、图表等}

## 3. 总结

{总结内容}

## 附录

### A. 参考资料

- [参考文档 1](链接)
- [参考文档 2](链接)

### B. 术语表

| 术语 | 说明 |
|------|------|
| API | 应用程序接口 |
| JWT | JSON Web Token |
```

#### 4.3.2 用户文档模板

```markdown
# {功能名称} 使用指南

## 功能简介

{功能简介说明}

## 操作步骤

### 步骤 1：{步骤名称}

1. {详细操作说明}
2. {详细操作说明}

![步骤 1 截图](./images/step1.png)

### 步骤 2：{步骤名称}

1. {详细操作说明}
2. {详细操作说明}

![步骤 2 截图](./images/step2.png)

## 注意事项

- ⚠️ {注意项 1}
- ⚠️ {注意项 2}

## 常见问题

**Q：{问题}**

A：{答案}
```

---

### 4.4 文档存储结构

#### 4.4.1 Git 仓库结构
```
Housing_ental_system/
├── .trae/
│   └── specs/              # 需求规格说明
├── docs/                   # 文档根目录
│   ├── README.md           # 文档索引
│   ├── technical/          # 技术文档
│   ├── user/               # 用户文档
│   ├── ops/                # 运维文档
│   └── templates/          # 文档模板
├── src/                    # 源代码
└── README.md               # 项目说明
```

#### 4.4.2 文档发布位置
| 文档类型 | 发布位置 | 访问方式 |
|----------|----------|----------|
| 技术文档 | Git 仓库 | Git 访问 |
| 用户文档 | 系统帮助中心 | Web 访问 |
| 运维文档 | 内部 Wiki | 内网访问 |

---

## 5. 文档移交流程

### 5.1 文档审查流程

#### 5.1.1 审查流程图
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  文档编写   │ →  │  自我审查   │ →  │  同行评审   │ →  │  客户确认   │
│  (作者)     │    │  (作者)     │    │  (技术负责人)│    │  (客户代表) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ↓                  ↓                  ↓                  ↓
   完成初稿          检查完整性          技术准确性          最终验收
```

#### 5.1.2 审查检查清单

**自我审查清单**
- [ ] 文档结构完整
- [ ] 内容准确无误
- [ ] 格式符合规范
- [ ] 图表清晰可读
- [ ] 链接有效
- [ ] 无错别字

**同行评审清单**
- [ ] 技术描述准确
- [ ] 代码示例正确
- [ ] 配置参数验证
- [ ] 操作步骤可复现
- [ ] 安全注意事项完整

**客户确认清单**
- [ ] 业务需求覆盖
- [ ] 操作流程正确
- [ ] 文档易于理解
- [ ] 示例贴合实际
- [ ] 验收标准满足

#### 5.1.3 审查意见处理
```markdown
## 审查意见记录

| 序号 | 审查人 | 意见内容 | 严重程度 | 处理状态 | 处理人 |
|------|--------|----------|----------|----------|--------|
| 1 | 李四 | API 示例代码有误 | 高 | 已修复 | 张三 |
| 2 | 王五 | 缺少部署架构图 | 中 | 处理中 | 张三 |
```

---

### 5.2 文档更新机制

#### 5.2.1 更新触发条件
- 系统功能变更
- Bug 修复
- 配置参数调整
- 客户反馈问题
- 定期审查发现

#### 5.2.2 更新流程
```
1. 接收更新请求（Issue/邮件/反馈）
2. 评估更新影响范围
3. 分配更新任务
4. 执行文档更新
5. 审查更新内容
6. 发布新版本
7. 通知相关人员
```

#### 5.2.3 版本兼容性
- 保持向后兼容
- 标注废弃内容
- 提供迁移指南
- 保留历史版本

#### 5.2.4 定期审查计划
| 文档类型 | 审查频率 | 负责人 |
|----------|----------|--------|
| 技术文档 | 每季度 | 技术负责人 |
| 用户文档 | 每月 | 产品经理 |
| 运维文档 | 每季度 | 运维负责人 |

---

### 5.3 文档交付方式

#### 5.3.1 交付物清单

**电子文档**
- [ ] 所有 Markdown 源文件
- [ ] PDF 导出文件
- [ ] 图片资源文件
- [ ] 文档索引文件

**在线文档**
- [ ] 帮助中心网站
- [ ] API 文档网站（Swagger/Redoc）
- [ ] 代码注释文档（Sphinx/JSDoc）

#### 5.3.2 交付介质
- Git 仓库（推荐）
- ZIP 压缩包
- 在线文档站点
- Wiki 系统

#### 5.3.3 交付清单模板
```markdown
# 文档交付清单

## 交付信息
- 项目名称：房屋租赁管理系统
- 交付版本：v1.0.0
- 交付日期：2024-01-15
- 交付人：张三

## 技术文档
- [ ] system-architecture.md
- [ ] database-design.md
- [ ] api-reference.md
- [ ] code-structure.md

## 用户文档
- [ ] user-manual.md
- [ ] quick-start.md
- [ ] faq.md
- [ ] best-practices.md

## 运维文档
- [ ] deployment-guide.md
- [ ] configuration-management.md
- [ ] backup-restore.md
- [ ] troubleshooting.md
- [ ] monitoring-alerting.md

## 交付确认
- 交付人签字：__________ 日期：__________
- 接收人签字：__________ 日期：__________
```

---

### 5.4 文档验收标准

#### 5.4.1 完整性检查
- [ ] 文档清单中所有文档已提供
- [ ] 每个文档章节完整
- [ ] 所有图表已包含
- [ ] 所有链接有效
- [ ] 附录资料完整

#### 5.4.2 准确性检查
- [ ] 技术描述准确无误
- [ ] 代码示例可运行
- [ ] 配置参数正确
- [ ] 操作步骤可复现
- [ ] 数据真实有效

#### 5.4.3 规范性检查
- [ ] 文档格式统一
- [ ] 命名符合规范
- [ ] 版本标识清晰
- [ ] 变更记录完整
- [ ] 目录结构正确

#### 5.4.4 可用性检查
- [ ] 内容易于理解
- [ ] 操作步骤清晰
- [ ] 示例贴合实际
- [ ] 检索方便快捷
- [ ] 阅读体验良好

#### 5.4.5 验收报告模板
```markdown
# 文档验收报告

## 项目信息
- 项目名称：{项目名称}
- 验收日期：{YYYY-MM-DD}
- 验收人：{姓名}

## 验收结果

### 完整性评分：{X/10}
{评价说明}

### 准确性评分：{X/10}
{评价说明}

### 规范性评分：{X/10}
{评价说明}

### 可用性评分：{X/10}
{评价说明}

## 总体评价
{总体评价说明}

## 改进建议
1. {建议 1}
2. {建议 2}

## 验收结论
- [ ] 通过
- [ ] 有条件通过（需完成改进项）
- [ ] 不通过（需重新提交）

验收人签字：__________ 日期：__________
```

---

## 6. 附录：文档模板示例

### 6.1 系统架构文档模板

详见：[system-architecture-template.md](./templates/system-architecture-template.md)

### 6.2 数据库设计文档模板

详见：[database-design-template.md](./templates/database-design-template.md)

### 6.3 API 接口文档模板

详见：[api-reference-template.md](./templates/api-reference-template.md)

### 6.4 用户操作手册模板

详见：[user-manual-template.md](./templates/user-manual-template.md)

### 6.5 部署指南模板

详见：[deployment-guide-template.md](./templates/deployment-guide-template.md)

---

## 7. 相关文档

- [项目规格说明](../spec.md)
- [部署指南](deployment-guide.md)
- [培训计划](training-plan.md)
- [交付检查清单](delivery-checklist.md)

---

## 文档修订记录

| 版本 | 日期 | 作者 | 修订说明 |
|------|------|------|----------|
| 1.0.0 | 2024-01-15 | 系统管理员 | 初始版本 |
| 1.0.1 | 2024-01-20 | 系统管理员 | 完善文档清单和模板示例 |

---

**文档状态**：已发布  
**最后更新**：2024-01-20  
**维护人**：系统管理员
