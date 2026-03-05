"""
数据库迁移脚本：添加软删除字段

为所有现有表添加 deleted_at 字段，实现软删除功能

使用方法：
    python app/migrations/add_soft_delete_column.py

迁移内容：
    - 为所有继承 BaseModel 的表添加 deleted_at 列（DateTime, nullable=True）
    - 现有数据的 deleted_at 默认为 NULL（未删除状态）
    - 添加索引以优化查询性能
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


def get_all_tables(cursor):
    """
    获取所有表名
    
    Args:
        cursor: 数据库游标
    
    Returns:
        list: 表名列表
    """
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return [row[0] for row in cursor.fetchall()]


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


def add_soft_delete_column():
    """
    为所有表添加 deleted_at 字段
    """
    db_path = get_db_path()
    
    print("=" * 70)
    print("开始添加软删除字段（deleted_at）...")
    print("=" * 70)
    print(f"数据库路径: {db_path}")
    print()
    
    if not Path(db_path).exists():
        print(f"✗ 数据库文件不存在: {db_path}")
        return False
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有表
    tables = get_all_tables(cursor)
    
    # 需要处理的表（排除系统表）
    target_tables = [
        'users',
        'houses',
        'rooms',
        'tenants',
        'landlords',
        'contracts',
        'landlord_contracts',
        'payments',
        'media',
    ]
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for table_name in target_tables:
        if table_name not in tables:
            print(f"⊗ 表 {table_name} 不存在，跳过")
            skip_count += 1
            continue
        
        try:
            # 检查列是否已存在
            if check_column_exists(cursor, table_name, 'deleted_at'):
                print(f"✓ 表 {table_name} 已有 deleted_at 列，跳过")
                skip_count += 1
                continue
            
            # 添加 deleted_at 列
            print(f"→ 为表 {table_name} 添加 deleted_at 列...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN deleted_at DATETIME")
            conn.commit()
            print(f"✓ 表 {table_name} 添加 deleted_at 列成功")
            success_count += 1
            
        except Exception as e:
            print(f"✗ 表 {table_name} 添加 deleted_at 列失败：{str(e)}")
            conn.rollback()
            error_count += 1
    
    conn.close()
    
    print()
    print("=" * 70)
    print("迁移完成！")
    print(f"  成功：{success_count} 个表")
    print(f"  跳过：{skip_count} 个表")
    print(f"  失败：{error_count} 个表")
    print("=" * 70)
    
    return error_count == 0


def add_indexes():
    """
    为 deleted_at 字段添加索引，优化查询性能
    """
    db_path = get_db_path()
    
    print()
    print("=" * 70)
    print("添加索引以优化查询性能...")
    print("=" * 70)
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    target_tables = [
        'users',
        'houses',
        'rooms',
        'tenants',
        'landlords',
        'contracts',
        'landlord_contracts',
        'payments',
        'media',
    ]
    
    for table_name in target_tables:
        try:
            # 检查列是否存在
            if not check_column_exists(cursor, table_name, 'deleted_at'):
                continue
            
            # 添加索引
            index_name = f'idx_{table_name}_deleted_at'
            
            # 检查索引是否已存在
            if check_index_exists(cursor, table_name, index_name):
                print(f"⊗ 表 {table_name} 已有索引 {index_name}，跳过")
                continue
            
            print(f"→ 为表 {table_name} 添加索引 {index_name}...")
            cursor.execute(f"CREATE INDEX {index_name} ON {table_name} (deleted_at)")
            conn.commit()
            print(f"✓ 表 {table_name} 添加索引成功")
            
        except Exception as e:
            print(f"✗ 表 {table_name} 添加索引失败：{str(e)}")
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
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    target_tables = [
        'users',
        'houses',
        'rooms',
        'tenants',
        'landlords',
        'contracts',
        'landlord_contracts',
        'payments',
        'media',
    ]
    
    for table_name in target_tables:
        # 检查表是否存在
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            continue
        
        has_deleted_at = check_column_exists(cursor, table_name, 'deleted_at')
        
        status = "✓" if has_deleted_at else "✗"
        print(f"{status} {table_name:25} deleted_at: {'存在' if has_deleted_at else '不存在'}")
    
    conn.close()
    print("=" * 70)


if __name__ == '__main__':
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "软删除字段迁移脚本" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # 执行迁移
    success = add_soft_delete_column()
    
    # 添加索引
    add_indexes()
    
    # 验证结果
    verify_migration()
    
    print()
    if success:
        print("✓ 迁移成功完成！")
        print()
        print("使用说明：")
        print("  1. 所有模型已自动继承软删除功能")
        print("  2. 使用 Model.query.all() 自动过滤已删除记录")
        print("  3. 使用 Model.query.with_deleted().all() 查询包含已删除记录")
        print("  4. 使用 Model.query.only_deleted().all() 仅查询已删除记录")
        print("  5. 使用 obj.soft_delete() 软删除记录")
        print("  6. 使用 obj.restore() 恢复已删除记录")
        print()
    else:
        print("✗ 迁移过程中出现错误，请检查日志")
    
    sys.exit(0 if success else 1)
