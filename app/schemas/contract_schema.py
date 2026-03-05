"""
合同 Schema

提供合同模型的序列化和验证
"""
from datetime import date
from marshmallow import fields, validates, ValidationError, post_dump
from .base import BaseSchema, TimestampMixin


class ContractSchema(BaseSchema, TimestampMixin):
    """
    合同序列化 Schema
    """
    
    # 基本字段
    id = fields.Int(dump_only=True)
    contract_no = fields.Str(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    
    # 租赁信息
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    rent_amount = fields.Float(required=True)
    deposit_amount = fields.Float(required=True)
    
    # 付款方式
    payment_type = fields.Str(validate=lambda x: x in ['月付', '季付', '半年付', '年付'])
    payment_cycle = fields.Int(validate=lambda x: x > 0)
    
    # 状态
    status = fields.Str(validate=lambda x: x in ['draft', 'active', 'expired', 'terminated'])
    
    # 文件
    contract_file = fields.Str(allow_none=True)
    
    # 备注
    remark = fields.Str(allow_none=True)
    
    # 外键
    house_id = fields.Int(required=True)
    room_id = fields.Int(allow_none=True)
    tenant_id = fields.Int(required=True)
    
    # 嵌套对象
    house = fields.Nested('HouseSchema', dump_only=True)
    room = fields.Nested('RoomSchema', dump_only=True)
    tenant_rel = fields.Nested('TenantSchema', dump_only=True)
    
    # 计算字段
    house_title = fields.Str(dump_only=True)
    house_address = fields.Str(dump_only=True)
    landlord_name = fields.Str(dump_only=True)
    landlord_id = fields.Int(dump_only=True)
    room_number = fields.Str(dump_only=True)
    room_name = fields.Str(dump_only=True)
    tenant_name = fields.Str(dump_only=True)
    tenant_phone = fields.Str(dump_only=True)
    is_expired = fields.Bool(dump_only=True)
    is_expiring_soon = fields.Bool(dump_only=True)
    days_until_expiry = fields.Int(dump_only=True)
    total_rent = fields.Float(dump_only=True)
    
    class Meta:
        fields = [
            'id', 'contract_no', 'title', 'description',
            'start_date', 'end_date', 'rent_amount', 'deposit_amount',
            'payment_type', 'payment_cycle',
            'status', 'contract_file', 'remark',
            'house_id', 'room_id', 'tenant_id',
            'house', 'room', 'tenant_rel',
            'house_title', 'house_address', 'landlord_name', 'landlord_id',
            'room_number', 'room_name',
            'tenant_name', 'tenant_phone',
            'is_expired', 'is_expiring_soon', 'days_until_expiry', 'total_rent',
            'created_at', 'updated_at', 'is_active'
        ]
    
    @validates('start_date')
    def validate_start_date(self, value: date):
        """验证开始日期"""
        if value < date.today():
            raise ValidationError('开始日期不能早于今天')
    
    @validates('end_date')
    def validate_end_date(self, value: date):
        """验证结束日期"""
        if 'start_date' in self.context and value <= self.context['start_date']:
            raise ValidationError('结束日期必须晚于开始日期')
    
    @validates('rent_amount')
    def validate_rent_amount(self, value: float):
        """验证租金"""
        if value <= 0:
            raise ValidationError('租金必须大于 0')
    
    @validates('deposit_amount')
    def validate_deposit_amount(self, value: float):
        """验证押金"""
        if value < 0:
            raise ValidationError('押金不能为负数')


class ContractCreateSchema(BaseSchema):
    """
    合同创建 Schema
    """
    
    title = fields.Str(required=True, validate=lambda x: len(x) >= 2)
    description = fields.Str(allow_none=True)
    
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    rent_amount = fields.Float(required=True, validate=lambda x: x > 0)
    deposit_amount = fields.Float(required=True, validate=lambda x: x >= 0)
    
    payment_type = fields.Str(validate=lambda x: x in ['月付', '季付', '半年付', '年付'])
    payment_cycle = fields.Int(validate=lambda x: x > 0)
    
    status = fields.Str(validate=lambda x: x in ['draft', 'active', 'expired', 'terminated'])
    contract_file = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    
    house_id = fields.Int(required=True)
    room_id = fields.Int(allow_none=True)
    tenant_id = fields.Int(required=True)
    
    @validates('house_id')
    def validate_house_id(self, value: int):
        """验证房源 ID"""
        from app.models import House
        if not House.query.get(value):
            raise ValidationError('房源不存在')
    
    @validates('tenant_id')
    def validate_tenant_id(self, value: int):
        """验证租客 ID"""
        from app.models import Tenant
        if not Tenant.query.get(value):
            raise ValidationError('租客不存在')


class ContractUpdateSchema(BaseSchema):
    """
    合同更新 Schema
    """
    
    title = fields.Str(allow_none=True, validate=lambda x: len(x) >= 2)
    description = fields.Str(allow_none=True)
    
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    rent_amount = fields.Float(allow_none=True, validate=lambda x: x > 0 if x else True)
    deposit_amount = fields.Float(allow_none=True, validate=lambda x: x >= 0 if x else True)
    
    payment_type = fields.Str(validate=lambda x: x in ['月付', '季付', '半年付', '年付'])
    payment_cycle = fields.Int(validate=lambda x: x > 0)
    
    status = fields.Str(validate=lambda x: x in ['draft', 'active', 'expired', 'terminated'])
    contract_file = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    
    room_id = fields.Int(allow_none=True)
