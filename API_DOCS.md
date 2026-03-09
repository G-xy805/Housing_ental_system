# 房屋租赁系统前端 API 接口文档

## 目录

- [1. 概述](#1-概述)
- [2. 认证说明](#2-认证说明)
- [3. 通用说明](#3-通用说明)
- [4. API 模块](#4-api-模块)
  - [4.1 认证模块 (Auth)](#41-认证模块-auth)
  - [4.2 用户管理模块 (Users)](#42-用户管理模块-users)
  - [4.3 房源管理模块 (Houses)](#43-房源管理模块-houses)
  - [4.4 租客管理模块 (Tenants)](#44-租客管理模块-tenants)
  - [4.5 房东管理模块 (Landlords)](#45-房东管理模块-landlords)
  - [4.6 租赁合同模块 (Contracts)](#46-租赁合同模块-contracts)
  - [4.7 支付管理模块 (Payments)](#47-支付管理模块-payments)
  - [4.8 承包合同模块 (Landlord Contracts)](#48-承包合同模块-landlord-contracts)
  - [4.9 统计分析模块 (Statistics)](#49-统计分析模块-statistics)
  - [4.10 数据备份模块 (Backup)](#410-数据备份模块-backup)
  - [4.11 员工管理模块 (Employees)](#411-员工管理模块-employees)
  - [4.12 文件上传模块 (Upload)](#412-文件上传模块-upload)
  - [4.13 公开房源模块 (Public Houses)](#413-公开房源模块-public-houses)
  - [4.14 审计日志模块 (Audit)](#414-审计日志模块-audit)
  - [4.15 系统监控模块 (Monitoring)](#415-系统监控模块-monitoring)
  - [4.16 启动任务模块 (Startup Tasks)](#416-启动任务模块-startup-tasks)
  - [4.17 押金退款模块 (Deposit Refunds)](#417-押金退款模块-deposit-refunds)
  - [4.18 通知管理模块 (Notifications)](#418-通知管理模块-notifications)
- [5. 数据模型参考](#5-数据模型参考)
- [6. 错误码说明](#6-错误码说明)

---

## 1. 概述

本文档描述房屋租赁系统的前端 API 接口规范，供前端开发人员参考使用。

**基础信息：**
- 基础 URL：`/api`
- 数据格式：JSON
- 字符编码：UTF-8
- 认证方式：JWT Token

---

## 2. 认证说明

### 2.1 Token 获取

通过登录接口获取 JWT Token：

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

**响应示例：**
```json
{
  "message": "登录成功",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "name": "管理员",
    "role": "admin"
  }
}
```

### 2.2 Token 使用

在需要认证的接口请求头中添加 Token：

```http
Authorization: Bearer <token>
```

### 2.3 Token 刷新

Token 有效期过期前，使用刷新接口获取新 Token：

```http
POST /api/auth/refresh
Authorization: Bearer <token>
```

---

## 3. 通用说明

### 3.1 请求格式

**查询参数（GET 请求）：**
```http
GET /api/houses?page=1&per_page=10&status=available&city=北京市
```

**请求体（POST/PUT 请求）：**
```http
POST /api/houses
Content-Type: application/json

{
  "title": "精装修两居室",
  "city": "北京市",
  "district": "海淀区",
  "rent_price": 5000
}
```

### 3.2 响应格式

**成功响应：**
```json
{
  "message": "操作成功",
  "data": { ... }
}
```

**列表响应（带分页）：**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 10,
  "pages": 10
}
```

**错误响应：**
```json
{
  "error": "错误类型",
  "message": "错误详情"
}
```

### 3.3 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无返回内容） |
| 400 | 请求参数错误 |
| 401 | 未认证/Token 无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 3.4 分页参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 当前页码 |
| per_page | int | 10 | 每页数量 |

### 3.5 权限说明

| 角色 | 权限 |
|------|------|
| admin | 所有权限（查看、创建、编辑、删除） |
| staff | 基础权限（查看、创建、编辑），无删除权限 |

---

## 4. API 模块

### 4.1 认证模块 (Auth)

**URL 前缀：** `/api/auth`

#### 4.1.1 用户注册

```http
POST /api/auth/register
```

**请求体：**
```json
{
  "username": "staff001",
  "password": "password123",
  "name": "张三",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "role": "staff"
}
```

**响应：**
```json
{
  "message": "注册成功",
  "user": {
    "id": 2,
    "username": "staff001",
    "name": "张三",
    "role": "staff"
  }
}
```

#### 4.1.2 用户登录

```http
POST /api/auth/login
```

**请求体：**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**响应：**
```json
{
  "message": "登录成功",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "name": "管理员",
    "role": "admin"
  }
}
```

#### 4.1.3 用户登出

```http
POST /api/auth/logout
Authorization: Bearer <token>
```

**响应：**
```json
{
  "message": "登出成功"
}
```

#### 4.1.4 获取当前用户信息

```http
GET /api/auth/me
Authorization: Bearer <token>
```

**响应：**
```json
{
  "id": 1,
  "username": "admin",
  "name": "管理员",
  "email": "admin@example.com",
  "phone": "13800138000",
  "role": "admin",
  "avatar": "/uploads/avatars/admin.jpg"
}
```

#### 4.1.5 更新当前用户信息

```http
PUT /api/auth/me
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "name": "新名称",
  "phone": "13900139000",
  "email": "newemail@example.com"
}
```

#### 4.1.6 刷新 Token

```http
POST /api/auth/refresh
Authorization: Bearer <token>
```

**响应：**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

#### 4.1.7 修改密码

```http
POST /api/auth/change-password
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

#### 4.1.8 验证 Token

```http
POST /api/auth/verify-token
Authorization: Bearer <token>
```

**响应：**
```json
{
  "valid": true,
  "user_id": 1,
  "expires_at": "2024-01-01T12:00:00Z"
}
```

#### 4.1.9 检查密码强度

```http
POST /api/auth/password/strength
```

**请求体：**
```json
{
  "password": "MyP@ssw0rd123"
}
```

**响应：**
```json
{
  "score": 4,
  "level": "strong",
  "suggestions": []
}
```

#### 4.1.10 获取密码过期信息

```http
GET /api/auth/password/expiry
Authorization: Bearer <token>
```

#### 4.1.11 请求密码重置

```http
POST /api/auth/password/reset-request
```

**请求体：**
```json
{
  "email": "user@example.com"
}
```

#### 4.1.12 重置密码

```http
POST /api/auth/password/reset
```

**请求体：**
```json
{
  "token": "reset-token-from-email",
  "new_password": "newpassword123"
}
```

#### 4.1.13 获取密码建议

```http
GET /api/auth/password/suggestions
```

#### 4.1.14 锁定用户账户（管理员）

```http
POST /api/auth/users/<id>/lock
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "reason": "账户异常活动"
}
```

**响应：**
```json
{
  "message": "账户已锁定",
  "user_id": 1
}
```

#### 4.1.15 解锁用户账户（管理员）

```http
POST /api/auth/users/<id>/unlock
Authorization: Bearer <token>
```

**响应：**
```json
{
  "message": "账户已解锁",
  "user_id": 1
}
```

---

### 4.2 用户管理模块 (Users)

**URL 前缀：** `/api/users`

**权限要求：** 需要登录，部分操作需要管理员权限

#### 4.2.1 获取用户列表

```http
GET /api/users
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页数量 |
| role | string | 角色筛选（admin/staff） |
| status | string | 状态筛选（active/resigned/disabled） |
| search | string | 搜索关键词 |

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "username": "admin",
      "name": "管理员",
      "email": "admin@example.com",
      "phone": "13800138000",
      "role": "admin",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

#### 4.2.2 获取用户详情

```http
GET /api/users/<id>
Authorization: Bearer <token>
```

#### 4.2.3 创建用户（管理员）

```http
POST /api/users
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "username": "staff001",
  "password": "password123",
  "name": "张三",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "role": "staff",
  "position": "业务员"
}
```

#### 4.2.4 更新用户

```http
PUT /api/users/<id>
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "name": "新名称",
  "phone": "13900139000",
  "position": "高级业务员"
}
```

#### 4.2.5 删除用户（管理员）

```http
DELETE /api/users/<id>
Authorization: Bearer <token>
```

#### 4.2.6 更新用户状态（管理员）

```http
PATCH /api/users/<id>/status
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "status": "disabled"
}
```

**状态值：**
- `active` - 在职
- `resigned` - 离职
- `disabled` - 禁用

#### 4.2.7 批量操作（管理员）

```http
POST /api/users/batch-action
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "action": "disable",
  "user_ids": [1, 2, 3]
}
```

**支持的操作：**
- `disable` - 禁用
- `enable` - 启用
- `delete` - 删除

#### 4.2.8 获取用户统计

```http
GET /api/users/stats
Authorization: Bearer <token>
```

**响应：**
```json
{
  "total": 10,
  "active": 8,
  "disabled": 2,
  "by_role": {
    "admin": 1,
    "staff": 9
  }
}
```

---

### 4.3 房源管理模块 (Houses)

**URL 前缀：** `/api/houses`

**权限要求：** 需要登录

#### 4.3.1 获取房源列表

```http
GET /api/houses
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页数量 |
| status | string | 状态筛选 |
| city | string | 城市筛选 |
| district | string | 区县筛选 |
| rental_type | string | 租赁类型（whole/shared） |
| landlord_id | int | 房东 ID |
| owner_id | int | 负责员工 ID |
| min_price | float | 最低租金 |
| max_price | float | 最高租金 |
| search | string | 搜索关键词 |

**状态值：**
- `available` - 空闲
- `rented` - 已租
- `maintenance` - 维护中
- `partially_rented` - 部分出租（合租模式）

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "title": "精装修两居室",
      "description": "靠近地铁站，交通便利",
      "province": "北京市",
      "city": "北京市",
      "district": "海淀区",
      "address": "中关村大街1号",
      "area": 80.5,
      "room_count": 2,
      "hall_count": 1,
      "bathroom_count": 1,
      "floor": "中层",
      "total_floors": 18,
      "rent_price": 5000.0,
      "deposit": 5000.0,
      "payment_method": "押一付三",
      "status": "available",
      "rental_type": "whole",
      "facilities": {
        "wifi": true,
        "ac": true,
        "heater": true,
        "kitchen": true
      },
      "cover_image": "/uploads/houses/1/cover.jpg",
      "landlord_id": 1,
      "landlord_name": "王房东",
      "owner_id": 1,
      "owner_name": "张业务员",
      "contact_name": "张业务员",
      "contact_phone": "13800138000",
      "contact_wechat": "zhang001",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 10,
  "pages": 10
}
```

#### 4.3.2 获取房源详情

```http
GET /api/houses/<id>
Authorization: Bearer <token>
```

#### 4.3.3 创建房源

```http
POST /api/houses
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "title": "精装修两居室",
  "description": "靠近地铁站，交通便利",
  "province": "北京市",
  "city": "北京市",
  "district": "海淀区",
  "address": "中关村大街1号",
  "latitude": 39.984,
  "longitude": 116.307,
  "area": 80.5,
  "room_count": 2,
  "hall_count": 1,
  "bathroom_count": 1,
  "floor": "中层",
  "total_floors": 18,
  "rent_price": 5000.0,
  "deposit": 5000.0,
  "payment_method": "押一付三",
  "rental_type": "whole",
  "facilities": {
    "wifi": true,
    "ac": true,
    "heater": true,
    "kitchen": true
  },
  "landlord_id": 1,
  "contact_name": "张业务员",
  "contact_phone": "13800138000",
  "contact_wechat": "zhang001"
}
```

#### 4.3.4 更新房源

```http
PUT /api/houses/<id>
Authorization: Bearer <token>
```

#### 4.3.5 删除房源（管理员）

```http
DELETE /api/houses/<id>
Authorization: Bearer <token>
```

#### 4.3.6 获取房源的房间列表

```http
GET /api/houses/<id>/rooms
Authorization: Bearer <token>
```

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "room_number": "101",
      "name": "主卧",
      "description": "朝南，带阳台",
      "area": 25.0,
      "direction": "南",
      "rent_price": 3000.0,
      "deposit": 3000.0,
      "status": "available",
      "facilities": {
        "bed": true,
        "desk": true,
        "ac": true,
        "balcony": true
      }
    }
  ]
}
```

#### 4.3.7 添加房间（合租房源）

```http
POST /api/houses/<id>/rooms
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "room_number": "101",
  "name": "主卧",
  "description": "朝南，带阳台",
  "area": 25.0,
  "direction": "南",
  "rent_price": 3000.0,
  "deposit": 3000.0,
  "facilities": {
    "bed": true,
    "desk": true,
    "ac": true
  }
}
```

#### 4.3.8 更新房间

```http
PUT /api/houses/rooms/<room_id>
Authorization: Bearer <token>
```

#### 4.3.9 删除房间（管理员）

```http
DELETE /api/houses/rooms/<room_id>
Authorization: Bearer <token>
```

#### 4.3.10 更新房源状态

```http
PUT /api/houses/<id>/status
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "status": "maintenance"
}
```

#### 4.3.11 自动更新房源状态

```http
POST /api/houses/<id>/auto-status
Authorization: Bearer <token>
```

根据房间出租情况自动计算房源状态。

#### 4.3.12 获取房源统计

```http
GET /api/houses/stats
Authorization: Bearer <token>
```

**响应：**
```json
{
  "total": 100,
  "available": 30,
  "rented": 50,
  "maintenance": 10,
  "partially_rented": 10,
  "by_city": {
    "北京市": 60,
    "上海市": 40
  },
  "by_rental_type": {
    "whole": 70,
    "shared": 30
  }
}
```

---

### 4.4 租客管理模块 (Tenants)

**URL 前缀：** `/api/tenants`

**权限要求：** 需要登录

#### 4.4.1 获取租客列表

```http
GET /api/tenants
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页数量 |
| status | string | 状态筛选 |
| search | string | 搜索关键词（姓名/电话） |

**状态值：**
- `pending` - 待审核
- `active` - 在租
- `expired` - 已退租
- `blacklisted` - 黑名单

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "name": "王小明",
      "phone": "13700137000",
      "email": "wang@example.com",
      "emergency_contact": "张大明",
      "emergency_phone": "13600136000",
      "emergency_relation": "父亲",
      "company": "某科技公司",
      "occupation": "工程师",
      "status": "active",
      "remark": "",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 10,
  "pages": 5
}
```

#### 4.4.2 获取租客详情

```http
GET /api/tenants/<id>
Authorization: Bearer <token>
```

#### 4.4.3 创建租客

```http
POST /api/tenants
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "name": "王小明",
  "id_card": "110101199001011234",
  "phone": "13700137000",
  "email": "wang@example.com",
  "emergency_contact": "张大明",
  "emergency_phone": "13600136000",
  "emergency_relation": "父亲",
  "company": "某科技公司",
  "occupation": "工程师",
  "remark": ""
}
```

> **注意：** 身份证号会自动加密存储

#### 4.4.4 更新租客

```http
PUT /api/tenants/<id>
Authorization: Bearer <token>
```

#### 4.4.5 删除租客（管理员）

```http
DELETE /api/tenants/<id>
Authorization: Bearer <token>
```

#### 4.4.6 获取租客的合同列表

```http
GET /api/tenants/<id>/contracts
Authorization: Bearer <token>
```

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "contract_no": "HT2024010100001",
      "title": "租赁合同",
      "house_title": "精装修两居室",
      "start_date": "2024-01-01",
      "end_date": "2024-12-31",
      "rent_amount": 5000.0,
      "status": "active"
    }
  ]
}
```

#### 4.4.7 获取租客统计

```http
GET /api/tenants/stats
Authorization: Bearer <token>
```

#### 4.4.8 搜索租客

```http
GET /api/tenants/search?q=王小明
Authorization: Bearer <token>
```

---

### 4.5 房东管理模块 (Landlords)

**URL 前缀：** `/api/landlords`

**权限要求：** 需要登录

#### 4.5.1 获取房东列表

```http
GET /api/landlords
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页数量 |
| status | string | 状态筛选 |
| search | string | 搜索关键词 |

**状态值：**
- `active` - 正常
- `inactive` - 停用
- `blacklisted` - 黑名单

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "name": "王房东",
      "phone": "13700137000",
      "bank_name": "中国工商银行北京分行",
      "bank_card_masked": "6222 **** **** 0123",
      "property_cert_no": "京房权证朝私字第123456号",
      "address": "北京市朝阳区某某小区3号楼",
      "status": "active",
      "remark": "优质房东",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 20,
  "page": 1,
  "per_page": 10,
  "pages": 2
}
```

> **注意：** 身份证号和银行卡号自动脱敏显示

#### 4.5.2 获取房东详情

```http
GET /api/landlords/<id>
Authorization: Bearer <token>
```

#### 4.5.3 创建房东

```http
POST /api/landlords
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "name": "王房东",
  "id_card": "110101199001011234",
  "phone": "13700137000",
  "bank_card": "6222001234567890123",
  "bank_name": "中国工商银行北京分行",
  "property_cert_no": "京房权证朝私字第123456号",
  "address": "北京市朝阳区某某小区3号楼",
  "remark": "优质房东"
}
```

> **注意：** 身份证号和银行卡号会自动加密存储

#### 4.5.4 更新房东

```http
PUT /api/landlords/<id>
Authorization: Bearer <token>
```

#### 4.5.5 删除房东（管理员）

```http
DELETE /api/landlords/<id>
Authorization: Bearer <token>
```

#### 4.5.6 获取房东的房源列表

```http
GET /api/landlords/<id>/houses
Authorization: Bearer <token>
```

#### 4.5.7 获取房东的合同列表

```http
GET /api/landlords/<id>/contracts
Authorization: Bearer <token>
```

#### 4.5.8 获取房东统计

```http
GET /api/landlords/stats
Authorization: Bearer <token>
```

#### 4.5.9 搜索房东

```http
GET /api/landlords/search?q=王
Authorization: Bearer <token>
```

---

### 4.6 租赁合同模块 (Contracts)

**URL 前缀：** `/api/contracts`

**权限要求：** 需要登录

#### 4.6.1 获取合同列表

```http
GET /api/contracts
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页数量 |
| status | string | 状态筛选 |
| tenant_id | int | 租客 ID |
| house_id | int | 房源 ID |
| start_date | string | 开始日期范围 |
| end_date | string | 结束日期范围 |

**状态值：**
- `draft` - 草稿
- `active` - 生效中
- `expired` - 已过期
- `terminated` - 已终止
- `renewed` - 已续签

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "contract_no": "HT2024010100001",
      "title": "精装修两居室租赁合同",
      "description": "标准租赁合同",
      "start_date": "2024-01-01",
      "end_date": "2024-12-31",
      "rent_amount": 5000.0,
      "deposit_amount": 5000.0,
      "payment_type": "季付",
      "payment_cycle": 3,
      "status": "active",
      "deposit_status": "paid",
      "deposit_status_name": "已支付",
      "version": 1,
      "house_id": 1,
      "house_title": "精装修两居室",
      "room_id": null,
      "room_name": null,
      "tenant_id": 1,
      "tenant_name": "王小明",
      "is_expired": false,
      "is_expiring_soon": false,
      "days_until_expiry": 300,
      "total_rent": 60000.0,
      "is_renewal": false,
      "original_contract_id": null,
      "original_contract_no": null,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 30,
  "page": 1,
  "per_page": 10,
  "pages": 3
}
```

**押金状态说明：**
- `pending` - 待支付：合同创建后的初始状态
- `paid` - 已支付：租客已支付押金
- `transferred` - 已转移：续签时押金转移到新合同
- `refunded` - 已退款：合同结束后押金已退还

**乐观锁说明：**
- `version` 字段用于并发控制，每次更新自动递增
- 更新合同时需携带当前版本号，版本不匹配将返回错误

#### 4.6.2 获取合同详情

```http
GET /api/contracts/<id>
Authorization: Bearer <token>
```

#### 4.6.3 创建合同

```http
POST /api/contracts
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "title": "精装修两居室租赁合同",
  "description": "标准租赁合同",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "rent_amount": 5000.0,
  "deposit_amount": 5000.0,
  "payment_type": "季付",
  "payment_cycle": 3,
  "house_id": 1,
  "room_id": null,
  "tenant_id": 1,
  "contract_file": "/uploads/contracts/contract.pdf",
  "remark": ""
}
```

> **说明：** 合同编号（contract_no）自动生成，格式：HT + 年月日 + 8位随机数

#### 4.6.4 更新合同

```http
PUT /api/contracts/<id>
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "title": "更新后的合同标题",
  "rent_amount": 5500.0,
  "version": 1
}
```

> **乐观锁说明：**
> - 更新合同时必须携带 `version` 字段
> - 如果版本号不匹配，将返回 409 Conflict 错误
> - 更新成功后版本号自动递增

**错误响应（版本冲突）：**
```json
{
  "success": false,
  "error": "version_conflict",
  "message": "合同已被其他用户修改，请刷新后重试"
}
```

#### 4.6.5 更新押金状态

```http
POST /api/contracts/<id>/deposit-status
Authorization: Bearer <token>
```

**权限要求：** edit 权限

**请求体：**
```json
{
  "deposit_status": "paid"
}
```

**押金状态转换规则：**
- `pending` → `paid`：确认收到押金
- `pending` → `refunded`：押金为 0 时直接退款
- `paid` → `transferred`：续签时转移押金到新合同
- `paid` → `refunded`：合同结束后退还押金

**错误响应：**
```json
{
  "success": false,
  "error": "invalid_transition",
  "message": "押金状态不能从 '已退款' 转换为 '已支付'"
}
```

#### 4.6.6 删除合同（管理员）

```http
DELETE /api/contracts/<id>
Authorization: Bearer <token>
```

#### 4.6.6 续签合同

```http
POST /api/contracts/<id>/renew
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "new_end_date": "2025-12-31",
  "new_rent_amount": 5500.0,
  "new_payment_type": "季付",
  "remark": "续签一年"
}
```

#### 4.6.7 激活合同

```http
POST /api/contracts/<id>/activate
Authorization: Bearer <token>
```

将草稿状态的合同激活为生效状态。

#### 4.6.8 终止合同

```http
POST /api/contracts/<id>/terminate
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "reason": "租客提前退租",
  "terminate_date": "2024-06-30"
}
```

#### 4.6.9 获取即将到期的合同

```http
GET /api/contracts/expiring?days=30
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| days | int | 30 | 查询多少天内到期的合同 |

#### 4.6.10 获取合同的支付记录

```http
GET /api/contracts/<id>/payments
Authorization: Bearer <token>
```

#### 4.6.11 获取合同统计

```http
GET /api/contracts/stats
Authorization: Bearer <token>
```

**响应：**
```json
{
  "total": 100,
  "draft": 10,
  "active": 60,
  "expired": 20,
  "terminated": 10,
  "expiring_soon": 15,
  "total_rent": 5000000.0
}
```

---

### 4.7 支付管理模块 (Payments)

**URL 前缀：** `/api/payments`

**权限要求：** 需要登录

#### 4.7.1 获取支付记录列表

```http
GET /api/payments
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页数量 |
| status | string | 状态筛选 |
| contract_id | int | 合同 ID |
| payment_type | string | 支付类型 |
| start_date | string | 开始日期 |
| end_date | string | 结束日期 |

**状态值：**
- `pending` - 待支付
- `paid` - 已支付
- `overdue` - 逾期
- `partial` - 部分支付
- `refunded` - 已退款

**支付类型：**
- `rent` - 租金
- `deposit` - 押金
- `utility` - 水电费
- `other` - 其他

**支付方式：**
- `cash` - 现金
- `bank` - 银行转账
- `wechat` - 微信
- `alipay` - 支付宝

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "payment_no": "PY2024010100001",
      "amount": 5000.0,
      "paid_amount": 5000.0,
      "payment_type": "rent",
      "payment_type_name": "租金",
      "payment_method": "wechat",
      "payment_method_name": "微信",
      "period_start": "2024-01-01",
      "period_end": "2024-03-31",
      "due_date": "2024-01-05",
      "payment_date": "2024-01-03",
      "confirmed_date": "2024-01-03",
      "late_fee": 0.0,
      "overdue_days": 0,
      "status": "paid",
      "status_name": "已支付",
      "total_amount": 5000.0,
      "contract_id": 1,
      "contract_no": "HT2024010100001",
      "tenant_name": "王小明",
      "operator_name": "张业务员",
      "remark": "",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 200,
  "page": 1,
  "per_page": 10,
  "pages": 20
}
```

#### 4.7.2 获取支付详情

```http
GET /api/payments/<id>
Authorization: Bearer <token>
```

#### 4.7.3 创建支付记录

```http
POST /api/payments
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "contract_id": 1,
  "amount": 5000.0,
  "payment_type": "rent",
  "period_start": "2024-01-01",
  "period_end": "2024-03-31",
  "due_date": "2024-01-05",
  "remark": ""
}
```

> **说明：** 支付编号（payment_no）自动生成，格式：PY + 年月日 + 8位随机数

#### 4.7.4 更新支付记录

```http
PUT /api/payments/<id>
Authorization: Bearer <token>
```

#### 4.7.5 删除支付记录（管理员）

```http
DELETE /api/payments/<id>
Authorization: Bearer <token>
```

#### 4.7.6 确认支付

```http
POST /api/payments/<id>/verify
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "paid_amount": 5000.0,
  "payment_date": "2024-01-03",
  "payment_method": "wechat",
  "remark": "微信转账确认"
}
```

#### 4.7.7 获取逾期支付列表

```http
GET /api/payments/overdue
Authorization: Bearer <token>
```

#### 4.7.8 获取合同支付计划

```http
GET /api/payments/contracts/<contract_id>/payment-plan
Authorization: Bearer <token>
```

#### 4.7.9 获取支付统计

```http
GET /api/payments/stats
Authorization: Bearer <token>
```

**响应：**
```json
{
  "total": 500,
  "pending": 50,
  "paid": 400,
  "overdue": 30,
  "partial": 15,
  "refunded": 5,
  "total_amount": 2500000.0,
  "total_paid": 2000000.0,
  "total_late_fee": 15000.0
}
```

#### 4.7.10 更新滞纳金

```http
POST /api/payments/update-late-fees
Authorization: Bearer <token>
```

批量更新所有逾期支付的滞纳金。

**滞纳金计算规则：**
- 日利率：0.05%
- 上限：20%
- 公式：滞纳金 = 应缴金额 × 日利率 × 逾期天数

---

### 4.8 承包合同模块 (Landlord Contracts)

**URL 前缀：** `/api/landlord_contracts`

**权限要求：** 需要登录

#### 4.8.1 获取承包合同列表

```http
GET /api/landlord_contracts
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页数量 |
| status | string | 状态筛选 |
| landlord_id | int | 房东 ID |

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "contract_no": "LC202401010001",
      "title": "平台与王房东承包合同",
      "description": "承包王房东的所有房源",
      "start_date": "2024-01-01",
      "end_date": "2024-12-31",
      "contract_amount": 100000.0,
      "service_fee_rate": 5.0,
      "minimum_fee": 5000.0,
      "payment_cycle": 3,
      "status": "active",
      "landlord_id": 1,
      "landlord_name": "王房东",
      "house_ids": [1, 2, 3],
      "houses": [
        {"id": 1, "title": "房源1"},
        {"id": 2, "title": "房源2"}
      ],
      "contract_term": 12,
      "service_fee": 5000.0,
      "is_expired": false,
      "days_until_expiry": 300,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

#### 4.8.2 获取承包合同详情

```http
GET /api/landlord_contracts/<id>
Authorization: Bearer <token>
```

#### 4.8.3 创建承包合同

```http
POST /api/landlord_contracts
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "title": "平台与王房东承包合同",
  "description": "承包王房东的所有房源",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "contract_amount": 100000.0,
  "service_fee_rate": 5.0,
  "minimum_fee": 5000.0,
  "payment_cycle": 3,
  "landlord_id": 1,
  "house_ids": [1, 2, 3],
  "contract_file": "/uploads/landlord_contracts/contract.pdf",
  "remark": ""
}
```

> **说明：** 合同编号（contract_no）自动生成，格式：LC + 年月日 + 4位随机数

#### 4.8.4 更新承包合同

```http
PUT /api/landlord_contracts/<id>
Authorization: Bearer <token>
```

#### 4.8.5 删除承包合同（管理员）

```http
DELETE /api/landlord_contracts/<id>
Authorization: Bearer <token>
```

#### 4.8.6 激活承包合同

```http
POST /api/landlord_contracts/<id>/activate
Authorization: Bearer <token>
```

#### 4.8.7 终止承包合同

```http
POST /api/landlord_contracts/<id>/terminate
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "reason": "房东违约",
  "terminate_date": "2024-06-30"
}
```

#### 4.8.8 续签承包合同

```http
POST /api/landlord_contracts/<id>/renew
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "new_end_date": "2025-12-31",
  "new_contract_amount": 120000.0,
  "new_service_fee_rate": 5.0,
  "remark": "续签一年"
}
```

#### 4.8.9 获取即将到期的承包合同

```http
GET /api/landlord_contracts/expiring?days=30
Authorization: Bearer <token>
```

#### 4.8.10 获取承包合同统计

```http
GET /api/landlord_contracts/stats
Authorization: Bearer <token>
```

---

### 4.9 统计分析模块 (Statistics)

**URL 前缀：** `/api/statistics`

**权限要求：** 需要登录

#### 4.9.1 获取概览统计

```http
GET /api/statistics/overview
Authorization: Bearer <token>
```

**响应：**
```json
{
  "total_houses": 100,
  "available_houses": 30,
  "rented_houses": 60,
  "total_tenants": 150,
  "active_tenants": 80,
  "total_contracts": 200,
  "active_contracts": 120,
  "total_payments": 500,
  "total_income": 2500000.0,
  "pending_payments": 50,
  "overdue_payments": 30,
  "occupancy_rate": 0.6,
  "collection_rate": 0.85
}
```

#### 4.9.2 获取房源统计

```http
GET /api/statistics/houses
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| start_date | string | 开始日期 |
| end_date | string | 结束日期 |
| group_by | string | 分组方式（city/district/rental_type） |

#### 4.9.3 获取收入统计

```http
GET /api/statistics/income
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| start_date | string | 开始日期 |
| end_date | string | 结束日期 |
| group_by | string | 分组方式（month/quarter/year） |

**响应：**
```json
{
  "total_income": 2500000.0,
  "total_late_fee": 15000.0,
  "by_period": [
    {
      "period": "2024-01",
      "income": 200000.0,
      "late_fee": 1000.0
    },
    {
      "period": "2024-02",
      "income": 220000.0,
      "late_fee": 800.0
    }
  ],
  "by_payment_type": {
    "rent": 2000000.0,
    "deposit": 400000.0,
    "utility": 100000.0
  }
}
```

#### 4.9.4 获取租客统计

```http
GET /api/statistics/tenants
Authorization: Bearer <token>
```

#### 4.9.5 获取合同统计

```http
GET /api/statistics/contracts
Authorization: Bearer <token>
```

#### 4.9.6 获取仪表盘数据

```http
GET /api/statistics/dashboard
Authorization: Bearer <token>
```

**响应：**
```json
{
  "overview": {
    "total_houses": 100,
    "available_houses": 30,
    "rented_houses": 60,
    "total_tenants": 150,
    "active_contracts": 120,
    "pending_payments": 50
  },
  "recent_activities": [...],
  "alerts": [...]
}
```

#### 4.9.7 获取收入统计

```http
GET /api/statistics/revenue
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| start_date | string | 开始日期 |
| end_date | string | 结束日期 |
| group_by | string | 分组方式（day/month/year） |

#### 4.9.8 获取入住率统计

```http
GET /api/statistics/occupancy
Authorization: Bearer <token>
```

**响应：**
```json
{
  "overall_rate": 0.85,
  "by_city": {
    "北京市": 0.82,
    "上海市": 0.88
  },
  "by_rental_type": {
    "whole": 0.80,
    "shared": 0.90
  }
}
```

#### 4.9.9 获取即将到期合同

```http
GET /api/statistics/expiring-contracts
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| days | int | 30 | 查询多少天内到期的合同 |

#### 4.9.10 导出 Excel 报表

```http
GET /api/statistics/export/excel
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| type | string | 报表类型（overview/income/houses/tenants/contracts） |
| start_date | string | 开始日期 |
| end_date | string | 结束日期 |

**响应：** 返回 Excel 文件下载

#### 4.9.11 导出 PDF 报表

```http
GET /api/statistics/export/pdf
Authorization: Bearer <token>
```

**查询参数：** 同 Excel 导出

**响应：** 返回 PDF 文件下载

---

### 4.10 数据备份模块 (Backup)

**URL 前缀：** `/api/backup`

**权限要求：** 需要管理员权限

#### 4.10.1 创建备份

```http
POST /api/backup/create
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "description": "每月定期备份",
  "tables": ["users", "houses", "contracts", "payments"]
}
```

**响应：**
```json
{
  "message": "备份创建成功",
  "backup": {
    "filename": "backup_20240101_120000.sql",
    "size": 1048576,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### 4.10.2 获取备份列表

```http
GET /api/backup/list
Authorization: Bearer <token>
```

**响应：**
```json
{
  "items": [
    {
      "filename": "backup_20240101_120000.sql",
      "size": 1048576,
      "size_formatted": "1.00 MB",
      "created_at": "2024-01-01T12:00:00Z",
      "description": "每月定期备份"
    }
  ],
  "total": 10
}
```

#### 4.10.3 下载备份文件

```http
GET /api/backup/download/<filename>
Authorization: Bearer <token>
```

**响应：** 返回 SQL 备份文件下载

#### 4.10.4 恢复数据

```http
POST /api/backup/restore
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "filename": "backup_20240101_120000.sql"
}
```

#### 4.10.5 删除备份

```http
DELETE /api/backup/<filename>
Authorization: Bearer <token>
```

#### 4.10.6 获取备份设置

```http
GET /api/backup/settings
Authorization: Bearer <token>
```

#### 4.10.7 更新备份设置

```http
PUT /api/backup/settings
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "auto_backup": true,
  "backup_interval": 24,
  "retention_days": 30,
  "backup_tables": ["users", "houses", "contracts", "payments"]
}
```

#### 4.10.8 获取备份统计

```http
GET /api/backup/stats
Authorization: Bearer <token>
```

#### 4.10.9 健康检查

```http
GET /api/backup/health
Authorization: Bearer <token>
```

#### 4.10.10 获取备份告警

```http
GET /api/backup/alerts
Authorization: Bearer <token>
```

#### 4.10.11 确认告警

```http
POST /api/backup/alerts/<id>/acknowledge
Authorization: Bearer <token>
```

#### 4.10.12 验证备份文件

```http
POST /api/backup/verify/<filename>
Authorization: Bearer <token>
```

---

### 4.11 员工管理模块 (Employees)

**URL 前缀：** `/api/employees`

**权限要求：** 需要管理员权限

#### 4.11.1 获取员工列表

```http
GET /api/employees
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页数量 |
| status | string | 状态筛选 |
| position | string | 职位筛选 |
| search | string | 搜索关键词 |

