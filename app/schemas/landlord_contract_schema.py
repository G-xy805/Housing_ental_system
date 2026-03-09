"""
房东合同 Schema

提供房东合同模型的序列化和验证
"""
from datetime import date
from marshmallow import fields, validates, ValidationError, post_dump
from .base import BaseSchema, TimestampMixin


class LandlordContractSchema(BaseSchema, TimestampMixin):
    """
    房东合同序列化 Schema
    """
    
    # 基本字段
    id = fields.Int(dump_only=True)
    contract_no = fields.Str(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    
    # 合同期限
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    
    # 金额信息
    contract_amount = fields.Decimal(required=True, places=2, as_string=False)
    service_fee_rate = fields.Decimal(required=True, places=2, as_string=False)
    minimum_fee = fields.Decimal(allow_none=True, places=2, as_string=False)
    payment_cycle = fields.Int(validate=lambda x: x > 0)
    
    # 状态
    status = fields.Str(validate=lambda x: x in ['draft', 'active', 'expired', 'terminated'])
    
    # 文件
    contract_file = fields.Str(allow_none=True)
    
    # 备注
    remark = fields.Str(allow_none=True)
    
    # 外键
    landlord_id = fields.Int(required=True)
    
    # 关联房源
    house_ids = fields.List(fields.Int(), allow_none=True)
    
    # 嵌套对象
    landlord = fields.Nested('LandlordSchema', dump_only=True)
    
    # 计算字段
    contract_term_months = fields.Float(dump_only=True)
    service_fee = fields.Decimal(dump_only=True, places=2, as_string=False)
    is_expired = fields.Bool(dump_only=True)
    days_until_expiry = fields.Int(dump_only=True)
    houses = fields.List(fields.Dict(), dump_only=True)
    
    class Meta:
        fields = [
            'id', 'contract_no', 'title', 'description',
            'start_date', 'end_date',
            'contract_amount', 'service_fee_rate', 'minimum_fee', 'payment_cycle',
            'status', 'contract_file', 'remark',
            'landlord_id', 'house_ids',
            'landlord',
            'contract_term_months', 'service_fee',
            'is_expired', 'days_until_expiry', 'houses',
            'created_at', 'updated_at', 'is_active'
        ]
    
    @validates('contract_amount')
    def validate_contract_amount(self, value: float):
        """验证合同金额"""
        if value <= 0:
            raise ValidationError('合同金额必须大于 0')
    
    @validates('service_fee_rate')
    def validate_service_fee_rate(self, value: float):
        """验证服务费率"""
        if value < 0 or value > 100:
            raise ValidationError('服务费率必须在 0-100 之间')


class LandlordContractCreateSchema(BaseSchema):
    """
    房东合同创建 Schema
    """
    
    title = fields.Str(required=True, validate=lambda x: len(x) >= 2)
    description = fields.Str(allow_none=True)
    
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    
    contract_amount = fields.Decimal(required=True, places=2, as_string=False, validate=lambda x: x > 0)
    service_fee_rate = fields.Decimal(required=True, places=2, as_string=False, validate=lambda x: 0 <= x <= 100)
    minimum_fee = fields.Decimal(allow_none=True, places=2, as_string=False, validate=lambda x: x >= 0 if x else True)
    payment_cycle = fields.Int(validate=lambda x: x > 0)
    
    status = fields.Str(validate=lambda x: x in ['draft', 'active', 'expired', 'terminated'])
    contract_file = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    
    landlord_id = fields.Int(required=True)
    house_ids = fields.List(fields.Int(), allow_none=True)
    
    @validates('landlord_id')
    def validate_landlord_id(self, value: int):
        """验证房东 ID"""
        from app.models import Landlord
        if not Landlord.query.get(value):
            raise ValidationError('房东不存在')


class LandlordContractUpdateSchema(BaseSchema):
    """
    房东合同更新 Schema
    """
    
    title = fields.Str(allow_none=True, validate=lambda x: len(x) >= 2)
    description = fields.Str(allow_none=True)
    
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    
    contract_amount = fields.Decimal(allow_none=True, places=2, as_string=False, validate=lambda x: x > 0 if x else True)
    service_fee_rate = fields.Decimal(allow_none=True, places=2, as_string=False, validate=lambda x: 0 <= x <= 100 if x else True)
    minimum_fee = fields.Decimal(allow_none=True, places=2, as_string=False, validate=lambda x: x >= 0 if x else True)
    payment_cycle = fields.Int(validate=lambda x: x > 0)
    
    status = fields.Str(validate=lambda x: x in ['draft', 'active', 'expired', 'terminated'])
    contract_file = fields.Str(allow_none=True)
    remark = fields.Str(allow_none=True)
    
    house_ids = fields.List(fields.Int(), allow_none=True)
