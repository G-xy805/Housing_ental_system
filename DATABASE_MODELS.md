# 房屋租赁系统数据库模型设计说明

## 1. 数据库模型概览

本系统采用 SQLAlchemy ORM 框架设计数据库模型，包含以下 18 个核心模型：

### 1.1 核心业务模型（11个）

| 模型名称 | 表名 | 描述 |
|---------|------|------|
| User | users | 用户表（管理员、普通员工，仅内部员工使用） |
| Landlord | landlords | 房东表（房源所有者，含房产证信息、银行卡信息，加密存储） |
| House | houses | 房源表（支持整租/合租，含地址、配套设施，关联房东和负责员工） |
| Room | rooms | 房间表（合租场景，独立租金和状态） |
| Tenant | tenants | 租客表（含紧急联系人、工作信息，身份证号加密） |
| Contract | contracts | 租赁合同表（支持合租合同、乐观锁、押金状态跟踪，自动编号） |
| LandlordContract | landlord_contracts | 承包合同表（平台与房东的合作合同，关联多个房源） |
| Payment | payments | 支付记录表（支持滞纳金、多种支付方式） |
| DepositRefund | deposit_refunds | 押金退款表（管理合同结束后的押金退款流程） |
| Media | media | 多媒体文件表（图片/视频/文档） |
| StartupTaskRecord | startup_task_records | 启动任务执行记录表（记录启动任务执行状态） |

### 1.2 数据归档模型（3个）

| 模型名称 | 表名 | 描述 |
|---------|------|------|
| ContractArchive | contracts_archive | 合同归档表（存储已过期或已终止的合同数据） |
| PaymentArchive | payments_archive | 支付记录归档表（存储已完成或已取消的支付记录） |
| ArchiveRecord | archive_records | 归档操作记录表（记录每次归档操作的详细信息） |

### 1.3 审计和安全模型（5个）

| 模型名称 | 表名 | 描述 |
|---------|------|------|
| EncryptionAuditLog | encryption_audit_logs | 加密访问审计日志表（记录加密/解密操作） |
| SensitiveDataAuditLog | sensitive_data_audit_logs | 敏感数据访问审计日志表（记录敏感数据访问） |
| BackupRecord | backup_records | 备份记录表（记录备份历史） |
| BackupSettings | backup_settings | 备份设置表（存储备份配置） |
| PasswordHistory | password_history | 密码历史记录表（防止密码重复使用） |

## 2. 数据库关系图

### 2.1 核心业务关系

```
┌─────────────┐
│    User     │
│  (用户表)    │
│  内部员工     │
└──────┬──────┘
       │ 1:N (负责管理)
       │
       ▼
┌─────────────┐                              ┌─────────────┐
│   Landlord  │                              │   Tenant    │
│  (房东表)    │                              │  (租客表)    │
└──────┬──────┘                              └──────┬──────┘
       │ 1:N                                        │ 1:N
       │                                            │
       ├──────────────────┐                         │
       │                  │                         │
       ▼                  ▼                         ▼
┌─────────────┐   ┌─────────────┐          ┌─────────────┐
│    House    │   │  Landlord   │          │  Contract   │
│  (房源表)    │   │  Contract   │          │  (合同表)    │
└──────┬──────┘   │ (承包合同)   │          └──────┬──────┘
       │ 1:N       └─────────────┘                 │ 1:N
       │                                           │
       ▼                                           ▼
┌─────────────┐                              ┌─────────────┐
│    Room     │                              │   Payment   │
│  (房间表)    │                              │  (支付表)    │
└──────┬──────┘                              └─────────────┘
       │
       │ N:1 (合租)
       └────────────────────────────────────────────┘

┌─────────────┐
│    Media    │
│ (多媒体表)   │
└──────┬──────┘
       │ N:1
       ▼
┌─────────────┐
│    House    │
│  (房源表)    │
└─────────────┘
```

### 2.2 审计和安全关系

```
┌─────────────────────────┐
│         User            │
│       (用户表)           │
└───────────┬─────────────┘
            │
            │ 1:N
            ├──────────────────────────────────────┐
            │                                      │
            ▼                                      ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│   PasswordHistory       │          │   EncryptionAuditLog    │
│   (密码历史记录表)        │          │   (加密审计日志表)       │
└─────────────────────────┘          └─────────────────────────┘

┌─────────────────────────┐          ┌─────────────────────────┐
│ SensitiveDataAuditLog   │          │     BackupRecord        │
│ (敏感数据审计日志表)      │          │    (备份记录表)          │
└─────────────────────────┘          └─────────────────────────┘

┌─────────────────────────┐
│     BackupSettings      │
│    (备份设置表)          │
│    单例模式（id=1）       │
└─────────────────────────┘
```

**关系说明：**
- User 1:N House（作为负责人）：一个员工负责多个房源
- User 1:N Media：一个用户上传多个媒体文件
- User 1:N Payment（作为操作员）：一个操作员处理多个支付
- User 1:N User（管理员创建的员工）：管理员可以创建多个员工账号
- User 1:N PasswordHistory：一个用户有多条密码历史记录
- Landlord 1:N House：一个房东拥有多个房源
- Landlord 1:N LandlordContract：一个房东有多个承包合同
- House 1:N Room：一个房源有多个房间（合租模式）
- House 1:N Contract：一个房源有多个租赁合同
- House 1:N Media：一个房源有多个媒体文件
- Room 1:N Contract：一个房间有多个合同（合租时）
- Tenant 1:N Contract：一个租客有多个合同
- LandlordContract N:1 Landlord：一个承包合同关联一个房东
- Contract 1:N Payment：一个合同有多个支付记录

## 3. 基础模型类

### 3.1 BaseModel（抽象基类）

所有模型都继承自 `BaseModel`，提供通用字段和方法：

**通用字段：**
```python
- id: 主键（Integer, primary_key, autoincrement）
- created_at: 创建时间（DateTime, default=datetime.now）
- updated_at: 更新时间（DateTime, default=datetime.now, onupdate=datetime.now）
- is_active: 是否激活（Boolean, default=True）
- deleted_at: 软删除时间戳（DateTime, nullable=True）
```

**软删除功能：**
```python
- is_deleted: 属性，判断记录是否已删除
- soft_delete(): 软删除记录（设置 deleted_at 为当前时间）
- restore(): 恢复已删除记录（设置 deleted_at 为 NULL）
- hard_delete(): 硬删除记录（真正从数据库删除）
- save(): 保存对象到数据库
- delete(): 软删除对象（兼容旧代码）
```

**查询方法：**
```python
- Model.query.all()           # 自动过滤已删除记录
- Model.query.with_deleted()  # 包含已删除记录
- Model.query.only_deleted()  # 仅查询已删除记录
- Model.active_query()        # 查询时自动过滤已删除记录
```

### 3.2 SoftDeleteQuery（自定义查询类）

提供软删除查询过滤功能：

```python
# 默认查询自动过滤已删除记录
houses = House.query.all()  # 不包含已删除记录

# 包含已删除记录
all_houses = House.query.with_deleted().all()

# 仅查询已删除记录
deleted_houses = House.query.only_deleted().all()

# 分页查询（自动过滤已删除记录）
page = House.query.paginate(page=1, per_page=20)
```

## 4. 核心业务模型详细说明

### 4.1 User（用户表）

**重要说明：** User 表仅用于公司内部员工（管理员和普通员工），房东不访问系统。

**关系：**
- 1:N → House（员工负责的房源）
- 1:N → Media（上传的媒体文件）
- 1:N → Payment（操作的支付记录）
- 1:N → User（创建的员工）
- 1:N → PasswordHistory（密码历史记录）

