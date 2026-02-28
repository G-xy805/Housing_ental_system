"""
基础模型类
"""
from datetime import datetime
from app import db


class BaseModel(db.Model):
    """基础模型类，提供通用字段和方法"""
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    
    def to_dict(self):
        """转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            result[column.name] = value
        return result
    
    def save(self):
        """保存对象到数据库"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """从数据库删除对象"""
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'
