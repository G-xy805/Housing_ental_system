# 房源 API 文档

## 概述

房源管理 API 提供房源的 CRUD 操作、房间管理、多媒体管理等功能。系统支持**内部接口**和**外部接口**两种模式：

- **内部接口**：供公司内部员工使用，返回完整信息（包含房东信息、联系信息等）
- **外部接口**：供租客/公众使用，返回脱敏信息（隐藏房东信息、联系信息等）

**基础 URL**: 
- 内部接口：`http://localhost:5000/api/houses`
- 外部接口：`http://localhost:5000/api/public/houses`

**认证方式**: 
- 内部接口：JWT Bearer Token
- 外部接口：无需认证（公开访问）

---

## 内部接口（员工使用）

### 1. 获取房源列表

**接口**: `GET /api/houses`

**权限**: 登录员工

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| per_page | int | 否 | 20 | 每页数量（最大 100） |
| keyword | string | 否 | - | 关键词搜索（标题、地址） |
| city | string | 否 | - | 城市筛选 |
| district | string | 否 | - | 区县筛选 |
| status | string | 否 | - | 状态筛选（available/rented/maintenance/partially_rented） |
| rental_type | string | 否 | - | 租赁类型（whole/shared） |
| min_price | float | 否 | - | 最低租金 |
| max_price | float | 否 | - | 最高租金 |
| order_by | string | 否 | created_at | 排序字段 |
| order | string | 否 | desc | 排序方向 |

**响应示例**:
```json
{
  "success": true,
  "message": "获取房源列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "科技园区合租公寓",
        "description": "靠近地铁站，交通便利",
        "city": "北京市",
        "district": "海淀区",
        "address": "中关村大街 1 号",
        "area": 120.5,
        "room_count": 3,
        "rent_price": 12000.0,
        "deposit": 12000.0,
        "rental_type": "shared",
        "status": "partially_rented",
        "owner_name": "李员工",
        "landlord_name": "王房东",
        "landlord_phone": "13700137000",
        "contact_name": "王房东",
        "contact_phone": "13700137000",
        "contact_wechat": "wang123",
        "room_count_actual": 3,
        "available_rooms": [],
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
      "has_prev": false
    }
  }
}
```

---

### 2. 获取房源详情（内部）

**接口**: `GET /api/houses/:id`

**权限**: 登录员工

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房源 ID |

**响应示例**:
```json
{
  "success": true,
  "message": "获取房源详情成功",
  "data": {
    "id": 1,
    "title": "科技园区合租公寓",
    "description": "靠近地铁站，交通便利",
    "province": "北京市",
    "city": "北京市",
    "district": "海淀区",
    "address": "中关村大街 1 号",
    "latitude": 39.9042,
    "longitude": 116.4074,
    "area": 120.5,
    "room_count": 3,
    "hall_count": 1,
    "bathroom_count": 2,
    "floor": "中层",
    "total_floors": 18,
    "rent_price": 12000.0,
    "deposit": 12000.0,
    "payment_method": "押一付三",
    "rental_type": "shared",
    "status": "partially_rented",
    "facilities": {
      "wifi": true,
      "ac": true,
      "heater": true,
      "kitchen": true
    },
    "owner_name": "李员工",
    "landlord": {
      "id": 1,
      "name": "王房东",
      "phone": "13700137000",
      "bank_card": "6222001234567890123",
      "bank_name": "中国工商银行北京分行",
      "property_cert_no": "京房权证朝私字第 123456 号"
    },
    "contact_name": "王房东",
    "contact_phone": "13700137000",
    "contact_wechat": "wang123",
    "rooms": [
      {
        "id": 1,
        "room_number": "101",
        "name": "主卧",
        "area": 25.0,
        "direction": "南",
        "rent_price": 5000.0,
        "status": "rented"
      },
      {
        "id": 2,
        "room_number": "102",
        "name": "次卧 A",
        "area": 18.0,
        "direction": "北",
        "rent_price": 3800.0,
        "status": "available"
      }
    ],
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  }
}
```

