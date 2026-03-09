"""
数据归档模型

提供合同和支付记录的归档功能：
- contracts_archive: 合同归档表
- payments_archive: 支付记录归档表

归档策略：
- 已过期或已终止的合同（超过保留期限）
- 已完成或已取消的支付记录（超过保留期限）
- 定期自动归档（每月执行）
"""
from datetime import datetime, date
from decimal import Decimal
from app import db
from .base import BaseModel


class ContractArchive(BaseModel):
    """
    合同归档表
    
    存储已过期或已终止的合同数据
    不设置外键约束，避免数据完整性问题
    """
    
    __tablename__ = 'contracts_archive'
    
    # 归档信息
    archived_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='归档时间')
    archive_reason = db.Column(db.String(50), comment='归档原因（expired/terminated/manual）')
    original_id = db.Column(db.Integer, nullable=False, comment='原合同ID')
    
    # 合同基本信息
    contract_no = db.Column(db.String(50), nullable=False, comment='合同编号')
    title = db.Column(db.String(100), nullable=False, comment='合同标题')
    description = db.Column(db.Text, comment='合同描述')
    
    # 租赁信息
    start_date = db.Column(db.Date, nullable=False, comment='起租日期')
    end_date = db.Column(db.Date, nullable=False, comment='结束日期')
    rent_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='租金金额（元/月）')
    deposit_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='押金金额（元）')
    
    # 付款方式
    payment_type = db.Column(db.String(20), default='月付', comment='付款类型')
    payment_cycle = db.Column(db.Integer, default=1, comment='付款周期（月数）')
    
    # 合同状态
    status = db.Column(db.String(20), default='expired', comment='合同状态')
    deposit_status = db.Column(db.String(20), default='pending', comment='押金状态')
    
    # 关联信息（不设置外键）
    original_contract_id = db.Column(db.Integer, comment='原合同ID（续签时）')
    house_id = db.Column(db.Integer, nullable=False, comment='房源 ID')
    room_id = db.Column(db.Integer, comment='房间 ID（合租时填写）')
    tenant_id = db.Column(db.Integer, nullable=False, comment='租客 ID')
    
    # 冗余字段（便于查询，避免关联）
    house_title = db.Column(db.String(100), comment='房源标题')
    house_address = db.Column(db.String(255), comment='房源地址')
    tenant_name = db.Column(db.String(50), comment='租客姓名')
    tenant_phone = db.Column(db.String(20), comment='租客电话')
    
    # 合同文件
    contract_file = db.Column(db.String(255), comment='合同文件路径')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 索引
    __table_args__ = (
        db.Index('idx_contracts_archive_archived_at', 'archived_at'),
        db.Index('idx_contracts_archive_original_id', 'original_id'),
        db.Index('idx_contracts_archive_house_id', 'house_id'),
        db.Index('idx_contracts_archive_tenant_id', 'tenant_id'),
        db.Index('idx_contracts_archive_dates', 'start_date', 'end_date'),
        db.Index('idx_contracts_archive_status', 'status'),
    )
    
    @classmethod
    def archive_from_contract(cls, contract, archive_reason='expired'):
        """
        从合同对象创建归档记录
        
        Args:
            contract: Contract 对象
            archive_reason: 归档原因
            
        Returns:
            ContractArchive: 归档记录
        """
        # 获取冗余字段
        house_title = None
        house_address = None
        tenant_name = None
        tenant_phone = None
        
        try:
            if contract.house:
                house_title = contract.house.title
                house_address = contract.house.address
        except Exception:
            pass
        
        try:
            if contract.tenant_rel:
                tenant_name = contract.tenant_rel.name
                tenant_phone = contract.tenant_rel.phone
        except Exception:
            pass
        
        archive = cls(
            archived_at=datetime.now(),
            archive_reason=archive_reason,
            original_id=contract.id,
            contract_no=contract.contract_no,
            title=contract.title,
            description=contract.description,
            start_date=contract.start_date,
            end_date=contract.end_date,
            rent_amount=contract.rent_amount,
            deposit_amount=contract.deposit_amount,
            payment_type=contract.payment_type,
            payment_cycle=contract.payment_cycle,
            status=contract.status,
            deposit_status=contract.deposit_status,
            original_contract_id=contract.original_contract_id,
            house_id=contract.house_id,
            room_id=contract.room_id,
            tenant_id=contract.tenant_id,
            house_title=house_title,
            house_address=house_address,
            tenant_name=tenant_name,
            tenant_phone=tenant_phone,
            contract_file=contract.contract_file,
            remark=contract.remark
        )
        
        return archive
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data['archived_at'] = self.archived_at.strftime('%Y-%m-%d %H:%M:%S') if self.archived_at else None
        data['start_date'] = self.start_date.strftime('%Y-%m-%d') if self.start_date else None
        data['end_date'] = self.end_date.strftime('%Y-%m-%d') if self.end_date else None
        return data
    
    def __repr__(self):
        return f'<ContractArchive {self.contract_no}>'


