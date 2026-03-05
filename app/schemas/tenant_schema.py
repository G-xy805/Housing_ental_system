"""
租客 Schema

提供租客模型的序列化和验证
"""
from typing import Optional
from marshmallow import fields, validates, validates_schema, ValidationError
from .base import BaseSchema, TimestampMixin


class TenantSchema(BaseSchema, TimestampMixin):
    """
    租客序列化 Schema
    
    自动过滤敏感字段（身份证号）
    """
    
    # 敏感字段
    SENSITIVE_FIELDS = {'id_card_encrypted'}
    
    # 基本字段
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    phone = fields.Str(required=True, validate=lambda x: len(x) >= 11)
    email = fields.Email(allow_none=True)
    
    # 敏感字段（仅用于反序列化）
    id_card = fields.Str(load_only=True, allow_none=True)
    
    # 加密字段（数据库存储，不输出）
    id_card_encrypted = fields.Str(load_only=True, allow_none=True)
    
    # 紧急联系人
    emergency_contact = fields.Str(allow_none=True)
    emergency_phone = fields.Str(allow_none=True)
    emergency_relation = fields.Str(allow_none=True)
    
    # 工作信息
    company = fields.Str(allow_none=True)
    occupation = fields.Str(allow_none=True)
    
    # 状态
    status = fields.Str(validate=lambda x: x in ['active', 'expired', 'blacklisted'])
    
    # 备注
    remark = fields.Str(allow_none=True)
    
    # 个人照片
    photo = fields.Str(allow_none=True)
    
    # 计算字段
    current_houses_count = fields.Int(dump_only=True)
    
    class Meta:
        fields = [
            'id', 'name', 'phone', 'email',
            'id_card', 'id_card_encrypted',
            'emergency_contact', 'emergency_phone', 'emergency_relation',
            'company', 'occupation',
            'status', 'remark', 'photo',
            'current_houses_count',
            'created_at', 'updated_at', 'is_active'
        ]
    
    @validates('phone')
    def validate_phone(self, value: str):
        """验证手机号"""
        if len(value) != 11:
            raise ValidationError('手机号必须是 11 位')
    
    @validates('emergency_phone')
    def validate_emergency_phone(self, value: Optional[str]):
        """验证紧急联系人电话"""
        if value and len(value) != 11:
            raise ValidationError('紧急联系人电话必须是 11 位')
    
    @validates('status')
    def validate_status(self, value: str):
        """验证状态"""
        if value not in ['active', 'expired', 'blacklisted']:
            raise ValidationError('状态必须是 active、expired 或 blacklisted')


class TenantCreateSchema(BaseSchema):
    """
    租客创建 Schema
    
    用于创建租客时的数据验证
    """
    
    name = fields.Str(required=True, validate=lambda x: len(x) >= 2)
    phone = fields.Str(required=True, validate=lambda x: len(x) == 11)
    email = fields.Email(allow_none=True)
    id_card = fields.Str(load_only=True, allow_none=True, validate=lambda x: len(x) == 18 if x else True)
    
    emergency_contact = fields.Str(allow_none=True)
    emergency_phone = fields.Str(allow_none=True, validate=lambda x: len(x) == 11 if x else True)
    emergency_relation = fields.Str(allow_none=True)
    
    company = fields.Str(allow_none=True)
    occupation = fields.Str(allow_none=True)
    
    status = fields.Str(validate=lambda x: x in ['active', 'expired', 'blacklisted'])
    remark = fields.Str(allow_none=True)
    photo = fields.Str(allow_none=True)
    
    @validates_schema
    def validate_unique_fields(self, data, **kwargs):
        """验证唯一字段"""
        from app.models import Tenant
        
        # 检查手机号是否已存在
        phone = data.get('phone')
        if phone and Tenant.query.filter_by(phone=phone).first():
            raise ValidationError('手机号已存在', field_name='phone')


class TenantUpdateSchema(BaseSchema):
    """
    租客更新 Schema
    
    用于更新租客信息时的数据验证
    """
    
    name = fields.Str(allow_none=True, validate=lambda x: len(x) >= 2)
    phone = fields.Str(allow_none=True, validate=lambda x: len(x) == 11 if x else True)
    email = fields.Email(allow_none=True)
    id_card = fields.Str(load_only=True, allow_none=True, validate=lambda x: len(x) == 18 if x else True)
    
    emergency_contact = fields.Str(allow_none=True)
    emergency_phone = fields.Str(allow_none=True, validate=lambda x: len(x) == 11 if x else True)
    emergency_relation = fields.Str(allow_none=True)
    
    company = fields.Str(allow_none=True)
    occupation = fields.Str(allow_none=True)
    
    status = fields.Str(validate=lambda x: x in ['active', 'expired', 'blacklisted'])
    remark = fields.Str(allow_none=True)
    photo = fields.Str(allow_none=True)
    
    @validates_schema
    def validate_unique_fields(self, data, **kwargs):
        """验证唯一字段（排除当前租客）"""
        from app.models import Tenant
        
        current_id = kwargs.get('instance') and kwargs['instance'].id
        if not current_id:
            return
        
        # 检查手机号是否已被其他租客使用
        phone = data.get('phone')
        if phone:
            existing = Tenant.query.filter_by(phone=phone).first()
            if existing and existing.id != current_id:
                raise ValidationError('手机号已被其他租客使用', field_name='phone')
