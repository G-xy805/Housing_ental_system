"""
基础 Schema 类

提供通用的序列化功能和字段过滤机制
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from marshmallow import Schema, fields, post_dump, pre_load
from flask import has_request_context, request


class TimestampMixin(Schema):
    """
    时间戳混入类
    
    自动处理 created_at 和 updated_at 字段
    """
    created_at = fields.DateTime(dump_only=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(dump_only=True, format='%Y-%m-%d %H:%M:%S')


class BaseSchema(Schema):
    """
    基础 Schema 类
    
    提供以下功能：
    1. 字段过滤（通过 exclude_fields 参数）
    2. 嵌套控制（通过 include_nested 参数）
    3. 敏感字段自动过滤
    4. 内部/外部接口区分
    """
    
    # 敏感字段列表（子类可覆盖）
    SENSITIVE_FIELDS: Set[str] = set()
    
    # 内部接口可见字段（子类可覆盖）
    INTERNAL_ONLY_FIELDS: Set[str] = set()
    
    class Meta:
        # 严格模式，未知字段不报错
        unknown = 'exclude'
        # 时间格式
        datetimeformat = '%Y-%m-%d %H:%M:%S'
    
    def __init__(
        self,
        *args,
        exclude_fields: Optional[List[str]] = None,
        include_nested: bool = True,
        is_internal: bool = False,
        **kwargs
    ):
        """
        初始化 Schema
        
        Args:
            exclude_fields: 需要排除的字段列表
            include_nested: 是否包含嵌套对象（默认 True）
            is_internal: 是否为内部接口（默认 False）
        """
        self._exclude_fields = set(exclude_fields or [])
        self._include_nested = include_nested
        self._is_internal = is_internal
        
        # 自动检测是否为内部接口（基于请求上下文）
        if has_request_context() and not is_internal:
            # 可以根据请求头、用户角色等判断
            self._is_internal = self._detect_internal_request()
        
        # 合并敏感字段
        self._exclude_fields.update(self.SENSITIVE_FIELDS)
        
        # 如果不是内部接口，排除内部专用字段
        if not self._is_internal:
            self._exclude_fields.update(self.INTERNAL_ONLY_FIELDS)
        
        # 调用父类初始化
        super().__init__(*args, **kwargs)
    
    def _detect_internal_request(self) -> bool:
        """
        检测是否为内部请求
        
        Returns:
            bool: 是否为内部请求
        """
        # 可以根据以下条件判断：
        # 1. 请求头中的标记
        # 2. 用户角色（管理员）
        # 3. API 路径
        
        # 示例：检查请求头
        if request.headers.get('X-Internal-Request') == 'true':
            return True
        
        # 示例：检查用户角色（需要从 JWT token 中获取）
        # 这需要在请求上下文中设置
        from flask import g
        if hasattr(g, 'current_user') and g.current_user:
            return g.current_user.role == 'admin'
        
        return False
    
    @post_dump
    def remove_excluded_fields(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        序列化后移除排除的字段
        
        Args:
            data: 序列化后的数据字典
            
        Returns:
            Dict: 处理后的数据字典
        """
        # 移除排除的字段
        for field in self._exclude_fields:
            data.pop(field, None)
        
        # 移除 None 值（可选）
        # data = {k: v for k, v in data.items() if v is not None}
        
        return data
    
    def get_nested_schema(self, schema_class_name: str, **kwargs):
        """
        获取嵌套 Schema 实例
        
        Args:
            schema_class_name: Schema 类名
            **kwargs: 传递给 Schema 的参数
            
        Returns:
            Schema 实例或 None（如果 include_nested=False）
        """
        if not self._include_nested:
            return None
        
        # 动态导入 Schema 类
        # 这里可以根据需要实现更复杂的逻辑
        return kwargs
    
    def filter_fields(self, data: Dict[str, Any], allowed_fields: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        过滤字段
        
        Args:
            data: 原始数据
            allowed_fields: 允许的字段集合（如果为 None，使用所有字段）
            
        Returns:
            Dict: 过滤后的数据
        """
        if allowed_fields is None:
            return data
        
        return {k: v for k, v in data.items() if k in allowed_fields}


class EnumField(fields.Field):
    """
    枚举字段
    
    用于序列化和反序列化枚举值
    """
    
    def __init__(self, enum_class, *args, **kwargs):
        """
        初始化枚举字段
        
        Args:
            enum_class: 枚举类
        """
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)
    
    def _serialize(self, value, attr, obj, **kwargs):
        """序列化枚举值"""
        if value is None:
            return None
        return value.value if hasattr(value, 'value') else str(value)
    
    def _deserialize(self, value, attr, data, **kwargs):
        """反序列化枚举值"""
        if value is None:
            return None
        try:
            return self.enum_class(value)
        except ValueError:
            self.fail('validator_failed', input=value)
