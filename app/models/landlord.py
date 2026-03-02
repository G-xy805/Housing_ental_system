"""
房东模型
"""
from .base import db, BaseModel
from app.utils.encryption import encrypt_sensitive_data, decrypt_sensitive_data, mask_sensitive_data


class Landlord(BaseModel):
    """
    房东模型
    
    用于管理房东信息，包括房产证信息、联系方式等
    房东可以与多个房源关联
    """
    
    __tablename__ = 'landlords'
    
    # 基本信息
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    
    # 身份证号（加密存储）
    id_card_encrypted = db.Column(db.Text, comment='身份证号（加密存储）')
    
    # 联系方式
    phone = db.Column(db.String(20), nullable=False, comment='联系电话')
    
    # 银行卡信息（用于打租金，加密存储）
    bank_card_encrypted = db.Column(db.Text, comment='银行卡号（加密存储）')
    bank_name = db.Column(db.String(100), comment='开户行名称')
    
    # 房产信息
    property_cert_no = db.Column(db.String(50), comment='房产证编号')
    address = db.Column(db.String(255), comment='房产地址')
    
    # 房东状态：active-正常，inactive-停用，blacklisted-黑名单
    status = db.Column(db.String(20), default='active', comment='房东状态')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 索引
    __table_args__ = (
        db.Index('idx_landlords_phone', 'phone'),
        db.Index('idx_landlords_status', 'status'),
    )
    
    # 关系 - 房东拥有的房源
    houses = db.relationship('House', back_populates='landlord_rel', lazy='dynamic')
    
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
    
    def set_bank_card(self, bank_card_number):
        """设置银行卡号并加密存储"""
        self.bank_card_encrypted = encrypt_sensitive_data(bank_card_number)
    
    def get_bank_card(self):
        """获取解密后的银行卡号"""
        return decrypt_sensitive_data(self.bank_card_encrypted)
    
    def mask_bank_card(self):
        """获取脱敏的银行卡号"""
        decrypted = self.get_bank_card()
        return mask_sensitive_data(decrypted) if decrypted else None
    
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
