"""
数据迁移脚本：从 Fernet 加密迁移到 AES-256-GCM 加密

功能：
1. 创建加密审计日志表
2. 迁移房东的身份证号和银行卡号
3. 迁移租客的身份证号
4. 验证迁移结果
5. 生成迁移报告

使用方法：
    python -m app.migrations.migrate_encryption_to_aes
"""
import sys
import os
from datetime import datetime
from tqdm import tqdm

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models.landlord import Landlord
from app.models.tenant import Tenant
from app.models.encryption_audit import EncryptionAuditLog
from app.utils.aes_encryption import HybridEncryptor


class EncryptionMigration:
    """加密数据迁移工具"""
    
    def __init__(self):
        """初始化迁移工具"""
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.migration_stats = {
            'landlords': {
                'total': 0,
                'migrated': 0,
                'skipped': 0,
                'failed': 0,
                'errors': []
            },
            'tenants': {
                'total': 0,
                'migrated': 0,
                'skipped': 0,
                'failed': 0,
                'errors': []
            },
            'start_time': None,
            'end_time': None
        }
    
    def create_audit_table(self):
        """创建加密审计日志表"""
        print("\n" + "="*60)
        print("步骤 1: 创建加密审计日志表")
        print("="*60)
        
        try:
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'encryption_audit_logs' not in tables:
                print("正在创建 encryption_audit_logs 表...")
                EncryptionAuditLog.__table__.create(db.engine)
                print("✓ 加密审计日志表创建成功")
            else:
                print("✓ 加密审计日志表已存在")
            
            return True
        except Exception as e:
            print(f"✗ 创建审计日志表失败: {str(e)}")
            return False
    
    def migrate_landlords(self):
        """迁移房东数据"""
        print("\n" + "="*60)
        print("步骤 2: 迁移房东数据")
        print("="*60)
        
        landlords = Landlord.query.all()
        self.migration_stats['landlords']['total'] = len(landlords)
        
        if not landlords:
            print("没有房东数据需要迁移")
            return
        
        print(f"找到 {len(landlords)} 条房东记录")
        
        for landlord in tqdm(landlords, desc="迁移房东数据"):
            try:
                # 检查是否需要重新加密
                if landlord.needs_re_encryption():
                    # 重新加密数据
                    landlord.re_encrypt_data(user_id=None)
                    db.session.commit()
                    self.migration_stats['landlords']['migrated'] += 1
                else:
                    self.migration_stats['landlords']['skipped'] += 1
            except Exception as e:
                db.session.rollback()
                self.migration_stats['landlords']['failed'] += 1
                self.migration_stats['landlords']['errors'].append({
                    'id': landlord.id,
                    'name': landlord.name,
                    'error': str(e)
                })
        
        print(f"\n房东数据迁移完成:")
        print(f"  - 总数: {self.migration_stats['landlords']['total']}")
        print(f"  - 已迁移: {self.migration_stats['landlords']['migrated']}")
        print(f"  - 已跳过（已是 AES 加密）: {self.migration_stats['landlords']['skipped']}")
        print(f"  - 失败: {self.migration_stats['landlords']['failed']}")
    
    def migrate_tenants(self):
        """迁移租客数据"""
        print("\n" + "="*60)
        print("步骤 3: 迁移租客数据")
        print("="*60)
        
        tenants = Tenant.query.all()
        self.migration_stats['tenants']['total'] = len(tenants)
        
        if not tenants:
            print("没有租客数据需要迁移")
            return
        
        print(f"找到 {len(tenants)} 条租客记录")
        
        for tenant in tqdm(tenants, desc="迁移租客数据"):
            try:
                # 检查是否需要重新加密
                if tenant.needs_re_encryption():
                    # 重新加密数据
                    tenant.re_encrypt_data(user_id=None)
                    db.session.commit()
                    self.migration_stats['tenants']['migrated'] += 1
                else:
                    self.migration_stats['tenants']['skipped'] += 1
            except Exception as e:
                db.session.rollback()
                self.migration_stats['tenants']['failed'] += 1
                self.migration_stats['tenants']['errors'].append({
                    'id': tenant.id,
                    'name': tenant.name,
                    'error': str(e)
                })
        
        print(f"\n租客数据迁移完成:")
        print(f"  - 总数: {self.migration_stats['tenants']['total']}")
        print(f"  - 已迁移: {self.migration_stats['tenants']['migrated']}")
        print(f"  - 已跳过（已是 AES 加密）: {self.migration_stats['tenants']['skipped']}")
        print(f"  - 失败: {self.migration_stats['tenants']['failed']}")
    
    def verify_migration(self):
        """验证迁移结果"""
        print("\n" + "="*60)
        print("步骤 4: 验证迁移结果")
        print("="*60)
        
        # 验证房东数据
        print("\n验证房东数据...")
        landlords = Landlord.query.all()
        landlord_verified = 0
        landlord_failed = 0
        
        for landlord in tqdm(landlords, desc="验证房东数据"):
            try:
                # 检查是否使用 AES 加密
                id_card_aes = HybridEncryptor.is_encrypted_with_aes(landlord.id_card_encrypted) if landlord.id_card_encrypted else True
                bank_card_aes = HybridEncryptor.is_encrypted_with_aes(landlord.bank_card_encrypted) if landlord.bank_card_encrypted else True
                
                if id_card_aes and bank_card_aes:
                    landlord_verified += 1
                else:
                    landlord_failed += 1
                    print(f"\n  警告: 房东 {landlord.name} (ID: {landlord.id}) 仍有未迁移的数据")
            except Exception as e:
                landlord_failed += 1
                print(f"\n  错误: 验证房东 {landlord.name} (ID: {landlord.id}) 失败: {str(e)}")
        
        print(f"\n房东数据验证结果:")
        print(f"  - 验证成功: {landlord_verified}")
        print(f"  - 验证失败: {landlord_failed}")
        
        # 验证租客数据
        print("\n验证租客数据...")
        tenants = Tenant.query.all()
        tenant_verified = 0
        tenant_failed = 0
        
        for tenant in tqdm(tenants, desc="验证租客数据"):
            try:
                # 检查是否使用 AES 加密
                id_card_aes = HybridEncryptor.is_encrypted_with_aes(tenant.id_card_encrypted) if tenant.id_card_encrypted else True
                
                if id_card_aes:
                    tenant_verified += 1
                else:
                    tenant_failed += 1
                    print(f"\n  警告: 租客 {tenant.name} (ID: {tenant.id}) 仍有未迁移的数据")
            except Exception as e:
                tenant_failed += 1
                print(f"\n  错误: 验证租客 {tenant.name} (ID: {tenant.id}) 失败: {str(e)}")
        
        print(f"\n租客数据验证结果:")
        print(f"  - 验证成功: {tenant_verified}")
        print(f"  - 验证失败: {tenant_failed}")
        
        return landlord_failed == 0 and tenant_failed == 0
    
    def generate_report(self):
        """生成迁移报告"""
        print("\n" + "="*60)
        print("迁移报告")
        print("="*60)
        
        duration = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
        
        print(f"\n迁移时间: {self.migration_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')} - {self.migration_stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {duration:.2f} 秒")
        
        print(f"\n房东数据:")
        print(f"  - 总数: {self.migration_stats['landlords']['total']}")
        print(f"  - 已迁移: {self.migration_stats['landlords']['migrated']}")
        print(f"  - 已跳过: {self.migration_stats['landlords']['skipped']}")
        print(f"  - 失败: {self.migration_stats['landlords']['failed']}")
        
        if self.migration_stats['landlords']['errors']:
            print(f"\n  错误详情:")
            for error in self.migration_stats['landlords']['errors'][:5]:  # 只显示前 5 个错误
                print(f"    - ID {error['id']} ({error['name']}): {error['error']}")
            if len(self.migration_stats['landlords']['errors']) > 5:
                print(f"    ... 还有 {len(self.migration_stats['landlords']['errors']) - 5} 个错误")
        
        print(f"\n租客数据:")
        print(f"  - 总数: {self.migration_stats['tenants']['total']}")
        print(f"  - 已迁移: {self.migration_stats['tenants']['migrated']}")
        print(f"  - 已跳过: {self.migration_stats['tenants']['skipped']}")
        print(f"  - 失败: {self.migration_stats['tenants']['failed']}")
        
        if self.migration_stats['tenants']['errors']:
            print(f"\n  错误详情:")
            for error in self.migration_stats['tenants']['errors'][:5]:  # 只显示前 5 个错误
                print(f"    - ID {error['id']} ({error['name']}): {error['error']}")
            if len(self.migration_stats['tenants']['errors']) > 5:
                print(f"    ... 还有 {len(self.migration_stats['tenants']['errors']) - 5} 个错误")
        
        # 保存报告到文件
        report_path = os.path.join(self.app.config['BASE_DIR'], 'logs', 'encryption_migration_report.txt')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("AES-256-GCM 加密迁移报告\n")
            f.write("="*60 + "\n\n")
            f.write(f"迁移时间: {self.migration_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')} - {self.migration_stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总耗时: {duration:.2f} 秒\n\n")
            
            f.write("房东数据:\n")
            f.write(f"  - 总数: {self.migration_stats['landlords']['total']}\n")
            f.write(f"  - 已迁移: {self.migration_stats['landlords']['migrated']}\n")
            f.write(f"  - 已跳过: {self.migration_stats['landlords']['skipped']}\n")
            f.write(f"  - 失败: {self.migration_stats['landlords']['failed']}\n\n")
            
            if self.migration_stats['landlords']['errors']:
                f.write("  错误详情:\n")
                for error in self.migration_stats['landlords']['errors']:
                    f.write(f"    - ID {error['id']} ({error['name']}): {error['error']}\n")
                f.write("\n")
            
            f.write("租客数据:\n")
            f.write(f"  - 总数: {self.migration_stats['tenants']['total']}\n")
            f.write(f"  - 已迁移: {self.migration_stats['tenants']['migrated']}\n")
            f.write(f"  - 已跳过: {self.migration_stats['tenants']['skipped']}\n")
            f.write(f"  - 失败: {self.migration_stats['tenants']['failed']}\n\n")
            
            if self.migration_stats['tenants']['errors']:
                f.write("  错误详情:\n")
                for error in self.migration_stats['tenants']['errors']:
                    f.write(f"    - ID {error['id']} ({error['name']}): {error['error']}\n")
        
        print(f"\n迁移报告已保存到: {report_path}")
    
    def run(self):
        """执行迁移"""
        print("\n" + "="*60)
        print("AES-256-GCM 加密数据迁移")
        print("="*60)
        
        self.migration_stats['start_time'] = datetime.now()
        
        # 步骤 1: 创建审计日志表
        if not self.create_audit_table():
            print("\n迁移失败：无法创建审计日志表")
            return False
        
        # 步骤 2: 迁移房东数据
        self.migrate_landlords()
        
        # 步骤 3: 迁移租客数据
        self.migrate_tenants()
        
        # 步骤 4: 验证迁移结果
        success = self.verify_migration()
        
        self.migration_stats['end_time'] = datetime.now()
        
        # 步骤 5: 生成报告
        self.generate_report()
        
        if success:
            print("\n" + "="*60)
            print("✓ 迁移成功完成！")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("✗ 迁移完成，但存在错误，请检查报告")
            print("="*60)
        
        return success
    
    def __del__(self):
        """清理资源"""
        try:
            self.app_context.pop()
        except:
            pass


def main():
    """主函数"""
    print("\n警告：此脚本将迁移所有加密数据到 AES-256-GCM 算法")
    print("建议在执行前备份数据库！")
    
    confirm = input("\n是否继续？(yes/no): ")
    
    if confirm.lower() != 'yes':
        print("迁移已取消")
        return
    
    migration = EncryptionMigration()
    success = migration.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