**字段说明：**
```python
- id: 主键
- username: 用户名（唯一，非空）
- email: 邮箱（唯一，可为空）
- password_hash: 密码哈希（非空）
- role: 角色（admin-管理员/staff-员工）
- user_type: 用户类型（admin-管理员/staff-员工）
- name: 姓名
- phone: 手机号（唯一）
- id_card: 身份证号
- id_card_hash: 身份证号哈希（用于去重验证）
- position: 职位
- status: 员工状态（active-在职/resigned-离职/disabled-禁用）
- avatar: 头像 URL
- last_login: 最后登录时间
- login_attempts: 登录失败次数
- locked_until: 锁定截止时间
- created_by: 创建人（外键）
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**权限控制：**
- admin：拥有所有权限（查看、创建、编辑、删除）
- staff：仅有基础权限（查看、创建、编辑），无删除权限

**业务方法：**
```python
- is_admin: 属性，判断是否为管理员
- is_staff: 属性，判断是否为普通员工
- has_permission(permission): 检查用户权限
- set_password(password, expires_days=None): 设置密码（支持密码历史记录）
- check_password(password): 验证密码
- generate_token(expires_in=3600): 生成 JWT token
- verify_token(token): 验证 JWT token（静态方法）
- set_id_card(id_card_number): 设置身份证号并生成哈希
- verify_id_card(id_card_number): 验证身份证号是否匹配
- is_account_locked(): 检查账号是否被锁定
- record_login_attempt(success): 记录登录尝试（连续失败 5 次锁定 30 分钟）
- to_dict(include_details=False): 转换为字典（自动移除敏感字段，身份证号脱敏）
```

**索引：**
- idx_users_username: username 字段索引
- idx_users_role: role 字段索引
- idx_users_email: email 字段索引
- idx_users_phone: phone 字段索引
- idx_users_status: status 字段索引
- idx_users_id_card_hash: id_card_hash 字段索引

---

### 4.2 Landlord（房东表）

**关系：**
- 1:N → House（房东拥有的房源）
- 1:N → LandlordContract（房东的承包合同）

**字段说明：**
```python
- id: 主键
- name: 姓名（非空）
- id_card_encrypted: 身份证号（AES-256-GCM 加密存储）
- phone: 联系电话（非空）
- bank_card_encrypted: 银行卡号（AES-256-GCM 加密存储）
- bank_name: 开户行名称
- property_cert_no: 房产证编号
- address: 房产地址
- status: 房东状态（active-正常/inactive-停用/blacklisted-黑名单）
- remark: 备注
- photo: 个人照片 URL
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**安全特性：**
- 身份证号和银行卡号使用 AES-256-GCM 加密存储
- 支持向后兼容旧的 Fernet 加密数据
- 所有加密操作记录审计日志
- 所有敏感数据访问记录审计日志

**业务方法：**
```python
- set_id_card(id_card_number, user_id=None, skip_audit=False): 设置身份证号并加密存储
- get_id_card(user_id=None, skip_audit=False): 获取解密后的身份证号
- verify_id_card(id_card_number, user_id=None, skip_audit=False): 验证身份证号是否匹配
- set_bank_card(bank_card_number, user_id=None, skip_audit=False): 设置银行卡号并加密存储
- get_bank_card(user_id=None, skip_audit=False): 获取解密后的银行卡号
- mask_bank_card(user_id=None, skip_audit=False): 获取脱敏的银行卡号
- needs_re_encryption(): 检查是否需要重新加密（从 Fernet 迁移到 AES-256-GCM）
- re_encrypt_data(user_id=None): 重新加密数据
- to_dict(include_details=False): 转换为字典（自动移除敏感字段，银行卡号脱敏）
```

**索引：**
- idx_landlords_phone: phone 字段索引
- idx_landlords_status: status 字段索引

---

### 4.3 House（房源表）

**关系：**
- N:1 → User（负责人，owner 关系）
- N:1 → Landlord（房东，landlord_rel 关系）
- 1:N → Room（房源包含多个房间）
- 1:N → Contract（房源有多个租赁合同）
- 1:N → Media（房源有多个媒体文件）

**字段说明：**
```python
- id: 主键
- title: 房源标题（非空）
- description: 房源描述
- province: 省份
- city: 城市
- district: 区县
- address: 详细地址
- latitude: 纬度
- longitude: 经度
- area: 面积（平方米）
- room_count: 房间数
- hall_count: 客厅数
- bathroom_count: 卫生间数
- floor: 楼层
- total_floors: 总楼层
- rent_price: 租金（元/月，非空）
- deposit: 押金（元）
- payment_method: 付款方式（默认：押一付三）
- status: 状态（available-空闲/rented-已租/maintenance-维护中/partially_rented-部分出租）
- facilities: 配套设施（JSON）
- images: 房源图片列表（JSON，保留字段）
- cover_image: 封面图片
- rental_type: 租赁类型（whole-整租/shared-合租）
- owner_id: 负责员工 ID（外键，非空）
- landlord_id: 房东 ID（外键，可为空）
- contact_name: 联系人姓名
- contact_phone: 联系电话
- contact_wechat: 微信号
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**状态管理：**
- 整租模式：根据合同状态自动更新（available/rented）
- 合租模式：根据房间状态计算（available/partially_rented/rented）

**业务方法：**
```python
- update_status(): 根据房间状态更新房源状态
- get_room_count(): 获取房间数量
- get_available_rooms(): 获取空闲房间列表
- to_dict(include_landlord=False, is_internal=False): 转换为字典（支持内部/外部接口区分）
```

**索引：**
- idx_houses_status: status 字段索引
- idx_houses_city: city 字段索引
- idx_houses_district: district 字段索引
- idx_houses_rental_type: rental_type 字段索引
- idx_houses_owner_id: owner_id 字段索引
- idx_houses_landlord_id: landlord_id 字段索引

---

### 4.4 Room（房间表）

**关系：**
- N:1 → House（房间属于某个房源）
- 1:N → Contract（房间有多个合同）

**字段说明：**
```python
- id: 主键
- room_number: 房间编号（同一房源内唯一，非空）
- name: 房间名称（如：主卧、次卧 A）
- description: 房间描述
- area: 房间面积（平方米）
- floor: 楼层
- direction: 朝向（南/北/东/西）
- rent_price: 房间租金（元/月，非空）
- deposit: 押金（元）
- facilities: 配套设施（JSON）
- status: 状态（available-空闲/rented-已租/maintenance-维护中）
- house_id: 房源 ID（外键，非空）
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**事件监听器：**
- `after_update`: 当房间状态变化时，自动更新所属房源的状态

**业务方法：**
```python
- to_dict(): 转换为字典（包含房源信息，添加 room_no 字段兼容前端）
```

**索引：**
- idx_rooms_house_id: house_id 字段索引
- idx_rooms_status: status 字段索引
- idx_rooms_house_number: (house_id, room_number) 复合唯一索引

---

### 4.5 Tenant（租客表）

**关系：**
- 1:N → Contract（租客有多个合同，tenant_rel 关系）

