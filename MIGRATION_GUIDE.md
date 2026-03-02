# 房东数据迁移指南

## 概述

本文档详细说明了房屋租赁系统从旧架构迁移到新房东 - 平台承包模式的完整流程。迁移的主要目标是：

1. 将原有的 `user_type='landlord'` 的用户数据清理
2. 从现有房源的 owner 信息推断并创建房东记录
3. 更新房源的 `landlord_id` 字段
4. 更新承包合同的关联关系
5. 验证数据完整性

---

## 迁移前准备

### 1. 系统版本检查

确保系统已更新到支持房东和承包合同功能的版本：

```bash
# 检查是否包含 Landlord 模型
python -c "from app.models.landlord import Landlord; print('Landlord 模型存在')"

# 检查是否包含 LandlordContract 模型
python -c "from app.models.landlord_contract import LandlordContract; print('LandlordContract 模型存在')"

# 检查 House 模型是否有 landlord_id 字段
python -c "from app.models.house import House; print('landlord_id 字段:', hasattr(House, 'landlord_id'))"
```

### 2. 数据备份（**重要**）

**在执行任何迁移操作之前，必须备份数据库！**

```bash
# 方法 1：手动复制数据库文件
cp instance/housing_rental.db instance/housing_rental.db.backup_$(date +%Y%m%d_%H%M%S)

# Windows PowerShell 版本
Copy-Item instance\housing_rental.db instance\housing_rental.db.backup_$(Get-Date -Format "yyyyMMdd_HHmmss")

# 方法 2：使用系统备份功能
python -c "
from app import create_app, db
from app.models import db
import shutil
from datetime import datetime

app = create_app()
with app.app_context():
    db_path = 'instance/housing_rental.db'
    backup_path = f'backups/housing_rental.db.backup_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}'
    shutil.copy2(db_path, backup_path)
    print(f'备份完成：{backup_path}')
"
```

### 3. 检查当前数据状态

```bash
# 检查是否有 user_type='landlord' 的用户
python -c "
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    landlords = User.query.filter_by(user_type='landlord').all()
    if landlords:
        print(f'警告：发现 {len(landlords)} 个 user_type=landlord 的用户')
        for u in landlords:
            print(f'  - {u.username} ({u.name}, {u.phone})')
    else:
        print('✓ 未发现 user_type=landlord 的用户')
"

# 检查房源数量
python -c "
from app import create_app, db
from app.models import House

app = create_app()
with app.app_context():
    houses = House.query.all()
    print(f'房源总数：{len(houses)}')
    with_landlord = House.query.filter(House.landlord_id.isnot(None)).count()
    print(f'已关联房东的房源：{with_landlord}')
    without_landlord = House.query.filter(House.landlord_id.is_(None)).count()
    print(f'未关联房东的房源：{without_landlord}')
"
```

---

## 迁移步骤

### 步骤 1：更新数据库架构

首先需要更新数据库架构，添加新的表和字段。

**方法 A：使用更新脚本（推荐）**

```bash
python -c "import sys; sys.path.insert(0, '.'); from app.migrations.update_schema import update_schema; update_schema()"
```

**方法 B：手动执行**

创建临时脚本 `temp_update_schema.py`:

```python
import sys
sys.path.insert(0, '.')
from app.migrations.update_schema import update_schema

print("开始更新数据库架构...")
update_schema()
print("数据库架构更新完成！")
```

然后执行：

```bash
python temp_update_schema.py
rm temp_update_schema.py  # Windows: del temp_update_schema.py
```

**更新内容：**
- 创建 `landlords` 表
- 创建 `landlord_contracts` 表
- 在 `houses` 表中添加 `landlord_id` 字段
- 在 `houses` 表中添加 `contact_name`, `contact_phone`, `contact_wechat` 字段
- 在 `contracts` 表中添加 `landlord_id` 字段

**预期输出：**
```
开始更新数据库架构...
✓ landlords 表已存在
✓ landlord_contracts 表已存在
✓ houses.landlord_id 字段已存在
✓ houses.contact_name 字段已存在
✓ houses.contact_phone 字段已存在
✓ houses.contact_wechat 字段已存在
✓ contracts.landlord_id 字段已存在
数据库架构更新完成！
```

