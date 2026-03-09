"""
数据库迁移脚本：添加租客信用评分字段

为 tenants 表添加信用评分相关字段

使用方法：
    python app/migrations/add_tenant_credit_fields.py

迁移内容：
    - 添加 credit_score 列（Integer, default=100）
    - 添加 credit_records 列（JSON, default=[]）
    - 为现有租客设置默认信用分 100
    - 添加索引以优化查询性能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sqlite3
from pathlib import Path


def get_db_path():
    """
    获取数据库文件路径
    
    Returns:
        str: 数据库文件路径
    """
    config_path = Path(__file__).parent.parent.parent / 'instance' / 'housing_rental.db'
    if config_path.exists():
        return str(config_path)
    
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


def add_credit_fields():
    """
    为 tenants 表添加信用评分字段
    """
    db_path = get_db_path()
    
    print("=" * 70)
    print("开始添加租客信用评分字段...")
    print("=" * 70)
    print(f"数据库路径: {db_path}")
    print()
    
    if not Path(db_path).exists():
        print(f"✗ 数据库文件不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    try:
        if check_column_exists(cursor, 'tenants', 'credit_score'):
            print("✓ tenants 表已有 credit_score 列，跳过")
            skip_count += 1
        else:
            print("→ 为 tenants 表添加 credit_score 列...")
            cursor.execute("ALTER TABLE tenants ADD COLUMN credit_score INTEGER DEFAULT 100")
            conn.commit()
            print("✓ tenants 表添加 credit_score 列成功")
            success_count += 1
        
        if check_column_exists(cursor, 'tenants', 'credit_records'):
            print("✓ tenants 表已有 credit_records 列，跳过")
            skip_count += 1
        else:
            print("→ 为 tenants 表添加 credit_records 列...")
            cursor.execute("ALTER TABLE tenants ADD COLUMN credit_records TEXT DEFAULT '[]'")
            conn.commit()
            print("✓ tenants 表添加 credit_records 列成功")
            success_count += 1
        
        cursor.execute("UPDATE tenants SET credit_score = 100 WHERE credit_score IS NULL")
        affected_rows = cursor.rowcount
        conn.commit()
        print(f"✓ 为 {affected_rows} 个现有租客设置默认信用分 100")
        
    except Exception as e:
        print(f"✗ 添加字段失败：{str(e)}")
        conn.rollback()
        error_count += 1
    
    conn.close()
    
    print()
    print("=" * 70)
    print("字段添加完成！")
    print(f"  成功：{success_count} 个字段")
    print(f"  跳过：{skip_count} 个字段")
    print(f"  失败：{error_count} 个字段")
    print("=" * 70)
    
    return error_count == 0


def add_indexes():
    """
    为信用评分字段添加索引
    """
    db_path = get_db_path()
    
    print()
    print("=" * 70)
    print("添加索引以优化查询性能...")
    print("=" * 70)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        if not check_column_exists(cursor, 'tenants', 'credit_score'):
            print("⊗ credit_score 列不存在，跳过索引创建")
            return
        
        index_name = 'idx_tenants_credit_score'
        
        if check_index_exists(cursor, 'tenants', index_name):
            print(f"⊗ tenants 表已有索引 {index_name}，跳过")
        else:
            print(f"→ 为 tenants 表添加索引 {index_name}...")
            cursor.execute(f"CREATE INDEX {index_name} ON tenants (credit_score)")
            conn.commit()
            print(f"✓ tenants 表添加索引成功")
        
    except Exception as e:
        print(f"✗ 添加索引失败：{str(e)}")
        conn.rollback()
    
    conn.close()
    print("=" * 70)


def verify_migration():
    """
    验证迁移结果
    """
    db_path = get_db_path()
    
    print()
    print("=" * 70)
    print("验证迁移结果...")
    print("=" * 70)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    has_credit_score = check_column_exists(cursor, 'tenants', 'credit_score')
    has_credit_records = check_column_exists(cursor, 'tenants', 'credit_records')
    
    status_score = "✓" if has_credit_score else "✗"
    status_records = "✓" if has_credit_records else "✗"
    
    print(f"{status_score} credit_score: {'存在' if has_credit_score else '不存在'}")
    print(f"{status_records} credit_records: {'存在' if has_credit_records else '不存在'}")
    
    if has_credit_score:
        cursor.execute("SELECT COUNT(*) FROM tenants WHERE credit_score IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"  信用分为 NULL 的租客数量: {null_count}")
        
        cursor.execute("SELECT COUNT(*) FROM tenants")
        total_count = cursor.fetchone()[0]
        print(f"  总租客数量: {total_count}")
    
    conn.close()
    print("=" * 70)


if __name__ == '__main__':
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "租客信用评分字段迁移脚本" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    success = add_credit_fields()
    
    add_indexes()
    
    verify_migration()
    
    print()
    if success:
        print("✓ 迁移成功完成！")
        print()
        print("使用说明：")
        print("  1. 租客默认信用评分为 100 分")
        print("  2. 使用 tenant.add_credit_record() 添加信用记录")
        print("  3. 使用 tenant.get_credit_records() 获取信用记录")
        print("  4. 信用评分范围：0-100 分")
        print()
        print("信用事件权重：")
        print("  - 逾期 7 天：-5 分")
        print("  - 逾期 30 天：-15 分")
        print("  - 提前解约：-20 分")
        print("  - 按时付款：+2 分")
        print("  - 合同正常完成：+10 分")
        print()
    else:
        print("✗ 迁移过程中出现错误，请检查日志")
    
    sys.exit(0 if success else 1)
