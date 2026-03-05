"""
事务管理装饰器模块
提供数据库事务的自动提交、回滚和嵌套事务支持
"""
from functools import wraps
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from contextlib import contextmanager
from typing import Optional, Callable, Any
import logging

from app.models import db
from app.utils.exceptions import (
    DatabaseException,
    IntegrityException,
    DeadlockException,
    DatabaseConnectionException
)


# ============================================================================
# 事务上下文管理器
# ============================================================================

@contextmanager
def transaction_context(
    auto_commit: bool = True,
    auto_rollback: bool = True,
    nested: bool = False
):
    """
    事务上下文管理器
    
    Args:
        auto_commit: 是否自动提交成功的事务
        auto_rollback: 是否自动回滚失败的事务
        nested: 是否使用嵌套事务（SAVEPOINT）
        
    Yields:
        None
        
    Raises:
        DatabaseException: 数据库操作失败时抛出
        
    Example:
        with transaction_context():
            user = User(username='test')
            db.session.add(user)
            # 自动提交或回滚
    """
    logger = logging.getLogger('transaction')
    
    try:
        # 如果需要嵌套事务，使用 SAVEPOINT
        if nested:
            savepoint = db.session.begin_nested()
            logger.debug("开始嵌套事务（SAVEPOINT）")
        else:
            savepoint = None
            logger.debug("开始事务")
        
        yield
        
        # 自动提交
        if auto_commit:
            if nested and savepoint:
                savepoint.commit()
                logger.debug("提交嵌套事务（SAVEPOINT）")
            else:
                db.session.commit()
                logger.debug("提交事务")
                
    except IntegrityError as e:
        # 数据完整性错误
        if auto_rollback:
            if nested and savepoint:
                savepoint.rollback()
                logger.warning("回滚嵌套事务（数据完整性错误）")
            else:
                db.session.rollback()
                logger.warning("回滚事务（数据完整性错误）")
        
        logger.error(f"数据完整性错误：{str(e)}")
        raise IntegrityException(
            message="数据完整性错误，可能存在重复数据或违反约束",
            details={'original_error': str(e)}
        )
        
    except OperationalError as e:
        # 数据库操作错误（包括死锁、连接失败等）
        error_msg = str(e).lower()
        
        if auto_rollback:
            if nested and savepoint:
                savepoint.rollback()
                logger.warning("回滚嵌套事务（操作错误）")
            else:
                db.session.rollback()
                logger.warning("回滚事务（操作错误）")
        
        # 检查是否为死锁
        if 'deadlock' in error_msg or 'lock' in error_msg:
            logger.error(f"数据库死锁：{str(e)}")
            raise DeadlockException(
                message="数据库死锁，请重试",
                details={'original_error': str(e)}
            )
        
        # 检查是否为连接失败
        if 'connection' in error_msg or 'connect' in error_msg:
            logger.error(f"数据库连接失败：{str(e)}")
            raise DatabaseConnectionException(
                message="数据库连接失败",
                details={'original_error': str(e)}
            )
        
        # 其他操作错误
        logger.error(f"数据库操作错误：{str(e)}")
        raise DatabaseException(
            message="数据库操作失败",
            details={'original_error': str(e)}
        )
        
    except SQLAlchemyError as e:
        # 其他 SQLAlchemy 错误
        if auto_rollback:
            if nested and savepoint:
                savepoint.rollback()
                logger.warning("回滚嵌套事务（SQLAlchemy 错误）")
            else:
                db.session.rollback()
                logger.warning("回滚事务（SQLAlchemy 错误）")
        
        logger.error(f"数据库错误：{str(e)}")
        raise DatabaseException(
            message="数据库操作失败",
            details={'original_error': str(e)}
        )
        
    except Exception as e:
        # 其他未知错误
        if auto_rollback:
            if nested and savepoint:
                savepoint.rollback()
                logger.warning("回滚嵌套事务（未知错误）")
            else:
                db.session.rollback()
                logger.warning("回滚事务（未知错误）")
        
        logger.error(f"事务执行失败：{str(e)}")
        raise


# ============================================================================
# 事务装饰器
# ============================================================================