class PaymentArchive(BaseModel):
    """
    支付记录归档表
    
    存储已完成或已取消的支付记录
    不设置外键约束，避免数据完整性问题
    """
    
    __tablename__ = 'payments_archive'
    
    # 归档信息
    archived_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='归档时间')
    archive_reason = db.Column(db.String(50), comment='归档原因（completed/cancelled/manual）')
    original_id = db.Column(db.Integer, nullable=False, comment='原支付记录ID')
    
    # 支付基本信息
    payment_no = db.Column(db.String(50), nullable=False, comment='支付编号')
    amount = db.Column(db.Numeric(10, 2), nullable=False, comment='应缴金额')
    paid_amount = db.Column(db.Numeric(10, 2), default=0, comment='实缴金额')
    
    # 支付类型
    payment_type = db.Column(db.String(20), nullable=False, comment='支付类型')
    payment_method = db.Column(db.String(50), comment='支付方式')
    
    # 支付周期
    period_start = db.Column(db.Date, comment='支付周期开始')
    period_end = db.Column(db.Date, comment='周期结束')
    
    # 支付日期
    payment_date = db.Column(db.Date, comment='实际支付日期')
    due_date = db.Column(db.Date, nullable=False, comment='应缴日期')
    confirmed_date = db.Column(db.DateTime, comment='确认到账日期')
    
    # 滞纳金
    late_fee = db.Column(db.Numeric(10, 2), default=Decimal('0.00'), comment='滞纳金金额')
    late_fee_rate = db.Column(db.Numeric(8, 6), default=Decimal('0.0005'), comment='滞纳金比例（每日）')
    overdue_days = db.Column(db.Integer, default=0, comment='逾期天数')
    
    # 状态
    status = db.Column(db.String(20), default='completed', comment='支付状态')
    
    # 关联信息（不设置外键）
    contract_id = db.Column(db.Integer, comment='合同 ID')
    operator_id = db.Column(db.Integer, comment='操作人 ID')
    
    # 冗余字段（便于查询，避免关联）
    contract_no = db.Column(db.String(50), comment='合同编号')
    tenant_name = db.Column(db.String(50), comment='租客姓名')
    tenant_phone = db.Column(db.String(20), comment='租客电话')
    house_address = db.Column(db.String(255), comment='房源地址')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 凭证
    receipt_file = db.Column(db.String(255), comment='收据/凭证文件路径')
    
    # 索引
    __table_args__ = (
        db.Index('idx_payments_archive_archived_at', 'archived_at'),
        db.Index('idx_payments_archive_original_id', 'original_id'),
        db.Index('idx_payments_archive_contract_id', 'contract_id'),
        db.Index('idx_payments_archive_due_date', 'due_date'),
        db.Index('idx_payments_archive_status', 'status'),
        db.Index('idx_payments_archive_payment_type', 'payment_type'),
    )
    
    @classmethod
    def archive_from_payment(cls, payment, archive_reason='completed'):
        """
        从支付记录对象创建归档记录
        
        Args:
            payment: Payment 对象
            archive_reason: 归档原因
            
        Returns:
            PaymentArchive: 归档记录
        """
        # 获取冗余字段
        contract_no = None
        tenant_name = None
        tenant_phone = None
        house_address = None
        
        try:
            if payment.contract_rel:
                contract_no = payment.contract_rel.contract_no
                if payment.contract_rel.tenant_rel:
                    tenant_name = payment.contract_rel.tenant_rel.name
                    tenant_phone = payment.contract_rel.tenant_rel.phone
                if payment.contract_rel.house:
                    house_address = payment.contract_rel.house.address
        except Exception:
            pass
        
        archive = cls(
            archived_at=datetime.now(),
            archive_reason=archive_reason,
            original_id=payment.id,
            payment_no=payment.payment_no,
            amount=payment.amount,
            paid_amount=payment.paid_amount,
            payment_type=payment.payment_type,
            payment_method=payment.payment_method,
            period_start=payment.period_start,
            period_end=payment.period_end,
            payment_date=payment.payment_date,
            due_date=payment.due_date,
            confirmed_date=payment.confirmed_date,
            late_fee=payment.late_fee,
            late_fee_rate=payment.late_fee_rate,
            overdue_days=payment.overdue_days,
            status=payment.status,
            contract_id=payment.contract_id,
            operator_id=payment.operator_id,
            contract_no=contract_no,
            tenant_name=tenant_name,
            tenant_phone=tenant_phone,
            house_address=house_address,
            remark=payment.remark,
            receipt_file=payment.receipt_file
        )
        
        return archive
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data['archived_at'] = self.archived_at.strftime('%Y-%m-%d %H:%M:%S') if self.archived_at else None
        data['payment_date'] = self.payment_date.strftime('%Y-%m-%d') if self.payment_date else None
        data['due_date'] = self.due_date.strftime('%Y-%m-%d') if self.due_date else None
        data['period_start'] = self.period_start.strftime('%Y-%m-%d') if self.period_start else None
        data['period_end'] = self.period_end.strftime('%Y-%m-%d') if self.period_end else None
        return data
    
    def __repr__(self):
        return f'<PaymentArchive {self.payment_no}>'


