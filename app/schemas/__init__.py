"""
Marshmallow Schema 包

提供模型序列化和反序列化功能，支持：
- 字段过滤和嵌套控制
- 数据验证
- 敏感字段自动过滤
- 向后兼容的 to_dict() 方法
"""
from .base import BaseSchema, TimestampMixin
from .user_schema import UserSchema, UserCreateSchema, UserUpdateSchema
from .landlord_schema import LandlordSchema, LandlordCreateSchema, LandlordUpdateSchema
from .house_schema import HouseSchema, HouseCreateSchema, HouseUpdateSchema, HouseListSchema
from .tenant_schema import TenantSchema, TenantCreateSchema, TenantUpdateSchema
from .contract_schema import ContractSchema, ContractCreateSchema, ContractUpdateSchema
from .room_schema import RoomSchema, RoomCreateSchema, RoomUpdateSchema
from .payment_schema import PaymentSchema, PaymentCreateSchema, PaymentUpdateSchema
from .landlord_contract_schema import LandlordContractSchema, LandlordContractCreateSchema, LandlordContractUpdateSchema
from .media_schema import MediaSchema, MediaCreateSchema

__all__ = [
    # Base
    'BaseSchema',
    'TimestampMixin',
    # User
    'UserSchema',
    'UserCreateSchema',
    'UserUpdateSchema',
    # Landlord
    'LandlordSchema',
    'LandlordCreateSchema',
    'LandlordUpdateSchema',
    # House
    'HouseSchema',
    'HouseCreateSchema',
    'HouseUpdateSchema',
    'HouseListSchema',
    # Tenant
    'TenantSchema',
    'TenantCreateSchema',
    'TenantUpdateSchema',
    # Contract
    'ContractSchema',
    'ContractCreateSchema',
    'ContractUpdateSchema',
    # Room
    'RoomSchema',
    'RoomCreateSchema',
    'RoomUpdateSchema',
    # Payment
    'PaymentSchema',
    'PaymentCreateSchema',
    'PaymentUpdateSchema',
    # LandlordContract
    'LandlordContractSchema',
    'LandlordContractCreateSchema',
    'LandlordContractUpdateSchema',
    # Media
    'MediaSchema',
    'MediaCreateSchema',
]
