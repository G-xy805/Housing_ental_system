# 房东管理 API 文档

## 概述

房东管理 API 提供了完整的房东 CRUD 操作、搜索筛选、房源关联、合同关联等功能。所有接口仅限内部员工访问，需要使用 JWT Token 进行认证。

**基础 URL**: `http://localhost:5000/api/landlords`

**认证方式**: JWT Bearer Token

**请求头**:
```
Authorization: Bearer <your_token>
Content-Type: application/json
```

---

## API 接口列表

### 1. 获取房东列表

**接口**: `GET /api/landlords`

**权限**: 登录员工

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| per_page | int | 否 | 20 | 每页数量（最大 100） |
| keyword | string | 否 | - | 关键词搜索（姓名、手机号、身份证号） |
| name | string | 否 | - | 姓名搜索 |
| phone | string | 否 | - | 手机号搜索 |
| id_card | string | 否 | - | 身份证号搜索 |
| status | string | 否 | - | 状态筛选（active/inactive/blacklisted） |
| order_by | string | 否 | created_at | 排序字段（created_at/updated_at/name） |
| order | string | 否 | desc | 排序方向（asc/desc） |

**响应示例**:
```json
{
  "success": true,
  "message": "获取房东列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "张三",
        "phone": "13800138000",
        "bank_card": "6222001234567890123",
        "bank_name": "中国工商银行北京分行",
        "property_cert_no": "京房权证朝私字第 123456 号",
        "address": "北京市朝阳区某某小区 3 号楼",
        "status": "active",
        "remark": "备注",
        "houses_count": 5,
        "contracts_count": 2,
        "owner_name": "管理员",
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 50,
      "pages": 3,
      "has_next": true,
      "has_prev": false,
      "next_num": 2,
      "prev_num": null
    }
  }
}
```

---

### 2. 获取房东详情

**接口**: `GET /api/landlords/:id`

**权限**: 登录员工

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房东 ID |

**响应示例**:
```json
{
  "success": true,
  "message": "获取房东详情成功",
  "data": {
    "id": 1,
    "name": "张三",
    "phone": "13800138000",
    "bank_card": "6222001234567890123",
    "bank_name": "中国工商银行北京分行",
    "property_cert_no": "京房权证朝私字第 123456 号",
    "address": "北京市朝阳区某某小区 3 号楼",
    "status": "active",
    "remark": "备注",
    "houses_count": 5,
    "contracts_count": 2,
    "owner_name": "管理员",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  }
}
```

---

### 3. 创建房东

**接口**: `POST /api/landlords`

**权限**: 登录员工（create 权限）

**请求体**:
```json
{
  "name": "张三",
  "id_card": "110101199001011234",
  "phone": "13800138000",
  "bank_card": "6222001234567890123",
  "bank_name": "中国工商银行北京分行",
  "property_cert_no": "京房权证朝私字第 123456 号",
  "address": "北京市朝阳区某某小区 3 号楼",
  "remark": "备注信息"
}
```

**字段验证**:
- `name`: 必填，最多 50 个字符
- `id_card`: 必填，18 位身份证号（最后一位可以是 X）
- `phone`: 必填，11 位中国大陆手机号（以 1 开头，第二位是 3-9 之间）
- `bank_card`: 可选，银行卡号必须是数字
- `bank_name`: 可选，最多 100 个字符
- `property_cert_no`: 可选，最多 50 个字符
- `address`: 可选，最多 255 个字符
- `remark`: 可选

**业务逻辑**:
1. 验证身份证号格式
2. 验证手机号格式
3. 检查身份证号是否已存在（通过身份证号哈希去重）
4. 创建房东并自动生成身份证号哈希
5. 记录操作日志

**响应示例**:
```json
{
  "success": true,
  "message": "房东创建成功",
  "data": {
    "id": 1,
    "name": "张三",
    "phone": "13800138000",
    ...
  }
}
```

---

### 4. 更新房东信息

**接口**: `PUT /api/landlords/:id`

**权限**: 登录员工（edit 权限）

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房东 ID |

