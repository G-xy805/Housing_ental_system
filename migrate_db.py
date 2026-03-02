from app import create_app, db

app = create_app()
with app.app_context():
    print("清理旧字段...")
    
    # 创建临时表并迁移数据
    # 1. 重命名原表
    db.session.execute(db.text("ALTER TABLE landlords RENAME TO landlords_old"))
    db.session.execute(db.text("ALTER TABLE tenants RENAME TO tenants_old"))
    print("✓ 重命名原表")
    
    # 2. 创建新表
    db.create_all()
    print("✓ 创建新表")
    
    # 3. 迁移数据（从旧表到新表）
    # 迁移 landlords 数据
    old_landlords = db.session.execute(db.text("SELECT * FROM landlords_old")).fetchall()
    for row in old_landlords:
        # 获取明文数据
        id_card = row['id_card']
        bank_card = row['bank_card']
        
        # 加密
        from app.utils.encryption import encrypt_sensitive_data
        encrypted_id_card = encrypt_sensitive_data(id_card)
        encrypted_bank_card = encrypt_sensitive_data(bank_card) if bank_card else None
        
        # 插入新表
        db.session.execute(
            db.text("""
                INSERT INTO landlords 
                (name, id_card_encrypted, phone, bank_card_encrypted, bank_name, 
                 property_cert_no, address, status, remark, created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """),
            (row['name'], encrypted_id_card, row['phone'], encrypted_bank_card, 
             row['bank_name'], row['property_cert_no'], row['address'], 
             row['status'], row['remark'], row['created_at'], row['updated_at'], row['is_active'])
        )
    
    print("✓ 迁移 landlords 数据")
    
    # 迁移 tenants 数据
    old_tenants = db.session.execute(db.text("SELECT * FROM tenants_old")).fetchall()
    for row in old_tenants:
        id_card = row['id_card']
        encrypted_id_card = encrypt_sensitive_data(id_card)
        
        db.session.execute(
            db.text("""
                INSERT INTO tenants 
                (name, id_card_encrypted, phone, email, emergency_contact, 
                 emergency_phone, emergency_relation, company, occupation, 
                 status, remark, created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """),
            (row['name'], encrypted_id_card, row['phone'], row['email'], 
             row['emergency_contact'], row['emergency_phone'], row['emergency_relation'],
             row['company'], row['occupation'], row['status'], row['remark'], 
             row['created_at'], row['updated_at'], row['is_active'])
        )
    
    print("✓ 迁移 tenants 数据")
    
    db.session.commit()
    
    # 4. 删除旧表
    db.session.execute(db.text("DROP TABLE landlords_old"))
    db.session.execute(db.text("DROP TABLE tenants_old"))
    print("✓ 删除旧表")
    
    print("\n数据库迁移完成！")