---

### 3. 创建房源

**接口**: `POST /api/houses`

**权限**: 登录员工（create 权限）

**请求体**:
```json
{
  "title": "科技园区合租公寓",
  "description": "靠近地铁站，交通便利",
  "province": "北京市",
  "city": "北京市",
  "district": "海淀区",
  "address": "中关村大街 1 号",
  "latitude": 39.9042,
  "longitude": 116.4074,
  "area": 120.5,
  "room_count": 3,
  "hall_count": 1,
  "bathroom_count": 2,
  "floor": "中层",
  "total_floors": 18,
  "rent_price": 12000.0,
  "deposit": 12000.0,
  "payment_method": "押一付三",
  "rental_type": "shared",
  "landlord_id": 1,
  "contact_name": "王房东",
  "contact_phone": "13700137000",
  "contact_wechat": "wang123",
  "facilities": {
    "wifi": true,
    "ac": true,
    "heater": true,
    "kitchen": true
  }
}
```

**字段验证**:
- `title`: 必填，最多 100 个字符
- `city`: 必填
- `address`: 必填
- `rent_price`: 必填，必须大于 0
- `rental_type`: 必填（whole/shared）
- `landlord_id`: 必填，有效的房东 ID
- 其他字段可选

**业务逻辑**:
1. 验证房东是否存在
2. 验证数据格式
3. 创建房源
4. 如果是整租模式，自动设置房源状态为 available
5. 如果是合租模式，需要创建房间后才能确定状态

**响应示例**:
```json
{
  "success": true,
  "message": "房源创建成功",
  "data": {
    "id": 1,
    "title": "科技园区合租公寓",
    ...
  }
}
```

---

### 4. 更新房源

**接口**: `PUT /api/houses/:id`

**权限**: 登录员工（edit 权限）

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房源 ID |

**请求体** (仅包含需要更新的字段):
```json
{
  "title": "新的房源标题",
  "rent_price": 11000.0,
  "contact_phone": "13800138000",
  "facilities": {
    "wifi": true,
    "ac": true
  }
}
```

**业务逻辑**:
1. 验证房源是否存在
2. 更新房源信息
3. 如果更新了租赁类型，重新计算房源状态
4. 记录操作日志

**响应示例**:
```json
{
  "success": true,
  "message": "房源信息更新成功",
  "data": {
    ...
  }
}
```

---

### 5. 删除房源

**接口**: `DELETE /api/houses/:id`

**权限**: 登录员工（delete 权限）

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房源 ID |

**业务逻辑**:
1. 验证房源是否存在
2. 检查是否有活跃合同（有合同不能删除）
3. 级联删除房间和媒体文件
4. 记录操作日志

**响应示例**:
```json
{
  "success": true,
  "message": "房源删除成功"
}
```

---

### 6. 获取房间列表

**接口**: `GET /api/houses/:id/rooms`

**权限**: 登录员工

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房源 ID |

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| status | string | 否 | - | 房间状态筛选（available/rented/maintenance） |

**响应示例**:
```json
{
  "success": true,
  "message": "获取房间列表成功",
  "data": {
    "house_id": 1,
    "house_title": "科技园区合租公寓",
    "rooms": [
      {
        "id": 1,
        "room_number": "101",
        "name": "主卧",
        "area": 25.0,
        "direction": "南",
        "rent_price": 5000.0,
        "status": "rented"
      },
      {
        "id": 2,
        "room_number": "102",
        "name": "次卧 A",
        "area": 18.0,
        "direction": "北",
        "rent_price": 3800.0,
        "status": "available"
      }
    ],
    "total_rooms": 3,
    "available_rooms": 1,
    "rented_rooms": 2
  }
}
```

---

### 7. 创建房间

