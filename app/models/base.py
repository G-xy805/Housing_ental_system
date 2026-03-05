"""
基础模型类

提供软删除功能的实现：
- deleted_at: 软删除时间戳字段
- is_deleted: 判断是否已删除的属性
- soft_delete(): 软删除方法
- restore(): 恢复方法
- SoftDeleteQuery: 自定义查询类，默认过滤已删除记录
"""
from datetime import datetime
from app import db
from sqlalchemy.orm import Query
from werkzeug.exceptions import NotFound


class SoftDeleteQuery(Query):
    """
    自定义查询类，默认过滤已删除的记录
    
    使用方式：
    - Model.query.all()  # 自动过滤已删除记录
    - Model.query.with_deleted().all()  # 包含已删除记录
    - Model.query.only_deleted().all()  # 仅查询已删除记录
    """
    
    def __new__(cls, *args, **kwargs):
        """
        创建查询对象时自动添加软删除过滤条件
        """
        # 获取模型类
        model = args[0] if args else kwargs.get('model', None)
        
        # 创建查询对象
        query = super(SoftDeleteQuery, cls).__new__(cls)
        
        # 如果模型有 deleted_at 字段，默认过滤已删除记录
        if model and hasattr(model, 'deleted_at'):
            query._with_deleted = False
            query._only_deleted = False
        
        return query
    
    def __init__(self, *args, **kwargs):
        super(SoftDeleteQuery, self).__init__(*args, **kwargs)
        # 初始化标志
        self._with_deleted = getattr(self, '_with_deleted', False)
        self._only_deleted = getattr(self, '_only_deleted', False)
    
    def _clone(self):
        """
        克隆查询对象，保留软删除标志
        """
        clone = super(SoftDeleteQuery, self)._clone()
        clone._with_deleted = self._with_deleted
        clone._only_deleted = self._only_deleted
        return clone
    
    def with_deleted(self):
        """
        包含已删除记录的查询
        
        Returns:
            SoftDeleteQuery: 包含已删除记录的查询对象
        """
        clone = self._clone()
        clone._with_deleted = True
        clone._only_deleted = False
        return clone
    
    def only_deleted(self):
        """
        仅查询已删除记录
        
        Returns:
            SoftDeleteQuery: 仅包含已删除记录的查询对象
        """
        clone = self._clone()
        clone._with_deleted = True
        clone._only_deleted = True
        return clone
    
    def _has_limit_or_offset(self):
        """
        检查查询是否已经应用了 limit 或 offset
        
        Returns:
            bool: 如果有 limit 或 offset 返回 True
        """
        # 尝试获取 limit 和 offset 属性
        # SQLAlchemy 2.x 使用 _limit 和 _offset
        # 但在某些情况下可能不存在这些属性
        try:
            limit = getattr(self, '_limit', None)
            offset = getattr(self, '_offset', None)
            return limit is not None or offset is not None
        except AttributeError:
            return False
    
    def paginate(self, page=None, per_page=None, error_out=True, max_per_page=None):
        """
        分页查询，应用软删除过滤
        
        Args:
            page: 页码，默认 None
            per_page: 每页数量，默认 None
            error_out: 是否在页码错误时抛出异常，默认 True
            max_per_page: 每页最大数量，默认 None
            
        Returns:
            Pagination: 分页结果对象
        """
        from flask import current_app
        
        # 手动实现分页逻辑
        if per_page is None:
            per_page = current_app.config.get('PER_PAGE', 20)
        
        if error_out and page is not None:
            if page < 1:
                raise NotFound("Page not found")
        
        if page is None:
            page = 1
        
        # 先应用软删除过滤条件
        if hasattr(self.column_descriptions[0]['type'], 'deleted_at'):
            if not self._with_deleted:
                query = self.filter(self.column_descriptions[0]['type'].deleted_at.is_(None))
            elif self._only_deleted:
                query = self.filter(self.column_descriptions[0]['type'].deleted_at.isnot(None))
            else:
                query = self
        else:
            query = self
        
        # 不在这里应用 limit 和 offset，让 Flask-SQLAlchemy 的 paginate 方法处理
        # 直接返回查询对象，由 Flask-SQLAlchemy 的 paginate 方法来分页
        return query.paginate(page=page, per_page=per_page, error_out=error_out)
    
    def __iter__(self):
        """
        迭代时应用软删除过滤
        """
        # 应用软删除过滤条件
        if hasattr(self, 'column_descriptions') and self.column_descriptions:
            model = self.column_descriptions[0]['type']
            if hasattr(model, 'deleted_at'):
                if not self._with_deleted:
                    # 检查是否已经有 limit 或 offset
                    if self._has_limit_or_offset():
                        results = super(SoftDeleteQuery, self).all()
                        return iter([r for r in results if r.deleted_at is None])
                    else:
                        filtered = self.filter(model.deleted_at.is_(None))
                        return super(SoftDeleteQuery, filtered).__iter__()
                elif self._only_deleted:
                    if self._has_limit_or_offset():
                        results = super(SoftDeleteQuery, self).all()
                        return iter([r for r in results if r.deleted_at is not None])
                    else:
                        filtered = self.filter(model.deleted_at.isnot(None))
                        return super(SoftDeleteQuery, filtered).__iter__()
        
        return super(SoftDeleteQuery, self).__iter__()
    
    def all(self):
        """
        获取所有记录，应用软删除过滤
        """
        # 应用软删除过滤条件
        if hasattr(self, 'column_descriptions') and self.column_descriptions:
            model = self.column_descriptions[0]['type']
            if hasattr(model, 'deleted_at'):
                if not self._with_deleted:
                    # 检查是否已经有 limit 或 offset，如果有则使用 with_deleted 模式
                    # 因为 SQLAlchemy 不允许在 limit/offset 后调用 filter
                    if self._has_limit_or_offset():
                        # 已经有 limit/offset，需要在结果中过滤
                        results = super(SoftDeleteQuery, self).all()
                        return [r for r in results if r.deleted_at is None]
                    else:
                        self = self.filter(model.deleted_at.is_(None))
                elif self._only_deleted:
                    if self._has_limit_or_offset():
                        results = super(SoftDeleteQuery, self).all()
                        return [r for r in results if r.deleted_at is not None]
                    else:
                        self = self.filter(model.deleted_at.isnot(None))
        
        return super(SoftDeleteQuery, self).all()
    
    def count(self):
        """
        计数，应用软删除过滤
        """
        # 应用软删除过滤条件
        if hasattr(self, 'column_descriptions') and self.column_descriptions:
            model = self.column_descriptions[0]['type']
            if hasattr(model, 'deleted_at'):
                if not self._with_deleted:
                    if self._has_limit_or_offset():
                        # 已经有 limit/offset，需要在结果中计数
                        results = super(SoftDeleteQuery, self).all()
                        return len([r for r in results if r.deleted_at is None])
                    else:
                        self = self.filter(model.deleted_at.is_(None))
                elif self._only_deleted:
                    if self._has_limit_or_offset():
                        results = super(SoftDeleteQuery, self).all()
                        return len([r for r in results if r.deleted_at is not None])
                    else:
                        self = self.filter(model.deleted_at.isnot(None))
        
        return super(SoftDeleteQuery, self).count()
    
    def first(self):
        """
        获取第一条记录，应用软删除过滤
        """
        # 应用软删除过滤条件
        if hasattr(self, 'column_descriptions') and self.column_descriptions:
            model = self.column_descriptions[0]['type']
            if hasattr(model, 'deleted_at'):
                if not self._with_deleted:
                    if self._has_limit_or_offset():
                        results = super(SoftDeleteQuery, self).all()
                        for r in results:
                            if r.deleted_at is None:
                                return r
                        return None
                    else:
                        self = self.filter(model.deleted_at.is_(None))
                elif self._only_deleted:
                    if self._has_limit_or_offset():
                        results = super(SoftDeleteQuery, self).all()
                        for r in results:
                            if r.deleted_at is not None:
                                return r
                        return None
                    else:
                        self = self.filter(model.deleted_at.isnot(None))
        
        return super(SoftDeleteQuery, self).first()
    
    def get(self, ident):
        """
        根据 ID 获取记录，应用软删除过滤
        """
        # 应用软删除过滤条件
        if hasattr(self.column_descriptions[0]['type'], 'deleted_at'):
            if not self._with_deleted:
                # 过滤已删除记录
                result = super(SoftDeleteQuery, self).get(ident)
                if result and result.deleted_at is not None:
                    return None
                return result
            elif self._only_deleted:
                # 仅返回已删除记录
                result = super(SoftDeleteQuery, self).get(ident)
                if result and result.deleted_at is None:
                    return None
                return result
        
        return super(SoftDeleteQuery, self).get(ident)


