"""
数据库索引优化迁移脚本 - P2-1

功能：
1. 添加合同表索引：idx_contract_status_date, idx_contract_tenant_status
2. 添加支付表索引：idx_payment_status_date, idx_payment_contract_status

优化目标：
- 优化合同列表查询（按状态筛选并按创建时间排序）
- 优化租客合同查询（按租客ID和状态筛选）
- 优化支付记录查询（按状态筛选并按到期日期排序）
- 优化合同支付记录查询（按合同ID和状态筛选）

注意：
- SQLite 不支持部分索引，使用常规复合索引
- 索引名称遵循规范：idx_表名_字段名
- 执行前请备份数据库
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import db
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

    Returns:
        bool: 是否成功创建
    """
    existing_indexes = get_existing_indexes(table_name)

    if index_name in existing_indexes:
        print(f"  ✓ 索引 {index_name} 已存在，跳过")
        return True

    try:
        columns_str = ', '.join(columns)
        unique_keyword = 'UNIQUE ' if unique else ''
        sql = f"CREATE {unique_keyword}INDEX {index_name} ON {table_name} ({columns_str})"

        db.session.execute(text(sql))
        db.session.commit()
        print(f"  ✓ 创建索引 {index_name} 成功")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"  ✗ 创建索引 {index_name} 失败: {str(e)}")
        return False


def add_contract_indexes():
    """
    添加合同表索引

    优化场景：
    1. 合同列表查询 - 按状态筛选并按创建时间排序
       Query: Contract.query.filter(Contract.status == 'active').order_by(Contract.created_at.desc())
       Index: idx_contract_status_date (status, created_at)

    2. 租客合同查询 - 按租客ID和状态筛选
       Query: Contract.query.filter(Contract.tenant_id == tenant_id, Contract.status == 'active')
       Index: idx_contract_tenant_status (tenant_id, status)
    """
    print("\n添加合同表索引...")

    # 复合索引：状态 + 创建时间
    # 用于合同列表查询，按状态筛选并按创建时间排序
    success1 = create_index_safely(
        'idx_contract_status_date',
        'contracts',
        ['status', 'created_at']
    )

    # 复合索引：租客ID + 状态
    # 用于查询租客的合同，按状态筛选
    success2 = create_index_safely(
        'idx_contract_tenant_status',
        'contracts',
        ['tenant_id', 'status']
    )

    return success1 and success2


def add_payment_indexes():
    """
    添加支付表索引

    优化场景：
    1. 支付记录查询 - 按状态筛选并按到期日期排序
       Query: Payment.query.filter(Payment.status == 'pending').order_by(Payment.due_date.asc())
       Index: idx_payment_status_date (status, due_date)

    2. 合同支付记录查询 - 按合同ID和状态筛选
       Query: Payment.query.filter(Payment.contract_id == contract_id, Payment.status == 'pending')
       Index: idx_payment_contract_status (contract_id, status)
    """
    print("\n添加支付表索引...")

    # 复合索引：状态 + 到期日期
    # 用于支付记录查询，按状态筛选并按到期日期排序
    success1 = create_index_safely(
        'idx_payment_status_date',
        'payments',
        ['status', 'due_date']
    )

    # 复合索引：合同ID + 状态
    # 用于查询合同的支付记录，按状态筛选
    success2 = create_index_safely(
        'idx_payment_contract_status',
        'payments',
        ['contract_id', 'status']
    )

    return success1 and success2


def verify_indexes():
    """
    验证索引是否创建成功
    """
    print("\n" + "="*80)
    print("验证索引创建结果")
    print("="*80)

    # 检查合同表索引
    print("\n合同表 (contracts) 索引:")
    contract_indexes = get_existing_indexes('contracts')
    target_indexes = ['idx_contract_status_date', 'idx_contract_tenant_status']

    for idx in target_indexes:
        if idx in contract_indexes:
            print(f"  ✓ {idx}")
        else:
            print(f"  ✗ {idx} (未找到)")

    # 检查支付表索引
    print("\n支付表 (payments) 索引:")
    payment_indexes = get_existing_indexes('payments')
    target_indexes = ['idx_payment_status_date', 'idx_payment_contract_status']

    for idx in target_indexes:
        if idx in payment_indexes:
            print(f"  ✓ {idx}")
        else:
            print(f"  ✗ {idx} (未找到)")


