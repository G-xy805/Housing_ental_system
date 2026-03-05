"""
用户 Schema

提供用户模型的序列化和验证
"""
from typing import Optional
from marshmallow import fields, validates, validates_schema, ValidationError, post_dump
from .base import BaseSchema, TimestampMixin


class UserSchema(BaseSchema, TimestampMixin):
    """
    用户序列化 Schema
    
    支持字段过滤和敏感字段自动移除
    """
    
    # 敏感字段
    SENSITIVE_FIELDS = {'password_hash', 'id_card', 'id_card_hash'}
    
    # 内部接口专用字段
    INTERNAL_ONLY_FIELDS = {'created_by', 'login_attempts', 'locked_until'}
    
    # 基本字段
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=lambda x: len(x) >= 3)
    email = fields.Email(allow_none=True)
    role = fields.Str(validate=lambda x: x in ['admin', 'staff'])
    user_type = fields.Str(dump_only=True)
    
    # 员工信息
    name = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True, validate=lambda x: len(x) >= 11)
    id_card = fields.Str(load_only=True, allow_none=True)
    position = fields.Str(allow_none=True)
    status = fields.Str(validate=lambda x: x in ['active', 'resigned', 'disabled'])
    avatar = fields.Str(allow_none=True)
    
    # 登录信息
    last_login = fields.DateTime(dump_only=True, allow_none=True)
    login_attempts = fields.Int(dump_only=True)
    locked_until = fields.DateTime(dump_only=True, allow_none=True)
    
    # 关联字段
    created_by = fields.Int(dump_only=True, allow_none=True)
    
    # 计算字段
    is_admin = fields.Boolean(dump_only=True)
    is_staff = fields.Boolean(dump_only=True)
    is_locked = fields.Boolean(dump_only=True)
    
    class Meta:
        fields = [
            'id', 'username', 'email', 'role', 'user_type',
            'name', 'phone', 'id_card', 'position', 'status', 'avatar',
            'last_login', 'login_attempts', 'locked_until', 'created_by',
            'is_admin', 'is_staff', 'is_locked',
            'created_at', 'updated_at', 'is_active'
        ]
    
    @validates('username')
    def validate_username(self, value: str):
        """验证用户名"""
        if len(value) < 3:
            raise ValidationError('用户名至少需要 3 个字符')
        if len(value) > 50:
            raise ValidationError('用户名不能超过 50 个字符')
    
    @validates('phone')
    def validate_phone(self, value: Optional[str]):
        """验证手机号"""
        if value and len(value) != 11:
            raise ValidationError('手机号必须是 11 位')
    
    @validates('role')
    def validate_role(self, value: str):
        """验证角色"""
        if value not in ['admin', 'staff']:
            raise ValidationError('角色必须是 admin 或 staff')
    
    @post_dump
    def add_computed_fields(self, data, **kwargs):
        """添加计算字段"""
        # 添加 is_locked 字段
        from datetime import datetime
        if 'locked_until' in data and data['locked_until']:
            locked_until = datetime.fromisoformat(data['locked_until'])
            data['is_locked'] = locked_until > datetime.now()
        else:
            data['is_locked'] = False
        
        return data


class UserCreateSchema(BaseSchema):
    """
    用户创建 Schema
    
    用于创建用户时的数据验证
    """
    
    username = fields.Str(required=True, validate=lambda x: 3 <= len(x) <= 50)
    email = fields.Email(allow_none=True)
    password = fields.Str(required=True, load_only=True, validate=lambda x: len(x) >= 6)
    role = fields.Str(required=True, validate=lambda x: x in ['admin', 'staff'])
    name = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True, validate=lambda x: len(x) == 11 if x else True)
    id_card = fields.Str(load_only=True, allow_none=True)
    position = fields.Str(allow_none=True)
    avatar = fields.Str(allow_none=True)
    
    @validates_schema
    def validate_unique_fields(self, data, **kwargs):
        """验证唯一字段"""
        from app.models import User
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=data.get('username')).first():
            raise ValidationError('用户名已存在', field_name='username')
        
        # 检查邮箱是否已存在
        email = data.get('email')
        if email and User.query.filter_by(email=email).first():
            raise ValidationError('邮箱已存在', field_name='email')
        
        # 检查手机号是否已存在
        phone = data.get('phone')
        if phone and User.query.filter_by(phone=phone).first():
            raise ValidationError('手机号已存在', field_name='phone')


class UserUpdateSchema(BaseSchema):
    """
    用户更新 Schema
    
    用于更新用户信息时的数据验证
    """
    
    email = fields.Email(allow_none=True)
    name = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True, validate=lambda x: len(x) == 11 if x else True)
    id_card = fields.Str(load_only=True, allow_none=True)
    position = fields.Str(allow_none=True)
    status = fields.Str(validate=lambda x: x in ['active', 'resigned', 'disabled'])
    avatar = fields.Str(allow_none=True)
    
    @validates_schema
    def validate_unique_fields(self, data, **kwargs):
        """验证唯一字段（排除当前用户）"""
        from flask import g
        from app.models import User
        
        current_user_id = kwargs.get('instance') and kwargs['instance'].id
        if not current_user_id:
            return
        
        # 检查邮箱是否已被其他用户使用
        email = data.get('email')
        if email:
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != current_user_id:
                raise ValidationError('邮箱已被其他用户使用', field_name='email')
        
        # 检查手机号是否已被其他用户使用
        phone = data.get('phone')
        if phone:
            existing = User.query.filter_by(phone=phone).first()
            if existing and existing.id != current_user_id:
                raise ValidationError('手机号已被其他用户使用', field_name='phone')
