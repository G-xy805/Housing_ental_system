"""
多媒体文件模型
"""
import os
from .base import db, BaseModel


class Media(BaseModel):
    """
    多媒体文件模型
    
    用于管理房源的图片和视频文件
    支持文件类型分类和排序
    """
    
    __tablename__ = 'media'
    
    # 文件信息
    file_name = db.Column(db.String(255), nullable=False, comment='原始文件名')
    file_path = db.Column(db.String(500), nullable=False, comment='文件存储路径')
    file_url = db.Column(db.String(500), comment='文件访问 URL')
    
    # 文件类型：image-图片，video-视频，document-文档
    file_type = db.Column(db.String(20), nullable=False, default='image', comment='文件类型')
    
    # 文件 MIME 类型
    mime_type = db.Column(db.String(100), comment='文件 MIME 类型')
    
    # 文件大小（字节）
    file_size = db.Column(db.Integer, comment='文件大小（字节）')
    
    # 文件描述
    description = db.Column(db.String(255), comment='文件描述')
    
    # 排序
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    
    # 是否为封面
    is_cover = db.Column(db.Boolean, default=False, comment='是否为封面图片')
    
    # 外键
    house_id = db.Column(db.Integer, db.ForeignKey('houses.id'), nullable=True, comment='房源 ID')
    
    # 上传人
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='上传人 ID')
    
    # 索引
    __table_args__ = (
        db.Index('idx_media_house_id', 'house_id'),
        db.Index('idx_media_file_type', 'file_type'),
        db.Index('idx_media_is_cover', 'is_cover'),
    )
    
    # 关系
    uploader = db.relationship('User', foreign_keys=[uploaded_by])
    
    # 允许的 MIME 类型映射
    ALLOWED_MIME_TYPES = {
        'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        'video': ['video/mp4', 'video/quicktime', 'video/x-msvideo'],
        'document': ['application/pdf', 'application/msword', 
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                     'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    }
    
    @classmethod
    def get_file_type(cls, mime_type):
        """根据 MIME 类型判断文件类型"""
        for file_type, mime_types in cls.ALLOWED_MIME_TYPES.items():
            if mime_type in mime_types:
                return file_type
        return None
    
    @classmethod
    def is_allowed_type(cls, mime_type):
        """检查 MIME 类型是否允许"""
        return cls.get_file_type(mime_type) is not None
    
    def get_file_size_formatted(self):
        """获取格式化后的文件大小"""
        if not self.file_size:
            return '0 B'
        
        size_units = ['B', 'KB', 'MB', 'GB']
        size = self.file_size
        unit_index = 0
        
        while size >= 1024 and unit_index < len(size_units) - 1:
            size /= 1024
            unit_index += 1
        
        return f'{size:.2f} {size_units[unit_index]}'
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data['file_size_formatted'] = self.get_file_size_formatted()
        if self.uploader:
            data['uploader_name'] = self.uploader.username
        return data
    
    def __repr__(self):
        return f'<Media {self.file_name}>'