**接口**: `POST /api/houses/:id/rooms`

**权限**: 登录员工（create 权限）

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房源 ID |

**请求体**:
```json
{
  "room_number": "103",
  "name": "次卧 B",
  "description": "朝北，采光好",
  "area": 18.0,
  "direction": "北",
  "rent_price": 3800.0,
  "deposit": 3800.0,
  "facilities": {
    "bed": true,
    "desk": true,
    "ac": true
  }
}
```

**字段验证**:
- `room_number`: 必填，同一房源内唯一
- `name`: 必填
- `rent_price`: 必填，必须大于 0
- `direction`: 可选（南/北/东/西）

**业务逻辑**:
1. 验证房源是否存在
2. 验证房源是否为合租模式
3. 检查房间编号是否重复
4. 创建房间
5. 自动更新房源状态

**响应示例**:
```json
{
  "success": true,
  "message": "房间创建成功",
  "data": {
    "id": 3,
    "room_number": "103",
    "name": "次卧 B",
    ...
  }
}
```

---

## 外部接口（租客/公众使用）

### 1. 获取房源列表（公开）

**接口**: `GET /api/public/houses`

**权限**: 无需认证（公开访问）

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| per_page | int | 否 | 20 | 每页数量（最大 100） |
| keyword | string | 否 | - | 关键词搜索（标题、地址） |
| city | string | 否 | - | 城市筛选 |
| district | string | 否 | - | 区县筛选 |
| rental_type | string | 否 | - | 租赁类型（whole/shared） |
| min_price | float | 否 | - | 最低租金 |
| max_price | float | 否 | - | 最高租金 |
| status | string | 否 | available | 状态筛选（仅显示 available） |

**响应示例**:
```json
{
  "success": true,
  "message": "获取房源列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "科技园区合租公寓",
        "description": "靠近地铁站，交通便利",
        "city": "北京市",
        "district": "海淀区",
        "address": "中关村大街 1 号",
        "area": 120.5,
        "room_count": 3,
        "rent_price": 12000.0,
        "deposit": 12000.0,
        "rental_type": "shared",
        "status": "available",
        "landlord_name": "平台管家",
        "landlord_phone": null,
        "contact_name": null,
        "contact_phone": null,
        "contact_wechat": null,
        "room_count_actual": 3,
        "available_rooms": [],
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
      "has_prev": false
    }
  }
}
```

**数据脱敏说明**:
- `landlord_name`: 显示为"平台管家"，不显示真实房东姓名
- `landlord_phone`: 不显示
- `contact_name`: 不显示
- `contact_phone`: 不显示
- `contact_wechat`: 不显示

---

### 2. 获取房源详情（公开）

**接口**: `GET /api/public/houses/:id`

**权限**: 无需认证（公开访问）

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 房源 ID |

**响应示例**:
```json
{
  "success": true,
  "message": "获取房源详情成功",
  "data": {
    "id": 1,
    "title": "科技园区合租公寓",
    "description": "靠近地铁站，交通便利",
    "city": "北京市",
    "district": "海淀区",
    "address": "中关村大街 1 号",
    "area": 120.5,
    "room_count": 3,
    "hall_count": 1,
    "bathroom_count": 2,
    "floor": "中层",
    "total_floors": 18,
    "rent_price": 12000.0,
    "deposit": 12000.0,
    "payment_method": "押一付三",
    "rental_type": "shared",
    "status": "available",
    "facilities": {
      "wifi": true,
      "ac": true,
      "heater": true,
      "kitchen": true
    },
    "landlord_name": "平台管家",
    "landlord_phone": null,
    "contact_name": null,
    "contact_phone": null,
    "contact_wechat": null,
    "rooms": [
      {
        "id": 2,
        "room_number": "102",
        "name": "次卧 A",
        "area": 18.0,
        "direction": "北",
        "rent_price": 3800.0,
        "status": "available"
      }
    ],
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  }
}
```

