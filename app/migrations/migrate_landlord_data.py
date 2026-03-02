"""
房东数据迁移脚本

用途：
1. 清理 user_type='landlord' 的用户数据（将其标记为 inactive 或迁移至 Landlord 表）
2. 更新现有房源的 landlord_id 字段（从现有 owner 信息推断或手动补充）
3. 更新现有承包合同的关联关系（从 house_id 改为 landlord_id）
4. 验证数据完整性

使用方法：
    python run.py migrate_landlord_data

回滚方法：
    python run.py rollback_landlord_migration
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models.user import User
from app.models.landlord import Landlord
from app.models.house import House
from app.models.landlord_contract import LandlordContract
from sqlalchemy import text


class LandlordDataMigration:
    """房东数据迁移类"""
    
    def __init__(self, app):
        self.app = app
        self.migration_log = []
        self.errors = []
        self.warnings = []
        
    def log(self, message, level='INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
        
    def check_landlord_users(self):
        """检查是否有 user_type='landlord' 的用户"""
        self.log("开始检查 user_type='landlord' 的用户...")
        
        landlord_users = User.query.filter(User.user_type == 'landlord').all()
        count = len(landlord_users)
        
        if count > 0:
            self.warnings.append(f"发现 {count} 个 user_type='landlord' 的用户")
            self.log(f"⚠️  警告：发现 {count} 个 user_type='landlord' 的用户", 'WARNING')
            
            for user in landlord_users:
                self.log(f"  - User ID: {user.id}, Username: {user.username}, "
                        f"Email: {user.email}, Phone: {user.phone}", 'WARNING')
            
            self.log("这些用户需要手动处理或迁移到 Landlord 表", 'WARNING')
        else:
            self.log("✓ 未发现 user_type='landlord' 的用户")
        
        return count
    
    def create_landlords_from_house_owners(self):
        """从现有房源 owner 信息推断并创建房东记录"""
        self.log("开始从房源 owner 信息创建房东记录...")
        
        # 获取所有有房源的用户
        house_owners = User.query.join(House, User.id == House.owner_id).distinct().all()
        created_count = 0
        skipped_count = 0
        
        for owner in house_owners:
            # 检查是否已经存在对应的房东记录
            existing_landlord = Landlord.query.filter(
                Landlord.phone == owner.phone
            ).first()
            
            if existing_landlord:
                self.log(f"  ⏭️  房东已存在 (phone={owner.phone}): {owner.username}", 'INFO')
                skipped_count += 1
                continue
            
            try:
                # 生成虚拟身份证号（如果没有）
                id_card = owner.id_card or f'MIGRATED_{owner.id}_{datetime.now().strftime("%Y%m%d")}'
                
                # 创建房东记录
                landlord = Landlord(
                    name=owner.name or owner.username,
                    phone=owner.phone or f'NO_PHONE_{owner.id}',
                    remark=f'从用户迁移 - User ID: {owner.id}, Username: {owner.username}'
                )
                
                # 设置身份证号并生成哈希
                landlord.set_id_card(id_card)
                
                # 从房源获取地址信息
                first_house = House.query.filter_by(owner_id=owner.id).first()
                if first_house:
                    landlord.address = first_house.address
                    landlord.property_cert_no = None  # 需要手动补充
                
                db.session.add(landlord)
                created_count += 1
                self.log(f"  ✓ 创建房东：{landlord.name} (phone={landlord.phone})", 'INFO')
                
            except Exception as e:
                self.errors.append(f"创建房东失败 - User ID: {owner.id}, Error: {str(e)}")
                self.log(f"  ✗ 创建房东失败 - User ID: {owner.id}: {str(e)}", 'ERROR')
        
        db.session.commit()
        self.log(f"✓ 房东创建完成：新建 {created_count} 个，跳过 {skipped_count} 个")
        return created_count, skipped_count
    
    def update_house_landlord_relations(self):
        """更新房源的 landlord_id 字段"""
        self.log("开始更新房源的 landlord_id 关联关系...")
        
        updated_count = 0
        no_landlord_count = 0
        
        # 获取所有房源
        houses = House.query.all()
        
        for house in houses:
            # 获取房源的 owner
            owner = User.query.get(house.owner_id)
            if not owner:
                self.log(f"  ⚠️  房源 ID {house.id} 无 owner 信息", 'WARNING')
                no_landlord_count += 1
                continue
            
            # 查找对应的房东
            landlord = None
            
            # 优先通过手机号匹配
            if owner.phone:
                landlord = Landlord.query.filter_by(phone=owner.phone).first()
            
            # 如果手机号匹配失败，尝试通过姓名匹配
            if not landlord and owner.name:
                landlord = Landlord.query.filter_by(name=owner.name).first()
            
            if landlord:
                # 更新房源的 landlord_id
                old_landlord_id = house.landlord_id
                house.landlord_id = landlord.id
                
                if old_landlord_id != landlord.id:
                    updated_count += 1
                    self.log(f"  ✓ 房源 '{house.title}' 更新 landlord_id: "
                            f"{old_landlord_id} -> {landlord.id}", 'INFO')
            else:
                self.log(f"  ⚠️  房源 '{house.title}' 未找到匹配的房东 (owner={owner.username})", 
                        'WARNING')
                no_landlord_count += 1
        
        db.session.commit()
        self.log(f"✓ 房源 landlord_id 更新完成：更新 {updated_count} 个，"
                f"无匹配房东 {no_landlord_count} 个")
        
        return updated_count, no_landlord_count
    
    def update_landlord_contract_relations(self):
        """更新承包合同的关联关系"""
        self.log("开始更新承包合同的关联关系...")
        
        updated_count = 0
        
        # 获取所有承包合同
        contracts = LandlordContract.query.all()
        
        for contract in contracts:
            # 检查是否已有 landlord_id
            if contract.landlord_id:
                self.log(f"  ⏭️  合同 '{contract.contract_no}' 已有 landlord_id", 'INFO')
                continue
            
            # 从关联的房源推断房东
            if contract.house_ids:
                # 获取第一个房源的房东信息
                first_house = House.query.get(contract.house_ids[0])
                if first_house and first_house.landlord_id:
                    contract.landlord_id = first_house.landlord_id
                    updated_count += 1
                    self.log(f"  ✓ 合同 '{contract.contract_no}' 更新 landlord_id: "
                            f"{first_house.landlord_id}", 'INFO')
                else:
                    self.log(f"  ⚠️  合同 '{contract.contract_no}' 无法推断房东", 'WARNING')
            else:
                self.log(f"  ⚠️  合同 '{contract.contract_no}' 无关联房源", 'WARNING')
        
        db.session.commit()
        self.log(f"✓ 承包合同关联关系更新完成：更新 {updated_count} 个")
        
        return updated_count
    
    def verify_data_integrity(self):
        """验证数据完整性"""
        self.log("=" * 60)
        self.log("开始验证数据完整性...")
        
        issues = []
        
        # 1. 检查房源是否都有 landlord_id
        houses_without_landlord = House.query.filter(
            House.landlord_id.is_(None)
        ).count()
        
        if houses_without_landlord > 0:
            issue = f"发现 {houses_without_landlord} 个房源没有 landlord_id"
            issues.append(issue)
            self.log(f"  ⚠️  {issue}", 'WARNING')
        else:
            self.log("  ✓ 所有房源都有 landlord_id", 'INFO')
        
        # 2. 检查承包合同是否都有 landlord_id
        contracts_without_landlord = LandlordContract.query.filter(
            LandlordContract.landlord_id.is_(None)
        ).count()
        
        if contracts_without_landlord > 0:
            issue = f"发现 {contracts_without_landlord} 个承包合同没有 landlord_id"
            issues.append(issue)
            self.log(f"  ⚠️  {issue}", 'WARNING')
        else:
            self.log("  ✓ 所有承包合同都有 landlord_id", 'INFO')
        
        # 3. 检查房东记录的完整性
        landlords_without_phone = Landlord.query.filter(
            (Landlord.phone.is_(None)) | (Landlord.phone == '')
        ).count()
        
        if landlords_without_phone > 0:
            issue = f"发现 {landlords_without_phone} 个房东没有电话号码"
            issues.append(issue)
            self.log(f"  ⚠️  {issue}", 'WARNING')
        else:
            self.log("  ✓ 所有房东都有电话号码", 'INFO')
        
        # 4. 检查房源和房东的关联是否有效
        invalid_house_landlord = db.session.query(House).outerjoin(
            Landlord, House.landlord_id == Landlord.id
        ).filter(
            House.landlord_id.isnot(None),
            Landlord.id.is_(None)
        ).count()
        
        if invalid_house_landlord > 0:
            issue = f"发现 {invalid_house_landlord} 个房源关联了不存在的房东"
            issues.append(issue)
            self.log(f"  ⚠️  {issue}", 'ERROR')
            self.errors.append(issue)
        else:
            self.log("  ✓ 所有房源的房东关联都有效", 'INFO')
        
        # 5. 检查承包合同和房东的关联是否有效
        invalid_contract_landlord = db.session.query(LandlordContract).outerjoin(
            Landlord, LandlordContract.landlord_id == Landlord.id
        ).filter(
            LandlordContract.landlord_id.isnot(None),
            Landlord.id.is_(None)
        ).count()
        
        if invalid_contract_landlord > 0:
            issue = f"发现 {invalid_contract_landlord} 个承包合同关联了不存在的房东"
            issues.append(issue)
            self.log(f"  ⚠️  {issue}", 'ERROR')
            self.errors.append(issue)
        else:
            self.log("  ✓ 所有承包合同的房东关联都有效", 'INFO')
        
        # 6. 统计信息
        self.log("=" * 60)
        self.log("数据统计:")
        total_users = User.query.count()
        total_landlords = Landlord.query.count()
        total_houses = House.query.count()
        total_contracts = LandlordContract.query.count()
        
        self.log(f"  - 用户总数：{total_users}")
        self.log(f"  - 房东总数：{total_landlords}")
        self.log(f"  - 房源总数：{total_houses}")
        self.log(f"  - 承包合同总数：{total_contracts}")
        
        self.log("=" * 60)
        
        if issues:
            self.log(f"⚠️  数据完整性检查发现 {len(issues)} 个问题", 'WARNING')
            return False
        else:
            self.log("✓ 数据完整性检查通过！", 'SUCCESS')
            return True
    
    def run_migration(self):
        """执行完整迁移流程"""
        self.log("=" * 60)
        self.log("开始房东数据迁移...")
        self.log("=" * 60)
        
        try:
            # 1. 检查 landlord 用户
            landlord_user_count = self.check_landlord_users()
            
            # 2. 创建房东记录
            created_count, skipped_count = self.create_landlords_from_house_owners()
            
            # 3. 更新房源 landlord_id
            updated_count, no_landlord_count = self.update_house_landlord_relations()
            
            # 4. 更新承包合同关联
            contract_updated_count = self.update_landlord_contract_relations()
            
            # 5. 验证数据完整性
            integrity_ok = self.verify_data_integrity()
            
            # 6. 输出迁移报告
            self.log("=" * 60)
            self.log("迁移报告:")
            self.log("=" * 60)
            self.log(f"✓ 发现 landlord 用户数：{landlord_user_count}")
            self.log(f"✓ 创建房东数：{created_count}")
            self.log(f"✓ 跳过已存在房东：{skipped_count}")
            self.log(f"✓ 更新房源 landlord 关联：{updated_count}")
            self.log(f"✓ 房源无匹配房东：{no_landlord_count}")
            self.log(f"✓ 更新承包合同关联：{contract_updated_count}")
            self.log(f"✓ 数据完整性检查：{'通过' if integrity_ok else '失败'}")
            
            if self.warnings:
                self.log("=" * 60)
                self.log("警告信息:")
                for warning in self.warnings:
                    self.log(f"  - {warning}", 'WARNING')
            
            if self.errors:
                self.log("=" * 60)
                self.log("错误信息:")
                for error in self.errors:
                    self.log(f"  - {error}", 'ERROR')
            
            self.log("=" * 60)
            self.log("迁移完成！", 'SUCCESS')
            
            return integrity_ok and len(self.errors) == 0
            
        except Exception as e:
            self.log(f"迁移过程中发生错误：{str(e)}", 'ERROR')
            db.session.rollback()
            return False


class LandlordDataRollback:
    """房东数据回滚类"""
    
    def __init__(self, app):
        self.app = app
        self.rollback_log = []
        
    def log(self, message, level='INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.rollback_log.append(log_entry)
        print(log_entry)
        
    def rollback(self):
        """执行回滚操作"""
        self.log("=" * 60)
        self.log("开始回滚房东数据迁移...")
        self.log("=" * 60)
        
        try:
            # 1. 清空房源的 landlord_id
            self.log("开始清空房源的 landlord_id...")
            updated_houses = House.query.update(
                {House.landlord_id: None},
                synchronize_session=False
            )
            db.session.commit()
            self.log(f"✓ 清空 {updated_houses} 个房源的 landlord_id")
            
            # 2. 清空承包合同的 landlord_id
            self.log("开始清空承包合同的 landlord_id...")
            updated_contracts = LandlordContract.query.update(
                {LandlordContract.landlord_id: None},
                synchronize_session=False
            )
            db.session.commit()
            self.log(f"✓ 清空 {updated_contracts} 个承包合同的 landlord_id")
            
            # 3. 删除迁移创建的房东记录
            self.log("开始删除迁移创建的房东记录...")
            migrated_landlords = Landlord.query.filter(
                Landlord.remark.like('从用户迁移 - User ID: %')
            ).all()
            
            deleted_count = 0
            for landlord in migrated_landlords:
                db.session.delete(landlord)
                deleted_count += 1
            
            db.session.commit()
            self.log(f"✓ 删除 {deleted_count} 个迁移创建的房东记录")
            
            self.log("=" * 60)
            self.log("回滚完成！", 'SUCCESS')
            self.log("=" * 60)
            self.log("回滚统计:")
            self.log(f"  - 清空房源 landlord_id: {updated_houses}")
            self.log(f"  - 清空承包合同 landlord_id: {updated_contracts}")
            self.log(f"  - 删除房东记录：{deleted_count}")
            
            return True
            
        except Exception as e:
            self.log(f"回滚过程中发生错误：{str(e)}", 'ERROR')
            db.session.rollback()
            return False


def run_migration():
    """执行迁移"""
    app = create_app()
    
    with app.app_context():
        migrator = LandlordDataMigration(app)
        success = migrator.run_migration()
        
        sys.exit(0 if success else 1)


def run_rollback():
    """执行回滚"""
    app = create_app()
    
    with app.app_context():
        rollback = LandlordDataRollback(app)
        success = rollback.rollback()
        
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        print("执行回滚操作...")
        run_rollback()
    else:
        print("执行迁移操作...")
        run_migration()
