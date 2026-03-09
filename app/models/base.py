"""
基础模型类

提供软删除功能的实现：
- deleted_at: 软删除时间戳字段
- is_deleted: 判断是否已删除的属性
- soft_delete(): 软删除方法
- restore(): 恢复方法
- cascade_soft_delete(): 级联软删除方法
- get_delete_preview(): 删除预览方法
- validate_delete(): 删除验证方法
- SoftDeleteQuery: 自定义查询类，默认过滤已删除记录
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from app import db
from sqlalchemy.orm import Query
from werkzeug.exceptions import NotFound
import logging

logger = logging.getLogger(__name__)


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
        from math import ceil
        
        if per_page is None:
            per_page = current_app.config.get('PER_PAGE', 20)
        
        if max_per_page is not None:
            per_page = min(per_page, max_per_page)
        
        if page is None:
            page = 1
        
        if error_out and page < 1:
            raise NotFound("Page not found")
        
        query = self
        
        if hasattr(self, 'column_descriptions') and self.column_descriptions:
            model = self.column_descriptions[0]['type']
            if hasattr(model, 'deleted_at'):
                if not self._with_deleted:
                    query = self.filter(model.deleted_at.is_(None))
                    query._with_deleted = True
                elif self._only_deleted:
                    query = self.filter(model.deleted_at.isnot(None))
                    query._with_deleted = True
        
        total = query.count()
        
        pages = ceil(total / per_page) if total > 0 else 1
        
        if error_out and page > pages:
            raise NotFound("Page not found")
        
        items = query.limit(per_page).offset((page - 1) * per_page).all()
        
        class Pagination:
            def __init__(self, items, page, per_page, total, pages):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = pages
                self.has_next = page < pages
                self.has_prev = page > 1
                self.next_num = page + 1 if self.has_next else None
                self.prev_num = page - 1 if self.has_prev else None
        
        return Pagination(items, page, per_page, total, pages)
    
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
            elif isinstance(value, date):
                value = value.strftime('%Y-%m-%d')
            elif isinstance(value, Decimal):
                value = float(value)
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
    
    def get_cascade_relations(self) -> Dict[str, Any]:
        """
        获取需要级联处理的关系定义
        
        子类应该重写此方法，定义需要级联软删除的关系
        
        Returns:
            Dict: 关系配置字典，格式如下：
                {
                    'relation_name': {
                        'relationship': self.rooms,  # 关系属性
                        'model': Room,               # 关联模型类
                        'cascade_delete': True,      # 是否级联删除
                        'validate_not_empty': False, # 是否验证非空
                        'error_message': '存在关联房间'  # 错误消息
                    }
                }
        """
        return {}
    
    def validate_delete(self) -> Tuple[bool, List[str]]:
        """
        验证是否可以删除
        
        检查关联数据，返回验证结果
        
        Returns:
            Tuple[bool, List[str]]: (是否可以删除, 错误消息列表)
        """
        errors = []
        relations = self.get_cascade_relations()
        
        for relation_name, config in relations.items():
            # 如果需要验证非空
            if config.get('validate_not_empty', False):
                relation = getattr(self, relation_name, None)
                if relation is not None:
                    # 处理动态关系（lazy='dynamic'）
                    if hasattr(relation, 'count'):
                        count = relation.count()
                    elif isinstance(relation, (list, tuple)):
                        count = len(relation)
                    else:
                        count = 1 if relation else 0
                    
                    if count > 0:
                        error_msg = config.get('error_message', f'存在关联的{relation_name}')
                        errors.append(f'{error_msg}（共 {count} 条）')
        
        return len(errors) == 0, errors
    
    def get_delete_preview(self) -> Dict[str, Any]:
        """
        获取删除预览信息
        
        返回将被删除或影响的所有关联数据
        
        Returns:
            Dict: 删除预览信息
                {
                    'can_delete': bool,           # 是否可以删除
                    'errors': List[str],          # 错误消息
                    'cascade_items': List[Dict],  # 将被级联删除的项目
                    'affected_items': List[Dict]  # 将受影响的项目
                }
        """
        can_delete, errors = self.validate_delete()
        cascade_items = []
        affected_items = []
        relations = self.get_cascade_relations()
        
        for relation_name, config in relations.items():
            relation = getattr(self, relation_name, None)
            if relation is None:
                continue
            
            # 处理动态关系
            if hasattr(relation, 'all'):
                items = relation.all()
            elif isinstance(relation, (list, tuple)):
                items = relation
            else:
                items = [relation] if relation else []
            
            if not items:
                continue
            
            model_class = config.get('model')
            model_name = model_class.__name__ if model_class else relation_name
            
            for item in items:
                item_info = {
                    'model': model_name,
                    'id': getattr(item, 'id', None),
                    'display': str(item),
                    'action': 'cascade_delete' if config.get('cascade_delete') else 'affected'
                }
                
                if config.get('cascade_delete'):
                    cascade_items.append(item_info)
                else:
                    affected_items.append(item_info)
        
        return {
            'can_delete': can_delete,
            'errors': errors,
            'cascade_items': cascade_items,
            'affected_items': affected_items,
            'total_cascade': len(cascade_items),
            'total_affected': len(affected_items)
        }
    
    def cascade_soft_delete(self, user_id: Optional[int] = None) -> Tuple[bool, str, int]:
        """
        级联软删除
        
        先验证是否可以删除，然后级联软删除所有关联数据
        
        Args:
            user_id: 操作用户 ID（用于审计日志）
            
        Returns:
            Tuple[bool, str, int]: (是否成功, 消息, 删除数量)
        """
        # 验证是否可以删除
        can_delete, errors = self.validate_delete()
        if not can_delete:
            return False, '; '.join(errors), 0
        
        # 获取删除预览
        preview = self.get_delete_preview()
        deleted_count = 0
        
        try:
            # 级联软删除关联数据
            for item_info in preview['cascade_items']:
                # 根据模型名获取模型类
                model_class = self._get_model_by_name(item_info['model'])
                if model_class:
                    item = model_class.query.with_deleted().get(item_info['id'])
                    if item and not item.is_deleted:
                        item.soft_delete()
                        deleted_count += 1
                        logger.info(f'级联软删除: {item_info["model"]} ID={item_info["id"]}')
            
            # 软删除自身
            self.soft_delete()
            deleted_count += 1
            
            # 记录删除操作日志
            logger.info(f'级联软删除完成: {self.__class__.__name__} ID={self.id}, 共删除 {deleted_count} 条记录')
            
            return True, f'删除成功，共删除 {deleted_count} 条记录', deleted_count
            
        except Exception as e:
            logger.error(f'级联软删除失败: {e}', exc_info=True)
            return False, f'删除失败: {str(e)}', deleted_count
    
    def _get_model_by_name(self, model_name: str):
        """
        根据模型名获取模型类
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型类或 None
        """
        # 导入所有模型
        from app.models import (
            User, House, Room, Contract, Payment, 
            Tenant, Landlord, LandlordContract, Media,
            ContractArchive, PaymentArchive, ArchiveRecord
        )
        
        model_map = {
            'User': User,
            'House': House,
            'Room': Room,
            'Contract': Contract,
            'Payment': Payment,
            'Tenant': Tenant,
            'Landlord': Landlord,
            'LandlordContract': LandlordContract,
            'Media': Media,
            'ContractArchive': ContractArchive,
            'PaymentArchive': PaymentArchive,
            'ArchiveRecord': ArchiveRecord
        }
        
        return model_map.get(model_name)
    
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
