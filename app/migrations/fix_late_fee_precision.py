"""
滞纳金精度修复迁移脚本

修复 late_fee 字段的精度问题：
1. 将 late_fee 默认值从 0 改为 Decimal('0.00')
2. 将 late_fee_rate 默认值从 0.0005 改为 Decimal('0.0005')
3. 处理现有数据的精度问题

注意事项：
- SQLite 不支持直接 ALTER COLUMN，需要重建表
- 迁移过程中会保留现有数据
- 建议在执行前备份数据库
"""
import sys
import os
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from sqlalchemy import text


def backup_table_data(table_name):
    """备份表数据"""
    print(f"  -> 备份 {table_name} 表数据...")
    result = db.session.execute(text(f"SELECT * FROM {table_name}"))
    rows = result.fetchall()
    columns = result.keys()
    print(f"  * 备份了 {len(rows)} 条记录")
    return rows, columns


def migrate_payments_late_fee():
    """迁移 payments 表的滞纳金字段精度"""
    print("\n[1/1] 迁移 payments 表滞纳金字段精度...")
    
    try:
        # 检查表是否存在
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='payments'
        """)).scalar()
        
        if result == 0:
            print("  * payments 表不存在，跳过迁移")
            return True
        
        # 检查是否需要迁移（检查 late_fee 字段是否存在）
        table_info = db.session.execute(text("PRAGMA table_info(payments)")).fetchall()
        columns = {row[1]: row[2] for row in table_info}
        
        if 'late_fee' not in columns:
            print("  * late_fee 字段不存在，跳过迁移")
            return True
        
        # 备份数据
        rows, columns_list = backup_table_data('payments')
        
        # 创建新表，使用正确的 NUMERIC 类型和默认值
        print("  -> 创建新表结构...")
        db.session.execute(text("""
            CREATE TABLE payments_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_no VARCHAR(50) NOT NULL UNIQUE,
                amount NUMERIC(10, 2) NOT NULL,
                paid_amount NUMERIC(10, 2) DEFAULT 0,
                payment_type VARCHAR(20) NOT NULL,
                payment_method VARCHAR(50),
                period_start DATE,
                period_end DATE,
                payment_date DATE,
                due_date DATE NOT NULL,
                confirmed_date DATETIME,
                late_fee NUMERIC(10, 2) DEFAULT 0.00,
                late_fee_rate NUMERIC(8, 6) DEFAULT 0.000500,
                overdue_days INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'pending',
                remark TEXT,
                receipt_file VARCHAR(255),
                contract_id INTEGER,
                operator_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                deleted_at DATETIME,
                FOREIGN KEY (contract_id) REFERENCES contracts(id),
                FOREIGN KEY (operator_id) REFERENCES users(id)
            )
        """))
        
        # 迁移数据，确保精度正确
        if rows:
            print("  -> 迁移数据并修复精度...")
            for row in rows:
                row_dict = dict(zip(columns_list, row))
                
                # 处理 late_fee 精度
                if row_dict.get('late_fee') is not None:
                    late_fee = Decimal(str(row_dict['late_fee'])).quantize(Decimal('0.01'))
                    row_dict['late_fee'] = float(late_fee)
                else:
                    row_dict['late_fee'] = 0.00
                
                # 处理 late_fee_rate 精度
                if row_dict.get('late_fee_rate') is not None:
                    late_fee_rate = Decimal(str(row_dict['late_fee_rate'])).quantize(Decimal('0.000001'))
                    row_dict['late_fee_rate'] = float(late_fee_rate)
                else:
                    row_dict['late_fee_rate'] = 0.000500
                
                # 处理 amount 和 paid_amount 精度
                if row_dict.get('amount') is not None:
                    amount = Decimal(str(row_dict['amount'])).quantize(Decimal('0.01'))
                    row_dict['amount'] = float(amount)
                
                if row_dict.get('paid_amount') is not None:
                    paid_amount = Decimal(str(row_dict['paid_amount'])).quantize(Decimal('0.01'))
                    row_dict['paid_amount'] = float(paid_amount)
                
                # 构建插入语句
                columns_str = ', '.join(columns_list)
                placeholders = ', '.join([f':{col}' for col in columns_list])
                insert_sql = f"INSERT INTO payments_new ({columns_str}) VALUES ({placeholders})"
                
                db.session.execute(text(insert_sql), row_dict)
        
        # 删除旧表，重命名新表
        print("  -> 替换旧表...")
        db.session.execute(text("DROP TABLE payments"))
        db.session.execute(text("ALTER TABLE payments_new RENAME TO payments"))
        
        # 重建索引
        print("  -> 重建索引...")
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_contract_id ON payments(contract_id)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_due_date ON payments(due_date)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_payment_type ON payments(payment_type)"))
        
        db.session.commit()
        print("  * payments 表迁移完成")
        return True
        
    except Exception as e:
        print(f"  X payments 表迁移失败：{str(e)}")
        db.session.rollback()
        return False


def verify_migration():
    """验证迁移结果"""
    print("\n验证迁移结果...")
    
    try:
        # 检查表结构
        table_info = db.session.execute(text("PRAGMA table_info(payments)")).fetchall()
        columns = {row[1]: {'type': row[2], 'default': row[4]} for row in table_info}
        
        print("\n表结构验证：")
        for col_name, info in columns.items():
            if col_name in ['late_fee', 'late_fee_rate', 'amount', 'paid_amount']:
                print(f"  {col_name}: type={info['type']}, default={info['default']}")
        
        # 检查数据精度
        result = db.session.execute(text("""
            SELECT id, late_fee, late_fee_rate, amount, paid_amount 
            FROM payments 
            LIMIT 5
        """)).fetchall()
        
        print("\n数据样本验证：")
        for row in result:
            print(f"  ID={row[0]}: late_fee={row[1]}, late_fee_rate={row[2]}, amount={row[3]}, paid_amount={row[4]}")
        
        print("\n  * 验证完成")
        return True
        
    except Exception as e:
        print(f"  X 验证失败：{str(e)}")
        return False


def main():
    """主迁移函数"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("滞纳金精度修复迁移脚本")
        print("=" * 80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        print("\n注意：")
        print("  1. 此脚本将修复 payments 表的滞纳金字段精度")
        print("  2. 建议在执行前备份数据库文件")
        print("  3. 迁移过程中会保留所有现有数据")
        print("  4. 迁移完成后请重启应用服务器")
        print()
        
        # 执行迁移
        success = migrate_payments_late_fee()
        
        if success:
            # 验证迁移结果
            verify_migration()
        
        print("\n" + "=" * 80)
        if success:
            print("* 所有迁移完成！")
            print("=" * 80)
            print("\n后续步骤：")
            print("  1. 重启应用服务器")
            print("  2. 验证滞纳金计算是否正常")
            print("  3. 检查前端显示是否正确")
        else:
            print("X 迁移失败，请检查错误信息")
            print("=" * 80)
        
        print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
