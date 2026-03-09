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
- DepositRefund: 押金退款模型
- Media: 多媒体文件模型
- EncryptionAuditLog: 加密访问审计日志模型
- SensitiveDataAuditLog: 敏感数据访问审计日志模型
- BackupRecord: 备份记录模型
- PasswordHistory: 密码历史记录模型
- StartupTaskRecord: 启动任务执行记录模型
- ContractArchive: 合同归档模型
- PaymentArchive: 支付记录归档模型
- ArchiveRecord: 归档操作记录模型
"""
from .base import db, BaseModel, SoftDeleteQuery
from .user import User
from .house import House
from .room import Room
from .tenant import Tenant
from .landlord import Landlord
from .contract import Contract
from .landlord_contract import LandlordContract
from .payment import Payment
from .deposit_refund import DepositRefund
from .media import Media
from .encryption_audit import EncryptionAuditLog
from .sensitive_data_audit import SensitiveDataAuditLog
from .backup_record import BackupRecord
from .backup_settings import BackupSettings
from .password_history import PasswordHistory
from .archive import ContractArchive, PaymentArchive, ArchiveRecord

from app.utils.startup_tasks import StartupTaskRecord

__all__ = [
    'db',
    'BaseModel',
    'SoftDeleteQuery',
    'User',
    'House',
    'Room',
    'Tenant',
    'Landlord',
    'Contract',
    'LandlordContract',
    'Payment',
    'DepositRefund',
    'Media',
    'EncryptionAuditLog',
    'SensitiveDataAuditLog',
    'BackupRecord',
    'BackupSettings',
    'PasswordHistory',
    'StartupTaskRecord',
    'ContractArchive',
    'PaymentArchive',
    'ArchiveRecord'
]
