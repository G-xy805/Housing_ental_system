"""
房东 Schema

提供房东模型的序列化和验证
"""
from typing import Optional
from marshmallow import fields, validates, validates_schema, ValidationError, post_dump
from .base import BaseSchema, TimestampMixin


class LandlordSchema(BaseSchema, TimestampMixin):
    """
    房东序列化 Schema
    
    自动过滤敏感字段（身份证号、银行卡号）
    """
    
    # 敏感字段
    SENSITIVE_FIELDS = {'id_card_encrypted', 'bank_card_encrypted'}
    
    # 内部接口专用字段
    INTERNAL_ONLY_FIELDS = {'bank_name', 'property_cert_no'}
    
    # 基本字段
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    phone = fields.Str(required=True, validate=lambda x: len(x) >= 11)
    
    # 敏感字段（仅用于反序列化）
    id_card = fields.Str(load_only=True, allow_none=True)
    bank_card = fields.Str(load_only=True, allow_none=True)
    
    # 加密字段（数据库存储，不输出）
    id_card_encrypted = fields.Str(load_only=True, allow_none=True)
    bank_card_encrypted = fields.Str(load_only=True, allow_none=True)
    
    # 银行信息
    bank_name = fields.Str(allow_none=True)
    
    # 房产信息
    property_cert_no = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    
    # 状态
    status = fields.Str(validate=lambda x: x in ['active', 'inactive', 'blacklisted'])
    
    # 备注
    remark = fields.Str(allow_none=True)
    
    # 个人照片
    photo = fields.Str(allow_none=True)
    
    # 计算字段
    bank_card_masked = fields.Str(dump_only=True)
    
    class Meta:
        fields = [
            'id', 'name', 'phone',
            'id_card', 'bank_card',
            'id_card_encrypted', 'bank_card_encrypted',
            'bank_name', 'property_cert_no', 'address',
            'status', 'remark', 'photo',
            'bank_card_masked',
            'created_at', 'updated_at', 'is_active'
        ]
    
    @validates('phone')
    def validate_phone(self, value: str):
        """验证手机号"""
        if len(value) != 11:
            raise ValidationError('手机号必须是 11 位')
    
    @validates('status')
    def validate_status(self, value: str):
        """验证状态"""
        if value not in ['active', 'inactive', 'blacklisted']:
            raise ValidationError('状态必须是 active、inactive 或 blacklisted')
    
    @post_dump
    def add_masked_fields(self, data, **kwargs):
        """添加脱敏字段"""
        # 添加脱敏的银行卡号
        from app.utils.aes_encryption import mask_sensitive_data
        
        if 'bank_card_encrypted' in data:
            # 如果有加密的银行卡号，添加脱敏版本
            try:
                from app.utils.aes_encryption import decrypt_sensitive_data
                decrypted = decrypt_sensitive_data(
                    encrypted_data=data.get('bank_card_encrypted'),
                    field_name='bank_card',
                    model_name='Landlord',
                    record_id=data.get('id', 0)
                )
                data['bank_card_masked'] = mask_sensitive_data(decrypted) if decrypted else None
            except:
                data['bank_card_masked'] = None
        
        return data


class LandlordCreateSchema(BaseSchema):
    """
    房东创建 Schema
    
    用于创建房东时的数据验证
    """
    
    name = fields.Str(required=True, validate=lambda x: len(x) >= 2)
    phone = fields.Str(required=True, validate=lambda x: len(x) == 11)
    id_card = fields.Str(load_only=True, allow_none=True, validate=lambda x: len(x) == 18 if x else True)
    bank_card = fields.Str(load_only=True, allow_none=True, validate=lambda x: len(x) >= 16 if x else True)
    bank_name = fields.Str(allow_none=True)
    property_cert_no = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    status = fields.Str(validate=lambda x: x in ['active', 'inactive', 'blacklisted'])
    remark = fields.Str(allow_none=True)
    photo = fields.Str(allow_none=True)
    
    @validates_schema
    def validate_unique_fields(self, data, **kwargs):
        """验证唯一字段"""
        from app.models import Landlord
        
        # 检查手机号是否已存在
        phone = data.get('phone')
        if phone and Landlord.query.filter_by(phone=phone).first():
            raise ValidationError('手机号已存在', field_name='phone')


class LandlordUpdateSchema(BaseSchema):
    """
    房东更新 Schema
    
    用于更新房东信息时的数据验证
    """
    
    name = fields.Str(allow_none=True, validate=lambda x: len(x) >= 2)
    phone = fields.Str(allow_none=True, validate=lambda x: len(x) == 11 if x else True)
    id_card = fields.Str(load_only=True, allow_none=True, validate=lambda x: len(x) == 18 if x else True)
    bank_card = fields.Str(load_only=True, allow_none=True, validate=lambda x: len(x) >= 16 if x else True)
    bank_name = fields.Str(allow_none=True)
    property_cert_no = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    status = fields.Str(validate=lambda x: x in ['active', 'inactive', 'blacklisted'])
    remark = fields.Str(allow_none=True)
    photo = fields.Str(allow_none=True)
    
    @validates_schema
    def validate_unique_fields(self, data, **kwargs):
        """验证唯一字段（排除当前房东）"""
        from app.models import Landlord
        
        current_id = kwargs.get('instance') and kwargs['instance'].id
        if not current_id:
            return
        
        # 检查手机号是否已被其他房东使用
        phone = data.get('phone')
        if phone:
            existing = Landlord.query.filter_by(phone=phone).first()
            if existing and existing.id != current_id:
                raise ValidationError('手机号已被其他房东使用', field_name='phone')