---

### 步骤 2：执行数据迁移

执行主迁移脚本：

```bash
python run.py migrate_landlord_data
```

或者使用 Python 直接执行：

```python
import sys
sys.path.insert(0, '.')
from app.migrations.migrate_landlord_data import run_migration

print("=" * 60)
print("开始房东数据迁移...")
print("=" * 60)
run_migration()
print("=" * 60)
print("迁移完成！")
print("=" * 60)
```

**迁移过程：**

1. **检查 landlord 用户**
   - 检查是否有 `user_type='landlord'` 的用户
   - 如有，输出警告信息

2. **创建房东记录**
   - 获取所有有房源的用户（通过 `House.owner_id`）
   - 通过手机号匹配检查是否已存在房东记录
   - 创建新的房东记录（如果没有）
   - 生成虚拟身份证号（如果原用户没有）

3. **更新房源 landlord_id**
   - 遍历所有房源
   - 通过手机号或姓名匹配对应的房东
   - 更新房源的 `landlord_id` 字段

4. **更新承包合同关联**
   - 遍历所有承包合同
   - 从关联的房源推断房东
   - 更新合同的 `landlord_id` 字段

5. **验证数据完整性**
   - 检查房源是否都有 `landlord_id`
   - 检查承包合同是否都有 `landlord_id`
   - 检查房东记录是否完整

**预期输出：**
```
============================================================
开始房东数据迁移...
============================================================
[2024-01-01 12:00:00] [INFO] 开始检查 user_type='landlord' 的用户...
[2024-01-01 12:00:00] [INFO] ✓ 未发现 user_type='landlord' 的用户
[2024-01-01 12:00:00] [INFO] 开始从房源 owner 信息创建房东记录...
[2024-01-01 12:00:00] [INFO]   ✓ 创建房东：张三 (phone=13800138000)
[2024-01-01 12:00:00] [INFO] ✓ 房东创建完成：新建 1 个，跳过 0 个
[2024-01-01 12:00:00] [INFO] 开始更新房源的 landlord_id 关联关系...
[2024-01-01 12:00:00] [INFO] ✓ 房源 landlord_id 更新完成：更新 5 个，无匹配房东 0 个
[2024-01-01 12:00:00] [INFO] 开始更新承包合同的关联关系...
[2024-01-01 12:00:00] [INFO] ✓ 承包合同关联关系更新完成：更新 2 个
============================================================
开始验证数据完整性...
============================================================
[2024-01-01 12:00:00] [INFO] 数据统计:
  - 用户总数：2
  - 房东总数：1
  - 房源总数：5
  - 承包合同总数：2
[2024-01-01 12:00:00] [INFO] ✓ 所有房源都有 landlord_id
[2024-01-01 12:00:00] [INFO] ✓ 所有承包合同都有 landlord_id
============================================================
迁移完成！
```

---

### 步骤 3：验证迁移结果

执行验证脚本：

```bash
python -c "
from app import create_app, db
from app.models import User, Landlord, House, LandlordContract

app = create_app()
with app.app_context():
    print('=' * 60)
    print('迁移结果验证')
    print('=' * 60)
    
    # 1. 检查用户
    users = User.query.all()
    landlord_users = User.query.filter_by(user_type='landlord').all()
    print(f'用户总数：{len(users)}')
    print(f'user_type=landlord 的用户：{len(landlord_users)}')
    
    # 2. 检查房东
    landlords = Landlord.query.all()
    print(f'房东总数：{len(landlords)}')
    for l in landlords:
        print(f'  - {l.name} (phone={l.phone}, houses={l.houses.count()})')
    
    # 3. 检查房源
    houses = House.query.all()
    with_landlord = House.query.filter(House.landlord_id.isnot(None)).count()
    print(f'房源总数：{len(houses)}')
    print(f'已关联房东的房源：{with_landlord}')
    
    # 4. 检查承包合同
    contracts = LandlordContract.query.all()
    print(f'承包合同总数：{len(contracts)}')
    for c in contracts:
        print(f'  - {c.contract_no} (landlord={c.landlord.name if c.landlord else None})')
    
    print('=' * 60)
    print('验证完成！')
    print('=' * 60)
"
```

---