**请求体** (仅包含需要更新的字段):
```json
{
  "name": "新的姓名",
  "phone": "新的手机号",
  "bank_card": "新的银行卡号",
  "bank_name": "新的开户行",
  "status": "active",
  "remark": "新的备注"
}
```

**业务逻辑**:
1. 验证房东是否存在
2. 验证数据格式
3. 检查身份证号是否重复（排除自己）
4. 更新房东信息
5. 记录操作日志

**响应示例**:
```json
{
  "success": true,
  "message": "房东信息更新成功",
  "data": {
    ...
  }
}
```

---

### 5. 删除房东

**接口**: `DELETE /api/landlords/:id`

**权限**: 仅管理员（admin 权限）

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房东 ID |

**业务逻辑**:
1. 检查房东是否存在
2. 检查是否有房源（有房源不能删除）
3. 检查是否有承包合同（有合同不能删除）
4. 删除房东
5. 记录操作日志

**响应示例**:
```json
{
  "success": true,
  "message": "房东删除成功"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "bad_request",
    "message": "房东名下有 5 个房源，无法删除"
  }
}
```

---

### 6. 获取房东名下所有房源

**接口**: `GET /api/landlords/:id/houses`

**权限**: 登录员工

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房东 ID |

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| status | string | 否 | - | 房源状态筛选（available/rented/maintenance/partially_rented） |
| rental_type | string | 否 | - | 租赁类型筛选（whole/shared） |
| page | int | 否 | 1 | 页码 |
| per_page | int | 否 | 20 | 每页数量（最大 100） |

