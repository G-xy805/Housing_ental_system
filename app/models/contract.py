"""
租赁合同模型
"""
from datetime import datetime, date
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
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='房东 ID')
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
    payments = db.relationship('Payment', backref='contract', lazy='dynamic', cascade='all, delete-orphan')
    
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
        if self.room:
            data['room_number'] = self.room.room_number
            data['room_name'] = self.room.name
        if self.tenant_rel:
            data['tenant_name'] = self.tenant_rel.name
            data['tenant_phone'] = self.tenant_rel.phone
        if self.landlord:
            data['landlord_name'] = self.landlord.username
        data['is_expired'] = self.is_expired()
        data['is_expiring_soon'] = self.is_expiring_soon()
        data['days_until_expiry'] = self.get_days_until_expiry()
        data['total_rent'] = self.calculate_total_rent()
        return data
    
    def __repr__(self):
        return f'<Contract {self.contract_no}>'
