"""
房东模型
"""
from .base import db, BaseModel
from app.utils.aes_encryption import (
    encrypt_sensitive_data, 
    decrypt_sensitive_data, 
    mask_sensitive_data,
    HybridEncryptor
)
from app.utils.sensitive_data_audit import SensitiveDataAuditLogger


class Landlord(BaseModel):
    """
    房东模型
    
    用于管理房东信息，包括房产证信息、联系方式等
    房东可以与多个房源关联
    
    安全特性：
    - 身份证号使用 AES-256-GCM 加密存储
    - 银行卡号使用 AES-256-GCM 加密存储
    - 支持向后兼容旧的 Fernet 加密数据
    - 所有加密操作记录审计日志
    - 所有敏感数据访问记录审计日志
    """
    
    __tablename__ = 'landlords'
    
    # 基本信息
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    
    # 身份证号（加密存储）
    id_card_encrypted = db.Column(db.Text, comment='身份证号（AES-256-GCM 加密存储）')
    
    # 联系方式
    phone = db.Column(db.String(20), nullable=False, comment='联系电话')
    
    # 银行卡信息（用于打租金，加密存储）
    bank_card_encrypted = db.Column(db.Text, comment='银行卡号（AES-256-GCM 加密存储）')
    bank_name = db.Column(db.String(100), comment='开户行名称')
    
    # 房产信息
    property_cert_no = db.Column(db.String(50), comment='房产证编号')
    address = db.Column(db.String(255), comment='房产地址')
    
    # 房东状态：active-正常，inactive-停用，blacklisted-黑名单
    status = db.Column(db.String(20), default='active', comment='房东状态')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 个人照片
    photo = db.Column(db.String(255), comment='个人照片 URL')
    
    # 索引
    __table_args__ = (
        db.Index('idx_landlords_phone', 'phone'),
        db.Index('idx_landlords_status', 'status'),
    )
    
    # 关系 - 房东拥有的房源
    houses = db.relationship('House', back_populates='landlord_rel', lazy='dynamic')
    
    def set_id_card(self, id_card_number, user_id=None, skip_audit=False):
        """
        设置身份证号并使用 AES-256-GCM 加密存储
        
        Args:
            id_card_number: 身份证号明文
            user_id: 操作用户 ID（用于审计日志）
            skip_audit: 是否跳过审计日志（避免重复记录）
        """
        old_value = None
        if self.id_card_encrypted:
            try:
                old_value = decrypt_sensitive_data(
                    encrypted_data=self.id_card_encrypted,
                    field_name='id_card',
                    model_name='Landlord',
                    record_id=self.id if self.id else 0,
                    user_id=user_id,
                    skip_audit=True
                )
            except:
                pass
        
        self.id_card_encrypted = encrypt_sensitive_data(
            data=id_card_number,
            field_name='id_card',
            model_name='Landlord',
            record_id=self.id if self.id else 0,
            user_id=user_id,
            skip_audit=True
        )
        
        if not skip_audit:
            SensitiveDataAuditLogger.log_modify(
                model_name='Landlord',
                record_id=self.id if self.id else 0,
                field_name='id_card',
                field_display_name='身份证号',
                old_value=old_value,
                new_value=id_card_number,
                user_id=user_id,
                remark='设置身份证号'
            )
    
    def get_id_card(self, user_id=None, skip_audit=False):
        """
        获取解密后的身份证号
        
        Args:
            user_id: 操作用户 ID（用于审计日志）
            skip_audit: 是否跳过审计日志（避免重复记录）
            
        Returns:
            str: 解密后的身份证号
        """
        decrypted = decrypt_sensitive_data(
            encrypted_data=self.id_card_encrypted,
            field_name='id_card',
            model_name='Landlord',
            record_id=self.id if self.id else 0,
            user_id=user_id,
            skip_audit=True
        )
        
        if decrypted and not skip_audit:
            SensitiveDataAuditLogger.log_view(
                model_name='Landlord',
                record_id=self.id if self.id else 0,
                field_name='id_card',
                field_display_name='身份证号',
                user_id=user_id,
                remark='查看身份证号'
            )
        
        return decrypted
    
    def verify_id_card(self, id_card_number, user_id=None, skip_audit=False):
        """
        验证身份证号是否匹配
        
        Args:
            id_card_number: 待验证的身份证号
            user_id: 操作用户 ID（用于审计日志）
            skip_audit: 是否跳过审计日志（避免重复记录）
            
        Returns:
            bool: 是否匹配
        """
        decrypted = self.get_id_card(user_id=user_id, skip_audit=skip_audit)
        return decrypted == id_card_number
    
    def set_bank_card(self, bank_card_number, user_id=None, skip_audit=False):
        """
        设置银行卡号并使用 AES-256-GCM 加密存储
        
        Args:
            bank_card_number: 银行卡号明文
            user_id: 操作用户 ID（用于审计日志）
            skip_audit: 是否跳过审计日志（避免重复记录）
        """
        old_value = None
        if self.bank_card_encrypted:
            try:
                old_value = decrypt_sensitive_data(
                    encrypted_data=self.bank_card_encrypted,
                    field_name='bank_card',
                    model_name='Landlord',
                    record_id=self.id if self.id else 0,
                    user_id=user_id,
                    skip_audit=True
                )
            except:
                pass
        
        self.bank_card_encrypted = encrypt_sensitive_data(
            data=bank_card_number,
            field_name='bank_card',
            model_name='Landlord',
            record_id=self.id if self.id else 0,
            user_id=user_id,
            skip_audit=True
        )
        
        if not skip_audit:
            SensitiveDataAuditLogger.log_modify(
                model_name='Landlord',
                record_id=self.id if self.id else 0,
                field_name='bank_card',
                field_display_name='银行卡号',
                old_value=old_value,
                new_value=bank_card_number,
                user_id=user_id,
                remark='设置银行卡号'
            )
    
    def get_bank_card(self, user_id=None, skip_audit=False):
        """
        获取解密后的银行卡号
        
        Args:
            user_id: 操作用户 ID（用于审计日志）
            skip_audit: 是否跳过审计日志（避免重复记录）
            
        Returns:
            str: 解密后的银行卡号
        """
        decrypted = decrypt_sensitive_data(
            encrypted_data=self.bank_card_encrypted,
            field_name='bank_card',
            model_name='Landlord',
            record_id=self.id if self.id else 0,
            user_id=user_id,
            skip_audit=True
        )
        
        if decrypted and not skip_audit:
            SensitiveDataAuditLogger.log_view(
                model_name='Landlord',
                record_id=self.id if self.id else 0,
                field_name='bank_card',
                field_display_name='银行卡号',
                user_id=user_id,
                remark='查看银行卡号'
            )
        
        return decrypted
    
    def mask_bank_card(self, user_id=None, skip_audit=False):
        """
        获取脱敏的银行卡号
        
        Args:
            user_id: 操作用户 ID（用于审计日志）
            skip_audit: 是否跳过审计日志（避免重复记录）
            
        Returns:
            str: 脱敏后的银行卡号（如：**** **** **** 1234）
        """
        decrypted = self.get_bank_card(user_id=user_id, skip_audit=True)
        return mask_sensitive_data(decrypted) if decrypted else None
    
    def needs_re_encryption(self):
        """
        检查是否需要重新加密（从 Fernet 迁移到 AES-256-GCM）
        
        Returns:
            bool: 是否需要重新加密
        """
        # 检查身份证号
        if self.id_card_encrypted and not HybridEncryptor.is_encrypted_with_aes(self.id_card_encrypted):
            return True
        
        # 检查银行卡号
        if self.bank_card_encrypted and not HybridEncryptor.is_encrypted_with_aes(self.bank_card_encrypted):
            return True
        
        return False
    
    def re_encrypt_data(self, user_id=None):
        """
        重新加密数据（从 Fernet 迁移到 AES-256-GCM）
        
        Args:
            user_id: 操作用户 ID（用于审计日志）
        """
        # 重新加密身份证号
        if self.id_card_encrypted and not HybridEncryptor.is_encrypted_with_aes(self.id_card_encrypted):
            decrypted = decrypt_sensitive_data(
                encrypted_data=self.id_card_encrypted,
                field_name='id_card',
                model_name='Landlord',
                record_id=self.id if self.id else 0,
                user_id=user_id
            )
            if decrypted:
                self.set_id_card(decrypted, user_id=user_id)
        
        # 重新加密银行卡号
        if self.bank_card_encrypted and not HybridEncryptor.is_encrypted_with_aes(self.bank_card_encrypted):
            decrypted = decrypt_sensitive_data(
                encrypted_data=self.bank_card_encrypted,
                field_name='bank_card',
                model_name='Landlord',
                record_id=self.id if self.id else 0,
                user_id=user_id
            )
            if decrypted:
                self.set_bank_card(decrypted, user_id=user_id)
    
    def to_dict(self, include_details=False):
        """
        转换为字典
        
        Args:
            include_details: 是否包含详细信息（敏感字段）
            
        Returns:
            dict: 房东信息字典
        """
        data = super().to_dict()
        
        # 添加脱敏的银行卡号
        if self.bank_card_encrypted:
            data['bank_card'] = self.mask_bank_card()
        
        # 添加脱敏的身份证号（用于前端显示，跳过审计日志）
        if self.id_card_encrypted:
            id_card = self.get_id_card(skip_audit=True)
            if id_card and len(id_card) == 18:
                # 脱敏显示：110101********1234
                data['id_card'] = id_card[:6] + '********' + id_card[14:]
        
        # 自动过滤敏感字段
        data.pop('id_card_encrypted', None)
        data.pop('bank_card_encrypted', None)
        
        if not include_details:
            # 默认响应不包含敏感信息
            data.pop('bank_name', None)
            data.pop('property_cert_no', None)
        
        return data
    
    def __repr__(self):
        return f'<Landlord {self.name}>'
