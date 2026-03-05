"""
备份记录模型

用于在数据库中记录备份历史，提供持久化存储和查询功能
"""
from datetime import datetime
from app import db
from app.models.base import BaseModel


class BackupRecord(BaseModel):
    """
    备份记录模型
    
    记录每次备份的详细信息，包括：
    - 备份类型（完整/增量）
    - 备份状态（成功/失败/进行中）
    - 备份文件信息
    - 备份耗时
    - 错误信息
    """
    
    __tablename__ = 'backup_records'
    
    # 基本信息
    backup_id = db.Column(db.String(50), unique=True, nullable=False, comment='备份ID')
    backup_type = db.Column(db.String(20), nullable=False, comment='备份类型: full/incremental')
    status = db.Column(db.String(20), nullable=False, default='running', comment='状态: running/success/failed')
    
    # 时间信息
    start_time = db.Column(db.DateTime, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=True, comment='结束时间')
    duration = db.Column(db.Float, nullable=True, comment='耗时（秒）')
    
    # 文件信息
    filename = db.Column(db.String(255), nullable=True, comment='备份文件名')
    file_path = db.Column(db.String(500), nullable=True, comment='备份文件路径')
    file_size = db.Column(db.BigInteger, nullable=True, comment='文件大小（字节）')
    file_hash = db.Column(db.String(64), nullable=True, comment='文件哈希值')
    
    # 加密和压缩信息
    encrypted = db.Column(db.Boolean, default=False, comment='是否加密')
    compressed = db.Column(db.Boolean, default=False, comment='是否压缩')
    
    # 备份内容
    includes_uploads = db.Column(db.Boolean, default=False, comment='是否包含上传文件')
    database_size = db.Column(db.BigInteger, nullable=True, comment='数据库大小（字节）')
    uploads_size = db.Column(db.BigInteger, nullable=True, comment='上传文件大小（字节）')
    
    # 操作信息
    backup_by = db.Column(db.String(100), nullable=True, comment='备份执行人')
    backup_method = db.Column(db.String(20), nullable=True, comment='备份方式: manual/auto/scheduled')
    trigger = db.Column(db.String(50), nullable=True, comment='触发方式')
    
    # 错误信息
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    error_traceback = db.Column(db.Text, nullable=True, comment='错误堆栈')
    
    # 元数据
    remark = db.Column(db.Text, nullable=True, comment='备注')
    backup_metadata = db.Column(db.JSON, nullable=True, comment='备份元数据')
    
    # 索引
    __table_args__ = (
        db.Index('idx_backup_records_backup_id', 'backup_id'),
        db.Index('idx_backup_records_status', 'status'),
        db.Index('idx_backup_records_backup_type', 'backup_type'),
        db.Index('idx_backup_records_start_time', 'start_time'),
        db.Index('idx_backup_records_backup_by', 'backup_by'),
    )
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        
        # 添加计算字段
        if self.file_size:
            data['file_size_mb'] = round(self.file_size / (1024 * 1024), 2)
        
        if self.database_size:
            data['database_size_mb'] = round(self.database_size / (1024 * 1024), 2)
        
        if self.uploads_size:
            data['uploads_size_mb'] = round(self.uploads_size / (1024 * 1024), 2)
        
        # 格式化时间
        if self.start_time:
            data['start_time'] = self.start_time.strftime('%Y-%m-%d %H:%M:%S')
        
        if self.end_time:
            data['end_time'] = self.end_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 添加状态描述
        status_map = {
            'running': '进行中',
            'success': '成功',
            'failed': '失败'
        }
        data['status_text'] = status_map.get(self.status, '未知')
        
        # 添加类型描述
        type_map = {
            'full': '完整备份',
            'incremental': '增量备份'
        }
        data['backup_type_text'] = type_map.get(self.backup_type, '未知')
        
        return data
    
    @classmethod
    def create_from_backup_info(cls, backup_info: dict, backup_id: str, backup_by: str = 'system'):
        """
        从备份信息创建记录
        
        Args:
            backup_info: 备份信息字典
            backup_id: 备份ID
            backup_by: 备份执行人
        
        Returns:
            BackupRecord: 备份记录实例
        """
        record = cls(
            backup_id=backup_id,
            backup_type=backup_info.get('backup_type', 'full'),
            status='success',
            start_time=datetime.now(),
            end_time=datetime.now(),
            filename=backup_info.get('filename'),
            file_path=backup_info.get('backup_path'),
            file_size=backup_info.get('file_size'),
            file_hash=backup_info.get('file_hash'),
            encrypted=backup_info.get('encrypted', False),
            compressed=backup_info.get('compressed', False),
            includes_uploads=backup_info.get('includes_uploads', False),
            backup_by=backup_by,
            remark=backup_info.get('remark'),
            backup_metadata=backup_info
        )
        
        return record
    
    @classmethod
    def get_latest_successful(cls, limit: int = 10):
        """
        获取最近成功的备份记录
        
        Args:
            limit: 返回数量限制
        
        Returns:
            List[BackupRecord]: 备份记录列表
        """
        return cls.query.filter(
            cls.status == 'success',
            cls.deleted_at.is_(None)
        ).order_by(cls.start_time.desc()).limit(limit).all()
    
    @classmethod
    def get_failed_backups(cls, days: int = 7):
        """
        获取最近失败的备份记录
        
        Args:
            days: 查询天数
        
        Returns:
            List[BackupRecord]: 备份记录列表
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return cls.query.filter(
            cls.status == 'failed',
            cls.start_time >= cutoff_date,
            cls.deleted_at.is_(None)
        ).order_by(cls.start_time.desc()).all()
    
    @classmethod
    def get_statistics(cls, days: int = 30):
        """
        获取备份统计信息
        
        Args:
            days: 统计天数
        
        Returns:
            Dict: 统计信息
        """
        from datetime import timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 总备份数
        total = cls.query.filter(
            cls.start_time >= cutoff_date,
            cls.deleted_at.is_(None)
        ).count()
        
        # 成功备份数
        successful = cls.query.filter(
            cls.start_time >= cutoff_date,
            cls.status == 'success',
            cls.deleted_at.is_(None)
        ).count()
        
        # 失败备份数
        failed = cls.query.filter(
            cls.start_time >= cutoff_date,
            cls.status == 'failed',
            cls.deleted_at.is_(None)
        ).count()
        
        # 平均备份大小
        avg_size = db.session.query(func.avg(cls.file_size)).filter(
            cls.start_time >= cutoff_date,
            cls.status == 'success',
            cls.deleted_at.is_(None)
        ).scalar() or 0
        
        # 总备份大小
        total_size = db.session.query(func.sum(cls.file_size)).filter(
            cls.start_time >= cutoff_date,
            cls.status == 'success',
            cls.deleted_at.is_(None)
        ).scalar() or 0
        
        # 平均备份耗时
        avg_duration = db.session.query(func.avg(cls.duration)).filter(
            cls.start_time >= cutoff_date,
            cls.status == 'success',
            cls.deleted_at.is_(None)
        ).scalar() or 0
        
        # 成功率
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            'total_backups': total,
            'successful_backups': successful,
            'failed_backups': failed,
            'success_rate': round(success_rate, 2),
            'average_size': int(avg_size),
            'average_size_mb': round(avg_size / (1024 * 1024), 2),
            'total_size': int(total_size),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'average_duration': round(avg_duration, 2),
            'period_days': days
        }
    
    def __repr__(self):
        return f'<BackupRecord {self.backup_id} - {self.status}>'