**响应：**
```json
{
  "items": [
    {
      "id": 2,
      "username": "staff001",
      "name": "张三",
      "email": "zhangsan@example.com",
      "phone": "13800138000",
      "role": "staff",
      "position": "业务员",
      "status": "active",
      "avatar": "/uploads/avatars/staff001.jpg",
      "last_login": "2024-01-01T10:00:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "created_by_name": "管理员"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

#### 4.11.2 获取员工详情

```http
GET /api/employees/<id>
Authorization: Bearer <token>
```

#### 4.11.3 创建员工

```http
POST /api/employees
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "username": "staff002",
  "password": "password123",
  "name": "李四",
  "phone": "13900139000",
  "email": "lisi@example.com",
  "position": "业务员",
  "id_card": "110101199002021234"
}
```

#### 4.11.4 更新员工

```http
PUT /api/employees/<id>
Authorization: Bearer <token>
```

#### 4.11.5 删除员工

```http
DELETE /api/employees/<id>
Authorization: Bearer <token>
```

#### 4.11.6 更新员工状态

```http
PATCH /api/employees/<id>/status
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "status": "resigned"
}
```

#### 4.11.7 重置员工密码

```http
POST /api/employees/<id>/reset-password
Authorization: Bearer <token>
```

**响应：**
```json
{
  "message": "密码重置成功",
  "new_password": "TempPass123!"
}
```

#### 4.11.8 批量操作

```http
POST /api/employees/batch-action
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "action": "disable",
  "employee_ids": [1, 2, 3]
}
```

#### 4.11.9 获取员工统计

```http
GET /api/employees/stats
Authorization: Bearer <token>
```

---

### 4.12 文件上传模块 (Upload)

**URL 前缀：** `/api/upload`

**权限要求：** 需要登录

#### 4.12.1 通用文件上传

```http
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**请求体：**
```
file: <文件>
```

