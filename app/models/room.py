"""
房间模型（支持合租）
"""
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm.attributes import get_history
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
    room_name = db.Column(db.String(50), comment='房间名称（如：主卧、次卧 A）')
    description = db.Column(db.Text, comment='房间描述')
    
    # 房间属性
    area = db.Column(db.Float, comment='房间面积（平方米）')
    floor = db.Column(db.String(20), comment='楼层')
    orientation = db.Column(db.String(20), comment='朝向（南/北/东/西）')
    
    # 租金信息
    rent_price = db.Column(db.Numeric(10, 2), nullable=False, comment='房间租金（元/月）')
    deposit = db.Column(db.Numeric(10, 2), default=0, comment='押金（元）')
    payment_method = db.Column(db.String(50), default='press1_pay3', comment='付款方式')
    
    # 房间特性
    is_master = db.Column(db.Boolean, default=False, comment='是否为主卧')
    
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
    
    def get_cascade_relations(self):
        """
        获取需要级联处理的关系定义
        
        房间删除规则：
        - 如果有活跃合同（active/draft），不允许删除
        """
        from .contract import Contract
        
        return {
            'contracts': {
                'model': Contract,
                'cascade_delete': True,
                'validate_not_empty': False,
                'error_message': '关联的合同'
            }
        }
    
    def validate_delete(self):
        """
        验证是否可以删除房间
        
        特殊规则：
        - 如果有活跃合同（active/draft），不允许删除
        
        Returns:
            Tuple[bool, List[str]]: (是否可以删除, 错误消息列表)
        """
        # 先调用父类的基础验证
        can_delete, errors = super().validate_delete()
        
        # 检查是否有活跃合同
        from .contract import Contract
        active_contracts = self.contracts.filter(
            Contract.status.in_(['active', 'draft'])
        ).count()
        
        if active_contracts > 0:
            errors.append(f'存在 {active_contracts} 个活跃合同，无法删除')
            can_delete = False
        
        return can_delete, errors
    
    def __repr__(self):
        return f'<Room {self.house_id}-{self.room_number}>'


# ==================== SQLAlchemy 事件监听器 ====================

@event.listens_for(Room, 'after_update')
def on_room_status_update(mapper, connection, target):
    """
    Room 模型的 after_update 事件监听器
    
    当房间状态发生变化时，自动更新所属房源的状态
    
    Args:
        mapper: SQLAlchemy mapper 对象
        connection: 数据库连接对象
        target: Room 实例对象
    
    说明：
        1. 只在房间状态实际变化时触发更新
        2. 使用 get_history 检查状态是否真正改变
        3. 避免循环触发和性能问题
        4. 支持整租和合租两种模式
        5. 使用纯 SQL 查询避免 session flush 冲突
    """
    # 检查状态字段是否有变化
    history = get_history(target, 'status')
    
    # history 返回元组：(deleted, unchanged, added)
    # 如果 added 不为空，说明状态发生了变化
    if not history.added:
        return
    
    # 获取状态变化前后的值
    old_status = history.deleted[0] if history.deleted else None
    new_status = history.added[0]
    
    # 如果状态实际没有变化，直接返回
    if old_status == new_status:
        return
    
    # 获取关联的房源 ID
    house_id = target.house_id
    
    if not house_id:
        return
    
    try:
        # 使用纯 SQL 查询获取房源信息，避免触发 session flush
        from sqlalchemy import text
        
        # 查询房源的租赁类型
        house_result = connection.execute(
            text("SELECT rental_type FROM houses WHERE id = :house_id"),
            {'house_id': house_id}
        ).fetchone()
        
        if not house_result:
            return
        
        rental_type = house_result[0]
        
        # 整租模式：房源状态由合同决定，不在此处理
        if rental_type == 'whole':
            return
        
        # 合租模式：根据房间状态计算房源状态
        # 使用纯 SQL 查询统计房间状态
        room_stats = connection.execute(
            text("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'rented' THEN 1 ELSE 0 END) as rented,
                    SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available
                FROM rooms 
                WHERE house_id = :house_id AND is_active = 1
            """),
            {'house_id': house_id}
        ).fetchone()
        
        if not room_stats:
            return
        
        total_rooms = room_stats[0]
        rented_rooms = room_stats[1] or 0
        available_rooms = room_stats[2] or 0
        
        # 计算房源状态
        if total_rooms == 0:
            new_status = 'available'
        elif rented_rooms == total_rooms:
            new_status = 'rented'
        elif available_rooms == total_rooms:
            new_status = 'available'
        else:
            new_status = 'partially_rented'
        
        # 使用 connection 执行更新，确保在同一事务中
        connection.execute(
            text("""
                UPDATE houses 
                SET status = :status, updated_at = :updated_at 
                WHERE id = :house_id
            """),
            {'status': new_status, 'updated_at': datetime.now(), 'house_id': house_id}
        )
        
    except Exception as e:
        # 记录错误但不抛出异常，避免影响主流程
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'更新房源状态失败: {e}', exc_info=True)