**字段说明：**
```python
- id: 主键
- name: 姓名（非空）
- id_card_encrypted: 身份证号（AES-256-GCM 加密存储）
- phone: 联系电话（非空）
- email: 电子邮箱
- emergency_contact: 紧急联系人姓名
- emergency_phone: 紧急联系人电话
- emergency_relation: 与紧急联系人关系
- company: 工作单位
- occupation: 职业
- status: 状态（pending-待租/active-在租/expired-已退租/blacklisted-黑名单）
- remark: 备注
- photo: 个人照片 URL
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**安全特性：**
- 身份证号使用 AES-256-GCM 加密存储
- 支持向后兼容旧的 Fernet 加密数据
- 所有加密操作记录审计日志
- 所有敏感数据访问记录审计日志

**业务方法：**
```python
- set_id_card(id_card_number, user_id=None): 设置身份证号并加密存储
- get_id_card(user_id=None): 获取解密后的身份证号
- verify_id_card(id_card_number, user_id=None): 验证身份证号是否匹配
- needs_re_encryption(): 检查是否需要重新加密
- re_encrypt_data(user_id=None): 重新加密数据
- get_active_contracts(): 获取当前有效的合同
- get_current_houses(): 获取当前租住的房源
- to_dict(): 转换为字典（自动移除敏感字段）
```

**索引：**
- idx_tenants_phone: phone 字段索引
- idx_tenants_status: status 字段索引

---

### 4.6 Contract（租赁合同表）

**关系：**
- N:1 → House（合同关联房源）
- N:1 → Room（合同关联房间，合租时）
- N:1 → Tenant（合同关联租客，tenant_rel 关系）
- N:1 → Contract（原合同，续签时 original_contract 关系）
- 1:N → Payment（合同有多个支付记录，contract_rel 关系）

**字段说明：**
```python
- id: 主键
- contract_no: 合同编号（自动生成，唯一，非空，格式：HT+年月日+8位随机数）
- version: 版本号（乐观锁，默认 0，非空）
- title: 合同标题（非空）
- description: 合同描述
- start_date: 起租日期（非空）
- end_date: 结束日期（非空）
- rent_amount: 租金金额（元/月，非空）
- deposit_amount: 押金金额（元，非空）
- payment_type: 付款类型（月付/季付/半年付/年付）
- payment_cycle: 付款周期（月数）
- status: 状态（draft-草稿/active-生效中/expired-已过期/terminated-已终止）
- deposit_status: 押金状态（pending-待支付/paid-已支付/transferred-已转移/refunded-已退款）
- original_contract_id: 原合同 ID（外键，续签时记录原合同）
- contract_file: 合同文件路径
- remark: 备注
- house_id: 房源 ID（外键，非空）
- room_id: 房间 ID（外键，合租时）
- tenant_id: 租客 ID（外键，非空）
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**乐观锁机制：**
```python
- version: 版本号字段，用于并发控制
- check_version(expected_version): 检查版本号是否匹配
- increment_version(): 递增版本号
- update_with_optimistic_lock(contract_id, expected_version, update_data): 使用乐观锁更新合同
- OptimisticLockError: 版本冲突异常
```

**押金状态管理：**
```python
DEPOSIT_STATUS = {
    'pending': '待支付',     # 合同创建后的初始状态
    'paid': '已支付',        # 租客已支付押金
    'transferred': '已转移', # 续签时押金转移到新合同
    'refunded': '已退款'     # 合同结束后押金已退还
}

- update_deposit_status(new_status): 更新押金状态（带状态转换验证）
- is_deposit_paid(): 检查押金是否已支付
- can_transfer_deposit(): 检查押金是否可以转移（用于续签）
```

**事件监听器：**
- `after_update`: 当合同状态变为 terminated 或 expired 时，自动取消所有未支付的支付记录

**业务方法：**
```python
- generate_contract_no(): 生成合同编号（类方法，格式：HT+年月日+8位随机UUID）
- is_expired(): 检查是否过期
- is_expiring_soon(days=30): 检查是否即将到期
- get_days_until_expiry(): 获取距离到期天数
- calculate_total_rent(): 计算合同期内的总租金（支持按天计算剩余天数）
- get_cascade_relations(): 获取需要级联处理的关系定义
- validate_delete(): 验证是否可以删除合同（活跃合同和有未完成支付的不允许删除）
- to_dict(): 转换为字典（包含房源、房间、租客信息，自动计算过期状态和总租金，押金状态信息）
```

**索引：**
- idx_contracts_house_id: house_id 字段索引
- idx_contracts_room_id: room_id 字段索引
- idx_contracts_tenant_id: tenant_id 字段索引
- idx_contracts_status: status 字段索引
- idx_contracts_deposit_status: deposit_status 字段索引
- idx_contracts_dates: (start_date, end_date) 复合索引
- idx_contract_status_date: (status, created_at) 复合索引（性能优化）
- idx_contract_tenant_status: (tenant_id, status) 复合索引（性能优化）

---

### 4.7 LandlordContract（承包合同表）

**关系：**
- N:1 → Landlord（合同关联房东，landlord 关系）
- N:1 → House（合同包含多个房源，通过 house_ids JSON 字段存储）

**字段说明：**
```python
- id: 主键
- contract_no: 合同编号（自动生成，唯一，非空，格式：LC+年月日+4位随机数）
- title: 合同标题（非空）
- description: 合同描述
- start_date: 开始日期（非空）
- end_date: 结束日期（非空）
- contract_amount: 承包总金额（元，非空）
- service_fee_rate: 服务费率（%，非空）
- minimum_fee: 最低服务费（元）
- payment_cycle: 付款周期（月数）
- status: 状态（draft-草稿/active-生效中/expired-已过期/terminated-已终止）
- contract_file: 合同文件路径
- remark: 备注
- landlord_id: 房东 ID（外键，非空）
- house_ids: 承包的房源 ID 列表（JSON，默认空数组）
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**业务方法：**
```python
- generate_contract_no(): 生成合同编号（类方法，格式：LC+年月日+4位随机数）
- is_expired(): 检查合同是否过期
- is_expiring_soon(days=30): 检查合同是否即将到期
- get_days_until_expiry(): 获取距离到期天数
- calculate_contract_term(): 计算合同期限（月数）
- calculate_service_fee(): 计算服务费（基于合同金额和服务费率，支持最低服务费）
- get_houses(): 获取合同关联的所有房源
- to_dict(): 转换为字典（包含房东信息、房源信息、合同期限、服务费、过期状态）
```

**索引：**
- idx_landlord_contracts_landlord_id: landlord_id 字段索引
- idx_landlord_contracts_status: status 字段索引
- idx_landlord_contracts_dates: (start_date, end_date) 复合索引

---

### 4.8 DepositRefund（押金退款表）

**关系：**
- N:1 → Contract（退款关联合同，contract 关系）
- N:1 → Tenant（退款关联租客，tenant 关系）
- N:1 → House（退款关联房源，house 关系）
- N:1 → User（处理人，processor 关系）

**字段说明：**
```python
- id: 主键
- contract_id: 合同 ID（外键，非空）
- tenant_id: 租客 ID（外键，非空）
- house_id: 房源 ID（外键，非空）
- original_deposit: 原始押金金额（非空）
- deductions: 扣款项列表（JSON 格式，默认空数组）
- total_deduction: 总扣款金额（默认 0）
- refund_amount: 实际退款金额（非空）
- status: 退款状态（pending-待处理/processed-已处理/completed-已完成/cancelled-已取消）
- processed_by: 处理人 ID（外键）
- processed_at: 处理时间
- completed_at: 完成时间
- remark: 备注
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**扣款项类型：**
```python
DEDUCTION_TYPES = {
    'unpaid_rent': '未付租金',
    'unpaid_utilities': '未付水电费',
    'late_fees': '滞纳金',
    'damage_compensation': '损坏赔偿',
    'other': '其他扣款'
}
```

