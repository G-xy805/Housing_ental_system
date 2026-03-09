"""
金额字段精度修复迁移脚本

将所有金额字段从 Float 类型迁移到 Numeric(10, 2) 类型
解决浮点数精度问题

迁移的表和字段：
1. contracts: rent_amount, deposit_amount
2. payments: amount, paid_amount, late_fee, late_fee_rate
3. deposit_refunds: original_deposit, total_deduction, refund_amount
4. houses: rent_price, deposit
5. rooms: rent_price, deposit
6. landlord_contracts: contract_amount, service_fee_rate, minimum_fee

注意事项：
- SQLite 不支持直接 ALTER COLUMN，需要重建表
- 迁移过程中会保留现有数据
- 建议在执行前备份数据库
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from sqlalchemy import text


def backup_table_data(table_name):
    """备份表数据"""
    print(f"  → 备份 {table_name} 表数据...")
    result = db.session.execute(text(f"SELECT * FROM {table_name}"))
    rows = result.fetchall()
    columns = result.keys()
    print(f"  ✓ 备份了 {len(rows)} 条记录")
    return rows, columns


def migrate_contracts_table():
    """迁移 contracts 表"""
    print("\n[1/6] 迁移 contracts 表...")
    
    try:
        # 检查是否需要迁移
        result = db.session.execute(text("""
            SELECT sql FROM sqlite_master WHERE type='table' AND name='contracts'
        """)).scalar()
        
        if 'NUMERIC' in result or 'DECIMAL' in result:
            print("  ✓ contracts 表已经是 NUMERIC 类型，跳过迁移")
            return True
        
        # 备份数据
        rows, columns = backup_table_data('contracts')
        
        # 创建新表
        print("  → 创建新表结构...")
        db.session.execute(text("""
            CREATE TABLE contracts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_no VARCHAR(50) NOT NULL UNIQUE,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                rent_amount NUMERIC(10, 2) NOT NULL,
                deposit_amount NUMERIC(10, 2) NOT NULL,
                payment_type VARCHAR(20) DEFAULT '月付',
                payment_cycle INTEGER DEFAULT 1,
                status VARCHAR(20) DEFAULT 'draft',
                contract_file VARCHAR(255),
                remark TEXT,
                house_id INTEGER NOT NULL,
                room_id INTEGER,
                tenant_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (house_id) REFERENCES houses(id),
                FOREIGN KEY (room_id) REFERENCES rooms(id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            )
        """))
        
        # 迁移数据
        if rows:
            print("  → 迁移数据...")
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO contracts_new ({', '.join(columns)}) VALUES ({placeholders})"
            
            for row in rows:
                db.session.execute(text(insert_sql), dict(zip(columns, row)))
        
        # 删除旧表，重命名新表
        print("  → 替换旧表...")
        db.session.execute(text("DROP TABLE contracts"))
        db.session.execute(text("ALTER TABLE contracts_new RENAME TO contracts"))
        
        # 重建索引
        print("  → 重建索引...")
        db.session.execute(text("CREATE INDEX idx_contracts_house_id ON contracts(house_id)"))
        db.session.execute(text("CREATE INDEX idx_contracts_room_id ON contracts(room_id)"))
        db.session.execute(text("CREATE INDEX idx_contracts_tenant_id ON contracts(tenant_id)"))
        db.session.execute(text("CREATE INDEX idx_contracts_status ON contracts(status)"))
        db.session.execute(text("CREATE INDEX idx_contracts_dates ON contracts(start_date, end_date)"))
        
        db.session.commit()
        print("  ✓ contracts 表迁移完成")
        return True
        
    except Exception as e:
        print(f"  ✗ contracts 表迁移失败：{str(e)}")
        db.session.rollback()
        return False


def migrate_payments_table():
    """迁移 payments 表"""
    print("\n[2/6] 迁移 payments 表...")
    
    try:
        # 检查是否需要迁移
        result = db.session.execute(text("""
            SELECT sql FROM sqlite_master WHERE type='table' AND name='payments'
        """)).scalar()
        
        if 'NUMERIC' in result or 'DECIMAL' in result:
            print("  ✓ payments 表已经是 NUMERIC 类型，跳过迁移")
            return True
        
        # 备份数据
        rows, columns = backup_table_data('payments')
        
        # 创建新表
        print("  → 创建新表结构...")
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
                late_fee NUMERIC(10, 2) DEFAULT 0,
                late_fee_rate NUMERIC(8, 6) DEFAULT 0.0005,
                overdue_days INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'pending',
                remark TEXT,
                receipt_file VARCHAR(255),
                contract_id INTEGER,
                operator_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (contract_id) REFERENCES contracts(id),
                FOREIGN KEY (operator_id) REFERENCES users(id)
            )
        """))
        
        # 迁移数据
        if rows:
            print("  → 迁移数据...")
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO payments_new ({', '.join(columns)}) VALUES ({placeholders})"
            
            for row in rows:
                db.session.execute(text(insert_sql), dict(zip(columns, row)))
        
        # 删除旧表，重命名新表
        print("  → 替换旧表...")
        db.session.execute(text("DROP TABLE payments"))
        db.session.execute(text("ALTER TABLE payments_new RENAME TO payments"))
        
        # 重建索引
        print("  → 重建索引...")
        db.session.execute(text("CREATE INDEX idx_payments_contract_id ON payments(contract_id)"))
        db.session.execute(text("CREATE INDEX idx_payments_status ON payments(status)"))
        db.session.execute(text("CREATE INDEX idx_payments_due_date ON payments(due_date)"))
        db.session.execute(text("CREATE INDEX idx_payments_payment_type ON payments(payment_type)"))
        
        db.session.commit()
        print("  ✓ payments 表迁移完成")
        return True
        
    except Exception as e:
        print(f"  ✗ payments 表迁移失败：{str(e)}")
        db.session.rollback()
        return False


