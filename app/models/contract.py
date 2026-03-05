"""
租赁合同模型
"""
from datetime import datetime, date
from sqlalchemy import event, case
from .base import db, BaseModel


class Contract(BaseModel):
    """
    租赁合同模型
    
    支持整租和合租合同
    合租合同可关联到具体房间
    """
    
    __tablename__ = 'contracts'
    
    # 合同编号（自动生成）
    contract_no = db.Column(db.String(50), unique=True, nullable=False, comment='合同编号')
    
    # 合同信息
    title = db.Column(db.String(100), nullable=False, comment='合同标题')
    description = db.Column(db.Text, comment='合同描述')
    
    # 租赁信息
    start_date = db.Column(db.Date, nullable=False, comment='起租日期')
    end_date = db.Column(db.Date, nullable=False, comment='结束日期')
    rent_amount = db.Column(db.Float, nullable=False, comment='租金金额（元/月）')
    deposit_amount = db.Column(db.Float, nullable=False, comment='押金金额（元）')
    
    # 付款方式：月付、季付、半年付、年付
    payment_type = db.Column(db.String(20), default='月付', comment='付款类型')
    payment_cycle = db.Column(db.Integer, default=1, comment='付款周期（月数）')
    
    # 合同状态：draft-草稿，active-生效中，expired-已过期，terminated-已终止
    status = db.Column(db.String(20), default='draft', comment='合同状态')
    
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
        db.Index('idx_contracts_dates', 'start_date', 'end_date'),
    )
    
    # 关系 - 使用 back_populates 避免与 Tenant 模型冲突
    tenant_rel = db.relationship('Tenant', back_populates='contracts', lazy='joined')
    payments = db.relationship('Payment', back_populates='contract_rel', lazy='selectin')
    
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
        if self.house:
            data['house_title'] = self.house.title
            data['house_address'] = self.house.address
            # 从房源获取房东信息
            if self.house.owner:
                data['landlord_name'] = self.house.owner.username
                data['landlord_id'] = self.house.owner_id
        if self.room:
            data['room_number'] = self.room.room_number
            data['room_name'] = self.room.name
            data['room_area'] = self.room.area
        elif self.house:
            data['room_area'] = self.house.area
        if self.tenant_rel:
            data['tenant_name'] = self.tenant_rel.name
            data['tenant_phone'] = self.tenant_rel.phone
        data['is_expired'] = self.is_expired()
        data['is_expiring_soon'] = self.is_expiring_soon()
        data['days_until_expiry'] = self.get_days_until_expiry()
        data['total_rent'] = self.calculate_total_rent()
        return data
    
    def __repr__(self):
        return f'<Contract {self.contract_no}>'


# ==================== 事件监听器 ====================

@event.listens_for(Contract, 'after_update')
def handle_contract_status_change(mapper, connection, target):
    """
    合同状态变更后的级联处理
    
    当合同状态变为 'terminated' 或 'expired' 时：
    1. 自动取消所有未支付的支付记录（状态为 'pending'）
    2. 将这些支付记录的状态标记为 'cancelled'
    
    Args:
        mapper: SQLAlchemy mapper 对象
        connection: 数据库连接对象
        target: 被更新的 Contract 实例
    """
    # 检查状态是否变更为 terminated 或 expired
    if target.status in ['terminated', 'expired']:
        # 导入 Payment 模型（避免循环导入）
        from .payment import Payment
        
        # 构建取消原因说明
        cancel_reason = f'[系统自动取消] 合同已{target.status}，支付记录自动取消'
        
        # 使用 connection 执行批量更新，提高性能
        # 只更新状态为 'pending' 的支付记录
        # 使用 CASE WHEN 处理备注字段，避免 NULL 拼接问题
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
