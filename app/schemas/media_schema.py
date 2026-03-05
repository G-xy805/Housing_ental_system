"""
多媒体 Schema

提供多媒体模型的序列化和验证
"""
from marshmallow import fields, validates, ValidationError
from .base import BaseSchema, TimestampMixin


class MediaSchema(BaseSchema, TimestampMixin):
    """
    多媒体序列化 Schema
    """
    
    # 基本字段
    id = fields.Int(dump_only=True)
    file_name = fields.Str(required=True)
    file_path = fields.Str(required=True)
    file_url = fields.Str(allow_none=True)
    
    # 文件类型
    file_type = fields.Str(required=True, validate=lambda x: x in ['image', 'video', 'document'])
    mime_type = fields.Str(allow_none=True)
    
    # 文件大小
    file_size = fields.Int(allow_none=True)
    
    # 描述
    description = fields.Str(allow_none=True)
    
    # 排序
    sort_order = fields.Int(allow_none=True)
    
    # 是否为封面
    is_cover = fields.Bool(allow_none=True)
    
    # 外键
    house_id = fields.Int(allow_none=True)
    uploaded_by = fields.Int(allow_none=True)
    
    # 嵌套对象
    uploader = fields.Nested('UserSchema', dump_only=True)
    
    # 计算字段
    file_size_formatted = fields.Str(dump_only=True)
    uploader_name = fields.Str(dump_only=True)
    
    class Meta:
        fields = [
            'id', 'file_name', 'file_path', 'file_url',
            'file_type', 'mime_type', 'file_size',
            'description', 'sort_order', 'is_cover',
            'house_id', 'uploaded_by',
            'uploader',
            'file_size_formatted', 'uploader_name',
            'created_at', 'updated_at', 'is_active'
        ]
    
    @validates('file_type')
    def validate_file_type(self, value: str):
        """验证文件类型"""
        if value not in ['image', 'video', 'document']:
            raise ValidationError('文件类型必须是 image、video 或 document')


class MediaCreateSchema(BaseSchema):
    """
    多媒体创建 Schema
    """
    
    file_name = fields.Str(required=True, validate=lambda x: len(x) >= 1)
    file_path = fields.Str(required=True)
    file_url = fields.Str(allow_none=True)
    
    file_type = fields.Str(required=True, validate=lambda x: x in ['image', 'video', 'document'])
    mime_type = fields.Str(allow_none=True)
    file_size = fields.Int(allow_none=True, validate=lambda x: x >= 0 if x else True)
    
    description = fields.Str(allow_none=True)
    sort_order = fields.Int(allow_none=True)
    is_cover = fields.Bool(allow_none=True)
    
    house_id = fields.Int(allow_none=True)
    uploaded_by = fields.Int(allow_none=True)
    
    @validates('mime_type')
    def validate_mime_type(self, value: str):
        """验证 MIME 类型"""
        if value:
            from app.models import Media
            if not Media.is_allowed_type(value):
                raise ValidationError('不支持的文件类型')
