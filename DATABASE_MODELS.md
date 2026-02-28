# 房屋租赁系统数据库模型设计说明

## 1. 数据库模型概览

本系统采用 SQLAlchemy ORM 框架设计数据库模型，包含以下 7 个核心模型：

| 模型名称 | 表名 | 描述 |
|---------|------|------|
| User | users | 用户表（管理员、普通员工，支持员工管理） |
| House | houses | 房源表（支持整租/合租，含地址、配套设施） |
| Room | rooms | 房间表（合租场景，独立租金和状态） |
| Tenant | tenants | 租客表（含紧急联系人、工作信息） |
| Contract | contracts | 合同表（支持合租合同，自动编号） |
| Payment | payments | 支付记录表（支持滞纳金、多种支付方式） |
| Media | media | 多媒体文件表（图片/视频/文档） |

## 2. 数据库关系图

```
┌─────────────┐
│    User     │
│  (用户表)    │
└──────┬──────┘
       │ 1:N
       ├──────────────────────────────────────────────┐
       │                                              │
       ▼                                              ▼
┌─────────────┐                              ┌─────────────┐
│    House    │                              │   Tenant    │
│  (房源表)    │                              │  (租客表)    │
└──────┬──────┘                              └──────┬──────┘
       │ 1:N                                        │ 1:N
       │                                            │
       ▼                                            ▼
┌─────────────┐                              ┌─────────────┐
│    Room     │                              │  Contract   │
│  (房间表)    │                              │  (合同表)    │
└──────┬──────┘                              └──────┬──────┘
       │                                            │
       │ N:1 (合租)                                 │ 1:N
       └────────────────────────────────────────────┘
                                                    │
                                                    ▼
                                           ┌─────────────┐
                                           │   Payment   │
                                           │  (支付表)    │
                                           └─────────────┘

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

**关系说明：**
- User 1:N House：一个用户（房东）拥有多个房源
- User 1:N Contract（作为房东）：一个房东有多个合同
- User 1:N Media：一个用户上传多个媒体文件
- User 1:N Payment（作为操作员）：一个操作员处理多个支付
- House 1:N Room：一个房源有多个房间（合租模式）
- House 1:N Contract：一个房源有多个合同
- House 1:N Media：一个房源有多个媒体文件
- Room N:1 Contract：房间关联到合同（合租时）
- Tenant 1:N Contract：一个租客有多个合同
- Contract 1:N Payment：一个合同有多个支付记录

## 3. 表关系详细说明

### 3.1 User（用户表）

**关系：**
- 1:N → House（用户拥有多个房源）
- 1:N → Contract（作为房东有多个合同）
- 1:N → Media（用户上传多个媒体文件）
- 1:N → Payment（操作员处理多个支付）
- 1:N → User（管理员创建的员工）

**字段说明：**
```python
- id: 主键
- username: 用户名（唯一）
- email: 邮箱（唯一）
- password_hash: 密码哈希
- role: 角色（admin/staff）
- user_type: 用户类型（admin/landlord/tenant）
- name: 姓名
- phone: 手机号（唯一）
- id_card: 身份证号
- id_card_hash: 身份证号哈希（用于去重验证）
- position: 职位
- status: 员工状态（active/resigned/disabled）
- avatar: 头像 URL
- last_login: 最后登录时间
- login_attempts: 登录失败次数
- locked_until: 锁定截止时间
- created_by: 创建人（外键）
```

**权限控制：**
- admin：拥有所有权限（查看、创建、编辑、删除）
- staff：仅有基础权限（查看、创建、编辑），无删除权限

**业务方法：**
- has_permission(permission): 检查用户权限
- set_password(password): 设置密码
- check_password(password): 验证密码
- generate_token(expires_in): 生成 JWT token
- verify_token(token): 验证 JWT token
- set_id_card(id_card_number): 设置身份证号并生成哈希
- verify_id_card(id_card_number): 验证身份证号是否匹配
- is_account_locked(): 检查账号是否被锁定
- record_login_attempt(success): 记录登录尝试
- to_dict(include_details): 转换为字典（自动移除敏感字段）

### 3.2 House（房源表）

**关系：**
- N:1 → User（房源属于某个用户/房东）
- 1:N → Room（房源包含多个房间）
- 1:N → Contract（房源有多个合同）
- 1:N → Media（房源有多个媒体文件）

**字段说明：**
```python
- id: 主键
- title: 房源标题
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
- rent_price: 租金（元/月）
- deposit: 押金（元）
- payment_method: 付款方式
- status: 状态（available/rented/maintenance/partially_rented）
- facilities: 配套设施（JSON）
- images: 房源图片列表（JSON，保留字段）
- cover_image: 封面图片
- rental_type: 租赁类型（whole/shared）
- owner_id: 房东 ID（外键）
```

**状态管理：**
- 整租模式：根据合同状态自动更新（available/rented）
- 合租模式：根据房间状态计算（available/partially_rented/rented）

**业务方法：**
- update_status(): 根据房间状态更新房源状态
- get_room_count(): 获取房间数量
- get_available_rooms(): 获取空闲房间列表
- to_dict(): 转换为字典（包含房源和房间信息）

### 3.3 Room（房间表）

**关系：**
- N:1 → House（房间属于某个房源）
- 1:N → Contract（房间有多个合同）

**字段说明：**
```python
- id: 主键
- room_number: 房间编号（同一房源内唯一）
- name: 房间名称（如：主卧、次卧 A）
- description: 房间描述
- area: 房间面积（平方米）
- floor: 楼层
- direction: 朝向（南/北/东/西）
- rent_price: 房间租金（元/月）
- deposit: 押金（元）
- facilities: 配套设施（JSON）
- status: 状态（available/rented/maintenance）
- house_id: 房源 ID（外键）
```

**索引：**
- idx_rooms_house_id: 房源 ID 索引
- idx_rooms_status: 状态索引
- idx_rooms_house_number: 房源 ID+ 房间编号唯一索引

**业务方法：**
- to_dict(): 转换为字典（包含房源信息）

### 3.4 Tenant（租客表）

**关系：**
- 1:N → Contract（租客有多个合同）

**字段说明：**
```python
- id: 主键
- name: 姓名
- id_card: 身份证号
- id_card_hash: 身份证号哈希（用于去重验证）
- phone: 联系电话
- email: 邮箱
- emergency_contact: 紧急联系人姓名
- emergency_phone: 紧急联系人电话
- emergency_relation: 与紧急联系人关系
- company: 工作单位
- occupation: 职业
- status: 状态（active/expired/blacklisted）
- remark: 备注
```

**安全特性：**
- 身份证号哈希存储，支持去重验证
- to_dict() 方法自动移除敏感字段

**业务方法：**
- set_id_card(id_card_number): 设置身份证号并生成哈希
- verify_id_card(id_card_number): 验证身份证号是否匹配
- get_active_contracts(): 获取当前有效的合同
- get_current_houses(): 获取当前租住的房源
- to_dict(): 转换为字典（自动移除敏感字段）

### 3.5 Contract（合同表）

**关系：**
- N:1 → House（合同关联房源）
- N:1 → Room（合同关联房间，合租时）
- N:1 → Tenant（合同关联租客）
- N:1 → User（合同关联房东）
- 1:N → Payment（合同有多个支付记录）

**字段说明：**
```python
- id: 主键
- contract_no: 合同编号（自动生成，唯一）
- title: 合同标题
- description: 合同描述
- start_date: 起租日期
- end_date: 结束日期
- rent_amount: 租金金额（元/月）
- deposit_amount: 押金金额（元）
- payment_type: 付款类型（月付/季付/半年付/年付）
- payment_cycle: 付款周期（月数）
- status: 状态（draft/active/expired/terminated）
- contract_file: 合同文件路径
- remark: 备注
- house_id: 房源 ID（外键）
- room_id: 房间 ID（外键，合租时）
- landlord_id: 房东 ID（外键）
- tenant_id: 租客 ID（外键）
```

**业务方法：**
- generate_contract_no(): 生成合同编号（类方法）
- is_expired(): 检查是否过期
- is_expiring_soon(days): 检查是否即将到期
- get_days_until_expiry(): 获取距离到期天数
- calculate_total_rent(): 计算合同期内的总租金
- to_dict(): 转换为字典（包含房源、房间、租客信息）

### 3.6 Payment（支付表）

**关系：**
- N:1 → Contract（支付属于某个合同）
- N:1 → User（操作员）

**字段说明：**
```python
- id: 主键
- payment_no: 支付编号（自动生成，唯一）
- amount: 应缴金额
- paid_amount: 实缴金额
- payment_type: 类型（rent/deposit/utility/other）
- payment_method: 方式（cash/bank/wechat/alipay）
- period_start: 支付周期开始
- period_end: 周期结束
- due_date: 应缴日期
- payment_date: 实际支付日期
- confirmed_date: 确认到账日期
- late_fee: 滞纳金金额
- late_fee_rate: 滞纳金比例（每日）
- overdue_days: 逾期天数
- status: 状态（pending/paid/overdue/partial/refunded）
- remark: 备注
- receipt_file: 收据/凭证文件路径
- contract_id: 合同 ID（外键）
- operator_id: 操作员 ID（外键）
```

**滞纳金计算：**
- 日利率：0.05%（可配置，LATE_FEE_RATE）
- 上限：20%（可配置，LATE_FEE_MAX_RATE）
- 公式：滞纳金 = 应缴金额 × 日利率 × 逾期天数

**业务方法：**
- generate_payment_no(): 生成支付编号（类方法）
- calculate_late_fee(current_date): 计算滞纳金
- get_total_amount(): 获取应缴总额（含滞纳金）
- mark_as_paid(paid_amount, payment_date, payment_method): 标记为已支付
- is_overdue(current_date): 检查是否逾期
- get_days_until_due(): 获取距离到期天数
- to_dict(): 转换为字典（包含合同、租客、操作员信息）

### 3.7 Media（多媒体表）

**关系：**
- N:1 → House（媒体属于某个房源）
- N:1 → User（上传人）

**字段说明：**
```python
- id: 主键
- file_name: 原始文件名
- file_path: 文件存储路径
- file_url: 文件访问 URL
- file_type: 类型（image/video/document）
- mime_type: 文件 MIME 类型
- file_size: 文件大小（字节）
- description: 文件描述
- sort_order: 排序顺序
- is_cover: 是否为封面图片
- house_id: 房源 ID（外键）
- uploaded_by: 上传人 ID（外键）
```

**支持的 MIME 类型：**
- 图片：image/jpeg, image/png, image/gif, image/webp
- 视频：video/mp4, video/quicktime, video/x-msvideo
- 文档：application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document, application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

**业务方法：**
- get_file_type(mime_type): 根据 MIME 类型判断文件类型（类方法）
- is_allowed_type(mime_type): 检查 MIME 类型是否允许（类方法）
- get_file_size_formatted(): 获取格式化后的文件大小
- to_dict(): 转换为字典（包含上传者信息）

## 4. 索引设计

### 4.1 User 表索引
- idx_users_username: username 字段索引
- idx_users_role: role 字段索引
- idx_users_email: email 字段索引
- idx_users_phone: phone 字段索引
- idx_users_status: status 字段索引
- idx_users_id_card_hash: id_card_hash 字段索引

### 4.2 House 表索引
- idx_houses_status: status 字段索引
- idx_houses_city: city 字段索引
- idx_houses_district: district 字段索引
- idx_houses_rental_type: rental_type 字段索引
- idx_houses_owner_id: owner_id 字段索引

### 4.3 Room 表索引
- idx_rooms_house_id: house_id 字段索引
- idx_rooms_status: status 字段索引
- idx_rooms_house_number: (house_id, room_number) 复合唯一索引

### 4.4 Tenant 表索引
- idx_tenants_phone: phone 字段索引
- idx_tenants_id_card_hash: id_card_hash 字段索引
- idx_tenants_status: status 字段索引

### 4.5 Contract 表索引
- idx_contracts_house_id: house_id 字段索引
- idx_contracts_room_id: room_id 字段索引
- idx_contracts_tenant_id: tenant_id 字段索引
- idx_contracts_status: status 字段索引
- idx_contracts_dates: (start_date, end_date) 复合索引，用于日期范围查询

### 4.6 Payment 表索引
- idx_payments_contract_id: contract_id 字段索引
- idx_payments_status: status 字段索引
- idx_payments_due_date: due_date 字段索引
- idx_payments_payment_type: payment_type 字段索引

### 4.7 Media 表索引
- idx_media_house_id: house_id 字段索引
- idx_media_file_type: file_type 字段索引
- idx_media_is_cover: is_cover 字段索引

## 5. 数据验证和约束

### 5.1 数据库约束
- NOT NULL：关键字段非空约束（如 username, email, password_hash, title, start_date, end_date 等）
- UNIQUE：唯一约束字段
  - User.username: 用户名唯一
  - User.email: 邮箱唯一
  - User.phone: 手机号唯一
  - Contract.contract_no: 合同编号唯一
  - Payment.payment_no: 支付编号唯一
  - Room: (house_id, room_number) 房源内房间编号唯一
- FOREIGN KEY：外键约束，保证参照完整性
  - House.owner_id → User.id
  - Room.house_id → House.id
  - Contract.house_id → House.id
  - Contract.room_id → Room.id（可选）
  - Contract.tenant_id → Tenant.id
  - Contract.landlord_id → User.id
  - Payment.contract_id → Contract.id
  - Payment.operator_id → User.id
  - Media.house_id → House.id
  - Media.uploaded_by → User.id
  - User.created_by → User.id

### 5.2 应用层验证
- 角色权限验证：User.has_permission(permission)
- 身份证号哈希验证：Tenant.verify_id_card(id_card_number)
- 房源状态自动更新：House.update_status()
- 滞纳金自动计算：Payment.calculate_late_fee(current_date)
- 账号锁定检查：User.is_account_locked()
- 合同到期检查：Contract.is_expired(), Contract.is_expiring_soon(days)
- 支付状态检查：Payment.is_overdue(current_date)

### 5.3 安全特性
- 密码加密存储：使用 Werkzeug 的 generate_password_hash/check_password_hash
- 身份证号哈希：使用 SHA-256 算法生成哈希值用于去重验证
- JWT Token 认证：User.generate_token(), User.verify_token()
- 敏感字段过滤：to_dict() 方法自动移除 password_hash, id_card, id_card_hash 等敏感字段

## 6. SQLAlchemy ORM 最佳实践

### 6.1 模型继承
使用抽象基类 BaseModel（[app/models/base.py](file://d:\Pro\Housing_ental_system\app\models\base.py)），提供通用字段：
- id：主键（Integer, primary_key, autoincrement）
- created_at：创建时间（DateTime, default=datetime.now）
- updated_at：更新时间（DateTime, default=datetime.now, onupdate=datetime.now）
- is_active：是否激活（Boolean, default=True）

### 6.2 关系定义
- lazy='dynamic'：延迟加载，支持链式查询（如 House.rooms, User.houses）
- backref/back_populates：双向关系
  - backref='house'：Room → House
  - backref='owner'：House → User
  - back_populates='contracts'：Contract ↔ Tenant
- cascade='all, delete-orphan'：级联删除（如 House → Room, House → Media, Contract → Payment）
- foreign_keys：明确指定外键字段（如 User.created_employees 关系）

### 6.3 序列化
所有模型实现 to_dict() 方法，支持 API 响应：
- BaseModel.to_dict()：基础实现，转换所有字段，datetime 格式化为字符串
- 子类重写 to_dict()：添加关联对象信息（如 House.to_dict() 包含 owner_name, available_rooms）
- 敏感字段过滤：User.to_dict() 移除 password_hash, id_card, id_card_hash 等

### 6.4 业务逻辑封装
将业务逻辑封装在模型方法中，保持业务规则与数据模型紧密耦合：
- User 模型：权限检查、密码管理、JWT Token、账号锁定
- House 模型：状态自动更新、空闲房间查询
- Tenant 模型：身份证号验证、有效合同查询
- Contract 模型：到期检查、租金计算
- Payment 模型：滞纳金计算、支付状态管理
- Media 模型：MIME 类型验证、文件大小格式化

### 6.5 类方法
使用类方法实现与具体实例无关的功能：
- Contract.generate_contract_no()：生成合同编号
- Payment.generate_payment_no()：生成支付编号
- Media.get_file_type(mime_type)：根据 MIME 类型判断文件类型
- Media.is_allowed_type(mime_type)：检查 MIME 类型是否允许

## 7. 模型使用示例

```python
from datetime import date, timedelta, datetime
from app import create_app, db
from app.models import User, House, Room, Tenant, Contract, Payment, Media