**业务方法：**
```python
- calculate_total_deduction(): 计算总扣款金额
- add_deduction(deduction_type, amount, description): 添加扣款项
- remove_deduction(index): 移除扣款项
- process(processed_by): 处理退款
- complete(): 完成退款
- can_complete(): 检查是否可以完成退款（返回元组：是否可以完成, 错误消息）
- cancel(reason): 取消退款
- get_deduction_summary(): 获取扣款项汇总
- to_dict(): 转换为字典（包含合同、租客、房源、处理人信息，押金状态信息）
```

**索引：**
- idx_deposit_refunds_contract_id: contract_id 字段索引
- idx_deposit_refunds_tenant_id: tenant_id 字段索引
- idx_deposit_refunds_house_id: house_id 字段索引
- idx_deposit_refunds_status: status 字段索引
- idx_deposit_refunds_processed_by: processed_by 字段索引

---

### 4.9 Payment（支付表）

**关系：**
- N:1 → Contract（支付属于某个合同，contract_rel 关系）
- N:1 → User（操作员，operator 关系）

**字段说明：**
```python
- id: 主键
- payment_no: 支付编号（自动生成，唯一，非空，格式：PY+年月日+8位随机数）
- amount: 应缴金额（非空）
- paid_amount: 实缴金额
- payment_type: 类型（rent-租金/deposit-押金/utility-水电费/other-其他，非空）
- payment_method: 方式（cash-现金/bank-银行转账/wechat-微信/alipay-支付宝）
- period_start: 支付周期开始
- period_end: 周期结束
- due_date: 应缴日期（非空）
- payment_date: 实际支付日期
- confirmed_date: 确认到账日期
- late_fee: 滞纳金金额
- late_fee_rate: 滞纳金比例（每日，默认 0.0005）
- overdue_days: 逾期天数
- status: 状态（pending-待支付/paid-已支付/overdue-逾期/partial-部分支付/refunded-已退款/cancelled-已取消）
- remark: 备注
- receipt_file: 收据/凭证文件路径
- contract_id: 合同 ID（外键）
- operator_id: 操作员 ID（外键）
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**滞纳金计算：**
- 日利率：0.05%（可配置，LATE_FEE_RATE）
- 上限：20%（可配置，LATE_FEE_MAX_RATE）
- 公式：滞纳金 = 应缴金额 × 日利率 × 逾期天数
- 计算逻辑：使用 Decimal 类型精确计算，支持按实际逾期天数和应用上限

**业务方法：**
```python
- generate_payment_no(): 生成支付编号（类方法，格式：PY+年月日+8位随机UUID）
- calculate_late_fee(current_date=None): 计算滞纳金（返回滞纳金金额和逾期天数）
- get_total_amount(): 获取应缴总额（含滞纳金）
- mark_as_paid(paid_amount, payment_date=None, payment_method=None): 标记为已支付
- is_overdue(current_date=None): 检查是否逾期
- get_days_until_due(): 获取距离到期天数
- to_dict(): 转换为字典（包含合同、租客、操作员信息，支付类型/方式中文名称）
```

**索引：**
- idx_payments_contract_id: contract_id 字段索引
- idx_payments_status: status 字段索引
- idx_payments_due_date: due_date 字段索引
- idx_payments_payment_type: payment_type 字段索引

---

### 4.10 Media（多媒体表）

**关系：**
- N:1 → House（媒体属于某个房源）
- N:1 → User（上传人，uploader 关系）

**字段说明：**
```python
- id: 主键
- file_name: 原始文件名（非空）
- file_path: 文件存储路径（非空）
- file_url: 文件访问 URL
- file_type: 类型（image-图片/video-视频/document-文档，非空）
- mime_type: 文件 MIME 类型
- file_size: 文件大小（字节）
- description: 文件描述
- sort_order: 排序顺序
- is_cover: 是否为封面图片
- house_id: 房源 ID（外键，可为空）
- uploaded_by: 上传人 ID（外键）
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**支持的 MIME 类型：**
```python
ALLOWED_MIME_TYPES = {
    'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    'video': ['video/mp4', 'video/quicktime', 'video/x-msvideo'],
    'document': ['application/pdf', 'application/msword', 
                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                 'application/vnd.ms-excel', 
                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
}
```

**业务方法：**
```python
- get_file_type(mime_type): 根据 MIME 类型判断文件类型（类方法）
- is_allowed_type(mime_type): 检查 MIME 类型是否允许（类方法）
- get_file_size_formatted(): 获取格式化后的文件大小（自动转换为 B/KB/MB/GB）
- to_dict(): 转换为字典（包含上传者信息、格式化文件大小）
```

**索引：**
- idx_media_house_id: house_id 字段索引
- idx_media_file_type: file_type 字段索引
- idx_media_is_cover: is_cover 字段索引

---

### 4.11 StartupTaskRecord（启动任务执行记录表）

**功能：** 记录应用启动时执行的定时任务状态，确保任务只执行一次。

**字段说明：**
```python
- id: 主键
- task_name: 任务名称（非空）
- task_date: 任务日期（非空）
- status: 状态（pending-待执行/running-执行中/completed-已完成/failed-执行失败）
- started_at: 开始时间
- completed_at: 完成时间
- total_records: 总记录数
- processed_records: 已处理记录数
- failed_records: 失败记录数
- execution_time: 执行时间（秒）
- error_message: 错误信息
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**业务方法：**
```python
- to_dict(): 转换为字典
- get_task_status(task_name, task_date): 获取任务状态（类方法）
- mark_running(task_name, task_date): 标记任务开始执行（类方法）
- mark_completed(task_name, task_date, processed_records, failed_records, execution_time): 标记任务完成（类方法）
- mark_failed(task_name, task_date, error_message): 标记任务失败（类方法）
```

**索引：**
- idx_startup_task_name_date: (task_name, task_date) 复合唯一索引

## 5. 数据归档模型详细说明

### 5.1 ContractArchive（合同归档表）

**功能：** 存储已过期或已终止的合同数据，不设置外键约束避免数据完整性问题。

**字段说明：**
```python
- id: 主键
- archived_at: 归档时间（非空）
- archive_reason: 归档原因（expired-过期/terminated-终止/manual-手动）
- original_id: 原合同 ID（非空）
- contract_no: 合同编号（非空）
- title: 合同标题（非空）
- description: 合同描述
- start_date: 起租日期（非空）
- end_date: 结束日期（非空）
- rent_amount: 租金金额（元/月，非空）
- deposit_amount: 押金金额（元，非空）
- payment_type: 付款类型
- payment_cycle: 付款周期（月数）
- status: 合同状态
- deposit_status: 押金状态
- original_contract_id: 原合同 ID（续签时）
- house_id: 房源 ID（非空）
- room_id: 房间 ID
- tenant_id: 租客 ID（非空）
- house_title: 房源标题（冗余字段）
- house_address: 房源地址（冗余字段）
- tenant_name: 租客姓名（冗余字段）
- tenant_phone: 租客电话（冗余字段）
- contract_file: 合同文件路径
- remark: 备注
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**业务方法：**
```python
- archive_from_contract(contract, archive_reason): 从合同对象创建归档记录（类方法）
- to_dict(): 转换为字典
```

**索引：**
- idx_contracts_archive_archived_at: archived_at 字段索引
- idx_contracts_archive_original_id: original_id 字段索引
- idx_contracts_archive_house_id: house_id 字段索引
- idx_contracts_archive_tenant_id: tenant_id 字段索引
- idx_contracts_archive_dates: (start_date, end_date) 复合索引
- idx_contracts_archive_status: status 字段索引

---

### 5.2 PaymentArchive（支付记录归档表）

**功能：** 存储已完成或已取消的支付记录，不设置外键约束避免数据完整性问题。

