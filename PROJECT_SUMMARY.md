# 房屋租赁系统项目总结

## 项目概述

**房屋租赁系统 (Housing Rental System)** 是一个基于 Flask + Vue 3 的现代化房屋租赁管理平台，系统支持整租和合租两种业务模式，提供完整的房源管理、租赁合同、租金收取、数据备份等功能。

---

## 技术架构

### 后端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Flask | 3.0 | Python Web 框架 |
| Flask-SQLAlchemy | 3.1 | ORM 数据库操作 |
| Flask-CORS | 4.0 | 跨域支持 |
| PyJWT | 2.8 | JWT 认证 |
| APScheduler | 3.10 | 定时任务调度 |
| Redis | 5.0 | 缓存服务 |
| MySQL/PostgreSQL/SQLite | - | 多数据库支持 |
| AES-256-GCM | - | 数据加密 |
| Prometheus | - | 监控指标 |

### 前端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue 3 | 3.5 | 渐进式 JavaScript 框架 |
| Vite | 5.0 | 前端构建工具 |
| Element Plus | 2.8 | UI 组件库 |
| Pinia | 2.2 | 状态管理 |
| Vue Router | 4.4 | 路由管理 |
| Axios | 1.7 | HTTP 客户端 |
| ECharts | 5.5 | 数据可视化 |

### DevOps 工具

- **Docker & Docker Compose** - 容器化部署
- **Nginx** - 反向代理
- **Gunicorn/Waitress** - WSGI 生产服务器
- **PyInstaller** - 桌面应用打包

---

## 项目结构

```
Housing_ental_system/
├── app/                          # Flask 后端应用
│   ├── models/                   # 数据库模型 (15+ 模型)
│   ├── routes/                   # API 路由 (20+ 路由模块)
│   ├── schemas/                   # 数据序列化 schema
│   ├── utils/                    # 工具函数 (30+ 工具模块)
│   ├── migrations/               # 数据库迁移脚本
│   └── config.py                # 配置文件
├── src/                          # Vue 3 前端源码
│   ├── api/                      # API 请求封装
│   ├── components/               # Vue 组件
│   ├── views/                    # 页面视图
│   ├── store/                    # Pinia 状态管理
│   ├── router/                   # 路由配置
│   ├── utils/                    # 工具函数
│   └── __tests__/                # 单元测试
├── docker/                      # Docker 配置
├── deploy/                      # 部署配置 (Nginx, Systemd)
├── coverage/                     # 测试覆盖率报告
└── backups/                     # 数据备份目录
```

---

## 核心功能模块

### 1. 用户与权限管理
- 用户类型：管理员 (admin)、普通员工 (staff)
- 基于角色的访问控制 (RBAC)
- JWT Token 认证机制
- 路由守卫与权限控制
- 密码策略：复杂度要求、过期机制、历史记录

### 2. 房东管理
- 房东档案管理（身份证、联系方式、银行卡）
- 房产证信息管理
- 状态管理：正常、停用、黑名单
- 房源关联与统计

### 3. 承包合同管理
- 平台与房东的合作合同
- 支持多房源承包
- 服务费自动计算
- 合同状态流转：草稿 → 生效中 → 已过期/已终止
- 到期自动提醒

### 4. 房源管理
- 整租/合租模式支持
- 房间管理（合租场景）
- 多媒体上传（图片、视频）
- 房源状态：待租、已租、维护中
- 内外接口分离（数据脱敏）

### 5. 租客管理
- 租客档案管理
- 信用评分体系
- 状态管理：入住、退租
- 合同关联

### 6. 合同管理
- 整租/合租合同
- 合同状态：待生效、生效中、已到期、已终止
- 合同 PDF 导出
- 续约、终止操作

### 7. 租金管理
- 支付记录管理
- 滞纳金自动计算
- 支付状态跟踪
- 到期提醒

### 8. 数据备份
- 自动备份（定时任务）
- 手动备份
- 备份加密与压缩
- 备份恢复功能
- 备份保留策略（默认30天）

### 9. 数据统计
- 仪表盘可视化
- 房源/收入/租客统计
- 房东/承包合同统计
- ECharts 图表展示

### 10. 监控与可观测性
- Prometheus 指标采集
- 健康检查接口
- 慢查询监控
- 性能监控
- 备份监控
- 告警机制（邮件、Webhook）

---

## 数据库模型

| 模型 | 说明 |
|------|------|
| User | 系统用户（管理员/员工） |
| Landlord | 房东信息 |
| House | 房源（整租） |
| Room | 房间（合租） |
| Tenant | 租客 |
| Contract | 租赁合同 |
| LandlordContract | 承包合同 |
| Payment | 支付记录 |
| Media | 多媒体文件 |
| BackupRecord | 备份记录 |
| PasswordHistory | 密码历史 |
| SensitiveDataAudit | 敏感数据审计 |
| EncryptionAudit | 加密审计 |

---

## 安全特性

1. **数据加密**：AES-256-GCM 敏感数据加密
2. **密钥轮换**：90天自动密钥轮换
3. **密码策略**：复杂度、过期、历史记录
4. **审计日志**：操作审计、加密审计、敏感数据审计
5. **SQL 注入防护**：参数化查询
6. **CORS 配置**：跨域访问控制
7. **Session 安全**：HttpOnly、Secure Cookie

---

## 部署方式

### 开发环境
```bash
# 后端
python -m flask run

# 前端
npm run dev
```

### Docker 部署
```bash
docker-compose up -d
```

### 生产环境
- Gunicorn + Nginx
- MySQL/PostgreSQL 数据库
- Redis 缓存
- systemd 服务管理

---

## 测试覆盖

### 后端测试
- pytest 框架
- 覆盖率报告
- 标记：unit, integration, api, auth, encryption

### 前端测试
- Vitest 测试框架
- Vue Test Utils
- 组件与视图测试
- Happy-DOM 单元测试

---

## 环境变量配置

系统通过 `.env` 文件配置，支持：
- 数据库连接（SQLite/MySQL/PostgreSQL）
- Redis 缓存
- JWT 密钥
- 文件上传限制
- 备份策略
- 监控阈值
- 告警配置

---

## 项目亮点

1. **完善的角色权限体系**：清晰的用户、员工、房东、租客角色分离
2. **灵活的业务模式**：支持整租、合租、承包合同等多种模式
3. **全面的监控体系**：Prometheus + 健康检查 + 慢查询监控
4. **数据安全**：AES-256-GCM 加密、密钥轮换、审计日志
5. **高可用部署**：Docker 容器化、自动备份、监控告警
6. **开发友好**：完整的 API 文档、测试覆盖、规范的开发指南

---

## 依赖版本

### Python 核心依赖
- Flask==3.0.0
- Flask-SQLAlchemy==3.1.1
- PyJWT==2.8.0
- APScheduler==3.10.4
- redis==5.0.1
- cryptography==41.0.7

### Node.js 核心依赖
- vue==3.5.0
- element-plus==2.8.0
- pinia==2.2.0
- vue-router==4.4.0
- axios==1.7.0
- echarts==5.5.0

---

**项目版本**: v2.0
**最后更新**: 2026-03-24