def transactional(
    auto_commit: bool = True,
    auto_rollback: bool = True,
    nested: bool = False,
    raise_on_error: bool = True
):
    """
    事务装饰器
    
    自动管理数据库事务的提交和回滚
    
    Args:
        auto_commit: 是否自动提交成功的事务
        auto_rollback: 是否自动回滚失败的事务
        nested: 是否使用嵌套事务（SAVEPOINT）
        raise_on_error: 是否在错误时抛出异常
        
    Returns:
        装饰器函数
        
    Example:
        @transactional()
        def create_user(username):
            user = User(username=username)
            db.session.add(user)
            return user
            
        @transactional(nested=True)
        def update_user_profile(user_id, data):
            # 使用嵌套事务
            user = User.query.get(user_id)
            user.update(data)
            return user
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs) -> Any:
            logger = logging.getLogger('transaction')
            
            try:
                # 使用事务上下文管理器
                with transaction_context(
                    auto_commit=auto_commit,
                    auto_rollback=auto_rollback,
                    nested=nested
                ):
                    result = f(*args, **kwargs)
                    return result
                    
            except DatabaseException as e:
                logger.error(f"事务执行失败 [{f.__name__}]: {str(e)}")
                
                if raise_on_error:
                    raise
                    
                return None
                
            except Exception as e:
                logger.error(f"事务执行失败 [{f.__name__}]: {str(e)}")
                
                if raise_on_error:
                    raise
                    
                return None
        
        return decorated_function
    
    return decorator


# ============================================================================
# 简化的事务装饰器
# ============================================================================

def with_transaction(f: Callable) -> Callable:
    """
    简化的事务装饰器
    
    自动提交成功的事务，自动回滚失败的事务
    
    Args:
        f: 被装饰的函数
        
    Returns:
        装饰后的函数
        
    Example:
        @with_transaction
        def create_order(order_data):
            order = Order(**order_data)
            db.session.add(order)
            return order
    """
    return transactional()(f)


def with_nested_transaction(f: Callable) -> Callable:
    """
    嵌套事务装饰器
    
    使用 SAVEPOINT 实现嵌套事务
    
    Args:
        f: 被装饰的函数
        
    Returns:
        装饰后的函数
        
    Example:
        @with_transaction
        def process_order(order_data):
            order = create_order(order_data)
            
            # 嵌套事务
            @with_nested_transaction
            def create_order_items(items):
                for item in items:
                    db.session.add(item)
            
            create_order_items(order_data['items'])
            return order
    """
    return transactional(nested=True)(f)


# ============================================================================
# 手动事务管理辅助函数
# ============================================================================

def begin_transaction():
    """
    开始一个新的事务
    
    注意：通常不需要手动调用，SQLAlchemy 会自动管理事务
    """
    logger = logging.getLogger('transaction')
    logger.debug("手动开始事务")


def commit_transaction():
    """
    提交当前事务
    
    Raises:
        DatabaseException: 提交失败时抛出
    """
    logger = logging.getLogger('transaction')
    
    try:
        db.session.commit()
        logger.debug("手动提交事务")
        
    except SQLAlchemyError as e:
        logger.error(f"提交事务失败：{str(e)}")
        db.session.rollback()
        raise DatabaseException(
            message="提交事务失败",
            details={'original_error': str(e)}
        )


def rollback_transaction():
    """
    回滚当前事务
    """
    logger = logging.getLogger('transaction')
    
    try:
        db.session.rollback()
        logger.debug("手动回滚事务")
        
    except Exception as e:
        logger.error(f"回滚事务失败：{str(e)}")


def begin_nested_transaction():
    """
    开始一个嵌套事务（SAVEPOINT）
    
    Returns:
        SAVEPOINT 对象
        
    Example:
        savepoint = begin_nested_transaction()
        try:
            # 执行数据库操作
            db.session.add(obj)
            savepoint.commit()
        except:
            savepoint.rollback()
    """
    logger = logging.getLogger('transaction')
    logger.debug("开始嵌套事务（SAVEPOINT）")
    return db.session.begin_nested()


# ============================================================================
# 批量操作事务辅助函数
# ============================================================================

def batch_insert(
    model_class,
    data_list: list,
    batch_size: int = 100,
    auto_commit: bool = True
) -> int:
    """
    批量插入数据
    
    Args:
        model_class: 模型类
        data_list: 数据列表（字典列表）
        batch_size: 每批处理的数据量
        auto_commit: 是否自动提交
        
    Returns:
        int: 成功插入的数量
        
    Raises:
        DatabaseException: 插入失败时抛出
        
    Example:
        users_data = [
            {'username': 'user1', 'email': 'user1@example.com'},
            {'username': 'user2', 'email': 'user2@example.com'},
        ]
        count = batch_insert(User, users_data, batch_size=50)
    """
    logger = logging.getLogger('transaction')
    
    if not data_list:
        return 0
    
    inserted_count = 0
    
    try:
        # 分批处理
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            
            # 批量创建对象
            objects = [model_class(**data) for data in batch]
            
            # 批量添加
            db.session.bulk_save_objects(objects)
            
            inserted_count += len(batch)
            
            # 每批提交一次
            if auto_commit:
                db.session.commit()
                logger.debug(f"批量插入 {len(batch)} 条数据")
        
        if not auto_commit:
            logger.debug(f"批量插入 {inserted_count} 条数据（未提交）")
        
        return inserted_count
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"批量插入失败：{str(e)}")
        raise DatabaseException(
            message="批量插入数据失败",
            details={
                'inserted_count': inserted_count,
                'total_count': len(data_list),
                'original_error': str(e)
            }
        )


def batch_update(
    model_class,
    updates: list,
    batch_size: int = 100,
    auto_commit: bool = True
) -> int:
    """
    批量更新数据
    
    Args:
        model_class: 模型类
        updates: 更新列表 [{'id': 1, 'field': 'value'}, ...]
        batch_size: 每批处理的数据量
        auto_commit: 是否自动提交
        
    Returns:
        int: 成功更新的数量
        
    Raises:
        DatabaseException: 更新失败时抛出
        
    Example:
        updates = [
            {'id': 1, 'status': 'active'},
            {'id': 2, 'status': 'inactive'},
        ]
        count = batch_update(User, updates, batch_size=50)
    """
    logger = logging.getLogger('transaction')
    
    if not updates:
        return 0
    
    updated_count = 0
    
    try:
        # 分批处理
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            for update_data in batch:
                obj_id = update_data.pop('id')
                model_class.query.filter_by(id=obj_id).update(update_data)
                updated_count += 1
            
            # 每批提交一次
            if auto_commit:
                db.session.commit()
                logger.debug(f"批量更新 {len(batch)} 条数据")
        
        if not auto_commit:
            logger.debug(f"批量更新 {updated_count} 条数据（未提交）")
        
        return updated_count
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"批量更新失败：{str(e)}")
        raise DatabaseException(
            message="批量更新数据失败",
            details={
                'updated_count': updated_count,
                'total_count': len(updates),
                'original_error': str(e)
            }
        )


def batch_delete(
    model_class,
    ids: list,
    batch_size: int = 100,
    auto_commit: bool = True
) -> int:
    """
    批量删除数据
    
    Args:
        model_class: 模型类
        ids: ID 列表
        batch_size: 每批处理的数据量
        auto_commit: 是否自动提交
        
    Returns:
        int: 成功删除的数量
        
    Raises:
        DatabaseException: 删除失败时抛出
        
    Example:
        ids = [1, 2, 3, 4, 5]
        count = batch_delete(User, ids, batch_size=50)
    """
    logger = logging.getLogger('transaction')
    
    if not ids:
        return 0
    
    deleted_count = 0
    
    try:
        # 分批处理
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            
            # 批量删除
            deleted = model_class.query.filter(model_class.id.in_(batch_ids)).delete(
                synchronize_session='fetch'
            )
            
            deleted_count += deleted
            
            # 每批提交一次
            if auto_commit:
                db.session.commit()
                logger.debug(f"批量删除 {deleted} 条数据")
        
        if not auto_commit:
            logger.debug(f"批量删除 {deleted_count} 条数据（未提交）")
        
        return deleted_count
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"批量删除失败：{str(e)}")
        raise DatabaseException(
            message="批量删除数据失败",
            details={
                'deleted_count': deleted_count,
                'total_count': len(ids),
                'original_error': str(e)
            }
        )