**响应：**
```json
{
  "message": "上传成功",
  "file": {
    "id": 1,
    "file_name": "image.jpg",
    "file_path": "/uploads/2024/01/image.jpg",
    "file_url": "http://example.com/uploads/2024/01/image.jpg",
    "file_type": "image",
    "file_size": 204800,
    "file_size_formatted": "200.00 KB"
  }
}
```

#### 4.12.2 上传图片

```http
POST /api/upload/image
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**请求体：**
```
file: <图片文件>
```

**支持的格式：** JPEG, PNG, GIF, WebP

#### 4.12.3 上传视频

```http
POST /api/upload/video
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**请求体：**
```
file: <视频文件>
```

**支持的格式：** MP4, MOV, AVI

#### 4.12.4 上传房源媒体

```http
POST /api/upload/house/<house_id>
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**请求体：**
```
file: <文件>
description: 图片描述
is_cover: true/false
sort_order: 1
```

#### 4.12.5 删除媒体文件

```http
DELETE /api/upload/<media_id>
Authorization: Bearer <token>
```

#### 4.12.6 设置封面图片

```http
PUT /api/upload/<media_id>/cover
Authorization: Bearer <token>
```

#### 4.12.7 获取房源媒体列表

```http
GET /api/upload/house/<house_id>/media
Authorization: Bearer <token>
```

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "file_name": "room_101.jpg",
      "file_url": "http://example.com/uploads/houses/1/room_101.jpg",
      "file_type": "image",
      "file_size": 204800,
      "file_size_formatted": "200.00 KB",
      "description": "主卧实拍",
      "is_cover": true,
      "sort_order": 1,
      "uploaded_by_name": "张业务员",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### 4.13 公开房源模块 (Public Houses)

**URL 前缀：** `/api/public/houses`

**权限要求：** 无需登录

> **说明：** 公开接口不返回敏感信息（如房东联系方式、负责员工信息等）

#### 4.13.1 获取公开房源列表

```http
GET /api/public/houses
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页数量 |
| city | string | 城市筛选 |
| district | string | 区县筛选 |
| rental_type | string | 租赁类型 |
| min_price | float | 最低租金 |
| max_price | float | 最高租金 |
| search | string | 搜索关键词 |

