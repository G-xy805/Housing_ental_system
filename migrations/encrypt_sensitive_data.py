"""
敏感数据加密迁移脚本
将明文存储的身份证号和银行卡号加密存储

使用方法：
    python -m migrations.encrypt_sensitive_data
"""
import os
import sys
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.landlord import Landlord
from app.models.tenant import Tenant
from app.utils.encryption import encrypt_sensitive_data, decrypt_sensitive_data


def encrypt_existing_data():
    """
    加密已存在的敏感数据
    """
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("开始加密敏感数据...")
        print("=" * 80)
        
        # 加密房东的身份证号
        print("\n[1/2] 加密房东身份证号...")
        landlords = Landlord.query.all()
        encrypted_landlords = 0
        
        for landlord in landlords:
            try:
                # 检查是否已经加密（字段名检查）
                if hasattr(landlord, 'id_card') and not hasattr(landlord, 'id_card_encrypted'):
                    # 旧字段名是 id_card，需要加密并迁移
                    old_id_card = getattr(landlord, 'id_card', None)
                    if old_id_card:
                        encrypted_id_card = encrypt_sensitive_data(old_id_card)
                        if encrypted_id_card:
                            # 设置新字段
                            setattr(landlord, 'id_card_encrypted', encrypted_id_card)
                            # 清除旧字段
                            setattr(landlord, 'id_card', None)
                            setattr(landlord, 'id_card_hash', None)
                            encrypted_landlords += 1
            except Exception as e:
                print(f"  ⚠️  处理房东 ID {landlord.id} 时出错: {str(e)}")
        
        db.session.commit()
        print(f"  ✓ 已加密 {encrypted_landlords} 个房东的身份证号")
        
        # 加密房东的银行卡号
        encrypted_bank_cards = 0
        for landlord in landlords:
            try:
                if hasattr(landlord, 'bank_card') and not hasattr(landlord, 'bank_card_encrypted'):
                    old_bank_card = getattr(landlord, 'bank_card', None)
                    if old_bank_card:
                        encrypted_bank_card = encrypt_sensitive_data(old_bank_card)
                        if encrypted_bank_card:
                            setattr(landlord, 'bank_card_encrypted', encrypted_bank_card)
                            setattr(landlord, 'bank_card', None)
                            encrypted_bank_cards += 1
            except Exception as e:
                print(f"  ⚠️  处理房东 ID {landlord.id} 的银行卡号时出错: {str(e)}")
        
        db.session.commit()
        print(f"  ✓ 已加密 {encrypted_bank_cards} 个房东的银行卡号")
        
        # 加密租客的身份证号
        print("\n[2/2] 加密租客身份证号...")
        tenants = Tenant.query.all()
        encrypted_tenants = 0
        
        for tenant in tenants:
            try:
                if hasattr(tenant, 'id_card') and not hasattr(tenant, 'id_card_encrypted'):
                    old_id_card = getattr(tenant, 'id_card', None)
                    if old_id_card:
                        encrypted_id_card = encrypt_sensitive_data(old_id_card)
                        if encrypted_id_card:
                            setattr(tenant, 'id_card_encrypted', encrypted_id_card)
                            setattr(tenant, 'id_card', None)
                            setattr(tenant, 'id_card_hash', None)
                            encrypted_tenants += 1
            except Exception as e:
                print(f"  ⚠️  处理