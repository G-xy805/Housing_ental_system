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
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='负责员工 ID（内部员工管理）')
    landlord_id = db.Column(db.Integer, db.ForeignKey('landlords.id'), nullable=True, comment='房东 ID（房源所有者）')
    
    # 房东联系信息
    contact_name = db.Column(db.String(50), comment='联系人姓名')
    contact_phone = db.Column(db.String(20), comment='联系电话')
    contact_wechat = db.Column(db.String(50), comment='微信号')
    
    # 索引
    __table_args__ = (
        db.Index('idx_houses_status', 'status'),
        db.Index('idx_houses_city', 'city'),
        db.Index('idx_houses_district', 'district'),
        db.Index('idx_houses_rental_type', 'rental_type'),
        db.Index('idx_houses_owner_id', 'owner_id'),
        db.Index('idx_houses_landlord_id', 'landlord_id'),
    )
    
    # 关系
    landlord_rel = db.relationship('Landlord', back_populates='houses', lazy='joined', foreign_keys=[landlord_id])
    owner = db.relationship('User', back_populates='houses', lazy='joined', foreign_keys=[owner_id])  # 负责的员工
    rooms = db.relationship('Room', backref='house', lazy='dynamic')
    contracts = db.relationship('Contract', backref='house', lazy='dynamic')
    media = db.relationship('Media', backref='house', lazy='dynamic', foreign_keys='Media.house_id')
    
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
    
    def to_dict(self, include_landlord=False, is_internal=False):
        """
        转换为字典
        
        Args:
            include_landlord: 是否包含房东信息（默认 False，用于租客接口）
                           True 时返回房东信息（用于内部接口）
            is_internal: 是否为内部接口（True 时返回完整信息，False 时过滤敏感信息）
        
        Returns:
            dict: 房源数据字典
        """
        data = super().to_dict()
        
        # 添加负责员工信息
        if self.owner:
            data['owner_name'] = self.owner.username
        
        # 添加房东信息（仅当 include_landlord=True 且 is_internal=True 时）
        if include_landlord and is_internal and self.landlord_rel:
            data['landlord'] = self.landlord_rel.to_dict(include_details=True)
            data['landlord_name'] = self.landlord_rel.name
            data['landlord_phone'] = self.landlord_rel.phone
        elif include_landlord and not is_internal:
            # 外部接口：仅显示脱敏的联系信息
            data['landlord_name'] = '平台管家'  # 不显示真实房东姓名
            data['landlord_phone'] = None  # 不显示房东电话
        
        # 添加联系信息字段（根据内部/外部接口决定是否显示）
        if is_internal:
            # 内部接口：显示完整联系信息
            data['contact_name'] = self.contact_name
            data['contact_phone'] = self.contact_phone
            data['contact_wechat'] = self.contact_wechat
        else:
            # 外部接口：脱敏处理或隐藏
            data['contact_name'] = None
            data['contact_phone'] = None
            data['contact_wechat'] = None
        
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