app = create_app()

with app.app_context():
    # ==================== 1. 用户管理 ====================
    # 1.1 创建管理员用户
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
    
    # 1.2 创建普通员工用户
    staff = User(
        username='staff001',
        email='staff@example.com',
        phone='13900139000',
        role='staff',
        name='李员工',
        position='业务员',
        created_by=admin.id  # 记录创建人
    )
    staff.set_password('staff123')
    db.session.add(staff)
    db.session.flush()
    
    # 1.3 权限检查
    if admin.has_permission('delete'):
        print("管理员有删除权限")
    if not staff.has_permission('delete'):
        print("普通员工无删除权限")
    
    # ==================== 2. 房源管理 ====================
    # 2.1 创建合租房源
    house = House(
        title='科技园区合租公寓',
        description='靠近地铁站，交通便利',
        city='北京市',
        district='海淀区',
        address='中关村大街 1 号',
        area=120.5,
        room_count=3,
        hall_count=1,
        bathroom_count=2,
        floor='中层',
        total_floors=18,
        rent_price=12000.0,
        deposit=12000.0,
        payment_method='押一付三',
        rental_type='shared',  # 合租模式
        facilities={'wifi': True, 'ac': True, 'heater': True, 'kitchen': True},
        owner_id=admin.id
    )
    db.session.add(house)
    db.session.flush()
    
    # 2.2 添加房间
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
    room2 = Room(
        room_number='102',
        name='次卧 A',
        description='朝北',
        area=18.0,
        direction='北',
        rent_price=3800.0,
        deposit=3800.0,
        facilities={'bed': True, 'desk': True, 'ac': True},
        house_id=house.id
    )
    db.session.add_all([room1, room2])
    
    # ==================== 3. 租客管理 ====================
    # 3.1 创建租客
    tenant = Tenant(
        name='王小明',
        phone='13700137000',
        email='wang@example.com',
        id_card='110101199001011234',
        emergency_contact='张大明',
        emergency_phone='13600136000',
        emergency_relation='父亲',
        company='某科技公司',
        occupation='工程师'
    )
    tenant.set_id_card('110101199001011234')  # 自动生成哈希
    db.session.add(tenant)
    db.session.flush()
    
    # ==================== 4. 合同管理 ====================
    # 4.1 创建租赁合同
    contract = Contract(
        contract_no=Contract.generate_contract_no(),
        title='科技园区合租公寓 101 房间租赁合同',
        description='标准租赁合同',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        rent_amount=5000.0,
        deposit_amount=5000.0,
        payment_type='季付',
        payment_cycle=3,
        status='active',
        house_id=house.id,
        room_id=room1.id,  # 合租时关联房间
        tenant_id=tenant.id,
        landlord_id=admin.id
    )
    db.session.add(contract)
    
    # 4.2 更新房间和房源状态
    room1.status = 'rented'
    house.update_status()  # 自动计算房源状态
    
    # ==================== 5. 支付管理 ====================
    # 5.1 创建支付记录
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
    
    # 5.2 标记为已支付
    payment.mark_as_paid(
        paid_amount=5000.0,
        payment_date=date.today(),
        payment_method='wechat'
    )
    db.session.commit()
    
    # 5.3 计算滞纳金
    late_fee, overdue_days = payment.calculate_late_fee()
    total_amount = payment.get_total_amount()
    
    # ==================== 6. 多媒体管理 ====================
    # 6.1 添加房源图片
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
    
    # ==================== 7. 查询示例 ====================
    # 7.1 查询用户的所有房源
    user_houses = admin.houses.all()
    
    # 7.2 查询房源的空闲房间
    available_rooms = house.get_available_rooms()
    
    # 7.3 查询房源的房间数量
    room_count = house.get_room_count()
    
    # 7.4 查询即将到期的合同
    expiring_contracts = Contract.query.filter(
        Contract.status == 'active'
    ).all()
    for c in expiring_contracts:
        if c.is_expiring_soon(30):
            print(f"合同 {c.contract_no} 即将到期，剩余 {c.get_days_until_expiry()} 天")
    
    # 7.5 查询租客的当前租住房源
    current_houses = tenant.get_current_houses()
    
    # 7.6 查询逾期支付
    overdue_payments = Payment.query.filter(
        Payment.status == 'overdue'
    ).all()
    for p in overdue_payments:
        if p.is_overdue():
            print(f"支付 {p.payment_no} 已逾期 {p.overdue_days} 天")
    
    # 7.7 查询房源的封面图片
    cover_media = Media.query.filter(
        Media.house_id == house.id,
        Media.is_cover == True
    ).first()
    
    # ==================== 8. 序列化示例 ====================
    # 8.1 转换为字典（用于 API 响应）
    house_data = house.to_dict()
    contract_data = contract.to_dict()
    payment_data = payment.to_dict()
    tenant_data = tenant.to_dict()  # 自动移除敏感字段
    
    # 8.2 用户详细信息
    user_data = admin.to_dict(include_details=True)
