"""
重试机制模块
提供数据库连接失败、死锁等场景的自动重试功能
"""
import time
import logging
from functools import wraps
from typing import Callable, Optional, List, Type, Tuple, Any
from random import random

from sqlalchemy.exc import OperationalError, InterfaceError, DBAPIError

from app.utils.exceptions import (
    DatabaseException,
    DeadlockException,
    DatabaseConnectionException,
    DatabaseTimeoutException
)


# ============================================================================
# 重试配置
# ============================================================================

class RetryConfig:
    """重试配置类"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        """
        初始化重试配置
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            exponential_base: 指数退避基数
            jitter: 是否添加随机抖动
            retryable_exceptions: 可重试的异常类型列表
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            OperationalError,
            InterfaceError,
            DBAPIError,
            DeadlockException,
            DatabaseConnectionException,
            DatabaseTimeoutException
        ]


# 默认配置
DEFAULT_RETRY_CONFIG = RetryConfig()


# ============================================================================
# 重试装饰器
# ============================================================================

def retry_on_exception(
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    on_retry: Optional[Callable] = None
):
    """
    重试装饰器
    
    当函数抛出指定异常时自动重试
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_base: 指数退避基数
        jitter: 是否添加随机抖动
        retryable_exceptions: 可重试的异常类型列表
        on_retry: 重试时的回调函数
        
    Returns:
        装饰器函数
        
    Example:
        @retry_on_exception(max_retries=3, base_delay=0.1)
        def query_database():
            # 数据库查询操作
            return db.session.query(User).all()
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions
    )
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs) -> Any:
            return retry_call(f, args, kwargs, config, on_retry)
        
        return decorated_function
    
    return decorator


def retry_call(
    f: Callable,
    args: tuple = None,
    kwargs: dict = None,
    config: RetryConfig = None,
    on_retry: Optional[Callable] = None
) -> Any:
    """
    执行带重试的函数调用
    
    Args:
        f: 要执行的函数
        args: 位置参数
        kwargs: 关键字参数
        config: 重试配置
        on_retry: 重试时的回调函数
        
    Returns:
        函数执行结果
        
    Raises:
        Exception: 达到最大重试次数后抛出最后一次异常
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    
    if args is None:
        args = ()
    
    if kwargs is None:
        kwargs = {}
    
    logger = logging.getLogger('retry')
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return f(*args, **kwargs)
            
        except tuple(config.retryable_exceptions) as e:
            last_exception = e
            
            # 检查是否还可以重试
            if attempt >= config.max_retries:
                logger.error(
                    f"函数 {f.__name__} 重试失败，已达到最大重试次数 {config.max_retries}"
                )
                raise
            
            # 计算延迟时间（指数退避）
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            # 添加随机抖动
            if config.jitter:
                delay = delay * (0.5 + random())
            
            # 记录重试日志
            logger.warning(
                f"函数 {f.__name__} 执行失败（尝试 {attempt + 1}/{config.max_retries + 1}），"
                f"{delay:.3f}秒后重试。错误：{str(e)}"
            )
            
            # 调用重试回调
            if on_retry:
                try:
                    on_retry(attempt, e, delay)
                except Exception as callback_error:
                    logger.error(f"重试回调函数执行失败：{str(callback_error)}")
            
            # 等待后重试
            time.sleep(delay)
        
        except Exception as e:
            # 不可重试的异常，直接抛出
            logger.error(f"函数 {f.__name__} 执行失败（不可重试）：{str(e)}")
            raise
    
    # 理论上不会到达这里
    raise last_exception


# ============================================================================
# 数据库操作重试装饰器
# ============================================================================

