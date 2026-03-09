"""
数据库迁移脚本：添加押金状态跟踪字段

为 contracts 表添加押金状态跟踪功能，支持押金支付、转移和退款的全流程管理

使用方法：
    python app/migrations/add_deposit_status_tracking.py

迁移内容：
    - 为 contracts 表添加 deposit_status 列（押金状态）
    - 为 contracts 表添加 original_contract_id 列（原合同ID，用于续签）
    - 添加索引以优化查询性能
    - 根据现有支付记录初始化押金状态
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sqlite3
from pathlib import Path


def get_db_path():
    """
    获取数据库文件路径
    
    Returns:
        str: 数据库文件路径
    """
    # 从配置文件读取数据库路径
    config_path = Path(__file__).parent.parent.parent / 'instance' / 'housing_rental.db'
    if config_path.exists():
        return str(config_path)
    
    # 默认路径
    return str(Path(__file__).parent.parent.parent / 'instance' / 'housing_rental.db')


def check_column_exists(cursor, table_name, column_name):
    """
    检查表中是否存在指定列
    
    Args:
        cursor: 数据库游标
        table_name: 表名
        column_name: 列名
    
    Returns:
        bool: 列是否存在
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def check_index_exists(cursor, table_name, index_name):
    """
    检查索引是否存在
    
    Args:
        cursor: 数据库游标
        table_name: 表名
        index_name: 索引名
    
    Returns:
        bool: 索引是否存在
    """
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = cursor.fetchall()
    return any(index[1] == index_name for index in indexes)


def add_deposit_status_columns():
    """
    为 contracts 表添加押金状态字段
    """
    db_path = get_db_path()
    
    print("=" * 70)
    print("开始添加押金状态跟踪字段...")
    print("=" * 70)
    print(f"数据库路径: {db_path}")
    print()
    
    if not Path(db_path).exists():
        print(f"✗ 数据库文件不存在: {db_path}")
        return False
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    success = True
    
    try:
        # 1. 添加 deposit_status 列
        if check_column_exists(cursor, 'contracts', 'deposit_status'):
            print("✓ contracts 表已有 deposit_status 列，跳过")
        else:
            print("→ 为 contracts 表添加 deposit_status 列...")
            cursor.execute("""
                ALTER TABLE contracts 
                ADD COLUMN deposit_status VARCHAR(20) DEFAULT 'pending'
            """)
            conn.commit()
            print("✓ contracts 表添加 deposit_status 列成功")
        
        # 2. 添加 original_contract_id 列
        if check_column_exists(cursor, 'contracts', 'original_contract_id'):
            print("✓ contracts 表已有 original_contract_id 列，跳过")
        else:
            print("→ 为 contracts 表添加 original_contract_id 列...")
            cursor.execute("""
                ALTER TABLE contracts 
                ADD COLUMN original_contract_id INTEGER 
                REFERENCES contracts(id)
            """)
            conn.commit()
            print("✓ contracts 表添加 original_contract_id 列成功")
        
        # 3. 添加索引
        if not check_index_exists(cursor, 'contracts', 'idx_contracts_deposit_status'):
            print("→ 为 contracts 表添加 deposit_status 索引...")
            cursor.execute("""
                CREATE INDEX idx_contracts_deposit_status 
                ON contracts (deposit_status)
            """)
            conn.commit()
            print("✓ 添加 deposit_status 索引成功")
        else:
            print("⊗ deposit_status 索引已存在，跳过")
        
        # 4. 根据现有支付记录初始化押金状态
        print()
        print("→ 根据现有支付记录初始化押金状态...")
        
        # 查询所有押金支付记录
        cursor.execute("""
            SELECT DISTINCT contract_id 
            FROM payments 
            WHERE payment_type = 'deposit' AND status = 'paid'
        """)
        paid_contracts = [row[0] for row in cursor.fetchall()]
        
        if paid_contracts:
            # 更新已支付押金的合同状态
            placeholders = ','.join(['?' for _ in paid_contracts])
            cursor.execute(f"""
                UPDATE contracts 
                SET deposit_status = 'paid' 
                WHERE id IN ({placeholders}) AND deposit_status = 'pending'
            """, paid_contracts)
            updated_count = cursor.rowcount
            conn.commit()
            print(f"✓ 已更新 {updated_count} 个合同的押金状态为 'paid'")
        else:
            print("⊗ 没有找到已支付的押金记录")
        
        # 5. 处理已退款的押金
        cursor.execute("""
            SELECT DISTINCT contract_id 
            FROM deposit_refunds 
            WHERE status = 'completed'
        """)
        refunded_contracts = [row[0] for row in cursor.fetchall()]
        
        if refunded_contracts:
            placeholders = ','.join(['?' for _ in refunded_contracts])
            cursor.execute(f"""
                UPDATE contracts 
                SET deposit_status = 'refunded' 
                WHERE id IN ({placeholders})
            """, refunded_contracts)
            updated_count = cursor.rowcount
            conn.commit()
            print(f"✓ 已更新 {updated_count} 个合同的押金状态为 'refunded'")
        
        # 6. 处理押金为0的合同（直接标记为已退款）
        cursor.execute("""
            UPDATE contracts 
            SET deposit_status = 'refunded' 
            WHERE deposit_amount = 0 AND deposit_status = 'pending'
        """)
        zero_deposit_count = cursor.rowcount
        if zero_deposit_count > 0:
            conn.commit()
            print(f"✓ 已更新 {zero_deposit_count} 个押金为0的合同状态为 'refunded'")
        
    except Exception as e:
        print(f"✗ 迁移失败：{str(e)}")
        conn.rollback()
        success = False
    finally:
        conn.close()
    
    print()
    print("=" * 70)
    if success:
        print("✓ 迁移成功完成！")
    else:
        print("✗ 迁移过程中出现错误")
    print("=" * 70)
    
    return success