## 回滚方法

如果迁移过程中出现问题，可以执行回滚操作。

### 方法 1：使用命令行

```bash
python run.py rollback_landlord_migration
```

### 方法 2：使用 Python 代码

```python
import sys
sys.path.insert(0, '.')
from app.migrations.migrate_landlord_data import run_rollback

print("开始回滚迁移...")
run_rollback()
print("回滚完成！")
```

### 方法 3：手动回滚

创建临时脚本 `temp_rollback.py`:

```python
import sys
sys.path.insert(0, '.')
from app import create_app, db
from app.models import House, LandlordContract, Landlord

app = create_app()
with app.app_context():
    print("开始回滚...")
    
    # 1. 清空所有房源的 landlord_id
    House.query.update({House.landlord_id: None})
    print("✓ 已清空房源的 landlord_id")
    
    # 2. 清空所有承包合同的 landlord_id
    LandlordContract.query.update({LandlordContract.landlord_id: None})
    print("✓ 已清空承包合同的 landlord_id")
    
    # 3. 删除迁移创建的房东记录（通过 remark 字段识别）
    migrated_landlords = Landlord.query.filter(
        Landlord.remark.like('%迁移创建%')
    ).all()
    for landlord in migrated_landlords:
        db.session.delete(landlord)
    print(f"✓ 已删除 {len(migrated_landlords)} 个迁移创建的房东记录")
    
    db.session.commit()
    print("回滚完成！")
```

然后执行：

```bash
python temp_rollback.py
rm temp_rollback.py  # Windows: del temp_rollback.py
```

### 回滚后的状态

回滚成功后，数据库将恢复到迁移前的状态：
- 所有房源的 `landlord_id` 为 NULL
- 所有承包合同的 `landlord_id` 为 NULL
- 迁移创建的房东记录被删除

---

## 注意事项

### 1. 数据备份

**再次强调：在执行迁移之前，必须备份数据库！**

如果迁移失败或数据损坏，可以从备份恢复：

```bash
# 恢复备份
cp instance/housing_rental.db.backup_20240101_120000 instance/housing_rental.db
```

### 2. 身份证号处理

迁移脚本会自动处理身份证号：

- 如果原用户有身份证号，直接使用
- 如果原用户没有身份证号，生成虚拟身份证号（格式：`MIGRATED_{user_id}_{date}`）

**迁移后需要手动补充真实的身份证号信息！**

```bash
# 检查虚拟身份证号
python -c "
from app import create_app, db
from app.models import Landlord

app = create_app()
with app.app_context():
    landlords = Landlord.query.filter(
        Landlord.id_card.like('MIGRATED_%')
    ).all()
    if landlords:
        print(f'发现 {len(landlords)} 个房东使用虚拟身份证号：')
        for l in landlords:
            print(f'  - {l.name}: {l.id_card}')
    else:
        print('✓ 所有房东都有真实身份证号')
"
```

### 3. 电话号码处理

迁移脚本会自动处理电话号码：

- 如果原用户有电话号码，直接使用
- 如果原用户没有电话号码，生成虚拟电话号码（格式：`NO_PHONE_{user_id}`）

**迁移后需要手动补充真实的电话号码信息！**

```bash
# 检查虚拟电话号码
python -c "
from app import create_app, db
from app.models import Landlord

app = create_app()
with app.app_context():
    landlords = Landlord.query.filter(
        Landlord.phone.like('NO_PHONE_%')
    ).all()
    if landlords:
        print(f'发现 {len(landlords)} 个房东使用虚拟电话号码：')
        for l in landlords:
            print(f'  - {l.name}: {l.phone}')
    else:
        print('✓ 所有房东都有真实电话号码')
"
```

### 4. 匹配规则

房源与房东的匹配规则：

1. **优先通过手机号匹配**
   - 房源 owner 的手机号与房东手机号匹配
   
2. **如果手机号匹配失败，尝试通过姓名匹配**
   - 房源 owner 的姓名与房东姓名匹配

3. **如果都失败，标记为"无匹配房东"**
   - 这些房源需要手动关联房东

### 5. 错误处理

迁移过程中遇到错误时：

- 单个记录失败不会影响整体迁移
- 错误信息会记录在日志中
- 可以使用回滚功能恢复到迁移前状态