def retry_on_db_error(
    max_retries: int = 3,
    base_delay: float = 0.1,
    retry_on_deadlock: bool = True,
    retry_on_connection_error: bool = True
):
    """
    数据库操作重试装饰器
    
    专门用于数据库操作的重试，支持死锁和连接失败重试
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
        retry_on_deadlock: 是否在死锁时重试
        retry_on_connection_error: 是否在连接失败时重试
        
    Returns:
        装饰器函数
        
    Example:
        @retry_on_db_error(max_retries=3)
        def update_user(user_id, data):
            user = User.query.get(user_id)
            user.update(data)
            db.session.commit()
            return user
    """
    # 构建可重试的异常列表
    retryable_exceptions = []
    
    if retry_on_deadlock:
        retryable_exceptions.extend([
            DeadlockException,
            OperationalError  # OperationalError 可能包含死锁
        ])
    
    if retry_on_connection_error:
        retryable_exceptions.extend([
            DatabaseConnectionException,
            InterfaceError,
            DBAPIError
        ])
    
    return retry_on_exception(
        max_retries=max_retries,
        base_delay=base_delay,
        retryable_exceptions=retryable_exceptions,
        on_retry=_db_retry_callback
    )


def _db_retry_callback(attempt: int, exception: Exception, delay: float):
    """
    数据库重试回调函数
    
    Args:
        attempt: 当前尝试次数
        exception: 异常对象
        delay: 延迟时间
    """
    logger = logging.getLogger('retry')
    
    # 检查是否为死锁
    if isinstance(exception, DeadlockException) or (
        isinstance(exception, OperationalError) and 
        'deadlock' in str(exception).lower()
    ):
        logger.warning(f"检测到数据库死锁，第 {attempt + 1} 次重试")
    
    # 检查是否为连接错误
    elif isinstance(exception, (DatabaseConnectionException, InterfaceError)):
        logger.warning(f"检测到数据库连接错误，第 {attempt + 1} 次重试")
    
    # 回滚事务
    try:
        from app.models import db
        db.session.rollback()
    except:
        pass


# ============================================================================
# 简化的重试装饰器
# ============================================================================

def with_retry(max_retries: int = 3):
    """
    简化的重试装饰器
    
    使用默认配置进行重试
    
    Args:
        max_retries: 最大重试次数
        
    Returns:
        装饰器函数
        
    Example:
        @with_retry(max_retries=3)
        def call_external_api():
            response = requests.get('https://api.example.com/data')
            return response.json()
    """
    return retry_on_exception(max_retries=max_retries)


def with_db_retry(max_retries: int = 3):
    """
    简化的数据库重试装饰器
    
    专门用于数据库操作
    
    Args:
        max_retries: 最大重试次数
        
    Returns:
        装饰器函数
        
    Example:
        @with_db_retry(max_retries=3)
        def create_order(order_data):
            order = Order(**order_data)
            db.session.add(order)
            db.session.commit()
            return order
    """
    return retry_on_db_error(max_retries=max_retries)


# ============================================================================
# 重试上下文管理器
# ============================================================================

class RetryContext:
    """
    重试上下文管理器
    
    用于需要在代码块中进行重试的场景
    
    Example:
        with RetryContext(max_retries=3) as retry:
            while retry.should_retry():
                try:
                    # 执行可能失败的操作
                    result = perform_operation()
                    break
                except SomeException as e:
                    retry.record_failure(e)
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        初始化重试上下文
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            exponential_base: 指数退避基数
            jitter: 是否添加随机抖动
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        
        self.attempt = 0
        self.last_exception = None
        self.logger = logging.getLogger('retry')
    
    def __enter__(self):
        """进入上下文"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        return False
    
    def should_retry(self) -> bool:
        """
        是否应该继续重试
        
        Returns:
            bool: 是否应该重试
        """
        return self.attempt <= self.max_retries
    
    def record_failure(self, exception: Exception):
        """
        记录失败并准备重试
        
        Args:
            exception: 异常对象
            
        Raises:
            Exception: 达到最大重试次数后抛出异常
        """
        self.last_exception = exception
        self.attempt += 1
        
        if self.attempt > self.max_retries:
            self.logger.error(
                f"重试失败，已达到最大重试次数 {self.max_retries}"
            )
            raise exception
        
        # 计算延迟时间
        delay = min(
            self.base_delay * (self.exponential_base ** (self.attempt - 1)),
            self.max_delay
        )
        
        # 添加随机抖动
        if self.jitter:
            delay = delay * (0.5 + random())
        
        self.logger.warning(
            f"操作失败（尝试 {self.attempt}/{self.max_retries + 1}），"
            f"{delay:.3f}秒后重试。错误：{str(exception)}"
        )
        
        # 等待后重试
        time.sleep(delay)
    
    def reset(self):
        """重置重试状态"""
        self.attempt = 0
        self.last_exception = None