def verify_migration():
    """
    验证迁移结果
    """
    db_path = get_db_path()
    
    print()
    print("=" * 70)
    print("验证迁移结果...")
    print("=" * 70)
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查列是否存在
    has_deposit_status = check_column_exists(cursor, 'contracts', 'deposit_status')
    has_original_contract_id = check_column_exists(cursor, 'contracts', 'original_contract_id')
    
    status1 = "✓" if has_deposit_status else "✗"
    status2 = "✓" if has_original_contract_id else "✗"
    
    print(f"{status1} contracts.deposit_status: {'存在' if has_deposit_status else '不存在'}")
    print(f"{status2} contracts.original_contract_id: {'存在' if has_original_contract_id else '不存在'}")
    
    # 统计押金状态分布
    if has_deposit_status:
        print()
        print("押金状态分布：")
        cursor.execute("""
            SELECT deposit_status, COUNT(*) 
            FROM contracts 
            GROUP BY deposit_status
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} 个合同")
    
    conn.close()
    print("=" * 70)


if __name__ == '__main__':
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "押金状态跟踪迁移脚本" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # 执行迁移
    success = add_deposit_status_columns()
    
    # 验证结果
    verify_migration()
    
    print()
    if success:
        print("✓ 迁移成功完成！")
        print()
        print("使用说明：")
        print("  1. 押金状态包括：pending(待支付)、paid(已支付)、transferred(已转移)、refunded(已退款)")
        print("  2. 续签合同时，原合同押金状态会自动更新为 'transferred'")
        print("  3. 押金支付后，合同押金状态会自动更新为 'paid'")
        print("  4. 押金退款后，合同押金状态会自动更新为 'refunded'")
        print("  5. 可通过 contract.deposit_status 查询押金状态")
        print("  6. 可通过 contract.original_contract_id 追溯续签关系")
        print()
    
    sys.exit(0 if success else 1)
