# 承包合同管理 API 文档

## 概述

承包合同管理 API 提供了完整的承包合同 CRUD 操作、合同状态管理、到期提醒等功能。所有接口仅限内部员工访问，需要使用 JWT Token 进行认证。

**基础 URL**: `http://localhost:5000/api/landlord_contracts`

**认证方式**: JWT Bearer Token

**请求头**:
```
Authorization: Bearer <your_token>
Content-Type: application/json
```

---

## API 接口列表

### 1. 获取承包合同列表

**接口**: `GET /api/landlord_contracts`

**权限**: 登录员工

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| per_page | int | 否 | 20 | 每页数量 (最大 100) |
| keyword | string | 否 | - | 关键词搜索（合同编号、标题） |
| contract_no | string | 否 | - | 合同编号搜索 |
| status | string | 否 | - | 状态筛选 (draft/active/expired/terminated)，多个用逗号分隔 |
| landlord_id | int | 否 | - | 房东 ID 筛选 |
| is_expiring | boolean | 否 | false | 是否查询即将到期合同 |
| order_by | string | 否 | created_at | 排序字段 (created_at/start_date/end_date) |
| order | string | 否 | desc | 排序方向 (asc/desc) |

**响应示例**:
```json
{
  "success": true,
  "message": "获取承包合同列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "contract_no": "LC202401011234",
        "title": "承包合同",
        "landlord_id": 1,
        "house_ids": [1, 2, 3],
        "contract_amount": 100000.0,
        "service_fee_rate": 5.0,
        "status": "active",
        "start_date": "2024-01-01",
        "end_date": "2025-01-01",
        "is_expired": false,
        "days_until_expiry": 300
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 50,
      "pages": 3,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

### 2. 获取承包合同详情

**接口**: `GET /api/landlord_contracts/<id>`

**权限**: 登录员工

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 合同 ID |

**响应示例**:
```json
{
  "success": true,
  "message": "获取承包合同详情成功",
  "data": {
    "id": 1,
    "contract_no": "LC202401011234",
    "title": "承包合同",
    "description": "合同描述",
    "landlord_id": 1,
    "house_ids": [1, 2, 3],
    "contract_amount": 100000.0,
    "service_fee_rate": 5.0,
    "minimum_fee": 5000.0,
    "payment_cycle": 3,
    "status": "active",
    "start_date": "2024-01-01",
    "end_date": "2025-01-01",
    "contract_file": "/uploads/contracts/xxx.pdf",
    "remark": "备注",
    "landlord": {
      "id": 1,
      "name": "张三",
      "phone": "13800138000",
      "status": "active"
    },
    "houses": [
      {
        "id": 1,
        "title": "房源标题",
        "address": "房源地址",
        "rental_type": "整租",
        "rent_price": 5000.0
      }
    ],
    "contract_term_months": 12.0,
    "service_fee": 5000.0,
    "is_expired": false,
    "days_until_expiry": 300
  }
}
```

---

### 3. 创建承包合同

**接口**: `POST /api/landlord_contracts`

**权限**: 登录员工 (create 权限)

**请求体**:
```json
{
  "title": "承包合同",
  "landlord_id": 1,
  "house_ids": [1, 2, 3],
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "contract_amount": 100000.0,
  "service_fee_rate": 5.0,
  "minimum_fee": 5000.0,
  "payment_cycle": 3,
  "description": "合同描述",
  "remark": "备注信息"
}
```

**字段验证**:
- `title`: 必填，最多 100 个字符
- `landlord_id`: 必填，有效的房东 ID
- `house_ids`: 必填，房源 ID 数组，支持多个房源
- `start_date`: 必填，格式 YYYY-MM-DD
- `end_date`: 必填，格式 YYYY-MM-DD，必须晚于 start_date
- `contract_amount`: 必填，必须大于 0
- `service_fee_rate`: 必填，0-100 之间
- `minimum_fee`: 可选，不能为负数
- `payment_cycle`: 可选，默认 1，必须大于 0
- `description`: 可选
- `remark`: 可选

**业务逻辑**:
1. 验证房东是否存在
2. 验证所有房源 ID 是否存在
3. 检查房源是否已被其他生效中的承包合同占用
4. 自动生成合同编号（格式：LC + 年月日 + 4 位随机数）
5. 创建合同，初始状态为 draft

**响应示例**:
```json
{
  "success": true,
  "message": "承包合同创建成功",
  "data": {
    "id": 1,
    "contract_no": "LC202401011234",
    ...
  }
}
```

---

### 4. 更新承包合同

**接口**: `PUT /api/landlord_contracts/<id>`

**权限**: 登录员工 (edit 权限)

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 合同 ID |

**请求体** (仅包含需要更新的字段):
```json
{
  "title": "新的合同标题",
  "contract_amount": 120000.0,
  "service_fee_rate": 6.0,
  "description": "新的描述"
}
```

**业务逻辑**:
1. 已生效 (active) 的合同不能修改关键字段：landlord_id, house_ids, start_date, end_date
2. 只能更新非关键字段

**响应示例**:
```json
{
  "success": true,
  "message": "承包合同更新成功",
  "data": {
    ...
  }
}
```

---

### 5. 删除承包合同

**接口**: `DELETE /api/landlord_contracts/<id>`

**权限**: 登录员工 (delete 权限)

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 合同 ID |

**业务逻辑**:
1. 只能删除草稿 (draft) 状态的合同
2. 已生效的合同需要先终止才能删除

**响应示例**:
```json
{
  "success": true,
  "message": "承包合同删除成功"
}
```

---

### 6. 激活承包合同

**接口**: `POST /api/landlord_contracts/<id>/activate`

**权限**: 登录员工 (edit 权限)

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 合同 ID |

**业务逻辑**:
1. 只有草稿 (draft) 状态的合同才能激活
2. 激活后状态变为 active

**响应示例**:
```json
{
  "success": true,
  "message": "承包合同激活成功",
  "data": {
    ...
  }
}
```

---

### 7. 终止承包合同

**接口**: `POST /api/landlord_contracts/<id>/terminate`

**权限**: 登录员工 (edit 权限)

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 合同 ID |

**请求体**:
```json
{
  "reason": "终止原因",
  "terminate_date": "2024-06-01",
  "settlement_amount": 5000
}
```

**业务逻辑**:
1. 只有生效中 (active) 的合同才能终止
2. terminate_date 默认为今天
3. 更新合同状态为 terminated
4. 记录终止原因到备注

**响应示例**:
```json
{
  "success": true,
  "message": "承包合同终止成功",
  "data": {
    ...
  }
}
```

---

### 8. 合同续签

**接口**: `POST /api/landlord_contracts/<id>/renew`

**权限**: 登录员工 (edit 权限)

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 合同 ID |

**请求体**:
```json
{
  "end_date": "2026-01-01",
  "contract_amount": 120000.0,
  "service_fee_rate": 6.0,
  "remark": "续签备注"
}
```

**业务逻辑**:
1. 只有生效中 (active) 或已过期 (expired) 的合同才能续签
2. 创建新合同，从原合同结束日期开始
3. 原合同标记为 expired
4. 新合同自动生成合同编号

**响应示例**:
```json
{
  "success": true,
  "message": "承包合同续签成功",
  "data": {
    "old_contract": {...},
    "new_contract": {...}
  }
}
```

---

### 9. 获取即将到期的合同

**接口**: `GET /api/landlord_contracts/expiring`

**权限**: 登录员工

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| days | int | 否 | 30 | 天数范围 |
| include_expired | boolean | 否 | false | 是否包含已过期合同 |

**业务逻辑**:
1. 查询状态为 active 且结束日期在指定范围内的合同
2. 按结束日期升序排序

**响应示例**:
```json
{
  "success": true,
  "message": "获取即将到期承包合同成功",
  "data": {
    "expiring_contracts": [
      {
        "id": 1,
        "contract_no": "LC202401011234",
        "end_date": "2024-03-15",
        "days_until_expiry": 13
      }
    ],
    "total_expiring": 1,
    "expired_contracts": [],
    "total_expired": 0
  }
}
```

---

### 10. 获取承包合同统计信息

**接口**: `GET /api/landlord_contracts/stats`

**权限**: 登录员工

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| landlord_id | int | 否 | - | 房东 ID（筛选特定房东） |

**响应示例**:
```json
{
  "success": true,
  "message": "获取承包合同统计信息成功",
  "data": {
    "total": 100,
    "by_status": {
      "draft": 5,
      "active": 60,
      "expired": 20,
      "terminated": 10
    },
    "expiring_soon": 10,
    "total_contract_amount": 5000000,
    "total_service_fee": 250000
  }
}
```

---

## 业务逻辑实现

### 1. 合同编号生成
- 格式：`LC` + 年月日 + 4 位随机数
- 示例：`LC202401011234`
- 保证唯一性

### 2. 房源占用检查
- 创建合同时检查房源是否已被其他生效中的合同占用
- 避免同一房源被多个合同同时承包

### 3. 服务费计算
```python
服务费 = 合同金额 × (服务费率 / 100)
实际服务费 = max(服务费，最低服务费)  # 如果设置了最低服务费
```

### 4. 合同状态流转
```
draft (草稿) 
  → activate (激活) → active (生效中)
  → delete (删除)
  
