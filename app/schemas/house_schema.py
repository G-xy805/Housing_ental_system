"""
房源 Schema

提供房源模型的序列化和验证
"""
from typing import Optional
from marshmallow import fields, validates, ValidationError, post_dump, pre_load
from .base import BaseSchema, TimestampMixin


class HouseSchema(BaseSchema, TimestampMixin):
    """
    房源序列化 Schema
    
    支持内部/外部接口区分
    支持 facilities/amenities 字段别名
    """
    
    # 内部接口专用字段
    INTERNAL_ONLY_FIELDS = {'contact_name', 'contact_phone', 'contact_wechat'}
    
    # 基本字段
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    
    # 地址信息
    province = fields.Str(allow_none=True)
    city = fields.Str(allow_none=True)
    district = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)
    
    # 房源属性
    area = fields.Float(allow_none=True)
    room_count = fields.Int(allow_none=True)
    hall_count = fields.Int(allow_none=True)
    bathroom_count = fields.Int(allow_none=True)
    floor = fields.Str(allow_none=True)
    total_floors = fields.Int(allow_none=True)
    orientation = fields.Str(allow_none=True)
    decoration = fields.Str(allow_none=True)
    
    # 租金信息
    rent_price = fields.Decimal(required=True, places=2, as_string=False)
    deposit = fields.Decimal(allow_none=True, places=2, as_string=False)
    payment_method = fields.Str(allow_none=True)
    
    # 状态
    status = fields.Str(validate=lambda x: x in ['available', 'rented', 'maintenance', 'partially_rented'])
    
    # 配套设施（数据库字段）
    facilities = fields.Dict(allow_none=True)
    
    # 配套设施别名（前端使用，数组格式）
    amenities = fields.List(fields.Str(), dump_only=True)
    
    # 图片
    images = fields.List(fields.Str(), allow_none=True)
    cover_image = fields.Str(allow_none=True)
    
    # 租赁类型
    rental_type = fields.Str(validate=lambda x: x in ['whole', 'shared'])
    
    # 外键
    owner_id = fields.Int(required=True)
    landlord_id = fields.Int(allow_none=True)
    
    # 联系信息
    contact_name = fields.Str(allow_none=True)
    contact_phone = fields.Str(allow_none=True)
    contact_wechat = fields.Str(allow_none=True)
    
    # 嵌套对象
    owner = fields.Nested('UserSchema', dump_only=True)
    landlord_rel = fields.Nested('LandlordSchema', dump_only=True)
    
    # 计算字段
    owner_name = fields.Str(dump_only=True)
    landlord_name = fields.Str(dump_only=True)
    landlord_phone = fields.Str(dump_only=True)
    room_count_actual = fields.Int(dump_only=True)
    available_rooms = fields.List(fields.Dict(), dump_only=True)
    
    class Meta:
        fields = [
            'id', 'title', 'description',
            'province', 'city', 'district', 'address', 'latitude', 'longitude',
            'area', 'room_count', 'hall_count', 'bathroom_count', 'floor', 'total_floors',
            'orientation', 'decoration',
            'rent_price', 'deposit', 'payment_method',
            'status', 'facilities', 'amenities', 'images', 'cover_image', 'rental_type',
            'owner_id', 'landlord_id',
            'contact_name', 'contact_phone', 'contact_wechat',
            'owner', 'landlord_rel',
            'owner_name', 'landlord_name', 'landlord_phone',
            'room_count_actual', 'available_rooms',
            'created_at', 'updated_at', 'is_active'
        ]
    
    @validates('rental_type')
    def validate_rental_type(self, value: str):
        """验证租赁类型"""
        if value not in ['whole', 'shared']:
            raise ValidationError('租赁类型必须是 whole 或 shared')
    
    @validates('status')
    def validate_status(self, value: str):
        """验证状态"""
        if value not in ['available', 'rented', 'maintenance', 'partially_rented']:
            raise ValidationError('状态无效')
    
    @pre_load
    def process_amenities(self, data, **kwargs):
        """
        处理 amenities 字段（前端输入）
        将 amenities 数组转换为 facilities 对象
        """
        if 'amenities' in data and isinstance(data['amenities'], list):
            # 将数组转换为对象格式 {item: true}
            facilities = {}
            for item in data['amenities']:
                if isinstance(item, str):
                    facilities[item] = True
            data['facilities'] = facilities
            # 移除 amenities 字段，避免重复处理
            data.pop('amenities', None)
        return data
    
    @post_dump
    def add_computed_fields(self, data, **kwargs):
        """添加计算字段"""
        # 根据内部/外部接口决定是否显示联系信息
        is_internal = self._is_internal
        
        if not is_internal:
            # 外部接口：隐藏房东信息
            data['contact_name'] = None
            data['contact_phone'] = None
            data['contact_wechat'] = None
            data['landlord_name'] = '平台管家'
            data['landlord_phone'] = None
        
        # 添加 amenities 别名（将 facilities 对象转换为数组）
        if 'facilities' in data and isinstance(data['facilities'], dict):
            amenities = [key for key, value in data['facilities'].items() if value is True]
            data['amenities'] = amenities
        elif 'amenities' not in data:
            data['amenities'] = []
        
        return data


class HouseListSchema(HouseSchema):
    """
    房源列表 Schema
    
    用于列表查询，不包含嵌套对象
    """
    
    class Meta(HouseSchema.Meta):
        # 列表查询时不包含嵌套对象
        exclude = ['owner', 'landlord_rel', 'available_rooms']