def analyze_query_performance():
    """
    分析查询性能，提供 EXPLAIN 示例
    """
    print("\n" + "="*80)
    print("查询性能分析示例")
    print("="*80)

    examples = [
        {
            'name': '合同列表查询（按状态筛选并按创建时间排序）',
            'sql': """
                EXPLAIN QUERY PLAN
                SELECT id, contract_no, title, status, created_at
                FROM contracts
                WHERE status = 'active'
                ORDER BY created_at DESC
                LIMIT 20
            """,
            'index': 'idx_contract_status_date'
        },
        {
            'name': '租客合同查询（按租客ID和状态筛选）',
            'sql': """
                EXPLAIN QUERY PLAN
                SELECT id, contract_no, title, status, start_date, end_date
                FROM contracts
                WHERE tenant_id = 1 AND status = 'active'
            """,
            'index': 'idx_contract_tenant_status'
        },
        {
            'name': '支付记录查询（按状态筛选并按到期日期排序）',
            'sql': """
                EXPLAIN QUERY PLAN
                SELECT id, payment_no, amount, due_date, status
                FROM payments
                WHERE status = 'pending'
                ORDER BY due_date ASC
                LIMIT 20
            """,
            'index': 'idx_payment_status_date'
        },
        {
            'name': '合同支付记录查询（按合同ID和状态筛选）',
            'sql': """
                EXPLAIN QUERY PLAN
                SELECT id, payment_no, amount, due_date, status
                FROM payments
                WHERE contract_id = 1 AND status = 'pending'
                ORDER BY due_date ASC
            """,
            'index': 'idx_payment_contract_status'
        }
    ]

    for example in examples:
        print(f"\n{example['name']}:")
        print(f"使用索引: {example['index']}")
        print("-" * 80)
        try:
            result = db.session.execute(text(example['sql'])).fetchall()
            for row in result:
                print(f"  {row}")
        except Exception as e:
            print(f"  执行失败: {str(e)}")


def main():
    """
    主函数：执行索引优化迁移
    """
    print("="*80)
    print("数据库索引优化迁移 - P2-1")
    print("="*80)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {db.engine.url}")

    try:
        # 显示迁移前的索引状态
        print("\n迁移前的索引状态:")
        verify_indexes()

        # 执行索引优化
        print("\n" + "="*80)
        print("开始创建优化索引...")
        print("="*80)

        contract_success = add_contract_indexes()
        payment_success = add_payment_indexes()

        # 显示迁移后的索引状态
        print("\n" + "="*80)
        print("迁移后的索引状态:")
        print("="*80)
        verify_indexes()

        # 分析查询性能
        analyze_query_performance()

        # 迁移结果
        print("\n" + "="*80)
        if contract_success and payment_success:
            print("索引优化迁移完成！")
            print("="*80)
            print("\n已创建的索引:")
            print("  合同表:")
            print("    - idx_contract_status_date (status, created_at)")
            print("    - idx_contract_tenant_status (tenant_id, status)")
            print("  支付表:")
            print("    - idx_payment_status_date (status, due_date)")
            print("    - idx_payment_contract_status (contract_id, status)")
            print("\n优化效果:")
            print("  - 合同列表查询性能提升（按状态筛选并排序）")
            print("  - 租客合同查询性能提升（按租客和状态筛选）")
            print("  - 支付记录查询性能提升（按状态筛选并排序）")
            print("  - 合同支付记录查询性能提升（按合同和状态筛选）")
            print("\n注意事项：")
            print("1. 索引会占用额外的存储空间")
            print("2. 索引会降低插入、更新、删除的速度")
            print("3. 建议定期使用 ANALYZE 命令更新统计信息")
            return True
        else:
            print("索引优化迁移部分失败，请检查错误信息")
            print("="*80)
            return False

    except Exception as e:
        print(f"\n迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    from app import create_app

    app = create_app()
    with app.app_context():
        success = main()
        sys.exit(0 if success else 1)