# ============================================================================
# 批量操作重试辅助函数
# ============================================================================

def retry_batch_operation(
    operation: Callable,
    items: list,
    batch_size: int = 10,
    max_retries: int = 3,
    on_item_failure: Optional[Callable] = None
) -> Tuple[list, list]:
    """
    批量操作重试
    
    对批量操作中的每个项目进行重试，记录失败的项目
    
    Args:
        operation: 操作函数，接受单个项目作为参数
        items: 项目列表
        batch_size: 批处理大小
        max_retries: 最大重试次数
        on_item_failure: 项目失败时的回调函数
        
    Returns:
        tuple: (成功项目列表, 失败项目列表)
        
    Example:
        def process_item(item):
            # 处理单个项目
            db.session.add(item)
            db.session.commit()
        
        succeeded, failed = retry_batch_operation(
            process_item,
            items,
            batch_size=10,
            max_retries=3
        )
    """
    logger = logging.getLogger('retry')
    succeeded = []
    failed = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        for item in batch:
            config = RetryConfig(max_retries=max_retries)
            
            try:
                result = retry_call(operation, args=(item,), config=config)
                succeeded.append({
                    'item': item,
                    'result': result
                })
                
            except Exception as e:
                logger.error(f"批量操作项目失败：{str(e)}")
                failed.append({
                    'item': item,
                    'error': str(e)
                })
                
                # 调用失败回调
                if on_item_failure:
                    try:
                        on_item_failure(item, e)
                    except Exception as callback_error:
                        logger.error(f"失败回调函数执行失败：{str(callback_error)}")
    
    return succeeded, failed


# ============================================================================
# 重试统计
# ============================================================================

class RetryStatistics:
    """重试统计类"""
    
    def __init__(self):
        self.stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'by_function': {}
        }
    
    def record_retry(self, function_name: str, success: bool):
        """
        记录重试统计
        
        Args:
            function_name: 函数名
            success: 是否成功
        """
        self.stats['total_retries'] += 1
        
        if success:
            self.stats['successful_retries'] += 1
        else:
            self.stats['failed_retries'] += 1
        
        # 按函数统计
        if function_name not in self.stats['by_function']:
            self.stats['by_function'][function_name] = {
                'total': 0,
                'success': 0,
                'failed': 0
            }
        
        self.stats['by_function'][function_name]['total'] += 1
        if success:
            self.stats['by_function'][function_name]['success'] += 1
        else:
            self.stats['by_function'][function_name]['failed'] += 1
    
    def get_statistics(self) -> dict:
        """
        获取统计信息
        
        Returns:
            dict: 统计信息
        """
        return self.stats.copy()
    
    def clear_statistics(self):
        """清除统计信息"""
        self.stats = {
            'total_retries': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'by_function': {}
        }


# 全局重试统计实例
retry_statistics = RetryStatistics()


def get_retry_statistics() -> dict:
    """
    获取重试统计信息
    
    Returns:
        dict: 重试统计信息
    """
    return retry_statistics.get_statistics()


def clear_retry_statistics():
    """清除重试统计信息"""
    retry_statistics.clear_statistics()