def migrate_deposit_refunds_table():
    """迁移 deposit_refunds 表"""
    print("\n[3/6] 迁移 deposit_refunds 表...")
    
    try:
        # 检查表是否存在
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='deposit_refunds'
        """)).scalar()
        
        if result == 0:
            print("  ✓ deposit_refunds 表不存在，跳过迁移")
            return True
        
        # 检查是否需要迁移
        result = db.session.execute(text("""
            SELECT sql FROM sqlite_master WHERE type='table' AND name='deposit_refunds'
        """)).scalar()
        
        if 'NUMERIC' in result or 'DECIMAL' in result:
            print("  ✓ deposit_refunds 表已经是 NUMERIC 类型，跳过迁移")
            return True
        
        # 备份数据
        rows, columns = backup_table_data('deposit_refunds')
        
        # 创建新表
        print("  → 创建新表结构...")
        db.session.execute(text("""
            CREATE TABLE deposit_refunds_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id INTEGER NOT NULL,
                tenant_id INTEGER NOT NULL,
                house_id INTEGER NOT NULL,
                original_deposit NUMERIC(10, 2) NOT NULL,
                deductions JSON DEFAULT '[]',
                total_deduction NUMERIC(10, 2) DEFAULT 0,
                refund_amount NUMERIC(10, 2) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                processed_by INTEGER,
                processed_at DATETIME,
                completed_at DATETIME,
                remark TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (contract_id) REFERENCES contracts(id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (house_id) REFERENCES houses(id),
                FOREIGN KEY (processed_by) REFERENCES users(id)
            )
        """))
        
        # 迁移数据
        if rows:
            print("  → 迁移数据...")
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO deposit_refunds_new ({', '.join(columns)}) VALUES ({placeholders})"
            
            for row in rows:
                db.session.execute(text(insert_sql), dict(zip(columns, row)))
        
        # 删除旧表，重命名新表
        print("  → 替换旧表...")
        db.session.execute(text("DROP TABLE deposit_refunds"))
        db.session.execute(text("ALTER TABLE deposit_refunds_new RENAME TO deposit_refunds"))
        
        # 重建索引
        print("  → 重建索引...")
        db.session.execute(text("CREATE INDEX idx_deposit_refunds_contract_id ON deposit_refunds(contract_id)"))
        db.session.execute(text("CREATE INDEX idx_deposit_refunds_tenant_id ON deposit_refunds(tenant_id)"))
        db.session.execute(text("CREATE INDEX idx_deposit_refunds_house_id ON deposit_refunds(house_id)"))
        db.session.execute(text("CREATE INDEX idx_deposit_refunds_status ON deposit_refunds(status)"))
        db.session.execute(text("CREATE INDEX idx_deposit_refunds_processed_by ON deposit_refunds(processed_by)"))
        
        db.session.commit()
        print("  ✓ deposit_refunds 表迁移完成")
        return True
        
    except Exception as e:
        print(f"  ✗ deposit_refunds 表迁移失败：{str(e)}")
        db.session.rollback()
        return False


def migrate_houses_table():
    """迁移 houses 表"""
    print("\n[4/6] 迁移 houses 表...")
    
    try:
        # 检查是否需要迁移
        result = db.session.execute(text("""
            SELECT sql FROM sqlite_master WHERE type='table' AND name='houses'
        """)).scalar()
        
        # 检查 rent_price 和 deposit 字段类型
        if result and ('NUMERIC' in result or 'DECIMAL' in result):
            print("  ✓ houses 表已经是 NUMERIC 类型，跳过迁移")
            return True
        
        # 备份数据
        rows, columns = backup_table_data('houses')
        
        # 创建新表
        print("  → 创建新表结构...")
        db.session.execute(text("""
            CREATE TABLE houses_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                province VARCHAR(50),
                city VARCHAR(50),
                district VARCHAR(50),
                address VARCHAR(200),
                latitude FLOAT,
                longitude FLOAT,
                area FLOAT,
                room_count INTEGER,
                hall_count INTEGER,
                bathroom_count INTEGER,
                floor VARCHAR(20),
                total_floors INTEGER,
                orientation VARCHAR(20),
                decoration VARCHAR(20),
                rent_price NUMERIC(10, 2),
                deposit NUMERIC(10, 2),
                payment_method VARCHAR(50),
                status VARCHAR(20) DEFAULT 'available',
                facilities JSON,
                images JSON,
                cover_image VARCHAR(255),
                rental_type VARCHAR(20) DEFAULT 'whole',
                owner_id INTEGER NOT NULL,
                landlord_id INTEGER,
                contact_name VARCHAR(50),
                contact_phone VARCHAR(20),
                contact_wechat VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (owner_id) REFERENCES users(id),
                FOREIGN KEY (landlord_id) REFERENCES landlords(id)
            )
        """))
        
        # 迁移数据
        if rows:
            print("  → 迁移数据...")
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO houses_new ({', '.join(columns)}) VALUES ({placeholders})"
            
            for row in rows:
                db.session.execute(text(insert_sql), dict(zip(columns, row)))
        
        # 删除旧表，重命名新表
        print("  → 替换旧表...")
        db.session.execute(text("DROP TABLE houses"))
        db.session.execute(text("ALTER TABLE houses_new RENAME TO houses"))
        
        # 重建索引
        print("  → 重建索引...")
        db.session.execute(text("CREATE INDEX idx_houses_status ON houses(status)"))
        db.session.execute(text("CREATE INDEX idx_houses_city ON houses(city)"))
        db.session.execute(text("CREATE INDEX idx_houses_district ON houses(district)"))
        db.session.execute(text("CREATE INDEX idx_houses_rental_type ON houses(rental_type)"))
        db.session.execute(text("CREATE INDEX idx_houses_owner_id ON houses(owner_id)"))
        db.session.execute(text("CREATE INDEX idx_houses_landlord_id ON houses(landlord_id)"))
        
        db.session.commit()
        print("  ✓ houses 表迁移完成")
        return True
        
    except Exception as e:
        print(f"  ✗ houses 表迁移失败：{str(e)}")
        db.session.rollback()
        return False


def migrate_rooms_table():
    """迁移 rooms 表"""
    print("\n[5/6] 迁移 rooms 表...")
    
    try:
        # 检查是否需要迁移
        result = db.session.execute(text("""
            SELECT sql FROM sqlite_master WHERE type='table' AND name='rooms'
        """)).scalar()
        
        if 'NUMERIC' in result or 'DECIMAL' in result:
            print("  ✓ rooms 表已经是 NUMERIC 类型，跳过迁移")
            return True
        
        # 备份数据
        rows, columns = backup_table_data('rooms')
        
        # 创建新表
        print("  → 创建新表结构...")
        db.session.execute(text("""
            CREATE TABLE rooms_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number VARCHAR(20) NOT NULL,
                room_name VARCHAR(50),
                description TEXT,
                area FLOAT,
                floor VARCHAR(20),
                orientation VARCHAR(20),
                rent_price NUMERIC(10, 2) NOT NULL,
                deposit NUMERIC(10, 2) DEFAULT 0,
                payment_method VARCHAR(50) DEFAULT 'press1_pay3',
                is_master BOOLEAN DEFAULT 0,
                facilities JSON,
                status VARCHAR(20) DEFAULT 'available',
                house_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (house_id) REFERENCES houses(id)
            )
        """))
        
        # 迁移数据
        if rows:
            print("  → 迁移数据...")
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO rooms_new ({', '.join(columns)}) VALUES ({placeholders})"
            
            for row in rows:
                db.session.execute(text(insert_sql), dict(zip(columns, row)))
        
        # 删除旧表，重命名新表
        print("  → 替换旧表...")
        db.session.execute(text("DROP TABLE rooms"))
        db.session.execute(text("ALTER TABLE rooms_new RENAME TO rooms"))
        
        # 重建索引
        print("  → 重建索引...")
        db.session.execute(text("CREATE INDEX idx_rooms_house_id ON rooms(house_id)"))
        db.session.execute(text("CREATE INDEX idx_rooms_status ON rooms(status)"))
        db.session.execute(text("CREATE UNIQUE INDEX idx_rooms_house_number ON rooms(house_id, room_number)"))
        
        db.session.commit()
        print("  ✓ rooms 表迁移完成")
        return True
        
    except Exception as e:
        print(f"  ✗ rooms 表迁移失败：{str(e)}")
        db.session.rollback()
        return False


def migrate_landlord_contracts_table():
    """迁移 landlord_contracts 表"""
    print("\n[6/6] 迁移 landlord_contracts 表...")
    
    try:
        # 检查表是否存在
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='landlord_contracts'
        """)).scalar()
        
        if result == 0:
            print("  ✓ landlord_contracts 表不存在，跳过迁移")
            return True
        
        # 检查是否需要迁移
        result = db.session.execute(text("""
            SELECT sql FROM sqlite_master WHERE type='table' AND name='landlord_contracts'
        """)).scalar()
        
        if 'NUMERIC' in result or 'DECIMAL' in result:
            print("  ✓ landlord_contracts 表已经是 NUMERIC 类型，跳过迁移")
            return True
        
        # 备份数据
        rows, columns = backup_table_data('landlord_contracts')
        
        # 创建新表
        print("  → 创建新表结构...")
        db.session.execute(text("""
            CREATE TABLE landlord_contracts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_no VARCHAR(50) NOT NULL UNIQUE,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                contract_amount NUMERIC(10, 2) NOT NULL,
                service_fee_rate NUMERIC(5, 2) NOT NULL,
                minimum_fee NUMERIC(10, 2),
                payment_cycle INTEGER DEFAULT 1,
                status VARCHAR(20) DEFAULT 'draft',
                contract_file VARCHAR(255),
                remark TEXT,
                landlord_id INTEGER NOT NULL,
                house_ids JSON DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (landlord_id) REFERENCES landlords(id)
            )
        """))
        
        # 迁移数据
        if rows:
            print("  → 迁移数据...")
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO landlord_contracts_new ({', '.join(columns)}) VALUES ({placeholders})"
            
            for row in rows:
                db.session.execute(text(insert_sql), dict(zip(columns, row)))
        
        # 删除旧表，重命名新表
        print("  → 替换旧表...")
        db.session.execute(text("DROP TABLE landlord_contracts"))
        db.session.execute(text("ALTER TABLE landlord_contracts_new RENAME TO landlord_contracts"))
        
        # 重建索引
        print("  → 重建索引...")
        db.session.execute(text("CREATE INDEX idx_landlord_contracts_landlord_id ON landlord_contracts(landlord_id)"))
        db.session.execute(text("CREATE INDEX idx_landlord_contracts_status ON landlord_contracts(status)"))
        db.session.execute(text("CREATE INDEX idx_landlord_contracts_dates ON landlord_contracts(start_date, end_date)"))
        
        db.session.commit()
        print("  ✓ landlord_contracts 表迁移完成")
        return True
        
    except Exception as e:
        print(f"  ✗ landlord_contracts 表迁移失败：{str(e)}")
        db.session.rollback()
        return False


def main():
    """主迁移函数"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("金额字段精度修复迁移脚本")
        print("=" * 80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        print("\n⚠️  重要提示：")
        print("  1. 此脚本将修改数据库表结构")
        print("  2. 建议在执行前备份数据库文件")
        print("  3. 迁移过程中会保留所有现有数据")
        print("  4. 迁移完成后请重启应用服务器")
        print()
        
        # 执行迁移
        success = True
        success = migrate_contracts_table() and success
        success = migrate_payments_table() and success
        success = migrate_deposit_refunds_table() and success
        success = migrate_houses_table() and success
        success = migrate_rooms_table() and success
        success = migrate_landlord_contracts_table() and success
        
        print("\n" + "=" * 80)
        if success:
            print("✓ 所有表迁移完成！")
            print("=" * 80)
            print("\n后续步骤：")
            print("  1. 重启应用服务器")
            print("  2. 验证金额计算是否正常")
            print("  3. 检查前端显示是否正确")
        else:
            print("✗ 部分表迁移失败，请检查错误信息")
            print("=" * 80)
        
        print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