**字段说明：**
```python
- id: 主键
- archived_at: 归档时间（非空）
- archive_reason: 归档原因（completed-完成/cancelled-取消/manual-手动）
- original_id: 原支付记录 ID（非空）
- payment_no: 支付编号（非空）
- amount: 应缴金额（非空）
- paid_amount: 实缴金额
- payment_type: 支付类型（非空）
- payment_method: 支付方式
- period_start: 支付周期开始
- period_end: 周期结束
- payment_date: 实际支付日期
- due_date: 应缴日期（非空）
- confirmed_date: 确认到账日期
- late_fee: 滞纳金金额
- late_fee_rate: 滞纳金比例（每日）
- overdue_days: 逾期天数
- status: 支付状态
- contract_id: 合同 ID
- operator_id: 操作人 ID
- contract_no: 合同编号（冗余字段）
- tenant_name: 租客姓名（冗余字段）
- tenant_phone: 租客电话（冗余字段）
- house_address: 房源地址（冗余字段）
- remark: 备注
- receipt_file: 收据/凭证文件路径
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**业务方法：**
```python
- archive_from_payment(payment, archive_reason): 从支付记录对象创建归档记录（类方法）
- to_dict(): 转换为字典
```

**索引：**
- idx_payments_archive_archived_at: archived_at 字段索引
- idx_payments_archive_original_id: original_id 字段索引
- idx_payments_archive_contract_id: contract_id 字段索引
- idx_payments_archive_due_date: due_date 字段索引
- idx_payments_archive_status: status 字段索引
- idx_payments_archive_payment_type: payment_type 字段索引

---

### 5.3 ArchiveRecord（归档操作记录表）

**功能：** 记录每次归档操作的详细信息，用于审计和追踪。

**字段说明：**
```python
- id: 主键
- archive_type: 归档类型（contract-合同/payment-支付，非空）
- archive_date: 归档日期（非空）
- archive_reason: 归档原因
- total_records: 总记录数
- archived_records: 已归档记录数
- failed_records: 失败记录数
- started_at: 开始时间
- completed_at: 完成时间
- execution_time: 执行时间（秒）
- date_range_start: 日期范围开始
- date_range_end: 日期范围结束
- error_message: 错误信息
- remark: 备注
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**业务方法：**
```python
- to_dict(): 转换为字典
```

**索引：**
- idx_archive_records_type: archive_type 字段索引
- idx_archive_records_date: archive_date 字段索引
- idx_archive_records_status: is_active 字段索引

## 6. 审计和安全模型详细说明

### 6.1 EncryptionAuditLog（加密访问审计日志表）

**功能：** 记录所有敏感数据的加密和解密操作，用于安全审计和合规性检查。

**字段说明：**
```python
- id: 主键
- operation: 操作类型（encrypt-加密/decrypt-解密，非空）
- field_name: 字段名称（非空）
- model_name: 模型名称（非空）
- record_id: 记录 ID（非空）
- key_id: 使用的密钥 ID（非空）
- user_id: 操作用户 ID
- ip_address: 操作 IP 地址
- success: 操作是否成功（默认 True）
- error_message: 错误信息（如果失败）
- timestamp: 操作时间（非空）
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**业务方法：**
```python
- to_dict(): 转换为字典（包含操作类型中文名称）
- get_logs_by_record(model_name, record_id, limit=100): 获取指定记录的审计日志（类方法）
- get_logs_by_user(user_id, limit=100): 获取指定用户的审计日志（类方法）
- get_logs_by_key(key_id, limit=100): 获取使用指定密钥的审计日志（类方法）
- get_failed_operations(limit=100): 获取失败的加密操作日志（类方法）
- get_statistics(start_date=None, end_date=None): 获取加密操作统计信息（类方法）
```

**索引：**
- idx_encryption_audit_timestamp: timestamp 字段索引
- idx_encryption_audit_operation: operation 字段索引
- idx_encryption_audit_model_record: (model_name, record_id) 复合索引
- idx_encryption_audit_user: user_id 字段索引
- idx_encryption_audit_key: key_id 字段索引

---

### 6.2 SensitiveDataAuditLog（敏感数据访问审计日志表）

**功能：** 记录所有敏感数据的访问、修改、删除操作，用于安全审计和合规性检查。

**字段说明：**
```python
- id: 主键
- operation_type: 操作类型（view-查看/modify-修改/delete-删除/export-导出，非空）
- model_name: 模型名称（非空）
- record_id: 记录 ID（非空）
- field_name: 字段名称（非空）
- field_display_name: 字段显示名称
- user_id: 操作用户 ID
- username: 操作用户名
- user_role: 用户角色
- ip_address: 操作 IP 地址
- user_agent: 用户代理（浏览器信息）
- request_path: 请求路径
- request_method: 请求方法
- success: 操作是否成功（默认 True）
- error_message: 错误信息
- old_value: 变更前的值（脱敏）
- new_value: 变更后的值（脱敏）
- operation_time: 操作时间（非空，有索引）
- remark: 备注信息
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**操作类型常量：**
```python
OPERATION_VIEW = 'view'       # 查看敏感数据
OPERATION_MODIFY = 'modify'   # 修改敏感数据
OPERATION_DELETE = 'delete'   # 删除敏感数据
OPERATION_EXPORT = 'export'   # 导出敏感数据
```

**敏感字段定义：**
```python
SENSITIVE_FIELDS = {
    'Landlord': {
        'id_card': '身份证号',
        'bank_card': '银行卡号',
        'property_cert_no': '房产证编号'
    },
    'Tenant': {
        'id_card': '身份证号',
        'emergency_phone': '紧急联系人电话',
        'phone': '联系电话'
    },
    'User': {
        'password': '密码',
        'phone': '联系电话',
        'email': '电子邮箱'
    }
}
```

**业务方法：**
```python
- to_dict(): 转换为字典（不包含变更信息）
- to_detail_dict(): 转换为详细字典（包含变更信息）
- get_logs_by_record(model_name, record_id, limit=100): 获取指定记录的审计日志（类方法）
- get_logs_by_user(user_id, limit=100): 获取指定用户的审计日志（类方法）
- get_logs_by_field(model_name, field_name, limit=100): 获取指定字段的审计日志（类方法）
- get_logs_by_operation(operation_type, limit=100): 获取指定操作类型的审计日志（类方法）
- get_failed_operations(limit=100): 获取失败的操作日志（类方法）
- get_logs_by_time_range(start_time, end_time, limit=1000): 获取指定时间范围的审计日志（类方法）
- get_statistics(start_date=None, end_date=None): 获取审计日志统计信息（类方法）
- get_user_activity_summary(user_id, days=30): 获取用户活动摘要（类方法）
- get_sensitive_access_alert(threshold=10, hours=1): 获取敏感数据访问预警（类方法）
```

**索引：**
- idx_sensitive_audit_operation_time: operation_time 字段索引
- idx_sensitive_audit_operation_type: operation_type 字段索引
- idx_sensitive_audit_model_record: (model_name, record_id) 复合索引
- idx_sensitive_audit_user: user_id 字段索引
- idx_sensitive_audit_field: (model_name, field_name) 复合索引
- idx_sensitive_audit_success: success 字段索引

---

### 5.3 BackupRecord（备份记录表）

**功能：** 记录每次备份的详细信息，提供持久化存储和查询功能。