class BaseModel(db.Model):
    """
    基础模型类，提供通用字段和方法
    
    包含软删除功能：
    - deleted_at: 软删除时间戳，NULL 表示未删除
    - is_deleted: 判断记录是否已删除
    - soft_delete(): 软删除记录（设置 deleted_at 为当前时间）
    - restore(): 恢复已删除记录（设置 deleted_at 为 NULL）
    """
    
    __abstract__ = True
    
    # 使用自定义查询类
    query_class = SoftDeleteQuery
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    
    # 软删除字段：记录删除时间，NULL 表示未删除
    deleted_at = db.Column(db.DateTime, nullable=True, comment='软删除时间')
    
    @property
    def is_deleted(self):
        """
        判断记录是否已删除
        
        Returns:
            bool: True 表示已删除，False 表示未删除
        """
        return self.deleted_at is not None
    
    def soft_delete(self):
        """
        软删除记录
        
        将 deleted_at 设置为当前时间，而不是真正从数据库删除
        软删除后的记录在默认查询中会被过滤
        
        Returns:
            self: 返回对象本身，支持链式调用
        """
        self.deleted_at = datetime.now()
        db.session.add(self)
        db.session.commit()
        return self
    
    def restore(self):
        """
        恢复已删除的记录
        
        将 deleted_at 设置为 NULL，使记录重新可见
        仅对已删除的记录有效
        
        Returns:
            self: 返回对象本身，支持链式调用
        """
        self.deleted_at = None
        db.session.add(self)
        db.session.commit()
        return self
    
    def hard_delete(self):
        """
        硬删除记录
        
        真正从数据库删除记录，不可恢复
        谨慎使用！
        """
        db.session.delete(self)
        db.session.commit()
    
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
        """
        软删除对象（推荐使用 soft_delete 方法）
        
        保留向后兼容性，调用 soft_delete 方法
        """
        return self.soft_delete()
    
    @classmethod
    def active_query(cls):
        """
        查询时自动过滤已删除的记录
        
        推荐使用 Model.query 代替，已默认过滤已删除记录
        
        Returns:
            SoftDeleteQuery: 查询对象
        """
        return db.session.query(cls).filter(cls.deleted_at.is_(None))
    
    @classmethod
    def with_deleted(cls):
        """
        查询包含已删除记录
        
        Returns:
            SoftDeleteQuery: 包含已删除记录的查询对象
        """
        return cls.query.with_deleted()
    
    @classmethod
    def only_deleted(cls):
        """
        仅查询已删除记录
        
        Returns:
            SoftDeleteQuery: 仅包含已删除记录的查询对象
        """
        return cls.query.only_deleted()
    
    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'
