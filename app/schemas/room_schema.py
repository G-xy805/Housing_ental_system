"""
房间 Schema

提供房间模型的序列化和验证
"""
from marshmallow import fields, validates, ValidationError
from .base import BaseSchema, TimestampMixin


class RoomSchema(BaseSchema, TimestampMixin):
    """
    房间序列化 Schema
    """
    
    # 基本字段
    id = fields.Int(dump_only=True)
    room_number = fields.Str(required=True)
    name = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    
    # 房间属性
    area = fields.Float(allow_none=True)
    floor = fields.Str(allow_none=True)
    direction = fields.Str(allow_none=True)
    
    # 租金信息
    rent_price = fields.Float(required=True)
    deposit = fields.Float(allow_none=True)
    
    # 配套设施
    facilities = fields.Dict(allow_none=True)
    
    # 状态
    status = fields.Str(validate=lambda x: x in ['available', 'rented', 'maintenance'])
    
    # 外键
    house_id = fields.Int(required=True)
    
    # 计算字段
    room_no = fields.Str(dump_only=True)
    house_title = fields.Str(dump_only=True)
    house_address = fields.Str(dump_only=True)
    
    class Meta:
        fields = [
            'id', 'room_number', 'name', 'description',
            'area', 'floor', 'direction',
            'rent_price', 'deposit', 'facilities',
            'status', 'house_id',
            'room_no', 'house_title', 'house_address',
            'created_at', 'updated_at', 'is_active'
        ]
    
    @validates('rent_price')
    def validate_rent_price(self, value: float):
        """验证租金"""
        if value <= 0:
            raise ValidationError('租金必须大于 0')
    
    @validates('status')
    def validate_status(self, value: str):
        """验证状态"""
        if value not in ['available', 'rented', 'maintenance']:
            raise ValidationError('状态必须是 available、rented 或 maintenance')


class RoomCreateSchema(BaseSchema):
    """
    房间创建 Schema
    """
    
    room_number = fields.Str(required=True, validate=lambda x: len(x) >= 1)
    name = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    
    area = fields.Float(allow_none=True, validate=lambda x: x > 0 if x else True)
    floor = fields.Str(allow_none=True)
    direction = fields.Str(allow_none=True)
    
    rent_price = fields.Float(required=True, validate=lambda x: x > 0)
    deposit = fields.Float(allow_none=True, validate=lambda x: x >= 0 if x else True)
    facilities = fields.Dict(allow_none=True)
    
    status = fields.Str(validate=lambda x: x in ['available', 'rented', 'maintenance'])
    house_id = fields.Int(required=True)
    
    @validates('house_id')
    def validate_house_id(self, value: int):
        """验证房源 ID"""
        from app.models import House
        if not House.query.get(value):
            raise ValidationError('房源不存在')


class RoomUpdateSchema(BaseSchema):
    """
    房间更新 Schema
    """
    
    room_number = fields.Str(allow_none=True, validate=lambda x: len(x) >= 1)
    name = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    
    area = fields.Float(allow_none=True, validate=lambda x: x > 0 if x else True)
    floor = fields.Str(allow_none=True)
    direction = fields.Str(allow_none=True)
    
    rent_price = fields.Float(allow_none=True, validate=lambda x: x > 0 if x else True)
    deposit = fields.Float(allow_none=True, validate=lambda x: x >= 0 if x else True)
    facilities = fields.Dict(allow_none=True)
    
    status = fields.Str(validate=lambda x: x in ['available', 'rented', 'maintenance'])
