"""
备份设置模型

用于持久化存储备份相关配置，确保应用重启后设置不丢失
"""
from datetime import datetime
from app import db
from app.models.base import BaseModel


class BackupSettings(BaseModel):
    """
    备份设置模型
    
    存储备份系统的配置信息：
    - 自动备份开关
    - 备份频率
    - 备份时间
    - 保留天数
    - 加密和压缩设置
    """
    
    __tablename__ = 'backup_settings'
    
    # 主键，使用固定ID确保只有一条记录
    id = db.Column(db.Integer, primary_key=True, default=1)
    
    # 自动备份设置
    enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用自动备份')
    frequency = db.Column(db.String(20), default='daily', nullable=False, comment='备份频率: daily/weekly/monthly')
    backup_time = db.Column(db.String(10), default='02:00', nullable=False, comment='备份时间 HH:MM')
    weekday = db.Column(db.Integer, default=1, nullable=True, comment='周几备份 (0=周一)')
    day_of_month = db.Column(db.Integer, default=1, nullable=True, comment='每月几号备份')
    
    # 保留设置
    keep_count = db.Column(db.Integer, default=30, nullable=False, comment='保留备份数量')
    retention_days = db.Column(db.Integer, default=30, nullable=False, comment='保留天数')
    
    # 备份内容设置
    backup_type = db.Column(db.String(20), default='full', nullable=False, comment='备份类型: full/incremental')
    include_uploads = db.Column(db.Boolean, default=True, nullable=False, comment='是否包含上传文件')
    
    # 加密压缩设置
    encryption_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用加密')
    compression_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用压缩')
    
    # 告警设置
    alert_enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用告警')
    alert_email = db.Column(db.String(100), nullable=True, comment='告警邮箱')
    
    # 更新时间
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    __table_args__ = (
        db.Index('idx_backup_settings_id', 'id'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'enabled': self.enabled,
            'frequency': self.frequency,
            'backup_time': self.backup_time,
            'weekday': self.weekday,
            'day_of_month': self.day_of_month,
            'keep_count': self.keep_count,
            'retention_days': self.retention_days,
            'backup_type': self.backup_type,
            'include_uploads': self.include_uploads,
            'encryption_enabled': self.encryption_enabled,
            'compression_enabled': self.compression_enabled,
            'alert_enabled': self.alert_enabled,
            'alert_email': self.alert_email,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
    
    @classmethod
    def get_settings(cls):
        """
        获取备份设置，如果不存在则创建默认设置
        
        Returns:
            BackupSettings: 备份设置实例
        """
        settings = cls.query.filter_by(id=1).first()
        
        if not settings:
            settings = cls(
                id=1,
                enabled=True,
                frequency='daily',
                backup_time='02:00',
                weekday=1,
                day_of_month=1,
                keep_count=30,
                retention_days=30,
                backup_type='full',
                include_uploads=True,
                encryption_enabled=True,
                compression_enabled=True,
                alert_enabled=True
            )
            db.session.add(settings)
            db.session.commit()
        
        return settings
    
    @classmethod
    def update_settings(cls, data: dict):
        """
        更新备份设置
        
        Args:
            data: 要更新的数据字典
            
        Returns:
            BackupSettings: 更新后的设置实例
        """
        settings = cls.get_settings()
        
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.updated_at = datetime.now()
        db.session.commit()
        
        return settings
    
    def __repr__(self):
        return f'<BackupSettings enabled={self.enabled} frequency={self.frequency} time={self.backup_time}>'
