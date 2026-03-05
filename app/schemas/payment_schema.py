"""
支付 Schema

提供支付模型的序列化和验证
"""
from datetime import date
from marshmallow import fields, validates, ValidationError, post_dump
from .base import BaseSchema, TimestampMixin


class PaymentSchema(BaseSchema, TimestampMixin):
    """
    支付序列化 Schema
    """
    
    # 基本字段
    id = fields.Int(dump_only=True)
    payment_no = fields.Str(dump_only=True)
    
    # 支付信息
    amount = fields.Float(required=True)
    paid_amount = fields.Float(allow_none=True)
    
    # 支付类型
    payment_type = fields.Str(required=True, validate=lambda x: x in ['rent', 'deposit', 'utility', 'other'])
    
    # 支付方式
    payment_method = fields.Str(allow_none=True, validate=lambda x: x in ['cash', 'bank', 'wechat', 'alipay'])
    
    # 支付周期
    period_start = fields.Date(allow_none=True)
    period_end = fields.Date(allow_none=True)
    
    # 支付日期
    payment_date = fields.Date(allow_none=True)
    due_date = fields.Date(required=True)
    confirmed_date = fields.DateTime(allow_none=True)
    
    # 滞纳金
    late_fee = fields.Float(dump_only=True)
    late_fee_rate = fields.Float(dump_only=True)
    overdue_days = fields.Int(dump_only=True)
    
    # 状态
    status = fields.Str(validate=lambda x: x in ['pending', 'paid', 'overdue', 'partial', 'refunded', 'cancelled'])
    
    # 备注
    remark = fields.Str(allow_none=True)
    
    # 凭证
    receipt_file = fields.Str(allow_none=True)
    
    # 外键
    contract_id = fields.Int(required=True)
    operator_id = fields.Int(allow_none=True)
    
    # 嵌套对象
    contract_rel = fields.Nested('ContractSchema', dump_only=True)
    operator = fields.Nested('UserSchema', dump_only=True)
    
    # 计算字段
    contract_no = fields.Str(dump_only=True)
    tenant_name = fields.Str(dump_only=True)
    tenant_phone = fields.Str(dump_only=True)
    house_address = fields.Str(dump_only=True)
    room_no = fields.Str(dump_only=True)
    operator_name = fields.Str(dump_only=True)
    total_amount = fields.Float(dump_only=True)
    is_overdue = fields.Bool(dump_only=True)
    days_until_due = fields.Int(dump_only=True)
    payment_type_name = fields.Str(dump_only=True)
    payment_method_name = fields.Str(dump_only=True)
    
    class Meta:
        fields = [
            'id', 'payment_no',
            'amount', 'paid_amount',
            'payment_type', 'payment_method',
            'period_start', 'period_end',
            'payment_date', 'due_date', 'confirmed_date',
            'late_fee', 'late_fee_rate', 'overdue_days',
            'status', 'remark', 'receipt_file',
            'contract_id', 'operator_id',
            'contract_rel', 'operator',
            'contract_no', 'tenant_name', 'tenant_phone',
            'house_address', 'room_no', 'operator_name',
            'total_amount', 'is_overdue', 'days_until_due',
            'payment_type_name', 'payment_method_name',
            'created_at', 'updated_at', 'is_active'
        ]
    
    @validates('amount')
    def validate_amount(self, value: float):
        """验证金额"""
        if value <= 0:
            raise ValidationError('金额必须大于 0')
    
    @validates('due_date')
    def validate_due_date(self, value: date):
        """验证应缴日期"""
        if not value:
            raise ValidationError('应缴日期不能为空')


class PaymentCreateSchema(BaseSchema):
    """
    支付创建 Schema
    """
    
    amount = fields.Float(required=True, validate=lambda x: x > 0)
    payment_type = fields.Str(required=True, validate=lambda x: x in ['rent', 'deposit', 'utility', 'other'])
    
    period_start = fields.Date(allow_none=True)
    period_end = fields.Date(allow_none=True)
    due_date = fields.Date(required=True)
    
    status = fields.Str(validate=lambda x: x in ['pending', 'paid', 'overdue', 'partial', 'refunded', 'cancelled'])
    remark = fields.Str(allow_none=True)
    
    contract_id = fields.Int(required=True)
    operator_id = fields.Int(allow_none=True)
    
    @validates('contract_id')
    def validate_contract_id(self, value: int):
        """验证合同 ID"""
        from app.models import Contract
        if not Contract.query.get(value):
            raise ValidationError('合同不存在')


class PaymentUpdateSchema(BaseSchema):
    """
    支付更新 Schema
    """
    
    amount = fields.Float(allow_none=True, validate=lambda x: x > 0 if x else True)
    paid_amount = fields.Float(allow_none=True, validate=lambda x: x >= 0 if x else True)
    
    payment_method = fields.Str(allow_none=True, validate=lambda x: x in ['cash', 'bank', 'wechat', 'alipay'])
    
    period_start = fields.Date(allow_none=True)
    period_end = fields.Date(allow_none=True)
    payment_date = fields.Date(allow_none=True)
    
    status = fields.Str(validate=lambda x: x in ['pending', 'paid', 'overdue', 'partial', 'refunded', 'cancelled'])
    remark = fields.Str(allow_none=True)
    receipt_file = fields.Str(allow_none=True)
