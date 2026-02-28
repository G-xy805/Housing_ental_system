"""
房源模型
"""
from .base import db, BaseModel


class House(BaseModel):
    """
    房源模型
    
    支持整租和合租两种模式
    房源状态根据房间状态自动管理
    """
    
    __tablename__ = 'houses'
    
    # 基本信息
    title = db.Column(db.String(100), nullable=False, comment='房源标题')
    description = db.Column(db.Text, comment='房源描述')
    
    # 地址信息
    province = db.Column(db.String(50), comment='省份')
    city = db.Column(db.String(50), comment='城市')
    district = db.Column(db.String(50), comment='区县')
    address = db.Column(db.String(200), comment='详细地址')
    latitude = db.Column(db.Float, comment='纬度')
    longitude = db.Column(db.Float, comment='经度')
    
    # 房源属性
    area = db.Column(db.Float, comment='面积（平方米）')
    room_count = db.Column(db.Integer, comment='房间数')
    hall_count = db.Column(db.Integer, comment='客厅数')
    bathroom_count = db.Column(db.Integer, comment='卫生间数')
    floor = db.Column(db.String(20), comment='楼层')
    total_floors = db.Column(db.Integer, comment='总楼层')
    
    # 租金信息
    rent_price = db.Column(db.Float, nullable=False, comment='租金（元/月）')
    deposit = db.Column(db.Float, comment='押金（元）')
    payment_method = db.Column(db.String(50), default='押一付三', comment='付款方式')
    
    # 房源状态：available-空闲，rented-已租，maintenance-维护中
    # 对于合租房源，状态根据房间状态自动计算
    status = db.Column(db.String(20), default='available', comment='房源状态')
    
    # 配套设施（JSON 格式）
    facilities = db.Column(db.JSON, comment='配套设施，如：{"wifi": true, "ac": true, "heater": true}')
    
    # 图片（保留字段，兼容旧数据）
    images = db.Column(db.JSON, comment='房源图片列表')
    cover_image = db.Column(db.String(255), comment='封面图片')
    
    # 租赁类型：whole-整租，shared-合租
    rental_type = db.Column(db.String(20), default='whole', comment='租赁类型')
    
    # 外键
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='房东 ID')
    
    # 索引
    __table_args__ = (
        db.Index('idx_houses_status', 'status'),
        db.Index('idx_houses_city', 'city'),
        db.Index('idx_houses_district', 'district'),
        db.Index('idx_houses_rental_type', 'rental_type'),
        db.Index('idx_houses_owner_id', 'owner_id'),
    )
    
    # 关系
    rooms = db.relationship('Room', backref='house', lazy='dynamic', cascade='all, delete-orphan')
    contracts = db.relationship('Contract', backref='house', lazy='dynamic')
    media = db.relationship('Media', backref='house', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='Media.house_id')
    
    def update_status(self):
        """
        根据房间状态更新房源状态（用于合租模式）
        
        Returns:
            str: 更新后的状态
        """
        from .contract import Contract
        from .room import Room
        
        if self.rental_type == 'whole':
            # 整租模式，根据合同状态判断
            active_contracts = self.contracts.filter(
                Contract.status.in_(['active'])
            ).count()
            if active_contracts > 0:
                self.status = 'rented'
            else:
                self.status = 'available'
        else:
            # 合租模式，根据房间状态计算
            total_rooms = self.rooms.count()
            if total_rooms == 0:
                self.status = 'available'
                return self.status
            
            rented_rooms = self.rooms.filter(Room.status == 'rented').count()
            available_rooms = self.rooms.filter(Room.status == 'available').count()
            
            if rented_rooms == total_rooms:
                self.status = 'rented'
            elif available_rooms == total_rooms:
                self.status = 'available'
            else:
                self.status = 'partially_rented'  # 部分出租
        
        return self.status
    
    def get_room_count(self):
        """获取房间数量"""
        return self.rooms.count()
    
    def get_available_rooms(self):
        """获取空闲房间列表"""
        return self.rooms.filter(Room.status == 'available').all()
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        if self.owner:
            data['owner_name'] = self.owner.username
        # 简化处理，避免在列表查询时加载过多关联数据
        try:
            data['room_count_actual'] = self.rooms.count()
            data['available_rooms'] = []
        except:
            data['room_count_actual'] = 0
            data['available_rooms'] = []
        return data
    
    def __repr__(self):
        return f'<House {self.title}>'
