"""
数据库迁移脚本：添加加密字段
"""
from app import create_app, db
from app.models.landlord import Landlord
from app.models.tenant import Tenant


def add_encryption_columns():
    """
    为 landlords 和 tenants 表添加加密字段
    """
    print("=" * 60)
    print("添加加密字段到数据库")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # 为 landlords 表添加加密字段
        print("\n1. 为 landlords 表添加加密字段...")
        
        # 检查字段是否已存在
        result = db.session.execute(db.text(
            "PRAGMA table_info(landlords)"
        )).fetchall()
        
        columns = [row[1] for row in result]
        
        if 'id_card_encrypted' not in columns:
            db.session.execute(db.text(
                "ALTER TABLE landlords ADD COLUMN id_card_encrypted TEXT"
            ))
            print("   ✓ 添加 id_card_encrypted 字段")
        
        if 'bank_card_encrypted' not in columns:
            db.session.execute(db.text(
                "ALTER TABLE landlords ADD COLUMN bank_card_encrypted TEXT"
            ))
            print("   ✓ 添加 bank_card_encrypted 字段")
        
        # 为 tenants 表添加加密字段
        print("\n2. 为 tenants 表添加加密字段...")
        
        result = db.session.execute(db.text(
            "PRAGMA table_info(tenants)"
        )).fetchall()
        
        columns = [row[1] for row in result]
        
        if 'id_card_encrypted' not in columns:
            db.session.execute(db.text(
                "ALTER TABLE tenants ADD COLUMN id_card_encrypted TEXT"
            ))
            print("   ✓ 添加 id_card_encrypted 字段")
        
        if 'bank_card_encrypted' not in columns:
            db.session.execute(db.text(
                "ALTER TABLE tenants ADD COLUMN bank_card_encrypted TEXT"
            ))
            print("   ✓ 添加 bank_card_encrypted 字段")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("数据库表结构更新完成！")
        print("=" * 60)
        
        print("\n下一步操作:")
        print("1. 运行迁移脚本加密现有数据:")
        print("   python migrations/001_encrypt_sensitive_data.py")
        print("\n2. 或直接运行测试:")
        print("   python test_security_fixes.py")


if __name__ == '__main__':
    add_encryption_columns()