**字段说明：**
```python
- id: 主键
- backup_id: 备份ID（唯一，非空）
- backup_type: 备份类型（full-完整备份/incremental-增量备份，非空）
- status: 状态（running-进行中/success-成功/failed-失败，非空）
- start_time: 开始时间（非空）
- end_time: 结束时间
- duration: 耗时（秒）
- filename: 备份文件名
- file_path: 备份文件路径
- file_size: 文件大小（字节）
- file_hash: 文件哈希值
- encrypted: 是否加密（默认 False）
- compressed: 是否压缩（默认 False）
- includes_uploads: 是否包含上传文件（默认 False）
- database_size: 数据库大小（字节）
- uploads_size: 上传文件大小（字节）
- backup_by: 备份执行人
- backup_method: 备份方式（manual-手动/auto-自动/scheduled-定时）
- trigger: 触发方式
- error_message: 错误信息
- error_traceback: 错误堆栈
- remark: 备注
- backup_metadata: 备份元数据（JSON）
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**业务方法：**
```python
- to_dict(): 转换为字典（包含计算字段和状态描述）
- create_from_backup_info(backup_info, backup_id, backup_by='system'): 从备份信息创建记录（类方法）
- get_latest_successful(limit=10): 获取最近成功的备份记录（类方法）
- get_failed_backups(days=7): 获取最近失败的备份记录（类方法）
- get_statistics(days=30): 获取备份统计信息（类方法）
```

**索引：**
- idx_backup_records_backup_id: backup_id 字段索引
- idx_backup_records_status: status 字段索引
- idx_backup_records_backup_type: backup_type 字段索引
- idx_backup_records_start_time: start_time 字段索引
- idx_backup_records_backup_by: backup_by 字段索引

---

### 5.4 BackupSettings（备份设置表）

**功能：** 持久化存储备份相关配置，确保应用重启后设置不丢失。采用单例模式（id=1）。

**字段说明：**
```python
- id: 主键（默认 1，单例模式）
- enabled: 是否启用自动备份（默认 True，非空）
- frequency: 备份频率（daily-每日/weekly-每周/monthly-每月，默认 daily，非空）
- backup_time: 备份时间 HH:MM（默认 02:00，非空）
- weekday: 周几备份（0=周一，用于周备份）
- day_of_month: 每月几号备份（用于月备份）
- keep_count: 保留备份数量（默认 30，非空）
- retention_days: 保留天数（默认 30，非空）
- backup_type: 备份类型（full-完整/incremental-增量，默认 full，非空）
- include_uploads: 是否包含上传文件（默认 True，非空）
- encryption_enabled: 是否启用加密（默认 True，非空）
- compression_enabled: 是否启用压缩（默认 True，非空）
- alert_enabled: 是否启用告警（默认 True，非空）
- alert_email: 告警邮箱
- updated_at: 更新时间（非空）
- created_at: 创建时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**业务方法：**
```python
- to_dict(): 转换为字典
- get_settings(): 获取备份设置，如果不存在则创建默认设置（类方法）
- update_settings(data): 更新备份设置（类方法）
```

**索引：**
- idx_backup_settings_id: id 字段索引

---

### 5.5 PasswordHistory（密码历史记录表）

**功能：** 记录用户密码变更历史，防止用户重复使用最近使用过的密码，支持密码过期管理。

**字段说明：**
```python
- id: 主键
- user_id: 用户ID（外键，非空）
- password_hash: 密码哈希（非空）
- password_set_at: 密码设置时间（非空）
- password_expires_at: 密码过期时间
- is_expired: 是否已过期（默认 False）
- created_at: 创建时间
- updated_at: 更新时间
- is_active: 是否激活
- deleted_at: 软删除时间戳
```

**业务方法：**
```python
- to_dict(): 转换为字典（不返回密码哈希）
- add_password_history(user_id, password, expires_days=90): 添加密码历史记录（类方法）
- check_password_in_history(user_id, password, limit=5): 检查密码是否在历史记录中（类方法）
- cleanup_old_passwords(user_id, keep_count=5): 清理旧的密码历史记录（类方法）
- mark_expired_passwords(): 标记所有已过期的密码（类方法）
- get_user_password_age(user_id): 获取用户当前密码的使用天数（类方法）
- is_password_expired(user_id): 检查用户密码是否已过期（类方法）
- get_days_until_expiry(user_id): 获取距离密码过期的天数（类方法）
```

**索引：**
- idx_password_history_user_id: user_id 字段索引
- idx_password_history_password_set_at: password_set_at 字段索引
- idx_password_history_is_expired: is_expired 字段索引

## 7. 数据验证和约束

### 7.1 数据库约束

**NOT NULL 约束：**
- User: username, password_hash
- Landlord: name, phone
- House: title, rent_price, owner_id
- Room: room_number, rent_price, house_id
- Tenant: name, phone
- Contract: contract_no, title, start_date, end_date, rent_amount, deposit_amount, house_id, tenant_id
- LandlordContract: contract_no, title, start_date, end_date, contract_amount, service_fee_rate, landlord_id
- Payment: payment_no, amount, payment_type, due_date
- DepositRefund: contract_id, tenant_id, house_id, original_deposit, refund_amount
- Media: file_name, file_path, file_type

**UNIQUE 约束：**
- User.username: 用户名唯一
- User.email: 邮箱唯一（可为空）
- User.phone: 手机号唯一
- Contract.contract_no: 合同编号唯一
- LandlordContract.contract_no: 承包合同编号唯一
- Payment.payment_no: 支付编号唯一
- BackupRecord.backup_id: 备份ID唯一
- Room: (house_id, room_number) 房源内房间编号唯一

**FOREIGN KEY 约束：**
- House.owner_id → Users.id（负责管理的员工）
- House.landlord_id → Landlords.id（房源所有者）
- Room.house_id → Houses.id
- Contract.house_id → Houses.id
- Contract.room_id → Rooms.id（可选，合租时）
- Contract.tenant_id → Tenants.id
- Contract.original_contract_id → Contracts.id（续签时）
- LandlordContract.landlord_id → Landlords.id
- Payment.contract_id → Contracts.id
- Payment.operator_id → Users.id
- DepositRefund.contract_id → Contracts.id
- DepositRefund.tenant_id → Tenants.id
- DepositRefund.house_id → Houses.id
- DepositRefund.processed_by → Users.id
- Media.house_id → Houses.id（可为空）
- Media.uploaded_by → Users.id
- User.created_by → Users.id
- PasswordHistory.user_id → Users.id

### 7.2 应用层验证

- **角色权限验证：** User.has_permission(permission)
- **身份证号验证：** Tenant.verify_id_card(), Landlord.verify_id_card(), User.verify_id_card()
- **房源状态自动更新：** House.update_status()
- **滞纳金自动计算：** Payment.calculate_late_fee()
- **账号锁定检查：** User.is_account_locked()
- **合同到期检查：** Contract.is_expired(), Contract.is_expiring_soon()
- **支付状态检查：** Payment.is_overdue()
- **承包合同到期检查：** LandlordContract.is_expired(), LandlordContract.is_expiring_soon()
- **MIME 类型验证：** Media.is_allowed_type()
- **密码历史检查：** PasswordHistory.check_password_in_history()
- **密码过期检查：** PasswordHistory.is_password_expired()
- **押金状态验证：** Contract.update_deposit_status(), Contract.can_transfer_deposit()
- **乐观锁验证：** Contract.check_version(), Contract.update_with_optimistic_lock()
- **退款状态验证：** DepositRefund.can_complete()

### 7.3 安全特性

**加密存储：**
- 密码加密：使用 Werkzeug 的 generate_password_hash/check_password_hash
- 身份证号加密：Tenant 和 Landlord 使用 AES-256-GCM 加密存储
- 银行卡号加密：Landlord 使用 AES-256-GCM 加密存储
- 支持向后兼容旧的 Fernet 加密数据

