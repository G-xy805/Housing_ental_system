"""
租赁合同模型
"""
from datetime import datetime, date
from sqlalchemy import event, case
from sqlalchemy.orm import validates
from .base import db, BaseModel


class OptimisticLockError(Exception):
    """乐观锁冲突异常"""
    pass


class Contract(BaseModel):
    """
    租赁合同模型
    
    支持整租和合租合同
    合租合同可关联到具体房间
    
    乐观锁机制：
    - version 字段用于版本控制
    - 更新时自动检查版本号，防止并发冲突
    
    押金状态跟踪：
    - pending: 待支付（合同创建后的初始状态）
    - paid: 已支付（租客已支付押金）
    - transferred: 已转移（续签时押金转移到新合同）
    - refunded: 已退款（合同结束后押金已退还）
    """
    
    __tablename__ = 'contracts'
    
    # 合同编号（自动生成）
    contract_no = db.Column(db.String(50), unique=True, nullable=False, comment='合同编号')
    
    # 乐观锁版本号
    version = db.Column(db.Integer, default=0, nullable=False, comment='版本号（乐观锁）')
    
    # 合同信息
    title = db.Column(db.String(100), nullable=False, comment='合同标题')
    description = db.Column(db.Text, comment='合同描述')
    
    # 租赁信息
    start_date = db.Column(db.Date, nullable=False, comment='起租日期')
    end_date = db.Column(db.Date, nullable=False, comment='结束日期')
    rent_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='租金金额（元/月）')
    deposit_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='押金金额（元）')
    
    # 付款方式：月付、季付、半年付、年付
    payment_type = db.Column(db.String(20), default='月付', comment='付款类型')
    payment_cycle = db.Column(db.Integer, default=1, comment='付款周期（月数）')
    
    # 合同状态：draft-草稿，active-生效中，expired-已过期，terminated-已终止
    status = db.Column(db.String(20), default='draft', comment='合同状态')
    
    # 押金状态：pending-待支付，paid-已支付，transferred-已转移，refunded-已退款
    deposit_status = db.Column(db.String(20), default='pending', comment='押金状态')
    
    # 关联的原合同ID（续签时记录原合同）
    original_contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), comment='原合同ID（续签时）')
    
    # 合同文件
    contract_file = db.Column(db.String(255), comment='合同文件路径')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 外键
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'), nullable=False, comment='房源 ID')
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), comment='房间 ID（合租时填写）')
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, comment='租客 ID')
    
    # 索引
    __table_args__ = (
        db.Index('idx_contracts_house_id', 'house_id'),
        db.Index('idx_contracts_room_id', 'room_id'),
        db.Index('idx_contracts_tenant_id', 'tenant_id'),
        db.Index('idx_contracts_status', 'status'),
        db.Index('idx_contracts_deposit_status', 'deposit_status'),
        db.Index('idx_contracts_dates', 'start_date', 'end_date'),
        # P2-1: 性能优化索引
        db.Index('idx_contract_status_date', 'status', 'created_at'),  # 按状态筛选并按创建时间排序
        db.Index('idx_contract_tenant_status', 'tenant_id', 'status'),  # 按租客查询合同状态
    )
    
    # 关系 - 使用 back_populates 避免与 Tenant 模型冲突
    tenant_rel = db.relationship('Tenant', back_populates='contracts', lazy='joined')
    payments = db.relationship('Payment', back_populates='contract_rel', lazy='selectin')
    # house 关系由 House.contracts 的 backref='house' 自动创建
    # room 关系由 Room 的 backref 自动创建
    # 原合同关系（续签时使用）
    original_contract = db.relationship('Contract', remote_side='Contract.id', foreign_keys=[original_contract_id], lazy='select')
    
    # 押金状态常量
    DEPOSIT_STATUS = {
        'pending': '待支付',
        'paid': '已支付',
        'transferred': '已转移',
        'refunded': '已退款'
    }
    
    @classmethod
    def generate_contract_no(cls):
        """生成合同编号"""
        import uuid
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_id = uuid.uuid4().hex[:8].upper()
        return f'HT{timestamp}{unique_id}'
    
    def is_expired(self):
        """检查合同是否已过期"""
        return date.today() > self.end_date
    
    def is_expiring_soon(self, days=30):
        """检查合同是否即将到期"""
        from datetime import timedelta
        expiring_date = self.end_date - timedelta(days=days)
        return date.today() >= expiring_date and not self.is_expired()
    
    def get_days_until_expiry(self):
        """获取距离到期天数"""
        from datetime import timedelta
        delta = self.end_date - date.today()
        return delta.days
    
    def update_deposit_status(self, new_status: str):
        """
        更新押金状态
        
        Args:
            new_status: 新的押金状态 (pending/paid/transferred/refunded)
            
        Raises:
            ValueError: 状态转换不合法时抛出
        """
        valid_transitions = {
            'pending': ['paid', 'refunded'],  # 待支付可以转为已支付或已退款（押金为0的情况）
            'paid': ['transferred', 'refunded'],  # 已支付可以转为已转移或已退款
            'transferred': [],  # 已转移不能再改变
            'refunded': []  # 已退款不能再改变
        }
        
        if new_status not in self.DEPOSIT_STATUS:
            raise ValueError(f"无效的押金状态: {new_status}")
        
        if new_status not in valid_transitions.get(self.deposit_status, []):
            raise ValueError(
                f"押金状态不能从 '{self.DEPOSIT_STATUS.get(self.deposit_status)}' "
                f"转换为 '{self.DEPOSIT_STATUS.get(new_status)}'"
            )
        
        self.deposit_status = new_status
    
    def is_deposit_paid(self):
        """检查押金是否已支付"""
        return self.deposit_status in ['paid', 'transferred']
    
    def can_transfer_deposit(self):
        """检查押金是否可以转移（用于续签）"""
        return self.deposit_status == 'paid' and self.deposit_amount > 0
    
    def calculate_total_rent(self):
        """计算合同期内的总租金"""
        # 计算租赁月数
        months = (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
        # 如果有剩余天数，按天计算
        remaining_days = (self.end_date.day - self.start_date.day)
        if remaining_days > 0:
            daily_rent = self.rent_amount / 30
            return months * self.rent_amount + remaining_days * daily_rent
        return months * self.rent_amount
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        # 安全访问 house 关系
        try:
            if self.house:
                data['house_title'] = self.house.title
                data['house_address'] = self.house.address
                # 从房源获取房东信息
                if hasattr(self.house, 'owner') and self.house.owner:
                    data['landlord_name'] = self.house.owner.username
                    data['landlord_id'] = self.house.owner_id
        except Exception:
            pass
        # 安全访问 room 关系
        try:
            if self.room:
                data['room_number'] = self.room.room_number
                data['room_name'] = self.room.room_name
                data['room_area'] = self.room.area
            elif self.house:
                data['room_area'] = self.house.area
        except Exception:
            pass
        # 安全访问 tenant_rel 关系
        try:
            if self.tenant_rel:
                data['tenant_name'] = self.tenant_rel.name
                data['tenant_phone'] = self.tenant_rel.phone
        except Exception:
            pass
        # 安全计算过期状态
        try:
            data['is_expired'] = self.is_expired()
            data['is_expiring_soon'] = self.is_expiring_soon()
            data['days_until_expiry'] = self.get_days_until_expiry()
            data['total_rent'] = self.calculate_total_rent()
        except Exception:
            data['is_expired'] = False
            data['is_expiring_soon'] = False
            data['days_until_expiry'] = 0
            data['total_rent'] = 0
        # 添加押金状态信息
        data['deposit_status_name'] = self.DEPOSIT_STATUS.get(self.deposit_status, self.deposit_status)
        # 添加原合同信息
        if self.original_contract_id:
            data['is_renewal'] = True
            try:
                if self.original_contract:
                    data['original_contract_no'] = self.original_contract.contract_no
            except Exception:
                pass
        else:
            data['is_renewal'] = False
        return data
    
    def get_cascade_relations(self):
        """
        获取需要级联处理的关系定义
        
        合同删除规则：
        - 如果有未完成的支付记录（pending/partial），不允许删除
        - 支付记录可以级联软删除（仅已完成/已取消状态）
        """
        from .payment import Payment
        
        return {
            'payments': {
                'model': Payment,
                'cascade_delete': True,
                'validate_not_empty': False,
                'error_message': '关联的支付记录'
            }
        }
    
    def validate_delete(self):
        """
        验证是否可以删除合同
        
        特殊规则：
        - 如果是活跃合同（active），不允许删除
        - 如果有未完成的支付记录（pending/partial），不允许删除
        
        Returns:
            Tuple[bool, List[str]]: (是否可以删除, 错误消息列表)
        """
        # 先调用父类的基础验证
        can_delete, errors = super().validate_delete()
        
        # 检查是否是活跃合同
        if self.status == 'active':
            errors.append('活跃合同无法删除，请先终止合同')
            can_delete = False
        
        # 检查是否有未完成的支付记录
        from .payment import Payment
        pending_payments = self.payments.filter(
            Payment.status.in_(['pending', 'partial', 'overdue'])
        ).count()
        
        if pending_payments > 0:
            errors.append(f'存在 {pending_payments} 个未完成的支付记录，无法删除')
            can_delete = False
        
        return can_delete, errors
    
    def check_version(self, expected_version: int) -> bool:
        """
        检查版本号是否匹配
        
        Args:
            expected_version: 期望的版本号
            
        Returns:
            bool: 版本号是否匹配
        """
        return self.version == expected_version
    
    def increment_version(self) -> int:
        """
        递增版本号
        
        Returns:
            int: 新的版本号
        """
        self.version = (self.version or 0) + 1
        return self.version
    
    @classmethod
    def update_with_optimistic_lock(
        cls,
        contract_id: int,
        expected_version: int,
        update_data: dict
    ) -> 'Contract':
        """
        使用乐观锁更新合同
        
        Args:
            contract_id: 合同 ID
            expected_version: 期望的版本号
            update_data: 要更新的数据字典
            
        Returns:
            Contract: 更新后的合同对象
            
        Raises:
            OptimisticLockError: 版本冲突时抛出
        """
        contract = cls.query.get(contract_id)
        if not contract:
            raise ValueError(f"合同不存在: {contract_id}")
        
        if not contract.check_version(expected_version):
            raise OptimisticLockError(
                f"合同版本冲突：期望版本 {expected_version}，实际版本 {contract.version}"
            )
        
        # 更新数据
        for key, value in update_data.items():
            if hasattr(contract, key) and key not in ['id', 'contract_no', 'version']:
                setattr(contract, key, value)
        
        # 递增版本号
        contract.increment_version()
        
        return contract
    
    def __repr__(self):
        return f'<Contract {self.contract_no}>'


# ==================== 事件监听器 ====================

@event.listens_for(Contract, 'after_update')
def handle_contract_status_change(mapper, connection, target):
    """
    合同状态变更后的级联处理
    
    当合同状态变为 'terminated' 或 'expired' 时：
    自动取消所有未支付的支付记录（状态为 'pending'）
    
    注意：租客状态更新在路由层处理，避免 session flush 问题
    
    Args:
        mapper: SQLAlchemy mapper 对象
        connection: 数据库连接对象
        target: 被更新的 Contract 实例
    """
    if target.status in ['terminated', 'expired']:
        from .payment import Payment
        
        cancel_reason = f'[系统自动取消] 合同已{target.status}，支付记录自动取消'
        
        connection.execute(
            Payment.__table__.update()
            .where(Payment.__table__.c.contract_id == target.id)
            .where(Payment.__table__.c.status == 'pending')
            .values(
                status='cancelled',
                remark=case(
                    (Payment.__table__.c.remark.is_(None), cancel_reason),
                    (Payment.__table__.c.remark == '', cancel_reason),
                    else_=Payment.__table__.c.remark + '\n' + cancel_reason
                )
            )
        )