常见错误及解决方案：

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| NOT NULL constraint failed: landlords.id_card | 原用户没有身份证号 | 迁移脚本已自动处理，生成虚拟身份证号 |
| NOT NULL constraint failed: landlords.phone | 原用户没有电话号码 | 迁移脚本已自动处理，生成虚拟电话号码 |
| 房源无法匹配房东 | 手机号和姓名都不匹配 | 手动更新房源的 landlord_id 字段 |

### 6. 迁移后清理

迁移完成后，建议执行以下清理操作：

1. **补充缺失的身份证号和电话号码**
   ```bash
   # 查看需要补充信息的房东
   python -c "
   from app import create_app, db
   from app.models import Landlord
   
   app = create_app()
   with app.app_context():
       landlords = Landlord.query.filter(
           (Landlord.id_card.like('MIGRATED_%')) | 
           (Landlord.phone.like('NO_PHONE_%'))
       ).all()
       for l in landlords:
           print(f'{l.name}: id_card={l.id_card}, phone={l.phone}')
   "
   ```

2. **手动关联无匹配房东的房源**
   ```bash
   # 查看无匹配房东的房源
   python -c "
   from app import create_app, db
   from app.models import House
   
   app = create_app()
   with app.app_context():
       houses = House.query.filter(House.landlord_id.is_(None)).all()
       for h in houses:
           print(f'{h.title}: owner_id={h.owner_id}')
   "
   ```

3. **更新承包合同的房东关联**
   ```bash
   # 查看无房东关联的承包合同
   python -c "
   from app import create_app, db
   from app.models import LandlordContract
   
   app = create_app()
   with app.app_context():
       contracts = LandlordContract.query.filter(
           LandlordContract.landlord_id.is_(None)
       ).all()
       for c in contracts:
           print(f'{c.contract_no}: house_ids={c.house_ids}')
   "
   ```

---

## 故障排查

### 问题 1: 数据库架构未更新

**错误信息**: `no such column: houses.landlord_id`

**解决方案**: 先运行数据库架构更新脚本

```bash
python -c "import sys; sys.path.insert(0, '.'); from app.migrations.update_schema import update_schema; update_schema()"
```

### 问题 2: NOT NULL 约束失败

**错误信息**: `NOT NULL constraint failed: landlords.id_card`

**解决方案**: 迁移脚本已自动处理，会为缺失的身份证号生成虚拟值

如果仍然失败，检查迁移脚本是否正确执行：

```bash
python -c "
from app import create_app, db
from app.models import Landlord

app = create_app()
with app.app_context():
    landlords = Landlord.query.all()
    for l in landlords:
        print(f'{l.name}: id_card={l.id_card}')
"
```

### 问题 3: 房源无法匹配房东

**现象**: 数据完整性检查显示"发现 X 个房源没有 landlord_id"

**解决方案**: 

1. 检查房源 owner 的手机号和姓名信息
   ```bash
   python -c "
   from app import create_app, db
   from app.models import House, User
   
   app = create_app()
   with app.app_context():
       houses = House.query.filter(House.landlord_id.is_(None)).all()
       for h in houses:
           owner = h.owner
           if owner:
               print(f'{h.title}: owner={owner.name}, phone={owner.phone}')
           else:
               print(f'{h.title}: no owner')
   "
   ```

2. 手动更新房源的 `landlord_id` 字段
   ```python
   from app import create_app, db
   from app.models import House, Landlord
   
   app = create_app()
   with app.app_context():
       # 找到对应的房东
       landlord = Landlord.query.filter_by(phone='13800138000').first()
       
       # 更新房源
       house = House.query.get(1)
       house.landlord_id = landlord.id
       db.session.commit()
   ```

### 问题 4: 承包合同无法匹配房东

**现象**: 数据完整性检查显示"发现 X 个承包合同没有 landlord_id"

**解决方案**:

