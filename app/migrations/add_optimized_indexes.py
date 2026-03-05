"""
数据库索引优化迁移脚本

功能：
1. 添加复合索引优化多条件查询
2. 添加覆盖索引减少回表查询
3. 优化常用查询场景的性能

注意：
- SQLite 不支持部分索引，使用常规索引代替
- 索引名称遵循规范：idx_表名_字段名
- 执行前请备份数据库
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import db
from app.models import House, Room, Tenant, Contract, Payment, User, Landlord
from sqlalchemy import text, inspect


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


def drop_index_safely(index_name, table_name):
    """
    安全删除索引（如果存在）
    
    Args:
        index_name: 索引名称
        table_name: 表名
    """
    existing_indexes = get_existing_indexes(table_name)
    
    if index_name not in existing_indexes:
        print(f"  ✓ 索引 {index_name} 不存在，跳过删除")
        return
    
    try:
        sql = f"DROP INDEX {index_name}"
        db.session.execute(text(sql))
        db.session.commit()
        print(f"  ✓ 删除索引 {index_name} 成功")
    except Exception as e:
        db.session.rollback()
        print(f"  ✗ 删除索引 {index_name} 失败: {str(e)}")


def optimize_house_indexes():
    """
    优化房源表索引
    
    常用查询场景：
    1. 按状态筛选并按创建时间排序
    2. 按城市和区县筛选
    3. 按负责人和状态筛选
    4. 按租金范围筛选
    """
    print("\n优化房源表索引...")
    
    # 复合索引：状态 + 创建时间（用于状态筛选和排序）
    create_index_safely(
        'idx_houses_status_created',
        'houses',
        ['status', 'created_at']
    )
    
    # 复合索引：城市 + 区县（用于地区筛选）
    create_index_safely(
        'idx_houses_city_district',
        'houses',
        ['city', 'district']
    )
    
    # 复合索引：负责人 + 状态（用于员工查看自己的房源）
    create_index_safely(
        'idx_houses_owner_status',
        'houses',
        ['owner_id', 'status']
    )
    
    # 复合索引：房东 + 状态（用于房东查看房源）
    create_index_safely(
        'idx_houses_landlord_status',
        'houses',
        ['landlord_id', 'status']
    )
    
    # 覆盖索引：状态 + ID + 标题 + 租金（用于列表查询，减少回表）
    # 注意：SQLite 的覆盖索引需要包含 SELECT 的所有列
    create_index_safely(
        'idx_houses_cover_list',
        'houses',
        ['status', 'id', 'title', 'rent_price', 'city', 'district', 'created_at']
    )
    
    # 复合索引：租赁类型 + 状态（用于按类型筛选）
    create_index_safely(
        'idx_houses_type_status',
        'houses',
        ['rental_type', 'status']
    )


def optimize_room_indexes():
    """
    优化房间表索引
    
    常用查询场景：
    1. 按房源和状态筛选
    2. 按房源统计房间状态
    """
    print("\n优化房间表索引...")
    
    # 复合索引：房源 + 状态（用于查询房源的房间状态）
    create_index_safely(
        'idx_rooms_house_status',
        'rooms',
        ['house_id', 'status']
    )
    
    # 覆盖索引：房源 + 状态 + ID（用于统计查询）
    create_index_safely(
        'idx_rooms_house_status_cover',
        'rooms',
        ['house_id', 'status', 'id', 'room_number', 'rent_price']
    )


def optimize_tenant_indexes():
    """
    优化租客表索引
    
    常用查询场景：
    1. 按状态筛选
    2. 按手机号查询
    """
    print("\n优化租客表索引...")
    
    # 现有索引已足够，添加覆盖索引
    # 覆盖索引：状态 + ID + 姓名 + 手机号（用于列表查询）
    create_index_safely(
        'idx_tenants_status_cover',
        'tenants',
        ['status', 'id', 'name', 'phone', 'created_at']
    )


def optimize_contract_indexes():
    """
    优化合同表索引
    
    常用查询场景：
    1. 按状态筛选并按日期排序
    2. 查询即将到期合同
    3. 按租客查询合同
    4. 按房源查询合同
    """
    print("\n优化合同表索引...")
    
    # 复合索引：状态 + 结束日期（用于查询即将到期合同）
    create_index_safely(
        'idx_contracts_status_enddate',
        'contracts',
        ['status', 'end_date']
    )
    
    # 复合索引：租客 + 状态（用于查询租客的活跃合同）
    create_index_safely(
        'idx_contracts_tenant_status',
        'contracts',
        ['tenant_id', 'status']
    )
    
    # 复合索引：房源 + 状态（用于查询房源的合同）
    create_index_safely(
        'idx_contracts_house_status',
        'contracts',
        ['house_id', 'status']
    )
    
    # 复合索引：状态 + 开始日期（用于按状态筛选并排序）
    create_index_safely(
        'idx_contracts_status_startdate',
        'contracts',
        ['status', 'start_date']
    )
    
    # 覆盖索引：状态 + ID + 合同号 + 租客ID（用于列表查询）
    create_index_safely(
        'idx_contracts_status_cover',
        'contracts',
        ['status', 'id', 'contract_no', 'tenant_id', 'house_id', 'start_date', 'end_date']
    )


def optimize_payment_indexes():
    """
    优化支付记录表索引
    
    常用查询场景：
    1. 按合同查询支付记录
    2. 查询逾期支付
    3. 按状态筛选
    4. 按到期日期查询
    """
    print("\n优化支付记录表索引...")
    
    # 复合索引：合同 + 状态 + 到期日期（用于查询合同的支付记录）
    create_index_safely(
        'idx_payments_contract_status_duedate',
        'payments',
        ['contract_id', 'status', 'due_date']
    )
    
    # 复合索引：状态 + 到期日期（用于查询逾期支付）
    create_index_safely(
        'idx_payments_status_duedate',
        'payments',
        ['status', 'due_date']
    )
    
    # 复合索引：状态 + 支付类型（用于按类型统计）
    create_index_safely(
        'idx_payments_status_type',
        'payments',
        ['status', 'payment_type']
    )
    
    # 覆盖索引：状态 + 到期日期 + ID + 金额（用于逾期查询）
    create_index_safely(
        'idx_payments_overdue_cover',
        'payments',
        ['status', 'due_date', 'id', 'amount', 'paid_amount', 'contract_id']
    )


def optimize_user_indexes():
    """
    优化用户表索引
    
    常用查询场景：
    1. 按角色筛选
    2. 按状态筛选
    3. 登录验证
    """
    print("\n优化用户表索引...")
    
    # 复合索引：角色 + 状态（用于筛选员工）
    create_index_safely(
        'idx_users_role_status',
        'users',
        ['role', 'status']
    )
    
    # 复合索引：状态 + 角色（用于筛选在职员工）
    create_index_safely(
        'idx_users_status_role',
        'users',
        ['status', 'role']
    )


def optimize_landlord_indexes():
    """
    优化房东表索引
    
    常用查询场景：
    1. 按状态筛选
    2. 按手机号查询
    """
    print("\n优化房东表索引...")
    
    # 现有索引已足够，添加覆盖索引
    # 覆盖索引：状态 + ID + 姓名 + 手机号（用于列表查询）
    create_index_safely(
        'idx_landlords_status_cover',
        'landlords',
        ['status', 'id', 'name', 'phone', 'created_at']
    )


def analyze_query_performance():
    """
    分析查询性能，提供 EXPLAIN 示例
    """
    print("\n" + "="*80)
    print("查询性能分析示例")
    print("="*80)
    
    examples = [
        {
            'name': '房源列表查询（按状态筛选并排序）',
            'sql': """
                EXPLAIN QUERY PLAN 
                SELECT id, title, rent_price, city, district 
                FROM houses 
                WHERE status = 'available' 
                ORDER BY created_at DESC 
                LIMIT 20
            """
        },
        {
            'name': '即将到期合同查询',
            'sql': """
                EXPLAIN QUERY PLAN 
                SELECT id, contract_no, tenant_id, end_date 
                FROM contracts 
                WHERE status = 'active' 
                  AND end_date <= date('now', '+30 days')
                  AND end_date >= date('now')
                ORDER BY end_date ASC
            """
        },
        {
            'name': '逾期支付查询',
            'sql': """
                EXPLAIN QUERY PLAN 
                SELECT id, amount, paid_amount, due_date 
                FROM payments 
                WHERE status IN ('pending', 'partial', 'overdue') 
                  AND due_date < date('now')
                ORDER BY due_date ASC
            """
        },
        {
            'name': '房源地区筛选',
            'sql': """
                EXPLAIN QUERY PLAN 
                SELECT id, title, rent_price 
                FROM houses 
                WHERE city = '北京' AND district = '朝阳区'
                ORDER BY created_at DESC
            """
        }
    ]
    
    for example in examples:
        print(f"\n{example['name']}:")
        print("-" * 80)
        try:
            result = db.session.execute(text(example['sql'])).fetchall()
            for row in result:
                print(f"  {row}")
        except Exception as e:
            print(f"  执行失败: {str(e)}")


def get_index_statistics():
    """
    获取索引统计信息
    """
    print("\n" + "="*80)
    print("索引统计信息")
    print("="*80)
    
    tables = ['houses', 'rooms', 'tenants', 'contracts', 'payments', 'users', 'landlords']
    
    for table in tables:
        print(f"\n表 {table}:")
        indexes = get_existing_indexes(table)
        if indexes:
            for idx in sorted(indexes):
                print(f"  - {idx}")
        else:
            print("  (无索引)")


def main():
    """
    主函数：执行索引优化迁移
    """
    print("="*80)
    print("数据库索引优化迁移")
    print("="*80)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {db.engine.url}")
    
    try:
        # 显示迁移前的索引状态
        print("\n迁移前的索引状态:")
        get_index_statistics()
        
        # 执行索引优化
        print("\n" + "="*80)
        print("开始创建优化索引...")
        print("="*80)
        
        optimize_house_indexes()
        optimize_room_indexes()
        optimize_tenant_indexes()
        optimize_contract_indexes()
        optimize_payment_indexes()
        optimize_user_indexes()
        optimize_landlord_indexes()
        
        # 显示迁移后的索引状态
        print("\n" + "="*80)
        print("迁移后的索引状态:")
        print("="*80)
        get_index_statistics()
        
        # 分析查询性能
        analyze_query_performance()
        
        print("\n" + "="*80)
        print("索引优化迁移完成！")
        print("="*80)
        print("\n注意事项：")
        print("1. 索引会占用额外的存储空间")
        print("2. 索引会降低插入、更新、删除的速度")
        print("3. 建议定期使用 ANALYZE 命令更新统计信息")
        print("4. 建议定期检查未使用的索引并删除")
        print("\n优化建议：")
        print("1. 对于大型表，建议在非高峰期执行迁移")
        print("2. 迁移前请备份数据库")
        print("3. 迁移后请测试关键业务功能")
        
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
