"""
平台与房东合同模型
"""
from datetime import datetime, date
from .base import db, BaseModel


class LandlordContract(BaseModel):
    """
    平台与房东合同模型
    
    用于管理平台与房东之间的合作合同
    一个合同可以关联房东的多个房源
    """
    
    __tablename__ = 'landlord_contracts'
    
    # 合同编号（自动生成）
    contract_no = db.Column(db.String(50), unique=True, nullable=False, comment='合同编号')
    
    # 合同信息
    title = db.Column(db.String(100), nullable=False, comment='合同标题')
    description = db.Column(db.Text, comment='合同描述')
    
    # 合同期限
    start_date = db.Column(db.Date, nullable=False, comment='开始日期')
    end_date = db.Column(db.Date, nullable=False, comment='结束日期')
    
    # 金额信息
    contract_amount = db.Column(db.Float, nullable=False, comment='承包总金额（元）')
    service_fee_rate = db.Column(db.Float, nullable=False, comment='服务费率（%）')
    minimum_fee = db.Column(db.Float, comment='最低服务费（元）')
    payment_cycle = db.Column(db.Integer, default=1, comment='付款周期（月数）')
    
    # 合同状态：draft-草稿，active-生效中，expired-已过期，terminated-已终止
    status = db.Column(db.String(20), default='draft', comment='合同状态')
    
    # 合同文件
    contract_file = db.Column(db.String(255), comment='合同文件路径')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 外键：关联房东
    landlord_id = db.Column(db.Integer, db.ForeignKey('landlords.id'), nullable=False, comment='房东 ID')
    
    # 关联的房源 ID 列表（JSON 格式）
    house_ids = db.Column(db.JSON, default=[], comment='承包的房源 ID 列表')
    
    # 索引
    __table_args__ = (
        db.Index('idx_landlord_contracts_landlord_id', 'landlord_id'),
        db.Index('idx_landlord_contracts_status', 'status'),
        db.Index('idx_landlord_contracts_dates', 'start_date', 'end_date'),
    )
    
    # 关系
    landlord = db.relationship('Landlord', backref='contracts', lazy='joined')
    
    @classmethod
    def generate_contract_no(cls):
        """
        生成合同编号
        格式：LC + 年月日 + 4位随机数
        """
        import random
        prefix = 'LC'
        date_part = datetime.now().strftime('%Y%m%d')
        random_part = str(random.randint(1000, 9999))
        return f"{prefix}{date_part}{random_part}"
    
    def is_expired(self):
        """
        检查合同是否过期
        """
        return date.today() > self.end_date
    
    def is_expiring_soon(self, days=30):
        """
        检查合同是否即将到期
        """
        from datetime import timedelta
        return (self.end_date - date.today()).days <= days and date.today() <= self.end_date
    
    def get_days_until_expiry(self):
        """
        获取距离到期天数
        """
        from datetime import timedelta
        if date.today() > self.end_date:
            return 0
        return (self.end_date - date.today()).days
    
    def calculate_contract_term(self):
        """
        计算合同期限（月数）
        """
        from datetime import timedelta
        days = (self.end_date - self.start_date).days
        return round(days / 30, 1)
    
    def calculate_service_fee(self):
        """
        计算服务费
        基于合同金额和服务费率，如果设置了最低服务费则取较大值
        
        Returns:
            float: 服务费金额
        """
        if not self.contract_amount or self.contract_amount <= 0:
            return 0.0
        
        # 计算服务费
        service_fee = self.contract_amount * (self.service_fee_rate / 100)
        
        # 如果有最低服务费，取较大值
        if self.minimum_fee and self.minimum_fee > 0:
            service_fee = max(service_fee, self.minimum_fee)
        
        return round(service_fee, 2)
    
    def get_houses(self):
        """
        获取合同关联的所有房源
        
        Returns:
            list: 房源对象列表
        """
        from .house import House
        if not self.house_ids:
            return []
        return House.query.filter(House.id.in_(self.house_ids)).all()
    
    def to_dict(self):
        """
        转换为字典
        包含房东信息和关联房源信息
        """
        from .house import House
        
        # 获取关联房源信息
        houses_info = []
        if self.house_ids:
            houses = House.query.filter(House.id.in_(self.house_ids)).all()
            for house in houses:
                houses_info.append({
                    'id': house.id,
                    'title': house.title,
                    'address': house.address,
                    'rental_type': house.rental_type,
                    'rent_price': house.rent_price
                })
        
        return {
            'id': self.id,
            'contract_no': self.contract_no,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'contract_amount': self.contract_amount,
            'service_fee_rate': self.service_fee_rate,
            'minimum_fee': self.minimum_fee,
            'payment_cycle': self.payment_cycle,
            'status': self.status,
            'contract_file': self.contract_file,
            'remark': self.remark,
            'landlord_id': self.landlord_id,
            'house_ids': self.house_ids or [],
            'landlord': {
                'id': self.landlord.id,
                'name': self.landlord.name,
                'phone': self.landlord.phone,
                'status': self.landlord.status
            } if self.landlord else None,
            'houses': houses_info,
            'contract_term_months': self.calculate_contract_term(),
            'service_fee': self.calculate_service_fee(),
            'is_expired': self.is_expired(),
            'days_until_expiry': self.get_days_until_expiry(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }