from app import create_app, db

app = create_app()
with app.app_context():
    print("添加加密字段...")
    
    # 为 landlords 表添加加密字段
    db.session.execute(db.text("ALTER TABLE landlords ADD COLUMN id_card_encrypted TEXT"))
    db.session.execute(db.text("ALTER TABLE landlords ADD COLUMN bank_card_encrypted TEXT"))
    print("✓ landlords 表添加加密字段完成")
    
    # 为 tenants 表添加加密字段
    db.session.execute(db.text("ALTER TABLE tenants ADD COLUMN id_card_encrypted TEXT"))
    db.session.execute(db.text("ALTER TABLE tenants ADD COLUMN bank_card_encrypted TEXT"))
    print("✓ tenants 表添加加密字段完成")
    
    db.session.commit()
    print("\n数据库表结构更新完成！")
