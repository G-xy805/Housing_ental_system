# 房屋租赁系统 (Housing Rental System)

一个基于 Flask + Vue 3 的现代化房屋租赁管理系统，提供完整的房源管理、租赁合同、租金收取、数据统计等功能。系统支持整租和合租两种模式，包含完善的租客管理、合同管理、租金收取与滞纳金计算、数据备份等核心功能。

## 技术栈

### 后端
- **Flask 3.0** - Python Web 框架
- **Flask-SQLAlchemy 3.1** - ORM 数据库操作
- **Flask-CORS 4.0** - 跨域支持
- **PyJWT 2.8** - JWT 认证
- **APScheduler 3.10** - 定时任务调度（自动备份、滞纳金计算）
- **openpyxl 3.1** - Excel 文件处理
- **reportlab 4.0** - PDF 报表生成
- **python-dotenv 1.0** - 环境变量管理

### 前端
- **Vue 3.5** - 渐进式 JavaScript 框架
- **Vite 5.0** - 下一代前端构建工具
- **Element Plus 2.8** - Vue 3 组件库
- **Pinia 2.2** - Vue 3 状态管理
- **Vue Router 4.4** - 路由管理
- **Axios 1.7** - HTTP 客户端
- **ECharts 5.5** - 数据可视化
- **Day.js** - 日期处理
- **Sass** - CSS 预处理器

## 目录结构

```
Housing_ental_system/
├── app/                    # 后端主应用目录
│   ├── models/            # 数据库模型
│   │   ├── __init__.py    # 模型导出
│   │   ├── base.py        # 基础模型类
│   │   ├── user.py        # 用户模型
│   │   ├── house.py       # 房源模型
│   │   ├── room.py        # 房间模型
│   │   ├── tenant.py      # 租客模型
│   │   ├── contract.py    # 合同模型
│   │   ├── payment.py     # 支付模型
│   │   └── media.py       # 多媒体模型
│   ├── routes/            # API 路由
│   │   ├── __init__.py    # 路由导出
│   │   ├── auth.py        # 认证路由
│   │   ├── users.py       # 用户管理路由
│   │   ├── employees.py   # 员工管理路由
│   │   ├── houses.py      # 房源管理路由
│   │   ├── tenants.py     # 租客管理路由
│   │   ├── contracts.py   # 合同管理路由
│   │   ├── payments.py    # 租金管理路由
│   │   ├── statistics.py  # 统计路由
│   │   ├── upload.py      # 文件上传路由
│   │   └── backup.py      # 数据备份路由
│   ├── utils/             # 工具函数
│   │   ├── __init__.py
│   │   ├── decorators.py  # 装饰器（权限验证）
│   │   ├── jwt.py         # JWT 工具
│   │   ├── responses.py   # 统一响应格式
│   │   └── helpers.py     # 辅助函数
│   ├── config.py          # 配置文件
│   └── __init__.py        # 应用初始化
├── src/                   # 前端源代码目录
│   ├── api/               # API 请求封装
│   │   ├── request.js     # 请求封装
│   │   ├── user.js        # 用户 API
│   │   ├── employee.js    # 员工 API
│   │   ├── house.js       # 房源 API
│   │   ├── tenant.js      # 租客 API
│   │   ├── contract.js    # 合同 API
│   │   ├── payment.js     # 支付 API
│   │   ├── statistics.js  # 统计 API
│   │   └── backup.js      # 备份 API
│   ├── components/        # 通用组件
│   │   ├── Layout.vue     # 布局组件
│   │   └── house/         # 房源相关组件
│   ├── views/             # 页面组件
│   │   ├── Dashboard.vue  # 仪表盘
│   │   ├── Login.vue      # 登录页
│   │   ├── houses/        # 房源管理
│   │   ├── tenants/       # 租客管理
│   │   ├── contracts/     # 合同管理
│   │   ├── payments/      # 租金管理
│   │   ├── users/         # 用户管理
│   │   ├── employees/     # 员工管理
│   │   ├── backup/        # 数据备份
│   │   └── profile/       # 个人中心
│   ├── router/            # 路由配置
│   │   └── index.js
│   ├── store/             # Pinia 状态管理
│   │   ├── user.js        # 用户状态
│   │   └── house.js       # 房源状态
│   ├── assets/            # 静态资源
│   │   └── main.scss      # 全局样式
│   ├── styles/            # 样式文件
│   │   ├── global.scss
│   │   └── variables.scss
│   ├── utils/             # 工具函数
│   │   ├── index.js
│   │   └── permission.js  # 权限控制
│   ├── App.vue            # 根组件
│   └── main.js            # 入口文件
├── backups/               # 备份文件存储
├── uploads/               # 上传文件存储
├── logs/                  # 日志文件存储
├── instance/              # Flask 实例目录（数据库文件）
├── .venv/                 # Python 虚拟环境
├── requirements.txt       # Python 依赖
├── package.json           # Node.js 依赖
├── .env                   # 环境变量配置
├── .env.example           # 环境变量示例
└── .gitignore             # Git 忽略文件
```

