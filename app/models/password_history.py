"""
密码历史记录模型
用于防止用户重复使用最近使用过的密码
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .base import db, BaseModel


class PasswordHistory(BaseModel):
    """
    密码历史记录模型
    
    功能：
    1. 记录用户密码变更历史
    2. 防止重复使用最近 N 个密码
    3. 记录密码设置时间，用于密码过期管理
    """
    
    __tablename__ = 'password_history'
    
    # 用户ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    
    # 密码哈希
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    
    # 密码设置时间
    password_set_at = db.Column(db.DateTime, default=datetime.now, nullable=False, comment='密码设置时间')
    
    # 密码过期时间
    password_expires_at = db.Column(db.DateTime, comment='密码过期时间')
    
    # 是否已过期
    is_expired = db.Column(db.Boolean, default=False, comment='是否已过期')
    
    # 索引
    __table_args__ = (
        db.Index('idx_password_history_user_id', 'user_id'),
        db.Index('idx_password_history_password_set_at', 'password_set_at'),
        db.Index('idx_password_history_is_expired', 'is_expired'),
    )
    
    # 关系
    user = db.relationship('User', backref=db.backref('password_histories', lazy='dynamic'))
    
    @classmethod
    def add_password_history(cls, user_id: int, password: str, expires_days: int = 90) -> 'PasswordHistory':
        """
        添加密码历史记录
        
        Args:
            user_id: 用户ID
            password: 明文密码
            expires_days: 密码过期天数（默认90天）
            
        Returns:
            PasswordHistory: 密码历史记录实例
        """
        from datetime import timedelta
        
        # 计算过期时间
        expires_at = datetime.now() + timedelta(days=expires_days)
        
        # 创建密码历史记录
        password_history = cls(
            user_id=user_id,
            password_hash=generate_password_hash(password),
            password_set_at=datetime.now(),
            password_expires_at=expires_at,
            is_expired=False
        )
        
        db.session.add(password_history)
        
        return password_history
    
    @classmethod
    def check_password_in_history(cls, user_id: int, password: str, limit: int = 5) -> bool:
        """
        检查密码是否在最近的历史记录中
        
        Args:
            user_id: 用户ID
            password: 明文密码
            limit: 检查最近N个密码（默认5个）
            
        Returns:
            bool: True表示密码在历史记录中（不能使用），False表示可以使用
        """
        # 获取最近的N个密码历史记录
        # 使用子查询方式避免与 SoftDeleteQuery 的 limit 冲突
        from sqlalchemy import select
        
        # 创建查询
        query = select(cls).where(cls.user_id == user_id)\
            .order_by(cls.password_set_at.desc())\
            .limit(limit)
        
        # 执行查询
        result = db.session.execute(query)
        recent_passwords = result.scalars().all()
        
        # 检查密码是否匹配
        for ph in recent_passwords:
            if check_password_hash(ph.password_hash, password):
                return True
        
        return False
    
    @classmethod
    def cleanup_old_passwords(cls, user_id: int, keep_count: int = 5):
        """
        清理旧的密码历史记录，只保留最近的N个
        
        Args:
            user_id: 用户ID
            keep_count: 保留的记录数量（默认5个）
        """
        # 获取该用户的所有密码历史记录
        all_passwords = cls.query.filter_by(user_id=user_id)\
            .order_by(cls.password_set_at.desc())\
            .all()
        
        # 如果记录数量超过保留数量，删除旧记录
        if len(all_passwords) > keep_count:
            passwords_to_delete = all_passwords[keep_count:]
            for ph in passwords_to_delete:
                db.session.delete(ph)
    
    @classmethod
    def mark_expired_passwords(cls):
        """
        标记所有已过期的密码
        
        Returns:
            int: 标记的过期密码数量
        """
        now = datetime.now()
        
        # 查找所有未过期但已超过过期时间的密码
        expired_passwords = cls.query.filter(
            cls.is_expired == False,
            cls.password_expires_at < now
        ).all()
        
        # 标记为过期
        for ph in expired_passwords:
            ph.is_expired = True
        
        db.session.commit()
        
        return len(expired_passwords)
    
    @classmethod
    def get_user_password_age(cls, user_id: int) -> int:
        """
        获取用户当前密码的使用天数
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 密码使用天数，如果没有记录返回-1
        """
        # 获取最新的密码历史记录
        latest_password = cls.query.filter_by(user_id=user_id)\
            .order_by(cls.password_set_at.desc())\
            .first()
        
        if not latest_password:
            return -1
        
        # 计算使用天数
        delta = datetime.now() - latest_password.password_set_at
        return delta.days
    
    @classmethod
    def is_password_expired(cls, user_id: int) -> bool:
        """
        检查用户密码是否已过期
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: True表示已过期，False表示未过期
        """
        # 获取最新的密码历史记录
        latest_password = cls.query.filter_by(user_id=user_id)\
            .order_by(cls.password_set_at.desc())\
            .first()
        
        if not latest_password:
            return False
        
        # 检查是否过期
        if latest_password.is_expired:
            return True
        
        if latest_password.password_expires_at and latest_password.password_expires_at < datetime.now():
            # 自动标记为过期
            latest_password.is_expired = True
            db.session.commit()
            return True
        
        return False
    
    @classmethod
    def get_days_until_expiry(cls, user_id: int) -> int:
        """
        获取距离密码过期的天数
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 距离过期的天数，如果已过期返回负数，如果没有记录返回-1
        """
        # 获取最新的密码历史记录
        latest_password = cls.query.filter_by(user_id=user_id)\
            .order_by(cls.password_set_at.desc())\
            .first()
        
        if not latest_password or not latest_password.password_expires_at:
            return -1
        
        # 计算距离过期的天数
        delta = latest_password.password_expires_at - datetime.now()
        return delta.days
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        # 不返回密码哈希
        data.pop('password_hash', None)
        return data
    
    def __repr__(self):
        return f'<PasswordHistory user_id={self.user_id} set_at={self.password_set_at}>'