**响应：**
```json
{
  "items": [
    {
      "id": 1,
      "title": "精装修两居室",
      "description": "靠近地铁站，交通便利",
      "city": "北京市",
      "district": "海淀区",
      "address": "中关村大街1号",
      "area": 80.5,
      "room_count": 2,
      "hall_count": 1,
      "bathroom_count": 1,
      "floor": "中层",
      "rent_price": 5000.0,
      "deposit": 5000.0,
      "rental_type": "whole",
      "facilities": {
        "wifi": true,
        "ac": true
      },
      "cover_image": "/uploads/houses/1/cover.jpg",
      "status": "available"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 10,
  "pages": 10
}
```

#### 4.13.2 获取公开房源详情

```http
GET /api/public/houses/<id>
```

#### 4.13.3 获取公开房源房间列表

```http
GET /api/public/houses/<id>/rooms
```

#### 4.13.4 获取公开房源统计

```http
GET /api/public/houses/stats
```

---

### 4.14 审计日志模块 (Audit)

**URL 前缀：** `/api/audit`

**权限要求：** 需要管理员权限

#### 4.14.1 获取审计日志开关状态

```http
GET /api/audit/toggle
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "data": {
    "enabled": false
  }
}
```

#### 4.14.2 更新审计日志开关状态（管理员）