active (生效中)
  → terminate (终止) → terminated (已终止)
  → expire (自动过期) → expired (已过期)
  → renew (续签) → expired (已过期)

expired (已过期)
  → renew (续签) → 创建新合同
```

### 5. 日期验证
- 结束日期必须晚于开始日期
- 续签时新结束日期必须晚于原结束日期

### 6. 合同期限计算
```python
合同期限 (月) = (结束日期 - 开始日期).days / 30
```

---

## 权限控制说明

### 1. 认证要求
- 所有接口都需要 JWT Token 认证
- 使用 `@login_required` 装饰器验证用户登录状态
- Token 从 Authorization Header 中获取：`Authorization: Bearer <token>`

### 2. 权限级别

| 接口 | 权限要求 | 装饰器 |
|------|---------|--------|
| GET /api/landlord_contracts | 登录员工 | @login_required |
| GET /api/landlord_contracts/:id | 登录员工 | @login_required |
| POST /api/landlord_contracts | create 权限 | @login_required + @permission_required('create') |
| PUT /api/landlord_contracts/:id | edit 权限 | @login_required + @permission_required('edit') |
| DELETE /api/landlord_contracts/:id | delete 权限 | @login_required + @permission_required('delete') |
| POST /api/landlord_contracts/:id/activate | edit 权限 | @login_required + @permission_required('edit') |
| POST /api/landlord_contracts/:id/terminate | edit 权限 | @login_required + @permission_required('edit') |
| POST /api/landlord_contracts/:id/renew | edit 权限 | @login_required + @permission_required('edit') |
| GET /api/landlord_contracts/expiring | 登录员工 | @login_required |
| GET /api/landlord_contracts/stats | 登录员工 | @login_required |

### 3. 用户角色权限
根据 [`User`](file:///d:/Pro/Housing_ental_system/app/models/user.py) 模型中的 `has_permission` 方法：

- **admin**: 所有权限 (view, create, edit, delete)
- **staff**: 根据配置可能有部分权限

### 4. 权限验证流程
1. 解析 Authorization Header 中的 Token
2. 验证 Token 有效性（是否过期、是否被篡改）
3. 从数据库获取用户信息
4. 检查用户是否有指定权限
5. 无权限则返回 403 Forbidden

---

## 错误响应

### 常见错误码

| HTTP 状态码 | 错误码 | 说明 |
|------------|--------|------|
| 400 | bad_request | 请求参数错误 |
| 401 | unauthorized | 未授权访问 |
| 401 | token_expired | Token 过期 |
| 401 | token_invalid | Token 无效 |
| 403 | forbidden | 没有权限 |
| 404 | not_found | 资源不存在 |
| 422 | validation_error | 参数验证失败 |
| 500 | internal_server_error | 服务器内部错误 |

### 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "error_code",
    "message": "错误描述信息"
  },
  "data": null,
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## 数据模型

### LandlordContract 模型

主要字段：
- `contract_no`: 合同编号（唯一）
- `title`: 合同标题
- `description`: 合同描述
- `landlord_id`: 房东 ID（外键）
- `house_ids`: 房源 ID 列表（JSON）
- `start_date`: 开始日期
- `end_date`: 结束日期
- `contract_amount`: 合同金额
- `service_fee_rate`: 服务费率
- `minimum_fee`: 最低服务费
- `payment_cycle`: 付款周期（月数）
- `status`: 合同状态（draft/active/expired/terminated）
- `contract_file`: 合同文件路径
- `remark`: 备注

### 关联关系
- `landlord`: 关联 Landlord 模型
- `houses`: 通过 house_ids 关联多个 House 模型

---

## 使用示例

### Python 示例

```python
import requests

# 登录获取 Token
login_response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = login_response.json()['data']['access_token']

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# 创建承包合同
create_data = {
    'title': '承包合同',
    'landlord_id': 1,
    'house_ids': [1, 2],
    'start_date': '2024-01-01',
    'end_date': '2025-01-01',
    'contract_amount': 100000.0,
    'service_fee_rate': 5.0
}

response = requests.post(
    'http://localhost:5000/api/landlord_contracts',
    headers=headers,
    json=create_data
)

if response.status_code == 201:
    contract = response.json()['data']
    print(f"创建成功，合同编号：{contract['contract_no']}")
else:
    print(f"创建失败：{response.json()['error']['message']}")
```

---

## 注意事项

1. **数据一致性**: 创建合同前确保房东和房源已存在
2. **房源占用**: 同一房源不能同时被多个生效中的合同承包
3. **状态管理**: 只能删除草稿状态的合同，已生效的合同需要先终止
4. **日期格式**: 所有日期字段使用 YYYY-MM-DD 格式
5. **金额精度**: 金额字段保留两位小数
6. **权限控制**: 确保用户有相应权限才能执行操作
7. **Token 有效期**: Token 过期需要重新登录获取新 Token