class ArchiveRecord(BaseModel):
    """
    归档操作记录表
    
    记录每次归档操作的详细信息
    """
    
    __tablename__ = 'archive_records'
    
    # 归档信息
    archive_type = db.Column(db.String(50), nullable=False, comment='归档类型（contract/payment）')
    archive_date = db.Column(db.Date, nullable=False, comment='归档日期')
    archive_reason = db.Column(db.String(50), comment='归档原因')
    
    # 统计信息
    total_records = db.Column(db.Integer, default=0, comment='总记录数')
    archived_records = db.Column(db.Integer, default=0, comment='已归档记录数')
    failed_records = db.Column(db.Integer, default=0, comment='失败记录数')
    
    # 时间信息
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    execution_time = db.Column(db.Float, comment='执行时间（秒）')
    
    # 筛选条件
    date_range_start = db.Column(db.Date, comment='日期范围开始')
    date_range_end = db.Column(db.Date, comment='日期范围结束')
    
    # 错误信息
    error_message = db.Column(db.Text, comment='错误信息')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 索引
    __table_args__ = (
        db.Index('idx_archive_records_type', 'archive_type'),
        db.Index('idx_archive_records_date', 'archive_date'),
        db.Index('idx_archive_records_status', 'is_active'),
    )
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data['archive_date'] = self.archive_date.strftime('%Y-%m-%d') if self.archive_date else None
        data['date_range_start'] = self.date_range_start.strftime('%Y-%m-%d') if self.date_range_start else None
        data['date_range_end'] = self.date_range_end.strftime('%Y-%m-%d') if self.date_range_end else None
        data['started_at'] = self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None
        data['completed_at'] = self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None
        return data
    
    def __repr__(self):
        return f'<ArchiveRecord {self.archive_type} {self.archive_date}>'
