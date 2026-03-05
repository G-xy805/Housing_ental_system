"""
租客模型
"""
from datetime import datetime
from .base import db, BaseModel
from app.utils.aes_encryption import (
    encrypt_sensitive_data, 
    decrypt_sensitive_data,
    HybridEncryptor
)
from app.utils.sensitive_data_audit import SensitiveDataAuditLogger


class Tenant(BaseModel):
    """
    租客模型
    
    用于管理租客信息，支持同一房源多个租客（合租场景）
    租客可以与多个合同关联
    
    安全特性：
    - 身份证号使用 AES-256-GCM 加密存储
    - 支持向后兼容旧的 Fernet 加密数据
    - 所有加密操作记录审计日志
    - 所有敏感数据访问记录审计日志
    """
    
    __tablename__ = 'tenants'
    
    # 基本信息
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    
    # 身份证号（加密存储）
    id_card_encrypted = db.Column(db.Text, comment='身份证号（AES-256-GCM 加密存储）')
    
    # 联系方式
    phone = db.Column(db.String(20), nullable=False, comment='联系电话')
    email = db.Column(db.String(120), comment='电子邮箱')
    
    # 紧急联系人
    emergency_contact = db.Column(db.String(50), comment='紧急联系人姓名')
    emergency_phone = db.Column(db.String(20), comment='紧急联系人电话')
    emergency_relation = db.Column(db.String(20), comment='与紧急联系人关系')
    
    # 工作信息
    company = db.Column(db.String(100), comment='工作单位')
    occupation = db.Column(db.String(50), comment='职业')
    
    # 租客状态：pending-待租/潜在租客，active-在租，expired-已退租，blacklisted-黑名单
    status = db.Column(db.String(20), default='pending', comment='租客状态')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 个人照片
    photo = db.Column(db.String(255), comment='个人照片 URL')
    
    # 索引
    __table_args__ = (
        db.Index('idx_tenants_phone', 'phone'),
        db.Index('idx_tenants_status', 'status'),
    )
    
    # 关系 - 通过合同关联房源
    contracts = db.relationship('Contract', back_populates='tenant_rel', lazy='dynamic')
    
    def set_id_card(self, id_card_number, user_id=None):
        """
        设置身份证号并使用 AES-256-GCM 加密存储
        
        Args:
            id_card_number: 身份证号明文
            user_id: 操作用户 ID（用于审计日志）
        """
        # 获取旧值用于审计
        old_value = None
        if self.id_card_encrypted:
            try:
                old_value = decrypt_sensitive_data(
                    encrypted_data=self.id_card_encrypted,
                    field_name='id_card',
                    model_name='Tenant',
                    record_id=self.id if self.id else 0,
                    user_id=user_id
                )
            except:
                pass
        
        self.id_card_encrypted = encrypt_sensitive_data(
            data=id_card_number,
            field_name='id_card',
            model_name='Tenant',
            record_id=self.id if self.id else 0,
            user_id=user_id
        )
        
        # 记录敏感数据修改审计日志
        SensitiveDataAuditLogger.log_modify(
            model_name='Tenant',
            record_id=self.id if self.id else 0,
            field_name='id_card',
            field_display_name='身份证号',
            old_value=old_value,
            new_value=id_card_number,
            user_id=user_id,
            remark='设置身份证号'
        )
    
    def get_id_card(self, user_id=None):
        """
        获取解密后的身份证号
        
        Args:
            user_id: 操作用户 ID（用于审计日志）
            
        Returns:
            str: 解密后的身份证号
        """
        decrypted = decrypt_sensitive_data(
            encrypted_data=self.id_card_encrypted,
            field_name='id_card',
            model_name='Tenant',
            record_id=self.id if self.id else 0,
            user_id=user_id
        )
        
        # 记录敏感数据查看审计日志
        if decrypted:
            SensitiveDataAuditLogger.log_view(
                model_name='Tenant',
                record_id=self.id if self.id else 0,
                field_name='id_card',
                field_display_name='身份证号',
                user_id=user_id,
                remark='查看身份证号'
            )
        
        return decrypted
    
    def verify_id_card(self, id_card_number, user_id=None):
        """
        验证身份证号是否匹配
        
        Args:
            id_card_number: 待验证的身份证号
            user_id: 操作用户 ID（用于审计日志）
            
        Returns:
            bool: 是否匹配
        """
        decrypted = self.get_id_card(user_id=user_id)
        return decrypted == id_card_number
    
    def needs_re_encryption(self):
        """
        检查是否需要重新加密（从 Fernet 迁移到 AES-256-GCM）
        
        Returns:
            bool: 是否需要重新加密
        """
        if self.id_card_encrypted and not HybridEncryptor.is_encrypted_with_aes(self.id_card_encrypted):
            return True
        return False
    
    def re_encrypt_data(self, user_id=None):
        """
        重新加密数据（从 Fernet 迁移到 AES-256-GCM）
        
        Args:
            user_id: 操作用户 ID（用于审计日志）
        """
        if self.id_card_encrypted and not HybridEncryptor.is_encrypted_with_aes(self.id_card_encrypted):
            decrypted = decrypt_sensitive_data(
                encrypted_data=self.id_card_encrypted,
                field_name='id_card',
                model_name='Tenant',
                record_id=self.id if self.id else 0,
                user_id=user_id
            )
            if decrypted:
                self.set_id_card(decrypted, user_id=user_id)
    
    def get_active_contracts(self):
        """获取当前有效的合同"""
        from .contract import Contract
        return self.contracts.filter(
            Contract.status.in_(['active', 'draft']),
            Contract.end_date >= datetime.now().date()
        ).all()
    
    def get_current_houses(self):
        """获取当前租住的房源"""
        active_contracts = self.get_active_contracts()
        return [contract.house for contract in active_contracts if contract.house]
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        # 移除敏感字段
        data.pop('id_card_encrypted', None)
        return data
    
    def __repr__(self):
        return f'<Tenant {self.name}>'
