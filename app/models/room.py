"""
房间模型（支持合租）
"""
from .base import db, BaseModel


class Room(BaseModel):
    """
    房间模型
    
    用于支持合租场景，一个房源可以包含多个房间
    每个房间可以独立出租，状态独立管理
    """
    
    __tablename__ = 'rooms'
    
    # 房间编号（在同一房源内唯一）
    room_number = db.Column(db.String(20), nullable=False, comment='房间编号')
    
    # 房间信息
    name = db.Column(db.String(50), comment='房间名称（如：主卧、次卧 A）')
    description = db.Column(db.Text, comment='房间描述')
    
    # 房间属性
    area = db.Column(db.Float, comment='房间面积（平方米）')
    floor = db.Column(db.String(20), comment='楼层')
    direction = db.Column(db.String(20), comment='朝向（南/北/东/西）')
    
    # 租金信息
    rent_price = db.Column(db.Float, nullable=False, comment='房间租金（元/月）')
    deposit = db.Column(db.Float, default=0, comment='押金（元）')
    
    # 配套设施（JSON 格式）
    facilities = db.Column(db.JSON, comment='房间配套设施，如：{"bed": true, "desk": true, "ac": true}')
    
    # 房间状态：available-空闲，rented-已租，maintenance-维护中
    status = db.Column(db.String(20), default='available', comment='房间状态')
    
    # 外键
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'), nullable=False, comment='房源 ID')
    
    # 索引
    __table_args__ = (
        db.Index('idx_rooms_house_id', 'house_id'),
        db.Index('idx_rooms_status', 'status'),
        db.Index('idx_rooms_house_number', 'house_id', 'room_number', unique=True),
    )
    
    # 关系
    contracts = db.relationship('Contract', backref='room', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        # 添加room_no字段，兼容前端使用
        data['room_no'] = data.get('room_number', '')
        if self.house:
            data['house_title'] = self.house.title
            data['house_address'] = self.house.address
        return data
    
    def __repr__(self):
        return f'<Room {self.house_id}-{self.room_number}>'