```http
PUT /api/audit/toggle
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "enabled": true
}
```

#### 4.14.3 获取审计日志列表

```http
GET /api/audit/logs
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| per_page | int | 每页数量 |
| user_id | int | 用户 ID |
| operation_type | string | 操作类型 |
| model_name | string | 模型名称 |
| start_date | string | 开始日期 |
| end_date | string | 结束日期 |

**响应：**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": 1,
        "user_id": 1,
        "user_name": "管理员",
        "operation_type": "view",
        "model_name": "Landlord",
        "record_id": 1,
        "field_name": "bank_card_encrypted",
        "old_value": null,
        "new_value": "****",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
        "created_at": "2024-01-01T12:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 100,
      "pages": 10
    }
  }
}
```

#### 4.14.4 获取审计日志详情

```http
GET /api/audit/logs/<id>
Authorization: Bearer <token>
```

#### 4.14.5 获取用户的审计日志

```http
GET /api/audit/logs/user/<user_id>
Authorization: Bearer <token>
```

#### 4.14.6 获取记录的审计日志

```http
GET /api/audit/logs/record/<model_name>/<record_id>
Authorization: Bearer <token>
```

#### 4.14.7 获取审计统计

```http
GET /api/audit/statistics
Authorization: Bearer <token>
```

#### 4.14.8 获取用户审计统计

