"""
数据库模型包

包含以下模型：
- User: 用户模型（管理员、普通员工）
- House: 房源模型（支持整租/合租）
- Room: 房间模型（合租场景）
- Tenant: 租客模型
- Landlord: 房东模型
- Contract: 合同模型（支持合租合同）
- LandlordContract: 平台与房东合同模型
- Payment: 支付记录模型（支持滞纳金计算）
- Media: 多媒体文件模型
"""
from .base import db, BaseModel
from .user import User
from .house import House
from .room import Room
from .tenant import Tenant
from .landlord import Landlord
from .contract import Contract
from .landlord_contract import LandlordContract
from .payment import Payment
from .media import Media

__all__ = [
    'db',
    'BaseModel',
    'User',
    'House',
    'Room',
    'Tenant',
    'Landlord',
    'Contract',
    'LandlordContract',
    'Payment',
    'Media'
]