## 快速开始

### 1. 后端环境配置

#### 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv .venv

# Windows 激活
.venv\Scripts\activate

# macOS/Linux 激活
source .venv/bin/activate
```

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 配置环境变量
```bash
# 复制环境变量示例文件
copy .env.example .env

# 编辑 .env 文件，设置必要的配置
# 主要配置项：
# - SECRET_KEY: 应用密钥
# - DATABASE_URI: 数据库连接 URI（默认 SQLite）
# - JWT_SECRET_KEY: JWT 密钥
# - CORS_ORIGINS: 允许的跨域来源
```

#### 运行后端服务
```bash
# 方式 1：使用 Flask 命令
flask run

# 方式 2：使用 Python 直接运行
python -m flask run

# 方式 3：直接运行应用
python app/__init__.py
```

后端服务默认运行在：**http://localhost:5000**

**提示**：首次运行时会自动创建数据库文件（存储在 `instance/housing_rental.db`）

### 2. 前端环境配置

#### 安装 Node.js 依赖
```bash
npm install
```

#### 运行开发服务器
```bash
npm run dev
```

前端服务默认运行在：**http://localhost:5173**

开发服务器启动后，访问上述地址即可使用系统。

#### 构建生产版本
```bash
# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

构建后的文件将输出到 `dist/` 目录。

#### 代码检查
```bash
# ESLint 代码检查
npm run lint
```

## API 文档

后端服务启动后，可通过以下端点访问 API：

### 基础端点
- **GET** `/api/health` - 健康检查
- **GET** `/api/` - API 概览（包含所有可用端点）

### 认证模块
- **POST** `/api/auth/login` - 用户登录
- **POST** `/api/auth/logout` - 用户登出
- **GET** `/api/auth/me` - 获取当前用户信息

### 用户管理
- **GET** `/api/users` - 获取用户列表
- **POST** `/api/users` - 创建用户
- **GET** `/api/users/:id` - 获取用户详情
- **PUT** `/api/users/:id` - 更新用户
- **DELETE** `/api/users/:id` - 删除用户

### 员工管理
- **GET** `/api/employees` - 获取员工列表
- **POST** `/api/employees` - 创建员工
- **GET** `/api/employees/:id` - 获取员工详情
- **PUT** `/api/employees/:id` - 更新员工
- **DELETE** `/api/employees/:id` - 删除员工

### 房源管理
- **GET** `/api/houses` - 获取房源列表
- **POST** `/api/houses` - 创建房源
- **GET** `/api/houses/:id` - 获取房源详情
- **PUT** `/api/houses/:id` - 更新房源
- **DELETE** `/api/houses/:id` - 删除房源
- **GET** `/api/houses/:id/rooms` - 获取房间列表
- **POST** `/api/houses/:id/rooms` - 创建房间

