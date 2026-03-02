"""
租客模型
"""
from datetime import datetime
from .base import db, BaseModel
from app.utils.encryption import encrypt_sensitive_data, decrypt_sensitive_data


class Tenant(BaseModel):
    """
    租客模型
    
    用于管理租客信息，支持同一房源多个租客（合租场景）
    租客可以与多个合同关联
    """
    
    __tablename__ = 'tenants'
    
    # 基本信息
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    
    # 身份证号（加密存储）
    id_card_encrypted = db.Column(db.Text, comment='身份证号（加密存储）')
    
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
    
    # 租客状态：active-在租，expired-已退租，blacklisted-黑名单
    status = db.Column(db.String(20), default='active', comment='租客状态')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 索引
    __table_args__ = (
        db.Index('idx_tenants_phone', 'phone'),
        db.Index('idx_tenants_status', 'status'),
    )
    
    # 关系 - 通过合同关联房源
    contracts = db.relationship('Contract', back_populates='tenant_rel', lazy='dynamic')
    
    def set_id_card(self, id_card_number):
        """设置身份证号并加密存储"""
        self.id_card_encrypted = encrypt_sensitive_data(id_card_number)
    
    def get_id_card(self):
        """获取解密后的身份证号"""
        return decrypt_sensitive_data(self.id_card_encrypted)
    
    def verify_id_card(self, id_card_number):
        """验证身份证号是否匹配"""
        decrypted = self.get_id_card()
        return decrypted == id_card_number
    
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
