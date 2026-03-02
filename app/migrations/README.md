# 房东数据迁移脚本使用说明

## 概述

本迁移脚本用于处理房屋租赁系统中房东数据的迁移，主要解决以下问题：

1. 清理 `user_type='landlord'` 的用户数据
2. 从现有房源 owner 信息推断并创建房东记录
3. 更新房源的 `landlord_id` 字段
4. 更新承包合同的关联关系
5. 验证数据完整性

## 文件位置

- **迁移脚本**: `app/migrations/migrate_landlord_data.py`
- **架构更新脚本**: `app/migrations/update_schema.py`

## 使用步骤

### 1. 更新数据库架构（首次运行）

在运行数据迁移之前，需要先更新数据库架构，添加必要的表和字段：

```bash
python -c "import sys; sys.path.insert(0, '.'); from app.migrations.update_schema import update_schema; update_schema()"
```

或创建临时脚本：

```python
import sys
sys.path.insert(0, '.')
from app.migrations.update_schema import update_schema
update_schema()
```

### 2. 执行数据迁移

```bash
python run.py migrate_landlord_data
```

迁移脚本会执行以下操作：

1. **检查 landlord 用户**: 检查是否有 `user_type='landlord'` 的用户，如有则输出警告
2. **创建房东记录**: 从现有房源的 owner 信息推断并创建 Landlord 记录
3. **更新房源关联**: 更新房源表的 `landlord_id` 字段
4. **更新承包合同关联**: 更新承包合同表的房东关联关系
5. **验证数据完整性**: 检查迁移后的数据完整性

### 3. 回滚迁移（如需要）

如果迁移过程中出现问题，可以执行回滚操作：

```bash
python run.py rollback_landlord_migration
```

回滚操作会：
- 清空所有房源的 `landlord_id`
- 清空所有承包合同的 `landlord_id`
- 删除迁移创建的房东记录（通过 remark 字段识别）

## 迁移脚本主要功能

### 1. 检查 landlord 用户

```python
def check_landlord_users(self):
    """检查是否有 user_type='landlord' 的用户"""
```

- 查询所有 `user_type='landlord'` 的用户
- 输出警告信息和用户列表
- 这些用户需要手动处理或迁移到 Landlord 表

### 2. 创建房东记录

```python
def create_landlords_from_house_owners(self):
    """从现有房源 owner 信息推断并创建房东记录"""
```

- 获取所有有房源的用户
- 通过手机号匹配检查是否已存在房东记录
- 创建新的房东记录（如果没有）
- 生成虚拟身份证号（如果原用户没有）

### 3. 更新房源 landlord_id

```python
def update_house_landlord_relations(self):
    """更新房源的 landlord_id 字段"""
```

- 遍历所有房源
- 通过手机号或姓名匹配对应的房东
- 更新房源的 `landlord_id` 字段

### 4. 更新承包合同关联

```python
def update_landlord_contract_relations(self):
    """更新承包合同的关联关系"""
```

- 遍历所有承包合同
- 从关联的房源推断房东
- 更新合同的 `landlord_id` 字段

### 5. 验证数据完整性

```python
def verify_data_integrity(self):
    """验证数据完整性"""
```

检查项目：
- 房源是否都有 `landlord_id`
- 承包合同是否都有 `landlord_id`
- 房东记录是否完整（电话号码等）
- 房源和房东的关联是否有效
- 承包合同和房东的关联是否有效

## 注意事项

### 1. 数据备份

在执行迁移之前，**强烈建议**先备份数据库：

```bash
# 使用系统备份功能或手动备份
cp housing_rental.db housing_rental.db.backup
```

### 2. 身份证号处理

- 如果原用户没有身份证号，系统会生成虚拟身份证号（格式：`MIGRATED_{user_id}_{date}`）
- 迁移后需要手动补充真实的身份证号信息

### 3. 电话号码处理

- 如果原用户没有电话号码，系统会生成虚拟电话号码（格式：`NO_PHONE_{user_id}`）
- 迁移后需要手动补充真实的电话号码信息

### 4. 匹配规则

房源与房东的匹配规则：
1. 优先通过手机号匹配
2. 如果手机号匹配失败，尝试通过姓名匹配
3. 如果都失败，标记为"无匹配房东"

### 5. 错误处理

迁移过程中遇到错误时：
- 单个记录失败不会影响整体迁移
- 错误信息会记录在日志中
- 可以使用回滚功能恢复到迁移前状态

## 迁移日志示例

```
============================================================
开始房东数据迁移...
============================================================
[2026-03-02 14:30:03] [INFO] 开始检查 user_type='landlord' 的用户...
[2026-03-02 14:30:03] [INFO] ✓ 未发现 user_type='landlord' 的用户
[2026-03-02 14:30:03] [INFO] 开始从房源 owner 信息创建房东记录...
[2026-03-02 14:30:03] [INFO]   ✓ 创建房东：admin (phone=NO_PHONE_1)
[2026-03-02 14:30:03] [INFO] ✓ 房东创建完成：新建 1 个，跳过 0 个
[2026-03-02 14:30:03] [INFO] 开始更新房源的 landlord_id 关联关系...
[2026-03-02 14:30:03] [INFO] ✓ 房源 landlord_id 更新完成：更新 0 个，无匹配房东 5 个
[2026-03-02 14:30:03] [INFO] 开始更新承包合同的关联关系...
[2026-03-02 14:30:03] [INFO] ✓ 承包合同关联关系更新完成：更新 0 个
============================================================
开始验证数据完整性...
============================================================
[2026-03-02 14:30:03] [INFO] 数据统计:
  - 用户总数：1
  - 房东总数：1
  - 房源总数：5
  - 承包合同总数：0
============================================================
迁移完成！
```

## 故障排查

### 问题 1: 数据库架构未更新

**错误信息**: `no such column: houses.landlord_id`

**解决方案**: 先运行数据库架构更新脚本

### 问题 2: NOT NULL 约束失败

**错误信息**: `NOT NULL constraint failed: landlords.id_card`

**解决方案**: 迁移脚本已自动处理，会为缺失的身份证号生成虚拟值

### 问题 3: 房源无法匹配房东

**现象**: 数据完整性检查显示"发现 X 个房源没有 landlord_id"

**解决方案**: 
1. 检查房源 owner 的手机号和姓名信息
2. 手动更新房源的 `landlord_id` 字段
3. 或者先创建对应的房东记录

## 回滚方法

### 使用命令行

```bash
python run.py rollback_landlord_migration
```

### 使用 Python 代码

```python
import sys
sys.path.insert(0, '.')
from app.migrations.migrate_landlord_data import run_rollback
run_rollback()
```

### 回滚后的状态

回滚成功后，数据库将恢复到迁移前的状态：
- 所有房源的 `landlord_id` 为 NULL
- 所有承包合同的 `landlord_id` 为 NULL
- 迁移创建的房东记录被删除

## 相关文件

- `app/migrations/migrate_landlord_data.py` - 主迁移脚本
- `app/migrations/update_schema.py` - 数据库架构更新脚本
- `app/models/landlord.py` - 房东模型
- `app/models/house.py` - 房源模型
- `app/models/landlord_contract.py` - 承包合同模型

## 技术支持

如有问题，请查看迁移日志或联系技术支持团队。
