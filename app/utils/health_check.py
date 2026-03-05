"""
健康检查模块

功能：
1. 数据库健康检查 - 检查数据库连接状态、连接池状态、查询性能
2. Redis 健康检查 - 检查 Redis 连接状态、性能
3. 系统资源检查 - CPU、内存、磁盘使用情况
4. 综合健康状态评估

使用方法：
    from app.utils.health_check import HealthChecker
    
    checker = HealthChecker(app, db)
    health_status = checker.check_all()
"""
import time
import os
import psutil
import logging
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


class HealthStatus:
    """健康状态常量"""
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'


class HealthCheckResult:
    """
    健康检查结果
    
    Attributes:
        name: 检查项名称
        status: 健康状态（healthy/degraded/unhealthy）
        message: 状态消息
        details: 详细信息
        timestamp: 检查时间戳
        response_time: 响应时间（秒）
    """
    
    def __init__(
        self,
        name: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        response_time: Optional[float] = None
    ):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        self.response_time = response_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'name': self.name,
            'status': self.status,
            'message': self.message,
            'timestamp': self.timestamp,
        }
        
        if self.response_time is not None:
            result['response_time'] = f"{self.response_time:.4f}秒"
        
        if self.details:
            result['details'] = self.details
        
        return result


class HealthChecker:
    """
    健康检查器
    
    提供全面的系统健康检查功能，包括：
    - 数据库连接和性能检查
    - Redis 缓存检查
    - 系统资源检查
    - 业务指标检查
    """
    
    def __init__(self, app: Optional[Flask] = None, db: Optional[SQLAlchemy] = None):
        """
        初始化健康检查器
        
        Args:
            app: Flask 应用实例
            db: SQLAlchemy 数据库实例
        """
        self.app = app
        self.db = db
        self.logger = logging.getLogger('health_check')
        
        # 健康检查阈值配置
        self.thresholds = {
            'db_response_time_warning': 1.0,  # 数据库响应时间警告阈值（秒）
            'db_response_time_critical': 3.0,  # 数据库响应时间严重阈值（秒）
            'cpu_usage_warning': 70,  # CPU 使用率警告阈值（%）
            'cpu_usage_critical': 90,  # CPU 使用率严重阈值（%）
            'memory_usage_warning': 80,  # 内存使用率警告阈值（%）
            'memory_usage_critical': 95,  # 内存使用率严重阈值（%）
            'disk_usage_warning': 80,  # 磁盘使用率警告阈值（%）
            'disk_usage_critical': 95,  # 磁盘使用率严重阈值（%）
            'pool_usage_warning': 80,  # 连接池使用率警告阈值（%）
            'pool_usage_critical': 95,  # 连接池使用率严重阈值（%）
        }
        
        if app and db:
            self.init_app(app, db)
    
    def init_app(self, app: Flask, db: SQLAlchemy):
        """
        初始化健康检查器
        
        Args:
            app: Flask 应用实例
            db: SQLAlchemy 数据库实例
        """
        self.app = app
        self.db = db
        
        # 从应用配置中读取阈值
        self.thresholds.update({
            'db_response_time_warning': app.config.get('HEALTH_DB_RESPONSE_TIME_WARNING', 1.0),
            'db_response_time_critical': app.config.get('HEALTH_DB_RESPONSE_TIME_CRITICAL', 3.0),
            'cpu_usage_warning': app.config.get('HEALTH_CPU_USAGE_WARNING', 70),
            'cpu_usage_critical': app.config.get('HEALTH_CPU_USAGE_CRITICAL', 90),
            'memory_usage_warning': app.config.get('HEALTH_MEMORY_USAGE_WARNING', 80),
            'memory_usage_critical': app.config.get('HEALTH_MEMORY_USAGE_CRITICAL', 95),
            'disk_usage_warning': app.config.get('HEALTH_DISK_USAGE_WARNING', 80),
            'disk_usage_critical': app.config.get('HEALTH_DISK_USAGE_CRITICAL', 95),
            'pool_usage_warning': app.config.get('HEALTH_POOL_USAGE_WARNING', 80),
            'pool_usage_critical': app.config.get('HEALTH_POOL_USAGE_CRITICAL', 95),
        })
        
        self.logger.info('健康检查器已初始化')
    
    def check_all(self) -> Dict[str, Any]:
        """
        执行所有健康检查
        
        Returns:
            综合健康状态报告
        """
        start_time = time.time()
        
        # 执行各项检查
        checks = [
            self.check_database(),
            self.check_database_pool(),
            self.check_redis(),
            self.check_system_resources(),
        ]
        
        # 计算总体状态
        overall_status = self._calculate_overall_status(checks)
        
        # 构建结果
        result = {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': [check.to_dict() for check in checks],
            'summary': self._generate_summary(checks),
            'total_check_time': f"{time.time() - start_time:.4f}秒"
        }
        
        return result
    
    def check_database(self) -> HealthCheckResult:
        """
        检查数据库连接和性能
        
        Returns:
            数据库健康检查结果
        """
        start_time = time.time()
        
        try:
            # 执行简单查询测试连接
            result = self.db.session.execute(text('SELECT 1')).scalar()
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 确定状态
            if response_time >= self.thresholds['db_response_time_critical']:
                status = HealthStatus.UNHEALTHY
                message = f'数据库响应时间过长: {response_time:.4f}秒'
            elif response_time >= self.thresholds['db_response_time_warning']:
                status = HealthStatus.DEGRADED
                message = f'数据库响应时间较慢: {response_time:.4f}秒'
            else:
                status = HealthStatus.HEALTHY
                message = '数据库连接正常'
            
            # 获取数据库信息
            db_info = self._get_database_info()
            
            # 获取连接池信息
            try:
                engine = self.db.engine
                pool = engine.pool
                pool_size = pool.size()
                checked_out = pool.checkedout()
                total_connections = pool_size + pool.overflow()
                
                db_info['connections'] = checked_out
                db_info['max_connections'] = total_connections
            except:
                db_info['connections'] = 0
                db_info['max_connections'] = 0
            
            # 添加响应时间（毫秒）
            db_info['response_time'] = round(response_time * 1000, 2)
            
            return HealthCheckResult(
                name='database',
                status=status,
                message=message,
                details=db_info,
                response_time=response_time
            )
            
        except Exception as e:
            return HealthCheckResult(
                name='database',
                status=HealthStatus.UNHEALTHY,
                message=f'数据库连接失败: {str(e)}',
                response_time=time.time() - start_time
            )
    
    def check_database_pool(self) -> HealthCheckResult:
        """
        检查数据库连接池状态
        
        Returns:
            连接池健康检查结果
        """
        try:
            # 获取连接池对象
            engine = self.db.engine
            pool = engine.pool
            
            # 获取连接池状态
            pool_size = pool.size()
            checked_in = pool.checkedin()
            checked_out = pool.checkedout()
            overflow = pool.overflow()
            
            # 计算使用率
            total_connections = pool_size + overflow
            usage_percent = (checked_out / total_connections * 100) if total_connections > 0 else 0
            
            # 确定状态
            if usage_percent >= self.thresholds['pool_usage_critical']:
                status = HealthStatus.UNHEALTHY
                message = f'连接池使用率过高: {usage_percent:.1f}%'
            elif usage_percent >= self.thresholds['pool_usage_warning']:
                status = HealthStatus.DEGRADED
                message = f'连接池使用率较高: {usage_percent:.1f}%'
            else:
                status = HealthStatus.HEALTHY
                message = '连接池状态正常'
            
            # 构建详细信息
            details = {
                'pool_size': pool_size,
                'checked_in': checked_in,
                'checked_out': checked_out,
                'overflow': overflow,
                'total_connections': total_connections,
                'usage_percent': f"{usage_percent:.1f}%",
                'config': {
                    'pool_size': self.app.config.get('SQLALCHEMY_POOL_SIZE', 10),
                    'max_overflow': self.app.config.get('SQLALCHEMY_MAX_OVERFLOW', 10),
                    'pool_recycle': self.app.config.get('SQLALCHEMY_POOL_RECYCLE', 3600),
                    'pool_timeout': self.app.config.get('SQLALCHEMY_POOL_TIMEOUT', 30),
                    'pool_pre_ping': self.app.config.get('SQLALCHEMY_POOL_PRE_PING', True),
                }
            }
            
            return HealthCheckResult(
                name='database_pool',
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                name='database_pool',
                status=HealthStatus.UNHEALTHY,
                message=f'连接池检查失败: {str(e)}'
            )
    
    def check_redis(self) -> HealthCheckResult:
        """
        检查 Redis 缓存状态
        
        Returns:
            Redis 健康检查结果
        """
        start_time = time.time()
        
        try:
            from app.utils.redis_cache import get_cache_manager
            
            cache_manager = get_cache_manager()
            
            # 检查是否连接
            if not cache_manager.is_connected:
                return HealthCheckResult(
                    name='redis',
                    status=HealthStatus.DEGRADED,
                    message='Redis 未连接，系统在无缓存模式下运行',
                    details={'connected': False, 'status': 'disconnected'}
                )
            
            # 测试 Redis 连接
            cache_manager.client.ping()
            response_time = time.time() - start_time
            
            # 获取 Redis 信息
            redis_info = self._get_redis_info(cache_manager)
            
            # 添加响应时间（毫秒）
            redis_info['response_time'] = round(response_time * 1000, 2)
            redis_info['status'] = 'healthy'
            
            # 添加内存使用信息
            if 'used_memory' in redis_info:
                redis_info['memory_usage'] = redis_info['used_memory']
            
            return HealthCheckResult(
                name='redis',
                status=HealthStatus.HEALTHY,
                message='Redis 连接正常',
                details=redis_info,
                response_time=response_time
            )
            
        except Exception as e:
            return HealthCheckResult(
                name='redis',
                status=HealthStatus.DEGRADED,
                message=f'Redis 检查失败: {str(e)}',
                response_time=time.time() - start_time,
                details={'status': 'error', 'error': str(e)}
            )
    
    def check_system_resources(self) -> HealthCheckResult:
        """
        检查系统资源使用情况
        
        Returns:
            系统资源健康检查结果
        """
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # CPU 负载（1分钟、5分钟、15分钟）
            try:
                cpu_load = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
                cpu_load_str = f"{cpu_load[0]:.2f}, {cpu_load[1]:.2f}, {cpu_load[2]:.2f}"
            except:
                cpu_load_str = "N/A"
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_available = memory.available
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used
            disk_total = disk.total
            
            # 系统启动时间
            boot_time = psutil.boot_time()
            start_time = datetime.fromtimestamp(boot_time).isoformat()
            
            # 计算运行时长
            uptime_seconds = time.time() - boot_time
            uptime = self._format_uptime(uptime_seconds)
            
            # 确定状态
            issues = []
            
            if cpu_percent >= self.thresholds['cpu_usage_critical']:
                issues.append(f'CPU 使用率过高: {cpu_percent:.1f}%')
            elif cpu_percent >= self.thresholds['cpu_usage_warning']:
                issues.append(f'CPU 使用率较高: {cpu_percent:.1f}%')
            
            if memory_percent >= self.thresholds['memory_usage_critical']:
                issues.append(f'内存使用率过高: {memory_percent:.1f}%')
            elif memory_percent >= self.thresholds['memory_usage_warning']:
                issues.append(f'内存使用率较高: {memory_percent:.1f}%')
            
            if disk_percent >= self.thresholds['disk_usage_critical']:
                issues.append(f'磁盘使用率过高: {disk_percent:.1f}%')
            elif disk_percent >= self.thresholds['disk_usage_warning']:
                issues.append(f'磁盘使用率较高: {disk_percent:.1f}%')
            
            # 确定总体状态
            if any('过高' in issue for issue in issues):
                status = HealthStatus.UNHEALTHY
            elif issues:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            message = '; '.join(issues) if issues else '系统资源使用正常'
            
            # 构建详细信息
            details = {
                'cpu': {
                    'usage': round(cpu_percent, 2),  # 数字类型
                    'cores': cpu_count,
                    'load': cpu_load_str,
                },
                'memory': {
                    'usage_percent': round(memory_percent, 2),  # 数字类型
                    'used': self._format_bytes(memory_used),
                    'available': self._format_bytes(memory_available),
                    'total': self._format_bytes(memory.total),
                },
                'disk': {
                    'usage_percent': round(disk_percent, 2),  # 数字类型
                    'used': self._format_bytes(disk_used),
                    'total': self._format_bytes(disk_total),
                    'free': self._format_bytes(disk.free),
                },
                'start_time': start_time,
                'uptime': uptime,
            }
            
            return HealthCheckResult(
                name='system_resources',
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                name='system_resources',
                status=HealthStatus.UNHEALTHY,
                message=f'系统资源检查失败: {str(e)}'
            )
    
    def check_database_query_performance(self, query: str, max_time: float = 1.0) -> HealthCheckResult:
        """
        检查数据库查询性能
        
        Args:
            query: SQL 查询语句
            max_time: 最大允许时间（秒）
        
        Returns:
            查询性能检查结果
        """
        start_time = time.time()
        
        try:
            # 执行查询
            result = self.db.session.execute(text(query))
            rows = result.fetchall()
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 确定状态
            if execution_time >= max_time:
                status = HealthStatus.DEGRADED
                message = f'查询执行时间过长: {execution_time:.4f}秒'
            else:
                status = HealthStatus.HEALTHY
                message = '查询执行正常'
            
            return HealthCheckResult(
                name='database_query_performance',
                status=status,
                message=message,
                details={
                    'query': query[:100] + '...' if len(query) > 100 else query,
                    'rows_returned': len(rows),
                },
                response_time=execution_time
            )
            
        except Exception as e:
            return HealthCheckResult(
                name='database_query_performance',
                status=HealthStatus.UNHEALTHY,
                message=f'查询执行失败: {str(e)}',
                response_time=time.time() - start_time
            )
    
    def _get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库信息
        
        Returns:
            数据库信息字典
        """
        try:
            # 获取数据库类型
            dialect = self.db.engine.dialect.name
            
            # 获取数据库版本
            if dialect == 'sqlite':
                version_result = self.db.session.execute(text('SELECT sqlite_version()')).scalar()
                version = version_result
            elif dialect == 'mysql':
                version_result = self.db.session.execute(text('SELECT VERSION()')).scalar()
                version = version_result
            elif dialect == 'postgresql':
                version_result = self.db.session.execute(text('SELECT version()')).scalar()
                version = version_result.split(',')[0] if version_result else 'unknown'
            else:
                version = 'unknown'
            
            return {
                'dialect': dialect,
                'version': version,
                'database_uri': self._mask_database_uri(self.app.config.get('SQLALCHEMY_DATABASE_URI', '')),
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_redis_info(self, cache_manager) -> Dict[str, Any]:
        """
        获取 Redis 信息
        
        Args:
            cache_manager: 缓存管理器实例
        
        Returns:
            Redis 信息字典
        """
        try:
            info = cache_manager.client.info()
            
            return {
                'connected': True,
                'version': info.get('redis_version', 'unknown'),
                'uptime': f"{info.get('uptime_in_seconds', 0)}秒",
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'total_keys': cache_manager.client.dbsize(),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_overall_status(self, checks: List[HealthCheckResult]) -> str:
        """
        计算总体健康状态
        
        Args:
            checks: 健康检查结果列表
        
        Returns:
            总体健康状态
        """
        # 如果有任何 UNHEALTHY 状态，总体状态为 UNHEALTHY
        if any(check.status == HealthStatus.UNHEALTHY for check in checks):
            return HealthStatus.UNHEALTHY
        
        # 如果有任何 DEGRADED 状态，总体状态为 DEGRADED
        if any(check.status == HealthStatus.DEGRADED for check in checks):
            return HealthStatus.DEGRADED
        
        # 否则为 HEALTHY
        return HealthStatus.HEALTHY
    
    def _generate_summary(self, checks: List[HealthCheckResult]) -> Dict[str, Any]:
        """
        生成健康检查摘要
        
        Args:
            checks: 健康检查结果列表
        
        Returns:
            摘要信息字典
        """
        healthy_count = sum(1 for check in checks if check.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for check in checks if check.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for check in checks if check.status == HealthStatus.UNHEALTHY)
        
        return {
            'total_checks': len(checks),
            'healthy': healthy_count,
            'degraded': degraded_count,
            'unhealthy': unhealthy_count,
        }
    
    def _format_bytes(self, bytes: int) -> str:
        """
        格式化字节数
        
        Args:
            bytes: 字节数
        
        Returns:
            格式化后的字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def _format_uptime(self, seconds: float) -> str:
        """
        格式化运行时长
        
        Args:
            seconds: 秒数
        
        Returns:
            格式化后的字符串，如 "2天 3小时 45分钟"
        """
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0 or not parts:
            parts.append(f"{minutes}分钟")
        
        return ' '.join(parts)
    
    def _mask_database_uri(self, uri: str) -> str:
        """
        遮蔽数据库 URI 中的敏感信息
        
        Args:
            uri: 数据库 URI
        
        Returns:
            遮蔽后的 URI
        """
        if '://' in uri:
            # 遮蔽密码部分
            parts = uri.split('://', 1)
            if '@' in parts[1]:
                auth, rest = parts[1].split('@', 1)
                if ':' in auth:
                    user, _ = auth.split(':', 1)
                    return f"{parts[0]}://{user}:***@{rest}"
        return uri


# 全局健康检查器实例
health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    """
    获取全局健康检查器实例
    
    Returns:
        HealthChecker 实例
    """
    return health_checker


def setup_health_checker(app: Flask, db: SQLAlchemy) -> HealthChecker:
    """
    设置健康检查器
    
    Args:
        app: Flask 应用实例
        db: SQLAlchemy 数据库实例
    
    Returns:
        HealthChecker 实例
    """
    global health_checker
    health_checker.init_app(app, db)
    return health_checker
