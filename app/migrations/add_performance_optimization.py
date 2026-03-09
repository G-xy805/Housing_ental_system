"""
性能优化迁移脚本

功能：
1. 为 landlords 表添加 id_card_hash 字段（用于快速查重）
2. 为 tenants 表添加 id_card_hash 字段
3. 为现有数据生成哈希值
4. 添加数据库索引优化查询性能
   - house 表复合索引 (city, status)
   - contract 表复合索引 (start_date, end_date, status)
   - payment 表索引 (due_date, status)

性能优化说明：
- 身份证号查重：从 O(n) 遍历解密优化为 O(1) 哈希查询
- 复合索引：优化多条件查询性能

注意：
- 执行前请备份数据库
- 建议在非高峰期执行
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import db
from app.models import Landlord, Tenant
from sqlalchemy import text, inspect
from app.utils.aes_encryption import decrypt_sensitive_data


def get_existing_columns(table_name):
    """
    获取表的现有列名
    
    Args:
        table_name: 表名
        
    Returns:
        set: 现有列名集合
    """
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table_name)
    return {col['name'] for col in columns}


def get_existing_indexes(table_name):
    """
    获取表的现有索引
    
    Args:
        table_name: 表名
        
    Returns:
        set: 现有索引名称集合
    """
    inspector = inspect(db.engine)
    indexes = inspector.get_indexes(table_name)
    return {idx['name'] for idx in indexes}


def add_column_safely(table_name, column_name, column_type, column_comment=None):
    """
    安全添加列（如果不存在）
    
    Args:
        table_name: 表名
        column_name: 列名
        column_type: 列类型
        column_comment: 列注释
    """
    existing_columns = get_existing_columns(table_name)
    
    if column_name in existing_columns:
        print(f"  ✓ 列 {table_name}.{column_name} 已存在，跳过")
        return True
    
    try:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        db.session.execute(text(sql))
        db.session.commit()
        print(f"  ✓ 添加列 {table_name}.{column_name} 成功")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"  ✗ 添加列 {table_name}.{column_name} 失败: {str(e)}")
        return False


def create_index_safely(index_name, table_name, columns, unique=False):
    """
    安全创建索引（如果不存在）
    
    Args:
        index_name: 索引名称
        table_name: 表名
        columns: 列名列表
        unique: 是否唯一索引
    """
    existing_indexes = get_existing_indexes(table_name)
    
    if index_name in existing_indexes:
        print(f"  ✓ 索引 {index_name} 已存在，跳过")
        return
    
    try:
        columns_str = ', '.join(columns)
        unique_keyword = 'UNIQUE ' if unique else ''
        sql = f"CREATE {unique_keyword}INDEX {index_name} ON {table_name} ({columns_str})"
        
        db.session.execute(text(sql))
        db.session.commit()
        print(f"  ✓ 创建索引 {index_name} 成功")
    except Exception as e:
        db.session.rollback()
        print(f"  ✗ 创建索引 {index_name} 失败: {str(e)}")


def migrate_landlord_hash():
    """
    为房东表添加哈希字段并迁移现有数据
    """
    print("\n迁移房东表哈希字段...")
    
    # 添加 id_card_hash 列
    add_column_safely('landlords', 'id_card_hash', 'VARCHAR(64)')
    
    # 创建唯一索引
    create_index_safely(
        'idx_landlords_id_card_hash',
        'landlords',
        ['id_card_hash'],
        unique=True
    )
    
    # 为现有数据生成哈希值
    print("  为现有房东数据生成哈希值...")
    landlords = Landlord.query.filter(
        Landlord.id_card_encrypted.isnot(None),
        Landlord.id_card_hash.is_(None)
    ).all()
    
    updated_count = 0
    for landlord in landlords:
        try:
            # 解密身份证号
            id_card = decrypt_sensitive_data(
                encrypted_data=landlord.id_card_encrypted,
                field_name='id_card',
                model_name='Landlord',
                record_id=landlord.id,
                skip_audit=True
            )
            
            if id_card:
                # 计算哈希值
                from app.models.landlord import calculate_id_card_hash
                landlord.id_card_hash = calculate_id_card_hash(id_card)
                updated_count += 1
        except Exception as e:
            print(f"    警告: 房东 {landlord.id} 哈希值生成失败: {str(e)}")
            continue
    
    if updated_count > 0:
        db.session.commit()
        print(f"  ✓ 已为 {updated_count} 个房东生成哈希值")
    else:
        print("  ✓ 无需更新")


def migrate_tenant_hash():
    """
    为租客表添加哈希字段并迁移现有数据
    """
    print("\n迁移租客表哈希字段...")
    
    # 添加 id_card_hash 列
    add_column_safely('tenants', 'id_card_hash', 'VARCHAR(64)')
    
    # 创建唯一索引
    create_index_safely(
        'idx_tenants_id_card_hash',
        'tenants',
        ['id_card_hash'],
        unique=True
    )
    
    # 为现有数据生成哈希值
    print("  为现有租客数据生成哈希值...")
    tenants = Tenant.query.filter(
        Tenant.id_card_encrypted.isnot(None),
        Tenant.id_card_hash.is_(None)
    ).all()
    
    updated_count = 0
    for tenant in tenants:
        try:
            # 解密身份证号
            id_card = decrypt_sensitive_data(
                encrypted_data=tenant.id_card_encrypted,
                field_name='id_card',
                model_name='Tenant',
                record_id=tenant.id,
                skip_audit=True
            )
            
            if id_card:
                # 计算哈希值
                from app.models.tenant import calculate_id_card_hash
                tenant.id_card_hash = calculate_id_card_hash(id_card)
                updated_count += 1
        except Exception as e:
            print(f"    警告: 租客 {tenant.id} 哈希值生成失败: {str(e)}")
            continue
    
    if updated_count > 0:
        db.session.commit()
        print(f"  ✓ 已为 {updated_count} 个租客生成哈希值")
    else:
        print("  ✓ 无需更新")


def optimize_house_indexes():
    """
    优化房源表索引
    
    添加复合索引：city + status
    用于按城市和状态筛选房源
    """
    print("\n优化房源表索引...")
    
    # 复合索引：城市 + 状态
    create_index_safely(
        'idx_houses_city_status',
        'houses',
        ['city', 'status']
    )


def optimize_contract_indexes():
    """
    优化合同表索引
    
    添加复合索引：start_date + end_date + status
    用于按日期范围和状态查询合同
    """
    print("\n优化合同表索引...")
    
    # 复合索引：开始日期 + 结束日期 + 状态
    create_index_safely(
        'idx_contracts_dates_status',
        'contracts',
        ['start_date', 'end_date', 'status']
    )


def optimize_payment_indexes():
    """
    优化支付记录表索引
    
    添加复合索引：due_date + status
    用于查询逾期支付和待支付记录
    """
    print("\n优化支付记录表索引...")
    
    # 复合索引：到期日期 + 状态
    create_index_safely(
        'idx_payments_due_date_status',
        'payments',
        ['due_date', 'status']
    )


def verify_migration():
    """
    验证迁移结果
    """
    print("\n" + "="*80)
    print("验证迁移结果")
    print("="*80)
    
    # 检查列是否存在
    print("\n检查列:")
    landlord_columns = get_existing_columns('landlords')
    tenant_columns = get_existing_columns('tenants')
    
    print(f"  landlords.id_card_hash: {'✓ 存在' if 'id_card_hash' in landlord_columns else '✗ 不存在'}")
    print(f"  tenants.id_card_hash: {'✓ 存在' if 'id_card_hash' in tenant_columns else '✗ 不存在'}")
    
    # 检查索引是否存在
    print("\n检查索引:")
    landlord_indexes = get_existing_indexes('landlords')
    tenant_indexes = get_existing_indexes('tenants')
    house_indexes = get_existing_indexes('houses')
    contract_indexes = get_existing_indexes('contracts')
    payment_indexes = get_existing_indexes('payments')
    
    print(f"  idx_landlords_id_card_hash: {'✓ 存在' if 'idx_landlords_id_card_hash' in landlord_indexes else '✗ 不存在'}")
    print(f"  idx_tenants_id_card_hash: {'✓ 存在' if 'idx_tenants_id_card_hash' in tenant_indexes else '✗ 不存在'}")
    print(f"  idx_houses_city_status: {'✓ 存在' if 'idx_houses_city_status' in house_indexes else '✗ 不存在'}")
    print(f"  idx_contracts_dates_status: {'✓ 存在' if 'idx_contracts_dates_status' in contract_indexes else '✗ 不存在'}")
    print(f"  idx_payments_due_date_status: {'✓ 存在' if 'idx_payments_due_date_status' in payment_indexes else '✗ 不存在'}")
    
    # 统计哈希值覆盖率
    print("\n哈希值覆盖率:")
    total_landlords = Landlord.query.filter(Landlord.id_card_encrypted.isnot(None)).count()
    landlords_with_hash = Landlord.query.filter(
        Landlord.id_card_encrypted.isnot(None),
        Landlord.id_card_hash.isnot(None)
    ).count()
    
    total_tenants = Tenant.query.filter(Tenant.id_card_encrypted.isnot(None)).count()
    tenants_with_hash = Tenant.query.filter(
        Tenant.id_card_encrypted.isnot(None),
        Tenant.id_card_hash.isnot(None)
    ).count()
    
    print(f"  房东: {landlords_with_hash}/{total_landlords} ({landlords_with_hash/max(total_landlords,1)*100:.1f}%)")
    print(f"  租客: {tenants_with_hash}/{total_tenants} ({tenants_with_hash/max(total_tenants,1)*100:.1f}%)")


def main():
    """
    主函数：执行性能优化迁移
    """
    print("="*80)
    print("性能优化迁移")
    print("="*80)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {db.engine.url}")
    
    try:
        # 1. 迁移哈希字段
        print("\n" + "="*80)
        print("步骤 1: 迁移哈希字段")
        print("="*80)
        migrate_landlord_hash()
        migrate_tenant_hash()
        
        # 2. 优化索引
        print("\n" + "="*80)
        print("步骤 2: 优化数据库索引")
        print("="*80)
        optimize_house_indexes()
        optimize_contract_indexes()
        optimize_payment_indexes()
        
        # 3. 验证迁移
        verify_migration()
        
        print("\n" + "="*80)
        print("性能优化迁移完成！")
        print("="*80)
        print("\n优化效果说明：")
        print("1. 身份证号查重性能提升：")
        print("   - 优化前：O(n) 遍历解密所有记录")
        print("   - 优化后：O(1) 哈希值索引查询")
        print("   - 预计性能提升：100-1000倍（取决于数据量）")
        print("\n2. 复合索引优化：")
        print("   - 房源按城市和状态筛选")
        print("   - 合同按日期范围和状态查询")
        print("   - 支付记录按到期日期和状态查询")
        print("\n注意事项：")
        print("1. 索引会占用额外的存储空间")
        print("2. 索引会略微降低插入、更新、删除的速度")
        print("3. 建议定期使用 ANALYZE 命令更新统计信息")
        print("4. 建议定期检查未使用的索引并删除")
        
    except Exception as e:
        print(f"\n迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    from app import create_app
    
    app = create_app()
    with app.app_context():
        success = main()
        sys.exit(0 if success else 1)
