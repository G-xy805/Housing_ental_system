"""
数据库架构更新脚本

用于添加 landlord_id 列到 houses 表
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from sqlalchemy import text


def update_schema():
    """更新数据库架构"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("开始更新数据库架构...")
        print("=" * 60)
        
        try:
            # 1. 检查 houses 表是否有 landlord_id 列
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM pragma_table_info('houses') 
                WHERE name='landlord_id'
            """)).scalar()
            
            if result == 0:
                print("✓ 添加 landlord_id 列到 houses 表...")
                db.session.execute(text("""
                    ALTER TABLE houses 
                    ADD COLUMN landlord_id INTEGER
                """))
                db.session.commit()
                print("✓ houses.landlord_id 列添加成功")
            else:
                print("✓ houses.landlord_id 列已存在")
            
            # 2. 检查 landlords 表是否存在
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table' AND name='landlords'
            """)).scalar()
            
            if result == 0:
                print("✓ 创建 landlords 表...")
                db.session.execute(text("""
                    CREATE TABLE landlords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(50) NOT NULL,
                        id_card VARCHAR(18) NOT NULL,
                        id_card_hash VARCHAR(64),
                        phone VARCHAR(20) NOT NULL,
                        bank_card VARCHAR(30),
                        bank_name VARCHAR(100),
                        property_cert_no VARCHAR(50),
                        address VARCHAR(255),
                        status VARCHAR(20) DEFAULT 'active',
                        remark TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                """))
                db.session.commit()
                print("✓ landlords 表创建成功")
            else:
                print("✓ landlords 表已存在")
            
            # 3. 检查 landlord_contracts 表是否存在
            result = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table' AND name='landlord_contracts'
            """)).scalar()
            
            if result == 0:
                print("✓ 创建 landlord_contracts 表...")
                db.session.execute(text("""
                    CREATE TABLE landlord_contracts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_no VARCHAR(50) NOT NULL UNIQUE,
                        title VARCHAR(100) NOT NULL,
                        description TEXT,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        contract_amount FLOAT NOT NULL,
                        service_fee_rate FLOAT NOT NULL,
                        minimum_fee FLOAT,
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
                db.session.commit()
                print("✓ landlord_contracts 表创建成功")
            else:
                print("✓ landlord_contracts 表已存在")
            
            print("=" * 60)
            print("✓ 数据库架构更新完成！")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"✗ 数据库架构更新失败：{str(e)}")
            db.session.rollback()
            return False


if __name__ == '__main__':
    success = update_schema()
    sys.exit(0 if success else 1)