1. 检查承包合同的 house_ids
   ```bash
   python -c "
   from app import create_app, db
   from app.models import LandlordContract, House
   
   app = create_app()
   with app.app_context():
       contracts = LandlordContract.query.filter(
           LandlordContract.landlord_id.is_(None)
       ).all()
       for c in contracts:
           print(f'{c.contract_no}: house_ids={c.house_ids}')
           if c.house_ids:
               houses = House.query.filter(House.id.in_(c.house_ids)).all()
               for h in houses:
                   print(f'  - house {h.id}: landlord_id={h.landlord_id}')
   "
   ```

2. 从房源推断房东并更新
   ```python
   from app import create_app, db
   from app.models import LandlordContract, House
   
   app = create_app()
   with app.app_context():
       contracts = LandlordContract.query.filter(
           LandlordContract.landlord_id.is_(None)
       ).all()
       for c in contracts:
           if c.house_ids:
               # 从第一个房源获取房东
               house = House.query.get(c.house_ids[0])
               if house and house.landlord_id:
                   c.landlord_id = house.landlord_id
       db.session.commit()
   ```

---

## 相关文件

- [`app/migrations/migrate_landlord_data.py`](file:///d:/Pro/Housing_ental_system/app/migrations/migrate_landlord_data.py) - 主迁移脚本
- [`app/migrations/update_schema.py`](file:///d:/Pro/Housing_ental_system/app/migrations/update_schema.py) - 数据库架构更新脚本
- [`app/models/landlord.py`](file:///d:/Pro/Housing_ental_system/app/models/landlord.py) - 房东模型
- [`app/models/house.py`](file:///d:/Pro/Housing_ental_system/app/models/house.py) - 房源模型
- [`app/models/landlord_contract.py`](file:///d:/Pro/Housing_ental_system/app/models/landlord_contract.py) - 承包合同模型

---

## 技术支持

如有问题，请：

1. 查看迁移日志
2. 检查数据库备份
3. 验证数据完整性
4. 联系技术支持团队

---

## 附录：完整迁移示例

### 完整迁移流程

```bash
# 1. 备份数据库
cp instance/housing_rental.db instance/housing_rental.db.backup_$(date +%Y%m%d_%H%M%S)

# 2. 检查当前数据状态
python -c "
from app import create_app, db
from app.models import User, House

app = create_app()
with app.app_context():
    print('迁移前数据状态:')
    print(f'  用户总数：{User.query.count()}')
    print(f'  landlord 用户：{User.query.filter_by(user_type=\"landlord\").count()}')
    print(f'  房源总数：{House.query.count()}')
"

# 3. 更新数据库架构
python -c "import sys; sys.path.insert(0, '.'); from app.migrations.update_schema import update_schema; update_schema()"

# 4. 执行数据迁移
python run.py migrate_landlord_data

# 5. 验证迁移结果
python -c "
from app import create_app, db
from app.models import User, Landlord, House, LandlordContract

app = create_app()
with app.app_context():
    print('迁移后数据状态:')
    print(f'  用户总数：{User.query.count()}')
    print(f'  房东总数：{Landlord.query.count()}')
    print(f'  房源总数：{House.query.count()}')
    print(f'  已关联房东的房源：{House.query.filter(House.landlord_id.isnot(None)).count()}')
    print(f'  承包合同总数：{LandlordContract.query.count()}')
"

# 6. 检查需要补充的信息
python -c "
from app import create_app, db
from app.models import Landlord

app = create_app()
with app.app_context():
    landlords = Landlord.query.filter(
        (Landlord.id_card.like('MIGRATED_%')) | 
        (Landlord.phone.like('NO_PHONE_%'))
    ).all()
    if landlords:
        print('需要补充信息的房东:')
        for l in landlords:
            print(f'  {l.name}: id_card={l.id_card}, phone={l.phone}')
    else:
        print('✓ 所有房东信息完整')
"
```

### 回滚流程

```bash
# 1. 执行回滚
python run.py rollback_landlord_migration

# 2. 验证回滚结果
python -c "
from app import create_app, db
from app.models import House, LandlordContract

app = create_app()
with app.app_context():
    print('回滚后数据状态:')
    print(f'  无 landlord_id 的房源：{House.query.filter(House.landlord_id.is_(None)).count()}')
    print(f'  无 landlord_id 的承包合同：{LandlordContract.query.filter(LandlordContract.landlord_id.is_(None)).count()}')
"

# 3. 如需重新迁移，重复完整迁移流程
```