```

## 8. 扩展性考虑

### 8.1 性能优化
- **数据库索引**：已为所有外键字段和常用查询字段创建索引
- **查询优化**：使用 lazy='dynamic' 延迟加载，避免 N+1 查询问题
- **批量操作**：使用 db.session.add_all() 批量插入数据
- **分页查询**：使用 paginate() 方法进行分页，避免一次性加载大量数据

### 8.2 分表策略
当数据量增长时，可考虑：
- **Payment 表按时间分表**：按月或年分表，如 payments_2024_01, payments_2024_02
- **Contract 表按状态分表**：将历史合同和当前合同分开存储
- **Media 表按房源分表**：根据 house_id 范围分表

### 8.3 读写分离
使用 SQLAlchemy 的 binds 配置，支持主从数据库：
```python
SQLALCHEMY_BINDS = {
    'master': 'mysql://user:password@master/db',
    'slave': 'mysql://user:password@slave/db'
}
```

### 8.4 缓存层
可在查询频繁的地方添加 Redis 缓存：
- 房源列表查询：缓存热门区域的房源列表
- 统计数据查询：缓存仪表盘统计数据
- 用户信息缓存：缓存频繁访问的用户信息
- 配置信息缓存：缓存系统配置参数

### 8.5 水平扩展
- **微服务架构**：将用户服务、房源服务、合同服务、支付服务拆分
- **API 网关**：统一入口，负载均衡
- **消息队列**：使用 RabbitMQ/Kafka 处理异步任务（如合同到期提醒、支付提醒）

### 8.6 监控和日志
- **数据库监控**：慢查询日志、连接池监控
- **业务监控**：合同到期率、支付逾期率、房源出租率
- **错误追踪**：使用 Sentry 等工具追踪异常

## 9. 总结

本数据库模型设计具有以下特点：

1. **完整性**：覆盖房源、租客、合同、支付全流程，支持整租/合租两种租赁模式
2. **安全性**：密码加密存储、身份证号哈希验证、JWT Token认证、敏感字段过滤，权限控制完善
3. **灵活性**：支持多种支付方式、付款周期、租赁类型，适应不同业务场景需求
4. **可扩展**：模型设计符合 SOLID 原则，预留扩展字段，易于功能扩展
5. **性能优化**：合理的索引设计，支持高效查询；使用延迟加载避免 N+1 查询问题
6. **业务逻辑封装**：将业务逻辑封装在模型方法中，如合同到期检查、滞纳金计算、房源状态更新
7. **最佳实践**：遵循 SQLAlchemy ORM 规范，使用抽象基类、关系定义、序列化方法等最佳实践
8. **数据一致性**：通过外键约束、唯一约束、NOT NULL 约束保证数据完整性
9. **审计跟踪**：记录创建时间、更新时间、操作人等信息，便于审计追踪
10. **用户体验**：支持多媒体文件管理、房源地理位置、配套设施管理，提升用户体验