### 租客管理
- **GET** `/api/tenants` - 获取租客列表
- **POST** `/api/tenants` - 创建租客
- **GET** `/api/tenants/:id` - 获取租客详情
- **PUT** `/api/tenants/:id` - 更新租客
- **DELETE** `/api/tenants/:id` - 删除租客

### 合同管理
- **GET** `/api/contracts` - 获取合同列表
- **POST** `/api/contracts` - 创建合同
- **GET** `/api/contracts/:id` - 获取合同详情
- **PUT** `/api/contracts/:id` - 更新合同
- **DELETE** `/api/contracts/:id` - 删除合同

### 租金管理
- **GET** `/api/payments` - 获取支付记录列表
- **POST** `/api/payments` - 创建支付记录
- **GET** `/api/payments/:id` - 获取支付记录详情
- **PUT** `/api/payments/:id` - 更新支付记录
- **DELETE** `/api/payments/:id` - 删除支付记录

### 统计管理
- **GET** `/api/statistics/overview` - 获取概览统计
- **GET** `/api/statistics/houses` - 房源统计
- **GET** `/api/statistics/payments` - 支付统计
- **GET** `/api/statistics/tenants` - 租客统计

### 文件上传
- **POST** `/api/upload` - 上传文件

### 数据备份
- **GET** `/api/backup` - 获取备份列表
- **POST** `/api/backup` - 创建备份
- **POST** `/api/backup/restore` - 恢复备份
- **DELETE** `/api/backup/:id` - 删除备份

**注意**：所有需要认证的接口需要在请求头中携带 JWT Token：
```
Authorization: Bearer <your_token>
```

## 项目说明

### 核心功能模块

#### 1. 用户与权限管理
- **用户类型**：管理员（admin）、普通员工（staff）
- **角色权限**：基于角色的访问控制（RBAC）
- **JWT 认证**：安全的 Token 认证机制
- **路由守卫**：前端路由权限控制

#### 2. 房源管理
- **整租/合租支持**：灵活的房源类型
- **房间管理**：合租场景下的房间管理
- **多媒体上传**：支持图片、视频上传
- **房源状态**：待租、已租、维护中等状态

#### 3. 租客管理
- **租客信息**：完整的租客档案管理
- **租客状态**：入住、退租等状态管理
- **关联合同**：租客与合同的关联

#### 4. 合同管理
- **合同创建**：支持整租/合租合同
- **合同状态**：待生效、生效中、已到期、已终止
- **合同期限**：租期、押金、租金设置
- **合同导出**：支持合同 PDF 导出

#### 5. 租金管理
- **支付记录**：完整的租金支付记录
- **滞纳金计算**：自动计算逾期滞纳金
- **支付状态**：待支付、已支付、逾期等
- **租金提醒**：到期提醒功能

#### 6. 数据统计
- **仪表盘**：可视化数据展示
- **房源统计**：房源数量、状态分布
- **收入统计**：租金收入趋势分析
- **租客统计**：租客数量、入住率

#### 7. 数据备份
- **自动备份**：定时自动备份数据库
- **手动备份**：随时创建数据备份
- **备份恢复**：支持从备份文件恢复
- **备份管理**：备份文件列表与删除

#### 8. 员工管理
- **员工信息**：员工档案管理
- **权限分配**：员工角色与权限设置
- **状态管理**：员工在职/离职状态

### 数据库模型

系统包含以下核心数据模型：

- **User** - 用户模型（管理员、普通员工）
- **House** - 房源模型（支持整租/合租）
- **Room** - 房间模型（合租场景下的房间）
- **Tenant** - 租客模型
- **Contract** - 合同模型（支持合租合同）
- **Payment** - 支付记录模型（支持滞纳金计算）
- **Media** - 多媒体文件模型