```http
GET /api/audit/statistics/user/<user_id>
Authorization: Bearer <token>
```

#### 4.14.9 获取审计告警

```http
GET /api/audit/alerts
Authorization: Bearer <token>
```

#### 4.14.10 导出审计日志

```http
GET /api/audit/export
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| start_date | string | 开始日期 |
| end_date | string | 结束日期 |
| format | string | 导出格式（csv/json） |

#### 4.14.11 导出审计统计

```http
GET /api/audit/export/statistics
Authorization: Bearer <token>
```

#### 4.14.12 获取敏感字段列表

```http
GET /api/audit/sensitive-fields
Authorization: Bearer <token>
```

#### 4.14.13 获取操作类型列表

```http
GET /api/audit/operation-types
Authorization: Bearer <token>
```

---

### 4.15 系统监控模块 (Monitoring)

**URL 前缀：** `/api/monitoring`

**权限要求：** 部分接口需要管理员权限

#### 4.15.1 系统健康检查

```http
GET /api/monitoring/health
```

**响应：**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

#### 4.15.2 数据库健康检查

```http
GET /api/monitoring/health/db
Authorization: Bearer <token>
```

#### 4.15.3 Redis 健康检查

```http
GET /api/monitoring/health/redis
Authorization: Bearer <token>
```

#### 4.15.4 系统资源健康检查

```http
GET /api/monitoring/health/system
Authorization: Bearer <token>
```

**响应：**
```json
{
  "status": "healthy",
  "cpu_usage": 25.5,
  "memory_usage": 60.2,
  "disk_usage": 45.8,
  "uptime": 86400
}
```

#### 4.15.5 Prometheus 指标

```http
GET /api/monitoring/metrics
```

**响应：** Prometheus 格式的监控指标

#### 4.15.6 性能概览

```http
GET /api/monitoring/performance
Authorization: Bearer <token>
```

#### 4.15.7 QPS 统计

```http
GET /api/monitoring/performance/qps
Authorization: Bearer <token>
```

#### 4.15.8 响应时间统计

```http
GET /api/monitoring/performance/response-time
Authorization: Bearer <token>
```

#### 4.15.9 错误率统计

```http
GET /api/monitoring/performance/error-rate
Authorization: Bearer <token>
```

#### 4.15.10 资源使用统计

```http
GET /api/monitoring/performance/resources
Authorization: Bearer <token>
```

#### 4.15.11 获取告警列表

```http
GET /api/monitoring/alerts
Authorization: Bearer <token>
```

#### 4.15.12 获取告警历史

```http
GET /api/monitoring/alerts/history
Authorization: Bearer <token>
```

#### 4.15.13 解决告警

```http
POST /api/monitoring/alerts/<id>/resolve
Authorization: Bearer <token>
```

#### 4.15.14 清除已解决告警

```http
POST /api/monitoring/alerts/clear-resolved
Authorization: Bearer <token>
```

#### 4.15.15 监控仪表盘

```http
GET /api/monitoring/dashboard
Authorization: Bearer <token>
```

#### 4.15.16 重置监控数据

```http
POST /api/monitoring/reset
Authorization: Bearer <token>
```

---

### 4.16 启动任务模块 (Startup Tasks)

**URL 前缀：** `/api/startup-tasks`

**权限要求：** 需要登录

#### 4.16.1 获取任务执行状态

```http
GET /api/startup-tasks/status
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| task_name | string | 任务名称（可选） |
| task_date | string | 任务日期（可选，格式：YYYY-MM-DD） |