**响应示例**:
```json
{
  "success": true,
  "message": "获取房东房源列表成功",
  "data": {
    "landlord_id": 1,
    "landlord_name": "张三",
    "houses": [
      {
        "id": 1,
        "title": "科技园区合租公寓",
        "address": "中关村大街 1 号",
        "rental_type": "shared",
        "rent_price": 5000.0,
        "status": "partially_rented",
        ...
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 5,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

### 7. 获取房东的所有承包合同

**接口**: `GET /api/landlords/:id/contracts`

**权限**: 登录员工

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房东 ID |

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| status | string | 否 | - | 合同状态筛选（draft/active/expired/terminated） |
| include_expired | boolean | 否 | true | 是否包含已过期合同 |
| page | int | 否 | 1 | 页码 |
| per_page | int | 否 | 20 | 每页数量（最大 100） |

**响应示例**:
```json
{
  "success": true,
  "message": "获取房东合同列表成功",
  "data": {
    "landlord_id": 1,
    "landlord_name": "张三",
    "contracts": [
      {
        "id": 1,
        "contract_no": "LC202401011234",
        "title": "平台与王房东承包合同",
        "contract_amount": 100000.0,
        "service_fee_rate": 5.0,
        "status": "active",
        "start_date": "2024-01-01",
        "end_date": "2025-01-01",
        "house_ids": [1, 2, 3],
        ...
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 2,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

### 8. 获取房东统计信息

**接口**: `GET /api/landlords/stats`

**权限**: 登录员工

**响应示例**:
```json
{
  "success": true,
  "message": "获取房东统计信息成功",
  "data": {
    "total": 100,
    "by_status": {
      "active": 80,
      "inactive": 15,
      "blacklisted": 5
    },
    "with_houses": 60,
    "with_contracts": 50
  }
}
```

**统计字段说明**:
- `total`: 房东总数
- `by_status`: 按状态统计（active/inactive/blacklisted）
- `with_houses`: 有房源的房东数量
- `with_contracts`: 有承包合同的房东数量

---

### 9. 高级搜索房东

**接口**: `GET /api/landlords/search`

**权限**: 登录员工

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| name | string | 否 | - | 姓名搜索 |
| phone | string | 否 | - | 手机号搜索 |
| id_card | string | 否 | - | 身份证号搜索 |
| city | string | 否 | - | 城市（通过房源地址搜索） |
| status | string | 否 | - | 状态筛选 |
| page | int | 否 | 1 | 页码 |
| per_page | int | 否 | 20 | 每页数量（最大 100） |

**响应示例**:
```json
{
  "success": true,
  "message": "搜索房东成功",
  "data": {
    "items": [...],
    "pagination": {...}
  }
}
```

---

## 业务逻辑实现

### 1. 身份证号验证

```python
# 18 位身份证号验证规则
- 长度为 18 位
- 前 17 位必须是数字
- 第 18 位可以是数字或 X/x
```

### 2. 手机号验证

```python
# 中国大陆手机号验证规则
- 11 位数字
- 以 1 开头
- 第二位是 3-9 之间的数字
```

### 3. 身份证号去重

使用 SHA-256 算法对身份证号进行哈希，通过哈希值判断是否重复：
```python
import hashlib
id_card_hash = hashlib.sha256(id_card.encode()).hexdigest()
```

### 4. 房东状态

| 状态 | 说明 | 业务影响 |
|------|------|----------|
| active | 正常 | 可以正常创建房源和合同 |
| inactive | 停用 | 不能创建新的房源和合同 |
| blacklisted | 黑名单 | 禁止合作 |

### 5. 删除限制

房东有以下关联时不能删除：
- 名下有房源
- 有承包合同

---

## 权限控制说明

### 1. 认证要求
- 所有接口都需要 JWT Token 认证
- 使用 `@login_required` 装饰器验证用户登录状态
- Token 从 Authorization Header 中获取：`Authorization: Bearer <token>`

### 2. 权限级别

| 接口 | 权限要求 | 装饰器 |
|------|---------|--------|
| GET /api/landlords | 登录员工 | @login_required |
| GET /api/landlords/:id | 登录员工 | @login_required |
| POST /api/landlords | create 权限 | @login_required + @permission_required('create') |
| PUT /api/landlords/:id | edit 权限 | @login_required + @permission_required('edit') |
| DELETE /api/landlords/:id | admin 权限 | @admin_required |
| GET /api/landlords/:id/houses | 登录员工 | @login_required |
| GET /api/landlords/:id/contracts | 登录员工 | @login_required |
| GET /api/landlords/stats | 登录员工 | @login_required |
| GET /api/landlords/search | 登录员工 | @login_required |

### 3. 用户角色权限

根据 [`User`](file:///d:/Pro/Housing_ental_system/app/models/user.py) 模型中的 `has_permission` 方法：

- **admin**: 所有权限（view, create, edit, delete）
- **staff**: 查看、创建、编辑权限，无删除权限

### 4. 操作日志

所有房东操作都会记录日志：
- 创建房东：记录房东 ID、姓名
- 更新房东：记录房东 ID、姓名
- 删除房东：记录房东 ID、姓名（仅管理员）
- 访问房东详情：记录访问的房东 ID

---

## 错误响应

### 常见错误码

| HTTP 状态码 | 错误码 | 说明 |
|------------|--------|------|
| 400 | bad_request | 请求参数错误、数据验证失败 |
| 401 | unauthorized | 未授权访问 |
| 401 | token_expired | Token 过期 |
| 401 | token_invalid | Token 无效 |
| 403 | forbidden | 没有权限 |
| 404 | not_found | 房东不存在 |
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

### 常见错误信息

| 错误信息 | 说明 |
|----------|------|
| 身份证号不能为空 | 缺少必填字段 |
| 身份证号必须是 18 位 | 身份证号格式错误 |
| 身份证号前 17 位必须是数字 | 身份证号格式错误 |
| 身份证号最后一位必须是数字或 X | 身份证号格式错误 |
| 手机号不能为空 | 缺少必填字段 |
| 手机号格式不正确，应为 11 位中国大陆手机号 | 手机号格式错误 |
| 该身份证号已登记在其他房东名下 | 身份证号重复 |
| 房东不存在 | 房东 ID 不存在 |
| 房东名下有 X 个房源，无法删除 | 删除限制 |
| 房东有 X 个承包合同，无法删除 | 删除限制 |

---

## 数据模型

### Landlord 模型

主要字段：
- `id`: 主键
- `name`: 姓名
- `id_card`: 身份证号（加密存储）
- `id_card_hash`: 身份证号哈希（用于去重验证）
- `phone`: 联系电话
- `bank_card`: 银行卡号
- `bank_name`: 开户行名称
- `property_cert_no`: 房产证编号
- `address`: 房产地址
- `status`: 房东状态（active/inactive/blacklisted）
- `remark`: 备注

### 关联关系
- `houses`: 房东拥有的房源列表
- `contracts`: 房东的承包合同列表

### 业务方法
- `set_id_card(id_card_number)`: 设置身份证号并生成哈希
- `verify_id_card(id_card_number)`: 验证身份证号是否匹配
- `to_dict(include_details)`: 转换为字典（自动移除敏感字段）

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

# 创建房东
create_data = {
    'name': '张三',
    'id_card': '110101199001011234',
    'phone': '13800138000',
    'bank_card': '6222001234567890123',
    'bank_name': '中国工商银行北京分行',
    'property_cert_no': '京房权证朝私字第 123456 号',
    'address': '北京市朝阳区某某小区 3 号楼',
    'remark': '优质房东'
}

response = requests.post(
    'http://localhost:5000/api/landlords',
    headers=headers,
    json=create_data
)

if response.status_code == 201:
    landlord = response.json()['data']
    print(f"创建成功，房东 ID: {landlord['id']}")
else:
    print(f"创建失败：{response.json()['error']['message']}")

# 获取房东列表
response = requests.get(
    'http://localhost:5000/api/landlords',
    headers=headers,
    params={'page': 1, 'per_page': 20}
)

if response.status_code == 200:
    data = response.json()['data']
    print(f"共 {data['pagination']['total']} 个房东")
    for item in data['items']:
        print(f"- {item['name']}: {item['phone']}")
else:
    print(f"获取失败：{response.json()['error']['message']}")

# 获取房东详情
response = requests.get(
    f'http://localhost:5000/api/landlords/1',
    headers=headers
)

if response.status_code == 200:
    landlord = response.json()['data']
    print(f"房东详情：{landlord['name']}")
    print(f"房源数量：{landlord['houses_count']}")
    print(f"合同数量：{landlord['contracts_count']}")
else:
    print(f"获取失败：{response.json()['error']['message']}")

# 获取房东的房源
response = requests.get(
    f'http://localhost:5000/api/landlords/1/houses',
    headers=headers,
    params={'page': 1, 'per_page': 20}
)

if response.status_code == 200:
    data = response.json()['data']
    print(f"房东 {data['landlord_name']} 有 {len(data['houses'])} 个房源")
else:
    print(f"获取失败：{response.json()['error']['message']}")
```

---

## 注意事项

1. **身份证号安全**: 
   - 身份证号使用 SHA-256 哈希存储，支持去重验证
   - API 响应中自动过滤身份证号和银行卡号等敏感字段
   - 仅详细信息接口在必要时返回脱敏后的数据

2. **数据一致性**: 
   - 创建房东前确保身份证号和手机号格式正确
   - 删除房东前检查是否有房源和合同关联

3. **权限控制**: 
   - 仅管理员可以删除房东
   - 普通员工可以创建和编辑房东信息

4. **操作日志**: 
   - 所有操作都会记录日志，便于审计追踪

5. **分页查询**: 
   - 列表接口支持分页，默认每页 20 条，最大 100 条
   - 使用 page 和 per_page 参数控制分页

6. **搜索功能**: 
   - 支持关键词搜索（姓名、手机号、身份证号）
   - 支持按城市搜索（通过房源地址关联）

7. **状态管理**: 
   - 房东状态影响业务操作，停用的房东不能创建新的房源和合同
   - 黑名单房东禁止合作

---

## 相关文档

- [数据库模型设计](DATABASE_MODELS.md) - Landlord 模型详细说明
- [承包合同管理 API](landlord_contracts_api_docs.md) - 承包合同相关接口
- [房源 API](houses_api_docs.md) - 房源管理接口（包含房东关联）
