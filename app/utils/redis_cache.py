"""
Redis 缓存管理模块
提供 Redis 连接管理、缓存装饰器、缓存失效机制等功能
"""
import json
import hashlib
import logging
import functools
from typing import Any, Callable, Optional, Union, List, Dict
from datetime import datetime
from flask import current_app
import redis
from redis.connection import ConnectionPool


# 缓存统计信息
cache_stats = {
    'hits': 0,
    'misses': 0,
    'errors': 0,
    'sets': 0,
    'deletes': 0,
    'total_time_saved': 0.0  # 累计节省的时间（秒）
}


class RedisCacheManager:
    """
    Redis 缓存管理器
    
    单例模式，管理 Redis 连接池和缓存操作
    """
    
    _instance = None
    _pool = None
    _client = None
    
    def __new__(cls, app=None):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, app=None):
        """初始化 Redis 连接"""
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        初始化 Redis 连接池
        
        Args:
            app: Flask 应用实例
        """
        if self._pool is not None:
            return
        
        try:
            # 创建连接池
            self._pool = ConnectionPool(
                host=app.config.get('REDIS_HOST', 'localhost'),
                port=app.config.get('REDIS_PORT', 6379),
                password=app.config.get('REDIS_PASSWORD'),
                db=app.config.get('REDIS_DB', 0),
                max_connections=app.config.get('REDIS_MAX_CONNECTIONS', 50),
                socket_timeout=app.config.get('REDIS_SOCKET_TIMEOUT', 5),
                socket_connect_timeout=app.config.get('REDIS_SOCKET_CONNECT_TIMEOUT', 5),
                retry_on_timeout=app.config.get('REDIS_RETRY_ON_TIMEOUT', True),
                decode_responses=True  # 自动解码为字符串
            )
            
            # 创建客户端
            self._client = redis.Redis(connection_pool=self._pool)
            
            # 测试连接
            self._client.ping()
            
            app.logger.info(
                f"Redis 连接池初始化成功 - "
                f"host: {app.config.get('REDIS_HOST')}, "
                f"port: {app.config.get('REDIS_PORT')}, "
                f"db: {app.config.get('REDIS_DB')}, "
                f"max_connections: {app.config.get('REDIS_MAX_CONNECTIONS')}"
            )
            
        except redis.ConnectionError as e:
            app.logger.error(f"Redis 连接失败: {str(e)}")
            self._pool = None
            self._client = None
            raise
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """获取 Redis 客户端"""
        return self._client
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在返回 None
        """
        if self._client is None:
            return None
        
        try:
            value = self._client.get(key)
            if value is not None:
                cache_stats['hits'] += 1
                return json.loads(value)
            cache_stats['misses'] += 1
            return None
        except Exception as e:
            cache_stats['errors'] += 1
            logging.error(f"Redis GET 失败 (key={key}): {str(e)}")
            return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 过期时间（秒），None 使用默认值
            
        Returns:
            是否成功
        """
        if self._client is None:
            return False
        
        try:
            if timeout is None:
                timeout = current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
            
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            result = self._client.setex(key, timeout, serialized)
            cache_stats['sets'] += 1
            return result
        except Exception as e:
            cache_stats['errors'] += 1
            logging.error(f"Redis SET 失败 (key={key}): {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        if self._client is None:
            return False
        
        try:
            result = self._client.delete(key)
            cache_stats['deletes'] += 1
            return result > 0
        except Exception as e:
            cache_stats['errors'] += 1
            logging.error(f"Redis DELETE 失败 (key={key}): {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有缓存
        
        Args:
            pattern: 键模式（如 "houses:*"）
            
        Returns:
            删除的键数量
        """
        if self._client is None:
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                deleted = self._client.delete(*keys)
                cache_stats['deletes'] += deleted
                return deleted
            return 0
        except Exception as e:
            cache_stats['errors'] += 1
            logging.error(f"Redis DELETE PATTERN 失败 (pattern={pattern}): {str(e)}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        if self._client is None:
            return False
        
        try:
            return self._client.exists(key) > 0
        except Exception as e:
            logging.error(f"Redis EXISTS 失败 (key={key}): {str(e)}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        获取键的剩余过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余秒数，-1 表示永不过期，-2 表示不存在
        """
        if self._client is None:
            return -2
        
        try:
            return self._client.ttl(key)
        except Exception as e:
            logging.error(f"Redis TTL 失败 (key={key}): {str(e)}")
            return -2
    
    def incr(self, key: str) -> int:
        """
        递增计数器
        
        Args:
            key: 缓存键
            
        Returns:
            递增后的值
        """
        if self._client is None:
            return 0
        
        try:
            return self._client.incr(key)
        except Exception as e:
            logging.error(f"Redis INCR 失败 (key={key}): {str(e)}")
            return 0
    
    def get_stats(self) -> Dict:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        total_requests = cache_stats['hits'] + cache_stats['misses']
        hit_rate = (cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            'hits': cache_stats['hits'],
            'misses': cache_stats['misses'],
            'errors': cache_stats['errors'],
            'sets': cache_stats['sets'],
            'deletes': cache_stats['deletes'],
            'hit_rate': f"{hit_rate:.2f}%",
            'total_requests': total_requests,
            'total_time_saved': f"{cache_stats['total_time_saved']:.2f}秒"
        }
        
        # 添加 Redis 服务器信息
        if self._client:
            try:
                info = self._client.info()
                stats['redis_info'] = {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'total_connections_received': info.get('total_connections_received', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'uptime_in_seconds': info.get('uptime_in_seconds', 0)
                }
                
                # 获取当前数据库的键数量
                db_size = self._client.dbsize()
                stats['redis_info']['total_keys'] = db_size
                
            except Exception as e:
                stats['redis_error'] = str(e)
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        global cache_stats
        cache_stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'sets': 0,
            'deletes': 0,
            'total_time_saved': 0.0
        }
    
    def close(self):
        """关闭连接池"""
        if self._pool:
            self._pool.disconnect()
            self._pool = None
            self._client = None


# 全局缓存管理器实例
cache_manager = RedisCacheManager()


def get_cache_manager() -> RedisCacheManager:
    """获取缓存管理器实例"""
    return cache_manager


def generate_cache_key(*args, **kwargs) -> str:
    """
    生成缓存键
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        缓存键字符串
    """
    # 将参数转换为字符串
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    # 生成哈希
    key_string = ":".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    return key_hash


def cache_result(
    key_prefix: str,
    timeout: Optional[int] = None,
    key_builder: Optional[Callable] = None,
    skip_cache: Optional[Callable] = None
):
    """
    缓存装饰器 - 缓存函数返回结果
    
    Args:
        key_prefix: 缓存键前缀
        timeout: 缓存过期时间（秒），None 使用默认值
        key_builder: 自定义键生成函数，接收函数参数
        skip_cache: 判断是否跳过缓存的函数，接收函数参数
        
    Returns:
        装饰器函数
        
    使用示例:
        @cache_result('houses', timeout=300)
        def get_houses(page, per_page):
            return House.query.paginate(page=page, per_page=per_page)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 检查缓存是否启用
            try:
                cache_enabled = current_app.config.get('CACHE_ENABLED', True)
            except:
                cache_enabled = True
            
            if not cache_enabled:
                return func(*args, **kwargs)
            
            # 检查是否跳过缓存
            if skip_cache and skip_cache(*args, **kwargs):
                return func(*args, **kwargs)
            
            # 生成缓存键
            if key_builder:
                cache_key_suffix = key_builder(*args, **kwargs)
            else:
                cache_key_suffix = generate_cache_key(*args, **kwargs)
            
            try:
                key_prefix_config = current_app.config.get('CACHE_KEY_PREFIX', 'housing_rental:')
            except:
                key_prefix_config = 'housing_rental:'
            
            cache_key = f"{key_prefix_config}{key_prefix}:{cache_key_suffix}"
            
            # 尝试从缓存获取
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 缓存结果
            cache_manager.set(cache_key, result, timeout)
            
            # 记录节省的时间
            cache_stats['total_time_saved'] += execution_time
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(key_prefix: str, *args, **kwargs):
    """
    手动失效缓存
    
    Args:
        key_prefix: 缓存键前缀
        *args: 位置参数
        **kwargs: 关键字参数
    """
    cache_key_suffix = generate_cache_key(*args, **kwargs)
    
    try:
        key_prefix_config = current_app.config.get('CACHE_KEY_PREFIX', 'housing_rental:')
    except:
        key_prefix_config = 'housing_rental:'
    
    cache_key = f"{key_prefix_config}{key_prefix}:{cache_key_suffix}"
    cache_manager.delete(cache_key)


def invalidate_cache_pattern(pattern: str):
    """
    失效匹配模式的所有缓存
    
    Args:
        pattern: 缓存键模式（如 "houses:*"）
    """
    try:
        key_prefix_config = current_app.config.get('CACHE_KEY_PREFIX', 'housing_rental:')
    except:
        key_prefix_config = 'housing_rental:'
    
    full_pattern = f"{key_prefix_config}{pattern}"
    cache_manager.delete_pattern(full_pattern)


class CacheEventEmitter:
    """
    缓存事件发射器
    用于实现事件驱动的缓存失效
    """
    
    # 事件到缓存模式的映射
    EVENT_CACHE_MAP = {
        # 房源相关事件
        'house_created': ['houses:*', 'house_stats:*'],
        'house_updated': ['houses:*', 'house:*'],
        'house_deleted': ['houses:*', 'house:*', 'house_stats:*'],
        
        # 用户相关事件
        'user_updated': ['user:*', 'users:*'],
        'user_deleted': ['user:*', 'users:*'],
        
        # 合同相关事件
        'contract_created': ['contracts:*', 'house:*', 'houses:*'],
        'contract_updated': ['contracts:*', 'house:*'],
        'contract_deleted': ['contracts:*', 'house:*', 'houses:*'],
        
        # 租客相关事件
        'tenant_created': ['tenants:*'],
        'tenant_updated': ['tenants:*', 'tenant:*'],
        'tenant_deleted': ['tenants:*', 'tenant:*'],
        
        # 系统配置相关事件
        'config_updated': ['config:*'],
    }
    
    @classmethod
    def emit(cls, event: str):
        """
        发射缓存失效事件
        
        Args:
            event: 事件名称
        """
        patterns = cls.EVENT_CACHE_MAP.get(event, [])
        for pattern in patterns:
            invalidate_cache_pattern(pattern)
            logging.info(f"缓存失效事件: {event} -> {pattern}")


def cached_model(
    model_name: str,
    timeout: Optional[int] = None
):
    """
    模型缓存装饰器
    专门用于缓存数据库模型查询结果
    
    Args:
        model_name: 模型名称（如 'house', 'user'）
        timeout: 缓存过期时间（秒）
        
    Returns:
        装饰器函数
        
    使用示例:
        @cached_model('house', timeout=600)
        def get_house_by_id(house_id):
            return House.query.get(house_id)
    """
    return cache_result(
        key_prefix=model_name,
        timeout=timeout,
        key_builder=lambda *args, **kwargs: str(args[0]) if args else str(kwargs.get('id', ''))
    )


def cached_list(
    list_name: str,
    timeout: Optional[int] = None,
    params_to_key: Optional[Callable] = None
):
    """
    列表缓存装饰器
    专门用于缓存列表查询结果
    
    Args:
        list_name: 列表名称（如 'houses', 'users'）
        timeout: 缓存过期时间（秒）
        params_to_key: 参数到键的转换函数
        
    Returns:
        装饰器函数
        
    使用示例:
        @cached_list('houses', timeout=300)
        def get_houses_list(page, per_page, **filters):
            return House.query.filter_by(**filters).paginate(page=page, per_page=per_page)
    """
    def default_params_to_key(*args, **kwargs):
        # 提取分页参数
        page = kwargs.get('page', args[0] if args else 1)
        per_page = kwargs.get('per_page', args[1] if len(args) > 1 else 20)
        
        # 提取筛选参数
        filters = {k: v for k, v in kwargs.items() if k not in ['page', 'per_page']}
        
        # 生成键
        filter_str = ":".join(f"{k}={v}" for k, v in sorted(filters.items()))
        return f"p{page}:pp{per_page}:{filter_str}"
    
    return cache_result(
        key_prefix=list_name,
        timeout=timeout,
        key_builder=params_to_key or default_params_to_key
    )


# 便捷函数
def cache_get(key: str) -> Optional[Any]:
    """获取缓存"""
    return cache_manager.get(key)


def cache_set(key: str, value: Any, timeout: Optional[int] = None) -> bool:
    """设置缓存"""
    return cache_manager.set(key, value, timeout)


def cache_delete(key: str) -> bool:
    """删除缓存"""
    return cache_manager.delete(key)


def cache_exists(key: str) -> bool:
    """检查缓存是否存在"""
    return cache_manager.exists(key)