**数据脱敏说明**:
- 不显示房东详细信息
- 不显示联系信息
- 仅显示空闲房间（available 状态的房间）
- 不显示负责员工信息

---

## 业务逻辑实现

### 1. 房源状态管理

#### 整租模式
- `available`: 没有活跃合同
- `rented`: 有活跃合同

#### 合租模式
- `available`: 所有房间都是 available 状态
- `partially_rented`: 部分房间已租，部分空闲
- `rented`: 所有房间都是 rented 状态

### 2. 内部/外部接口区分

[`House.to_dict()`](file:///d:/Pro/Housing_ental_system/app/models/house.py) 方法支持两个参数：

```python
def to_dict(self, include_landlord=False, is_internal=False):
    """
    Args:
        include_landlord: 是否包含房东信息
        is_internal: 是否为内部接口（True 返回完整信息，False 脱敏）
    """
```

**内部接口** (`is_internal=True`):
- 显示完整的房东信息
- 显示联系信息（电话、微信）
- 显示负责员工信息

**外部接口** (`is_internal=False`):
- 房东姓名显示为"平台管家"
- 隐藏所有联系信息
- 隐藏负责员工信息

### 3. 数据权限控制

| 数据类型 | 内部接口 | 外部接口 |
|---------|---------|---------|
| 房东姓名 | 显示真实姓名 | 显示"平台管家" |
| 房东电话 | 显示 | 隐藏 |
| 联系信息 | 显示 | 隐藏 |
| 负责员工 | 显示 | 隐藏 |
| 房间列表 | 显示所有房间 | 仅显示空闲房间 |
| 房源状态 | 显示所有状态 | 仅显示 available 房源 |

---

## 权限控制说明

### 内部接口权限

| 接口 | 权限要求 | 装饰器 |
|------|---------|--------|
| GET /api/houses | 登录员工 | @login_required |
| GET /api/houses/:id | 登录员工 | @login_required |
| POST /api/houses | create 权限 | @login_required + @permission_required('create') |
| PUT /api/houses/:id | edit 权限 | @login_required + @permission_required('edit') |
| DELETE /api/houses/:id | delete 权限 | @login_required + @permission_required('delete') |
| GET /api/houses/:id/rooms | 登录员工 | @login_required |
| POST /api/houses/:id/rooms | create 权限 | @login_required + @permission_required('create') |

### 外部接口权限

所有 `/api/public/houses` 接口无需认证，公开访问。

---

## 错误响应

### 常见错误码

| HTTP 状态码 | 错误码 | 说明 |
|------------|--------|------|
| 400 | bad_request | 请求参数错误、数据验证失败 |
| 401 | unauthorized | 未授权访问（内部接口） |
| 403 | forbidden | 没有权限 |
| 404 | not_found | 房源不存在 |
| 422 | validation_error | 参数验证失败 |
| 500 | internal_server_error | 服务器内部错误 |

### 常见错误信息

| 错误信息 | 说明 |
|----------|------|
| 房源不存在 | 房源 ID 不存在 |
| 房源标题不能为空 | 缺少必填字段 |
| 租金必须大于 0 | 租金字段验证失败 |
| 租赁类型必须是 whole 或 shared | rental_type 字段验证失败 |
| 房东不存在 | landlord_id 无效 |
| 房间编号已存在 | 同一房源内房间编号重复 |
| 房源有活跃合同，无法删除 | 删除限制 |

---

## 数据模型

### House 模型

主要字段：
- `id`: 主键
- `title`: 房源标题
- `description`: 房源描述
- `city`: 城市
- `district`: 区县
- `address`: 详细地址
- `area`: 面积（平方米）
- `room_count`: 房间数
- `rent_price`: 租金（元/月）
- `deposit`: 押金（元）
- `rental_type`: 租赁类型（whole/shared）
- `status`: 房源状态
- `facilities`: 配套设施（JSON）
- `owner_id`: 负责员工 ID（内部管理）
- `landlord_id`: 房东 ID（房源所有者）
- `contact_name`: 联系人姓名
- `contact_phone`: 联系电话
- `contact_wechat`: 微信号

### Room 模型

主要字段：
- `id`: 主键
- `room_number`: 房间编号
- `name`: 房间名称
- `area`: 房间面积
- `direction`: 朝向
- `rent_price`: 房间租金
- `status`: 房间状态
- `house_id`: 房源 ID（外键）

---

## 使用示例

### Python 示例（内部接口）

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

# 创建房源
create_data = {
    'title': '科技园区合租公寓',
    'city': '北京市',
    'district': '海淀区',
    'address': '中关村大街 1 号',
    'area': 120.5,
    'rent_price': 12000.0,
    'deposit': 12000.0,
    'rental_type': 'shared',
    'landlord_id': 1,
    'contact_name': '王房东',
    'contact_phone': '13700137000',
    'contact_wechat': 'wang123'
}

response = requests.post(
    'http://localhost:5000/api/houses',
    headers=headers,
    json=create_data
)

if response.status_code == 201:
    house = response.json()['data']
    print(f"创建成功，房源 ID: {house['id']}")
else:
    print(f"创建失败：{response.json()['error']['message']}")

# 获取房源列表（内部，包含完整信息）
response = requests.get(
    'http://localhost:5000/api/houses',
    headers=headers,
    params={'page': 1, 'per_page': 20}
)

if response.status_code == 200:
    data = response.json()['data']
    for item in data['items']:
        print(f"- {item['title']}: 房东={item.get('landlord_name')}, 电话={item.get('contact_phone')}")
else:
    print(f"获取失败：{response.json()['error']['message']}")
```

### Python 示例（外部接口）

```python
import requests

# 无需认证，直接访问
response = requests.get(
    'http://localhost:5000/api/public/houses',
    params={'page': 1, 'per_page': 20, 'status': 'available'}
)

if response.status_code == 200:
    data = response.json()['data']
    print(f"可租房源共 {data['pagination']['total']} 个")
    for item in data['items']:
        print(f"- {item['title']}: {item['rent_price']}元/月")
        print(f"  房东：{item['landlord_name']}")  # 显示"平台管家"
        print(f"  联系信息：隐藏")
else:
    print(f"获取失败：{response.json()['error']['message']}")

# 获取房源详情（外部，脱敏信息）
response = requests.get('http://localhost:5000/api/public/houses/1')

if response.status_code == 200:
    house = response.json()['data']
    print(f"房源详情：{house['title']}")
    print(f"房东：{house['landlord_name']}")  # 显示"平台管家"
    print(f"可租房间：{len(house.get('rooms', []))}个")
else:
    print(f"获取失败：{response.json()['error']['message']}")
```

---

## 注意事项

1. **数据脱敏**: 
   - 外部接口自动脱敏，保护房东隐私
   - 内部接口返回完整信息，便于员工管理

2. **状态管理**: 
   - 整租模式根据合同状态自动更新
   - 合租模式根据房间状态计算

3. **房间管理**: 
   - 仅合租模式需要创建房间
   - 整租模式不需要房间

4. **删除限制**: 
   - 有活跃合同的房源不能删除
   - 删除房源会级联删除房间和媒体文件

5. **分页查询**: 
   - 列表接口支持分页，默认每页 20 条，最大 100 条

6. **搜索功能**: 
   - 支持关键词、城市、区县、价格范围搜索
   - 外部接口默认仅查询 available 状态的房源

---

## 相关文档

- [数据库模型设计](DATABASE_MODELS.md) - House 和 Room 模型详细说明
- [房东管理 API](landlords_api_docs.md) - 房东管理接口
- [承包合同管理 API](landlord_contracts_api_docs.md) - 承包合同相关接口
