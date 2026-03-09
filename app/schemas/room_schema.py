"""
房间 Schema

提供房间模型的序列化和验证
支持 facilities/amenities 字段别名
"""
from marshmallow import fields, validates, ValidationError, post_dump
from .base import BaseSchema, TimestampMixin


class RoomSchema(BaseSchema, TimestampMixin):
    """
    房间序列化 Schema
    支持 facilities/amenities 字段别名
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
    rent_price = fields.Decimal(required=True, places=2, as_string=False)
    deposit = fields.Decimal(allow_none=True, places=2, as_string=False)
    
    # 配套设施（数据库字段）
    facilities = fields.Dict(allow_none=True)
    
    # 配套设施别名（前端使用，数组格式）
    amenities = fields.List(fields.Str(), dump_only=True)
    
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
            'rent_price', 'deposit', 'facilities', 'amenities',
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
    
    @post_dump
    def add_amenities_alias(self, data, **kwargs):
        """添加 amenities 别名字段"""
        # 将 facilities 对象转换为 amenities 数组
        if 'facilities' in data and isinstance(data['facilities'], dict):
            amenities = [key for key, value in data['facilities'].items() if value is True]
            data['amenities'] = amenities
        elif 'amenities' not in data:
            data['amenities'] = []
        
        return data


class RoomCreateSchema(BaseSchema):
    """
    房间创建 Schema
    支持 facilities/amenities 字段别名
    """
    
    room_number = fields.Str(required=True, validate=lambda x: len(x) >= 1)
    name = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    
    area = fields.Float(allow_none=True, validate=lambda x: x > 0 if x else True)
    floor = fields.Str(allow_none=True)
    direction = fields.Str(allow_none=True)
    
    rent_price = fields.Decimal(required=True, places=2, as_string=False, validate=lambda x: x > 0)
    deposit = fields.Decimal(allow_none=True, places=2, as_string=False, validate=lambda x: x >= 0 if x else True)
    
    # 配套设施（支持两种格式）
    facilities = fields.Dict(allow_none=True)  # 后端存储格式：{"bed": true, "ac": true}
    amenities = fields.List(fields.Str(), load_only=True)  # 前端提交格式：["bed", "ac"]
    
    status = fields.Str(validate=lambda x: x in ['available', 'rented', 'maintenance'])
    house_id = fields.Int(required=True)
    
    @validates('house_id')
    def validate_house_id(self, value: int):
        """验证房源 ID"""
        from app.models import House
        if not House.query.get(value):
            raise ValidationError('房源不存在')
    
    @post_dump
    def convert_amenities_to_facilities(self, data, **kwargs):
        """将 amenities 转换为 facilities 格式"""
        # 如果前端传了 amenities 数组，转换为 facilities 对象
        if 'amenities' in data and isinstance(data['amenities'], list):
            data['facilities'] = {item: True for item in data['amenities'] if item}
            # 移除 amenities 字段（不存入数据库）
            data.pop('amenities', None)
        return data


class RoomUpdateSchema(BaseSchema):
    """
    房间更新 Schema
    支持 facilities/amenities 字段别名
    """
    
    room_number = fields.Str(allow_none=True, validate=lambda x: len(x) >= 1)
    name = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    
    area = fields.Float(allow_none=True, validate=lambda x: x > 0 if x else True)
    floor = fields.Str(allow_none=True)
    direction = fields.Str(allow_none=True)
    
    rent_price = fields.Decimal(allow_none=True, places=2, as_string=False, validate=lambda x: x > 0 if x else True)
    deposit = fields.Decimal(allow_none=True, places=2, as_string=False, validate=lambda x: x >= 0 if x else True)
    
    # 配套设施（支持两种格式）
    facilities = fields.Dict(allow_none=True)  # 后端存储格式：{"bed": true, "ac": true}
    amenities = fields.List(fields.Str(), load_only=True)  # 前端提交格式：["bed", "ac"]
    
    status = fields.Str(validate=lambda x: x in ['available', 'rented', 'maintenance'])
    
    @post_dump
    def convert_amenities_to_facilities(self, data, **kwargs):
        """将 amenities 转换为 facilities 格式"""
        # 如果前端传了 amenities 数组，转换为 facilities 对象
        if 'amenities' in data and isinstance(data['amenities'], list):
            data['facilities'] = {item: True for item in data['amenities'] if item}
            # 移除 amenities 字段（不存入数据库）
            data.pop('amenities', None)
        return data