### 文件说明
- `requirements.txt` - Python 依赖列表
- `package.json` - Node.js 依赖列表
- `.gitignore` - Git 忽略文件配置
- `.env.example` - 环境变量示例
- `.env` - 本地环境变量配置（需自行创建）
- `README.md` - 项目说明文档

## 开发规范

### Python 代码规范
- 遵循 PEP 8 编码规范
- 使用 type hints 进行类型注解
- 编写清晰的文档字符串
- 使用 Black 进行代码格式化（可选）
- 使用 Flask 应用工厂模式

### Vue 代码规范
- 使用 Composition API（`<script setup>`）
- 组件命名采用 PascalCase
- 使用 ESLint 进行代码检查
- 使用 Sass 进行样式开发
- 遵循 Vue 3 最佳实践

### 环境变量配置

#### 必要的环境变量
```bash
# Flask 配置
FLASK_APP=app
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# 安全配置
SECRET_KEY=your-secret-key-change-in-production

# 数据库配置
DATABASE_URI=sqlite:///housing_rental.db

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=86400

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 文件上传配置
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# 调度器配置
SCHEDULER_API_ENABLED=True
```

### 数据库配置

#### SQLite（默认）
```bash
DATABASE_URI=sqlite:///housing_rental.db
```

#### MySQL（可选）
```bash
# 1. 安装 MySQL 驱动
pip install pymysql

# 2. 配置数据库连接
DATABASE_URI=mysql+pymysql://username:password@localhost:3306/housing_rental
```

#### PostgreSQL（可选）
```bash
# 1. 安装 PostgreSQL 驱动
pip install psycopg2-binary

# 2. 配置数据库连接
DATABASE_URI=postgresql://username:password@localhost:5432/housing_rental
```

### 生产部署

#### 使用 Gunicorn（可选）
```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app\(\)
```

#### 前端构建
```bash
# 构建生产版本
npm run build

# 将 dist 目录部署到静态文件服务器
```

## License

MIT License

## 常见问题

### 1. 数据库文件在哪里？
数据库文件默认存储在 `instance/housing_rental.db`。如果使用 SQLite，首次运行时会自动创建。

### 2. 如何重置数据库？
```bash
# 删除数据库文件
rm instance/housing_rental.db

# 或使用 Windows
del instance\housing_rental.db

# 重启应用会自动创建新的数据库
```

### 3. 上传的文件存储在哪里？
上传的文件存储在 `uploads/` 目录，可通过 `http://localhost:5000/uploads/<filename>` 访问。

### 4. 日志文件在哪里？
日志文件存储在 `logs/app.log`，使用轮转日志，单个文件最大 10MB。

### 5. 如何修改默认端口？
修改 `.env` 文件中的 `FLASK_PORT` 环境变量：
```bash
FLASK_PORT=8080
```

### 6. 如何更改前端代理地址？
修改 `vite.config.js` 中的 `server.proxy` 配置。

### 7. 数据备份在哪里？
备份文件存储在 `backups/` 目录，支持手动备份和自动备份。

## 系统截图

### 登录页面
访问 `http://localhost:5173/login` 进入登录页面

### 工作台
登录后可查看数据统计概览、房源状态分布、收入趋势等信息

### 房源管理
支持整租/合租房源的增删改查，可上传房源图片和视频

### 合同管理
完整的合同生命周期管理，支持合同创建、续约、终止等操作

## 联系方式

如有问题或建议，请：
- 提交 Issue
- 查看项目文档
- 联系开发团队

## 致谢

感谢以下开源项目：
- [Flask](https://flask.palletsprojects.com/)
- [Vue 3](https://vuejs.org/)
- [Element Plus](https://element-plus.org/)
- [ECharts](https://echarts.apache.org/)
- [Pinia](https://pinia.vuejs.org/)

---

**注意**：本项目仅供学习参考，生产环境使用请根据实际情况进行调整和完善。