**认证和授权：**
- JWT Token 认证：User.generate_token(), User.verify_token()
- 角色权限控制：admin 拥有所有权限，staff 仅有基础权限
- 账号锁定机制：连续登录失败 5 次锁定 30 分钟

**敏感数据处理：**
- 敏感字段自动过滤：to_dict() 方法自动移除 password_hash, id_card_encrypted, bank_card_encrypted 等
- 银行卡号脱敏：Landlord.mask_bank_card() 显示脱敏后的银行卡号
- 身份证号脱敏：User.to_dict() 自动脱敏身份证号

**审计日志：**
- 加密操作审计：EncryptionAuditLog 记录所有加密/解密操作
- 敏感数据访问审计：SensitiveDataAuditLog 记录所有敏感数据访问
- 访问预警：检测短时间内频繁访问敏感数据的行为

**密码安全：**
- 密码历史记录：防止重复使用最近 5 个密码
- 密码过期管理：支持密码过期时间设置
- 密码过期提醒：提前通知用户密码即将过期

**乐观锁机制：**
- 合同并发更新保护：Contract.version 字段
- 版本冲突检测：OptimisticLockError 异常

## 8. SQLAlchemy ORM 最佳实践

### 8.1 模型继承

使用抽象基类 BaseModel，提供通用字段：
- id：主键
- created_at：创建时间
- updated_at：更新时间
- is_active：是否激活
- deleted_at：软删除时间戳

### 8.2 关系定义

**加载策略：**
- `lazy='dynamic'`：延迟加载，支持链式查询（如 House.rooms, User.houses）
- `lazy='joined'`：连接加载，立即加载关联对象（如 House.owner, House.landlord_rel）
- `lazy='selectin'`：IN 加载，适用于集合关系（如 Contract.payments）

**双向关系：**
- `back_populates='owner'`：House ↔ User（负责员工）
- `back_populates='landlord_rel'`：House ↔ Landlord（房东）
- `back_populates='tenant_rel'`：Contract ↔ Tenant（租客）
- `back_populates='payments'`：Payment ↔ Contract（支付）
- `backref='house'`：Room → House（房间）

**级联删除：**
- `cascade='all, delete-orphan'`：级联删除（如 House → Room, House → Media）

**外键指定：**
- `foreign_keys`：明确指定外键字段（如 User.created_employees, Media.uploaded_by）

### 8.3 序列化

所有模型实现 to_dict() 方法，支持 API 响应：
- BaseModel.to_dict()：基础实现，转换所有字段，datetime 格式化为字符串
- 子类重写 to_dict()：添加关联对象信息
- 敏感字段过滤：to_dict() 方法自动移除敏感字段

### 8.4 业务逻辑封装

将业务逻辑封装在模型方法中，保持业务规则与数据模型紧密耦合：
- User：权限检查、密码管理、JWT Token、账号锁定
- House：状态自动更新、空闲房间查询
- Landlord/Tenant：身份证号加密/解密验证
- Contract：到期检查、租金计算、押金状态管理、乐观锁
- Payment：滞纳金精确计算、支付状态管理
- DepositRefund：扣款项管理、退款状态跟踪
- Media：MIME 类型验证、文件大小格式化
- LandlordContract：服务费计算、合同期限计算
- PasswordHistory：密码历史管理、过期检查

### 8.5 事件监听器

使用 SQLAlchemy 事件监听器实现自动化处理：
- Room.after_update：房间状态变化时自动更新房源状态
- Contract.after_update：合同终止时自动取消未支付记录

## 9. 模型使用示例

```python
from datetime import date, timedelta, datetime
from app import create_app, db
from app.models import (
    User, House, Room, Tenant, Contract, Payment, Media, 
    Landlord, LandlordContract, EncryptionAuditLog, 
    SensitiveDataAuditLog, BackupRecord, PasswordHistory
)

app = create_app()

with app.app_context():
    # ==================== 1. 用户管理 ====================
    # 创建管理员
    admin = User(
        username='admin',
        email='admin@example.com',
        phone='13800138000',
        role='admin',
        name='张管理员',
        position='经理'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.flush()
    
    # 创建员工
    staff = User(
        username='staff001',
        email='staff@example.com',
        phone='13900139000',
        role='staff',
        name='李员工',
        position='业务员',
        created_by=admin.id
    )
    staff.set_password('staff123')
    db.session.add(staff)
    db.session.flush()
    
    # 权限检查
    if admin.has_permission('delete'):
        print("管理员有删除权限")
    if not staff.has_permission('delete'):
        print("普通员工无删除权限")
    
    # ==================== 2. 房东管理 ====================
    landlord = Landlord(
        name='王房东',
        phone='13700137000',
        bank_name='中国工商银行北京分行',
        property_cert_no='京房权证朝私字第123456号',
        address='北京市朝阳区某某小区3号楼',
        remark='优质房东'
    )
    landlord.set_id_card('110101199001011234', user_id=admin.id)
    landlord.set_bank_card('6222001234567890123', user_id=admin.id)
    db.session.add(landlord)
    db.session.flush()
    
    # 获取脱敏银行卡号
    masked_card = landlord.mask_bank_card()
    print(f"银行卡号：{masked_card}")  # 输出：**** **** **** 0123
    
    # ==================== 3. 房源管理 ====================
    house = House(
        title='科技园区合租公寓',
        description='靠近地铁站，交通便利',
        city='北京市',
        district='海淀区',
        address='中关村大街1号',
        area=120.5,
        room_count=3,
        hall_count=1,
        bathroom_count=2,
        floor='中层',
        total_floors=18,
        rent_price=12000.0,
        deposit=12000.0,
        payment_method='押一付三',
        rental_type='shared',
        facilities={'wifi': True, 'ac': True, 'heater': True, 'kitchen': True},
        owner_id=staff.id,
        landlord_id=landlord.id
    )
    db.session.add(house)
    db.session.flush()
    
    # 添加房间
    room1 = Room(
        room_number='101',
        name='主卧',
        description='朝南，带阳台',
        area=25.0,
        direction='南',
        rent_price=5000.0,
        deposit=5000.0,
        facilities={'bed': True, 'desk': True, 'ac': True, 'balcony': True},
        house_id=house.id
    )
    db.session.add(room1)
    
    # ==================== 4. 租客管理 ====================
    tenant = Tenant(
        name='王小明',
        phone='13700137000',
        email='wang@example.com',
        company='某科技公司',
        occupation='工程师',
        emergency_contact='张大明',
        emergency_phone='13600136000',
        emergency_relation='父亲'
    )
    tenant.set_id_card('110101199001011234', user_id=admin.id)
    db.session.add(tenant)
    db.session.flush()
    
    # ==================== 5. 合同管理 ====================
    contract = Contract(
        contract_no=Contract.generate_contract_no(),
        title='科技园区合租公寓101房间租赁合同',
        description='标准租赁合同',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        rent_amount=5000.0,
        deposit_amount=5000.0,
        payment_type='季付',
        payment_cycle=3,
        status='active',
        house_id=house.id,
        room_id=room1.id,
        tenant_id=tenant.id
    )
    db.session.add(contract)
    
    # 创建承包合同
    landlord_contract = LandlordContract(
        contract_no=LandlordContract.generate_contract_no(),
        title='平台与王房东承包合同',
        description='承包王房东的所有房源',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        contract_amount=100000.0,
        service_fee_rate=5.0,
        minimum_fee=5000.0,
        payment_cycle=3,
        status='active',
        landlord_id=landlord.id,
        house_ids=[house.id]
    )
    db.session.add(landlord_contract)
    db.session.commit()
    
    # 更新房间和房源状态
    room1.status = 'rented'
    house.update_status()
    
    # ==================== 6. 支付管理 ====================
    payment = Payment(
        payment_no=Payment.generate_payment_no(),
        amount=5000.0,
        payment_type='rent',
        period_start=date.today(),
        period_end=date.today() + timedelta(days=90),
        due_date=date.today() + timedelta(days=7),
        contract_id=contract.id,
        operator_id=staff.id
    )
    db.session.add(payment)
    db.session.commit()
    
    # 标记为已支付
    payment.mark_as_paid(
        paid_amount=5000.0,
        payment_date=date.today(),
        payment_method='wechat'
    )
    db.session.commit()
    
    # 计算滞纳金
    late_fee, overdue_days = payment.calculate_late_fee()
    total_amount = payment.get_total_amount()
    
    # ==================== 7. 多媒体管理 ====================
    media = Media(
        file_name='room_101.jpg',
        file_path='/uploads/houses/1/room_101.jpg',
        file_url='http://example.com/uploads/houses/1/room_101.jpg',
        file_type='image',
        mime_type='image/jpeg',
        file_size=204800,
        description='主卧实拍',
        is_cover=True,
        sort_order=1,
        house_id=house.id,
        uploaded_by=admin.id
    )
    db.session.add(media)
    db.session.commit()
    
    # ==================== 8. 查询示例 ====================
    # 查询用户管理的所有房源
    user_houses = staff.houses.all()
    
    # 查询房东的所有房源
    landlord_houses = landlord.houses.all()
    
    # 查询房源的空闲房间
    available_rooms = house.get_available_rooms()
    
    # 查询即将到期的合同
    expiring_contracts = Contract.query.filter(
        Contract.status == 'active'
    ).all()
    for c in expiring_contracts:
        if c.is_expiring_soon(30):
            print(f"合同 {c.contract_no} 即将到期，剩余 {c.get_days_until_expiry()} 天")
    
    # 查询逾期支付
    overdue_payments = Payment.query.filter(
        Payment.status == 'overdue'
    ).all()
    
    # ==================== 9. 软删除示例 ====================
    # 软删除
    house.soft_delete()
    
    # 查询已删除记录
    deleted_houses = House.query.only_deleted().all()
    
    # 恢复删除
    house.restore()
    
    # 包含已删除记录的查询
    all_houses = House.query.with_deleted().all()
    
    # ==================== 10. 审计日志查询 ====================
    # 获取加密操作统计
    encryption_stats = EncryptionAuditLog.get_statistics()
    
    # 获取敏感数据访问统计
    sensitive_stats = SensitiveDataAuditLog.get_statistics()
    
    # 获取用户活动摘要
    user_activity = SensitiveDataAuditLog.get_user_activity_summary(user_id=admin.id)
    
    # 获取敏感数据访问预警
    alerts = SensitiveDataAuditLog.get_sensitive_access_alert(threshold=10, hours=1)
    
    # ==================== 11. 密码管理 ====================
    # 检查密码是否在历史记录中
    is_in_history = PasswordHistory.check_password_in_history(
        user_id=admin.id, 
        password='admin123'
    )
    
    # 获取密码使用天数
    password_age = PasswordHistory.get_user_password_age(user_id=admin.id)
    
    # 检查密码是否过期
    is_expired = PasswordHistory.is_password_expired(user_id=admin.id)
    
    # 获取距离密码过期的天数
    days_until_expiry = PasswordHistory.get_days_until_expiry(user_id=admin.id)
    
    # ==================== 12. 备份管理 ====================
    # 获取最近成功的备份
    recent_backups = BackupRecord.get_latest_successful(limit=10)
    
    # 获取备份统计
    backup_stats = BackupRecord.get_statistics(days=30)
    
    # 获取备份设置
    backup_settings = BackupSettings.get_settings()
    
    # 更新备份设置
    BackupSettings.update_settings({
        'enabled': True,
        'frequency': 'daily',
        'backup_time': '03:00'
    })
```

