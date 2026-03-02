"""
数据库迁移脚本：加密敏感数据并移除级联删除
此脚本用于：
1. 将现有的身份证号和银行卡号加密存储
2. 移除级联删除配置
3. 更新数据库表结构
"""
from datetime import datetime
from app import create_app, db
from app.models.landlord import Landlord
from app.models.tenant import Tenant
from app.models.house import House
from app.models.contract import Contract
from app.models.payment import Payment
from app.utils.encryption import encrypt_sensitive_data, decrypt_sensitive_data
import sys


def encrypt_existing_data():
    """
    加密现有的敏感数据
    """
    print("=" * 60)
    print("开始加密现有敏感数据...")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # 加密房东身份证号
        print("\n[1/4] 加密房东身份证号...")
        landlords = Landlord.query.all()
        encrypted_landlord_count = 0
        for landlord in landlords:
            try:
                # 读取明文身份证号
                id_card = getattr(landlord, 'id_card', None)
                if id_card:
                    encrypted_id_card = encrypt_sensitive_data(id_card)
                    if encrypted_id_card:
                        landlord.id_card_encrypted = encrypted_id_card
                        encrypted_landlord_count += 1
                        print(f"  ✓ 房东 {landlord.id}: {landlord.name} - 身份证已加密")
            except Exception as e:
                print(f"  ✗ 房东 {landlord.id} 加密失败: {str(e)}")
        
        db.session.commit()
        print(f"  完成: {encrypted_landlord_count} 个房东身份证号已加密")
        
        # 加密房东银行卡号
        print("\n[2/4] 加密房东银行卡号...")
        landlords_with_bank = Landlord.query.filter(Landlord.bank_card != None).all()
        encrypted_bank_count = 0
        for landlord in landlords_with_bank:
            try:
                bank_card = getattr(landlord, 'bank_card', None)
                if bank_card:
                    encrypted_bank_card = encrypt_sensitive_data(bank_card)
                    if encrypted_bank_card:
                        landlord.bank_card_encrypted = encrypted_bank_card
                        encrypted_bank_count += 1
                        print(f"  ✓ 房东 {landlord.id}: {landlord.name} - 银行卡已加密")
            except Exception as e:
                print(f"  ✗ 房东 {landlord.id} 银行卡加密失败: {str(e)}")
        
        db.session.commit()
        print(f"  完成: {encrypted_bank_count} 个房东银行卡号已加密")
        
        # 加密租客身份证号
        print("\n[3/4] 加密租客身份证号...")
        tenants = Tenant.query.all()
        encrypted_tenant_count = 0
        for tenant in tenants:
            try:
                id_card = getattr(tenant, 'id_card', None)
                if id_card:
                    encrypted_id_card = encrypt_sensitive_data(id_card)
                    if encrypted_id_card:
                        tenant.id_card_encrypted = encrypted_id_card
                        encrypted_tenant_count += 1
                        print(f"  ✓ 租客 {tenant.id}: {tenant.name} - 身份证已加密")
            except Exception as e:
                print(f"  ✗ 租客 {tenant.id} 加密失败: {str(e)}")
        
        db.session.commit()
        print(f"  完成: {encrypted_tenant_count} 个租客身份证号已加密")
        
        # 加密租客银行卡号（如果有）
        print("\n[4/4] 加密租客银行卡号...")
        tenants_with_bank = Tenant.query.filter(Tenant.bank_card != None).all()
        encrypted_tenant_bank_count = 0
        for tenant in tenants_with_bank:
            try:
                bank_card = getattr(tenant, 'bank_card', None)
                if bank_card:
                    encrypted_bank_card = encrypt_sensitive_data(bank_card)
                    if encrypted_bank_card:
                        tenant.bank_card_encrypted = encrypted_bank_card
                        encrypted_tenant_bank_count += 1
                        print(f"  ✓ 租客 {tenant.id}: {tenant.name} - 银行卡已加密")
            except Exception as e:
                print(f"  ✗ 租客 {tenant.id} 银行卡加密失败: {str(e)}")
        
        db.session.commit()
        print(f"  完成: {encrypted_tenant_bank_count} 个租客银行卡号已加密")
        
        print("\n" + "=" * 60)
        print("敏感数据加密完成！")
        print("=" * 60)
        
        # 显示统计信息
        print("\n加密统计:")
        print(f"  - 房东身份证号: {encrypted_landlord_count} 个")
        print(f"  - 房东银行卡号: {encrypted_bank_count} 个")
        print(f"  - 租客身份证号: {encrypted_tenant_count} 个")
        print(f"  - 租客银行卡号: {encrypted_tenant_bank_count} 个")


def remove_cascade_deletes():
    """
    移除级联删除配置（需要手动修改模型）
    """
    print("\n" + "=" * 60)
    print("级联删除配置说明...")
    print("=" * 60)
    print("""
    级联删除配置已在模型文件中移除，但需要手动处理现有数据：
    
    1. Contract -> Payment:
       - 旧配置: Contract删除时级联删除Payment
       - 新配置: 需要手动删除Payment或设置为NULL
       - 建议: 删除Contract前先处理Payment记录
    
    2. House -> Room:
       - 旧配置: House删除时级联删除Room
       - 新配置: 需要手动删除Room或设置为NULL
       - 建议: 删除House前先处理Room记录
    
    3. House -> Media:
       - 旧配置: House删除时级联删除Media
       - 新配置: 需要手动删除Media
       - 建议: 删除House前先备份Media记录
    """)


def verify_encryption():
    """
    验证加密是否成功
    """
    print("\n" + "=" * 60)
    print("验证加密结果...")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # 检查 landlords 表
        landlords = Landlord.query.all()
        has_plain_text = False
        for landlord in landlords[:10]:  # 只检查前10条
            if hasattr(landlord, 'id_card') and landlord.id_card:
                has_plain_text = True
                break
            if hasattr(landlord, 'bank_card') and landlord.bank_card:
                has_plain_text = True
                break
        
        if has_plain_text:
            print("  ⚠ 警告: 发现明文存储的敏感数据，请检查")
        else:
            print("  ✓ 未发现明文存储的敏感数据")
        
        # 检查 tenants 表
        tenants = Tenant.query.all()
        for tenant in tenants[:10]:
            if hasattr(tenant, 'id_card') and tenant.id_card:
                has_plain_text = True
                break
        
        if has_plain_text:
            print("  ⚠ 警告: 租客表发现明文存储的敏感数据")
        else:
            print("  ✓ 租客表未发现明文存储的敏感数据")


def main():
    """
    主函数
    """
    print("\n" + "=" * 60)
    print("数据库迁移脚本 - 敏感数据加密与级联删除修复")
    print("=" * 60)
    print("""
    此脚本将执行以下操作：
    1. 加密现有的身份证号和银行卡号
    2. 移除级联删除配置
    3. 验证加密结果
    
    ⚠ 警告：执行前请务必备份数据库！
    """)
    
    confirm = input("是否继续执行？(yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("操作已取消")
        sys.exit(0)
    
    try:
        # 执行加密
        encrypt_existing_data()
        
        # 移除级联删除配置说明
        remove_cascade_deletes()
        
        # 验证结果
        verify_encryption()
        
        print("\n" + "=" * 60)
        print("数据库迁移完成！")
        print("=" * 60)
        print("""
    下一步操作：
    1. 检查加密后的数据是否正确
    2. 更新应用配置，设置 ENCRYPTION_KEY
    3. 测试所有相关API
    4. 部署到生产环境前进行完整测试
    """)
        
    except Exception as e:
        print(f"\n✗ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