**响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "task_name": "data_consistency_check",
      "task_date": "2024-01-01",
      "status": "completed",
      "started_at": "2024-01-01T00:00:00Z",
      "completed_at": "2024-01-01T00:01:00Z",
      "total_records": 1000,
      "processed_records": 1000,
      "failed_records": 0,
      "execution_time": 60.5
    }
  ]
}
```

#### 4.16.2 获取任务执行日志

```http
GET /api/startup-tasks/logs
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| task_name | string | 任务名称（可选） |
| limit | int | 返回记录数量限制（默认 100，最大 1000） |

**响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "task_name": "contract_expiry_check",
      "task_date": "2024-01-01",
      "status": "completed",
      "started_at": "2024-01-01T00:01:00Z",
      "completed_at": "2024-01-01T00:02:00Z",
      "total_records": 50,
      "processed_records": 50,
      "failed_records": 0,
      "execution_time": 45.2
    }
  ]
}
```

#### 4.16.3 获取任务配置信息（管理员）

```http
GET /api/startup-tasks/config
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "batch_size": 100,
    "timeout": 60,
    "delay": 100,
    "tasks": [
      "data_consistency_check",
      "contract_expiry_check",
      "payment_overdue_process",
      "contract_expiry_reminder"
    ]
  }
}
```

#### 4.16.4 获取任务执行摘要

```http
GET /api/startup-tasks/summary
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "data": {
    "date": "2024-01-01",
    "total": 4,
    "completed": 3,
    "running": 1,
    "failed": 0,
    "pending": 0,
    "tasks": [...]
  }
}
```

**任务类型说明：**
- `data_consistency_check` - 数据一致性检查（优先级最高）
- `contract_expiry_check` - 合同到期检查
- `payment_overdue_process` - 支付逾期处理
- `contract_expiry_reminder` - 合同到期提醒（优先级最低）

**任务状态说明：**
- `pending` - 待执行
- `running` - 执行中
- `completed` - 已完成
- `failed` - 执行失败

---

### 4.17 押金退款模块 (Deposit Refunds)

**URL 前缀：** `/api/deposit-refunds`

**权限要求：** 需要登录

#### 4.17.1 获取退款列表

```http
GET /api/deposit-refunds
Authorization: Bearer <token>
```

**查询参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认 1 |
| per_page | int | 每页数量，默认 20，最大 100 |
| status | string | 状态筛选 (pending/processed/completed/cancelled) |
| contract_id | int | 合同 ID 筛选 |
| tenant_id | int | 租客 ID 筛选 |
| house_id | int | 房源 ID 筛选 |

**响应：**
```json
{
  "success": true,
  "message": "获取退款列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "contract_id": 1,
        "contract_no": "HT2024010100001",
        "contract_title": "租赁合同",
        "tenant_id": 1,
        "tenant_name": "王小明",
        "tenant_phone": "13800138000",
        "house_id": 1,
        "house_title": "精装修两居室",
        "house_address": "中关村大街1号",
        "original_deposit": 5000.0,
        "deductions": [
          {
            "type": "unpaid_rent",
            "type_name": "未付租金",
            "amount": 1000.0,
            "description": "未付最后一个月租金"
          }
        ],
        "total_deduction": 1000.0,
        "refund_amount": 4000.0,
        "status": "pending",
        "status_name": "待处理",
        "deposit_status": "paid",
        "deposit_status_name": "已支付",
        "processor_name": null,
        "processed_at": null,
        "completed_at": null,
        "remark": "",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 10,
      "pages": 1
    }
  }
}
```

#### 4.17.2 获取退款详情

```http
GET /api/deposit-refunds/<refund_id>
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "contract_id": 1,
    "contract_no": "HT2024010100001",
    "original_deposit": 5000.0,
    "deductions": [...],
    "total_deduction": 1000.0,
    "refund_amount": 4000.0,
    "status": "pending",
    "status_name": "待处理",
    "deduction_summary": [
      {
        "type": "unpaid_rent",
        "type_name": "未付租金",
        "total_amount": 1000.0,
        "count": 1,
        "items": [...]
      }
    ]
  }
}
```

#### 4.17.3 处理退款

```http
POST /api/deposit-refunds/<refund_id>/process
Authorization: Bearer <token>
```

**权限要求：** edit 权限

**请求体：**
```json
{
  "deductions": [
    {
      "type": "unpaid_rent",
      "amount": 1000,
      "description": "未付最后一个月租金"
    },
    {
      "type": "damage_compensation",
      "amount": 500,
      "description": "墙面损坏赔偿"
    }
  ],
  "remark": "已确认扣款项"
}
```

**扣款类型：**
- `unpaid_rent` - 未付租金
- `unpaid_utilities` - 未付水电费
- `late_fees` - 滞纳金
- `damage_compensation` - 损坏赔偿
- `other` - 其他扣款

**响应：**
```json
{
  "success": true,
  "message": "退款处理成功",
  "data": {
    "id": 1,
    "status": "processed",
    "status_name": "已处理",
    "total_deduction": 1500.0,
    "refund_amount": 3500.0,
    "processed_at": "2024-01-01T12:00:00Z"
  }
}
```

#### 4.17.4 完成退款

```http
POST /api/deposit-refunds/<refund_id>/complete
Authorization: Bearer <token>
```

**权限要求：** edit 权限

**请求体：**
```json
{
  "remark": "已通过银行转账退还"
}
```

**响应：**
```json
{
  "success": true,
  "message": "退款完成",
  "data": {
    "id": 1,
    "status": "completed",
    "status_name": "已完成",
    "completed_at": "2024-01-01T14:00:00Z"
  }
}
```

> **说明：** 完成退款时会自动更新合同押金状态为 `refunded`

#### 4.17.5 取消退款

```http
POST /api/deposit-refunds/<refund_id>/cancel
Authorization: Bearer <token>
```

**权限要求：** edit 权限

**请求体：**
```json
{
  "reason": "租客撤回退租申请"
}
```

**响应：**
```json
{
  "success": true,
  "message": "退款已取消",
  "data": {
    "id": 1,
    "status": "cancelled",
    "status_name": "已取消"
  }
}
```

**退款状态说明：**
- `pending` - 待处理：退款申请已创建，等待处理
- `processed` - 已处理：已确认扣款项，等待打款
- `completed` - 已完成：退款已打款完成
- `cancelled` - 已取消：退款申请已取消

---

### 4.18 通知管理模块 (Notifications)

**URL 前缀：** `/api/notifications`

**权限要求：** 需要登录

#### 4.18.1 批量发送通知

```http
POST /api/notifications/batch-send
Authorization: Bearer <token>
```

**权限要求：** edit 权限

**请求体：**
```json
{
  "tenant_ids": [1, 2, 3],
  "message": "您的租金即将到期，请及时缴纳。"
}
```

**响应：**
```json
{
  "success": true,
  "message": "批量发送成功：3 条通知已发送",
  "data": {
    "sent_count": 3,
    "failed_count": 0,
    "details": [
      {
        "tenant_id": 1,
        "success": true,
        "tenant_name": "王小明",
        "tenant_phone": "13800138000",
        "message": "发送成功"
      },
      {
        "tenant_id": 2,
        "success": true,
        "tenant_name": "李四",
        "tenant_phone": "13900139000",
        "message": "发送成功"
      }
    ]
  }
}
```

#### 4.18.2 发送单个通知

```http
POST /api/notifications/send
Authorization: Bearer <token>
```

**权限要求：** edit 权限

**请求体：**
```json
{
  "tenant_id": 1,
  "message": "您的合同将于 30 天后到期，如需续租请及时联系。"
}
```

**响应：**
```json
{
  "success": true,
  "message": "通知发送成功",
  "data": {
    "tenant_id": 1,
    "tenant_name": "王小明",
    "tenant_phone": "13800138000",
    "message": "您的合同将于 30 天后到期...",
    "sent_at": "2024-01-01T12:00:00",
    "active_contracts_count": 1
  }
}
```

> **注意：** 
> - 通知内容不能超过 500 个字符
> - 发送通知时会记录操作日志
> - 当前为模拟发送，实际项目中可对接短信/邮件服务

---

## 5. 数据模型参考

详细的数据模型设计请参考 [DATABASE_MODELS.md](DATABASE_MODELS.md) 文件。

### 5.1 核心模型概览

| 模型名称 | 表名 | 描述 |
|---------|------|------|
| User | users | 用户表（管理员、普通员工） |
| Landlord | landlords | 房东表 |
| House | houses | 房源表 |
| Room | rooms | 房间表 |
| Tenant | tenants | 租客表 |
| Contract | contracts | 租赁合同表 |
| LandlordContract | landlord_contracts | 承包合同表 |
| Payment | payments | 支付记录表 |
| Media | media | 多媒体文件表 |

### 5.2 枚举值参考

#### 用户状态 (User.status)
- `active` - 在职
- `resigned` - 离职
- `disabled` - 禁用

#### 用户角色 (User.role)
- `admin` - 管理员
- `staff` - 员工

#### 房源状态 (House.status)
- `available` - 空闲
- `rented` - 已租
- `maintenance` - 维护中
- `partially_rented` - 部分出租

#### 租赁类型 (House.rental_type)
- `whole` - 整租
- `shared` - 合租

#### 房间状态 (Room.status)
- `available` - 空闲
- `rented` - 已租
- `maintenance` - 维护中

#### 租客状态 (Tenant.status)
- `pending` - 待审核
- `active` - 在租
- `expired` - 已退租
- `blacklisted` - 黑名单

#### 房东状态 (Landlord.status)
- `active` - 正常
- `inactive` - 停用
- `blacklisted` - 黑名单

#### 合同状态 (Contract.status / LandlordContract.status)
- `draft` - 草稿
- `active` - 生效中
- `expired` - 已过期
- `terminated` - 已终止
- `renewed` - 已续签

#### 押金状态 (Contract.deposit_status)
- `pending` - 待支付
- `paid` - 已支付
- `transferred` - 已转移
- `refunded` - 已退款

#### 支付状态 (Payment.status)
- `pending` - 待支付
- `paid` - 已支付
- `overdue` - 逾期
- `partial` - 部分支付
- `refunded` - 已退款

#### 支付类型 (Payment.payment_type)
- `rent` - 租金
- `deposit` - 押金
- `utility` - 水电费
- `other` - 其他

#### 押金退款状态 (DepositRefund.status)
- `pending` - 待处理
- `processed` - 已处理
- `completed` - 已完成
- `cancelled` - 已取消

#### 扣款类型 (DepositRefund.deduction_type)
- `unpaid_rent` - 未付租金
- `unpaid_utilities` - 未付水电费
- `late_fees` - 滞纳金
- `damage_compensation` - 损坏赔偿
- `other` - 其他扣款

#### 支付方式 (Payment.payment_method)
- `cash` - 现金
- `bank` - 银行转账
- `wechat` - 微信
- `alipay` - 支付宝

---

## 6. 错误码说明

### 6.1 通用错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未认证或 Token 无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如唯一性约束） |
| 422 | 数据验证失败 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### 6.2 业务错误示例

**参数验证错误：**
```json
{
  "error": "validation_error",
  "message": "数据验证失败",
  "details": {
    "phone": ["手机号格式不正确"],
    "email": ["邮箱格式不正确"]
  }
}
```

**唯一性冲突：**
```json
{
  "error": "conflict",
  "message": "用户名已存在"
}
```

**权限不足：**
```json
{
  "error": "forbidden",
  "message": "您没有权限执行此操作"
}
```

**乐观锁冲突：**
```json
{
  "error": "version_conflict",
  "message": "合同已被其他用户修改，请刷新后重试",
  "current_version": 2,
  "expected_version": 1
}
```

**押金状态转换错误：**
```json
{
  "error": "invalid_transition",
  "message": "押金状态不能从 '已退款' 转换为 '已支付'"
}
```

**退款完成条件不满足：**
```json
{
  "error": "cannot_complete",
  "message": "只有已处理状态的退款才能完成"
}
```

**资源不存在：**
```json
{
  "error": "not_found",
  "message": "房源不存在"
}
```

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.2.0 | 2024-03-10 | 新增模块：押金退款模块（4.17）、通知管理模块（4.18）；新增功能：合同乐观锁机制、合同押金状态管理、押金状态转换接口；更新枚举值：押金状态、退款状态、扣款类型；新增错误码：乐观锁冲突、状态转换错误 |
| 1.1.0 | 2024-03-05 | 新增接口：认证模块锁定/解锁用户账户、统计模块仪表盘/收入/入住率/即将到期合同、备份模块更新设置、审计模块开关状态；修正监控模块URL路径；补充租客pending状态和合同renewed状态 |
| 1.0.0 | 2024-01-01 | 初始版本 |

---

> **注意：** 本文档基于后端代码自动生成，如有疑问请参考后端源码或联系后端开发人员。