## 10. 扩展性考虑

### 10.1 性能优化

- **数据库索引**：已为所有外键字段和常用查询字段创建索引
- **查询优化**：使用 lazy='dynamic' 延迟加载，避免 N+1 查询问题
- **批量操作**：使用 db.session.add_all() 批量插入数据
- **分页查询**：使用 paginate() 方法进行分页

### 10.2 分表策略

当数据量增长时，可考虑：
- **Payment 表按时间分表**：按月或年分表
- **Contract 表按状态分表**：将历史合同和当前合同分开存储
- **审计日志表按时间分表**：按月分表存储审计日志

### 10.3 读写分离

使用 SQLAlchemy 的 binds 配置，支持主从数据库：
```python
SQLALCHEMY_BINDS = {
    'master': 'mysql://user:password@master/db',
    'slave': 'mysql://user:password@slave/db'
}
```

### 10.4 缓存层

可在查询频繁的地方添加 Redis 缓存：
- 房源列表查询：缓存热门区域的房源列表
- 统计数据查询：缓存仪表盘统计数据
- 用户信息缓存：缓存频繁访问的用户信息
- 配置信息缓存：缓存系统配置参数

### 10.5 水平扩展

- **微服务架构**：将用户服务、房源服务、合同服务、支付服务拆分
- **API 网关**：统一入口，负载均衡
- **消息队列**：使用 RabbitMQ/Kafka 处理异步任务

### 10.6 监控和日志

- **数据库监控**：慢查询日志、连接池监控
- **业务监控**：合同到期率、支付逾期率、房源出租率
- **安全监控**：敏感数据访问预警、异常登录检测
- **错误追踪**：使用 Sentry 等工具追踪异常

## 11. 总结

本数据库模型设计具有以下特点：

1. **完整性**：覆盖房源、租客、合同、支付全流程，支持整租/合租两种租赁模式，包含房东管理和承包合同管理

2. **安全性**：
   - 密码加密存储（Werkzeug generate_password_hash）
   - 身份证号和银行卡号 AES-256-GCM 加密存储
   - JWT Token 认证
   - 敏感字段自动过滤
   - 银行卡号脱敏显示
   - 账号锁定机制
   - 密码历史记录防止重复使用

3. **审计能力**：
   - 加密操作审计日志
   - 敏感数据访问审计日志
   - 备份记录管理
   - 访问预警机制

4. **灵活性**：支持多种支付方式、付款周期、租赁类型，适应不同业务场景需求

5. **可扩展**：模型设计符合 SOLID 原则，预留扩展字段，易于功能扩展

6. **性能优化**：
   - 合理的索引设计
   - 使用 lazy='dynamic' 和 lazy='joined' 优化加载策略
   - 避免 N+1 查询问题

7. **业务逻辑封装**：将业务逻辑封装在模型方法中

8. **最佳实践**：遵循 SQLAlchemy ORM 规范，使用抽象基类、关系定义、序列化方法等

9. **数据一致性**：通过外键约束、唯一约束、NOT NULL 约束保证数据完整性

10. **审计跟踪**：记录创建时间、更新时间、操作人等信息，便于审计追踪

11. **软删除支持**：所有模型支持软删除，数据可恢复

12. **角色分离**：User 表仅用于内部员工，Landlord 表管理房东信息，职责清晰

13. **平台模式**：支持平台与房东的承包合作模式，通过 LandlordContract 实现灵活的商业模式

14. **押金管理**：支持押金状态跟踪、押金转移（续签）、押金退款流程

15. **乐观锁机制**：合同并发更新保护，防止数据冲突

16. **数据归档**：支持合同和支付记录的归档，优化数据库性能