class HouseCreateSchema(BaseSchema):
    """
    房源创建 Schema
    
    用于创建房源时的数据验证
    支持 facilities/amenities 字段别名
    """
    
    title = fields.Str(required=True, validate=lambda x: len(x) >= 2)
    description = fields.Str(allow_none=True)
    
    province = fields.Str(allow_none=True)
    city = fields.Str(allow_none=True)
    district = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)
    
    area = fields.Float(allow_none=True, validate=lambda x: x > 0 if x else True)
    room_count = fields.Int(allow_none=True, validate=lambda x: x >= 0 if x else True)
    hall_count = fields.Int(allow_none=True, validate=lambda x: x >= 0 if x else True)
    bathroom_count = fields.Int(allow_none=True, validate=lambda x: x >= 0 if x else True)
    floor = fields.Str(allow_none=True)
    total_floors = fields.Int(allow_none=True, validate=lambda x: x > 0 if x else True)
    
    rent_price = fields.Decimal(required=True, places=2, as_string=False, validate=lambda x: x > 0)
    deposit = fields.Decimal(allow_none=True, places=2, as_string=False, validate=lambda x: x >= 0 if x else True)
    payment_method = fields.Str(allow_none=True)
    
    status = fields.Str(validate=lambda x: x in ['available', 'rented', 'maintenance', 'partially_rented'])
    
    # 配套设施（支持两种格式）
    facilities = fields.Dict(allow_none=True)  # 后端存储格式：{"wifi": true, "ac": true}
    amenities = fields.List(fields.Str(), load_only=True)  # 前端提交格式：["wifi", "ac"]
    
    images = fields.List(fields.Str(), allow_none=True)
    cover_image = fields.Str(allow_none=True)
    rental_type = fields.Str(required=True, validate=lambda x: x in ['whole', 'shared'])
    
    owner_id = fields.Int(required=True)
    landlord_id = fields.Int(allow_none=True)
    
    contact_name = fields.Str(allow_none=True)
    contact_phone = fields.Str(allow_none=True)
    contact_wechat = fields.Str(allow_none=True)
    
    @validates('owner_id')
    def validate_owner_id(self, value: int):
        """验证负责人 ID"""
        from app.models import User
        if not User.query.get(value):
            raise ValidationError('负责人不存在')
    
    @post_dump
    def convert_amenities_to_facilities(self, data, **kwargs):
        """将 amenities 转换为 facilities 格式"""
        # 如果前端传了 amenities 数组，转换为 facilities 对象
        if 'amenities' in data and isinstance(data['amenities'], list):
            data['facilities'] = {item: True for item in data['amenities'] if item}
            # 移除 amenities 字段（不存入数据库）
            data.pop('amenities', None)
        return data


class HouseUpdateSchema(BaseSchema):
    """
    房源更新 Schema
    
    用于更新房源信息时的数据验证
    支持 facilities/amenities 字段别名
    """
    
    title = fields.Str(allow_none=True, validate=lambda x: len(x) >= 2)
    description = fields.Str(allow_none=True)
    
    province = fields.Str(allow_none=True)
    city = fields.Str(allow_none=True)
    district = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)
    
    area = fields.Float(allow_none=True, validate=lambda x: x > 0 if x else True)
    room_count = fields.Int(allow_none=True, validate=lambda x: x >= 0 if x else True)
    hall_count = fields.Int(allow_none=True, validate=lambda x: x >= 0 if x else True)
    bathroom_count = fields.Int(allow_none=True, validate=lambda x: x >= 0 if x else True)
    floor = fields.Str(allow_none=True)
    total_floors = fields.Int(allow_none=True, validate=lambda x: x > 0 if x else True)
    
    rent_price = fields.Decimal(allow_none=True, places=2, as_string=False, validate=lambda x: x > 0 if x else True)
    deposit = fields.Decimal(allow_none=True, places=2, as_string=False, validate=lambda x: x >= 0 if x else True)
    payment_method = fields.Str(allow_none=True)
    
    status = fields.Str(validate=lambda x: x in ['available', 'rented', 'maintenance', 'partially_rented'])
    
    # 配套设施（支持两种格式）
    facilities = fields.Dict(allow_none=True)  # 后端存储格式：{"wifi": true, "ac": true}
    amenities = fields.List(fields.Str(), load_only=True)  # 前端提交格式：["wifi", "ac"]
    
    images = fields.List(fields.Str(), allow_none=True)
    cover_image = fields.Str(allow_none=True)
    rental_type = fields.Str(validate=lambda x: x in ['whole', 'shared'])
    
    landlord_id = fields.Int(allow_none=True)
    
    contact_name = fields.Str(allow_none=True)
    contact_phone = fields.Str(allow_none=True)
    contact_wechat = fields.Str(allow_none=True)
    
    @post_dump
    def convert_amenities_to_facilities(self, data, **kwargs):
        """将 amenities 转换为 facilities 格式"""
        # 如果前端传了 amenities 数组，转换为 facilities 对象
        if 'amenities' in data and isinstance(data['amenities'], list):
            data['facilities'] = {item: True for item in data['amenities'] if item}
            # 移除 amenities 字段（不存入数据库）
            data.pop('amenities', None)
        return data
