"""
添加唯一约束迁移脚本

为以下字段添加数据库级别的唯一约束：
1. contracts.contract_no - 合同编号
2. payments.payment_no - 支付编号
3. landlord_contracts.contract_no - 承包合同编号

SQLite 不支持直接添加唯一约束，需要通过重建表的方式实现
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from sqlalchemy import text, inspect


def check_unique_constraint_exists(table_name, column_name):
    """
    检查表中某列是否已存在唯一约束
    
    Args:
        table_name: 表名
        column_name: 列名
        
    Returns:
        bool: 是否存在唯一约束
    """
    # 获取表的索引信息
    result = db.session.execute(text(f"""
        SELECT name, sql FROM sqlite_master 
        WHERE type='index' AND tbl_name='{table_name}'
    """)).fetchall()
    
    for index_name, index_sql in result:
        # 检查是否有唯一索引包含该列
        if index_sql and 'UNIQUE' in index_sql.upper() and column_name in index_sql:
            return True
        # 检查索引名称是否符合命名规范
        if f'unique_{column_name}' in index_name.lower() or f'ix_{table_name}_{column_name}' in index_name.lower():
            # 进一步检查是否是唯一索引
            index_info = db.session.execute(text(f"""
                SELECT * FROM pragma_index_info('{index_name}')
            """)).fetchall()
            for info in index_info:
                if column_name in str(info):
                    # 检查是否唯一
                    idx_list = db.session.execute(text(f"""
                        SELECT * FROM pragma_index_list('{table_name}')
                        WHERE name='{index_name}'
                    """)).fetchone()
                    if idx_list and 'unique' in str(idx_list).lower():
                        return True
    
    # 检查表定义中是否有 UNIQUE 约束
    table_info = db.session.execute(text(f"""
        SELECT sql FROM sqlite_master 
        WHERE type='table' AND name='{table_name}'
    """)).fetchone()
    
    if table_info and table_info[0]:
        sql = table_info[0].upper()
        # 检查是否有 UNIQUE(column_name) 或 column_name UNIQUE
        if f'UNIQUE({column_name.upper()})' in sql or f'{column_name.upper()} UNIQUE' in sql:
            return True
        # 也检查原始大小写
        sql_original = table_info[0]
        if f'UNIQUE({column_name})' in sql_original or f'{column_name} UNIQUE' in sql_original:
            return True
    
    return False


def check_duplicate_values(table_name, column_name):
    """
    检查表中是否存在重复值
    
    Args:
        table_name: 表名
        column_name: 列名
        
    Returns:
        list: 重复值列表
    """
    result = db.session.execute(text(f"""
        SELECT {column_name}, COUNT(*) as count
        FROM {table_name}
        WHERE {column_name} IS NOT NULL
        GROUP BY {column_name}
        HAVING COUNT(*) > 1
    """)).fetchall()
    
    return result


def add_unique_constraint_sqlite(table_name, column_name, model_class):
    """
    为 SQLite 表添加唯一约束（通过重建表）
    
    SQLite 不支持 ALTER TABLE ADD CONSTRAINT，需要：
    1. 创建新表（带唯一约束）
    2. 复制数据
    3. 删除旧表
    4. 重命名新表
    
    Args:
        table_name: 表名
        column_name: 列名
        model_class: SQLAlchemy 模型类
    """
    print(f"  正在为 {table_name}.{column_name} 添加唯一约束...")
    
    # 获取表结构
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table_name)
    
    # 构建列定义
    column_defs = []
    column_names = []
    for col in columns:
        col_name = col['name']
        col_type = str(col['type'])
        nullable = 'NULL' if col['nullable'] else 'NOT NULL'
        default = f"DEFAULT {col.get('default')}" if col.get('default') else ''
        
        # 为目标列添加 UNIQUE 约束
        if col_name == column_name:
            column_defs.append(f"{col_name} {col_type} {nullable} UNIQUE {default}")
        else:
            column_defs.append(f"{col_name} {col_type} {nullable} {default}")
        
        column_names.append(col_name)
    
    # 获取外键
    foreign_keys = inspector.get_foreign_keys(table_name)
    fk_constraints = []
    for fk in foreign_keys:
        fk_name = fk.get('name', f"fk_{table_name}_{fk['constrained_columns'][0]}")
        fk_cols = ', '.join(fk['constrained_columns'])
        ref_table = fk['referred_table']
        ref_cols = ', '.join(fk['referred_columns'])
        fk_constraints.append(f"FOREIGN KEY ({fk_cols}) REFERENCES {ref_table}({ref_cols})")
    
    # 创建临时表
    temp_table_name = f"{table_name}_temp_unique"
    
    # 构建创建表语句
    create_sql = f"""
        CREATE TABLE {temp_table_name} (
            {', '.join(column_defs)}
            {', ' + ', '.join(fk_constraints) if fk_constraints else ''}
        )
    """
    
    print(f"  创建临时表 {temp_table_name}...")
    db.session.execute(text(create_sql))
    
    # 复制数据
    cols_str = ', '.join(column_names)
    print(f"  复制数据到临时表...")
    db.session.execute(text(f"""
        INSERT INTO {temp_table_name} ({cols_str})
        SELECT {cols_str} FROM {table_name}
    """))
    
    # 获取索引信息
    indexes = inspector.get_indexes(table_name)
    
    # 删除旧表
    print(f"  删除原表 {table_name}...")
    db.session.execute(text(f"DROP TABLE {table_name}"))
    
    # 重命名新表
    print(f"  重命名临时表为 {table_name}...")
    db.session.execute(text(f"ALTER TABLE {temp_table_name} RENAME TO {table_name}"))
    
    # 重建索引（排除唯一约束相关的索引）
    for idx in indexes:
        idx_name = idx['name']
        idx_cols = ', '.join(idx['column_names'])
        unique = 'UNIQUE' if idx['unique'] else ''
        
        # 跳过自动创建的主键索引
        if idx_name.startswith('sqlite_'):
            continue
        
        # 如果索引包含目标列且是唯一索引，跳过（已在表定义中）
        if column_name in idx['column_names'] and idx['unique']:
            continue
        
        print(f"  重建索引 {idx_name}...")
        try:
            db.session.execute(text(f"""
                CREATE {unique} INDEX {idx_name} ON {table_name} ({idx_cols})
            """))
        except Exception as e:
            print(f"  警告：创建索引 {idx_name} 失败：{e}")
    
    db.session.commit()
    print(f"  ✓ {table_name}.{column_name} 唯一约束添加成功")


def migrate():
    """执行迁移"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("开始添加唯一约束迁移...")
        print("=" * 70)
        print()
        
        # 定义需要添加唯一约束的表和列
        constraints = [
            {
                'table_name': 'contracts',
                'column_name': 'contract_no',
                'description': '合同编号'
            },
            {
                'table_name': 'payments',
                'column_name': 'payment_no',
                'description': '支付编号'
            },
            {
                'table_name': 'landlord_contracts',
                'column_name': 'contract_no',
                'description': '承包合同编号'
            }
        ]
        
        results = []
        
        for constraint in constraints:
            table_name = constraint['table_name']
            column_name = constraint['column_name']
            description = constraint['description']
            
            print(f"[{description}] {table_name}.{column_name}")
            print("-" * 70)
            
            try:
                # 1. 检查表是否存在
                table_exists = db.session.execute(text(f"""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """)).scalar()
                
                if not table_exists:
                    print(f"  ⊗ 表 {table_name} 不存在，跳过")
                    print()
                    results.append({
                        'table': table_name,
                        'column': column_name,
                        'status': 'skipped',
                        'message': '表不存在'
                    })
                    continue
                
                # 2. 检查是否已有唯一约束
                if check_unique_constraint_exists(table_name, column_name):
                    print(f"  ✓ 唯一约束已存在，无需迁移")
                    print()
                    results.append({
                        'table': table_name,
                        'column': column_name,
                        'status': 'exists',
                        'message': '唯一约束已存在'
                    })
                    continue
                
                # 3. 检查是否存在重复值
                duplicates = check_duplicate_values(table_name, column_name)
                
                if duplicates:
                    print(f"  ✗ 发现重复值，无法添加唯一约束：")
                    for dup in duplicates:
                        print(f"    - {column_name}={dup[0]}, 重复次数={dup[1]}")
                    print()
                    results.append({
                        'table': table_name,
                        'column': column_name,
                        'status': 'error',
                        'message': f'存在 {len(duplicates)} 个重复值'
                    })
                    continue
                
                # 4. 添加唯一约束
                # 获取模型类
                from app.models.contract import Contract
                from app.models.payment import Payment
                from app.models.landlord_contract import LandlordContract
                
                model_map = {
                    'contracts': Contract,
                    'payments': Payment,
                    'landlord_contracts': LandlordContract
                }
                
                model_class = model_map.get(table_name)
                add_unique_constraint_sqlite(table_name, column_name, model_class)
                print()
                
                results.append({
                    'table': table_name,
                    'column': column_name,
                    'status': 'success',
                    'message': '唯一约束添加成功'
                })
                
            except Exception as e:
                print(f"  ✗ 迁移失败：{str(e)}")
                print()
                results.append({
                    'table': table_name,
                    'column': column_name,
                    'status': 'error',
                    'message': str(e)
                })
                db.session.rollback()
        
        # 打印汇总结果
        print("=" * 70)
        print("迁移结果汇总")
        print("=" * 70)
        
        success_count = sum(1 for r in results if r['status'] in ['success', 'exists'])
        error_count = sum(1 for r in results if r['status'] == 'error')
        skipped_count = sum(1 for r in results if r['status'] == 'skipped')
        
        for result in results:
            status_icon = {
                'success': '✓',
                'exists': '✓',
                'error': '✗',
                'skipped': '⊗'
            }.get(result['status'], '?')
            
            print(f"{status_icon} {result['table']}.{result['column']}: {result['message']}")
        
        print()
        print(f"总计：成功/已存在 {success_count}，失败 {error_count}，跳过 {skipped_count}")
        print("=" * 70)
        
        return error_count == 0


if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
