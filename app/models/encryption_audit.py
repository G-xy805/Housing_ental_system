"""
加密访问审计日志模型
记录所有敏感数据的加密和解密操作，用于安全审计和合规性检查
"""
from datetime import datetime
from .base import db, BaseModel


class EncryptionAuditLog(BaseModel):
    """
    加密访问审计日志模型
    
    记录所有加密/解密操作的详细信息，包括：
    - 操作类型（加密/解密）
    - 操作的字段和记录
    - 使用的密钥 ID
    - 操作用户和 IP 地址
    - 操作结果（成功/失败）
    """
    
    __tablename__ = 'encryption_audit_logs'
    
    # 操作类型：encrypt-加密，decrypt-解密
    operation = db.Column(db.String(20), nullable=False, comment='操作类型')
    
    # 字段信息
    field_name = db.Column(db.String(100), nullable=False, comment='字段名称')
    model_name = db.Column(db.String(100), nullable=False, comment='模型名称')
    record_id = db.Column(db.Integer, nullable=False, comment='记录 ID')
    
    # 密钥信息
    key_id = db.Column(db.String(100), nullable=False, comment='使用的密钥 ID')
    
    # 操作用户信息
    user_id = db.Column(db.Integer, comment='操作用户 ID')
    ip_address = db.Column(db.String(50), comment='操作 IP 地址')
    
    # 操作结果
    success = db.Column(db.Boolean, default=True, comment='操作是否成功')
    error_message = db.Column(db.Text, comment='错误信息（如果失败）')
    
    # 时间戳
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='操作时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_encryption_audit_timestamp', 'timestamp'),
        db.Index('idx_encryption_audit_operation', 'operation'),
        db.Index('idx_encryption_audit_model_record', 'model_name', 'record_id'),
        db.Index('idx_encryption_audit_user', 'user_id'),
        db.Index('idx_encryption_audit_key', 'key_id'),
    )
    
    def to_dict(self):
        """
        转换为字典
        
        Returns:
            dict: 审计日志信息字典
        """
        data = super().to_dict()
        
        # 添加操作类型中文名称
        operation_names = {
            'encrypt': '加密',
            'decrypt': '解密'
        }
        data['operation_name'] = operation_names.get(self.operation, self.operation)
        
        # 格式化时间戳
        if self.timestamp:
            data['timestamp'] = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        return data
    
    @classmethod
    def get_logs_by_record(cls, model_name: str, record_id: int, limit: int = 100):
        """
        获取指定记录的审计日志
        
        Args:
            model_name: 模型名称
            record_id: 记录 ID
            limit: 返回记录数量限制
            
        Returns:
            list: 审计日志列表
        """
        return cls.query.filter_by(
            model_name=model_name,
            record_id=record_id
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_logs_by_user(cls, user_id: int, limit: int = 100):
        """
        获取指定用户的审计日志
        
        Args:
            user_id: 用户 ID
            limit: 返回记录数量限制
            
        Returns:
            list: 审计日志列表
        """
        return cls.query.filter_by(
            user_id=user_id
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_logs_by_key(cls, key_id: str, limit: int = 100):
        """
        获取使用指定密钥的审计日志
        
        Args:
            key_id: 密钥 ID
            limit: 返回记录数量限制
            
        Returns:
            list: 审计日志列表
        """
        return cls.query.filter_by(
            key_id=key_id
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_failed_operations(cls, limit: int = 100):
        """
        获取失败的加密操作日志
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            list: 失败的审计日志列表
        """
        return cls.query.filter_by(
            success=False
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_statistics(cls, start_date: datetime = None, end_date: datetime = None):
        """
        获取加密操作统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 统计信息
        """
        query = cls.query
        
        if start_date:
            query = query.filter(cls.timestamp >= start_date)
        if end_date:
            query = query.filter(cls.timestamp <= end_date)
        
        # 总操作数
        total_operations = query.count()
        
        # 加密操作数
        encrypt_count = query.filter(cls.operation == 'encrypt').count()
        
        # 解密操作数
        decrypt_count = query.filter(cls.operation == 'decrypt').count()
        
        # 成功操作数
        success_count = query.filter(cls.success == True).count()
        
        # 失败操作数
        failed_count = query.filter(cls.success == False).count()
        
        # 按模型统计
        model_stats = db.session.query(
            cls.model_name,
            db.func.count(cls.id).label('count')
        ).filter(
            cls.timestamp >= start_date if start_date else True,
            cls.timestamp <= end_date if end_date else True
        ).group_by(cls.model_name).all()
        
        # 按字段统计
        field_stats = db.session.query(
            cls.field_name,
            db.func.count(cls.id).label('count')
        ).filter(
            cls.timestamp >= start_date if start_date else True,
            cls.timestamp <= end_date if end_date else True
        ).group_by(cls.field_name).all()
        
        return {
            'total_operations': total_operations,
            'encrypt_count': encrypt_count,
            'decrypt_count': decrypt_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'success_rate': (success_count / total_operations * 100) if total_operations > 0 else 0,
            'model_statistics': [{'model_name': stat[0], 'count': stat[1]} for stat in model_stats],
            'field_statistics': [{'field_name': stat[0], 'count': stat[1]} for stat in field_stats]
        }
    
    def __repr__(self):
        return f'<EncryptionAuditLog {self.operation} {self.model_name}.{self.field_name}>'
